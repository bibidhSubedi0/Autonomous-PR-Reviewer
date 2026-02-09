import subprocess
import os

def _run_flake8(local_path: str) -> list[str]:
    """Worker: Runs flake8 specifically."""
    try:
        # --exclude: Ignore virtual envs and hidden git folders
        # --max-line-length=88: Standard Black/PEP8 length
        result = subprocess.run(
            ["flake8", ".", "--exclude=venv,.git,__pycache__", "--max-line-length=88"],
            cwd=local_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0 and result.stdout:
            # Filter empty lines
            return [line for line in result.stdout.split('\n') if line.strip()]
            
        return []
    except FileNotFoundError:
        return ["Flake8 not installed. Run 'pip install flake8'"]

def lint_repo(local_path: str) -> list[str]:
    """
    Dispatcher: Scans for languages and routes to the correct linter.
    """
    errors = []
    
    # 1. Detect Languages
    has_python = False
    
    # We walk the tree once to see what we have
    for root, _, files in os.walk(local_path):
        if has_python: 
            break
            
        if any(f.endswith(".py") for f in files):
            has_python = True

    # 2. Dispatch
    if has_python:
        print(f"Detected Python files in {local_path}. Running Flake8...")
        python_errors = _run_flake8(local_path)
        errors.extend(python_errors)
    
    # Future: if has_cpp: errors.extend(_run_cppcheck(local_path))

    return errors