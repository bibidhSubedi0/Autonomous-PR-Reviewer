import os
import requests

def post_review_comments(repo_url, pr_number, comments, token):
    """
    Takes the AI comments and posts them to the Pull Request.
    """
    if not comments:
        print("No comments to post.")
        return

    # 1. Convert Repo URL to API URL
    # From: https://github.com/bibidhSubedi0/Test_Repo_For_APPR.git
    # To:   https://api.github.com/repos/bibidhSubedi0/Test_Repo_For_APPR
    owner_repo = repo_url.replace("https://github.com/", "").replace(".git", "")
    api_url = f"https://api.github.com/repos/{owner_repo}/pulls/{pr_number}/reviews"

    # 2. Format Comments for GitHub API
    github_comments = []
    for c in comments:
        github_comments.append({
            "path": c["file"],
            "line": int(c["line"]),
            "body": f"**AI Review:** {c['comment']}"
        })

    payload = {
        "body": "Here is my automated review based on the changes.",
        "event": "COMMENT", # or "REQUEST_CHANGES"
        "comments": github_comments
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 3. Send the POST Request
    print(f"Posting {len(comments)} comments to PR #{pr_number}...")
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        if response.status_code == 200:
            print("Successfully posted review!")
        else:
            print(f"Failed to post review: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Connection Error: {e}")