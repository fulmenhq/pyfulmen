"""CLI tests leveraging Click runner."""

import json
from pathlib import Path

import pytest

click = pytest.importorskip("click")
from click.testing import CliRunner  # noqa: E402

from pyfulmen.schema.cli import cli  # noqa: E402

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "schema"


def test_cli_list_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--prefix", "observability/logging"])
    assert result.exit_code == 0
    assert "observability/logging" in result.output


def test_cli_info_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["info", "observability/logging/v1.0.0/logger-config"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["name"] == "logger-config"


def test_cli_validate_command():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "validate",
            "observability/logging/v1.0.0/logger-config",
            "--data",
            "{}",
            "--no-goneat",
        ],
    )
    assert result.exit_code in (0, 1)


def test_cli_validate_file_success():
    runner = CliRunner()
    valid_path = FIXTURES / "box_chars_valid.json"
    result = runner.invoke(
        cli,
        [
            "validate",
            "ascii/v1.0.0/box-chars",
            "--file",
            str(valid_path),
            "--no-goneat",
        ],
    )
    assert result.exit_code == 0


def test_cli_validate_file_failure():
    runner = CliRunner()
    invalid_path = FIXTURES / "box_chars_invalid.json"
    result = runner.invoke(
        cli,
        [
            "validate",
            "ascii/v1.0.0/box-chars",
            "--file",
            str(invalid_path),
            "--no-goneat",
        ],
    )
    assert result.exit_code == 1
