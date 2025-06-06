#!/usr/bin/env python3
"""
AI-Powered Code Review for GitLab CI/CD
Main reviewer script that orchestrates the code review process
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from gemini_client import GeminiClient
from gitlab_client import GitLabClient
from report_generator import ReportGenerator

# Setup logging and console
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console)]
)
logger = logging.getLogger("ai_reviewer")


class AICodeReviewer:
    """Main AI Code Reviewer class"""
    
    def __init__(self):
        self.config = self._load_config()
        self.gemini_client = GeminiClient(self.config['gemini_api_key'])
        self.gitlab_client = GitLabClient(
            self.config['gitlab_token'],
            self.config['ci_project_id'],
            self.config['ci_project_url']
        )
        self.report_generator = ReportGenerator()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        required_vars = ['GEMINI_API_KEY', 'GITLAB_TOKEN', 'CI_PROJECT_ID']
        config = {}
        
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                logger.error(f"Missing required environment variable: {var}")
                sys.exit(1)
            config[var.lower()] = value
            
        # Optional configuration
        config.update({
            'review_scope': os.getenv('REVIEW_SCOPE', 'changed'),
            'max_files': int(os.getenv('MAX_FILES', '50')),
            'languages': os.getenv('LANGUAGES', '').split(',') if os.getenv('LANGUAGES') else [],
            'severity_threshold': os.getenv('SEVERITY_THRESHOLD', 'medium'),
            'include_patterns': os.getenv('INCLUDE_PATTERNS', '').split(',') if os.getenv('INCLUDE_PATTERNS') else [],
            'exclude_patterns': os.getenv('EXCLUDE_PATTERNS', '').split(',') if os.getenv('EXCLUDE_PATTERNS') else [],
            'enable_security_scan': os.getenv('ENABLE_SECURITY_SCAN', 'true').lower() == 'true',
            'enable_performance_hints': os.getenv('ENABLE_PERFORMANCE_HINTS', 'true').lower() == 'true',
            'post_mr_comments': os.getenv('POST_MR_COMMENTS', 'true').lower() == 'true',
            'generate_report': os.getenv('GENERATE_REPORT', 'true').lower() == 'true',
            'ci_merge_request_iid': os.getenv('CI_MERGE_REQUEST_IID'),
            'ci_commit_sha': os.getenv('CI_COMMIT_SHA'),
            'ci_project_url': os.getenv('CI_PROJECT_URL'),
            'gitlab_user_login': os.getenv('GITLAB_USER_LOGIN', 'ai-reviewer'),
        })
        
        return config
    
    def _get_files_to_review(self) -> List[Dict[str, Any]]:
        """Get list of files that need to be reviewed"""
        if not self.config['ci_merge_request_iid']:
            logger.warning("No merge request found, skipping review")
            return []
            
        if self.config['review_scope'] == 'changed':
            files = self.gitlab_client.get_changed_files(self.config['ci_merge_request_iid'])
        else:
            files = self.gitlab_client.get_all_project_files()
            
        # Filter files based on patterns and languages
        filtered_files = self._filter_files(files)
        
        # Limit number of files
        if len(filtered_files) > self.config['max_files']:
            logger.warning(f"Too many files ({len(filtered_files)}), limiting to {self.config['max_files']}")
            filtered_files = filtered_files[:self.config['max_files']]
            
        return filtered_files
    
    def _filter_files(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter files based on include/exclude patterns and languages"""
        filtered = []
        
        for file_info in files:
            file_path = file_info['new_path'] if 'new_path' in file_info else file_info['path']
            
            # Skip deleted files
            if file_info.get('deleted_file', False):
                continue
                
            # Check exclude patterns
            if self._matches_patterns(file_path, self.config['exclude_patterns']):
                continue
                
            # Check include patterns (if specified)
            if self.config['include_patterns'] and not self._matches_patterns(file_path, self.config['include_patterns']):
                continue
                
            # Check language filter
            if self.config['languages'] and not self._matches_languages(file_path, self.config['languages']):
                continue
                
            filtered.append(file_info)
            
        return filtered
    
    def _matches_patterns(self, file_path: str, patterns: List[str]) -> bool:
        """Check if file path matches any of the given patterns"""
        import fnmatch
        return any(fnmatch.fnmatch(file_path, pattern.strip()) for pattern in patterns if pattern.strip())
    
    def _matches_languages(self, file_path: str, languages: List[str]) -> bool:
        """Check if file matches any of the specified languages"""
        file_ext = Path(file_path).suffix.lower()
        language_extensions = {
            'python': ['.py', '.pyw'],
            'javascript': ['.js', '.mjs'],
            'typescript': ['.ts', '.tsx'],
            'java': ['.java'],
            'go': ['.go'],
            'rust': ['.rs'],
            'cpp': ['.cpp', '.cc', '.cxx', '.c++', '.hpp', '.h'],
            'csharp': ['.cs'],
            'php': ['.php'],
            'ruby': ['.rb'],
            'html': ['.html', '.htm'],
            'css': ['.css', '.scss', '.sass'],
            'yaml': ['.yml', '.yaml'],
            'json': ['.json'],
            'xml': ['.xml'],
            'sql': ['.sql'],
            'shell': ['.sh', '.bash', '.zsh']
        }
        
        for lang in languages:
            lang = lang.strip().lower()
            if lang in language_extensions and file_ext in language_extensions[lang]:
                return True
        return False
    
    def _review_file(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Review a single file using Gemini"""
        file_path = file_info['new_path'] if 'new_path' in file_info else file_info['path']
        
        try:
            # Get file content
            file_content = self.gitlab_client.get_file_content(file_path, self.config['ci_commit_sha'])
            if not file_content:
                logger.warning(f"Could not retrieve content for {file_path}")
                return None
                
            # Get diff if this is a changed file
            diff_content = None
            if 'diff' in file_info:
                diff_content = file_info['diff']
                
            # Review with Gemini
            review_result = self.gemini_client.review_code(
                file_path=file_path,
                file_content=file_content,
                diff_content=diff_content,
                enable_security_scan=self.config['enable_security_scan'],
                enable_performance_hints=self.config['enable_performance_hints']
            )
            
            return {
                'file_path': file_path,
                'review_result': review_result,
                'file_info': file_info
            }
            
        except Exception as e:
            logger.error(f"Error reviewing {file_path}: {str(e)}")
            return None
    
    def _post_review_comments(self, reviews: List[Dict[str, Any]]):
        """Post review comments to the merge request"""
        if not self.config['post_mr_comments'] or not self.config['ci_merge_request_iid']:
            return
            
        for review in reviews:
            if not review or not review['review_result']:
                continue
                
            review_result = review['review_result']
            file_path = review['file_path']
            
            for comment in review_result.get('comments', []):
                if self._should_post_comment(comment):
                    self.gitlab_client.post_mr_comment(
                        mr_iid=self.config['ci_merge_request_iid'],
                        file_path=file_path,
                        line_number=comment.get('line_number'),
                        comment_text=self._format_comment(comment)
                    )
    
    def _should_post_comment(self, comment: Dict[str, Any]) -> bool:
        """Determine if a comment should be posted based on severity threshold"""
        severity_levels = {'low': 1, 'medium': 2, 'high': 3}
        comment_severity = severity_levels.get(comment.get('severity', 'low'), 1)
        threshold_severity = severity_levels.get(self.config['severity_threshold'], 2)
        return comment_severity >= threshold_severity
    
    def _format_comment(self, comment: Dict[str, Any]) -> str:
        """Format a review comment for posting"""
        severity_emoji = {
            'low': '💡',
            'medium': '⚠️',
            'high': '🚨'
        }
        
        category_emoji = {
            'security': '🔒',
            'performance': '⚡',
            'quality': '✨',
            'logic': '🧠',
            'style': '🎨'
        }
        
        severity = comment.get('severity', 'low')
        category = comment.get('category', 'quality')
        
        formatted = f"{severity_emoji.get(severity, '💡')} {category_emoji.get(category, '✨')} "
        formatted += f"**{comment.get('title', 'Code Review')}**\n\n"
        formatted += f"{comment.get('description', '')}\n\n"
        
        if comment.get('suggestion'):
            formatted += f"**Suggestion:**\n```\n{comment['suggestion']}\n```\n\n"
            
        formatted += f"*Severity: {severity.title()} | Category: {category.title()}*\n"
        formatted += f"*🤖 Generated by AI Code Review*"
        
        return formatted
    
    def run(self):
        """Main entry point for the AI code reviewer"""
        console.print(Panel.fit("🤖 AI-Powered Code Review", style="bold blue"))
        
        start_time = datetime.now()
        
        try:
            # Get files to review
            console.print("\n📁 Analyzing files to review...")
            files_to_review = self._get_files_to_review()
            
            if not files_to_review:
                console.print("ℹ️ No files to review", style="yellow")
                return
                
            console.print(f"📋 Found {len(files_to_review)} files to review")
            
            # Display files table
            table = Table(title="Files to Review")
            table.add_column("File Path", style="cyan")
            table.add_column("Status", style="green")
            
            for file_info in files_to_review:
                file_path = file_info['new_path'] if 'new_path' in file_info else file_info['path']
                status = "Modified" if 'new_path' in file_info else "Existing"
                table.add_row(file_path, status)
                
            console.print(table)
            
            # Review files
            console.print("\n🔍 Starting AI code review...")
            reviews = []
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Reviewing files...", total=len(files_to_review))
                
                for file_info in files_to_review:
                    file_path = file_info['new_path'] if 'new_path' in file_info else file_info['path']
                    progress.update(task, description=f"Reviewing {file_path}")
                    
                    review = self._review_file(file_info)
                    if review:
                        reviews.append(review)
                        
                    progress.advance(task)
            
            console.print(f"✅ Reviewed {len(reviews)} files successfully")
            
            # Post comments to MR
            if self.config['post_mr_comments']:
                console.print("\n💬 Posting review comments...")
                self._post_review_comments(reviews)
                console.print("✅ Comments posted to merge request")
            
            # Generate reports
            if self.config['generate_report']:
                console.print("\n📊 Generating review reports...")
                self.report_generator.generate_reports(reviews, self.config)
                console.print("✅ Reports generated")
            
            # Summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            console.print(f"\n🎉 AI Code Review completed in {duration:.2f} seconds!")
            
            # Print summary
            total_comments = sum(len(r['review_result'].get('comments', [])) for r in reviews if r['review_result'])
            console.print(f"📈 Generated {total_comments} review comments")
            
        except Exception as e:
            logger.error(f"Error during code review: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    reviewer = AICodeReviewer()
    reviewer.run() 