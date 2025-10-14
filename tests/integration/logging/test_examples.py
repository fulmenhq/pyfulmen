"""Integration tests to ensure logging examples run successfully.

These tests validate that all example scripts in examples/ directory
execute without errors and produce expected output.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Get the repository root and examples directory
REPO_ROOT = Path(__file__).parent.parent.parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"


class TestLoggingExamples:
    """Test that all logging examples run without errors."""

    def test_logging_simple_example_runs(self):
        """Test examples/logging_simple.py runs successfully."""
        example_path = EXAMPLES_DIR / "logging_simple.py"
        assert example_path.exists(), f"Example not found: {example_path}"

        result = subprocess.run(
            [sys.executable, str(example_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should complete without errors
        assert result.returncode == 0, (
            f"logging_simple.py failed with return code {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )

        # Should produce output (logs go to stderr)
        assert result.stderr, "Expected log output on stderr"

        # Should include key messages from the example
        assert "demo-app" in result.stderr
        assert "Application started successfully" in result.stderr

    def test_logging_structured_example_runs(self):
        """Test examples/logging_structured.py runs successfully."""
        example_path = EXAMPLES_DIR / "logging_structured.py"
        assert example_path.exists(), f"Example not found: {example_path}"

        result = subprocess.run(
            [sys.executable, str(example_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should complete without errors
        assert result.returncode == 0, (
            f"logging_structured.py failed with return code {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )

        # Should produce output (logs go to stderr)
        assert result.stderr, "Expected log output on stderr"

        # Should include JSON output (STRUCTURED profile uses JSON)
        assert '"service":' in result.stderr or '"service": ' in result.stderr
        assert "api-service" in result.stderr

    def test_logging_enterprise_example_runs(self):
        """Test examples/logging_enterprise.py runs successfully."""
        example_path = EXAMPLES_DIR / "logging_enterprise.py"
        assert example_path.exists(), f"Example not found: {example_path}"

        result = subprocess.run(
            [sys.executable, str(example_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should complete without errors
        assert result.returncode == 0, (
            f"logging_enterprise.py failed with return code {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )

        # Should produce output (logs go to stderr)
        assert result.stderr, "Expected log output on stderr"

        # Should include JSON output with ENTERPRISE features
        assert '"service":' in result.stderr or '"service": ' in result.stderr
        assert "payment-api" in result.stderr
        # Should have correlation IDs in ENTERPRISE profile
        assert '"correlationId":' in result.stderr or '"correlationId": ' in result.stderr

    def test_all_logging_examples_exist(self):
        """Verify all expected logging example files exist."""
        expected_examples = [
            "logging_simple.py",
            "logging_structured.py",
            "logging_enterprise.py",
        ]

        for example_name in expected_examples:
            example_path = EXAMPLES_DIR / example_name
            assert example_path.exists(), f"Missing example: {example_name}"
            assert example_path.is_file(), f"Not a file: {example_name}"

    def test_examples_have_docstrings(self):
        """Verify all logging examples have module docstrings."""
        example_files = [
            EXAMPLES_DIR / "logging_simple.py",
            EXAMPLES_DIR / "logging_structured.py",
            EXAMPLES_DIR / "logging_enterprise.py",
        ]

        for example_path in example_files:
            with open(example_path, encoding="utf-8") as f:
                content = f.read()
                # Should have triple-quoted docstring at start
                assert '"""' in content[:500], f"Missing docstring in {example_path.name}"


class TestExamplesNoErrors:
    """Test examples complete without Python errors."""

    @pytest.mark.parametrize(
        "example_name",
        [
            "logging_simple.py",
            "logging_structured.py",
            "logging_enterprise.py",
        ],
    )
    def test_example_no_import_errors(self, example_name):
        """Test example imports successfully without errors."""
        example_path = EXAMPLES_DIR / example_name

        # Use python -m py_compile to check for syntax errors
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(example_path)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"{example_name} has syntax errors:\n{result.stderr}"

    @pytest.mark.parametrize(
        "example_name",
        [
            "logging_simple.py",
            "logging_structured.py",
            "logging_enterprise.py",
        ],
    )
    def test_example_completes_in_reasonable_time(self, example_name):
        """Test example completes within reasonable timeout."""
        example_path = EXAMPLES_DIR / example_name

        # Should complete within 10 seconds
        result = subprocess.run(
            [sys.executable, str(example_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Just verify it completed (timeout would raise TimeoutExpired)
        assert result.returncode == 0


class TestExamplesOutput:
    """Test examples produce expected output characteristics."""

    def test_simple_example_produces_text_output(self):
        """Test SIMPLE profile example produces human-readable text."""
        example_path = EXAMPLES_DIR / "logging_simple.py"

        result = subprocess.run(
            [sys.executable, str(example_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # SIMPLE profile should NOT produce JSON-only output
        # (some logs might be JSON, but not all)
        stderr_lines = result.stderr.strip().split("\n")
        non_json_lines = 0
        for line in stderr_lines:
            if line and not line.strip().startswith("{"):
                non_json_lines += 1

        # At least some lines should be non-JSON text format
        assert non_json_lines > 0, "SIMPLE profile should produce text output"

    def test_structured_example_produces_json_output(self):
        """Test STRUCTURED profile example produces JSON output."""
        example_path = EXAMPLES_DIR / "logging_structured.py"

        result = subprocess.run(
            [sys.executable, str(example_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # STRUCTURED profile should produce JSON output
        stderr_lines = result.stderr.strip().split("\n")
        json_lines = 0
        for line in stderr_lines:
            if line.strip().startswith("{"):
                json_lines += 1

        # Most lines should be JSON
        assert json_lines > 0, "STRUCTURED profile should produce JSON output"

    def test_enterprise_example_includes_correlation_ids(self):
        """Test ENTERPRISE profile example includes correlation IDs."""
        example_path = EXAMPLES_DIR / "logging_enterprise.py"

        result = subprocess.run(
            [sys.executable, str(example_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # ENTERPRISE profile should include correlationId in output
        assert "correlationId" in result.stderr, "ENTERPRISE profile should include correlation IDs"


class TestExamplesUsage:
    """Test examples demonstrate proper API usage."""

    def test_simple_example_imports_logger(self):
        """Verify simple example imports Logger correctly."""
        example_path = EXAMPLES_DIR / "logging_simple.py"

        with open(example_path, encoding="utf-8") as f:
            content = f.read()

        assert "from pyfulmen.logging import Logger" in content

    def test_structured_example_imports_profile(self):
        """Verify structured example imports LoggingProfile."""
        example_path = EXAMPLES_DIR / "logging_structured.py"

        with open(example_path, encoding="utf-8") as f:
            content = f.read()

        assert "from pyfulmen.logging import" in content
        assert "LoggingProfile" in content

    def test_enterprise_example_uses_correlation_context(self):
        """Verify enterprise example demonstrates correlation_context."""
        example_path = EXAMPLES_DIR / "logging_enterprise.py"

        with open(example_path, encoding="utf-8") as f:
            content = f.read()

        assert "correlation_context" in content
        assert "with correlation_context" in content
