import os
import shutil
import stat
import subprocess
from tempfile import mkdtemp

def clone_repository(repo_url: str, commit_sha: str, token: str) -> str:
    """Clones a specific commit to a temp dir."""
    temp_dir = mkdtemp()
    auth_url = repo_url.replace("https://", f"https://{token}@")
    
    try:
        # 1. Init
        subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
        # 2. Remote
        subprocess.run(["git", "remote", "add", "origin", auth_url], cwd=temp_dir, check=True, capture_output=True)
        # 3. Fetch (Shallow)
        subprocess.run(
            ["git", "fetch", "--depth", "1", "origin", commit_sha], 
            cwd=temp_dir, check=True, capture_output=True
        )
        # 4. Checkout
        subprocess.run(["git", "checkout", "FETCH_HEAD"], cwd=temp_dir, check=True, capture_output=True)
        
        return temp_dir

    except subprocess.CalledProcessError as e:
        # Cleanup on failure to not leave junk folders
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        # Re-raise so the caller knows it failed
        raise RuntimeError(f"Git Clone Failed: {e}")

def get_diff(local_path: str, target_branch: str = "main") -> str:
    """Gets the diff between HEAD and target."""
    try:
        # Fetch target info first
        subprocess.run(
            ["git", "fetch", "origin", target_branch, "--depth", "1"], 
            cwd=local_path, check=True, capture_output=True
        )
        # Get diff
        result = subprocess.run(
            ["git", "diff", f"origin/{target_branch}...HEAD"],
            cwd=local_path, capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return ""
    

def cleanup_repo(local_path: str):
    """Deletes the temporary folder, handling Windows read-only files."""
    
    def on_rm_error(func, path, exc_info):
        """
        Error handler for shutil.rmtree.
        If the error is due to an access error (read only file),
        it attempts to add write permission and then retries.
        """
        os.chmod(path, stat.S_IWRITE)
        os.unlink(path)

    if local_path and os.path.exists(local_path):
        try:
            # onerror=on_rm_error handles the read-only git files
            shutil.rmtree(local_path, onerror=on_rm_error)
            print(f"🧹 Cleaned up {local_path}")
        except Exception as e:
            print(f" Warning: Cleanup failed partially: {e}")
        finally:
            # if local_path:
            #     print("Testing Cleanup...", end=" ", flush=True)
            #     cleanup_repo(local_path)
            #     if not os.path.exists(local_path):
            #         print("Success!")
            #     else:
            #         print("Failed to delete temp dir.")
            pass