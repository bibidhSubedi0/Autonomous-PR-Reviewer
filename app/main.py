import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from tools.github_poster import post_review_comments
from tools.auth import get_installation_access_token

# Import agent
from agents.graph import app

# Load environment variables
load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Flask(__name__)

@server.route('/webhook', methods=['POST'])
def github_webhook():
    """
    This is the listener. GitHub will send a JSON payload here
    whenever a Pull Request is opened or updated.
    """
    data = request.json
    
    # 1. Validation: Ensure this is a Pull Request event
    if not data or 'pull_request' not in data:
        return jsonify({"status": "ignored", "reason": "Not a PR event"}), 200


    if 'installation' not in data:
        return jsonify({"status": "ignored", "reason": "No installation ID. Is this a GitHub App?"}), 200
        
    installation_id = data['installation']['id']
    dynamic_token = get_installation_access_token(installation_id)
    
    if not dynamic_token:
        return jsonify({"status": "error", "reason": "Could not generate auth token"}), 500
    
    

    action = data.get('action')
    if action not in ['opened', 'synchronize', 'reopened']:
        return jsonify({"status": "ignored", "reason": f"Action {action} not supported"}), 200

    # 2. Extract Data
    pr_info = data['pull_request']
    repo_info = data['repository']
    
    repo_url = repo_info['clone_url']
    commit_sha = pr_info['head']['sha']
    pr_number = pr_info['number']
    
    logger.info(f"PR #{pr_number} detected! Commit: {commit_sha}")

    # 3. Trigger the Autonomous Agent
    initial_state = {
        "repo_url": repo_url,
        "commit_sha": commit_sha,
        "github_token": dynamic_token,
        "review_status": "pending",
        "lint_errors": [],
        "comments": []
    }
    
    result = app.invoke(initial_state)
    
    # POST TO GITHUB
    if result['comments']:
        post_review_comments(
            repo_url, 
            pr_number, 
            result['comments'], 
            dynamic_token
        )
    
    # 4. Return Summary
    return jsonify({
        "status": "success",
        "comments_posted": len(result['comments'])
    }), 200

if __name__ == '__main__':
    # Run the server on port 5000
    print("Server is running on http://localhost:5000/webhook")
    server.run(host='0.0.0.0', port=5000)