# Google Cloud Deployment Guide

This guide covers deploying the AI-Powered Code Review component on Google Cloud for the GitLab Hackathon.

## 🌟 Overview

The component can run in two modes:
1. **GitLab CI/CD Mode**: Traditional CI/CD job execution (original functionality)
2. **Cloud Run Service Mode**: Web service with webhook support for real-time reviews

## 🚀 Quick Deployment

### Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Google Cloud SDK** installed and configured
3. **Docker** installed
4. **Required APIs** enabled (handled by setup script)

### One-Click Setup

```bash
# Make setup script executable
chmod +x deploy/setup-gcp.sh

# Run the setup
./deploy/setup-gcp.sh
```

This script will:
- ✅ Enable required Google Cloud APIs
- ✅ Create service accounts with proper permissions
- ✅ Build and deploy the Docker image
- ✅ Deploy to Cloud Run
- ✅ Provide setup instructions

## 🏗️ Manual Deployment

### Step 1: Enable APIs

```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  containerregistry.googleapis.com \
  aiplatform.googleapis.com
```

### Step 2: Create Service Account

```bash
# Create service account
gcloud iam service-accounts create ai-code-reviewer \
  --description="AI Code Review service account" \
  --display-name="AI Code Reviewer"

# Add required permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:ai-code-reviewer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:ai-code-reviewer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"
```

### Step 3: Build and Deploy

```bash
# Build with Cloud Build
gcloud builds submit --config=cloudbuild.yaml

# The cloudbuild.yaml handles the deployment automatically
```

### Step 4: Configure Environment Variables

```bash
gcloud run services update ai-code-review \
  --region=us-central1 \
  --set-env-vars="GEMINI_API_KEY=your-api-key,GITLAB_TOKEN=your-gitlab-token"
```

## 🔐 Authentication Methods

The component supports multiple authentication methods for flexibility:

### 1. Service Account (Recommended for Cloud Run)

```bash
# Service account is automatically used when deployed on Cloud Run
# No additional configuration needed
```

### 2. API Key (Fallback)

```bash
# Set as environment variable
export GEMINI_API_KEY="your-api-key"
```

### 3. Application Default Credentials

```bash
# Automatically used on Google Cloud services
gcloud auth application-default login
```

## 🪝 Webhook Integration

### Setup GitLab Webhook

1. Go to your GitLab project → **Settings** → **Webhooks**
2. Add webhook:
   - **URL**: `https://your-service-url/webhook/gitlab`
   - **Trigger**: Merge request events
   - **Secret Token**: (optional, set `GITLAB_WEBHOOK_SECRET` env var)

### Webhook Features

- **Real-time processing**: Reviews are triggered immediately on MR events
- **Concurrent handling**: Multiple reviews can run simultaneously
- **Status tracking**: Check review progress via `/review/status/<id>`
- **Manual triggering**: Use `/review/manual` endpoint for testing

## 📊 Monitoring and Logging

### Health Checks

```bash
# Check service health
curl https://your-service-url/health

# Get service statistics
curl https://your-service-url/stats
```

### Cloud Logging

```bash
# View logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=ai-code-review" \
  --limit=50 \
  --format="table(timestamp,severity,textPayload)"
```

### Monitoring Dashboard

Access metrics in Google Cloud Console:
1. Go to **Cloud Run** → **ai-code-review**
2. Click **Metrics** tab
3. Monitor requests, latency, and errors

## 🔧 Configuration Options

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `GEMINI_API_KEY` | Yes* | Google AI API key | - |
| `GITLAB_TOKEN` | Yes | GitLab access token | - |
| `GOOGLE_CLOUD_PROJECT` | No | GCP Project ID | Auto-detected |
| `PORT` | No | Server port | `8080` |
| `MAX_CONCURRENT_REVIEWS` | No | Max parallel reviews | `3` |
| `GITLAB_WEBHOOK_SECRET` | No | Webhook security token | - |

*Not required if using service account authentication

### Resource Configuration

