#!/bin/bash

# Google Cloud setup script for AI Code Review hackathon submission
# This script sets up all necessary GCP resources

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up AI Code Review on Google Cloud${NC}"
echo -e "${BLUE}GitLab Hackathon Submission${NC}"

# Check if required tools are installed
check_requirements() {
    echo -e "\n${YELLOW}📋 Checking requirements...${NC}"
    
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found. Please install it first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All requirements satisfied${NC}"
}

# Get project configuration
get_config() {
    echo -e "\n${YELLOW}⚙️  Configuration${NC}"
    
    # Get or set project ID
    if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
        read -p "Enter your Google Cloud Project ID: " PROJECT_ID
    else
        PROJECT_ID=$GOOGLE_CLOUD_PROJECT
    fi
    
    # Set default region
    REGION=${REGION:-"us-central1"}
    
    # Service names
    SERVICE_NAME="ai-code-review"
    SERVICE_ACCOUNT_NAME="ai-code-reviewer"
    
    echo -e "Project ID: ${GREEN}$PROJECT_ID${NC}"
    echo -e "Region: ${GREEN}$REGION${NC}"
    echo -e "Service: ${GREEN}$SERVICE_NAME${NC}"
}

# Enable required APIs
enable_apis() {
    echo -e "\n${YELLOW}🔌 Enabling required APIs...${NC}"
    
    gcloud services enable \
        cloudbuild.googleapis.com \
        run.googleapis.com \
        containerregistry.googleapis.com \
        aiplatform.googleapis.com \
        --project=$PROJECT_ID
    
    echo -e "${GREEN}✅ APIs enabled${NC}"
}

# Create service account
create_service_account() {
    echo -e "\n${YELLOW}👤 Creating service account...${NC}"
    
    # Create service account
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --description="AI Code Review service account" \
        --display-name="AI Code Reviewer" \
        --project=$PROJECT_ID || true
    
    # Add required roles
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/aiplatform.user"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/logging.logWriter"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/monitoring.metricWriter"
    
    echo -e "${GREEN}✅ Service account created${NC}"
}

# Build and deploy
build_and_deploy() {
    echo -e "\n${YELLOW}🏗️  Building and deploying...${NC}"
    
    # Build with Cloud Build
    gcloud builds submit \
        --config=cloudbuild.yaml \
        --project=$PROJECT_ID \
        --substitutions=_REGION=$REGION,_SERVICE_NAME=$SERVICE_NAME
    
    echo -e "${GREEN}✅ Build and deployment completed${NC}"
}

# Set environment variables
setup_env_vars() {
    echo -e "\n${YELLOW}🔐 Setting up environment variables...${NC}"
    
    echo "You'll need to set these environment variables in Cloud Run:"
    echo "1. GEMINI_API_KEY - Your Google AI API key"
    echo "2. GITLAB_TOKEN - GitLab access token"
    echo "3. GITLAB_WEBHOOK_SECRET - (Optional) Webhook secret for security"
    echo ""
    echo "Run this command to update the Cloud Run service:"
    echo ""
    echo -e "${BLUE}gcloud run services update $SERVICE_NAME \\"
    echo "  --region=$REGION \\"
    echo "  --set-env-vars=\"GEMINI_API_KEY=your-api-key,GITLAB_TOKEN=your-gitlab-token\" \\"
    echo -e "  --project=$PROJECT_ID${NC}"
}

# Get service URL
get_service_url() {
    echo -e "\n${YELLOW}🌐 Getting service URL...${NC}"
    
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --format="value(status.url)")
    
    echo -e "${GREEN}✅ Service deployed at: $SERVICE_URL${NC}"
    echo -e "${GREEN}📊 Health check: $SERVICE_URL/health${NC}"
    echo -e "${GREEN}🪝 Webhook URL: $SERVICE_URL/webhook/gitlab${NC}"
}

# Create GitLab webhook instructions
create_webhook_instructions() {
    echo -e "\n${YELLOW}🪝 GitLab Webhook Setup${NC}"
    echo "To complete the setup, add a webhook in your GitLab project:"
    echo ""
    echo "1. Go to your GitLab project → Settings → Webhooks"
    echo "2. Add new webhook with:"
    echo -e "   URL: ${BLUE}$SERVICE_URL/webhook/gitlab${NC}"
    echo "   Trigger: Merge request events"
    echo "   Secret Token: (optional, set GITLAB_WEBHOOK_SECRET if used)"
    echo ""
}

# Test deployment
test_deployment() {
    echo -e "\n${YELLOW}🧪 Testing deployment...${NC}"
    
    # Test health endpoint
    if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Health check passed${NC}"
    else
        echo -e "${RED}❌ Health check failed${NC}"
        echo "Check the Cloud Run logs for details"
    fi
}

# Main execution
main() {
    check_requirements
    get_config
    
    # Set the project
    gcloud config set project $PROJECT_ID
    
    enable_apis
    create_service_account
    build_and_deploy
    get_service_url
    setup_env_vars
    create_webhook_instructions
    test_deployment
    
    echo -e "\n${GREEN}🎉 Setup completed!${NC}"
    echo -e "${GREEN}Your AI Code Review service is ready for the GitLab Hackathon!${NC}"
    echo -e "\n${BLUE}Next steps:${NC}"
    echo "1. Set the environment variables in Cloud Run"
    echo "2. Add the webhook to your GitLab project"
    echo "3. Test with a merge request"
    echo "4. Submit to GitLab CI/CD Catalog"
}

# Run main function
main "$@" 