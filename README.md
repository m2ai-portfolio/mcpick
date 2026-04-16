

<p align="center">
  <img src="assets/infographic.png" alt="MCPick" width="800">
</p>

<h3 align="center">CLI tool that generates a complete, buildable MCP server project from a single YAML config file. Outputs Python project with tool stubs, pyproject.toml, tests, and init.sh. Supports stdio transport.</h3>

<p align="center">
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#features">Features</a> &bull;
  <a href="#examples">Examples</a> &bull;
  <a href="#contributing">Contributing</a>
</p>

## What is this?
MCPick is a command-line utility that transforms a simple YAML description into a ready-to-build MCP server project. It eliminates boilerplate so solo AI developers can focus on implementing tools instead of setting up projects.

Example usage:
```
$ mcpick generate examples/calculator.yaml
✔ Generated project in ./calculator-server
```

## Problem
Setting up a new MCP server requires significant boilerplate: project structure, SDK wiring, transport configuration, and test scaffolding. This repetitive setup slows down developers who want to ship MCP tools quickly.

## Features
| Feature | Description |
|---------|-------------|
| YAML Configuration Parsing and Validation | Reads a YAML file, validates required fields, and provides clear error messages for missing or malformed data. |
| MCP Server Code Generation | Produces a full Python server with stdio transport, tool handler stubs, and proper async/await patterns. |
| Project Structure and Dependency Management | Creates pyproject.toml, test suite, README, init.sh, and .gitignore following Python packaging best practices. |
| Interactive Tool Definition Wizard | Launches a prompt‑driven interface to build a YAML config when no file is supplied. |
| Template Customization and Extension | Allows users to override Jinja2 templates or add custom ones for specialized project layouts. |
| Built‑in Testing Support | Generates pytest fixtures and test cases for each tool so the generated project can be validated immediately. |

## Quick Start
1. Clone the repository:
   ```
   git clone https://github.com/m2ai-portfolio/mcpick.git
   cd mcpick
   ```
2. Install the tool in editable mode:
   ```
   pip install -e .
   ```
3. Generate a server from the example config:
   ```
   mcpick generate examples/calculator.yaml
   ```
4. Enter the generated directory and set up the environment:
   ```
   cd calculator-server
   chmod +x init.sh
   ./init.sh
   source .venv/bin/activate
   ```
5. Run the test suite to verify everything works:
   ```
   pytest
   ```

## Examples
**Basic generation**  
Create a simple calculator MCP server:
```
$ mcpick generate examples/calculator.yaml
✔ Generated project in ./calculator-server
$ ls calculator-server
README.md  init.sh  pyproject.toml  src  tests
```

**Interactive wizard**  
Build a config via prompts and immediately generate the project:
```
$ mcpick generate --interactive
? Server name: weather-tools
? Description: A set of tools for fetching weather data
? Author name: Jane Doe
? Author email: jane@example.com
? Add a tool? (y/n) y
? Tool name: get_current
? Tool description: Returns current temperature for a location
? Parameter name: location
? Parameter type: string
? Required? (y/n) y
? Add another parameter? (y/n) n
? Add another tool? (y/n) n
✔ Config written to weather-tools.yaml
? Generate project now? (y/n) y
✔ Generated project in ./weather-tools
```

**Custom template usage**  
Generate a server using a user‑defined template directory:
```
$ mcpick generate examples/database_tools.yaml --template-dir ./examples/custom_templates/database
✔ Generated project in ./database-server
$ grep -r "custom_logic" database-server/
src/database-server/server.py:    # Custom logic from template
```

## File Structure
```
MCPick/
  src/                    # Core source code
    mcpick/               # MCPick package
      __init__.py
      cli.py              # Click‑based command line interface
      config.py           # YAML parsing and validation models
      generator.py        # Jinja2 template rendering and file writing
      templates/          # Default Jinja2 templates for server, tests, etc.
  tests/                  # Test suite for MCPick itself
    test_cli.py
    test_config.py
    test_generator.py
  examples/               # Sample configs and custom templates
    calculator.yaml
    database_tools.yaml
    weather_api.yaml
    custom_templates/
      api_wrapper/
        server.py.j2
      database/
        server.py.j2
      README.md
  screenshots/            # Demonstration output files (omitted for brevity)
  pyproject.toml
  README.md
  LICENSE
```

## Tech Stack
| Technology | Purpose |
|------------|---------|
| Python 3.11+ | Core language for the CLI and generated projects |
| Click | Builds the command‑line interface with rich argument handling |
| Jinja2 | Templating engine for generating Python files and project structure |
| PyYAML | Parses YAML configuration files |
| Pydantic | Validates configuration data and provides data models |
| pytest | Testing framework for both MCPick and generated projects |
| mcp | Model Context Protocol SDK used in generated servers |
| pathlib | Modern, cross‑platform file system operations |
| rich | Enhanced CLI output with progress indicators and formatting |

## Contributing
Fork the repo, create a feature branch, make changes, run `pytest`, and submit a pull request. Please keep commits atomic and update tests when adding new functionality.

## License
MIT

## Author
Matthew Snow -- [M2AI](https://m2ai.co) | [@m2ai-portfolio](https://github.com/m2ai-portfolio)