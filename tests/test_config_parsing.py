"""Tests for YAML configuration parsing and validation."""

import pytest
from pathlib import Path
from pydantic import ValidationError

from mcpick.config import parse_yaml, validate_yaml, ServerConfig, ToolDefinition, ToolParameter
from mcpick.validators import (
    validate_json_schema_compatibility,
    validate_tool_definition,
    validate_server_config,
)


class TestYAMLParsing:
    """Test YAML parsing functionality."""

    def test_parse_valid_calculator_config(self, calculator_yaml):
        """Test parsing a valid calculator configuration."""
        config = parse_yaml(calculator_yaml)

        assert config.server_name == "Test Calculator"
        assert config.description == "Test calculator for validation"
        assert config.version == "0.1.0"
        assert len(config.tools) == 1
        assert config.tools[0].name == "add"

    def test_parse_valid_file_tools_config(self, file_tools_yaml):
        """Test parsing a valid file tools configuration."""
        config = parse_yaml(file_tools_yaml)

        assert config.server_name == "File Operations"
        assert config.author == "Test Author"
        assert config.author_email == "test@example.com"
        assert len(config.tools) == 2
        assert config.tools[0].name == "read_file"
        assert config.tools[1].name == "write_file"
        assert "pathlib2" in config.dependencies

    def test_parse_missing_server_name(self, missing_name_yaml):
        """Test that missing server_name raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            parse_yaml(missing_name_yaml)

        # Check that the error mentions server_name
        error_str = str(exc_info.value)
        assert "server_name" in error_str.lower()

    def test_parse_invalid_tool_schema(self, invalid_tool_schema_yaml):
        """Test that invalid tool schema raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            parse_yaml(invalid_tool_schema_yaml)

        # Should have errors about missing fields
        error_str = str(exc_info.value)
        assert "description" in error_str.lower() or "type" in error_str.lower()

    def test_parse_nonexistent_file(self):
        """Test that parsing nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parse_yaml(Path("/nonexistent/file.yaml"))

    def test_validate_yaml_valid_config(self, calculator_yaml):
        """Test validate_yaml with valid configuration."""
        is_valid, error = validate_yaml(calculator_yaml)
        assert is_valid is True
        assert error is None

    def test_validate_yaml_invalid_config(self, missing_name_yaml):
        """Test validate_yaml with invalid configuration."""
        is_valid, error = validate_yaml(missing_name_yaml)
        assert is_valid is False
        assert error is not None
        assert "server_name" in error.lower()


class TestPydanticModels:
    """Test Pydantic model validation."""

    def test_tool_parameter_valid(self):
        """Test creating a valid ToolParameter."""
        param = ToolParameter(
            name="test_param",
            type="string",
            description="A test parameter",
            required=True
        )
        assert param.name == "test_param"
        assert param.type == "string"

    def test_tool_parameter_invalid_type(self):
        """Test that invalid parameter type raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ToolParameter(
                name="bad_param",
                type="invalid_type",
                description="Bad type"
            )
        assert "invalid parameter type" in str(exc_info.value).lower()

    def test_tool_parameter_default_with_required(self):
        """Test that required=True with default raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ToolParameter(
                name="param",
                type="string",
                description="Test",
                required=True,
                default="default_value"
            )
        assert "cannot have both required=true and a default value" in str(exc_info.value).lower()

    def test_tool_definition_valid(self):
        """Test creating a valid ToolDefinition."""
        tool = ToolDefinition(
            name="my_tool",
            description="A test tool",
            parameters=[
                ToolParameter(name="p1", type="string", description="Param 1")
            ]
        )
        assert tool.name == "my_tool"
        assert len(tool.parameters) == 1

    def test_tool_definition_duplicate_params(self):
        """Test that duplicate parameter names raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ToolDefinition(
                name="tool",
                description="Test",
                parameters=[
                    ToolParameter(name="dup", type="string", description="P1"),
                    ToolParameter(name="dup", type="string", description="P2"),
                ]
            )
        assert "duplicate parameter names" in str(exc_info.value).lower()

    def test_server_config_valid(self):
        """Test creating a valid ServerConfig."""
        config = ServerConfig(
            server_name="Test Server",
            description="A test server",
            tools=[
                ToolDefinition(
                    name="tool1",
                    description="Tool 1",
                    parameters=[]
                )
            ]
        )
        assert config.server_name == "Test Server"
        assert len(config.tools) == 1

    def test_server_config_missing_tools(self):
        """Test that ServerConfig requires at least one tool."""
        with pytest.raises(ValidationError) as exc_info:
            ServerConfig(
                server_name="Test",
                description="Test",
                tools=[]
            )
        # Pydantic should complain about min_items
        assert "at least 1 item" in str(exc_info.value).lower() or "min_items" in str(exc_info.value).lower()

    def test_server_config_duplicate_tools(self, duplicate_tools_yaml):
        """Test that duplicate tool names raise ValidationError."""
        with pytest.raises(ValueError) as exc_info:
            parse_yaml(duplicate_tools_yaml)
        assert "duplicate tool names" in str(exc_info.value).lower()


