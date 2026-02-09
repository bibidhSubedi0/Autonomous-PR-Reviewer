import os
import json
import google.generativeai as genai
from typing import List, Dict

def analyze_code_with_gemini(diff: str) -> List[Dict]:
    """
    Sends the diff to Gemini Flash and enforces JSON output.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env")
        return []

    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(
        model_name="gemini-flash-latest",
        generation_config={"response_mime_type": "application/json"}
    )

    system_prompt = """
    You are a Senior Software Engineer acting as a Code Reviewer.
    
    INPUT: A Git Diff of changes.
    TASK: Identify potential bugs, security risks, and logic errors.
    ignoring: Formatting/whitespace changes (assume a linter handles that).
    
    OUTPUT: A strictly valid JSON array of objects.
    Schema:
    [
        {
            "file": "filename.py",
            "line": 10,
            "comment": "Brief actionable feedback."
        }
    ]
    
    If no issues are found, return [].
    """

    user_prompt = f"Here is the diff to review:\n\n{diff}"

    try:
        response = model.generate_content([system_prompt, user_prompt])
        
        # Parse text to JSON
        comments = json.loads(response.text)
        
        # Validation
        if isinstance(comments, list):
            return comments
        else:
            print("AI returned invalid format (not a list).")
            return []

    except Exception as e:
        print(f"AI Review Failed: {e}")
        return []