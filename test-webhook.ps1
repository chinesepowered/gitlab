#!/usr/bin/env pwsh
# Test webhook script for AI Code Review

Write-Host "🧪 Testing AI Code Review Webhook" -ForegroundColor Green

# Get your GitLab project ID
Write-Host "First, we need your GitLab project information:" -ForegroundColor Yellow
$projectId = Read-Host "Enter your GitLab Project ID (found in project settings)"
$mrIid = Read-Host "Enter the Merge Request IID (number from MR URL)"

# Create test payload
$payload = @{
    object_kind = "merge_request"
    object_attributes = @{
        iid = [int]$mrIid
        action = "open"
        last_commit = @{
            id = "abc123"
        }
        author = @{
            username = "test-user"
        }
    }
    project = @{
        id = [int]$projectId
        web_url = "https://gitlab.com/your-project"
    }
} | ConvertTo-Json -Depth 10

Write-Host "📤 Sending test webhook..." -ForegroundColor Blue

try {
    $response = Invoke-RestMethod -Uri "https://asia-east2-hack-458102.cloudfunctions.net/ai-code-review" `
        -Method POST `
        -ContentType "application/json" `
        -Body $payload

    Write-Host "✅ Success! Response:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "❌ Error:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    Write-Host "Response:" $_.Exception.Response
}

Write-Host "`n🔍 Check the Cloud Function logs at:" -ForegroundColor Cyan
Write-Host "https://console.cloud.google.com/functions/details/asia-east2/ai-code-review?project=hack-458102&tab=logs" 