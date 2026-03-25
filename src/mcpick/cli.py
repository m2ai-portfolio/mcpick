"""Command-line interface for MCPick."""

import sys
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from pydantic import ValidationError

from .config import parse_yaml, validate_yaml, GenerationOptions
from .validators import validate_server_config
from .generator import generate_project

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="mcpick")
def main():
    """MCPick - Generate production-ready MCP server projects from YAML configurations."""
    pass


@main.command()
@click.argument("config_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory for generated project (defaults to server name)",
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite existing project directory",
)
@click.option(
    "--no-venv",
    is_flag=True,
    help="Skip virtual environment creation",
)
@click.option(
    "--no-install",
    is_flag=True,
    help="Skip dependency installation",
)
def generate(config_file, output_dir, overwrite, no_venv, no_install):
    """Generate an MCP server project from a YAML configuration file."""
    try:
        # Parse and validate configuration
        with console.status("[bold blue]Parsing configuration..."):
            config = parse_yaml(config_file)

        # Run additional validation
        validation_errors = validate_server_config(config)
        if validation_errors:
            console.print("[bold red]Configuration validation failed:[/bold red]")
            for error in validation_errors:
                console.print(f"  [red]✗[/red] {error}")
            sys.exit(1)

        # Determine output directory
        if output_dir is None:
            output_dir = Path.cwd() / config.server_name.lower().replace(" ", "-")
        else:
            output_dir = Path(output_dir)

        # Create generation options
        options = GenerationOptions(
            output_dir=output_dir,
            template_dir=None,
            overwrite=overwrite,
            create_venv=not no_venv,
            install_deps=not no_install,
        )

        # Generate project
        console.print(f"\n[bold green]Generating MCP server project:[/bold green] {config.server_name}")
        console.print(f"[dim]Output directory: {output_dir}[/dim]\n")

        generate_project(config, options)

        # Success message
        console.print(Panel(
            f"[bold green]✓ Project generated successfully![/bold green]\n\n"
            f"Next steps:\n"
            f"  1. cd {output_dir}\n"
            f"  2. chmod +x init.sh && ./init.sh\n"
            f"  3. Implement tool handlers in src/server.py\n"
            f"  4. Run tests with: pytest tests/",
            title="Success",
            border_style="green"
        ))

    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except ValidationError as e:
        console.print("[bold red]Configuration validation failed:[/bold red]")
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            console.print(f"  [red]✗[/red] {field}: {error['msg']}")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        sys.exit(1)


@main.command()
@click.argument("config_file", type=click.Path(exists=True, path_type=Path))
def validate(config_file):
    """Validate a YAML configuration file without generating a project."""
    try:
        # Parse configuration
        with console.status("[bold blue]Validating configuration..."):
            config = parse_yaml(config_file)

            # Run additional validation
            validation_errors = validate_server_config(config)

        if validation_errors:
            console.print("[bold red]Configuration validation failed:[/bold red]")
            for error in validation_errors:
                console.print(f"  [red]✗[/red] {error}")
            sys.exit(1)

        # Display success
        console.print(f"[bold green]✓ Configuration is valid[/bold green]")

        # Display summary
        table = Table(title="Configuration Summary", show_header=True, header_style="bold cyan")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Server Name", config.server_name)
        table.add_row("Description", config.description)
        table.add_row("Version", config.version)
        table.add_row("Author", config.author or "[dim]not specified[/dim]")
        table.add_row("Tools", str(len(config.tools)))
        table.add_row("Dependencies", str(len(config.dependencies)))

        console.print("\n")
        console.print(table)

        # List tools
        if config.tools:
            console.print("\n[bold]Tools:[/bold]")
            for tool in config.tools:
                param_count = len(tool.parameters)
                console.print(f"  [green]✓[/green] {tool.name} ({param_count} parameters)")

    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except ValidationError as e:
        console.print("[bold red]Configuration validation failed:[/bold red]")
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            console.print(f"  [red]✗[/red] {field}: {error['msg']}")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
