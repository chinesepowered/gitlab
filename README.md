# AI Code Review for GitLab CI/CD

🚀 **GitLab Hackathon Submission** - An intelligent code review component powered by Google's Gemini 2.5 Flash model for GitLab CI/CD pipelines.

---

## 🎬 **Demo & Presentation** (For Judges)

### 📺 **Live Demo Video**
[![AI Code Review Demo](https://img.shields.io/badge/▶️_Watch_Demo-YouTube-red?style=for-the-badge&logo=youtube)](https://youtu.be/n8z1rR6C6OA)

### 📊 **Presentation Slides**
[![Presentation](https://img.shields.io/badge/📊_View_Slides-Canva-blue?style=for-the-badge&logo=canva)](https://www.canva.com/design/DAGqZxd0zbo/VJCZ8SGIs6_bgfTLuEPcAQ/edit?utm_content=DAGqZxd0zbo&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton)

### 🌐 **Live Webhook Service**
```
https://us-west2-hack-458102.cloudfunctions.net/ai-code-review
```
*Production-ready Google Cloud Function endpoint for real-time AI code reviews (linked to my Gitlab, deploy your own from below)*

### 🌐 **Example Gitlab Merge Request**
```
https://gitlab.com/chinesepowered/hackathon/-/merge_requests/3
```
*Example of AI Code Review reviewing a merge request on my Gitlab project*


### 📸 **Screenshots**

#### **AI Code Review in Action**
![AI Code Review Screenshot 1](/public/screen1.png)
*Real-time AI analysis providing intelligent feedback on merge requests*

#### **Detailed Code Analysis**
![AI Code Review Screenshot 2](/public/screen2.png)
*Comprehensive security and quality assessment with actionable suggestions*

---

## 🌟 Overview

This GitLab CI/CD component provides automated, AI-powered code reviews using Google's Gemini 2.5 Flash model. It analyzes code changes in merge requests and provides intelligent feedback on code quality, potential issues, security vulnerabilities, and improvement suggestions.

## ✨ Features

- 🤖 **AI-Powered Analysis**: Leverages Gemini 2.5 Flash for intelligent code review
- 🔍 **Multi-Language Support**: Analyzes code in various programming languages
- 🛡️ **Security Scanning**: Identifies potential security vulnerabilities
- 📊 **Code Quality Assessment**: Evaluates code quality and suggests improvements
- 🔄 **CI/CD Integration**: Seamlessly integrates with GitLab pipelines
- 💬 **MR Comments**: Posts review comments directly on merge requests
- 📈 **Detailed Reports**: Generates comprehensive review reports
- ⚡ **Fast Analysis**: Optimized for quick feedback in CI/CD workflows

## 🚀 Quick Start

### 🌟 Google Cloud Deployment (Recommended for Hackathon)

#### **Prerequisites**
1. **Google Cloud Project** with billing enabled
2. **Google Cloud CLI** installed and authenticated
3. **Gemini API Key** from Google AI Studio
4. **GitLab Access Token** with `api` and `read_repository` scopes

#### **Step 1: Get Your API Keys**

**Gemini API Key:**
1. Go to [Google AI Studio](https://aistudio.google.com)
2. Create a new API key
3. Copy the key (starts with `AIza...`)

**GitLab Access Token:**
1. GitLab → User Settings → Access Tokens
2. Create token with scopes: `api`, `read_repository`
3. Copy the token (starts with `glpat-...`)

#### **Step 2: Deploy to Google Cloud**

**🚀 One-Command Deployment:**
```bash
gcloud functions deploy ai-code-review \
  --gen2 \
  --runtime=python311 \
  --trigger=http \
  --entry-point=webhook_handler \
  --source=scripts/ \
  --allow-unauthenticated \
  --set-env-vars="GEMINI_API_KEY=YOUR_GEMINI_KEY,GITLAB_TOKEN=YOUR_GITLAB_TOKEN" \
  --memory=1GB \
  --timeout=540s \
  --max-instances=10 \
  --region=us-west1
```

**⚠️ Important:** Use `us-west1` or `us-central1` regions for full Gemini API support.

#### **Step 3: Configure GitLab Webhook**

1. **Go to your GitLab project** → Settings → Webhooks
2. **Add webhook:**
   - **URL**: `https://us-west1-YOUR_PROJECT_ID.cloudfunctions.net/ai-code-review`
   - **Triggers**: ✅ Merge request events
   - **SSL verification**: ✅ Enable
3. **Test webhook**: Click "Test" → "Merge request events"

#### **Step 4: Test Your Setup**

1. **Create a merge request** with code changes
2. **Check the function logs** in Google Cloud Console
3. **Look for AI comments** in your GitLab MR

**🎉 You're done! AI reviews will now appear automatically on merge requests.**

### 🔧 Alternative Deployment Options

**💡 Super Simple (No Docker Required!):**
```powershell
# One-command deployment using Cloud Functions
.\deploy\simple-deploy.ps1
```

**🔧 Advanced (Docker + Cloud Run):**
```bash
# Full-featured deployment with Docker
chmod +x deploy/setup-gcp.sh
./deploy/setup-gcp.sh
```

**🚀 Choose Your Deployment:**
- **Cloud Functions**: Simplest, no Docker needed, pay-per-request
- **Cloud Run**: Advanced features, auto-scaling containers
- **App Engine**: Traditional web app deployment

**[📖 Simple Deployment Guide](deploy/simple-cloud-functions.md)** | **[📖 Advanced Guide](docs/GOOGLE_CLOUD_DEPLOYMENT.md)**

## 🔧 Troubleshooting

### **Common Issues**

#### **❌ "User location is not supported for the API use"**
- **Cause**: Gemini API geographic restrictions
- **Fix**: Deploy to US regions (`us-west1`, `us-central1`, `us-east1`)

#### **❌ "404 Commit Not Found"**
- **Cause**: Invalid commit SHA in webhook
- **Fix**: Ensure GitLab webhook is properly configured with real MR events

#### **❌ "No files to review"**
- **Cause**: Empty merge request or unsupported file types
- **Fix**: Add code files (.py, .js, .ts, .java, .go, etc.) to your MR

#### **❌ "GitLab API errors"**
- **Cause**: Insufficient token permissions
- **Fix**: Ensure GitLab token has `api` and `read_repository` scopes

### **Debugging Steps**

1. **Check function logs**: Google Cloud Console → Cloud Functions → Logs
2. **Test webhook**: GitLab → Settings → Webhooks → Test
3. **Verify API keys**: Ensure both Gemini and GitLab tokens are valid
4. **Check file types**: Only supported languages are reviewed

### **Supported Languages**
- Python (`.py`), JavaScript (`.js`), TypeScript (`.ts`)
- Java (`.java`), Go (`.go`), Rust (`.rs`)
- C++ (`.cpp`, `.hpp`), C# (`.cs`), PHP (`.php`)
- Ruby (`.rb`), HTML, CSS, YAML, JSON, SQL, Shell

### 🔄 Traditional CI/CD Usage

For traditional GitLab CI/CD pipeline integration:

```yaml
include:
  - component: gitlab.com/your-namespace/ai-code-review/ai-review@main

stages:
  - ai-review

ai-code-review:
  extends: .ai-code-review
  variables:
    GEMINI_API_KEY: $GEMINI_API_KEY
    GITLAB_TOKEN: $GITLAB_ACCESS_TOKEN
```

### Prerequisites

- GitLab project with CI/CD enabled
- Google Cloud project (for hackathon deployment)
- Google Cloud API key with Gemini API access
- GitLab access token for posting MR comments

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Cloud API key for Gemini access |
| `GITLAB_TOKEN` | Yes | GitLab access token for posting comments |
| `REVIEW_SCOPE` | No | Scope of review (`changed`, `all`) - default: `changed` |
| `MAX_FILES` | No | Maximum files to review - default: `50` |
| `LANGUAGES` | No | Comma-separated list of languages to review |
| `SEVERITY_THRESHOLD` | No | Minimum severity for comments (`low`, `medium`, `high`) |

## 🏗️ Architecture

```
AI Code Review Component
├── 📄 template.yml (GitLab CI component template)
├── 🐍 scripts/
│   ├── ai_reviewer.py (Main review logic)
│   ├── gemini_client.py (Gemini API integration)
│   ├── gitlab_client.py (GitLab API integration)
│   └── report_generator.py (Report generation)
├── 📋 requirements.txt (Python dependencies)
├── 🐳 Dockerfile (Container image)
└── 📚 docs/ (Documentation)
```

## 🔧 Configuration

### Advanced Configuration

```yaml
ai-code-review:
  extends: .ai-code-review
  variables:
    GEMINI_API_KEY: $GEMINI_API_KEY
    GITLAB_TOKEN: $GITLAB_ACCESS_TOKEN
    REVIEW_SCOPE: "changed"
    MAX_FILES: "30"
    LANGUAGES: "python,javascript,typescript,go,java"
    SEVERITY_THRESHOLD: "medium"
    INCLUDE_PATTERNS: "src/,lib/"
    EXCLUDE_PATTERNS: "tests/,docs/"
```

## 📝 Review Types

- **Code Quality**: Style, maintainability, and best practices
- **Security**: Vulnerability detection and security patterns
- **Performance**: Performance bottlenecks and optimizations
- **Logic**: Potential bugs and logical errors
- **Documentation**: Missing or inadequate documentation

## 🤝 Contributing

This project is part of the GitLab Hackathon and contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a merge request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🏆 GitLab Hackathon

This component is designed for submission to the GitLab CI/CD Catalog as part of the GitLab Hackathon initiative to enhance the GitLab ecosystem with AI-powered tools.

### 🌟 Hackathon Features

- ✅ **Google Cloud Native**: Deployed on Google Cloud Run with auto-scaling
- ✅ **Real-time Integration**: Webhook-based immediate code reviews
- ✅ **Production Ready**: Health checks, monitoring, and comprehensive logging
- ✅ **Cost Efficient**: Pay-per-use serverless architecture
- ✅ **Dual Mode**: Supports both CI/CD jobs and real-time webhook processing
- ✅ **Advanced AI**: Powered by Google's Gemini 2.5 Flash model

### 🚀 Deployment Options

1. **Google Cloud Run**: Real-time webhook service (recommended for hackathon)
2. **GitLab CI/CD**: Traditional pipeline integration
3. **Hybrid**: Use both modes for maximum flexibility

**[🚀 Deploy to Google Cloud](docs/GOOGLE_CLOUD_DEPLOYMENT.md)**

---

**Made with ❤️ for the GitLab Community**