```yaml
# cloud-run.yml
resources:
  limits:
    cpu: "1000m"
    memory: "2Gi"
  requests:
    cpu: "500m"
    memory: "1Gi"
```

## 🧪 Testing the Deployment

### 1. Health Check

```bash
curl https://your-service-url/health
```

Expected response:
```json
{
  "status": "healthy",
  "authentication": {
    "method": "service_account",
    "authenticated": true
  }
}
```

### 2. Manual Review Test

```bash
curl -X POST https://your-service-url/review/manual \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "123",
    "mr_iid": "456",
    "commit_sha": "abc123"
  }'
```

### 3. Webhook Test

Create a test merge request in your GitLab project and verify:
- Webhook is triggered
- Review starts automatically
- Comments appear on the MR
- Reports are generated

## 🔄 GitLab CI/CD Integration

You can still use the component in traditional CI/CD mode:

```yaml
# .gitlab-ci.yml
include:
  - component: gitlab.com/your-namespace/ai-code-review@main

ai-code-review:
  extends: .ai-code-review
  image: gcr.io/YOUR_PROJECT_ID/ai-code-review:latest
  variables:
    GEMINI_API_KEY: $GEMINI_API_KEY
    GITLAB_TOKEN: $GITLAB_ACCESS_TOKEN
```

## 📈 Scaling and Performance

### Auto-scaling

Cloud Run automatically scales based on:
- **Requests per second**
- **CPU utilization**  
- **Memory usage**

Configuration:
```yaml
autoscaling.knative.dev/maxScale: "10"
autoscaling.knative.dev/minScale: "0"
```

### Performance Optimization

1. **Concurrent Reviews**: Limited to 3 by default to manage costs
2. **Cold Start Optimization**: Keep 1 instance warm during business hours
3. **Resource Limits**: 2Gi memory, 1 CPU core per instance
4. **Request Timeout**: 3600 seconds for large reviews

## 💰 Cost Optimization

### Estimated Costs

- **Cloud Run**: ~$0.10 per review (varies by code size)
- **Gemini API**: ~$0.002 per 1K tokens
- **Cloud Build**: ~$0.003 per build minute
- **Storage**: Minimal for artifacts

### Cost Management

1. **Set max instances**: Limit concurrent reviews
2. **Use min instances = 0**: No idle costs
3. **Monitor API usage**: Track Gemini API calls
4. **Set up budgets**: Alert when costs exceed thresholds

## 🔍 Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   # Check service account permissions
   gcloud projects get-iam-policy YOUR_PROJECT_ID \
     --flatten="bindings[].members" \
     --filter="bindings.members:ai-code-reviewer@YOUR_PROJECT_ID.iam.gserviceaccount.com"
   ```

2. **Memory Issues**
   ```bash
   # Increase memory limit
   gcloud run services update ai-code-review \
     --memory=4Gi --region=us-central1
   ```

3. **Timeout Issues**
   ```bash
   # Increase timeout
   gcloud run services update ai-code-review \
     --timeout=3600 --region=us-central1
   ```

### Debug Mode

```bash
# Enable debug logging
gcloud run services update ai-code-review \
  --set-env-vars="FLASK_DEBUG=true" \
  --region=us-central1
```

## 🏆 Hackathon Submission

This deployment is optimized for the GitLab Hackathon with:

- ✅ **Google Cloud Native**: Full Cloud Run deployment
- ✅ **Scalable Architecture**: Auto-scaling with concurrent reviews
- ✅ **Real-time Integration**: Webhook-based immediate reviews
- ✅ **Cost Efficient**: Pay-per-use with automatic scaling to zero
- ✅ **Production Ready**: Health checks, monitoring, and logging
- ✅ **Secure**: Service account authentication and webhook secrets

## 📞 Support

For deployment issues:
1. Check Cloud Run logs: `gcloud logs read`
2. Verify service account permissions
3. Test authentication with `/health` endpoint
4. Monitor resource usage in Cloud Console

---

**🤖 AI-Powered Code Review - GitLab Hackathon Submission** 