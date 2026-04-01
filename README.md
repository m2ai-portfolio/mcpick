

# MCPick ![Python](https://img.shields.io/badge/python-3.11%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green)


## Overview
MCPick is a command‑line tool that turns a single YAML configuration into a complete, production‑ready Python Model Context Protocol (MCP) server. It eliminates the repetitive boilerplate, dependency wiring, and test scaffolding so solo AI developers can focus on building tool functionality instead of project setup.

## Problem Statement
Starting an MCP server project requires manually configuring the project structure, integrating the MCP SDK, setting up stdio transport, writing tool handler stubs, managing dependencies in `pyproject.toml`, and creating test scaffolding—a 2‑4 hour repetitive process that slows down rapid prototyping.

## Features
- **YAML configuration parsing & validation** – reads `server_name`, `description`, `tools[]`, optional `dependencies` and validates schemas with clear error messages.  
- **MCP server code generation** – produces `server.py` with proper SDK imports, stdio transport, typed tool handlers, and registration code.  
- **Full project scaffolding** – creates `pyproject.toml`, `tests/`, `README.md`, `init.sh`, `.gitignore` following Python packaging best practices.  
- **Interactive tool wizard** – `--interactive` prompts for server metadata and tool definitions, generating a YAML file ready for project creation.  
- **Custom template support** – users can place Jinja2 templates in `MCPICK_TEMPLATE_DIR` to override or extend generated files.  
- **Built‑in testing** – generated projects include pytest fixtures and test cases that run out‑of‑the‑box.  
- **Dependency management** – user‑specified `dependencies` are added to `pyproject.toml` alongside the MCP SDK.  
- **Cross‑platform CLI** – built with Click and Rich for a friendly, colored terminal experience.

## Tech Stack
- **Python 3.11+** – core language  
- **Click** – CLI framework  
- **Jinja2** – template engine for file generation  
- **PyYAML** – YAML parsing  
- **Pydantic** – configuration validation  
- **pytest** – testing framework  
- **mcp** – Model Context Protocol SDK (in generated projects)  
- **pathlib** – filesystem handling  
- **rich** – formatted CLI output  

## Quick Start / Installation
1. **Install MCPick** (from PyPI or source):  
   ```bash
   pip install mcpick
   ```
2. **Verify installation**:  
   ```bash
   mcpick --help
   ```
3. **Generate a server from an example**:  
   ```bash
   mcpick generate examples/calculator.yaml
   ```
4. **Set up the generated project**:  
   ```bash
   cd <server_name>
   chmod +x init.sh
   ./init.sh   # creates venv, installs deps
   source .venv/bin/activate
   ```
5. **Run the MCP server**:  
   ```bash
   python src/server.py
   ```
6. **Run the test suite**:  
   ```bash
   pytest
   ```

## Usage
- **Create a new server**:  
  ```bash
  mcpick generate my_tool.yaml
  ```
- **Interactive mode**:  
  ```bash
  mcpick generate --interactive
  ```
- **Validate a YAML config without generating**:  
  ```bash
  mcpick validate my_tool.yaml
  ```
- **Use a custom template directory**:  
  ```bash
  export MCPICK_TEMPLATE_DIR=$HOME/.mcpick/templates
  mcpick generate my_tool.yaml
  ```
- **Show version**:  
  ```bash
  mcpick --version
  ```

## Architecture
MCPick consists of a Click‑based CLI that parses arguments, loads and validates YAML via Pydantic, selects Jinja2 templates (default or user‑provided), renders files into a target directory, and writes supporting files (`pyproject.toml`, `README.md`, `init.sh`, etc.). The generated MCP server follows the official SDK pattern: stdio transport, automatic tool registration, and async handler functions. All generated code is lint‑ and type‑checked by the included pytest suite.

## License
MIT © 2025 MCPick Contributors. See the `LICENSE` file for details.