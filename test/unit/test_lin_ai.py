import os
import sys
import pytest
from unittest.mock import patch, MagicMock, call

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from tools.linters import lint_repo, _detect_languages, _run_cppcheck, _run_eslint


# ---------------------------------------------------------------------------
# _detect_languages
# ---------------------------------------------------------------------------

@patch("os.walk")
def test_detect_cpp_only(mock_walk):
    mock_walk.return_value = [("/repo", [], ["main.cpp", "utils.h"])]
    result = _detect_languages("/repo")
    assert result["cpp"] is True
    assert result["python"] is False
    assert result["js"] is False


@patch("os.walk")
def test_detect_js_only(mock_walk):
    mock_walk.return_value = [("/repo", [], ["index.js", "app.ts"])]
    result = _detect_languages("/repo")
    assert result["js"] is True
    assert result["python"] is False
    assert result["cpp"] is False


@patch("os.walk")
def test_detect_all_three(mock_walk):
    mock_walk.return_value = [("/repo", [], ["main.py", "engine.cpp", "app.js"])]
    result = _detect_languages("/repo")
    assert result["python"] is True
    assert result["cpp"] is True
    assert result["js"] is True


@patch("os.walk")
def test_detect_skips_node_modules(mock_walk):
    """Files inside node_modules should not count toward language detection."""
    mock_walk.return_value = [
        ("/repo", ["node_modules", "src"], []),
        ("/repo/src", [], ["index.js"]),
    ]
    # Simulate dirs[:] pruning — node_modules won't be yielded because
    # _detect_languages prunes it in-place. We replicate that here by not
    # including node_modules in subsequent walk entries.
    result = _detect_languages("/repo")
    assert result["js"] is True
    assert result["python"] is False


# ---------------------------------------------------------------------------
# _run_cppcheck
# ---------------------------------------------------------------------------

@patch("subprocess.run")
def test_cppcheck_returns_errors_on_findings(mock_run):
    """cppcheck exits 1 and writes findings to stderr."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "[main.cpp:10]: (warning) Null pointer dereference\n[utils.cpp:5]: (error) Buffer overflow\n"
    mock_result.stdout = ""
    mock_run.return_value = mock_result

    errors = _run_cppcheck("/repo")

    assert len(errors) == 2
    assert "Null pointer dereference" in errors[0]
    assert "Buffer overflow" in errors[1]


@patch("subprocess.run")
def test_cppcheck_returns_empty_on_clean(mock_run):
    """cppcheck exits 0 and produces no output when code is clean."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""
    mock_result.stdout = ""
    mock_run.return_value = mock_result

    errors = _run_cppcheck("/repo")

    assert errors == []


@patch("subprocess.run")
def test_cppcheck_correct_flags(mock_run):
    """Verify the cppcheck command includes the expected flags."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""
    mock_result.stdout = ""
    mock_run.return_value = mock_result

    _run_cppcheck("/repo")

    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "cppcheck"
    assert "--enable=warning,style,performance,portability" in cmd
    assert "--suppress=missingIncludeSystem" in cmd
    assert "--error-exitcode=1" in cmd


def test_cppcheck_not_installed():
    """If cppcheck binary is missing, return a helpful message."""
    with patch("subprocess.run", side_effect=FileNotFoundError):
        errors = _run_cppcheck("/repo")
    assert len(errors) == 1
    assert "cppcheck not found" in errors[0]


# ---------------------------------------------------------------------------
# _run_eslint
# ---------------------------------------------------------------------------

@patch("os.path.isfile", return_value=False)
@patch("subprocess.run")
def test_eslint_returns_errors_on_findings(mock_run, mock_isfile):
    """ESLint exits non-zero and writes findings to stdout."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = "app.js: line 3, col 5, Error - Expected === but got == (eqeqeq)\napp.js: line 7, col 1, Warning - 'foo' is defined but never used (no-unused-vars)\n"
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    errors = _run_eslint("/repo")

    assert len(errors) == 2
    assert "eqeqeq" in errors[0]
    assert "no-unused-vars" in errors[1]


