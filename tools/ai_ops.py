import os
import json
from typing import List, Dict
from google import genai
from google.genai import types


def analyze_code_with_gemini(diff: str) -> List[Dict]:
    """
    Sends the diff to Gemini and enforces JSON output.
    Uses the new google-genai SDK (replaces deprecated google-generativeai).
    Supports Python, C/C++, and JavaScript/TypeScript diffs.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ai_ops] Error: GEMINI_API_KEY not found in environment.")
        return []

    client = genai.Client(api_key=api_key)

    system_prompt = """
You are a Senior Software Engineer acting as a Code Reviewer.

INPUT: A Git diff that may contain Python, C/C++, and/or JavaScript/TypeScript changes.
TASK: Identify potential bugs, security risks, memory issues, and logic errors.
IGNORE: Formatting/whitespace changes (a linter handles those separately).

Language-specific guidance:
- Python: watch for None-dereferences, mutable default args, broad except clauses, missing input validation.
- C/C++: watch for buffer overflows, uninitialized variables, memory leaks, missing null checks, unsafe pointer arithmetic.
- JavaScript/TypeScript: watch for == vs ===, async/await errors not caught, prototype pollution, missing error handling in promises.

OUTPUT: A strictly valid JSON array. Each object must match this schema exactly:
[
    {
        "file": "path/to/filename.ext",
        "line": 10,
        "comment": "Brief, actionable feedback."
    }
]

Return [] if no issues are found. Do not include any text outside the JSON array.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{system_prompt}\n\nHere is the diff to review:\n\n{diff}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        raw = response.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        comments = json.loads(raw)

        if isinstance(comments, list):
            valid = []
            for item in comments:
                if isinstance(item, dict) and {"file", "line", "comment"} <= item.keys():
                    valid.append(item)
                else:
                    print(f"[ai_ops] Dropping malformed comment entry: {item}")
            return valid
        else:
            print("[ai_ops] AI returned invalid format (not a list).")
            return []

    except json.JSONDecodeError as e:
        print(f"[ai_ops] JSON parse failed: {e}\nRaw response: {response.text[:300]}")
        return []
    except Exception as e:
        print(f"[ai_ops] AI Review Failed: {e}")
        return []