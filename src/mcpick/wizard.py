"""Interactive wizard for creating MCP server configurations."""

from pathlib import Path
from typing import Optional, Dict, List, Any
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import yaml

from .config import ServerConfig, ToolDefinition, ToolParameter

console = Console()


def run_wizard() -> tuple[ServerConfig, Optional[Path]]:
    """
    Run the interactive wizard to create a server configuration.

    Returns:
        Tuple of (ServerConfig, optional YAML output path)
    """
    console.print(Panel(
        "[bold cyan]MCPick Interactive Wizard[/bold cyan]\n\n"
        "This wizard will guide you through creating an MCP server configuration.",
        border_style="cyan"
    ))

    # Step 1: Get server metadata
    console.print("\n[bold]Step 1: Server Metadata[/bold]")
    metadata = prompt_server_metadata()

    # Step 2: Add tools
    console.print("\n[bold]Step 2: Tool Definitions[/bold]")
    tools = []
    while True:
        tool = prompt_tool_definition(len(tools) + 1)
        tools.append(tool)

        if not prompt_add_more_tools():
            break

    # Step 3: Additional dependencies
    console.print("\n[bold]Step 3: Dependencies (optional)[/bold]")
    dependencies = prompt_dependencies()

    # Create the configuration
    config = ServerConfig(
        server_name=metadata["server_name"],
        description=metadata["description"],
        author=metadata["author"],
        author_email=metadata["author_email"],
        version=metadata["version"],
        tools=tools,
        dependencies=dependencies,
        python_version=metadata.get("python_version", ">=3.11")
    )

    # Display summary
    display_config_summary(config)

    # Ask if user wants to save YAML
    yaml_path = None
    if click.confirm("\nDo you want to save this configuration to a YAML file?", default=True):
        default_filename = config.server_name.lower().replace(" ", "-") + ".yaml"
        filename = click.prompt("Enter filename", default=default_filename, type=str)
        yaml_path = Path(filename)
        save_yaml_config(config, yaml_path)
        console.print(f"[green]✓[/green] Configuration saved to: {yaml_path}")

    return config, yaml_path


def prompt_server_metadata() -> Dict[str, str]:
    """
    Prompt for server metadata (name, description, author, etc.).

    Returns:
        Dictionary with server metadata
    """
    server_name = click.prompt(
        "Server name",
        type=str,
        default="My MCP Server"
    )

    description = click.prompt(
        "Description",
        type=str,
        default="An MCP server generated with MCPick"
    )

    author = click.prompt(
        "Author name",
        type=str,
        default=""
    )

    author_email = click.prompt(
        "Author email",
        type=str,
        default=""
    )

    version = click.prompt(
        "Version",
        type=str,
        default="0.1.0"
    )

    python_version = click.prompt(
        "Python version requirement",
        type=str,
        default=">=3.11"
    )

    return {
        "server_name": server_name,
        "description": description,
        "author": author,
        "author_email": author_email,
        "version": version,
        "python_version": python_version
    }


def prompt_tool_definition(tool_number: int) -> ToolDefinition:
    """
    Prompt for a single tool's details.

    Args:
        tool_number: The number of this tool (for display purposes)

    Returns:
        ToolDefinition object
    """
    console.print(f"\n[cyan]Tool {tool_number}:[/cyan]")

    # Tool name with validation
    while True:
        name = click.prompt("  Tool name", type=str)
        # Validate it's a reasonable identifier
        sanitized = name.replace("-", "_").replace(" ", "_")
        if sanitized and (sanitized[0].isalpha() or sanitized[0] == '_') and sanitized.replace("_", "").isalnum():
            break
        console.print("  [red]Invalid tool name. Use letters, numbers, underscores, or hyphens.[/red]")

    description = click.prompt("  Description", type=str)

    # Parameters
    console.print("  [dim]Now let's add parameters for this tool (press Enter with empty name to finish)[/dim]")
    parameters = prompt_tool_parameters()

    # Return type
    return_type = click.prompt(
        "  Return type",
        type=click.Choice(["string", "integer", "number", "boolean", "array", "object"], case_sensitive=False),
        default="object"
    )

    return_description = click.prompt(
        "  Return description",
        type=str,
        default="Tool execution result"
    )

    return ToolDefinition(
        name=name,
        description=description,
        parameters=parameters,
        return_type=return_type,
        return_description=return_description
    )


