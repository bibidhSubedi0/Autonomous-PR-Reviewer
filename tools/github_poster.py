import os
import requests


def post_review_comments(repo_url: str, pr_number: int, comments: list, token: str):
    """
    Takes the AI comments and posts them to the Pull Request as a review.
    """
    if not comments:
        print("[poster] No comments to post.")
        return

    # Convert clone URL to API URL
    # From: https://github.com/owner/repo.git
    # To:   https://api.github.com/repos/owner/repo/pulls/{pr_number}/reviews
    owner_repo = repo_url.replace("https://github.com/", "").replace(".git", "")
    api_url = f"https://api.github.com/repos/{owner_repo}/pulls/{pr_number}/reviews"

    # Format comments for the GitHub Pull Request Review API
    github_comments = []
    for c in comments:
        github_comments.append({
            "path": c["file"],
            "line": int(c["line"]),
            "body": f"**AI Review:** {c['comment']}",
        })

    payload = {
        "body": "Automated review based on the diff changes.",
        "event": "COMMENT",   # Use "REQUEST_CHANGES" to block merging
        "comments": github_comments,
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    print(f"[poster] Posting {len(comments)} comment(s) to PR #{pr_number}...")
    try:
        response = requests.post(api_url, json=payload, headers=headers)

        # FIX: GitHub returns 200 when updating an existing review and 201 when
        # creating a new one. Checking == 200 silently ignores the 201 success
        # case. response.ok covers both (and any other 2xx code).
        if response.ok:
            print(f"[poster] Review posted successfully (HTTP {response.status_code}).")
        else:
            print(f"[poster] Failed to post review: HTTP {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"[poster] Connection error: {e}")