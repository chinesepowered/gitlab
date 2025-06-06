# Setup Guide

This guide will help you set up the AI-Powered Code Review component in your GitLab project.

## Prerequisites

1. **GitLab Project**: A GitLab project with CI/CD enabled
2. **Google Cloud Account**: Access to Google Cloud with Gemini API enabled
3. **API Keys**: Required API keys and access tokens

## Step 1: Get API Keys

### Google Cloud / Gemini API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Generative AI API
4. Go to "APIs & Services" > "Credentials"
5. Click "Create Credentials" > "API Key"
6. Copy your API key (keep it secure!)

### GitLab Access Token

1. Go to your GitLab project
2. Navigate to Settings > Access Tokens
3. Create a project access token with these scopes:
   - `api` (to read files and post comments)
   - `read_repository` (to access repository content)
   - `write_repository` (to post merge request comments)
4. Copy the generated token

## Step 2: Configure CI/CD Variables

In your GitLab project:

1. Go to Settings > CI/CD > Variables
2. Add these variables:
   - `GEMINI_API_KEY`: Your Google Cloud API key (mark as protected and masked)
   - `GITLAB_ACCESS_TOKEN`: Your GitLab access token (mark as protected and masked)

## Step 3: Add Component to Your Pipeline

Create or update your `.gitlab-ci.yml` file:

```yaml
include:
  - component: gitlab.com/your-namespace/ai-code-review/ai-review@main

stages:
  - ai-review
  - test
  - deploy

ai-code-review:
  extends: .ai-code-review
  variables:
    GEMINI_API_KEY: $GEMINI_API_KEY
    GITLAB_TOKEN: $GITLAB_ACCESS_TOKEN
```

## Step 4: Test the Setup

1. Create a merge request with some code changes
2. Push commits to trigger the pipeline
3. Check the pipeline logs for the AI review job
4. Look for review comments on your merge request
5. Download the generated HTML report from job artifacts

## Configuration Options

### Basic Configuration

```yaml
ai-code-review:
  extends: .ai-code-review
  variables:
    GEMINI_API_KEY: $GEMINI_API_KEY
    GITLAB_TOKEN: $GITLAB_ACCESS_TOKEN
    REVIEW_SCOPE: "changed"              # "changed" or "all"
    MAX_FILES: "50"                      # Maximum files to review
    SEVERITY_THRESHOLD: "medium"         # "low", "medium", or "high"
```

### Advanced Configuration

```yaml
ai-code-review:
  extends: .ai-code-review
  variables:
    GEMINI_API_KEY: $GEMINI_API_KEY
    GITLAB_TOKEN: $GITLAB_ACCESS_TOKEN
    LANGUAGES: "python,javascript,go"   # Specific languages only
    INCLUDE_PATTERNS: "src/,lib/"       # Include specific directories
    EXCLUDE_PATTERNS: "tests/,docs/"    # Exclude specific directories
    ENABLE_SECURITY_SCAN: "true"        # Enable security analysis
    ENABLE_PERFORMANCE_HINTS: "true"    # Enable performance suggestions
    POST_MR_COMMENTS: "true"            # Post comments on MR
    GENERATE_REPORT: "true"             # Generate HTML/JSON reports
```

## Troubleshooting

### Common Issues

1. **"Missing API key" error**
   - Verify `GEMINI_API_KEY` is set in CI/CD variables
   - Check that the variable is not masked if debugging

2. **"GitLab API access denied"**
   - Verify `GITLAB_TOKEN` has correct permissions
   - Ensure token is not expired

3. **No comments posted on MR**
   - Check if `POST_MR_COMMENTS` is set to "true"
   - Verify severity threshold settings
   - Check GitLab token permissions

4. **Pipeline fails with timeout**
   - Reduce `MAX_FILES` value
   - Use `INCLUDE_PATTERNS` to focus on specific directories

### Debug Mode

Enable debug logging by adding:

```yaml
variables:
  CI_DEBUG_TRACE: "true"
```

This will show detailed logs of the AI review process.

## Security Considerations

1. **API Keys**: Always mark API keys as protected and masked
2. **Permissions**: Use minimal required permissions for GitLab tokens
3. **Review Scope**: Consider using `INCLUDE_PATTERNS` to avoid reviewing sensitive files
4. **Rate Limits**: Be aware of Gemini API rate limits for large repositories

## Next Steps

- Check out [examples/](../examples/) for more configuration examples
- Read [CUSTOMIZATION.md](CUSTOMIZATION.md) for advanced customization options
- See [API.md](API.md) for details on extending the component 