# Custom Template Examples

This directory contains example custom templates for MCPick that demonstrate specialized MCP server patterns.

## Available Templates

### 1. Database Template (`database/`)

A template for MCP servers that need database access with connection pooling.

**Features:**
- SQLite connection pool
- Database initialization
- Async context manager for connections
- Example schema setup

**Usage:**
```bash
export MCPICK_TEMPLATE_DIR=/path/to/examples/custom_templates/database
mcpick generate your-config.yaml
```

Or:
```bash
mcpick generate your-config.yaml --template-dir examples/custom_templates/database
```

### 2. API Wrapper Template (`api_wrapper/`)

A template for MCP servers that wrap external REST APIs.

**Features:**
- HTTP client using httpx
- Support for GET, POST, PUT, DELETE
- Authentication headers
- Error handling for HTTP errors

**Usage:**
```bash
export MCPICK_TEMPLATE_DIR=/path/to/examples/custom_templates/api_wrapper
mcpick generate your-config.yaml
```

## Creating Your Own Templates

### Template Structure

Custom templates can override any of the built-in templates:
- `server.py.j2` - Main server implementation
- `pyproject.toml.j2` - Python project configuration
- `test_tools.py.j2` - Test suite
- `README.md.j2` - Documentation
- `init.sh.j2` - Initialization script
- `conftest.py.j2` - Pytest configuration

You only need to provide the templates you want to customize. MCPick will fall back to built-in templates for the rest.

### Required Template Variables

Each template must reference certain variables to generate valid projects:

- **server.py.j2**: `config`, `tools`, `package_name`
- **pyproject.toml.j2**: `config`, `package_name`
- **test_tools.py.j2**: `config`, `tools`, `package_name`
- **README.md.j2**: `config`, `tools`, `package_name`
- **init.sh.j2**: `config`, `package_name`
- **conftest.py.j2**: `config`, `package_name`

### Validation

Check your custom templates:
```bash
export MCPICK_TEMPLATE_DIR=/path/to/your/templates
mcpick list-templates
```

This will show any missing required variables.

## Example: Partial Override

You can override just `server.py.j2` while using built-in templates for everything else:

```bash
mkdir my-templates
cp examples/custom_templates/database/server.py.j2 my-templates/
# Edit my-templates/server.py.j2 as needed
export MCPICK_TEMPLATE_DIR=my-templates
mcpick generate config.yaml
```

MCPick will use your custom `server.py.j2` and built-in templates for `pyproject.toml.j2`, `README.md.j2`, etc.
