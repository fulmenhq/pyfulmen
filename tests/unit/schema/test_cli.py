"""CLI tests leveraging Click runner."""

import json

import pytest

click = pytest.importorskip("click")
from click.testing import CliRunner  # noqa: E402

from pyfulmen.schema.cli import cli  # noqa: E402


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
        ["validate", "observability/logging/v1.0.0/logger-config", "--data", "{}"],
    )
    assert result.exit_code in (0, 1)
