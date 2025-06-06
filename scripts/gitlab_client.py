#!/usr/bin/env python3
"""
GitLab API client for AI-powered code review
Handles GitLab repository operations and MR interactions
"""

import os
import logging
import base64
from typing import Dict, List, Any, Optional
import requests
import gitlab
from urllib.parse import quote

logger = logging.getLogger("gitlab_client")


class GitLabClient:
    """Client for interacting with GitLab API"""
    
    def __init__(self, access_token: str, project_id: str, project_url: str):
        self.access_token = access_token
        self.project_id = project_id
        self.project_url = project_url
        self._setup_client()
        
    def _setup_client(self):
        """Setup GitLab client and project reference"""
        try:
            # Extract GitLab instance URL from project URL
            if '//' in self.project_url:
                gitlab_url = '/'.join(self.project_url.split('/')[:3])
            else:
                gitlab_url = 'https://gitlab.com'
                
            self.gl = gitlab.Gitlab(gitlab_url, private_token=self.access_token)
            self.project = self.gl.projects.get(self.project_id)
            
            logger.info(f"Connected to GitLab project: {self.project.name}")
            
        except Exception as e:
            logger.error(f"Failed to setup GitLab client: {str(e)}")
            raise
    
    def get_changed_files(self, merge_request_iid: str) -> List[Dict[str, Any]]:
        """Get list of changed files in a merge request"""
        try:
            mr = self.project.mergerequests.get(merge_request_iid)
            changes = mr.changes()
            
            files = []
            for change in changes.get('changes', []):
                files.append({
                    'old_path': change.get('old_path'),
                    'new_path': change.get('new_path'),
                    'new_file': change.get('new_file', False),
                    'renamed_file': change.get('renamed_file', False),
                    'deleted_file': change.get('deleted_file', False),
                    'diff': change.get('diff', ''),
                    'change': change
                })
                
            logger.info(f"Found {len(files)} changed files in MR {merge_request_iid}")
            return files
            
        except Exception as e:
            logger.error(f"Error getting changed files for MR {merge_request_iid}: {str(e)}")
            return []
    
    def get_all_project_files(self, path: str = "", max_files: int = 100) -> List[Dict[str, Any]]:
        """Get all files in the project repository"""
        try:
            files = []
            items = self.project.repository_tree(path=path, recursive=True, all=True)
            
            for item in items:
                if item['type'] == 'blob' and len(files) < max_files:
                    files.append({
                        'path': item['path'],
                        'name': item['name'],
                        'id': item['id']
                    })
                    
            logger.info(f"Found {len(files)} files in project")
            return files
            
        except Exception as e:
            logger.error(f"Error getting project files: {str(e)}")
            return []
    
    def get_file_content(self, file_path: str, ref: str = 'HEAD') -> Optional[str]:
        """Get content of a specific file"""
        try:
            file_data = self.project.files.get(file_path=file_path, ref=ref)
            
            # Decode base64 content
            if file_data.encoding == 'base64':
                content = base64.b64decode(file_data.content).decode('utf-8', errors='ignore')
            else:
                content = file_data.content
                
            return content
            
        except Exception as e:
            logger.error(f"Error getting file content for {file_path}: {str(e)}")
            return None
    
    def get_merge_request_info(self, merge_request_iid: str) -> Optional[Dict[str, Any]]:
        """Get merge request information"""
        try:
            mr = self.project.mergerequests.get(merge_request_iid)
            return {
                'iid': mr.iid,
                'title': mr.title,
                'description': mr.description,
                'author': mr.author,
                'source_branch': mr.source_branch,
                'target_branch': mr.target_branch,
                'state': mr.state,
                'web_url': mr.web_url,
                'created_at': mr.created_at,
                'updated_at': mr.updated_at
            }
        except Exception as e:
            logger.error(f"Error getting MR info for {merge_request_iid}: {str(e)}")
            return None
    
    def post_mr_comment(
        self,
        mr_iid: str,
        comment_text: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None
    ) -> bool:
        """Post a comment on a merge request"""
        try:
            mr = self.project.mergerequests.get(mr_iid)
            
            if file_path and line_number:
                # Post as a line comment
                # Note: GitLab API requires position data for line comments
                # For simplicity, we'll post as a general discussion note
                # In a production environment, you'd want to implement proper position tracking
                formatted_comment = f"**File: `{file_path}` (Line {line_number})**\n\n{comment_text}"
                note = mr.notes.create({'body': formatted_comment})
            else:
                # Post as a general comment
                note = mr.notes.create({'body': comment_text})
                
            logger.info(f"Posted comment on MR {mr_iid}")
            return True
            
        except Exception as e:
            logger.error(f"Error posting comment on MR {mr_iid}: {str(e)}")
            return False
    
    def create_mr_discussion(
        self,
        mr_iid: str,
        file_path: str,
        line_number: int,
        comment_text: str,
        line_type: str = "new"
    ) -> bool:
        """Create a discussion on a specific line in an MR"""
        try:
            mr = self.project.mergerequests.get(mr_iid)
            
            # Get the latest commit of the MR
            commits = mr.commits()
            if not commits:
                logger.warning(f"No commits found for MR {mr_iid}")
                return False
                
            latest_commit = commits[0]
            
            # Create discussion data
            discussion_data = {
                'body': comment_text,
                'position': {
                    'position_type': 'text',
                    'base_sha': mr.diff_refs['base_sha'],
                    'start_sha': mr.diff_refs['start_sha'],
                    'head_sha': mr.diff_refs['head_sha'],
                    'old_path': file_path,
                    'new_path': file_path,
                    'new_line': line_number if line_type == "new" else None,
                    'old_line': line_number if line_type == "old" else None,
                }
            }
            
            discussion = mr.discussions.create(discussion_data)
            logger.info(f"Created discussion on MR {mr_iid} for {file_path}:{line_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating discussion on MR {mr_iid}: {str(e)}")
            # Fallback to regular comment
            return self.post_mr_comment(mr_iid, f"**{file_path}:{line_number}**\n\n{comment_text}")
    
    def get_mr_discussions(self, mr_iid: str) -> List[Dict[str, Any]]:
        """Get existing discussions on a merge request"""
        try:
            mr = self.project.mergerequests.get(mr_iid)
            discussions = mr.discussions.list(all=True)
            
            discussion_list = []
            for discussion in discussions:
                discussion_info = {
                    'id': discussion.id,
                    'notes': []
                }
                
                for note in discussion.attributes.get('notes', []):
                    discussion_info['notes'].append({
                        'id': note['id'],
                        'body': note['body'],
                        'author': note['author'],
                        'created_at': note['created_at'],
                        'position': note.get('position')
                    })
                    
                discussion_list.append(discussion_info)
                
            return discussion_list
            
        except Exception as e:
            logger.error(f"Error getting discussions for MR {mr_iid}: {str(e)}")
            return []
    
    def update_mr_description(self, mr_iid: str, new_description: str) -> bool:
        """Update merge request description"""
        try:
            mr = self.project.mergerequests.get(mr_iid)
            mr.description = new_description
            mr.save()
            
            logger.info(f"Updated description for MR {mr_iid}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating MR description for {mr_iid}: {str(e)}")
            return False
    
    def add_mr_label(self, mr_iid: str, label: str) -> bool:
        """Add a label to merge request"""
        try:
            mr = self.project.mergerequests.get(mr_iid)
            
            # Get current labels and add new one if not present
            current_labels = mr.labels if mr.labels else []
            if label not in current_labels:
                current_labels.append(label)
                mr.labels = current_labels
                mr.save()
                
                logger.info(f"Added label '{label}' to MR {mr_iid}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error adding label to MR {mr_iid}: {str(e)}")
            return False
    
    def create_commit_status(
        self,
        commit_sha: str,
        state: str,
        description: str,
        context: str = "ai-code-review"
    ) -> bool:
        """Create a commit status"""
        try:
            commit = self.project.commits.get(commit_sha)
            
            status_data = {
                'state': state,  # pending, running, success, failed, canceled
                'description': description,
                'context': context
            }
            
            commit.statuses.create(status_data)
            logger.info(f"Created commit status for {commit_sha}: {state}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating commit status for {commit_sha}: {str(e)}")
            return False
    
    def get_project_languages(self) -> Dict[str, float]:
        """Get programming languages used in the project"""
        try:
            languages = self.project.languages()
            logger.info(f"Project languages: {languages}")
            return languages
        except Exception as e:
            logger.error(f"Error getting project languages: {str(e)}")
            return {}
    
    def search_files(self, query: str, scope: str = "blobs") -> List[Dict[str, Any]]:
        """Search for files in the project"""
        try:
            results = self.project.search(scope=scope, search=query)
            
            files = []
            for result in results:
                if scope == "blobs":
                    files.append({
                        'path': result['path'],
                        'filename': result['filename'],
                        'data': result.get('data', ''),
                        'ref': result.get('ref', 'master')
                    })
                    
            logger.info(f"Found {len(files)} files matching '{query}'")
            return files
            
        except Exception as e:
            logger.error(f"Error searching files with query '{query}': {str(e)}")
            return [] 