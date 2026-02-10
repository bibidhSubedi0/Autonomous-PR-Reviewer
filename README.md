# Autonomous PR Reviewer

A GitHub App that provides automated code review on Pull Requests. It utilizes Flake8 for static syntax analysis and Google Gemini 1.5 Flash for semantic code review, identifying logic bugs and security vulnerabilities that standard linters miss.

## How to Use (For Repository Owners)

You do not need to download or host any code to use this tool. It is deployed as a public GitHub App.

### 1. Install the App

1. Navigate to the App's public installation page: `https://github.com/apps/autonomous-pr-reviewer-bot`
2. Click **Install**.
3. Select the specific repositories (or your entire account) where you want the reviewer active.
4. Click **Install & Authorize**.

### 2. Triggering a Review

The application operates passively. Once installed:

1. Create a new branch and commit your code changes.
2. Open a **Pull Request** against your target branch (e.g., `main`).
3. The App will automatically detect the `pull_request` event, analyze the diff, and post actionable feedback directly on the PR timeline as inline comments.
4. The bot will re-run its analysis automatically if you push new commits to the open PR.

---

## Self-Hosting Guide (For Developers)

If you wish to host your own instance of the application or modify its behavior, follow the setup instructions below.

### Prerequisites

* Python 3.10+
* A [Google Gemini API Key](https://aistudio.google.com/)
* A public endpoint for GitHub Webhooks (e.g., a Render web service or a local [ngrok](https://ngrok.com/) tunnel)

### 1. Create a Custom GitHub App

1. In your GitHub account, navigate to **Settings > Developer Settings > GitHub Apps > New GitHub App**.
2. Name your App and set the **Webhook URL** to your server's endpoint (e.g., `https://your-domain.com/webhook`).
3. Under **Repository Permissions**, set:
* **Contents:** `Read-only`
* **Metadata:** `Read-only`
* **Pull Requests:** `Read and write`


4. Under **Subscribe to events**, check **Pull request**.
5. Click **Create GitHub App**.
6. Save your **App ID** and generate a **Private Key** (`.pem` file).

### 2. Local Installation

1. Clone the repository and navigate into the directory:
```bash
git clone https://github.com/your-username/autonomous-pr-reviewer.git
cd autonomous-pr-reviewer

```


2. Set up the Python environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

```



### 3. Environment Configuration

Create a `.env` file in the project root. You must format your `.pem` private key as a single continuous line, replacing physical line breaks with `\n` characters.

```env
GITHUB_APP_ID=your_app_id
GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
GEMINI_API_KEY=your_gemini_api_key

```

*(Note: If deploying to Render, paste the raw, multi-line key into the dashboard variable without quotes).*

### 4. Running the Service

**Development:**

```bash
python -m app.main

```

**Production (WSGI):**

```bash
gunicorn app.main:server

```