class TestValidators:
    """Test additional validation logic."""

    def test_validate_json_schema_compatibility_valid(self):
        """Test JSON schema compatibility validation with valid parameter."""
        param = ToolParameter(
            name="count",
            type="integer",
            description="Count",
            default=10,
            required=False
        )
        errors = validate_json_schema_compatibility(param)
        assert len(errors) == 0

    def test_validate_json_schema_enum_mismatch(self):
        """Test that enum values must match parameter type."""
        param = ToolParameter(
            name="number",
            type="integer",
            description="A number",
            enum_values=["not", "a", "number"]
        )
        errors = validate_json_schema_compatibility(param)
        assert len(errors) > 0
        assert any("not a valid integer" in err for err in errors)

    def test_validate_tool_definition_reserved_keyword(self):
        """Test that reserved Python keywords are rejected."""
        tool = ToolDefinition(
            name="class",  # Reserved keyword
            description="Test tool",
            parameters=[]
        )
        errors = validate_tool_definition(tool)
        assert len(errors) > 0
        assert any("reserved python keyword" in err.lower() for err in errors)

    def test_validate_server_config_comprehensive(self):
        """Test comprehensive server config validation."""
        config = ServerConfig(
            server_name="Valid Server",
            description="Test server",
            tools=[
                ToolDefinition(
                    name="valid_tool",
                    description="A valid tool",
                    parameters=[
                        ToolParameter(
                            name="valid_param",
                            type="string",
                            description="Valid parameter"
                        )
                    ]
                )
            ],
            dependencies={"requests": ">=2.31.0"}
        )
        errors = validate_server_config(config)
        assert len(errors) == 0


class TestOptionalFields:
    """Test optional fields and defaults."""

    def test_server_config_optional_author(self):
        """Test that author fields are optional."""
        config = ServerConfig(
            server_name="Test",
            description="Test server",
            tools=[
                ToolDefinition(name="tool", description="Tool", parameters=[])
            ]
        )
        assert config.author == ""
        assert config.author_email == ""

    def test_server_config_default_version(self):
        """Test default version is 0.1.0."""
        config = ServerConfig(
            server_name="Test",
            description="Test",
            tools=[
                ToolDefinition(name="tool", description="Tool", parameters=[])
            ]
        )
        assert config.version == "0.1.0"

    def test_server_config_default_python_version(self):
        """Test default Python version is >=3.11."""
        config = ServerConfig(
            server_name="Test",
            description="Test",
            tools=[
                ToolDefinition(name="tool", description="Tool", parameters=[])
            ]
        )
        assert config.python_version == ">=3.11"

    def test_tool_definition_default_return_type(self):
        """Test default return type is object."""
        tool = ToolDefinition(
            name="tool",
            description="Test",
            parameters=[]
        )
        assert tool.return_type == "object"
        assert tool.return_description == ""
