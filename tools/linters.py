import subprocess
import os


# ---------------------------------------------------------------------------
# Per-language workers
# ---------------------------------------------------------------------------

def _run_flake8(local_path: str) -> list[str]:
    """Runs flake8 on the repo. Returns a list of error strings."""
    try:
        result = subprocess.run(
            [
                "flake8", ".",
                "--exclude=venv,.git,__pycache__,node_modules",
                "--max-line-length=88",
            ],
            cwd=local_path,
            capture_output=True,
            text=True,
        )
        # returncode 0  -> no issues
        # returncode 1  -> lint issues found  (stdout has the errors)
        # returncode >1 -> flake8 itself errored (stderr)
        if result.returncode == 1 and result.stdout:
            return [line for line in result.stdout.split("\n") if line.strip()]
        if result.returncode > 1:
            return [f"Flake8 internal error: {result.stderr.strip()}"]
        return []
    except FileNotFoundError:
        return ["[linter] Flake8 not found. Run: pip install flake8"]


def _run_cppcheck(local_path: str) -> list[str]:
    """
    Runs cppcheck on all C/C++ source files.
    cppcheck writes findings to stderr by default.
    """
    try:
        result = subprocess.run(
            [
                "cppcheck",
                "--enable=warning,style,performance,portability",
                "--suppress=missingIncludeSystem",
                "--error-exitcode=1",
                "--quiet",
                ".",
            ],
            cwd=local_path,
            capture_output=True,
            text=True,
        )
        # cppcheck outputs to stderr even on normal runs
        output = result.stderr or result.stdout
        if result.returncode != 0 and output:
            return [line for line in output.split("\n") if line.strip()]
        return []
    except FileNotFoundError:
        return ["[linter] cppcheck not found. Run: sudo apt install cppcheck  (or: brew install cppcheck)"]


def _run_eslint(local_path: str) -> list[str]:
    """
    Runs ESLint on all JS/TS files.
    Prefers a locally installed eslint (node_modules/.bin), falls back to global.
    When no project config exists, uses a minimal built-in ruleset.
    """
    local_eslint = os.path.join(local_path, "node_modules", ".bin", "eslint")
    eslint_cmd = local_eslint if os.path.isfile(local_eslint) else "eslint"

    try:
        result = subprocess.run(
            [
                eslint_cmd,
                ".",
                "--ext", ".js,.jsx,.ts,.tsx,.mjs,.cjs",
                "--ignore-pattern", "node_modules/",
                "--ignore-pattern", ".git/",
                # Minimal ruleset when no project-level config exists
                "--no-eslintrc",
                "--rule", '{"no-undef": "warn", "no-unused-vars": "warn", "eqeqeq": "error"}',
                "--format", "compact",
            ],
            cwd=local_path,
            capture_output=True,
            text=True,
        )
        output = result.stdout or result.stderr
        if result.returncode != 0 and output:
            return [line for line in output.split("\n") if line.strip()]
        return []
    except FileNotFoundError:
        return ["[linter] ESLint not found. Run: npm install -g eslint"]


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

_PYTHON_EXTS = {".py"}
_CPP_EXTS    = {".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".hxx"}
_JS_EXTS     = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}

# Directories to skip entirely during detection and linting
_SKIP_DIRS = {"venv", ".git", "__pycache__", "node_modules", ".tox", ".mypy_cache"}


def _detect_languages(local_path: str) -> dict[str, bool]:
    """
    Walks the repo once and returns which language families are present.
    FIX: The old code broke out of the loop after Python was found, so
    C++ and JS were never detected. We now prune ignored dirs in-place
    and only exit early once *all* languages have been found.
    """
    found = {"python": False, "cpp": False, "js": False}

    for root, dirs, files in os.walk(local_path):
        # Prune ignored directories in-place so os.walk won't descend into them
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]

        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in _PYTHON_EXTS:
                found["python"] = True
            elif ext in _CPP_EXTS:
                found["cpp"] = True
            elif ext in _JS_EXTS:
                found["js"] = True

        # Early-exit only once all three families are confirmed
        if all(found.values()):
            break

    return found


# ---------------------------------------------------------------------------
# Public dispatcher
# ---------------------------------------------------------------------------

def lint_repo(local_path: str) -> list[str]:
    """
    Detects languages present in the repo and dispatches to the appropriate
    linter(s). All linters always run (no short-circuit on first failure).
    """
    errors: list[str] = []
    languages = _detect_languages(local_path)

    if languages["python"]:
        print("[linter] Detected Python -> running Flake8...")
        errors.extend(_run_flake8(local_path))

    if languages["cpp"]:
        print("[linter] Detected C/C++ -> running cppcheck...")
        errors.extend(_run_cppcheck(local_path))

    if languages["js"]:
        print("[linter] Detected JS/TS -> running ESLint...")
        errors.extend(_run_eslint(local_path))

    if not any(languages.values()):
        print("[linter] No supported languages detected (Python/C++/JS). Skipping lint.")

    return errors