"""Tests for custom template functionality."""

import os
import pytest
from pathlib import Path
from click.testing import CliRunner

from mcpick.cli import main
from mcpick.generator import list_available_templates, get_custom_template_dir, generate_project
from mcpick.validators import validate_template, validate_custom_templates, TEMPLATE_REQUIRED_VARS
from mcpick.config import ServerConfig, ToolDefinition, ToolParameter, GenerationOptions


@pytest.fixture
def sample_config():
    """Create a sample server configuration."""
    return ServerConfig(
        server_name="Test Server",
        description="Test MCP server",
        author="Test Author",
        version="1.0.0",
        tools=[
            ToolDefinition(
                name="test_tool",
                description="A test tool",
                parameters=[
                    ToolParameter(
                        name="input",
                        type="string",
                        description="Test input",
                        required=True
                    )
                ]
            )
        ]
    )


@pytest.fixture
def custom_template_dir(tmp_path):
    """Create a temporary custom template directory with valid templates."""
    template_dir = tmp_path / "custom_templates"
    template_dir.mkdir()

    # Create a custom server.py.j2 with all required variables
    server_template = template_dir / "server.py.j2"
    server_template.write_text("""
# Custom template for {{ config.server_name }}
# Package: {{ package_name }}
{% for tool in tools %}
# Tool: {{ tool.name }}
{% endfor %}
""")

    return template_dir


@pytest.fixture
def invalid_custom_template_dir(tmp_path):
    """Create a custom template directory with missing required variables."""
    template_dir = tmp_path / "invalid_templates"
    template_dir.mkdir()

    # Create a custom server.py.j2 missing required variables
    server_template = template_dir / "server.py.j2"
    server_template.write_text("""
# Custom template without required variables
# This is missing: config, tools, package_name
Just a static template.
""")

    return template_dir


class TestTemplateValidation:
    """Tests for template validation."""

    def test_validate_valid_template(self, custom_template_dir):
        """Test validation of a valid template."""
        template_path = custom_template_dir / "server.py.j2"
        required_vars = ["config", "tools", "package_name"]
        errors = validate_template(template_path, required_vars)
        assert errors == []

    def test_validate_template_missing_variables(self, invalid_custom_template_dir):
        """Test validation detects missing required variables."""
        template_path = invalid_custom_template_dir / "server.py.j2"
        required_vars = ["config", "tools", "package_name"]
        errors = validate_template(template_path, required_vars)
        assert len(errors) == 3
        assert "config" in errors
        assert "tools" in errors
        assert "package_name" in errors

    def test_validate_template_nonexistent(self, tmp_path):
        """Test validation of non-existent template."""
        template_path = tmp_path / "nonexistent.j2"
        errors = validate_template(template_path, ["config"])
        assert len(errors) == 1
        assert "not found" in errors[0]

    def test_validate_custom_templates_directory(self, custom_template_dir):
        """Test validation of entire custom template directory."""
        errors = validate_custom_templates(custom_template_dir)
        # Should not have errors for the valid template
        assert "server.py.j2" not in errors

    def test_validate_custom_templates_with_errors(self, invalid_custom_template_dir):
        """Test validation detects errors in custom template directory."""
        errors = validate_custom_templates(invalid_custom_template_dir)
        assert "server.py.j2" in errors
        assert len(errors["server.py.j2"]) > 0

    def test_validate_nonexistent_directory(self, tmp_path):
        """Test validation of non-existent directory."""
        nonexistent = tmp_path / "nonexistent"
        errors = validate_custom_templates(nonexistent)
        assert "_error" in errors


class TestTemplateDiscovery:
    """Tests for template discovery and listing."""

    def test_list_builtin_templates(self):
        """Test listing built-in templates."""
        templates = list_available_templates()
        assert "builtin" in templates
        assert "custom" in templates
        assert len(templates["builtin"]) >= 6  # We have 6 built-in templates

        # Check specific templates exist
        template_names = [t.name for t in templates["builtin"]]
        assert "server.py.j2" in template_names
        assert "pyproject.toml.j2" in template_names
        assert "test_tools.py.j2" in template_names
        assert "README.md.j2" in template_names
        assert "init.sh.j2" in template_names
        assert "conftest.py.j2" in template_names

    def test_list_custom_templates_env_var(self, custom_template_dir, monkeypatch):
        """Test listing custom templates from environment variable."""
        monkeypatch.setenv("MCPICK_TEMPLATE_DIR", str(custom_template_dir))

        templates = list_available_templates()
        assert len(templates["custom"]) == 1
        assert templates["custom"][0].name == "server.py.j2"

    def test_get_custom_template_dir_not_set(self):
        """Test getting custom template dir when not set."""
        # Temporarily unset the env var
        old_value = os.environ.get("MCPICK_TEMPLATE_DIR")
        if old_value:
            del os.environ["MCPICK_TEMPLATE_DIR"]

        result = get_custom_template_dir()
        assert result is None

        # Restore old value
        if old_value:
            os.environ["MCPICK_TEMPLATE_DIR"] = old_value

    def test_get_custom_template_dir_invalid_path(self, tmp_path, monkeypatch, capsys):
        """Test getting custom template dir with invalid path."""
        invalid_path = tmp_path / "nonexistent"
        monkeypatch.setenv("MCPICK_TEMPLATE_DIR", str(invalid_path))

        result = get_custom_template_dir()
        assert result is None

        # Should print warning
        captured = capsys.readouterr()
        assert "Warning" in captured.out or "directory not found" in captured.out.lower()


