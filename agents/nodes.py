import os
from agents.state import AgentState
from tools.linters import lint_repo
from tools.ai_ops import analyze_code_with_gemini

def linter_node(state: AgentState):
    """Node: Checks code style using the Dispatcher."""
    local_dir = state.get("local_path")
    
    if not local_dir or not os.path.exists(local_dir):
        return {"lint_errors": ["Error: Code not found."]}

    # Call the Dispatcher
    errors = lint_repo(local_dir)
    
    if errors:
        print(f"Linter found {len(errors)} issues.")
        return {
            "lint_errors": errors,
            "review_status": "lint_failed"
        }
    
    print("Linter passed (or no lintable files found).")
    return {
        "lint_errors": [],
        "review_status": "lint_passed"
    }

def ai_review_node(state: AgentState):
    """Node: Critiques the logic."""
    diff = state.get("diff_content")
    
    if not diff:
        print("Skipping AI: Empty diff.")
        return {"comments": []}
        
    if len(diff) > 30000:
        print("Skipping AI: Diff too large (>30k chars).")
        return {"comments": []}

    print("Sending diff to Gemini...")
    comments = analyze_code_with_gemini(diff)
    
    print(f"Gemini found {len(comments)} logic issues.")
    return {
        "comments": comments,
        "review_status": "completed"
    }