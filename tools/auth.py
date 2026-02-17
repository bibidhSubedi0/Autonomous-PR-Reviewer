import os
from github import GithubIntegration

import os
from github import GithubIntegration

def get_installation_access_token(installation_id):
    env = os.getenv("ENV", "prod")
    
    if env == "dev":
        app_id = os.getenv("GITHUB_APP_ID_DEV")
        private_key = os.getenv("GITHUB_PRIVATE_KEY_DEV")
    else:
        app_id = os.getenv("GITHUB_APP_ID")
        private_key = os.getenv("GITHUB_PRIVATE_KEY")

    if not app_id or not private_key:
        print("Error: Missing app credentials")
        return None

    private_key = private_key.replace('\\n', '\n')

    try:
        integration = GithubIntegration(app_id, private_key)
        access_token = integration.get_access_token(installation_id).token
        return access_token
    except Exception as e:
        print(f"Auth Failed: {e}")
        return None