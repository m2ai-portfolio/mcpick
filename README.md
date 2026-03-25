# MCPick

A production-ready Python CLI tool that generates MCP (Model Context Protocol) server projects from YAML configuration files.

## Overview

MCPick streamlines the creation of Python MCP servers by providing a templating and scaffolding system. Instead of manually writing boilerplate code, developers can define their MCP server configuration in a simple YAML format and generate a fully functional project structure.

## Tech Stack

- **Python**: 3.11+
- **CLI Framework**: Click
- **Templating**: Jinja2
- **Configuration**: PyYAML
- **Data Validation**: Pydantic
- **Testing**: pytest
- **Protocol SDK**: mcp (Model Context Protocol)
- **Terminal UI**: Rich

## Features

- Generate production-ready MCP server projects from YAML configuration
- Customizable project templates with Jinja2
- Data validation with Pydantic schemas
- Built-in development environment setup
- Cross-platform compatibility (Linux, macOS, Git Bash on Windows)

## Quick Start

### Setup Development Environment

Run the initialization script to set up your development environment:

```bash
./init.sh
```

This script will:
1. Create a Python virtual environment (`.venv`)
2. Activate the environment
3. Install MCPick in editable mode with all development dependencies

After setup, activate the virtual environment:

```bash
source .venv/bin/activate  # On Linux/macOS
# or
.venv\Scripts\activate     # On Windows
```

## Usage

### Generate a New MCP Server Project

Create a `config.yaml` file defining your MCP server:

```yaml
name: my-mcp-server
description: My custom MCP server
version: 0.1.0
```

Then generate the project:

```bash
mcpick generate config.yaml
```

This creates a new directory with the project structure ready for development.

## Development

After running `./init.sh`, you can:

- Run tests: `pytest`
- Check code style: `ruff check .`
- Format code: `ruff format .`
- Build the package: `pip install -e .[dev]`

## Project Structure

```
mcpick/
├── src/mcpick/
│   ├── cli.py              # Click CLI commands
│   ├── generator.py        # Project generation logic
│   ├── templates/          # Jinja2 templates
│   └── schemas.py          # Pydantic schemas
├── tests/
├── README.md
├── pyproject.toml          # Project configuration
├── init.sh                 # Development setup script
└── .gitignore
```

## License

MIT

## Contributing

Contributions are welcome! Please ensure all tests pass and code follows the project style guidelines.
