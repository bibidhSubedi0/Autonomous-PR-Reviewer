"""
dry_run.py : runs the real LangGraph pipeline against a local folder.

Patches clone_node and cleanup_node so:
  - clone is skipped (local path injected directly)
  - your local folder is never deleted

Usage:
    python dry_run.py
    python dry_run.py --path ./test_validate
"""

import json
import os
import argparse
from unittest.mock import patch
from dotenv import load_dotenv

load_dotenv()


def build_diff_from_folder(folder: str) -> str:
    diff_lines = []
    for fname in sorted(os.listdir(folder)):
        fpath = os.path.join(folder, fname)
        if not os.path.isfile(fpath):
            continue
        diff_lines.append(f"diff --git a/{fname} b/{fname}")
        diff_lines.append(f"--- /dev/null")
        diff_lines.append(f"+++ b/{fname}")
        diff_lines.append(f"@@ -0,0 +1 @@")
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    diff_lines.append(f"+{line.rstrip()}")
        except Exception as e:
            diff_lines.append(f"+[Could not read file: {e}]")
    return "\n".join(diff_lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default="./test_validate", help="Local folder to lint and review")
    args = parser.parse_args()

    folder = os.path.abspath(args.path)
    if not os.path.isdir(folder):
        print(f"[ERROR] Folder not found: {folder}")
        return

    print(f"[dry_run] Target folder : {folder}")
    print(f"[dry_run] Files         : {os.listdir(folder)}")

    diff = build_diff_from_folder(folder)

    def fake_clone_node(state):
        print("[dry_run] Skipping clone — using local folder directly")
        return {
            "local_path": folder,
            "diff_content": diff,
            "review_status": "cloned",
        }

    def fake_cleanup_node(state):
        print("[dry_run] Skipping cleanup — local folder preserved")
        return {"review_status": "done"}

    with patch("agents.nodes.clone_node", side_effect=fake_clone_node), \
         patch("agents.nodes.cleanup_node", side_effect=fake_cleanup_node):

        from agents.graph import app

        initial_state = {
            "repo_url":      "local://dry-run",
            "pr_number":     0,
            "commit_sha":    "local",
            "github_token":  "none",
            "local_path":    None,
            "diff_content":  "",
            "review_status": "pending",
            "lint_errors":   [],
            "comments":      [],
        }

        print("\n[dry_run] Invoking real LangGraph pipeline...\n")
        final_state = app.invoke(initial_state)

    print("\n" + "=" * 60)
    print("WHAT WOULD BE POSTED TO GITHUB")
    print("=" * 60)

    if final_state.get("lint_errors"):
        print(f"\n--- Linter ({len(final_state['lint_errors'])} issues) ---")
        for e in final_state["lint_errors"]:
            print(f"  {e}")

    comments = final_state.get("comments", [])
    if comments:
        print(f"\n--- AI Review ({len(comments)} comments) ---")
        print(json.dumps(comments, indent=2))
    else:
        print("\n--- AI Review: no comments ---")

    print(f"\n[dry_run] Final status: {final_state.get('review_status')}")


if __name__ == "__main__":
    main()

"""
[dry_run] Target folder : C:\Users\Bibidh\Documents\ResumeProjects\Autonomous-PR-Reviewer\test_validate
[dry_run] Files         : ['bad.cpp', 'bad.js', 'dev_test', 'test.py']

[dry_run] Invoking real LangGraph pipeline...

[dry_run] Skipping clone — using local folder directly
[INFO] Running Linter...
[linter] Detected Python -> running Flake8...
[linter] Detected C/C++ -> running cppcheck...
[linter] Detected JS/TS -> running ESLint...
[WARN] Linter found 12 issues. Stopping early.
[INFO] Asking Gemini...
[ai_ops] Diff size: original=2435 → filtered=2323 → final=2323 chars
[dry_run] Skipping cleanup — local folder preserved

============================================================
WHAT WOULD BE POSTED TO GITHUB
============================================================

--- Linter (12 issues) ---
  .\test.py:5:1: F401 'fastapi.Header' imported but unused
  .\test.py:15:1: E302 expected 2 blank lines, found 1
  .\test.py:23:1: W293 blank line contains whitespace
  .\test.py:26:40: W291 trailing whitespace
  .\test.py:27:18: W291 trailing whitespace
  .\test.py:34:1: W293 blank line contains whitespace
  .\test.py:37:1: E302 expected 2 blank lines, found 1
  .\test.py:41:1: W293 blank line contains whitespace
  .\test.py:51:1: W293 blank line contains whitespace
  .\test.py:57:33: W292 no newline at end of file
  [linter] cppcheck not found. Run: sudo apt install cppcheck  (or: brew install cppcheck)
  [linter] ESLint not found. Run: npm install -g eslint

--- AI Review (7 comments) ---
[
  {
    "file": "bad.cpp",
    "line": 5,
    "comment": "Dereferencing a nullptr will cause a segmentation fault. Always check pointers for null before dereferencing."
  },
  {
    "file": "bad.cpp",
    "line": 8,
    "comment": "Variable 'x' is used before being initialized. This results in undefined behavior and could print a garbage value."
  },
  {
    "file": "bad.cpp",
    "line": 11,
    "comment": "Memory allocated with 'new int[100]' is not deallocated with 'delete[]', leading to a memory leak."
  },
  {
    "file": "bad.js",
    "line": 4,
    "comment": "Using '==' (loose equality) instead of '===' (strict equality) can lead to unexpected type coercion. For example, '1 == \"1\"' is true."
  },
  {
    "file": "bad.js",
    "line": 5,
    "comment": "The variable 'undefinedVar' is not declared or defined, which will cause a ReferenceError at runtime."
  },
  {
    "file": "test.py",
    "line": 16,
    "comment": "WEBHOOK_SECRET from os.getenv() can be None if not set in the environment. This will cause an AttributeError when .encode('utf-8') is called later. Consider adding a startup check or a default value, or raising an explicit error if it's critical."
  },
  {
    "file": "test.py",
    "line": 40,
    "comment": "json.loads(body) can raise a json.JSONDecodeError if the request body is not valid JSON. This should be handled with a try-except block to prevent application crashes and return an appropriate error response."
  }
]

[dry_run] Final status: done
"""