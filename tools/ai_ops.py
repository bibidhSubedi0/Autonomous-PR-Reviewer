import os
import json
from typing import List, Dict
from groq import Groq


# ---------------------------------------------------------------------------
# Diff preprocessing
# ---------------------------------------------------------------------------

# After filtering, cap at this many characters before sending to model.
# Adjust based on the model's context window.
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
    and append a note so the model knows it's seeing a partial diff.
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
# AI review via Groq
# ---------------------------------------------------------------------------

def analyze_code_with_groq(diff: str) -> List[Dict]:
    """
    Preprocesses the diff and sends it to Groq for review.
    Uses the Groq SDK with Llama models.
    Supports Python, C/C++, and JavaScript/TypeScript diffs.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[ai_ops] Error: GROQ_API_KEY not found in environment.")
        return []

    if not diff or not diff.strip():
        print("[ai_ops] Empty diff, skipping review.")
        return []

    # Preprocess before sending
    diff = preprocess_diff(diff)

    client = Groq(api_key=api_key)

    system_prompt = """
You are a Senior Software Engineer acting as a Code Reviewer.

OUTPUT INSTRUCTION: Output ONLY a valid JSON array with no surrounding text, markdown markers, or explanations. Format each issue as {"file": "path/to/filename.ext", "line": 10, "comment": "Brief, actionable feedback."}. Return [] if no issues are found. Maximum 10 issues.
"""

    try:
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the diff to review:\n\n{diff}"},
            ],
            temperature=0,
            max_tokens=1024,
        )

        raw = response.choices[0].message.content.strip()
        # Strip markdown code block markers if present
        raw = raw.lstrip("```").rstrip("```").strip()
        
        # DEBUG: Print raw output
        print(f"[ai_ops] RAW MODEL OUTPUT: {raw[:500]}")
        
        comments = []
        
        # Try to parse as JSON array directly
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and {"file", "line", "comment"} <= item.keys():
                        comments.append(item)
                # Cap at 10
                if len(comments) > 10:
                    comments = comments[:10]
                return comments
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Try to find JSON in the response text
        # Look for patterns like {"file": ..., "line": ..., "comment": ...}
        import re
        # Find all dict-like patterns with file, line, comment keys
        dict_pattern = r'\{[^}]*"file"[^}]*"line"[^}]*"comment"[^}]*\}'
        matches = re.findall(dict_pattern, raw)
        print(f"[ai_ops] Regex matches: {matches[:3]}")  # Log first 3 matches
        for match in matches:
            try:
                item = json.loads(match)
                if isinstance(item, dict) and {"file", "line", "comment"} <= item.keys():
                    comments.append(item)
            except (json.JSONDecodeError, TypeError):
                pass
        if len(comments) > 10:
            comments = comments[:10]
        return comments

    except json.JSONDecodeError as e:
        print(f"[ai_ops] JSON parse failed: {e}\nRaw response: {raw[:300]}")
        return []
    except Exception as e:
        print(f"[ai_ops] AI Review Failed: {e}")
        return []