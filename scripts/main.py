#!/usr/bin/env python3
"""
Main entry point for Google Cloud Functions
This file is required by Cloud Functions (must be named main.py)
"""

# Import the webhook handler from our cloud function module
from cloud_function_main import webhook_handler

# The webhook_handler function is automatically discovered by Cloud Functions
# when it's in main.py and matches the --entry-point parameter 