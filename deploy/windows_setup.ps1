#!/usr/bin/env pwsh
# Google Cloud setup script for AI Code Review hackathon submission on Windows PowerShell
# This script sets up all necessary GCP resources

# Colors for output
$RED = "\u001b[31m"
$GREEN = "\u001b[32m"
$YELLOW = "\u001b[33m"
$BLUE = "\u001b[34m"
$NC = "\u001b[0m" # No Color

Write-Host "$($BLUE)🚀 Setting up AI Code Review on Google Cloud$($NC)"
Write-Host "$($BLUE)GitLab Hackathon Submission$($NC)"

# Check if required tools are installed
function Check-Requirements {
    Write-Host "`n$($YELLOW)📋 Checking requirements...$($NC)"
    
    if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
        Write-Host "$($RED)❌ gcloud CLI not found. Please install it first.$($NC)"
        exit 1
    }
    
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Host "$($RED)❌ Docker not found. Please install it first.$($NC)"
        exit 1
    }
    
    Write-Host "$($GREEN)✅ All requirements satisfied$($NC)"
}

# Get project configuration
function Get-Config {
    Write-Host "`n$($YELLOW)⚙️  Configuration$($NC)"
    
    # Get or set project ID
    if ([string]::IsNullOrEmpty($env:GOOGLE_CLOUD_PROJECT)) {
        $PROJECT_ID = Read-Host "Enter your Google Cloud Project ID"
    } else {
        $PROJECT_ID = $env:GOOGLE_CLOUD_PROJECT
    }
    
    # Set default region
    $REGION = $env:REGION -or "asia-east2"
    
    # Service names
    $SERVICE_NAME = "ai-code-review"
    $SERVICE_ACCOUNT_NAME = "ai-code-reviewer"
    
    Write-Host "Project ID: $($GREEN)$PROJECT_ID$($NC)"
    Write-Host "Region: $($GREEN)$REGION$($NC)"
    Write-Host "Service: $($GREEN)$SERVICE_NAME$($NC)"
    
    # Export for other functions
    $script:PROJECT_ID = $PROJECT_ID
    $script:REGION = $REGION
    $script:SERVICE_NAME = $SERVICE_NAME
    $script:SERVICE_ACCOUNT_NAME = $SERVICE_ACCOUNT_NAME
}

