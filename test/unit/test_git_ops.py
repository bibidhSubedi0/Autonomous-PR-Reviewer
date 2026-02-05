import os
import pytest
from unittest.mock import patch, MagicMock
import subprocess
from tools.git_ops import clone_repository, get_diff

# --- Fixtures ---
# This simulates a fake temporary directory for our tests
@pytest.fixture
def mock_temp_dir(tmp_path):
    return str(tmp_path)

# --- Tests for clone_repository ---

@patch("subprocess.run")
@patch("tools.git_ops.mkdtemp")
def test_clone_repository_success(mock_mkdtemp, mock_subprocess, mock_temp_dir):
    """
    Test that the function runs the correct sequence of git commands.
    """
    # Arrange
    mock_mkdtemp.return_value = mock_temp_dir
    repo_url = "https://github.com/user/test-repo"
    commit_sha = "abc123456"
    token = "fake-token"

    # Act
    result_path = clone_repository(repo_url, commit_sha, token)

    # Assert
    assert result_path == mock_temp_dir
    
    # Verify strict order of Git commands
    # 1. git init
    assert mock_subprocess.call_args_list[0][0][0] == ["git", "init"]
    # 2. git remote add (with token injected)
    assert "https://fake-token@" in mock_subprocess.call_args_list[1][0][0][4]
    # 3. git fetch (shallow)
    assert "abc123456" in mock_subprocess.call_args_list[2][0][0]

@patch("subprocess.run")
@patch("tools.git_ops.mkdtemp")
@patch("shutil.rmtree")
def test_clone_repository_failure_cleanup(mock_rmtree, mock_mkdtemp, mock_subprocess, mock_temp_dir):
    """
    Test that if git fails, we clean up the folder and raise an error.
    """
    # Arrange
    mock_mkdtemp.return_value = mock_temp_dir
    # Simulate the 3rd command (git fetch) failing
    mock_subprocess.side_effect = [
        MagicMock(), # init ok
        MagicMock(), # remote ok
        subprocess.CalledProcessError(1, "git fetch") # FAIL
    ]

    # Act & Assert
    with pytest.raises(RuntimeError) as excinfo:
        clone_repository("http://url", "sha", "token")
    
    assert "Git Clone Failed" in str(excinfo.value)
    # Verify cleanup was called
    mock_rmtree.assert_called_once_with(mock_temp_dir)

# --- Tests for get_diff ---

@patch("subprocess.run")
def test_get_diff_success(mock_subprocess):
    """Test that it returns the stdout from the git diff command."""
    # Arrange
    mock_response = MagicMock()
    mock_response.stdout = "diff --git a/main.py..."
    # We have two subprocess calls (fetch, then diff). 
    # The first returns whatever, the second returns our mock_response
    mock_subprocess.side_effect = [MagicMock(), mock_response]

    # Act
    diff = get_diff("/fake/path")

    # Assert
    assert diff == "diff --git a/main.py..."
    # Verify the diff command structure
    cmd_used = mock_subprocess.call_args_list[1][0][0]
    assert cmd_used[0] == "git"
    assert cmd_used[1] == "diff"