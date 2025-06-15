#!/usr/bin/env pwsh
# Super Simple Deployment for AI Code Review (No Docker Required!)
# GitLab Hackathon Submission

Write-Host "🚀 AI Code Review - Simple Cloud Functions Deployment" -ForegroundColor Blue
Write-Host "GitLab Hackathon Submission" -ForegroundColor Blue

# Get configuration
if ([string]::IsNullOrEmpty($env:GOOGLE_CLOUD_PROJECT)) {
    $PROJECT_ID = Read-Host "Enter your Google Cloud Project ID"
} else {
    $PROJECT_ID = $env:GOOGLE_CLOUD_PROJECT
}

Write-Host "`n📋 Project: $PROJECT_ID" -ForegroundColor Green

# Set project
Write-Host "`n⚙️  Setting up project..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

# Enable APIs
Write-Host "`n🔌 Enabling APIs..." -ForegroundColor Yellow
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable aiplatform.googleapis.com

# Get API keys from user
Write-Host "`n🔑 API Configuration" -ForegroundColor Yellow
$GEMINI_API_KEY = Read-Host "Enter your Gemini API Key" -AsSecureString
$GITLAB_TOKEN = Read-Host "Enter your GitLab Access Token" -AsSecureString

# Convert secure strings to plain text for gcloud
$GEMINI_API_KEY_TEXT = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($GEMINI_API_KEY))
$GITLAB_TOKEN_TEXT = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($GITLAB_TOKEN))

# Ensure main.py exists (required by Cloud Functions)
if (-not (Test-Path "scripts/main.py")) {
    Write-Host "Creating main.py entry point..." -ForegroundColor Cyan
    @"
#!/usr/bin/env python3
from cloud_function_main import webhook_handler
"@ | Out-File -FilePath "scripts/main.py" -Encoding UTF8
}

# Deploy Cloud Function
Write-Host "`n🚀 Deploying Cloud Function..." -ForegroundColor Yellow
Write-Host "This will take a few minutes..." -ForegroundColor Cyan

gcloud functions deploy ai-code-review `
  --gen2 `
  --runtime python311 `
  --trigger-http `
  --entry-point webhook_handler `
  --source scripts/ `
  --allow-unauthenticated `
  --set-env-vars="GEMINI_API_KEY=$GEMINI_API_KEY_TEXT,GITLAB_TOKEN=$GITLAB_TOKEN_TEXT" `
  --memory 1GB `
  --timeout 540s `
  --max-instances 10 `
  --region asia-east2

# Get function URL
Write-Host "`n🌐 Getting function URL..." -ForegroundColor Yellow
$FUNCTION_URL = gcloud functions describe ai-code-review --region=asia-east2 --format="value(serviceConfig.uri)"

Write-Host "`n✅ Deployment Complete!" -ForegroundColor Green
Write-Host "Function URL: $FUNCTION_URL" -ForegroundColor Cyan
Write-Host "Health Check: $FUNCTION_URL/health" -ForegroundColor Cyan

# Test health check
Write-Host "`n🧪 Testing deployment..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$FUNCTION_URL/health" -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Health check passed!" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Health check pending (function may still be starting up)" -ForegroundColor Yellow
}

# GitLab webhook setup instructions
Write-Host "`n🪝 GitLab Webhook Setup:" -ForegroundColor Yellow
Write-Host "1. Go to your GitLab project → Settings → Webhooks" -ForegroundColor White
Write-Host "2. Add webhook URL: $FUNCTION_URL" -ForegroundColor Cyan
Write-Host "3. Select 'Merge request events'" -ForegroundColor White
Write-Host "4. Save the webhook" -ForegroundColor White

Write-Host "`n🎉 Your AI Code Review is ready!" -ForegroundColor Green
Write-Host "Perfect for GitLab Hackathon submission!" -ForegroundColor Magenta

# Clean up sensitive variables
$GEMINI_API_KEY_TEXT = $null
$GITLAB_TOKEN_TEXT = $null 