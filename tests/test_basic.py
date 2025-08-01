"""Basic tests to verify the testing setup."""

import pytest


def test_imports():
    """Test that we can import our modules."""
    try:
        import src.agent
        import src.config
        import src.executor
        import src.memory.manager
        import src.sandbox.docker
        import src.tools.base
        import src.tools.shell
        import src.tools.file
        import src.tools.mcp
    except ImportError as e:
        pytest.fail(f"Failed to import module: {e}")


def test_basic_functionality():
    """Test basic functionality."""
    assert 1 + 1 == 2


def test_string_operations():
    """Test string operations."""
    assert "hello" + " " + "world" == "hello world"


if __name__ == "__main__":
    pytest.main([__file__])
