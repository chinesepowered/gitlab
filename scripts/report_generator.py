#!/usr/bin/env python3
"""
Report generator for AI-powered code review
Creates HTML and JSON reports from review results
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from jinja2 import Template
import xml.etree.ElementTree as ET
from xml.dom import minidom

logger = logging.getLogger("report_generator")


class ReportGenerator:
    """Generates various report formats from AI code review results"""
    
    def __init__(self):
        self.html_template = self._get_html_template()
    
    def generate_reports(self, reviews: List[Dict[str, Any]], config: Dict[str, Any]):
        """Generate all report formats"""
        try:
            # Generate summary data
            summary = self._generate_summary(reviews, config)
            
            # Generate JSON report
            self._generate_json_report(summary, reviews)
            
            # Generate HTML report
            self._generate_html_report(summary, reviews, config)
            
            # Generate JUnit XML report
            self._generate_junit_report(summary, reviews)
            
            logger.info("All reports generated successfully")
            
        except Exception as e:
            logger.error(f"Error generating reports: {str(e)}")
    
    def _generate_summary(self, reviews: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics from reviews"""
        total_files = len(reviews)
        total_comments = 0
        severity_counts = {'high': 0, 'medium': 0, 'low': 0}
        category_counts = {}
        average_score = 0
        
        for review in reviews:
            if not review or not review.get('review_result'):
                continue
                
            result = review['review_result']
            
            # Count comments by severity and category
            for comment in result.get('comments', []):
                total_comments += 1
                severity = comment.get('severity', 'medium')
                category = comment.get('category', 'quality')
                
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                category_counts[category] = category_counts.get(category, 0) + 1
            
            # Sum scores for average
            score = result.get('overall_score', 5)
            average_score += score
        
        # Calculate averages
        if total_files > 0:
            average_score = average_score / total_files
        
        return {
            'timestamp': datetime.now().isoformat(),
            'project_id': config.get('ci_project_id', ''),
            'merge_request_iid': config.get('ci_merge_request_iid', ''),
            'commit_sha': config.get('ci_commit_sha', ''),
            'total_files_reviewed': total_files,
            'total_comments': total_comments,
            'average_score': round(average_score, 2),
            'severity_distribution': severity_counts,
            'category_distribution': category_counts,
            'configuration': {
                'review_scope': config.get('review_scope', 'changed'),
                'max_files': config.get('max_files', 50),
                'severity_threshold': config.get('severity_threshold', 'medium'),
                'security_scan_enabled': config.get('enable_security_scan', True),
                'performance_hints_enabled': config.get('enable_performance_hints', True)
            }
        }
    
    def _generate_json_report(self, summary: Dict[str, Any], reviews: List[Dict[str, Any]]):
        """Generate JSON summary report"""
        try:
            report_data = {
                'summary': summary,
                'reviews': []
            }
            
            for review in reviews:
                if not review or not review.get('review_result'):
                    continue
                    
                review_data = {
                    'file_path': review.get('file_path', ''),
                    'overall_score': review['review_result'].get('overall_score', 0),
                    'summary': review['review_result'].get('summary', ''),
                    'comment_count': len(review['review_result'].get('comments', [])),
                    'positive_aspects_count': len(review['review_result'].get('positive_aspects', [])),
                    'recommendations_count': len(review['review_result'].get('recommendations', [])),
                    'severity_breakdown': self._get_severity_breakdown(review['review_result'].get('comments', []))
                }
                report_data['reviews'].append(review_data)
            
            # Write JSON report
            with open('ai-review-summary.json', 'w') as f:
                json.dump(report_data, f, indent=2)
            
            logger.info("JSON report generated: ai-review-summary.json")
            
        except Exception as e:
            logger.error(f"Error generating JSON report: {str(e)}")
    
    def _generate_html_report(self, summary: Dict[str, Any], reviews: List[Dict[str, Any]], config: Dict[str, Any]):
        """Generate HTML report"""
        try:
            # Prepare data for template
            template_data = {
                'summary': summary,
                'reviews': reviews,
                'config': config,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'severity_colors': {
                    'high': '#dc3545',
                    'medium': '#ffc107', 
                    'low': '#28a745'
                },
                'category_icons': {
                    'security': '🔒',
                    'performance': '⚡',
                    'quality': '✨',
                    'logic': '🧠',
                    'style': '🎨',
                    'documentation': '📝'
                }
            }
            
            # Render template
            html_content = self.html_template.render(**template_data)
            
            # Write HTML report
            with open('ai-review-report.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info("HTML report generated: ai-review-report.html")
            
        except Exception as e:
            logger.error(f"Error generating HTML report: {str(e)}")
    
    def _generate_junit_report(self, summary: Dict[str, Any], reviews: List[Dict[str, Any]]):
        """Generate JUnit XML report for GitLab CI integration"""
        try:
            # Create root element
            testsuites = ET.Element('testsuites')
            testsuites.set('name', 'AI Code Review')
            testsuites.set('tests', str(summary['total_files_reviewed']))
            testsuites.set('failures', str(summary['severity_distribution'].get('high', 0)))
            testsuites.set('errors', str(summary['severity_distribution'].get('medium', 0)))
            testsuites.set('time', '0')
            
            # Create testsuite
            testsuite = ET.SubElement(testsuites, 'testsuite')
            testsuite.set('name', 'Code Review Results')
            testsuite.set('tests', str(summary['total_files_reviewed']))
            testsuite.set('failures', str(summary['severity_distribution'].get('high', 0)))
            testsuite.set('errors', str(summary['severity_distribution'].get('medium', 0)))
            testsuite.set('time', '0')
            
            # Add test cases for each reviewed file
            for review in reviews:
                if not review or not review.get('review_result'):
                    continue
                    
                file_path = review.get('file_path', 'unknown')
                result = review['review_result']
                
                testcase = ET.SubElement(testsuite, 'testcase')
                testcase.set('classname', 'CodeReview')
                testcase.set('name', file_path)
                testcase.set('time', '0')
                
                # Check for high severity issues (failures)
                high_issues = [c for c in result.get('comments', []) if c.get('severity') == 'high']
                if high_issues:
                    failure = ET.SubElement(testcase, 'failure')
                    failure.set('message', f"High severity issues found in {file_path}")
                    failure.text = '\n'.join([f"{c.get('title', '')}: {c.get('description', '')}" for c in high_issues])
                
                # Check for medium severity issues (errors)
                medium_issues = [c for c in result.get('comments', []) if c.get('severity') == 'medium']
                if medium_issues and not high_issues:  # Only if no high issues
                    error = ET.SubElement(testcase, 'error')
                    error.set('message', f"Medium severity issues found in {file_path}")
                    error.text = '\n'.join([f"{c.get('title', '')}: {c.get('description', '')}" for c in medium_issues])
            
            # Write XML file
            xml_str = minidom.parseString(ET.tostring(testsuites)).toprettyxml(indent='  ')
            with open('ai-review-results.xml', 'w', encoding='utf-8') as f:
                f.write(xml_str)
            
            logger.info("JUnit XML report generated: ai-review-results.xml")
            
        except Exception as e:
            logger.error(f"Error generating JUnit report: {str(e)}")
    
    def _get_severity_breakdown(self, comments: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get severity breakdown for a list of comments"""
        breakdown = {'high': 0, 'medium': 0, 'low': 0}
        for comment in comments:
            severity = comment.get('severity', 'medium')
            breakdown[severity] = breakdown.get(severity, 0) + 1
        return breakdown
    
    def _get_html_template(self) -> Template:
        """Get the HTML report template"""
        template_str = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Code Review Report</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; background: #f8f9fa; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 10px; margin-bottom: 2rem; }
        .header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
        .header p { opacity: 0.9; font-size: 1.1rem; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .stat-card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .stat-card h3 { color: #6c757d; font-size: 0.9rem; text-transform: uppercase; margin-bottom: 0.5rem; }
        .stat-card .value { font-size: 2rem; font-weight: bold; color: #495057; }
        .severity-high { color: #dc3545; }
        .severity-medium { color: #ffc107; }
        .severity-low { color: #28a745; }
        .section { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 2rem; }
        .section h2 { color: #495057; margin-bottom: 1rem; border-bottom: 2px solid #e9ecef; padding-bottom: 0.5rem; }
        .file-review { border: 1px solid #e9ecef; border-radius: 6px; margin-bottom: 1rem; overflow: hidden; }
        .file-header { background: #f8f9fa; padding: 1rem; border-bottom: 1px solid #e9ecef; }
        .file-path { font-family: monospace; font-weight: bold; color: #495057; }
        .file-score { float: right; font-weight: bold; padding: 0.25rem 0.75rem; border-radius: 20px; color: white; }
        .score-excellent { background: #28a745; }
        .score-good { background: #20c997; }
        .score-fair { background: #ffc107; }
        .score-poor { background: #fd7e14; }
        .score-bad { background: #dc3545; }
        .file-content { padding: 1rem; }
        .summary { margin-bottom: 1rem; color: #6c757d; }
        .comments { margin-top: 1rem; }
        .comment { background: #f8f9fa; border-left: 4px solid; padding: 1rem; margin-bottom: 0.5rem; border-radius: 0 4px 4px 0; }
        .comment-high { border-left-color: #dc3545; }
        .comment-medium { border-left-color: #ffc107; }
        .comment-low { border-left-color: #28a745; }
        .comment-header { display: flex; justify-content: between; align-items: center; margin-bottom: 0.5rem; }
        .comment-title { font-weight: bold; }
        .comment-meta { font-size: 0.85rem; color: #6c757d; }
        .comment-description { margin-bottom: 0.5rem; }
        .suggestion { background: #e7f3ff; border: 1px solid #b8daff; border-radius: 4px; padding: 0.75rem; margin-top: 0.5rem; }
        .suggestion-title { font-weight: bold; color: #004085; margin-bottom: 0.25rem; }
        .suggestion code { background: #f8f9fa; padding: 0.25rem; border-radius: 3px; font-family: monospace; }
        .positive-aspects, .recommendations { margin-top: 1rem; }
        .positive-aspects h4, .recommendations h4 { color: #28a745; margin-bottom: 0.5rem; }
        .list-item { background: #d4edda; border: 1px solid #c3e6cb; padding: 0.5rem; margin-bottom: 0.25rem; border-radius: 4px; }
        .footer { text-align: center; color: #6c757d; margin-top: 2rem; }
        .chart-container { height: 300px; margin: 1rem 0; }
        .no-comments { color: #6c757d; font-style: italic; text-align: center; padding: 2rem; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Code Review Report</h1>
            <p>Generated on {{ generated_at }} | Project: {{ summary.project_id }}</p>
            {% if summary.merge_request_iid %}
            <p>Merge Request: #{{ summary.merge_request_iid }} | Commit: {{ summary.commit_sha[:8] }}</p>
            {% endif %}
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>Files Reviewed</h3>
                <div class="value">{{ summary.total_files_reviewed }}</div>
            </div>
            <div class="stat-card">
                <h3>Total Comments</h3>
                <div class="value">{{ summary.total_comments }}</div>
            </div>
            <div class="stat-card">
                <h3>Average Score</h3>
                <div class="value">{{ summary.average_score }}/10</div>
            </div>
            <div class="stat-card">
                <h3>High Severity</h3>
                <div class="value severity-high">{{ summary.severity_distribution.high }}</div>
            </div>
            <div class="stat-card">
                <h3>Medium Severity</h3>
                <div class="value severity-medium">{{ summary.severity_distribution.medium }}</div>
            </div>
            <div class="stat-card">
                <h3>Low Severity</h3>
                <div class="value severity-low">{{ summary.severity_distribution.low }}</div>
            </div>
        </div>

        <div class="section">
            <h2>📊 Review Summary</h2>
            <div class="summary">
                <p><strong>Review Scope:</strong> {{ summary.configuration.review_scope }}</p>
                <p><strong>Security Scanning:</strong> {{ "Enabled" if summary.configuration.security_scan_enabled else "Disabled" }}</p>
                <p><strong>Performance Hints:</strong> {{ "Enabled" if summary.configuration.performance_hints_enabled else "Disabled" }}</p>
                <p><strong>Severity Threshold:</strong> {{ summary.configuration.severity_threshold|title }}</p>
            </div>
            
            {% if summary.category_distribution %}
            <h4>Issues by Category</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;">
                {% for category, count in summary.category_distribution.items() %}
                <div class="stat-card">
                    <h3>{{ category_icons.get(category, '📋') }} {{ category|title }}</h3>
                    <div class="value">{{ count }}</div>
                </div>
                {% endfor %}
            </div>
            {% endif %}
        </div>

        <div class="section">
            <h2>📁 File Reviews</h2>
            {% if reviews %}
                {% for review in reviews %}
                    {% if review and review.review_result %}
                    <div class="file-review">
                        <div class="file-header">
                            <span class="file-path">{{ review.file_path }}</span>
                            {% set score = review.review_result.overall_score %}
                            <span class="file-score 
                                {% if score >= 9 %}score-excellent
                                {% elif score >= 7 %}score-good  
                                {% elif score >= 5 %}score-fair
                                {% elif score >= 3 %}score-poor
                                {% else %}score-bad{% endif %}">
                                {{ score }}/10
                            </span>
                        </div>
                        <div class="file-content">
                            {% if review.review_result.summary %}
                            <div class="summary">{{ review.review_result.summary }}</div>
                            {% endif %}
                            
                            {% if review.review_result.comments %}
                            <div class="comments">
                                <h4>Comments ({{ review.review_result.comments|length }})</h4>
                                {% for comment in review.review_result.comments %}
                                <div class="comment comment-{{ comment.severity }}">
                                    <div class="comment-header">
                                        <span class="comment-title">
                                            {{ category_icons.get(comment.category, '📋') }}
                                            {{ comment.title }}
                                        </span>
                                        <span class="comment-meta">
                                            {{ comment.severity|title }} • {{ comment.category|title }}
                                            {% if comment.line_number %} • Line {{ comment.line_number }}{% endif %}
                                        </span>
                                    </div>
                                    <div class="comment-description">{{ comment.description }}</div>
                                    {% if comment.suggestion %}
                                    <div class="suggestion">
                                        <div class="suggestion-title">💡 Suggestion:</div>
                                        <code>{{ comment.suggestion }}</code>
                                    </div>
                                    {% endif %}
                                    {% if comment.impact %}
                                    <div style="margin-top: 0.5rem; font-size: 0.9rem; color: #6c757d;">
                                        <strong>Impact:</strong> {{ comment.impact }}
                                    </div>
                                    {% endif %}
                                </div>
                                {% endfor %}
                            </div>
                            {% endif %}
                            
                            {% if review.review_result.positive_aspects %}
                            <div class="positive-aspects">
                                <h4>✅ Positive Aspects</h4>
                                {% for aspect in review.review_result.positive_aspects %}
                                <div class="list-item">{{ aspect }}</div>
                                {% endfor %}
                            </div>
                            {% endif %}
                            
                            {% if review.review_result.recommendations %}
                            <div class="recommendations">
                                <h4>💡 Recommendations</h4>
                                {% for rec in review.review_result.recommendations %}
                                <div class="list-item">{{ rec }}</div>
                                {% endfor %}
                            </div>
                            {% endif %}
                        </div>
                    </div>
                    {% endif %}
                {% endfor %}
            {% else %}
                <div class="no-comments">
                    <p>No files were reviewed or no issues were found.</p>
                </div>
            {% endif %}
        </div>

        <div class="footer">
            <p>🤖 Generated by AI-Powered Code Review using Gemini 2.5 Flash</p>
            <p>GitLab Hackathon Submission</p>
        </div>
    </div>
</body>
</html>
        '''
        return Template(template_str) 