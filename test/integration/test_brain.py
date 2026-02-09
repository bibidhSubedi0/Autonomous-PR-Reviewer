import sys
import os
import json
from dotenv import load_dotenv

# Path Magic to find the 'tools' folder
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
 
from tools.git_ops import clone_repository, get_diff, cleanup_repo
from tools.linters import lint_repo
from tools.ai_ops import analyze_code_with_gemini

# Load .env for GITHUB_TOKEN and GEMINI_API_KEY
load_dotenv()

def verify_logic_on_real_repo():
    repo_url = "https://github.com/bibidhSubedi0/Test_Repo_For_APPR.git"
    token = os.getenv("GITHUB_TOKEN")
    
    # Validation
    if not token:
        print("GITHUB_TOKEN missing.")
        return
    if not os.getenv("GEMINI_API_KEY"):
        print("GEMINI_API_KEY missing.")
        return

    # Ask for SHA to ensure we test a specific state
    print(f"Target Repo: {repo_url}")
    # This is the SHA of your 'bad.py' commit
    commit_sha = "9e22cfe5a2448fb3ce6538b2eaa4242781cf6231"
    
    if not commit_sha:
        print("You must provide a SHA for the shallow clone tool to work.")
        return

    local_path = None
    try:
        print("\nCloning Real Code...")
        local_path = clone_repository(repo_url, commit_sha, token)
        print(f"Cloned to {local_path}")

        print("\nTesting Linter Dispatcher...")
        lint_errors = lint_repo(local_path)
        if lint_errors:
            print(f"Linter found {len(lint_errors)} issues:")
            for e in lint_errors[:3]: # Print first 3
                print(f"      - {e}")
        else:
            print("Linter passed (or no Python files found).")

        print("\nTesting AI Brain...")
        # FIX: We compare against 'main' because this is a PR simulation
        diff = get_diff(local_path, target_branch="main")
        
        if not diff:
            print("Diff is empty. Something is wrong with the comparison.")
        else:
            print(f"Sending {len(diff)} chars to Gemini...")
            comments = analyze_code_with_gemini(diff)
            
            print(f"Gemini responded with {len(comments)} comments.")
            print(json.dumps(comments, indent=2))

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
    finally:
        if local_path:
            print("\nCleaning up...")
            cleanup_repo(local_path)

if __name__ == "__main__":
    verify_logic_on_real_repo()