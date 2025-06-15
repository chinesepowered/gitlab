@echo off
echo Deploying AI Code Review Function with Enhanced Debugging...

gcloud functions deploy ai-code-review ^
  --gen2 ^
  --runtime=python311 ^
  --trigger=http ^
  --entry-point=webhook_handler ^
  --source=scripts/ ^
  --allow-unauthenticated ^
  --set-env-vars="GEMINI_API_KEY=AIzaSyDU89iunQ3Du9tLdZ2VIwll6-gG8BKbq7M,GITLAB_TOKEN=glpat-ADAtKZzcn5mgx-uzqxrr" ^
  --memory=1GB ^
  --timeout=540s ^
  --max-instances=10 ^
  --region=asia-east2

echo.
echo Deployment complete! Test with:
echo .\test-debug.ps1
pause 