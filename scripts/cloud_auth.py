#!/usr/bin/env python3
"""
Google Cloud authentication and configuration for AI Code Review
Supports both API key and service account authentication
"""

import os
import logging
import json
from typing import Optional
import google.auth
from google.auth import default
from google.oauth2 import service_account
import google.generativeai as genai

logger = logging.getLogger("cloud_auth")


class CloudAuthenticator:
    """Handles Google Cloud authentication with multiple methods"""
    
    def __init__(self):
        self.project_id = None
        self.credentials = None
        self.gemini_client = None
        
    def authenticate(self) -> bool:
        """
        Authenticate with Google Cloud using the best available method
        Priority: Service Account -> Application Default Credentials -> API Key
        """
        try:
            # Method 1: Try Service Account JSON
            if self._try_service_account_auth():
                logger.info("✅ Authenticated using Service Account")
                return True
                
            # Method 2: Try Application Default Credentials (Cloud Run, GCE, etc.)
            if self._try_default_credentials():
                logger.info("✅ Authenticated using Application Default Credentials")
                return True
                
            # Method 3: Fall back to API Key
            if self._try_api_key_auth():
                logger.info("✅ Authenticated using API Key")
                return True
                
            logger.error("❌ All authentication methods failed")
            return False
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    def _try_service_account_auth(self) -> bool:
        """Try to authenticate using service account JSON"""
        try:
            # Check for service account key file
            service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            
            if service_account_path and os.path.exists(service_account_path):
                self.credentials = service_account.Credentials.from_service_account_file(
                    service_account_path,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                self.project_id = self.credentials.project_id
                return True
                
            elif service_account_json:
                # Parse JSON from environment variable
                service_account_info = json.loads(service_account_json)
                self.credentials = service_account.Credentials.from_service_account_info(
                    service_account_info,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                self.project_id = service_account_info.get('project_id')
                return True
                
        except Exception as e:
            logger.debug(f"Service account auth failed: {str(e)}")
            
        return False
    
    def _try_default_credentials(self) -> bool:
        """Try to use Application Default Credentials"""
        try:
            self.credentials, project = default(
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            self.project_id = project or os.getenv('GOOGLE_CLOUD_PROJECT')
            
            if self.credentials and self.project_id:
                return True
                
        except Exception as e:
            logger.debug(f"Default credentials auth failed: {str(e)}")
            
        return False
    
    def _try_api_key_auth(self) -> bool:
        """Try to authenticate using API key"""
        try:
            api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'default-project')
                return True
                
        except Exception as e:
            logger.debug(f"API key auth failed: {str(e)}")
            
        return False
    
    def get_gemini_client(self):
        """Get configured Gemini client"""
        if not self.gemini_client:
            if self.credentials:
                # Use credentials for authentication
                genai.configure(credentials=self.credentials)
            else:
                # Fall back to API key
                api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
                if api_key:
                    genai.configure(api_key=api_key)
                else:
                    raise ValueError("No valid authentication method found for Gemini")
            
            # Create model with enhanced configuration for Cloud deployment
            self.gemini_client = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=4096,
                ),
                safety_settings={
                    genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
                    genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                    genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                    genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
        return self.gemini_client
    
    def get_project_id(self) -> Optional[str]:
        """Get the current Google Cloud project ID"""
        return self.project_id
    
    def is_authenticated(self) -> bool:
        """Check if authentication was successful"""
        return self.credentials is not None or os.getenv('GEMINI_API_KEY') is not None
    
    def get_auth_info(self) -> dict:
        """Get information about the current authentication method"""
        info = {
            'project_id': self.project_id,
            'authenticated': self.is_authenticated(),
            'method': 'unknown'
        }
        
        if self.credentials:
            if hasattr(self.credentials, 'service_account_email'):
                info['method'] = 'service_account'
                info['service_account'] = self.credentials.service_account_email
            else:
                info['method'] = 'default_credentials'
        elif os.getenv('GEMINI_API_KEY'):
            info['method'] = 'api_key'
            
        return info


def get_authenticated_client():
    """
    Convenience function to get an authenticated Gemini client
    Returns configured client ready for use
    """
    authenticator = CloudAuthenticator()
    
    if not authenticator.authenticate():
        raise RuntimeError("Failed to authenticate with Google Cloud")
        
    return authenticator.get_gemini_client(), authenticator.get_auth_info()


if __name__ == "__main__":
    # Test authentication
    try:
        client, auth_info = get_authenticated_client()
        print(f"✅ Authentication successful!")
        print(f"Method: {auth_info['method']}")
        print(f"Project ID: {auth_info['project_id']}")
        if 'service_account' in auth_info:
            print(f"Service Account: {auth_info['service_account']}")
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}") 