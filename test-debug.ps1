#!/usr/bin/env pwsh
# Test the enhanced debugging version

Write-Host "🔍 Testing Enhanced Debug Version" -ForegroundColor Green

$projectId = 70831895
$mrIid = 2

Write-Host "📤 Sending webhook to trigger detailed logging..." -ForegroundColor Blue

$payload = @{
    object_kind = "merge_request"
    object_attributes = @{
        iid = [int]$mrIid
        action = "open"
        title = "Test MR for AI Review"
        source_branch = "feature-branch"
        target_branch = "main"
        last_commit = @{
            id = "abc123def456"
        }
        author = @{
            username = "test-user"
            name = "Test User"
        }
    }
    project = @{
        id = [int]$projectId
        web_url = "https://gitlab.com/test-project"
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "https://asia-east2-hack-458102.cloudfunctions.net/ai-code-review" `
        -Method POST `
        -ContentType "application/json" `
        -Body $payload

    Write-Host "✅ Response:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 10
    
    Write-Host "`n🔍 Now check the detailed logs at:" -ForegroundColor Cyan
    Write-Host "https://console.cloud.google.com/functions/details/asia-east2/ai-code-review?project=hack-458102&tab=logs"
    
    Write-Host "`n📋 Look for these debug messages in the logs:" -ForegroundColor Yellow
    Write-Host "• 🔍 Getting files for MR..."
    Write-Host "• 📁 GitLab API returned X changed files"
    Write-Host "• 📄 File 1: [filename]"
    Write-Host "• 🔧 Applying filters..."
    Write-Host "• ✅ After filtering: X files remain"
    
} catch {
    Write-Host "❌ Error:" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

Write-Host "`n💡 If you see '📁 GitLab API returned 0 changed files':" -ForegroundColor Magenta
Write-Host "   → Your MR has no file changes"
Write-Host "   → Add/edit a file in your MR and try again"

Write-Host "`n💡 If you see files but '✅ After filtering: 0 files remain':" -ForegroundColor Magenta
Write-Host "   → Files are being filtered out"
Write-Host "   → Check file extensions and language support" 