import os
from agents.state import AgentState
from tools.git_ops import clone_repository, get_diff, cleanup_repo
from tools.linters import lint_repo
from tools.ai_ops import analyze_code_with_gemini

def clone_node(state: AgentState):
    """1. Clones the repo and calculates the diff."""
    print(f"\n[INFO] Cloning {state['repo_url']}...")
    try:
        # Clone the repo
        local_path = clone_repository(state["repo_url"], state["commit_sha"], state["github_token"])
        
        # Get Diff (Compare against 'main' for PRs)
        diff = get_diff(local_path, target_branch="main")
        
        return {
            "local_path": local_path,
            "diff_content": diff,
            "review_status": "cloned"
        }
    except Exception as e:
        print(f"[ERROR] Clone failed: {e}")
        return {"review_status": "failed"}

def linter_node(state: AgentState):
    """2. Checks for syntax errors."""
    local_path = state.get("local_path")
    
    if not local_path:
        return {"review_status": "failed"}

    print("[INFO] Running Linter...")
    errors = lint_repo(local_path)
    
    if errors:
        print(f"[WARN] Linter found {len(errors)} issues. Stopping early.")
        return {
            "lint_errors": errors,
            "review_status": "lint_failed" 
        }
    
    print("[INFO] Linter passed.")
    return {
        "lint_errors": [],
        "review_status": "lint_passed"
    }

def ai_review_node(state: AgentState):
    """3. Uses Gemini to find bugs."""
    diff = state.get("diff_content")
    
    if not diff:
        print("[INFO] Skipping AI: Diff is empty.")
        return {"comments": [], "review_status": "completed"}

    print("[INFO] Asking Gemini...")
    comments = analyze_code_with_gemini(diff)
    
    return {
        "comments": comments,
        "review_status": "completed"
    }

def cleanup_node(state: AgentState):
    """4. Deletes the temp folder."""
    local_path = state.get("local_path")
    if local_path:
        print(f"[INFO] Cleaning up {local_path}...")
        cleanup_repo(local_path)
    return {"review_status": "done"}