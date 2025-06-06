# AI-Powered Code Review for GitLab CI/CD

🚀 **GitLab Hackathon Submission** - An intelligent code review component powered by Google's Gemini 2.5 Flash model for GitLab CI/CD pipelines.

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

### Prerequisites

- GitLab project with CI/CD enabled
- Google Cloud API key with Gemini API access
- GitLab access token for posting MR comments

### Basic Usage

Add this component to your `.gitlab-ci.yml`:

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

---

**Made with ❤️ for the GitLab Community** 