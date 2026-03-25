"""Command-line interface for MCPick."""

import sys
import os
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from pydantic import ValidationError

from .config import parse_yaml, validate_yaml, GenerationOptions
from .validators import validate_server_config, validate_custom_templates
from .generator import generate_project, list_available_templates, get_custom_template_dir
from .wizard import run_wizard, prompt_generate_project

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="mcpick")
def main():
    """MCPick - Generate production-ready MCP server projects from YAML configurations."""
    pass


@main.command()
@click.argument("config_file", type=click.Path(exists=True, path_type=Path), required=False)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Launch interactive wizard to create configuration",
)
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
@click.option(
    "--template-dir",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Custom template directory (overrides MCPICK_TEMPLATE_DIR)",
)
def generate(config_file, interactive, output_dir, overwrite, no_venv, no_install, template_dir):
    """Generate an MCP server project from a YAML configuration file or interactive wizard."""
    try:
        # Check if we should use interactive mode
        if interactive or config_file is None:
            # Run the interactive wizard
            config, yaml_path = run_wizard()

            # Ask if user wants to generate project now
            should_generate, wizard_output_dir = prompt_generate_project(config, yaml_path)

            if not should_generate:
                console.print("\n[yellow]Project generation skipped.[/yellow]")
                console.print(f"[dim]You can generate the project later using:[/dim]")
                if yaml_path:
                    console.print(f"[dim]  mcpick generate {yaml_path}[/dim]")
                return

            # Use wizard-provided output directory if not overridden by CLI option
            if output_dir is None:
                output_dir = wizard_output_dir
        else:
            # Parse and validate configuration from file
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

        # Validate custom template directory if provided
        if template_dir:
            validation_errors_dict = validate_custom_templates(template_dir)
            if validation_errors_dict:
                console.print("[bold yellow]Custom template validation warnings:[/bold yellow]")
                for template_name, errors in validation_errors_dict.items():
                    if template_name == "_error":
                        for error in errors:
                            console.print(f"  [red]✗[/red] {error}")
                        sys.exit(1)
                    else:
                        console.print(f"  [yellow]⚠[/yellow] {template_name}:")
                        for error in errors:
                            console.print(f"      Missing required variable: {error}")

        # Create generation options
        options = GenerationOptions(
            output_dir=output_dir,
            template_dir=template_dir,
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
def wizard():
    """Launch interactive wizard to create a server configuration."""
    try:
        config, yaml_path = run_wizard()

        # Ask if user wants to generate project now
        should_generate, output_dir = prompt_generate_project(config, yaml_path)

        if not should_generate:
            console.print("\n[yellow]Project generation skipped.[/yellow]")
            console.print(f"[dim]You can generate the project later using:[/dim]")
            if yaml_path:
                console.print(f"[dim]  mcpick generate {yaml_path}[/dim]")
            return

        # Create generation options
        options = GenerationOptions(
            output_dir=output_dir,
            template_dir=None,
            overwrite=False,
            create_venv=True,
            install_deps=True,
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


@main.command(name="list-templates")
def list_templates():
    """List available built-in and custom templates."""
    try:
        templates = list_available_templates()

        # Check if custom template dir is set
        custom_dir = get_custom_template_dir()
        env_var_set = "MCPICK_TEMPLATE_DIR" in os.environ

        # Display header
        console.print(Panel(
            "[bold cyan]MCPick Template Overview[/bold cyan]\n\n"
            f"Built-in templates: {len(templates['builtin'])}\n"
            f"Custom templates: {len(templates['custom'])}",
            title="Available Templates",
            border_style="cyan"
        ))

        # Display built-in templates
        console.print("\n[bold]Built-in Templates:[/bold]")
        if templates['builtin']:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Template", style="cyan")
            table.add_column("Status", style="green")

            for template_path in templates['builtin']:
                template_name = template_path.name
                # Check if this template is overridden by custom template
                is_overridden = any(t.name == template_name for t in templates['custom'])
                status = "[yellow]Overridden by custom[/yellow]" if is_overridden else "[green]Active[/green]"
                table.add_row(template_name, status)

            console.print(table)
        else:
            console.print("[dim]  No built-in templates found[/dim]")

        # Display custom templates
        if env_var_set or templates['custom']:
            console.print("\n[bold]Custom Templates:[/bold]")
            if custom_dir:
                console.print(f"[dim]Location: {custom_dir}[/dim]\n")

            if templates['custom']:
                # Validate custom templates
                validation_results = validate_custom_templates(custom_dir)

                table = Table(show_header=True, header_style="bold cyan")
                table.add_column("Template", style="cyan")
                table.add_column("Validation", style="white")

                for template_path in templates['custom']:
                    template_name = template_path.name
                    if template_name in validation_results:
                        missing = validation_results[template_name]
                        status = f"[yellow]⚠ Missing: {', '.join(missing)}[/yellow]"
                    else:
                        status = "[green]✓ Valid[/green]"
                    table.add_row(template_name, status)

                console.print(table)

                # Show validation warnings
                if validation_results:
                    console.print("\n[bold yellow]Validation Warnings:[/bold yellow]")
                    console.print("[dim]Custom templates are missing required template variables.[/dim]")
                    console.print("[dim]They may not generate valid projects.[/dim]")
            else:
                console.print(f"[dim]  MCPICK_TEMPLATE_DIR set but no .j2 templates found in: {custom_dir}[/dim]")
        else:
            console.print("\n[bold]Custom Templates:[/bold]")
            console.print("[dim]  No custom template directory set[/dim]")
            console.print("[dim]  Set MCPICK_TEMPLATE_DIR environment variable or use --template-dir flag[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error listing templates:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