class TestCustomTemplateGeneration:
    """Tests for generating projects with custom templates."""

    def test_generate_with_custom_template(self, sample_config, custom_template_dir, tmp_path):
        """Test generating a project with custom templates."""
        output_dir = tmp_path / "output"
        options = GenerationOptions(
            output_dir=output_dir,
            template_dir=custom_template_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(sample_config, options)

        # Check that output was created
        assert output_dir.exists()
        server_file = output_dir / "src" / "server.py"
        assert server_file.exists()

        # Check that custom template was used
        content = server_file.read_text()
        assert "Custom template for Test Server" in content
        assert "Package: test_server" in content

    def test_generate_with_partial_override(self, sample_config, custom_template_dir, tmp_path):
        """Test that non-overridden templates fall back to built-in."""
        output_dir = tmp_path / "output"
        options = GenerationOptions(
            output_dir=output_dir,
            template_dir=custom_template_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(sample_config, options)

        # Check that built-in templates were used for other files
        assert (output_dir / "pyproject.toml").exists()
        assert (output_dir / "README.md").exists()
        assert (output_dir / "init.sh").exists()
        assert (output_dir / "tests" / "test_tools.py").exists()

    def test_generate_with_env_var_template_dir(self, sample_config, custom_template_dir, tmp_path, monkeypatch):
        """Test generating with template dir from environment variable."""
        monkeypatch.setenv("MCPICK_TEMPLATE_DIR", str(custom_template_dir))

        output_dir = tmp_path / "output"
        options = GenerationOptions(
            output_dir=output_dir,
            template_dir=None,  # Should use env var
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(sample_config, options)

        # Check that custom template was used
        server_file = output_dir / "src" / "server.py"
        content = server_file.read_text()
        assert "Custom template" in content


class TestCLIListTemplates:
    """Tests for list-templates CLI command."""

    def test_list_templates_command(self):
        """Test list-templates command shows built-in templates."""
        runner = CliRunner()
        result = runner.invoke(main, ["list-templates"])

        assert result.exit_code == 0
        assert "Built-in Templates" in result.output
        assert "server.py.j2" in result.output
        assert "pyproject.toml.j2" in result.output

    def test_list_templates_with_custom(self, custom_template_dir, monkeypatch):
        """Test list-templates command with custom templates."""
        monkeypatch.setenv("MCPICK_TEMPLATE_DIR", str(custom_template_dir))

        runner = CliRunner()
        result = runner.invoke(main, ["list-templates"])

        assert result.exit_code == 0
        assert "Custom Templates" in result.output
        assert "server.py.j2" in result.output

    def test_list_templates_shows_override(self, custom_template_dir, monkeypatch):
        """Test list-templates shows which templates are overridden."""
        monkeypatch.setenv("MCPICK_TEMPLATE_DIR", str(custom_template_dir))

        runner = CliRunner()
        result = runner.invoke(main, ["list-templates"])

        assert result.exit_code == 0
        # Should show that server.py.j2 is overridden
        assert "Overridden" in result.output or "custom" in result.output.lower()

    def test_list_templates_validation_warnings(self, invalid_custom_template_dir, monkeypatch):
        """Test list-templates shows validation warnings."""
        monkeypatch.setenv("MCPICK_TEMPLATE_DIR", str(invalid_custom_template_dir))

        runner = CliRunner()
        result = runner.invoke(main, ["list-templates"])

        assert result.exit_code == 0
        assert "Validation" in result.output or "Missing" in result.output


class TestCLIGenerateWithTemplates:
    """Tests for generate command with custom templates."""

    def test_generate_with_template_dir_flag(self, tmp_path, custom_template_dir):
        """Test generate command with --template-dir flag."""
        # Create a simple config file
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
server_name: Test Server
description: A test server
tools:
  - name: test_tool
    description: A test tool
    parameters:
      - name: input
        type: string
        description: Input parameter
""")

        output_dir = tmp_path / "output"

        runner = CliRunner()
        result = runner.invoke(main, [
            "generate",
            str(config_file),
            "--output-dir", str(output_dir),
            "--template-dir", str(custom_template_dir),
            "--no-venv",
            "--no-install"
        ])

        assert result.exit_code == 0
        assert output_dir.exists()

        # Check custom template was used
        server_file = output_dir / "src" / "server.py"
        content = server_file.read_text()
        assert "Custom template" in content

    def test_generate_invalid_template_dir(self, tmp_path):
        """Test generate command with invalid template directory."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
server_name: Test Server
description: A test server
tools:
  - name: test_tool
    description: A test tool
""")

        invalid_dir = tmp_path / "nonexistent"

        runner = CliRunner()
        result = runner.invoke(main, [
            "generate",
            str(config_file),
            "--template-dir", str(invalid_dir)
        ])

        # Should fail because directory doesn't exist
        assert result.exit_code != 0


class TestTemplateRequirements:
    """Tests for template variable requirements."""

    def test_required_vars_defined(self):
        """Test that required variables are defined for all template types."""
        expected_templates = {
            "server.py.j2",
            "pyproject.toml.j2",
            "test_tools.py.j2",
            "README.md.j2",
            "init.sh.j2",
            "conftest.py.j2"
        }

        assert set(TEMPLATE_REQUIRED_VARS.keys()) == expected_templates

    def test_all_templates_require_config(self):
        """Test that all templates require 'config' variable."""
        for template_name, required_vars in TEMPLATE_REQUIRED_VARS.items():
            assert "config" in required_vars, f"{template_name} should require 'config'"

    def test_all_templates_require_package_name(self):
        """Test that all templates require 'package_name' variable."""
        for template_name, required_vars in TEMPLATE_REQUIRED_VARS.items():
            assert "package_name" in required_vars, f"{template_name} should require 'package_name'"
