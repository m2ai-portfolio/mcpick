"""Integration tests for end-to-end project generation and setup."""

import pytest
import subprocess
import tempfile
import shutil
from pathlib import Path

from mcpick.config import parse_yaml, GenerationOptions
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
def weather_api_yaml(tmp_path):
    """Path to weather_api.yaml example fixture."""
    examples_dir = Path(__file__).parent.parent / "examples"
    weather_yaml = examples_dir / "weather_api.yaml"
    if weather_yaml.exists():
        return weather_yaml
    # Fallback: create a test fixture
    test_yaml = tmp_path / "test_weather.yaml"
    test_yaml.write_text("""server_name: "Weather API MCP Server"
description: "MCP server for fetching weather information"
author: "Test Author"
author_email: "test@example.com"
version: "0.1.0"

tools:
  - name: "get_current_weather"
    description: "Get current weather for a location"
    parameters:
      - name: "location"
        type: "string"
        description: "City name"
        required: true
      - name: "units"
        type: "string"
        description: "Temperature units"
        required: false
        default: "metric"
    return_type: "object"
    return_description: "Weather data"

dependencies:
  requests: ">=2.31.0"
  python-dotenv: ">=1.0.0"
""")
    return test_yaml


class TestEndToEndGeneration:
    """Test complete end-to-end project generation workflow."""

    def test_generate_from_yaml_all_files_present(self, weather_api_yaml, temp_output_dir):
        """Test generating a project from YAML creates all required files."""
        config = parse_yaml(weather_api_yaml)
        output_dir = temp_output_dir / "weather_test"

        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(config, options)

        # Verify all expected files exist
        assert (output_dir / "pyproject.toml").exists(), "pyproject.toml missing"
        assert (output_dir / "README.md").exists(), "README.md missing"
        assert (output_dir / "init.sh").exists(), "init.sh missing"
        assert (output_dir / ".gitignore").exists(), ".gitignore missing"
        assert (output_dir / "src" / "server.py").exists(), "server.py missing"
        assert (output_dir / "tests" / "test_tools.py").exists(), "test_tools.py missing"
        assert (output_dir / "tests" / "conftest.py").exists(), "conftest.py missing"
        assert (output_dir / "tests" / "__init__.py").exists(), "tests/__init__.py missing"

    def test_pyproject_has_mcp_and_user_dependencies(self, weather_api_yaml, temp_output_dir):
        """Test that pyproject.toml includes MCP SDK and user-specified dependencies."""
        config = parse_yaml(weather_api_yaml)
        output_dir = temp_output_dir / "weather_test"

        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(config, options)

        pyproject_content = (output_dir / "pyproject.toml").read_text()

        # Verify MCP SDK dependency
        assert "mcp>=0.9.0" in pyproject_content, "MCP SDK dependency missing"

        # Verify user-specified dependencies
        assert "requests>=2.31.0" in pyproject_content, "requests dependency missing"
        assert "python-dotenv>=1.0.0" in pyproject_content, "python-dotenv dependency missing"

        # Verify dev dependencies
        assert "pytest>=7.4.0" in pyproject_content, "pytest dev dependency missing"
        assert "pytest-asyncio>=0.21.0" in pyproject_content, "pytest-asyncio dev dependency missing"

        # Verify project metadata
        assert 'name = "weather_api_mcp_server"' in pyproject_content or \
               'name = "test_weather"' in pyproject_content, "package name missing"
        assert 'version = "0.1.0"' in pyproject_content, "version missing"
        assert 'requires-python = ">=3.11"' in pyproject_content, "Python version requirement missing"

    def test_readme_mentions_all_tools(self, weather_api_yaml, temp_output_dir):
        """Test that README.md documents all tools defined in the config."""
        config = parse_yaml(weather_api_yaml)
        output_dir = temp_output_dir / "weather_test"

        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(config, options)

        readme_content = (output_dir / "README.md").read_text()

        # Verify all tools are documented
        for tool in config.tools:
            assert tool.name in readme_content, f"Tool {tool.name} not documented in README"
            assert tool.description in readme_content, f"Tool {tool.name} description missing"

            # Verify parameters are documented
            for param in tool.parameters:
                assert param.name in readme_content, f"Parameter {param.name} not documented"

        # Verify installation instructions present
        assert "init.sh" in readme_content, "init.sh not mentioned in README"
        assert "Installation" in readme_content, "Installation section missing"
        assert "Usage" in readme_content, "Usage section missing"
        assert "Testing" in readme_content or "pytest" in readme_content, "Testing section missing"

    def test_init_script_is_executable(self, weather_api_yaml, temp_output_dir):
        """Test that init.sh is created with executable permissions."""
        config = parse_yaml(weather_api_yaml)
        output_dir = temp_output_dir / "weather_test"

        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(config, options)

        init_script = output_dir / "init.sh"
        assert init_script.exists(), "init.sh not created"

        # Check executable permission
        import stat
        st = init_script.stat()
        assert st.st_mode & stat.S_IXUSR, "init.sh is not executable"

    def test_gitignore_covers_python_patterns(self, weather_api_yaml, temp_output_dir):
        """Test that .gitignore includes comprehensive Python patterns."""
        config = parse_yaml(weather_api_yaml)
        output_dir = temp_output_dir / "weather_test"

        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(config, options)

        gitignore_content = (output_dir / ".gitignore").read_text()

        # Essential Python patterns
        essential_patterns = [
            "__pycache__",
            "*.py[cod]",
            "venv/",
            ".venv",
            "*.egg-info",
            ".pytest_cache",
            ".coverage",
            "dist/",
            "build/",
        ]

        for pattern in essential_patterns:
            assert pattern in gitignore_content, f"Pattern {pattern} missing from .gitignore"

    def test_conftest_includes_fixtures(self, weather_api_yaml, temp_output_dir):
        """Test that conftest.py includes useful test fixtures."""
        config = parse_yaml(weather_api_yaml)
        output_dir = temp_output_dir / "weather_test"

        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(config, options)

        conftest_content = (output_dir / "tests" / "conftest.py").read_text()

        # Verify fixtures are defined
        assert "@pytest.fixture" in conftest_content, "No pytest fixtures defined"
        assert "sample_arguments" in conftest_content or "valid_tool_names" in conftest_content, \
               "Expected fixtures missing"

    def test_init_script_syntax_is_valid(self, weather_api_yaml, temp_output_dir):
        """Test that generated init.sh has valid bash syntax."""
        config = parse_yaml(weather_api_yaml)
        output_dir = temp_output_dir / "weather_test"

        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(config, options)

        init_script = output_dir / "init.sh"

        # Use bash -n to check syntax without executing
        result = subprocess.run(
            ["bash", "-n", str(init_script)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"init.sh has syntax errors: {result.stderr}"

    def test_generated_tests_are_valid_python(self, weather_api_yaml, temp_output_dir):
        """Test that generated test files are valid Python syntax."""
        config = parse_yaml(weather_api_yaml)
        output_dir = temp_output_dir / "weather_test"

        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(config, options)

        # Check test_tools.py syntax
        test_file = output_dir / "tests" / "test_tools.py"
        result = subprocess.run(
            ["python3", "-m", "py_compile", str(test_file)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"test_tools.py has syntax errors: {result.stderr}"

        # Check conftest.py syntax
        conftest_file = output_dir / "tests" / "conftest.py"
        result = subprocess.run(
            ["python3", "-m", "py_compile", str(conftest_file)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"conftest.py has syntax errors: {result.stderr}"

    def test_generated_server_is_valid_python(self, weather_api_yaml, temp_output_dir):
        """Test that generated server.py is valid Python syntax."""
        config = parse_yaml(weather_api_yaml)
        output_dir = temp_output_dir / "weather_test"

        options = GenerationOptions(
            output_dir=output_dir,
            overwrite=False,
            create_venv=False,
            install_deps=False
        )

        generate_project(config, options)

        server_file = output_dir / "src" / "server.py"
        result = subprocess.run(
            ["python3", "-m", "py_compile", str(server_file)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"server.py has syntax errors: {result.stderr}"
