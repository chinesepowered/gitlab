#!/usr/bin/env python3
"""
Gemini API client for AI-powered code review
Integrates with Google's Gemini 2.5 Flash model
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger("gemini_client")


class GeminiClient:
    """Client for interacting with Google's Gemini 2.5 Flash model"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._configure_client()
        
    def _configure_client(self):
        """Configure the Gemini client"""
        genai.configure(api_key=self.api_key)
        
        # Configure model with safety settings for code review
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
            generation_config=genai.GenerationConfig(
                temperature=0.1,  # Lower temperature for more consistent code reviews
                top_p=0.8,
                top_k=40,
                max_output_tokens=4096,
            )
        )
        
    def review_code(
        self,
        file_path: str,
        file_content: str,
        diff_content: Optional[str] = None,
        enable_security_scan: bool = True,
        enable_performance_hints: bool = True
    ) -> Dict[str, Any]:
        """
        Review code using Gemini 2.5 Flash model
        
        Args:
            file_path: Path to the file being reviewed
            file_content: Content of the file
            diff_content: Git diff content (if available)
            enable_security_scan: Whether to include security analysis
            enable_performance_hints: Whether to include performance suggestions
            
        Returns:
            Dictionary containing review results
        """
        try:
            prompt = self._build_review_prompt(
                file_path, file_content, diff_content,
                enable_security_scan, enable_performance_hints
            )
            
            logger.info(f"Reviewing {file_path} with Gemini 2.5 Flash")
            
            # Generate review
            response = self.model.generate_content(prompt)
            
            if not response.text:
                logger.warning(f"Empty response for {file_path}")
                return {'error': 'Empty response from Gemini'}
                
            # Parse JSON response
            try:
                review_result = json.loads(response.text)
                return self._validate_review_result(review_result)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response for {file_path}: {e}")
                # Try to extract JSON from response if it's wrapped in markdown
                return self._extract_json_from_response(response.text)
                
        except Exception as e:
            logger.error(f"Error reviewing {file_path}: {str(e)}")
            return {'error': str(e)}
    
    def _build_review_prompt(
        self,
        file_path: str,
        file_content: str,
        diff_content: Optional[str],
        enable_security_scan: bool,
        enable_performance_hints: bool
    ) -> str:
        """Build the prompt for code review"""
        
        file_extension = file_path.split('.')[-1] if '.' in file_path else ''
        
        prompt = f"""You are an expert code reviewer conducting a thorough analysis of code changes. 
Please review the following {'file diff' if diff_content else 'file'} and provide detailed feedback.

FILE INFORMATION:
- File path: {file_path}
- File type: {file_extension}

"""
        
        if diff_content:
            prompt += f"""
DIFF CONTENT:
```diff
{diff_content}
```

FULL FILE CONTENT:
```{file_extension}
{file_content}
```
"""
        else:
            prompt += f"""
FILE CONTENT:
```{file_extension}
{file_content}
```
"""
        
        prompt += f"""
REVIEW REQUIREMENTS:
Please analyze this code for the following aspects:

1. **Code Quality**: 
   - Code style and formatting
   - Naming conventions
   - Code structure and organization
   - Maintainability and readability
   - Best practices for the language

2. **Logic and Correctness**:
   - Potential bugs and logical errors
   - Edge cases that might not be handled
   - Correct implementation of algorithms
   - Error handling

3. **Documentation**:
   - Missing or inadequate comments
   - Unclear variable/function names
   - Need for additional documentation

"""
        
        if enable_security_scan:
            prompt += """
4. **Security Analysis**:
   - Potential security vulnerabilities
   - Input validation issues
   - Authentication and authorization problems
   - Data exposure risks
   - Injection vulnerabilities (SQL, XSS, etc.)

"""
        
        if enable_performance_hints:
            prompt += """
5. **Performance Optimization**:
   - Inefficient algorithms or data structures
   - Memory usage concerns
   - Database query optimization
   - Caching opportunities
   - Resource management

"""
        
        prompt += """
RESPONSE FORMAT:
Respond with a JSON object in the following format:

{
  "overall_score": <number between 1-10>,
  "summary": "<brief summary of the review>",
  "comments": [
    {
      "line_number": <line number or null if general>,
      "severity": "<low|medium|high>",
      "category": "<security|performance|quality|logic|style|documentation>",
      "title": "<short title>",
      "description": "<detailed description>",
      "suggestion": "<optional code suggestion>",
      "impact": "<potential impact if not addressed>"
    }
  ],
  "positive_aspects": [
    "<list of good practices found>"
  ],
  "recommendations": [
    "<high-level recommendations>"
  ]
}

GUIDELINES:
- Focus on actionable feedback
- Prioritize security and logic issues
- Be constructive and helpful
- Include line numbers when possible
- Provide specific suggestions when applicable
- Consider the context and purpose of the code
- Be concise but thorough

Please provide your review in the exact JSON format specified above.
"""
        
        return prompt
    
    def _validate_review_result(self, review_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean up the review result"""
        
        # Ensure required fields exist
        required_fields = ['overall_score', 'summary', 'comments']
        for field in required_fields:
            if field not in review_result:
                review_result[field] = [] if field == 'comments' else ''
                
        # Validate overall_score
        if 'overall_score' in review_result:
            try:
                score = float(review_result['overall_score'])
                review_result['overall_score'] = max(1, min(10, score))
            except (ValueError, TypeError):
                review_result['overall_score'] = 5
                
        # Validate comments
        validated_comments = []
        for comment in review_result.get('comments', []):
            if isinstance(comment, dict):
                validated_comment = {
                    'line_number': comment.get('line_number'),
                    'severity': comment.get('severity', 'medium'),
                    'category': comment.get('category', 'quality'),
                    'title': comment.get('title', 'Code Review'),
                    'description': comment.get('description', ''),
                    'suggestion': comment.get('suggestion', ''),
                    'impact': comment.get('impact', '')
                }
                
                # Validate severity
                if validated_comment['severity'] not in ['low', 'medium', 'high']:
                    validated_comment['severity'] = 'medium'
                    
                # Validate category
                valid_categories = ['security', 'performance', 'quality', 'logic', 'style', 'documentation']
                if validated_comment['category'] not in valid_categories:
                    validated_comment['category'] = 'quality'
                    
                validated_comments.append(validated_comment)
                
        review_result['comments'] = validated_comments
        
        # Ensure other fields are lists
        for field in ['positive_aspects', 'recommendations']:
            if field not in review_result:
                review_result[field] = []
            elif not isinstance(review_result[field], list):
                review_result[field] = []
                
        return review_result
    
    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from response that might be wrapped in markdown"""
        try:
            # Look for JSON in markdown code blocks
            import re
            json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            matches = re.findall(json_pattern, response_text, re.DOTALL)
            
            if matches:
                return json.loads(matches[0])
                
            # Try to find JSON-like content
            brace_start = response_text.find('{')
            brace_end = response_text.rfind('}')
            
            if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
                json_content = response_text[brace_start:brace_end + 1]
                return json.loads(json_content)
                
        except Exception as e:
            logger.error(f"Failed to extract JSON: {e}")
            
        # Return fallback response
        return {
            'overall_score': 5,
            'summary': 'Review completed but response format was invalid',
            'comments': [{
                'line_number': None,
                'severity': 'medium',
                'category': 'quality',
                'title': 'Review Format Issue',
                'description': 'The AI review response could not be properly parsed. Manual review may be needed.',
                'suggestion': '',
                'impact': 'Unable to provide detailed feedback'
            }],
            'positive_aspects': [],
            'recommendations': ['Manual code review recommended due to parsing issues']
        } 