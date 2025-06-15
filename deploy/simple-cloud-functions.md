# 🚀 Super Simple Deployment (No Docker Required!)

The easiest way to deploy your AI Code Review for the GitLab Hackathon.

## ✨ Option 1: Google Cloud Functions (Recommended for Simplicity)

Cloud Functions can deploy directly from your source code - no Docker needed!

### Quick Setup (5 minutes)

1. **Set your project ID:**
   ```powershell
   $PROJECT_ID = "your-google-cloud-project-id"
   gcloud config set project $PROJECT_ID
   ```

2. **Enable required APIs:**
   ```powershell
   gcloud services enable cloudfunctions.googleapis.com
   gcloud services enable aiplatform.googleapis.com
   ```

3. **Deploy the function directly from source:**
   ```powershell
   gcloud functions deploy ai-code-review `
     --runtime python311 `
     --trigger-http `
     --entry-point webhook_handler `
     --source scripts/ `
     --allow-unauthenticated `
     --set-env-vars="GEMINI_API_KEY=your-api-key,GITLAB_TOKEN=your-gitlab-token" `
     --memory 1GB `
     --timeout 540
   ```

4. **Get your webhook URL:**
   ```powershell
   gcloud functions describe ai-code-review --format="value(httpsTrigger.url)"
   ```

That's it! No Docker, no complex setup needed.

## ✨ Option 2: Google App Engine (Even simpler!)

App Engine can deploy directly from a simple `app.yaml` file:

### Create `app.yaml`:
```yaml
runtime: python311

env_variables:
  GEMINI_API_KEY: "your-api-key"
  GITLAB_TOKEN: "your-gitlab-token"

automatic_scaling:
  min_instances: 0
  max_instances: 10
```

### Deploy:
```powershell
gcloud app deploy app.yaml
```

## ✨ Option 3: Cloud Build with Buildpacks (No Dockerfile needed)

Google Cloud can automatically detect your Python app and build it:

### Create `.gcloudignore`:
```
node_modules/
.git/
.gitignore
README.md
docs/
examples/
```

### Deploy:
```powershell
gcloud run deploy ai-code-review `
  --source . `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --set-env-vars="GEMINI_API_KEY=your-api-key,GITLAB_TOKEN=your-gitlab-token"
```

This automatically builds and deploys without any Docker files!

## 🎯 Which Option to Choose?

- **Cloud Functions**: Simplest, pay-per-request, perfect for webhooks
- **App Engine**: Easy, good for web apps, automatic scaling
- **Cloud Run (with buildpacks)**: Most flexible, containers without Docker complexity
- **Cloud Run (with Docker)**: Full control, but more complex

For the hackathon, I recommend **Cloud Functions** - it's the simplest and works perfectly for webhook-based code reviews. 