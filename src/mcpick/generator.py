"""Project generation logic using Jinja2 templates."""

import os
import shutil
from pathlib import Path
from typing import Optional
from jinja2 import Environment, FileSystemLoader, ChoiceLoader
from rich.console import Console

from .config import ServerConfig, GenerationOptions

console = Console()


def get_template_dir() -> Path:
    """Get the directory containing Jinja2 templates."""
    return Path(__file__).parent / "templates"


def get_custom_template_dir() -> Optional[Path]:
    """Get custom template directory from environment variable if set."""
    env_dir = os.environ.get("MCPICK_TEMPLATE_DIR")
    if env_dir:
        path = Path(env_dir)
        if path.exists() and path.is_dir():
            return path
        else:
            console.print(f"[yellow]Warning:[/yellow] MCPICK_TEMPLATE_DIR set but directory not found: {env_dir}")
    return None


def list_available_templates() -> dict[str, list[Path]]:
    """
    List all available templates (built-in and custom).

    Returns:
        Dictionary with 'builtin' and 'custom' keys, each containing list of template paths
    """
    builtin_dir = get_template_dir()
    builtin_templates = sorted(builtin_dir.glob("*.j2"))

    custom_templates = []
    custom_dir = get_custom_template_dir()
    if custom_dir:
        custom_templates = sorted(custom_dir.glob("*.j2"))

    return {
        "builtin": builtin_templates,
        "custom": custom_templates
    }


def sanitize_package_name(name: str) -> str:
    """
    Convert server name to a valid Python package name.

    Args:
        name: Server name to sanitize

    Returns:
        Valid Python package name

    Raises:
        ValueError: If name cannot be sanitized to a valid identifier
    """
    # Convert to lowercase and replace spaces/hyphens with underscores
    package_name = name.lower().replace(" ", "_").replace("-", "_")

    # Remove any other invalid characters
    package_name = "".join(c if c.isalnum() or c == "_" else "" for c in package_name)

    # Ensure it doesn't start with a digit
    if package_name and package_name[0].isdigit():
        package_name = f"pkg_{package_name}"

    # Verify it's a valid identifier
    if not package_name.isidentifier():
        raise ValueError(
            f"Cannot create valid Python package name from '{name}'. "
            f"Result '{package_name}' is not a valid identifier."
        )

    return package_name


def validate_output_path(output_dir: Path) -> Path:
    """
    Validate and resolve output directory path.

    Args:
        output_dir: Output directory path

    Returns:
        Resolved absolute path

    Raises:
        ValueError: If path is invalid or suspicious
    """
    # Resolve to absolute path
    resolved = output_dir.resolve()

    # Basic path traversal check - ensure we're not trying to write to system directories
    sensitive_paths = ["/bin", "/sbin", "/usr", "/etc", "/boot", "/sys", "/proc"]
    for sensitive in sensitive_paths:
        if str(resolved).startswith(sensitive):
            raise ValueError(
                f"Cannot generate project in sensitive directory: {resolved}"
            )

    return resolved


def generate_project(config: ServerConfig, options: GenerationOptions) -> None:
    """
    Generate a complete MCP server project from configuration.

    Args:
        config: Server configuration
        options: Generation options

    Raises:
        FileExistsError: If output directory exists and overwrite=False
        ValueError: If path validation fails
        Exception: If template rendering or file writing fails
    """
    # Validate and resolve output path
    try:
        output_dir = validate_output_path(options.output_dir)
    except ValueError as e:
        raise ValueError(f"Invalid output directory: {e}") from e

    # Validate package name
    package_name = sanitize_package_name(config.server_name)

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

    # Set up Jinja2 environment with custom template support
    template_dir = options.template_dir or get_custom_template_dir()
    builtin_dir = get_template_dir()

    # Use ChoiceLoader to check custom templates first, then fall back to built-in
    if template_dir and template_dir != builtin_dir:
        loader = ChoiceLoader([
            FileSystemLoader(template_dir),
            FileSystemLoader(builtin_dir)
        ])
        console.print(f"[cyan]Using custom templates from:[/cyan] {template_dir}")
        console.print(f"[dim]Falling back to built-in templates: {builtin_dir}[/dim]")
    else:
        loader = FileSystemLoader(builtin_dir)
        console.print(f"[dim]Using built-in templates: {builtin_dir}[/dim]")

    env = Environment(
        loader=loader,
        autoescape=False,  # We're generating Python/TOML/Markdown, not HTML
        trim_blocks=True,
        lstrip_blocks=False,  # Keep leading whitespace for proper Python indentation
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
        "package_name": package_name,
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

        # Generate test files
        _render_template(env, "test_tools.py.j2", tests_dir / "test_tools.py", context)
        _render_template(env, "conftest.py.j2", tests_dir / "conftest.py", context)

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
        raise Exception(f"Failed to render template {template_name}: {e}") from e


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
