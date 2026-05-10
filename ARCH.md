# Autonomous PR Reviewer — Architecture

## Full system flow

```mermaid
flowchart TD
    PR["Pull Request opened or pushed"] --> WH["POST /webhook"]
    WH --> AUTH["auth.py - get installation token"]
    AUTH --> GRAPH["LangGraph Agent"]

    GRAPH --> GIT["git_ops.py"]
    GIT --> CLONE["Shallow clone commit SHA"]
    CLONE --> DIFF["git diff vs target branch"]

    DIFF --> LINT["linters.py"]
    LINT --> PY["Python - flake8"]
    LINT --> CPP["C/C++ - cppcheck"]
    LINT --> JS["JS/TS - ESLint"]

    DIFF --> AI["ai_ops.py"]
    AI --> PRE["Preprocess diff"]
    PRE --> GEM["Gemini 2.5 Flash"]
    GEM --> PARSE["Parse and validate JSON"]

    PY --> POST["github_poster.py"]
    CPP --> POST
    JS --> POST
    PARSE --> POST
    POST --> GHAPI["GitHub PR Review API"]
```

## AgentState data flow

```mermaid
flowchart LR
    A["repo_url, commit_sha, pr_number, token"] --> B["local_path, diff"]
    B --> C["lint_errors"]
    C --> D["ai comments"]
    D --> E["POST to GitHub"]
```

## Module responsibilities

| File | Role |
|---|---|
| `main.py` | Flask server, single `/webhook` route, wires everything together |
| `auth.py` | GitHub App auth, generates short-lived installation access tokens |
| `agents/graph.py` | LangGraph state machine, orchestrates the three tools in sequence |
| `git_ops.py` | Shallow clone by SHA, diff vs target branch, temp dir cleanup |
| `linters.py` | Walks repo, detects languages, dispatches to correct linter |
| `ai_ops.py` | Preprocesses diff, calls Gemini, validates and caps JSON output |
| `github_poster.py` | Formats comments and posts them to the GitHub PR Review API |