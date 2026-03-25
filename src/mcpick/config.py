"""YAML configuration parsing and validation using Pydantic."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class ToolParameter(BaseModel):
    """Definition of a tool parameter with type and validation."""

    name: str = Field(..., min_length=1, description="Parameter name")
    type: str = Field(..., description="Parameter type (string, integer, boolean, array, object)")
    description: str = Field(..., min_length=1, description="Parameter description")
    required: bool = Field(default=True, description="Whether parameter is required")
    default: Optional[Any] = Field(default=None, description="Default value if not required")
    enum_values: Optional[List[str]] = Field(default=None, description="Allowed enum values")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate parameter type is one of the allowed types."""
        valid_types = {"string", "integer", "number", "boolean", "array", "object"}
        if v not in valid_types:
            raise ValueError(
                f"Invalid parameter type '{v}'. Must be one of: {', '.join(sorted(valid_types))}"
            )
        return v

    @model_validator(mode="after")
    def validate_default_with_required(self) -> "ToolParameter":
        """Ensure default is only set when required=False."""
        if self.required and self.default is not None:
            raise ValueError(
                f"Parameter '{self.name}' cannot have both required=True and a default value"
            )
        return self


class ToolDefinition(BaseModel):
    """Definition of an MCP tool with parameters and return type."""

    name: str = Field(..., min_length=1, description="Tool name (must be valid Python identifier)")
    description: str = Field(..., min_length=1, description="Tool description")
    parameters: List[ToolParameter] = Field(default_factory=list, description="Tool parameters")
    return_type: str = Field(default="object", description="Return type")
    return_description: str = Field(default="", description="Description of return value")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate tool name is a valid Python identifier."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                f"Tool name '{v}' must be alphanumeric (underscores and hyphens allowed)"
            )
        # Convert hyphens to underscores for Python compatibility
        return v.replace("-", "_")

    @model_validator(mode="after")
    def validate_no_duplicate_params(self) -> "ToolDefinition":
        """Ensure no duplicate parameter names."""
        param_names = [p.name for p in self.parameters]
        duplicates = [name for name in param_names if param_names.count(name) > 1]
        if duplicates:
            raise ValueError(
                f"Tool '{self.name}' has duplicate parameter names: {', '.join(set(duplicates))}"
            )
        return self


class ServerConfig(BaseModel):
    """Complete MCP server configuration."""

    server_name: str = Field(..., min_length=1, description="Server name")
    description: str = Field(..., min_length=1, description="Server description")
    author: str = Field(default="", description="Author name")
    author_email: str = Field(default="", description="Author email")
    version: str = Field(default="0.1.0", description="Server version")
    tools: List[ToolDefinition] = Field(..., min_length=1, description="List of tools")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Additional Python dependencies")
    python_version: str = Field(default=">=3.11", description="Required Python version")

    @field_validator("server_name")
    @classmethod
    def validate_server_name(cls, v: str) -> str:
        """Validate server name is suitable for package naming."""
        # Allow alphanumeric, underscores, and hyphens
        if not v.replace("_", "").replace("-", "").replace(" ", "").isalnum():
            raise ValueError(
                f"Server name '{v}' contains invalid characters. Use alphanumeric, spaces, underscores, or hyphens."
            )
        return v

    @model_validator(mode="after")
    def validate_no_duplicate_tools(self) -> "ServerConfig":
        """Ensure no duplicate tool names."""
        tool_names = [t.name for t in self.tools]
        duplicates = [name for name in tool_names if tool_names.count(name) > 1]
        if duplicates:
            raise ValueError(
                f"Duplicate tool names found: {', '.join(set(duplicates))}"
            )
        return self


class GenerationOptions(BaseModel):
    """Options for project generation."""

    output_dir: Path = Field(..., description="Output directory for generated project")
    template_dir: Optional[Path] = Field(default=None, description="Custom template directory")
    overwrite: bool = Field(default=False, description="Overwrite existing project")
    create_venv: bool = Field(default=True, description="Create virtual environment")
    install_deps: bool = Field(default=True, description="Install dependencies")


def parse_yaml(config_path: Path) -> ServerConfig:
    """
    Parse and validate a YAML configuration file.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        ServerConfig: Validated server configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
        pydantic.ValidationError: If validation fails
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Failed to parse YAML file: {e}")

    if data is None:
        raise ValueError("Configuration file is empty")

    # Validate using Pydantic - let ValidationError propagate
    config = ServerConfig(**data)
    return config


def validate_yaml(config_path: Path) -> tuple[bool, Optional[str]]:
    """
    Validate a YAML configuration file without parsing fully.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        parse_yaml(config_path)
        return True, None
    except Exception as e:
        return False, str(e)
