import operator
from typing import TypedDict, List, Annotated, Optional

class AgentState(TypedDict):
    repo_url: str          # https://github.com/owner/repo
    pr_number: int         # 42
    commit_sha: str        # The specific commit to review
    github_token: str      # Passed in to avoid frequent env lookups

    local_path: Optional[str]   # Path to /tmp/xyz123
    diff_content: str           # The string diff sent to AI
    
    # need to use 'operator.add' so multiple nodes can append errors/comments
    lint_errors: Annotated[List[str], operator.add]
    comments: Annotated[List[dict], operator.add]
    
    # Used by Conditional Edges to route logic
    review_status: str     # "pending", "lint_failed", "success"