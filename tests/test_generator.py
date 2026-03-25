"""Tests for project generation."""

import pytest
import re
from pathlib import Path
import shutil
import tempfile

from mcpick.config import ServerConfig, ToolDefinition, ToolParameter, GenerationOptions
from mcpick.generator import generate_project, sanitize_package_name, validate_output_path


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def simple_config():
    """Create a simple server configuration for testing."""
    return ServerConfig(
        server_name="Test Server",
        description="A test MCP server",
        author="Test Author",
        tools=[
            ToolDefinition(
                name="test_tool",
                description="A test tool",
                parameters=[
                    ToolParameter(
                        name="param1",
                        type="string",
                        description="First parameter"
                    )
                ]
            )
        ]
    )


class TestProjectGeneration:
    """Test project generation functionality."""

    def test_generate_basic_project(self, simple_config, temp_output_dir):
        """Test basic project generation creates expected files."""
        output_dir = temp_output_dir / "test_project"
        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(simple_config, options)

        # Check that expected files exist
        assert output_dir.exists()
        assert (output_dir / "src" / "server.py").exists()
        assert (output_dir / "tests" / "test_tools.py").exists()
        assert (output_dir / "pyproject.toml").exists()
        assert (output_dir / "README.md").exists()
        assert (output_dir / "init.sh").exists()
        assert (output_dir / ".gitignore").exists()

    def test_generate_project_overwrite(self, simple_config, temp_output_dir):
        """Test that overwrite flag works correctly."""
        output_dir = temp_output_dir / "test_project"
        output_dir.mkdir()
        (output_dir / "existing_file.txt").write_text("should be removed")

        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=True,
            create_venv=False,
            install_deps=False
        )

        generate_project(simple_config, options)

        # Old file should be gone
        assert not (output_dir / "existing_file.txt").exists()
        # New files should exist
        assert (output_dir / "src" / "server.py").exists()

    def test_generate_project_no_overwrite_fails(self, simple_config, temp_output_dir):
        """Test that generation fails if directory exists and overwrite=False."""
        output_dir = temp_output_dir / "test_project"
        output_dir.mkdir()

        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        with pytest.raises(FileExistsError):
            generate_project(simple_config, options)

    def test_generated_server_has_correct_tools(self, simple_config, temp_output_dir):
        """Test that generated server.py contains the defined tools."""
        output_dir = temp_output_dir / "test_project"
        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(simple_config, options)

        server_py = (output_dir / "src" / "server.py").read_text()

        # Check that tool is defined
        assert "test_tool" in server_py
        assert "A test tool" in server_py
        assert "param1" in server_py

    def test_generated_pyproject_has_dependencies(self, temp_output_dir):
        """Test that generated pyproject.toml includes dependencies."""
        config = ServerConfig(
            server_name="Test Server",
            description="Test",
            tools=[
                ToolDefinition(name="tool", description="Tool", parameters=[])
            ],
            dependencies={"requests": ">=2.31.0", "numpy": ">=1.24.0"}
        )

        output_dir = temp_output_dir / "test_project"
        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(config, options)

        pyproject = (output_dir / "pyproject.toml").read_text()

        # Check dependencies are included
        assert "requests>=2.31.0" in pyproject
        assert "numpy>=1.24.0" in pyproject
        assert "mcp>=0.9.0" in pyproject

    def test_generated_server_has_async_handlers(self, simple_config, temp_output_dir):
        """Test that generated server.py has async handler functions."""
        output_dir = temp_output_dir / "test_project"
        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(simple_config, options)

        server_py = (output_dir / "src" / "server.py").read_text()

        # Check for async function definition
        assert "async def test_tool(" in server_py
        assert "async def list_tools(" in server_py
        assert "async def call_tool(" in server_py

    def test_generated_server_has_proper_imports(self, simple_config, temp_output_dir):
        """Test that generated server.py has correct MCP imports."""
        output_dir = temp_output_dir / "test_project"
        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(simple_config, options)

        server_py = (output_dir / "src" / "server.py").read_text()

        # Check for required imports
        assert "from mcp.server import Server" in server_py
        assert "from mcp.server.stdio import stdio_server" in server_py
        assert "from mcp.types import Tool, TextContent" in server_py
        assert "import asyncio" in server_py
        assert "import logging" in server_py

    def test_generated_server_has_error_handling(self, simple_config, temp_output_dir):
        """Test that generated server.py includes error handling."""
        output_dir = temp_output_dir / "test_project"
        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(simple_config, options)

        server_py = (output_dir / "src" / "server.py").read_text()

        # Check for try/except blocks
        assert "try:" in server_py
        assert "except Exception as e:" in server_py
        assert "logger.error" in server_py

    def test_generated_tests_have_async_markers(self, simple_config, temp_output_dir):
        """Test that generated tests use pytest.mark.asyncio."""
        output_dir = temp_output_dir / "test_project"
        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(simple_config, options)

        test_file = (output_dir / "tests" / "test_tools.py").read_text()

        # Check for asyncio markers
        assert "@pytest.mark.asyncio" in test_file
        assert "async def test_" in test_file

    def test_generated_tests_import_handlers(self, simple_config, temp_output_dir):
        """Test that generated tests import tool handlers."""
        output_dir = temp_output_dir / "test_project"
        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(simple_config, options)

        test_file = (output_dir / "tests" / "test_tools.py").read_text()

        # Check for imports
        assert "from src.server import" in test_file
        assert "test_tool" in test_file
        assert "call_tool" in test_file
        assert "list_tools" in test_file

    def test_multiple_tools_generation(self, temp_output_dir):
        """Test project generation with multiple tools."""
        config = ServerConfig(
            server_name="Multi Tool Server",
            description="Server with multiple tools",
            tools=[
                ToolDefinition(
                    name="tool_one",
                    description="First tool",
                    parameters=[
                        ToolParameter(name="arg1", type="string", description="Arg 1")
                    ]
                ),
                ToolDefinition(
                    name="tool_two",
                    description="Second tool",
                    parameters=[
                        ToolParameter(name="arg2", type="integer", description="Arg 2")
                    ]
                ),
                ToolDefinition(
                    name="tool_three",
                    description="Third tool",
                    parameters=[]
                ),
            ]
        )

        output_dir = temp_output_dir / "multi_tool"
        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(config, options)

        server_py = (output_dir / "src" / "server.py").read_text()

        # Check all three tools are present
        assert "async def tool_one(" in server_py
        assert "async def tool_two(" in server_py
        assert "async def tool_three(" in server_py

        # Check tool registration in call_tool
        assert 'if name == "tool_one":' in server_py
        assert 'elif name == "tool_two":' in server_py
        assert 'elif name == "tool_three":' in server_py

    def test_init_script_is_executable(self, simple_config, temp_output_dir):
        """Test that init.sh is created with executable permissions."""
        output_dir = temp_output_dir / "test_project"
        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(simple_config, options)

        init_script = output_dir / "init.sh"
        assert init_script.exists()

        # Check executable bit
        import stat
        st = init_script.stat()
        assert st.st_mode & stat.S_IXUSR  # User executable


