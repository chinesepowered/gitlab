#!/usr/bin/env python3
"""
Web server for AI Code Review component on Google Cloud Run
Handles webhook requests from GitLab and provides health endpoints
"""

import os
import json
import logging
from flask import Flask, request, jsonify
from datetime import datetime
import asyncio
import threading
from typing import Dict, Any

from ai_reviewer import AICodeReviewer
from cloud_auth import get_authenticated_client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("web_server")

app = Flask(__name__)

# Global configuration
config = {
    'port': int(os.getenv('PORT', 8080)),
    'debug': os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
    'webhook_secret': os.getenv('GITLAB_WEBHOOK_SECRET', ''),
    'max_concurrent_reviews': int(os.getenv('MAX_CONCURRENT_REVIEWS', '3'))
}

# Track active reviews
active_reviews = {}
review_semaphore = threading.Semaphore(config['max_concurrent_reviews'])


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Cloud Run"""
    try:
        # Test Google Cloud authentication
        client, auth_info = get_authenticated_client()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'ai-code-review',
            'version': '1.0.0',
            'authentication': {
                'method': auth_info.get('method', 'unknown'),
                'project_id': auth_info.get('project_id', 'unknown'),
                'authenticated': auth_info.get('authenticated', False)
            },
            'active_reviews': len(active_reviews),
            'available_slots': review_semaphore._value
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/webhook/gitlab', methods=['POST'])
def gitlab_webhook():
    """Handle GitLab webhook for merge request events"""
    try:
        # Verify webhook secret if configured
        if config['webhook_secret']:
            gitlab_token = request.headers.get('X-Gitlab-Token', '')
            if gitlab_token != config['webhook_secret']:
                logger.warning("Invalid webhook token")
                return jsonify({'error': 'Invalid webhook token'}), 401
        
        # Parse webhook data
        webhook_data = request.get_json()
        if not webhook_data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Check if this is a merge request event
        event_type = webhook_data.get('object_kind', '')
        if event_type != 'merge_request':
            return jsonify({'message': 'Event type not supported', 'event_type': event_type}), 200
        
        # Extract merge request information
        mr_data = webhook_data.get('object_attributes', {})
        mr_iid = mr_data.get('iid')
        mr_action = mr_data.get('action', '')
        project_id = webhook_data.get('project', {}).get('id')
        
        if not mr_iid or not project_id:
            return jsonify({'error': 'Missing required merge request data'}), 400
        
        # Only process specific MR actions
        if mr_action not in ['open', 'update', 'reopen']:
            return jsonify({'message': f'MR action "{mr_action}" not processed'}), 200
        
        # Check if we're already reviewing this MR
        review_key = f"{project_id}:{mr_iid}"
        if review_key in active_reviews:
            return jsonify({
                'message': 'Review already in progress',
                'review_id': review_key
            }), 202
        
        # Start async review
        def run_review():
            try:
                with review_semaphore:
                    active_reviews[review_key] = {
                        'started_at': datetime.now().isoformat(),
                        'status': 'running',
                        'mr_iid': mr_iid,
                        'project_id': project_id
                    }
                    
                    # Set up environment for the reviewer
                    review_env = {
                        'CI_PROJECT_ID': str(project_id),
                        'CI_MERGE_REQUEST_IID': str(mr_iid),
                        'CI_COMMIT_SHA': mr_data.get('last_commit', {}).get('id', ''),
                        'CI_PROJECT_URL': webhook_data.get('project', {}).get('web_url', ''),
                        'GITLAB_USER_LOGIN': mr_data.get('author', {}).get('username', 'webhook-user')
                    }
                    
                    # Override environment variables
                    for key, value in review_env.items():
                        os.environ[key] = value
                    
                    # Run the AI review
                    reviewer = AICodeReviewer()
                    reviewer.run()
                    
                    # Update status
                    active_reviews[review_key]['status'] = 'completed'
                    active_reviews[review_key]['completed_at'] = datetime.now().isoformat()
                    
                    logger.info(f"✅ Review completed for MR {mr_iid} in project {project_id}")
                    
            except Exception as e:
                logger.error(f"Review failed for MR {mr_iid}: {str(e)}")
                if review_key in active_reviews:
                    active_reviews[review_key]['status'] = 'failed'
                    active_reviews[review_key]['error'] = str(e)
                    active_reviews[review_key]['completed_at'] = datetime.now().isoformat()
            finally:
                # Clean up after a delay
                def cleanup():
                    import time
                    time.sleep(300)  # Keep status for 5 minutes
                    if review_key in active_reviews:
                        del active_reviews[review_key]
                
                threading.Thread(target=cleanup, daemon=True).start()
        
        # Start review in background thread
        review_thread = threading.Thread(target=run_review, daemon=True)
        review_thread.start()
        
        return jsonify({
            'message': 'AI code review started',
            'review_id': review_key,
            'mr_iid': mr_iid,
            'project_id': project_id,
            'action': mr_action
        }), 202
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/review/status/<review_id>', methods=['GET'])
def review_status(review_id):
    """Get status of a specific review"""
    if review_id in active_reviews:
        return jsonify(active_reviews[review_id])
    else:
        return jsonify({'error': 'Review not found'}), 404


@app.route('/review/manual', methods=['POST'])
def manual_review():
    """Trigger manual review for testing"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        project_id = data.get('project_id')
        mr_iid = data.get('mr_iid')
        
        if not project_id or not mr_iid:
            return jsonify({'error': 'Missing project_id or mr_iid'}), 400
        
        # Set up environment
        os.environ.update({
            'CI_PROJECT_ID': str(project_id),
            'CI_MERGE_REQUEST_IID': str(mr_iid),
            'CI_COMMIT_SHA': data.get('commit_sha', 'HEAD'),
            'CI_PROJECT_URL': data.get('project_url', ''),
        })
        
        # Run review
        reviewer = AICodeReviewer()
        reviewer.run()
        
        return jsonify({
            'message': 'Manual review completed',
            'project_id': project_id,
            'mr_iid': mr_iid
        })
        
    except Exception as e:
        logger.error(f"Manual review error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/stats', methods=['GET'])
def stats():
    """Get service statistics"""
    return jsonify({
        'active_reviews': len(active_reviews),
        'available_slots': review_semaphore._value,
        'max_concurrent_reviews': config['max_concurrent_reviews'],
        'reviews': {k: v for k, v in active_reviews.items()}
    })


@app.route('/', methods=['GET'])
def root():
    """Root endpoint with service information"""
    return jsonify({
        'service': 'AI Code Review for GitLab',
        'version': '1.0.0',
        'description': 'AI-powered code review using Gemini 2.5 Flash',
        'endpoints': {
            '/health': 'Health check',
            '/webhook/gitlab': 'GitLab webhook handler',
            '/review/status/<id>': 'Review status',
            '/review/manual': 'Manual review trigger',
            '/stats': 'Service statistics'
        },
        'hackathon': 'GitLab Hackathon Submission'
    })


if __name__ == '__main__':
    # Configure for Cloud Run
    logger.info(f"Starting AI Code Review server on port {config['port']}")
    logger.info(f"Max concurrent reviews: {config['max_concurrent_reviews']}")
    
    # Test authentication on startup
    try:
        client, auth_info = get_authenticated_client()
        logger.info(f"✅ Authentication successful: {auth_info['method']}")
    except Exception as e:
        logger.error(f"❌ Authentication failed: {str(e)}")
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=config['port'],
        debug=config['debug'],
        threaded=True
    ) 