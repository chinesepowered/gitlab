#!/usr/bin/env python3
"""
Google Cloud Functions entry point for AI Code Review
No Docker required - deploys directly from source code
"""

import functions_framework
import json
import logging
import os
from datetime import datetime
from flask import Request

# Import our existing modules
from ai_reviewer import AICodeReviewer
from cloud_auth import get_authenticated_client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cloud_function")


@functions_framework.http
def webhook_handler(request: Request):
    """
    Cloud Functions HTTP trigger for GitLab webhooks
    This is the entry point when deployed as a Cloud Function
    """
    
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type, X-Gitlab-Token',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)
    
    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': '*'
    }
    
    try:
        # Health check endpoint
        if request.path == '/health' or request.args.get('health'):
            return handle_health_check()
        
        # Handle webhook
        if request.method == 'POST':
            return handle_gitlab_webhook(request)
        
        # Default response
        return json.dumps({
            'service': 'AI Code Review for GitLab',
            'version': '1.0.0',
            'description': 'AI-powered code review using Gemini 2.5 Flash',
            'hackathon': 'GitLab Hackathon Submission'
        }), 200, headers
        
    except Exception as e:
        logger.error(f"Function error: {str(e)}")
        return json.dumps({'error': str(e)}), 500, headers


def handle_health_check():
    """Handle health check requests"""
    try:
        # Test authentication
        client, auth_info = get_authenticated_client()
        
        response_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'ai-code-review-function',
            'version': '1.0.0',
            'authentication': {
                'method': auth_info.get('method', 'unknown'),
                'project_id': auth_info.get('project_id', 'unknown'),
                'authenticated': auth_info.get('authenticated', False)
            }
        }
        
        return json.dumps(response_data), 200, {'Content-Type': 'application/json'}
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return json.dumps({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500, {'Content-Type': 'application/json'}


def handle_gitlab_webhook(request: Request):
    """Handle GitLab webhook requests"""
    try:
        # Verify webhook secret if configured
        webhook_secret = os.getenv('GITLAB_WEBHOOK_SECRET', '')
        if webhook_secret:
            gitlab_token = request.headers.get('X-Gitlab-Token', '')
            if gitlab_token != webhook_secret:
                logger.warning("Invalid webhook token")
                return json.dumps({'error': 'Invalid webhook token'}), 401
        
        # Parse webhook data
        webhook_data = request.get_json()
        if not webhook_data:
            return json.dumps({'error': 'No JSON data provided'}), 400
        
        # Check if this is a merge request event
        event_type = webhook_data.get('object_kind', '')
        if event_type != 'merge_request':
            return json.dumps({
                'message': 'Event type not supported', 
                'event_type': event_type
            }), 200
        
        # Extract merge request information
        mr_data = webhook_data.get('object_attributes', {})
        mr_iid = mr_data.get('iid')
        mr_action = mr_data.get('action', '')
        project_id = webhook_data.get('project', {}).get('id')
        
        if not mr_iid or not project_id:
            return json.dumps({'error': 'Missing required merge request data'}), 400
        
        # Only process specific MR actions
        if mr_action not in ['open', 'update', 'reopen']:
            return json.dumps({
                'message': f'MR action "{mr_action}" not processed'
            }), 200
        
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
        
        logger.info(f"Starting AI review for MR {mr_iid} in project {project_id}")
        
        # Run the AI review (synchronously for Cloud Functions)
        reviewer = AICodeReviewer()
        reviewer.run()
        
        logger.info(f"✅ Review completed for MR {mr_iid} in project {project_id}")
        
        return json.dumps({
            'message': 'AI code review completed',
            'mr_iid': mr_iid,
            'project_id': project_id,
            'action': mr_action
        }), 200
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return json.dumps({'error': str(e)}), 500


# For testing locally
if __name__ == "__main__":
    from flask import Flask
    
    app = Flask(__name__)
    
    @app.route('/', methods=['GET', 'POST', 'OPTIONS'])
    @app.route('/health', methods=['GET'])
    def local_handler():
        from flask import request
        return webhook_handler(request)
    
    print("🧪 Running Cloud Function locally for testing...")
    print("Health check: http://localhost:8080/health")
    print("Webhook: http://localhost:8080/")
    
    app.run(host='0.0.0.0', port=8080, debug=True) 