# Enable required APIs
function Enable-Apis {
    Write-Host "`n$($YELLOW)🔌 Enabling required APIs...$($NC)"
    
    gcloud services enable `
        cloudbuild.googleapis.com `
        run.googleapis.com `
        containerregistry.googleapis.com `
        aiplatform.googleapis.com `
        --project=$script:PROJECT_ID
    
    Write-Host "$($GREEN)✅ APIs enabled$($NC)"
}

# Create service account
function Create-ServiceAccount {
    Write-Host "`n$($YELLOW)👤 Creating service account...$($NC)"
    
    # Create service account
    gcloud iam service-accounts create $script:SERVICE_ACCOUNT_NAME `
        --description="AI Code Review service account" `
        --display-name="AI Code Reviewer" `
        --project=$script:PROJECT_ID -ErrorAction SilentlyContinue # Ignores error if already exists
    
    # Add required roles
    gcloud projects add-iam-policy-binding $script:PROJECT_ID `
        --member="serviceAccount:$($script:SERVICE_ACCOUNT_NAME)@$($script:PROJECT_ID).iam.gserviceaccount.com" `
        --role="roles/aiplatform.user"
    
    gcloud projects add-iam-policy-binding $script:PROJECT_ID `
        --member="serviceAccount:$($script:SERVICE_ACCOUNT_NAME)@$($script:PROJECT_ID).iam.gserviceaccount.com" `
        --role="roles/logging.logWriter"
    
    gcloud projects add-iam-policy-binding $script:PROJECT_ID `
        --member="serviceAccount:$($script:SERVICE_ACCOUNT_NAME)@$($script:PROJECT_ID).iam.gserviceaccount.com" `
        --role="roles/monitoring.metricWriter"
    
    Write-Host "$($GREEN)✅ Service account created$($NC)"
}

# Build and deploy
function Build-And-Deploy {
    Write-Host "`n$($YELLOW)🏗️  Building and deploying...$($NC)"
    
    # Build with Cloud Build
    gcloud builds submit `
        --config=cloudbuild.yaml `
        --project=$script:PROJECT_ID `
        --substitutions=_REGION=$script:REGION,_SERVICE_NAME=$script:SERVICE_NAME
    
    Write-Host "$($GREEN)✅ Build and deployment completed$($NC)"
}

# Set environment variables instructions
function Setup-Env-Vars {
    Write-Host "`n$($YELLOW)🔐 Setting up environment variables...$($NC)"
    
    Write-Host "You'll need to set these environment variables in Cloud Run:"
    Write-Host "1. GEMINI_API_KEY - Your Google AI API key"
    Write-Host "2. GITLAB_TOKEN - GitLab access token"
    Write-Host "3. GITLAB_WEBHOOK_SECRET - (Optional) Webhook secret for security"
    Write-Host ""
    Write-Host "Run this command to update the Cloud Run service:"
    Write-Host ""
    Write-Host "$($BLUE)gcloud run services update $($script:SERVICE_NAME) \`
  --region=$($script:REGION) \`
  --set-env-vars=\`"GEMINI_API_KEY=your-api-key,GITLAB_TOKEN=your-gitlab-token\`" \`
  --project=$($script:PROJECT_ID)$($NC)"
}

# Get service URL
function Get-Service-Url {
    Write-Host "`n$($YELLOW)🌐 Getting service URL...$($NC)"
    
    $SERVICE_URL = gcloud run services describe $script:SERVICE_NAME `
        --region=$script:REGION `
        --project=$script:PROJECT_ID `
        --format="value(status.url)"
    
    Write-Host "$($GREEN)✅ Service deployed at: $($SERVICE_URL)$($NC)"
    Write-Host "$($GREEN)📊 Health check: $($SERVICE_URL)/health$($NC)"
    Write-Host "$($GREEN)🪝 Webhook URL: $($SERVICE_URL)/webhook/gitlab$($NC)"
    
    $script:SERVICE_URL = $SERVICE_URL
}

# Create GitLab webhook instructions
function Create-Webhook-Instructions {
    Write-Host "`n$($YELLOW)🪝 GitLab Webhook Setup$($NC)"
    Write-Host "To complete the setup, add a webhook in your GitLab project:"
    Write-Host ""
    Write-Host "1. Go to your GitLab project → Settings → Webhooks"
    Write-Host "2. Add new webhook with:"
    Write-Host "   URL: $($BLUE)$($script:SERVICE_URL)/webhook/gitlab$($NC)"
    Write-Host "   Trigger: Merge request events"
    Write-Host "   Secret Token: (optional, set GITLAB_WEBHOOK_SECRET if used)"
    Write-Host ""
}

# Test deployment
function Test-Deployment {
    Write-Host "`n$($YELLOW)🧪 Testing deployment...$($NC)"
    
    # Test health endpoint
    try {
        $response = Invoke-WebRequest -Uri "$($script:SERVICE_URL)/health" -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "$($GREEN)✅ Health check passed$($NC)"
        } else {
            Write-Host "$($RED)❌ Health check failed with status code $($response.StatusCode)$($NC)"
            Write-Host "Check the Cloud Run logs for details"
        }
    } catch {
        Write-Host "$($RED)❌ Health check failed: $($_.Exception.Message)$($NC)"
        Write-Host "Check the Cloud Run logs for details"
    }
}

# Main execution
function Main {
    Check-Requirements
    Get-Config
    
    # Set the project
    gcloud config set project $script:PROJECT_ID
    
    Enable-Apis
    Create-ServiceAccount
    Build-And-Deploy
    Get-Service-Url
    Setup-Env-Vars
    Create-Webhook-Instructions
    Test-Deployment
    
    Write-Host "`n$($GREEN)🎉 Setup completed!$($NC)"
    Write-Host "$($GREEN)Your AI Code Review service is ready for the GitLab Hackathon!$($NC)"
    Write-Host "`n$($BLUE)Next steps:$($NC)"
    Write-Host "1. Set the environment variables in Cloud Run"
    Write-Host "2. Add the webhook to your GitLab project"
    Write-Host "3. Test with a merge request"
    Write-Host "4. Submit to GitLab CI/CD Catalog"
}

# Run main function
Main 