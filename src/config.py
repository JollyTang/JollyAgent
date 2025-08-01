"""Configuration management for JollyAgent."""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM configuration."""

    # 硅基流动API配置
    base_url: str = Field(
        default="https://api.siliconflow.cn/v1",
        description="API base URL",
    )
    model: str = Field(
        default="Qwen/QwQ-32B",
        description="Model name",
    )
    api_key: Optional[str] = Field(
        default="sk-atpfqgdfpusndwvlufdyxjkriuwepbbrpnrwuctdydmeqyaz",
        description="API key (from environment variable)",
    )
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Temperature for generation",
    )
    max_tokens: int = Field(
        default=4096,
        ge=1,
        description="Maximum tokens to generate",
    )


class MemoryConfig(BaseModel):
    """Memory configuration."""

    # Chroma向量数据库配置
    persist_directory: str = Field(
        default="./chroma_db",
        description="Directory to persist vector database",
    )
    collection_name: str = Field(
        default="jollyagent_memory",
        description="Collection name for memory storage",
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model name",
    )
    max_memory_items: int = Field(
        default=1000,
        ge=1,
        description="Maximum number of memory items to keep",
    )
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Similarity threshold for memory retrieval",
    )


class SandboxConfig(BaseModel):
    """Sandbox configuration."""

    # Docker沙箱配置
    docker_image: str = Field(
        default="python:3.11-slim",
        description="Docker image for sandbox",
    )
    memory_limit: str = Field(
        default="128m",
        description="Memory limit for containers",
    )
    timeout_seconds: int = Field(
        default=30,
        ge=1,
        description="Timeout for sandbox operations",
    )
    enable_network: bool = Field(
        default=False,
        description="Enable network access in sandbox",
    )
    work_dir: str = Field(
        default="/workspace",
        description="Working directory in sandbox",
    )


class ToolConfig(BaseModel):
    """Tool configuration."""

    # 工具配置
    enable_shell: bool = Field(
        default=True,
        description="Enable shell command execution",
    )
    enable_file_ops: bool = Field(
        default=True,
        description="Enable file operations",
    )
    enable_mcp: bool = Field(
        default=True,
        description="Enable MCP protocol support",
    )
    allowed_commands: list[str] = Field(
        default=["ls", "cat", "head", "tail", "grep", "find"],
        description="Allowed shell commands",
    )
    forbidden_commands: list[str] = Field(
        default=["rm", "rmdir", "del", "format"],
        description="Forbidden shell commands",
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(
        default="INFO",
        description="Logging level",
    )
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format",
    )
    file: Optional[str] = Field(
        default="./logs/jollyagent.log",
        description="Log file path",
    )
    max_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum log file size",
    )
    backup_count: int = Field(
        default=5,
        description="Number of backup log files",
    )


class Config(BaseModel):
    """Main configuration class."""

    # 项目基本信息
    project_name: str = Field(
        default="JollyAgent",
        description="Project name",
    )
    version: str = Field(
        default="0.1.0",
        description="Project version",
    )

    # 各模块配置
    llm: LLMConfig = Field(default_factory=LLMConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    tools: ToolConfig = Field(default_factory=ToolConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # 性能配置
    max_concurrent_requests: int = Field(
        default=5,
        ge=1,
        description="Maximum concurrent requests",
    )
    request_timeout: int = Field(
        default=60,
        ge=1,
        description="Request timeout in seconds",
    )

    # 安全配置
    require_confirmation: bool = Field(
        default=True,
        description="Require user confirmation for dangerous operations",
    )
    enable_undo: bool = Field(
        default=True,
        description="Enable undo functionality",
    )


def load_config() -> Config:
    """Load configuration from environment variables and defaults."""

    # 从环境变量加载API密钥
    api_key = os.getenv("JOLLYAGENT_API_KEY")

    # 创建配置实例
    config = Config()

    # 更新API密钥
    if api_key:
        config.llm.api_key = api_key

    # 确保日志目录存在
    if config.logging.file:
        log_path = Path(config.logging.file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # 确保向量数据库目录存在
    persist_dir = Path(config.memory.persist_directory)
    persist_dir.mkdir(parents=True, exist_ok=True)

    return config


# 全局配置实例
config = load_config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config


def reload_config() -> Config:
    """Reload configuration from environment variables."""
    global config
    config = load_config()
    return config
