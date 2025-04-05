# ✅ VisionWorks AI Code Reviewer

Automated code review powered by **Google Gemini**, **OpenAI**, **Claude**, and **DeepSeek** – triggered by PR comments.

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
  - ✅ DeepSeek Coder
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

2. Add **secrets** to your GitHub repo:

   - `GEMINI_API_KEY` – for Gemini
   - `OPENAI_API_KEY` – for OpenAI
   - `CLAUDE_API_KEY` – for Claude
   - `DEEPSEEK_API_KEY` – for DeepSeek

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
  DEEPSEEK_MODEL: deepseek-coder:1.3b
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
| `DEEPSEEK_API_KEY`  | Required for DeepSeek reviews                         |
| `DEEPSEEK_MODEL`    | Optional: override DeepSeek model                     |

---

## 🧱 Project Structure

```
visionworks_code_reviewer.py     # Main entry point
models/
  ├── __init__.py                # Model router / factory
  ├── base_model.py              # Common base interface
  ├── gemini_model.py            # Gemini integration
  ├── openai_model.py            # OpenAI integration
  ├── claude_model.py            # Claude integration
  └── deepseek_model.py          # DeepSeek integration
github_utils.py                  # GitHub API + comment posting
diff_utils.py                    # Diff parsing + filtering
```

---

## ➕ Adding New Models

1. Add a new file in `models/` (e.g. `my_model.py`)
2. Inherit from `BaseAIModel`
3. Register your model inside `models/__init__.py`

---

## 🧪 Requirements

- Python 3.7+
- Dependencies:
  - `PyGithub`, `github3.py`, `openai>=1.0.0`
  - `google-generativeai`, `google-ai-generativelanguage`
  - `requests`, `unidiff`
  - (Optional for DeepSeek: `httpx` or `requests`)

---

## 🤖 Model Comparison

| Model              | Strengths                         | Notes                               |
|--------------------|-----------------------------------|-------------------------------------|
| **Gemini**         | Fast, cost-effective              | Great default, free tier available  |
| **OpenAI GPT-4**   | Most advanced, high quality       | Higher cost                         |
| **Claude 3 Sonnet**| Balanced, reliable                | Great general-purpose choice        |
| **Claude 3 Haiku** | Fastest, cheapest Claude          | Ideal for quick/cheap reviews       |
| **Claude 3 Opus**  | Most powerful Claude              | High cost, deep reasoning           |
| **Local Reviewer** | Slow, open-source focused         | You can customize according to your device |

---

## 🛡️ Security

- This action does **not store, reuse, or expose your API keys**
- All keys are required to be provided via repo-level GitHub Secrets
- The action **fails securely** if required secrets are missing

---

## ✅ Roadmap

- [x] Support Google Gemini
- [x] Support OpenAI GPT
- [x] Support Claude 3
- [x] Support DeepSeek 
- [ ] Support new local models
- [ ] Optional Slack/Discord integration

## Known Issues
- [ ] Review line numbers in local reviewer are sometimes different from the actual line.
- [ ] Improve acceleration/performance for local reviewers.
