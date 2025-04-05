# ✅ VisionWorks AI Code Reviewer

Automated code review powered by **Google Gemini**, **OpenAI**, **Claude**, and **Local LLM** – triggered by PR comments.

---

## 🚀 Overview

VisionWorks AI Code Reviewer is a reusable GitHub Action that performs automated, AI-powered code reviews. When you comment on a pull request (e.g. `/openai-review`, `/gemini-review`, `/claude-review`, `/local-review`), it uses the selected model to analyze the code diff and provide line-by-line feedback.

---

## ✨ Features

- 🔍 Analyzes pull request diffs
- 💡 AI-generated, line-level review comments
- 🧠 Supports multiple AI providers:
  - ✅ Google Gemini
  - ✅ OpenAI GPT
  - ✅ Claude by Anthropic
  - ✅ Local LLM (DeepSeek Coder 6.7b via Ollama)
- 🎯 Exclude specific file types with glob patterns
- 🔐 Secure – requires each user to define their own secrets
- 🛡️ Secure failover if required keys are missing
- 🚀 Modular model support
- 📌 File exclusion for docs, JSON, etc.
- 📋 Review posted as GitHub PR comments

---

## ⚙️ Installation (in your repo)

1. Create a workflow file in `.github/workflows/ai-review.yml`:

```yaml
name: AI Code Review

on:
  issue_comment:
    types: [created]

permissions: write-all

jobs:
  ai-review:
    runs-on: self-hosted

    steps:
      - uses: actions/checkout@v4

      - name: Run AI Reviewer
        uses: visionworksai/code-reviewer@v1
        with:
          # /gemini-review → triggers Gemini
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}

          # /openai-review → triggers OpenAI
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

          # /claude-review → triggers Claude
          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}

          # /local-review → triggers DeepSeek via Ollama (uses default model from action)
          INPUT_EXCLUDE: "*.md, docs/**"

```

2. Add **secrets** to your GitHub repo (only for cloud models):
   - `GEMINI_API_KEY` – for Gemini
   - `OPENAI_API_KEY` – for OpenAI
   - `CLAUDE_API_KEY` – for Claude

---

## 🧑‍💻 Usage

1. Open a pull request
2. Add one of these comments:

```
/gemini-review
/openai-review
/claude-review
/local-review
```

3. The action will:
   - Detect the requested model
   - Run the code analysis
   - Post inline comments

> You can override specific model versions:

```yaml
with:
  GEMINI_MODEL: gemini-1.5-flash-001
  OPENAI_MODEL: gpt-4
  CLAUDE_MODEL: claude-3-haiku-20240307
<<<<<<< Updated upstream
  DEEPSEEK_MODEL: deepseek-coder:1.3b
=======
>>>>>>> Stashed changes
```

---

## 🔧 Configuration

| Input               | Description                                           |
|---------------------|-------------------------------------------------------|
| `INPUT_EXCLUDE`     | Comma-separated list of glob patterns to ignore       |
| `AI_MODEL_TYPE`     | Auto-detected from PR comment (no need to set manually) |
| `GEMINI_API_KEY`    | Required for Gemini reviews                           |
| `GEMINI_MODEL`      | Optional: override Gemini model                       |
| `OPENAI_API_KEY`    | Required for OpenAI reviews                           |
| `OPENAI_MODEL`      | Optional: override OpenAI model                       |
| `CLAUDE_API_KEY`    | Required for Claude reviews                           |
| `CLAUDE_MODEL`      | Optional: override Claude model                       |
| `OLLAMA_URL`        | URL for Ollama API (default: http://localhost:11434)  |

---

## 🧱 Project Structure

```
visionworks_code_reviewer.py     # Main entry point
models/
  ├── __init__.py               # Model router / factory
  ├── base_model.py             # Common base interface
  ├── gemini_model.py           # Gemini integration
  ├── openai_model.py           # OpenAI integration
  ├── claude_model.py           # Claude integration
  └── deepseek_model.py         # Local LLM integration (via Ollama)
github_utils.py                 # GitHub API + comment posting
diff_utils.py                  # Diff parsing + filtering
```

---

## 🧪 Requirements

- Python 3.7+
- Dependencies:
  - `google-ai-generativelanguage==0.6.10` - Google AI Language API
  - `google-generativeai` - Google Gemini API
  - `PyGitHub` - GitHub API client
  - `github3.py==1.3.0` - GitHub API client
  - `unidiff` - Diff parsing
  - `openai>=1.0.0` - OpenAI API
  - `anthropic>=0.5.0` - Claude API
  - `requests>=2.28.0` - HTTP client
  - Docker (for local LLM)
  - Ollama

---

## 🤖 Model Comparison

| Model              | Strengths                         | Notes                               |
|--------------------|-----------------------------------|-------------------------------------|
| **Gemini**         | Fast, cost-effective              | Great default, free tier available  |
| **OpenAI GPT-4**   | Most advanced, high quality       | Higher cost                         |
| **Claude 3 Sonnet**| Balanced, reliable                | Great general-purpose choice        |
| **Claude 3 Haiku** | Fastest, cheapest Claude          | Ideal for quick/cheap reviews       |
| **Claude 3 Opus**  | Most powerful Claude              | High cost, deep reasoning           |
<<<<<<< Updated upstream
| **Local Reviewer** | Slow, open-source focused         | You can customize according to your device |
=======
| **Local LLM**      | Private, no API costs             | Uses DeepSeek Coder 6.7b via Ollama |
>>>>>>> Stashed changes

---

## 🛡️ Security

- This action does **not store, reuse, or expose your API keys**
- All keys are required to be provided via repo-level GitHub Secrets
- The action **fails securely** if required secrets are missing
- Local LLM review runs completely on your infrastructure

---

## ✅ Roadmap

- [x] Support Google Gemini
- [x] Support OpenAI GPT
- [x] Support Claude 3
<<<<<<< Updated upstream
- [x] Support DeepSeek 
- [ ] Support new local models
- [ ] Optional Slack/Discord integration

## Known Issues
- [ ] Review line numbers in local reviewer are sometimes different from the actual line.
- [ ] Improve acceleration/performance for local reviewers.
=======
- [x] Support Local LLM via Ollama
- [ ] Support additional local models
- [ ] Optional Slack/Discord integration

## Using Local Review

The code reviewer supports using local LLM models through Ollama. This is useful for environments where you want to keep your code analysis private or don't have access to external API services.

### Setup for Local Review

The workflow will automatically:
- Start Ollama container if not running
- Pull and use the DeepSeek Coder 6.7b model for review
- Stop the container after completion

### Configuration

You can configure the local review behavior through environment variables:

```yaml
with:
  OLLAMA_URL: "http://localhost:11434"  # Default Ollama API URL
```

For optimal performance, we recommend using a GPU-enabled runner with CUDA support.
>>>>>>> Stashed changes
