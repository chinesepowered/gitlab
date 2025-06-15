#!/usr/bin/env pwsh
# Debug GitLab API access for AI Code Review

Write-Host "🔍 GitLab API Debug Tool" -ForegroundColor Green

# Get project information
$projectId = Read-Host "Enter your GitLab Project ID"
$mrIid = Read-Host "Enter the Merge Request IID"

Write-Host "`n🧪 Testing GitLab API access..." -ForegroundColor Blue

# Test 1: Basic project access
Write-Host "`n1️⃣ Testing project access..." -ForegroundColor Yellow
$projectPayload = @{
    object_kind = "test"
    project = @{
        id = [int]$projectId
        web_url = "https://gitlab.com/test"
    }
} | ConvertTo-Json -Depth 10

try {
    $response1 = Invoke-RestMethod -Uri "https://asia-east2-hack-458102.cloudfunctions.net/ai-code-review" `
        -Method POST `
        -ContentType "application/json" `
        -Body $projectPayload

    Write-Host "✅ Project access test response:" -ForegroundColor Green
    $response1 | ConvertTo-Json -Depth 10
} catch {
    Write-Host "❌ Project access failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

# Test 2: MR webhook with minimal data
Write-Host "`n2️⃣ Testing MR webhook (minimal)..." -ForegroundColor Yellow
$minimalPayload = @{
    object_kind = "merge_request"
    object_attributes = @{
        iid = [int]$mrIid
        action = "open"
        last_commit = @{
            id = "test-commit-sha"
        }
        author = @{
            username = "test-user"
        }
    }
    project = @{
        id = [int]$projectId
        web_url = "https://gitlab.com/test-project"
    }
} | ConvertTo-Json -Depth 10

try {
    $response2 = Invoke-RestMethod -Uri "https://asia-east2-hack-458102.cloudfunctions.net/ai-code-review" `
        -Method POST `
        -ContentType "application/json" `
        -Body $minimalPayload

    Write-Host "✅ Minimal MR webhook response:" -ForegroundColor Green
    $response2 | ConvertTo-Json -Depth 10
} catch {
    Write-Host "❌ Minimal MR webhook failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

# Test 3: Check if your MR actually has file changes
Write-Host "`n3️⃣ Manual GitLab API test..." -ForegroundColor Yellow
Write-Host "Please check your GitLab merge request manually:"
Write-Host "1. Go to your MR: https://gitlab.com/your-project/-/merge_requests/$mrIid"
Write-Host "2. Click on 'Changes' tab"
Write-Host "3. Verify there are actual file changes shown"
Write-Host "4. Check if the files are in supported languages (py, js, ts, java, go, etc.)"

# Test 4: Environment variable check
Write-Host "`n4️⃣ Checking function environment..." -ForegroundColor Yellow
$envPayload = @{
    object_kind = "debug"
    debug_action = "check_env"
} | ConvertTo-Json -Depth 10

try {
    $response4 = Invoke-RestMethod -Uri "https://asia-east2-hack-458102.cloudfunctions.net/ai-code-review" `
        -Method POST `
        -ContentType "application/json" `
        -Body $envPayload

    Write-Host "✅ Environment check response:" -ForegroundColor Green
    $response4 | ConvertTo-Json -Depth 10
} catch {
    Write-Host "❌ Environment check failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Check the Cloud Function logs: https://console.cloud.google.com/functions/details/asia-east2/ai-code-review?project=hack-458102&tab=logs"
Write-Host "2. Verify your GitLab token has 'api' and 'read_repository' scopes"
Write-Host "3. Ensure your MR has actual file changes"
Write-Host "4. Check if files are in supported languages"

Write-Host "`n🔧 Common Issues:" -ForegroundColor Magenta
Write-Host "• Empty MR (no file changes)"
Write-Host "• GitLab token lacks permissions"
Write-Host "• Files filtered out by language/pattern matching"
Write-Host "• Project ID mismatch" 