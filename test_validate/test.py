import hmac
import hashlib
import os
import json
from fastapi import FastAPI, Request, HTTPException, Header
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configuration from .env
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

async def verify_signature(request: Request):
    """Verify that the webhook request came from GitHub."""
    signature_header = request.headers.get("X-Hub-Signature-256")
    if not signature_header:
        raise HTTPException(status_code=403, detail="Signature missing")

    # Get the raw body bytes for hash calculation
    body = await request.body()
    
    # Create HMAC hex digest
    hash_object = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"), 
        msg=body, 
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()

    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    return body

@app.post("/webhook")
async def github_webhook(request: Request):
    # 1. Validate the sender
    body = await verify_signature(request)
    
    # 2. Parse the payload
    payload = json.loads(body)
    event_type = request.headers.get("X-GitHub-Event")

    # 3. Handle Pull Request events
    if event_type == "pull_request":
        action = payload.get("action")
        pr_number = payload.get("number")
        repo_name = payload.get("repository", {}).get("full_name")
        
        if action in ["opened", "synchronize"]:
            print(f"New PR #{pr_number} in {repo_name} detected!")
            # TODO: Trigger LangGraph Worker via Redis here
            return {"status": "accepted", "message": "Review task queued"}

    return {"status": "ignored"}