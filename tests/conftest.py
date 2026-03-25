"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def fixtures_dir():
    """Return the path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def invalid_configs_dir(fixtures_dir):
    """Return the path to invalid configs directory."""
    return fixtures_dir / "invalid_configs"


@pytest.fixture
def calculator_yaml(fixtures_dir):
    """Return path to calculator.yaml fixture."""
    return fixtures_dir / "calculator.yaml"


@pytest.fixture
def file_tools_yaml(fixtures_dir):
    """Return path to file_tools.yaml fixture."""
    return fixtures_dir / "file_tools.yaml"


@pytest.fixture
def missing_name_yaml(invalid_configs_dir):
    """Return path to missing_name.yaml fixture."""
    return invalid_configs_dir / "missing_name.yaml"


@pytest.fixture
def invalid_tool_schema_yaml(invalid_configs_dir):
    """Return path to invalid_tool_schema.yaml fixture."""
    return invalid_configs_dir / "invalid_tool_schema.yaml"


@pytest.fixture
def duplicate_tools_yaml(invalid_configs_dir):
    """Return path to duplicate_tools.yaml fixture."""
    return invalid_configs_dir / "duplicate_tools.yaml"
