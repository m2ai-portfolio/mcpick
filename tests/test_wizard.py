"""Tests for the interactive wizard functionality."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
import yaml

from mcpick.wizard import (
    prompt_server_metadata,
    prompt_tool_definition,
    prompt_tool_parameters,
    prompt_add_more_tools,
    prompt_dependencies,
    save_yaml_config,
    display_config_summary,
    run_wizard,
    prompt_generate_project
)
from mcpick.config import ServerConfig, ToolDefinition, ToolParameter, parse_yaml
from mcpick.cli import main


class TestPromptFunctions:
    """Test individual prompt functions with mocked inputs."""

    @patch('mcpick.wizard.click.prompt')
    def test_prompt_server_metadata(self, mock_prompt):
        """Test prompting for server metadata."""
        mock_prompt.side_effect = [
            "Test Server",
            "A test MCP server",
            "Test Author",
            "test@example.com",
            "1.0.0",
            ">=3.11"
        ]

        metadata = prompt_server_metadata()

        assert metadata["server_name"] == "Test Server"
        assert metadata["description"] == "A test MCP server"
        assert metadata["author"] == "Test Author"
        assert metadata["author_email"] == "test@example.com"
        assert metadata["version"] == "1.0.0"
        assert metadata["python_version"] == ">=3.11"

    @patch('mcpick.wizard.click.confirm')
    @patch('mcpick.wizard.click.prompt')
    def test_prompt_tool_parameters_empty(self, mock_prompt, mock_confirm):
        """Test prompting for parameters with no parameters."""
        # Empty name ends parameter input
        mock_prompt.return_value = ""

        params = prompt_tool_parameters()

        assert params == []

    @patch('mcpick.wizard.click.confirm')
    @patch('mcpick.wizard.click.prompt')
    def test_prompt_tool_parameters_with_required(self, mock_prompt, mock_confirm):
        """Test prompting for required parameters."""
        mock_prompt.side_effect = [
            "param1",  # name
            "string",  # type
            "First parameter",  # description
            "",  # end parameters
        ]
        mock_confirm.return_value = True  # required

        params = prompt_tool_parameters()

        assert len(params) == 1
        assert params[0].name == "param1"
        assert params[0].type == "string"
        assert params[0].description == "First parameter"
        assert params[0].required is True
        assert params[0].default is None

    @patch('mcpick.wizard.click.confirm')
    @patch('mcpick.wizard.click.prompt')
    def test_prompt_tool_parameters_with_default(self, mock_prompt, mock_confirm):
        """Test prompting for optional parameter with default value."""
        mock_prompt.side_effect = [
            "param1",  # name
            "integer",  # type
            "An integer parameter",  # description
            "42",  # default value
            "",  # end parameters
        ]
        mock_confirm.side_effect = [
            False,  # not required
            True,  # provide default
        ]

        params = prompt_tool_parameters()

        assert len(params) == 1
        assert params[0].name == "param1"
        assert params[0].type == "integer"
        assert params[0].required is False
        assert params[0].default == 42

    @patch('mcpick.wizard.click.confirm')
    def test_prompt_add_more_tools_yes(self, mock_confirm):
        """Test asking to add more tools (yes)."""
        mock_confirm.return_value = True
        assert prompt_add_more_tools() is True

    @patch('mcpick.wizard.click.confirm')
    def test_prompt_add_more_tools_no(self, mock_confirm):
        """Test asking to add more tools (no)."""
        mock_confirm.return_value = False
        assert prompt_add_more_tools() is False

    @patch('mcpick.wizard.click.prompt')
    @patch('mcpick.wizard.click.confirm')
    def test_prompt_dependencies_none(self, mock_confirm, mock_prompt):
        """Test prompting for dependencies with none added."""
        mock_confirm.return_value = False

        deps = prompt_dependencies()

        assert deps == {}

    @patch('mcpick.wizard.click.prompt')
    @patch('mcpick.wizard.click.confirm')
    def test_prompt_dependencies_with_packages(self, mock_confirm, mock_prompt):
        """Test prompting for dependencies with packages."""
        mock_confirm.return_value = True
        mock_prompt.side_effect = [
            "requests",  # package name
            "^2.28.0",  # version
            "pydantic",  # package name
            "^2.0.0",  # version
            "",  # end dependencies
        ]

        deps = prompt_dependencies()

        assert deps == {
            "requests": "^2.28.0",
            "pydantic": "^2.0.0"
        }


class TestSaveYAMLConfig:
    """Test saving configuration to YAML."""

    def test_save_yaml_config(self, tmp_path):
        """Test saving a complete configuration to YAML."""
        config = ServerConfig(
            server_name="Test Server",
            description="A test server",
            author="Test Author",
            author_email="test@example.com",
            version="1.0.0",
            tools=[
                ToolDefinition(
                    name="test_tool",
                    description="A test tool",
                    parameters=[
                        ToolParameter(
                            name="param1",
                            type="string",
                            description="First parameter",
                            required=True
                        )
                    ],
                    return_type="object",
                    return_description="Test result"
                )
            ],
            dependencies={"requests": "^2.28.0"}
        )

        output_path = tmp_path / "test_config.yaml"
        save_yaml_config(config, output_path)

        # Verify file was created
        assert output_path.exists()

        # Verify content is valid YAML
        with open(output_path) as f:
            data = yaml.safe_load(f)

        assert data["server_name"] == "Test Server"
        assert data["description"] == "A test server"
        assert len(data["tools"]) == 1
        assert data["tools"][0]["name"] == "test_tool"
        assert data["dependencies"]["requests"] == "^2.28.0"

    def test_save_yaml_config_parseable(self, tmp_path):
        """Test that saved YAML can be parsed back."""
        config = ServerConfig(
            server_name="Calculator",
            description="A calculator server",
            tools=[
                ToolDefinition(
                    name="add",
                    description="Add two numbers",
                    parameters=[
                        ToolParameter(name="a", type="number", description="First number", required=True),
                        ToolParameter(name="b", type="number", description="Second number", required=True)
                    ]
                )
            ]
        )

        output_path = tmp_path / "calculator.yaml"
        save_yaml_config(config, output_path)

        # Parse the saved file
        parsed_config = parse_yaml(output_path)

        assert parsed_config.server_name == config.server_name
        assert parsed_config.description == config.description
        assert len(parsed_config.tools) == len(config.tools)
        assert parsed_config.tools[0].name == config.tools[0].name


class TestDisplayConfigSummary:
    """Test configuration summary display."""

    def test_display_config_summary(self, capsys):
        """Test displaying configuration summary."""
        config = ServerConfig(
            server_name="Test Server",
            description="A test server",
            author="Test Author",
            version="1.0.0",
            tools=[
                ToolDefinition(
                    name="tool1",
                    description="First tool",
                    parameters=[]
                ),
                ToolDefinition(
                    name="tool2",
                    description="Second tool",
                    parameters=[
                        ToolParameter(name="p1", type="string", description="Param 1", required=True)
                    ]
                )
            ],
            dependencies={"requests": "^2.28.0"}
        )

        # This should not raise an error
        display_config_summary(config)


class TestWizardCLI:
    """Test wizard integration with CLI."""

    def test_wizard_command_full_flow(self):
        """Test the wizard command with simulated input."""
        runner = CliRunner()

        # Simulate full wizard flow
        input_data = "\n".join([
            "Test Server",  # server name
            "A test server",  # description
            "Test Author",  # author
            "test@example.com",  # author email
            "1.0.0",  # version
            ">=3.11",  # python version
            "test_tool",  # tool 1 name
            "A test tool",  # tool 1 description
            "",  # no parameters (empty param name)
            "object",  # return type
            "Test result",  # return description
            "n",  # no more tools
            "n",  # no dependencies
            "y",  # save YAML
            "test.yaml",  # filename
            "n",  # don't generate project
        ])

        with runner.isolated_filesystem():
            result = runner.invoke(main, ['wizard'], input=input_data)

            # Check that wizard ran without errors
            assert result.exit_code == 0
            assert "Test Server" in result.output
            assert "test_tool" in result.output

            # Check that YAML was created
            assert Path("test.yaml").exists()

    def test_generate_interactive_flag(self):
        """Test generate command with --interactive flag."""
        runner = CliRunner()

        # Simulate minimal wizard input
        input_data = "\n".join([
            "Simple Server",  # server name
            "A simple server",  # description
            "",  # author (default)
            "",  # author email (default)
            "",  # version (default)
            "",  # python version (default)
            "simple_tool",  # tool name
            "A simple tool",  # description
            "",  # no parameters
            "",  # return type (default)
            "",  # return description (default)
            "n",  # no more tools
            "n",  # no dependencies
            "n",  # don't save YAML
            "n",  # don't generate project
        ])

        with runner.isolated_filesystem():
            result = runner.invoke(main, ['generate', '--interactive'], input=input_data)

            # Should complete without error
            assert result.exit_code == 0

    def test_generate_with_wizard_and_generation(self):
        """Test complete flow: wizard -> save YAML -> generate project."""
        runner = CliRunner()

        input_data = "\n".join([
            "Calculator",  # server name
            "A calculator server",  # description
            "",  # author
            "",  # email
            "",  # version
            "",  # python version
            "add",  # tool name
            "Add numbers",  # description
            "",  # no parameters
            "",  # return type
            "",  # return description
            "n",  # no more tools
            "n",  # no dependencies
            "y",  # save YAML
            "calc.yaml",  # filename
            "y",  # generate project
            "calc-server",  # output directory
        ])

        with runner.isolated_filesystem():
            result = runner.invoke(main, ['generate', '-i'], input=input_data)

            # Should generate successfully
            assert result.exit_code == 0
            assert Path("calc.yaml").exists()
            assert Path("calc-server").exists()
            assert (Path("calc-server") / "src" / "server.py").exists()


class TestPromptGenerateProject:
    """Test project generation prompting."""

    @patch('mcpick.wizard.click.prompt')
    @patch('mcpick.wizard.click.confirm')
    def test_prompt_generate_project_yes(self, mock_confirm, mock_prompt):
        """Test prompting to generate project (yes)."""
        mock_confirm.return_value = True
        mock_prompt.return_value = "test-server"

        config = ServerConfig(
            server_name="Test Server",
            description="A test",
            tools=[
                ToolDefinition(name="test", description="Test tool", parameters=[])
            ]
        )

        should_generate, output_dir = prompt_generate_project(config)

        assert should_generate is True
        assert output_dir == Path("test-server")

    @patch('mcpick.wizard.click.confirm')
    def test_prompt_generate_project_no(self, mock_confirm):
        """Test prompting to generate project (no)."""
        mock_confirm.return_value = False

        config = ServerConfig(
            server_name="Test Server",
            description="A test",
            tools=[
                ToolDefinition(name="test", description="Test tool", parameters=[])
            ]
        )

        should_generate, output_dir = prompt_generate_project(config)

        assert should_generate is False
        assert output_dir is None


class TestWizardValidation:
    """Test that wizard output passes validation."""

    def test_wizard_output_validates(self, tmp_path):
        """Test that wizard-generated YAML passes parse_yaml validation."""
        config = ServerConfig(
            server_name="Valid Server",
            description="A valid server configuration",
            author="Test Author",
            version="1.0.0",
            tools=[
                ToolDefinition(
                    name="valid_tool",
                    description="A valid tool",
                    parameters=[
                        ToolParameter(
                            name="input_param",
                            type="string",
                            description="An input parameter",
                            required=True
                        ),
                        ToolParameter(
                            name="optional_param",
                            type="integer",
                            description="An optional parameter",
                            required=False,
                            default=42
                        )
                    ],
                    return_type="object",
                    return_description="Tool result"
                )
            ],
            dependencies={"requests": "^2.28.0"}
        )

        yaml_path = tmp_path / "valid.yaml"
        save_yaml_config(config, yaml_path)

        # Should parse without errors
        parsed_config = parse_yaml(yaml_path)

        assert parsed_config.server_name == config.server_name
        assert len(parsed_config.tools) == 1
        assert parsed_config.tools[0].name == "valid_tool"
        assert len(parsed_config.tools[0].parameters) == 2
