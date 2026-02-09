import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Fix path for imports
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from tools.linters import lint_repo
from tools.ai_ops import analyze_code_with_gemini

# --- TEST 1: The Linter Dispatcher ---

@patch("subprocess.run")
@patch("os.walk")
def test_linter_dispatch_python(mock_walk, mock_run):
    """If Python files exist, it should call flake8."""
    # Arrange: Simulate finding a .py file
    mock_walk.return_value = [("/tmp", [], ["main.py"])]
    
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = "main.py:1: Error"
    mock_run.return_value = mock_result

    # Act
    errors = lint_repo("/tmp")

    # Assert
    assert len(errors) == 1
    # Verify flake8 was actually called
    assert "flake8" in mock_run.call_args[0][0]

@patch("subprocess.run")
@patch("os.walk")
def test_linter_ignores_non_python(mock_walk, mock_run):
    """If only C++ files exist, it should NOT call flake8."""
    # Arrange: Simulate finding ONLY a .cpp file
    mock_walk.return_value = [("/tmp", [], ["main.cpp"])]

    # Act
    errors = lint_repo("/tmp")

    # Assert
    assert errors == []
    # Verify subprocess was NEVER called
    mock_run.assert_not_called()

# --- TEST 2: The AI JSON Parser ---

@patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}) # <--- ADD THIS LINE
@patch("google.generativeai.GenerativeModel")
def test_ai_parses_json(mock_model_class):
    """Test that valid JSON strings from AI become Python lists."""
    # Arrange
    mock_instance = mock_model_class.return_value
    fake_json = '[{"file": "main.py", "line": 5, "comment": "Bug"}]'
    mock_instance.generate_content.return_value.text = fake_json
    
    # Act
    result = analyze_code_with_gemini("diff...")
    
    # Assert
    assert len(result) == 1
    assert result[0]["comment"] == "Bug"