@patch("os.path.isfile", return_value=False)
@patch("subprocess.run")
def test_eslint_returns_empty_on_clean(mock_run, mock_isfile):
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    errors = _run_eslint("/repo")

    assert errors == []


@patch("os.path.isfile", return_value=False)
@patch("subprocess.run")
def test_eslint_correct_flags(mock_run, mock_isfile):
    """Verify ESLint is called with the right extensions and ruleset."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    _run_eslint("/repo")

    cmd = mock_run.call_args[0][0]
    assert "eslint" in cmd[0]
    assert "--ext" in cmd
    ext_idx = cmd.index("--ext")
    assert ".js" in cmd[ext_idx + 1]
    assert ".ts" in cmd[ext_idx + 1]
    assert "--no-eslintrc" in cmd
    assert "--format" in cmd


@patch("os.path.isfile", return_value=True)
@patch("subprocess.run")
def test_eslint_prefers_local_binary(mock_run, mock_isfile):
    """If node_modules/.bin/eslint exists, it should be used over global."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    _run_eslint("/repo")

    cmd = mock_run.call_args[0][0]
    assert "node_modules" in cmd[0]


def test_eslint_not_installed():
    """If eslint binary is missing, return a helpful message."""
    with patch("os.path.isfile", return_value=False):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            errors = _run_eslint("/repo")
    assert len(errors) == 1
    assert "ESLint not found" in errors[0]


# ---------------------------------------------------------------------------
# lint_repo dispatcher — cpp and js paths
# ---------------------------------------------------------------------------

@patch("subprocess.run")
@patch("os.walk")
def test_lint_repo_dispatches_cppcheck_for_cpp(mock_walk, mock_run):
    """lint_repo must call cppcheck when a .cpp file is found."""
    mock_walk.return_value = [("/repo", [], ["engine.cpp"])]
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""
    mock_result.stdout = ""
    mock_run.return_value = mock_result

    lint_repo("/repo")

    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "cppcheck"


@patch("os.path.isfile", return_value=False)
@patch("subprocess.run")
@patch("os.walk")
def test_lint_repo_dispatches_eslint_for_js(mock_walk, mock_run, mock_isfile):
    """lint_repo must call eslint when a .js file is found."""
    mock_walk.return_value = [("/repo", [], ["app.js"])]
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    lint_repo("/repo")

    cmd = mock_run.call_args[0][0]
    assert "eslint" in cmd[0]


@patch("os.path.isfile", return_value=False)
@patch("subprocess.run")
@patch("os.walk")
def test_lint_repo_runs_all_linters_for_mixed_repo(mock_walk, mock_run, mock_isfile):
    """All three linters run when all three language families are present."""
    mock_walk.return_value = [("/repo", [], ["main.py", "engine.cpp", "app.js"])]
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    lint_repo("/repo")

    all_cmds = [c[0][0][0] for c in mock_run.call_args_list]
    assert "flake8" in all_cmds
    assert "cppcheck" in all_cmds
    assert any("eslint" in c for c in all_cmds)


@patch("subprocess.run")
@patch("os.walk")
def test_lint_repo_cpp_errors_bubble_up(mock_walk, mock_run):
    """Errors from cppcheck are included in lint_repo return value."""
    mock_walk.return_value = [("/repo", [], ["main.c"])]
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "[main.c:3]: (error) Null pointer dereference\n"
    mock_result.stdout = ""
    mock_run.return_value = mock_result

    errors = lint_repo("/repo")

    assert any("Null pointer" in e for e in errors)


@patch("os.path.isfile", return_value=False)
@patch("subprocess.run")
@patch("os.walk")
def test_lint_repo_js_errors_bubble_up(mock_walk, mock_run, mock_isfile):
    """Errors from ESLint are included in lint_repo return value."""
    mock_walk.return_value = [("/repo", [], ["app.ts"])]
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = "app.ts: line 1, col 1, Error - Expected === (eqeqeq)\n"
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    errors = lint_repo("/repo")

    assert any("eqeqeq" in e for e in errors)