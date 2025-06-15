#!/usr/bin/env python3
"""
App Engine entry point for AI Code Review
Alternative to Cloud Functions for easier deployment
"""

from flask import Flask, request
from cloud_function_main import webhook_handler

# Create Flask app for App Engine
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST', 'OPTIONS'])
@app.route('/health', methods=['GET'])
@app.route('/webhook/gitlab', methods=['POST'])
def main():
    """App Engine entry point"""
    return webhook_handler(request)

if __name__ == '__main__':
    # For local testing
    app.run(host='127.0.0.1', port=8080, debug=True) 