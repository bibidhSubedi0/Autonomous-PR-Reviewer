import os
import sys
from dotenv import load_dotenv

# Ensure we can import from tools
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from tools.git_ops import clone_repository, get_diff, cleanup_repo

# Load your actual .env file (Validation Step 1)
load_dotenv()

def run_integration_test():
    repo_url = "https://github.com/bibidhSubedi0/Test_Repo_For_APPR.git"
    
    # Validation Step 2: Check Token
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print(" Error: GITHUB_TOKEN not found in .env")
        return

    # --- INPUT REQUIRED ---
    # Paste your SHA here, or the script will ask for it
    commit_sha = "9e22cfe5a2448fb3ce6538b2eaa4242781cf6231"
    
    if len(commit_sha) < 40:
        print(" Warning: That looks too short to be a full SHA, but trying anyway...")

    print(f"\nStarting Integration Test on {repo_url}...")
    local_path = None

    try:
        # 1. Test Cloning
        print("Testing Clone...", end=" ", flush=True)
        local_path = clone_repository(repo_url, commit_sha, token)
        
        # Verify file existence
        if os.path.exists(local_path) and os.path.exists(os.path.join(local_path, ".git")):
            print("Success!")
            print(f"   📂 Cloned to: {local_path}")
        else:
            print(" Failed: Directory created but .git missing.")
            return

        # 2. Test Diffing
        print("Testing Diff vs 'main'...", end=" ", flush=True)
        # Note: If your main branch is called 'master', change 'main' below
        diff = get_diff(local_path, target_branch="main")
        
        if diff:
            print("Success!")
            print(f"Diff Length: {len(diff)} chars")
            print(f"First 50 chars: {diff[:50].replace('\n', ' ')}...")
        else:
            print("  Warning: Diff is empty (Did you clone the same commit as main?)")

    except Exception as e:
        print(f"\n FATAL ERROR: {e}")\

    # finally:
    #     # 3. Test Cleanup
    #     if local_path:
    #         print("3️⃣  Testing Cleanup...", end=" ", flush=True)
    #         cleanup_repo(local_path)
    #         if not os.path.exists(local_path):
    #             print("Success!")
    #         else:
    #             print(" Failed to delete temp dir.")

if __name__ == "__main__":
    run_integration_test()