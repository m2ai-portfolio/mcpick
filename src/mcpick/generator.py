"""Project generation logic using Jinja2 templates."""

import os
import shutil
from pathlib import Path
from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from rich.console import Console

from .config import ServerConfig, GenerationOptions

console = Console()


def get_template_dir() -> Path:
    """Get the directory containing Jinja2 templates."""
    return Path(__file__).parent / "templates"


def generate_project(config: ServerConfig, options: GenerationOptions) -> None:
    """
    Generate a complete MCP server project from configuration.

    Args:
        config: Server configuration
        options: Generation options

    Raises:
        FileExistsError: If output directory exists and overwrite=False
        Exception: If template rendering or file writing fails
    """
    output_dir = options.output_dir

    # Check if output directory exists
    if output_dir.exists() and not options.overwrite:
        raise FileExistsError(
            f"Output directory already exists: {output_dir}\n"
            f"Use --overwrite to replace it."
        )

    # Create output directory
    if output_dir.exists() and options.overwrite:
        console.print(f"[yellow]Warning:[/yellow] Removing existing directory: {output_dir}")
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Set up Jinja2 environment
    template_dir = options.template_dir or get_template_dir()
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Prepare template context
    context = {
        "config": config,
        "server_name": config.server_name,
        "description": config.description,
        "author": config.author,
        "author_email": config.author_email,
        "version": config.version,
        "tools": config.tools,
        "dependencies": config.dependencies,
        "python_version": config.python_version,
        "package_name": config.server_name.lower().replace(" ", "_").replace("-", "_"),
    }

    # Create directory structure
    src_dir = output_dir / "src"
    src_dir.mkdir(exist_ok=True)

    tests_dir = output_dir / "tests"
    tests_dir.mkdir(exist_ok=True)

    # Generate files from templates
    with console.status("[bold blue]Generating project files..."):
        # Generate server.py
        _render_template(env, "server.py.j2", src_dir / "server.py", context)

        # Generate pyproject.toml
        _render_template(env, "pyproject.toml.j2", output_dir / "pyproject.toml", context)

        # Generate test file
        _render_template(env, "test_tools.py.j2", tests_dir / "test_tools.py", context)

        # Generate README.md
        _render_template(env, "README.md.j2", output_dir / "README.md", context)

        # Generate init.sh
        init_script = output_dir / "init.sh"
        _render_template(env, "init.sh.j2", init_script, context)
        init_script.chmod(0o755)  # Make executable

        # Create __init__.py files
        (tests_dir / "__init__.py").write_text("")

        # Create .gitignore
        _create_gitignore(output_dir)

    console.print("[green]✓[/green] Project structure created")
    console.print(f"[green]✓[/green] Generated {len(config.tools)} tool handler stubs")


def _render_template(env: Environment, template_name: str, output_path: Path, context: dict) -> None:
    """Render a Jinja2 template and write to file."""
    try:
        template = env.get_template(template_name)
        content = template.render(**context)
        output_path.write_text(content)
    except Exception as e:
        raise Exception(f"Failed to render template {template_name}: {e}")


def _create_gitignore(output_dir: Path) -> None:
    """Create a .gitignore file for Python MCP server projects."""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# OS
.DS_Store
Thumbs.db

# MCP specific
*.log
"""
    (output_dir / ".gitignore").write_text(gitignore_content)
