#!/usr/bin/env python3
"""
Sample Python code for demonstrating AI code review capabilities
This file contains various issues that the AI reviewer should detect
"""

import os
import sys
import requests
import hashlib

# Security issue: hardcoded credentials
API_KEY = "sk-1234567890abcdef"
SECRET_TOKEN = "secret123"

class UserManager:
    def __init__(self):
        self.users = {}
        self.connection = self.connect_db()
    
    def connect_db(self):
        # Security issue: hardcoded database credentials
        return {"host": "localhost", "user": "admin", "password": "admin123"}
    
    def authenticate_user(self, username, password):
        # Security issue: SQL injection vulnerability
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        
        # Logic issue: using == for password comparison (timing attack)
        if self.get_user_password(username) == password:
            return True
        return False
    
    def get_user_password(self, username):
        # Performance issue: inefficient loop instead of dict lookup
        for user_id, user_data in self.users.items():
            if user_data['username'] == username:
                return user_data['password']
        return None
    
    def hash_password(self, password):
        # Security issue: using MD5 for password hashing
        return hashlib.md5(password.encode()).hexdigest()
    
    def create_user(self, username, password, email):
        # Logic issue: no input validation
        user_id = len(self.users) + 1
        self.users[user_id] = {
            'username': username,
            'password': self.hash_password(password),
            'email': email
        }
        return user_id
    
    def send_notification(self, email, message):
        # Security issue: no input validation for email
        # Performance issue: making HTTP request without timeout
        try:
            response = requests.post('https://api.notifications.com/send', {
                'to': email,
                'message': message,
                'api_key': API_KEY
            })
            return response.status_code == 200
        except:
            # Quality issue: bare except clause
            return False
    
    def process_file(self, filename):
        # Logic issue: file operations without proper error handling
        with open(filename, 'r') as f:
            data = f.read()
        
        # Performance issue: inefficient string concatenation in loop
        result = ""
        for line in data.split('\n'):
            result += line.strip() + " "
        
        return result
    
    def calculate_statistics(self, numbers):
        # Logic issue: division by zero possibility
        average = sum(numbers) / len(numbers)
        
        # Performance issue: sorting when only max is needed
        max_value = sorted(numbers)[-1]
        
        return {'average': average, 'max': max_value}

# Quality issue: global variable
global_counter = 0

def increment_counter():
    # Quality issue: modifying global variable
    global global_counter
    global_counter += 1
    return global_counter

# Quality issue: function with too many parameters
def complex_function(a, b, c, d, e, f, g, h, i, j):
    # Style issue: inconsistent naming and spacing
    result=a+b+c+d+e+f+g+h+i+j
    return result

def main():
    # Logic issue: not checking if command line arguments exist
    filename = sys.argv[1]
    
    manager = UserManager()
    
    # Security issue: printing sensitive information
    print(f"API Key: {API_KEY}")
    
    # Performance issue: unnecessary repeated calculations
    for i in range(1000):
        hash_result = hashlib.sha256(str(i).encode()).hexdigest()
        print(f"Hash {i}: {hash_result}")
    
    # Logic issue: hardcoded values
    result = manager.calculate_statistics([1, 2, 3, 4, 5])
    print(result)

if __name__ == "__main__":
    main() 