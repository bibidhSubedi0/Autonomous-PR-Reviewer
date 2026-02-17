import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import os
import json
import google.generativeai as genai
from typing import List, Dict


def analyze_code_with_gemini(diff: str) -> List[Dict]:
    """
    Sends the diff to Gemini Flash and enforces JSON output.
    Supports Python, C/C++, and JavaScript/TypeScript diffs.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env")
        return []

    genai.configure(api_key=api_key)

    # FIX: "gemini-flash-latest" is not a valid model string.
    # The correct identifiers are "gemini-1.5-flash-latest" (stable)
    # or "gemini-2.0-flash" (latest generation).
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={"response_mime_type": "application/json"},
    )

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

    user_prompt = f"Here is the diff to review:\n\n{diff}"

    try:
        response = model.generate_content([system_prompt, user_prompt])

        # Strip accidental markdown fences (defensive — mime type should prevent this)
        raw = response.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        comments = json.loads(raw)

        if isinstance(comments, list):
            # Validate that each entry has the required keys; drop malformed ones
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