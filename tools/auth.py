import os
from github import GithubIntegration

def get_installation_access_token(installation_id):
    """
    Swaps the App's Private Key for a temporary token for a specific repository.
    """
    app_id = os.getenv("GITHUB_APP_ID")
    private_key = os.getenv("GITHUB_PRIVATE_KEY")
    
    if not app_id or not private_key:
        print("Error: Missing GITHUB_APP_ID or GITHUB_PRIVATE_KEY")
        return None

    # Fallback: Sometimes cloud providers flatten multi-line keys. 
    # This ensures the PEM format is strictly respected.
    private_key = private_key.replace('\\n', '\n')

    try:
        integration = GithubIntegration(app_id, private_key)
        # Get the token for this specific installation
        access_token = integration.get_access_token(installation_id).token
        return access_token
    except Exception as e:
        print(f"Auth Failed: {e}")
        return None