class TestPackageNameSanitization:
    """Test package name sanitization."""

    def test_sanitize_simple_name(self):
        """Test sanitizing simple server name."""
        assert sanitize_package_name("MyServer") == "myserver"

    def test_sanitize_with_spaces(self):
        """Test sanitizing name with spaces."""
        assert sanitize_package_name("My Server") == "my_server"

    def test_sanitize_with_hyphens(self):
        """Test sanitizing name with hyphens."""
        assert sanitize_package_name("my-server") == "my_server"

    def test_sanitize_mixed_case(self):
        """Test sanitizing mixed case name."""
        assert sanitize_package_name("Calculator MCP Server") == "calculator_mcp_server"

    def test_sanitize_starting_with_digit(self):
        """Test sanitizing name starting with digit."""
        result = sanitize_package_name("123server")
        assert result == "pkg_123server"
        assert result.isidentifier()

    def test_sanitize_with_special_chars(self):
        """Test sanitizing name with special characters."""
        result = sanitize_package_name("My@Server#2024")
        assert result.isidentifier()
        assert "@" not in result
        assert "#" not in result


class TestPathValidation:
    """Test output path validation."""

    def test_validate_normal_path(self, temp_output_dir):
        """Test validating a normal output path."""
        test_path = temp_output_dir / "output"
        result = validate_output_path(test_path)
        assert result.is_absolute()

    def test_validate_rejects_system_dirs(self):
        """Test that system directories are rejected."""
        with pytest.raises(ValueError, match="sensitive directory"):
            validate_output_path(Path("/bin/myproject"))

        with pytest.raises(ValueError, match="sensitive directory"):
            validate_output_path(Path("/etc/myproject"))

        with pytest.raises(ValueError, match="sensitive directory"):
            validate_output_path(Path("/usr/myproject"))
