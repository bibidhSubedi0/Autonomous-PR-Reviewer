import sys
import os
import json
from dotenv import load_dotenv

# Path Magic
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from agents.graph import app  # <--- Importing the machine we just built

# Load keys
load_dotenv()

def run_autonomous_agent():
    repo_url = "https://github.com/bibidhSubedi0/Test_Repo_For_APPR.git"
    token = os.getenv("GITHUB_TOKEN")
    
    # 1. Prepare the Input
    # Use the SHA of your 'bad.py' commit
    commit_sha = "9e22cfe5a2448fb3ce6538b2eaa4242781cf6231" 

    print(f"🚀 Starting Autonomous Agent on {commit_sha[:7]}...\n")

    initial_state = {
        "repo_url": repo_url,
        "commit_sha": commit_sha,
        "github_token": token,
        "review_status": "pending",
        "lint_errors": [],
        "comments": []
    }

    # 2. Press the "ON" Button (Invoke the Graph)
    # This runs the entire flowchart automatically
    final_state = app.invoke(initial_state)

    # 3. Check the Output (The finished product)
    print("\n🏁 Agent Finished!")
    print(f"   Status: {final_state['review_status']}")
    
    if final_state['lint_errors']:
        print(f"   ⚠️  Linter Issues: {len(final_state['lint_errors'])}")
    
    if final_state['comments']:
        print(f"   ✅ AI Comments: {len(final_state['comments'])}")
        print(json.dumps(final_state['comments'], indent=2))
    else:
        print("   ❌ No AI comments (Did linter fail or diff was empty?)")

if __name__ == "__main__":
    run_autonomous_agent()