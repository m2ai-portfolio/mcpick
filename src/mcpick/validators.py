"""Additional validation logic for MCP server configurations."""

from typing import List, Dict, Any
from pathlib import Path
import re
from .config import ServerConfig, ToolDefinition, ToolParameter


def validate_json_schema_compatibility(parameter: ToolParameter) -> List[str]:
    """
    Validate that a tool parameter is compatible with JSON Schema.

    Args:
        parameter: Tool parameter to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Check enum values match type
    if parameter.enum_values:
        if parameter.type == "integer":
            for val in parameter.enum_values:
                try:
                    int(val)
                except (ValueError, TypeError):
                    errors.append(
                        f"Parameter '{parameter.name}': enum value '{val}' is not a valid integer"
                    )
        elif parameter.type == "number":
            for val in parameter.enum_values:
                try:
                    float(val)
                except (ValueError, TypeError):
                    errors.append(
                        f"Parameter '{parameter.name}': enum value '{val}' is not a valid number"
                    )
        elif parameter.type == "boolean":
            valid_bool_values = {"true", "false", "True", "False", "1", "0"}
            for val in parameter.enum_values:
                if str(val) not in valid_bool_values:
                    errors.append(
                        f"Parameter '{parameter.name}': enum value '{val}' is not a valid boolean"
                    )

    # Check default value matches type if provided
    if parameter.default is not None:
        if parameter.type == "integer" and not isinstance(parameter.default, int):
            errors.append(
                f"Parameter '{parameter.name}': default value must be an integer"
            )
        elif parameter.type == "boolean" and not isinstance(parameter.default, bool):
            errors.append(
                f"Parameter '{parameter.name}': default value must be a boolean"
            )
        elif parameter.type == "array" and not isinstance(parameter.default, list):
            errors.append(
                f"Parameter '{parameter.name}': default value must be an array"
            )
        elif parameter.type == "object" and not isinstance(parameter.default, dict):
            errors.append(
                f"Parameter '{parameter.name}': default value must be an object"
            )

    return errors


def validate_tool_definition(tool: ToolDefinition) -> List[str]:
    """
    Validate a complete tool definition.

    Args:
        tool: Tool definition to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Validate each parameter
    for param in tool.parameters:
        param_errors = validate_json_schema_compatibility(param)
        errors.extend(param_errors)

    # Check for reserved Python keywords
    reserved_keywords = {
        "False", "None", "True", "and", "as", "assert", "async", "await",
        "break", "class", "continue", "def", "del", "elif", "else", "except",
        "finally", "for", "from", "global", "if", "import", "in", "is",
        "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
        "try", "while", "with", "yield"
    }

    if tool.name in reserved_keywords:
        errors.append(f"Tool name '{tool.name}' is a reserved Python keyword")

    for param in tool.parameters:
        if param.name in reserved_keywords:
            errors.append(
                f"Tool '{tool.name}': parameter name '{param.name}' is a reserved Python keyword"
            )

    return errors


def validate_server_config(config: ServerConfig) -> List[str]:
    """
    Perform comprehensive validation on a server configuration.

    Args:
        config: Server configuration to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Validate each tool
    for tool in config.tools:
        tool_errors = validate_tool_definition(tool)
        errors.extend(tool_errors)

    # Validate dependencies format
    for dep_name, dep_version in config.dependencies.items():
        if not dep_name or not isinstance(dep_name, str):
            errors.append(f"Invalid dependency name: {dep_name}")
        if not dep_version or not isinstance(dep_version, str):
            errors.append(f"Invalid version specifier for dependency '{dep_name}': {dep_version}")

    # Validate Python version format
    if not config.python_version.startswith(">=") and not config.python_version.startswith("=="):
        errors.append(
            f"Python version '{config.python_version}' should start with '>=' or '=='"
        )

    return errors


# Template variable requirements for each template type
TEMPLATE_REQUIRED_VARS = {
    "server.py.j2": ["config", "tools", "package_name"],
    "pyproject.toml.j2": ["config", "package_name"],
    "test_tools.py.j2": ["config", "tools", "package_name"],
    "README.md.j2": ["config", "tools", "package_name"],
    "init.sh.j2": ["config", "package_name"],
    "conftest.py.j2": ["config", "package_name"],
}


def validate_template(template_path: Path, required_vars: List[str]) -> List[str]:
    """
    Validate that a custom template references required template variables.

    Args:
        template_path: Path to the template file
        required_vars: List of required variable names

    Returns:
        List of missing variable names (empty if all required variables are present)
    """
    if not template_path.exists():
        return [f"Template file not found: {template_path}"]

    try:
        content = template_path.read_text()
    except Exception as e:
        return [f"Failed to read template: {e}"]

    missing_vars = []

    # Check for each required variable
    for var in required_vars:
        # Look for variable references in various Jinja2 forms:
        # {{ var }}, {{ var. }}, {% for item in var %}, etc.
        patterns = [
            r"\{\{\s*" + var + r"[\s\.\}]",  # {{ var or {{ var.
            r"\{\{\s*" + var + r"\|",  # {{ var|filter
            r"\{%\s*for\s+\w+\s+in\s+" + var + r"\s*%\}",  # {% for x in var %}
            r"\{%\s*if\s+" + var + r"[\s\.]",  # {% if var or {% if var.
        ]

        found = any(re.search(pattern, content) for pattern in patterns)

        if not found:
            missing_vars.append(var)

    return missing_vars


def validate_custom_templates(custom_dir: Path) -> Dict[str, List[str]]:
    """
    Validate all custom templates in a directory.

    Args:
        custom_dir: Path to custom templates directory

    Returns:
        Dictionary mapping template names to lists of validation errors
    """
    if not custom_dir.exists():
        return {"_error": [f"Custom template directory not found: {custom_dir}"]}

    if not custom_dir.is_dir():
        return {"_error": [f"Custom template path is not a directory: {custom_dir}"]}

    validation_results = {}

    for template_name, required_vars in TEMPLATE_REQUIRED_VARS.items():
        template_path = custom_dir / template_name
        if template_path.exists():
            errors = validate_template(template_path, required_vars)
            if errors:
                validation_results[template_name] = errors

    return validation_results
