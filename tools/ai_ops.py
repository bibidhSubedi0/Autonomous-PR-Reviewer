import os
import json
from typing import List, Dict
from google import genai
from google.genai import types


# ---------------------------------------------------------------------------
# Diff preprocessing
# ---------------------------------------------------------------------------

# After filtering, cap at this many characters before sending to Gemini.
# ~30k chars ≈ ~7.5k tokens — well within gemini-2.5-flash's 1M token window
# but keeps cost and latency reasonable for typical 1000 LOC PRs.
MAX_DIFF_CHARS = 30_000


def _filter_diff(diff: str) -> str:
    """
    Strips context lines from the diff, keeping only:
      - File headers  (diff --git a/... b/...)
      - Hunk headers  (@@ -x,y +x,y @@)
      - Added lines   (+ but not +++)
      - Removed lines (- but not ---)

    This typically reduces diff size by 60-70% since unchanged context
    lines make up the bulk of a large diff.
    """
    filtered = []
    for line in diff.split("\n"):
        if (
            line.startswith("diff --git")
            or line.startswith("@@")
            or (line.startswith("+") and not line.startswith("+++"))
            or (line.startswith("-") and not line.startswith("---"))
        ):
            filtered.append(line)
    return "\n".join(filtered)


def _truncate_diff(diff: str, max_chars: int = MAX_DIFF_CHARS) -> str:
    """
    Safety net: if the filtered diff is still too large, truncate it
    and append a note so Gemini knows it's seeing a partial diff.
    """
    if len(diff) <= max_chars:
        return diff

    truncated = diff[:max_chars]
    note = (
        "\n\n[DIFF TRUNCATED] The diff exceeded the analysis limit. "
        "The above is a partial view — focus on what is shown."
    )
    print(f"[ai_ops] Diff truncated from {len(diff)} to {max_chars} chars.")
    return truncated + note


def preprocess_diff(diff: str) -> str:
    """Filter then truncate — always run both in this order."""
    original_len = len(diff)
    diff = _filter_diff(diff)
    filtered_len = len(diff)
    diff = _truncate_diff(diff)
    final_len = len(diff)

    print(
        f"[ai_ops] Diff size: original={original_len} → "
        f"filtered={filtered_len} → final={final_len} chars"
    )
    return diff


# ---------------------------------------------------------------------------
# Gemini review
# ---------------------------------------------------------------------------

def analyze_code_with_gemini(diff: str) -> List[Dict]:
    """
    Preprocesses the diff and sends it to Gemini for review.
    Uses the new google-genai SDK (replaces deprecated google-generativeai).
    Supports Python, C/C++, and JavaScript/TypeScript diffs.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ai_ops] Error: GEMINI_API_KEY not found in environment.")
        return []

    if not diff or not diff.strip():
        print("[ai_ops] Empty diff, skipping review.")
        return []

    # Preprocess before sending
    diff = preprocess_diff(diff)

    client = genai.Client(api_key=api_key)

    system_prompt = """
You are a Senior Software Engineer acting as a Code Reviewer.

INPUT: A Git diff (possibly filtered/truncated) that may contain Python, C/C++, and/or JavaScript/TypeScript changes.
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
Limit your response to the 10 most important issues maximum.
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

            # Hard cap — never post more than 10 comments
            if len(valid) > 10:
                print(f"[ai_ops] Capping comments from {len(valid)} to 10.")
                valid = valid[:10]

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