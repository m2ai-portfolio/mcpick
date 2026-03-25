"""Tests for project generation (stubs for future implementation)."""

import pytest
from pathlib import Path
import shutil
import tempfile

from mcpick.config import ServerConfig, ToolDefinition, ToolParameter, GenerationOptions
from mcpick.generator import generate_project


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