def prompt_tool_parameters() -> List[ToolParameter]:
    """
    Prompt for tool parameters.

    Returns:
        List of ToolParameter objects
    """
    parameters = []

    while True:
        console.print(f"\n  [dim]Parameter {len(parameters) + 1}:[/dim]")

        # Empty name ends parameter input
        name = click.prompt("    Parameter name (or press Enter to finish)", type=str, default="", show_default=False)
        if not name:
            break

        # Validate parameter name
        if not name.replace("_", "").isalnum():
            console.print("    [red]Invalid parameter name. Use letters, numbers, and underscores.[/red]")
            continue

        param_type = click.prompt(
            "    Type",
            type=click.Choice(["string", "integer", "number", "boolean", "array", "object"], case_sensitive=False),
            default="string"
        )

        description = click.prompt("    Description", type=str)

        required = click.confirm("    Required?", default=True)

        default_value = None
        if not required:
            if click.confirm("    Provide a default value?", default=False):
                default_value = click.prompt("    Default value", type=str)
                # Try to convert to appropriate type
                if param_type == "integer":
                    try:
                        default_value = int(default_value)
                    except ValueError:
                        console.print("    [yellow]Warning: Could not convert to integer, storing as string[/yellow]")
                elif param_type == "number":
                    try:
                        default_value = float(default_value)
                    except ValueError:
                        console.print("    [yellow]Warning: Could not convert to number, storing as string[/yellow]")
                elif param_type == "boolean":
                    default_value = default_value.lower() in ("true", "yes", "1")

        parameters.append(ToolParameter(
            name=name,
            type=param_type,
            description=description,
            required=required,
            default=default_value
        ))

    return parameters


def prompt_add_more_tools() -> bool:
    """
    Ask if user wants to add another tool.

    Returns:
        True if user wants to add more tools
    """
    return click.confirm("\nAdd another tool?", default=True)


def prompt_dependencies() -> Dict[str, str]:
    """
    Prompt for additional Python dependencies.

    Returns:
        Dictionary of package name to version specifier
    """
    if not click.confirm("Do you want to add additional Python dependencies?", default=False):
        return {}

    dependencies = {}
    console.print("[dim]Enter dependencies one at a time (press Enter with empty name to finish)[/dim]")

    while True:
        package_name = click.prompt("\nPackage name (or press Enter to finish)", type=str, default="", show_default=False)
        if not package_name:
            break

        version = click.prompt(
            "Version specifier",
            type=str,
            default="*"
        )

        dependencies[package_name] = version

    return dependencies


def display_config_summary(config: ServerConfig) -> None:
    """
    Display a summary of the configuration.

    Args:
        config: Server configuration to summarize
    """
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]Configuration Summary[/bold cyan]")
    console.print("=" * 60)

    # Server info table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Server Name", config.server_name)
    table.add_row("Description", config.description)
    table.add_row("Version", config.version)
    if config.author:
        table.add_row("Author", f"{config.author}" + (f" <{config.author_email}>" if config.author_email else ""))
    table.add_row("Python Version", config.python_version)
    table.add_row("Tools", str(len(config.tools)))

    console.print(table)

    # Tools list
    console.print("\n[bold]Tools:[/bold]")
    for i, tool in enumerate(config.tools, 1):
        param_count = len(tool.parameters)
        console.print(f"  {i}. [green]{tool.name}[/green] - {tool.description}")
        console.print(f"     [dim]{param_count} parameter(s), returns {tool.return_type}[/dim]")

    # Dependencies
    if config.dependencies:
        console.print("\n[bold]Dependencies:[/bold]")
        for pkg, version in config.dependencies.items():
            console.print(f"  • {pkg}: {version}")

    console.print("=" * 60)


def save_yaml_config(config: ServerConfig, output_path: Path) -> None:
    """
    Save the configuration to a YAML file.

    Args:
        config: Server configuration to save
        output_path: Path to save the YAML file
    """
    # Convert config to dict for YAML serialization
    config_dict = {
        "server_name": config.server_name,
        "description": config.description,
        "author": config.author,
        "author_email": config.author_email,
        "version": config.version,
        "python_version": config.python_version,
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": [
                    {
                        "name": param.name,
                        "type": param.type,
                        "description": param.description,
                        "required": param.required,
                        **({"default": param.default} if param.default is not None else {}),
                        **({"enum_values": param.enum_values} if param.enum_values else {})
                    }
                    for param in tool.parameters
                ],
                "return_type": tool.return_type,
                "return_description": tool.return_description
            }
            for tool in config.tools
        ],
        "dependencies": config.dependencies
    }

    # Write YAML file
    with open(output_path, "w") as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False, indent=2)


def prompt_generate_project(config: ServerConfig, yaml_path: Optional[Path] = None) -> tuple[bool, Optional[Path]]:
    """
    Ask if user wants to generate the project immediately.

    Args:
        config: Server configuration
        yaml_path: Path to saved YAML file (if any)

    Returns:
        Tuple of (should_generate, output_directory)
    """
    if not click.confirm("\nDo you want to generate the project now?", default=True):
        return False, None

    default_dir = config.server_name.lower().replace(" ", "-")
    output_dir = click.prompt(
        "Output directory",
        type=str,
        default=default_dir
    )

    return True, Path(output_dir)
