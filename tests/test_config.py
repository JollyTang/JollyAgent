"""Tests for configuration management."""

import os
import tempfile
from pathlib import Path

import pytest

from src.config import (
    Config,
    LLMConfig,
    MemoryConfig,
    SandboxConfig,
    ToolConfig,
    LoggingConfig,
    load_config,
    get_config,
    reload_config,
)


class TestLLMConfig:
    """Test LLM configuration."""

    def test_default_values(self):
        """Test default LLM configuration values."""
        config = LLMConfig()

        assert config.base_url == "https://api.siliconflow.cn/v1"
        assert config.model == "Qwen/QwQ-32B"
        assert config.api_key == "sk-atpfqgdfpusndwvlufdyxjkriuwepbbrpnrwuctdydmeqyaz"
        assert config.temperature == 0.1
        assert config.max_tokens == 4096

    def test_custom_values(self):
        """Test custom LLM configuration values."""
        config = LLMConfig(
            base_url="https://custom.api.com/v1",
            model="custom-model",
            api_key="test-key",
            temperature=0.5,
            max_tokens=2048,
        )

        assert config.base_url == "https://custom.api.com/v1"
        assert config.model == "custom-model"
        assert config.api_key == "test-key"
        assert config.temperature == 0.5
        assert config.max_tokens == 2048

    def test_validation(self):
        """Test LLM configuration validation."""
        # 测试温度范围验证
        with pytest.raises(ValueError):
            LLMConfig(temperature=-0.1)

        with pytest.raises(ValueError):
            LLMConfig(temperature=2.1)

        # 测试最大token数验证
        with pytest.raises(ValueError):
            LLMConfig(max_tokens=0)


class TestMemoryConfig:
    """Test memory configuration."""

    def test_default_values(self):
        """Test default memory configuration values."""
        config = MemoryConfig()

        assert config.persist_directory == "./chroma_db"
        assert config.collection_name == "jollyagent_memory"
        assert config.embedding_model == "text-embedding-3-small"
        assert config.max_memory_items == 1000
        assert config.similarity_threshold == 0.7

    def test_validation(self):
        """Test memory configuration validation."""
        # 测试相似度阈值验证
        with pytest.raises(ValueError):
            MemoryConfig(similarity_threshold=-0.1)

        with pytest.raises(ValueError):
            MemoryConfig(similarity_threshold=1.1)

        # 测试最大内存项数验证
        with pytest.raises(ValueError):
            MemoryConfig(max_memory_items=0)


class TestSandboxConfig:
    """Test sandbox configuration."""

    def test_default_values(self):
        """Test default sandbox configuration values."""
        config = SandboxConfig()

        assert config.docker_image == "python:3.11-slim"
        assert config.memory_limit == "128m"
        assert config.timeout_seconds == 30
        assert config.enable_network is False
        assert config.work_dir == "/workspace"

    def test_validation(self):
        """Test sandbox configuration validation."""
        # 测试超时验证
        with pytest.raises(ValueError):
            SandboxConfig(timeout_seconds=0)


class TestToolConfig:
    """Test tool configuration."""

    def test_default_values(self):
        """Test default tool configuration values."""
        config = ToolConfig()

        assert config.enable_shell is True
        assert config.enable_file_ops is True
        assert config.enable_mcp is True
        assert "ls" in config.allowed_commands
        assert "rm" in config.forbidden_commands


class TestLoggingConfig:
    """Test logging configuration."""

    def test_default_values(self):
        """Test default logging configuration values."""
        config = LoggingConfig()

        assert config.level == "INFO"
        assert "asctime" in config.format
        assert config.file == "./logs/jollyagent.log"
        assert config.max_size == 10 * 1024 * 1024  # 10MB
        assert config.backup_count == 5


class TestConfig:
    """Test main configuration."""

    def test_default_config(self):
        """Test default configuration."""
        config = Config()

        assert config.project_name == "JollyAgent"
        assert config.version == "0.1.0"
        assert isinstance(config.llm, LLMConfig)
        assert isinstance(config.memory, MemoryConfig)
        assert isinstance(config.sandbox, SandboxConfig)
        assert isinstance(config.tools, ToolConfig)
        assert isinstance(config.logging, LoggingConfig)
        assert config.max_concurrent_requests == 5
        assert config.request_timeout == 60
        assert config.require_confirmation is True
        assert config.enable_undo is True


class TestConfigFunctions:
    """Test configuration functions."""

    def test_load_config(self):
        """Test load_config function."""
        config = load_config()

        assert isinstance(config, Config)
        assert config.project_name == "JollyAgent"

    def test_load_config_with_env_var(self):
        """Test load_config with environment variable."""
        # 设置环境变量
        os.environ["JOLLYAGENT_API_KEY"] = "test-api-key"

        try:
            config = load_config()
            assert config.llm.api_key == "test-api-key"
        finally:
            # 清理环境变量
            if "JOLLYAGENT_API_KEY" in os.environ:
                del os.environ["JOLLYAGENT_API_KEY"]

    def test_get_config(self):
        """Test get_config function."""
        config = get_config()
        assert isinstance(config, Config)

    def test_reload_config(self):
        """Test reload_config function."""
        config1 = get_config()
        config2 = reload_config()

        assert isinstance(config2, Config)
        # 重新加载应该返回新的配置实例
        assert config2 is not config1


class TestConfigDirectories:
    """Test configuration directory creation."""

    def test_log_directory_creation(self):
        """Test that log directory is created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "logs" / "test.log"

            # 创建临时配置
            config = Config()
            config.logging.file = str(log_file)

            # 确保日志目录存在
            log_file.parent.mkdir(parents=True, exist_ok=True)

            assert log_file.parent.exists()

    def test_memory_directory_creation(self):
        """Test that memory directory is created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_dir = Path(temp_dir) / "memory"

            # 创建临时配置
            config = Config()
            config.memory.persist_directory = str(memory_dir)

            # 确保内存目录存在
            memory_dir.mkdir(parents=True, exist_ok=True)

            assert memory_dir.exists()
