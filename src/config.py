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

    # FAISS向量数据库配置
    persist_directory: str = Field(
        default="./memory_db",
        description="Directory to persist vector database",
    )
    index_type: str = Field(
        default="IVF100,Flat",
        description="FAISS index type (IVF100,Flat, HNSW, etc.)",
    )
    embedding_dimension: int = Field(
        default=1024,  # BAAI/bge-large-zh-v1.5的维度是1024
        ge=1,
        description="Embedding dimension",
    )
    embedding_model: str = Field(
        default="BAAI/bge-large-zh-v1.5",  # 使用硅基流动的免费模型
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
    
    # 分层记忆管理配置
    enable_layered_memory: bool = Field(
        default=True,
        description="Enable layered memory management",
    )
    conversation_length_threshold: int = Field(
        default=10,
        ge=1,
        description="Threshold for switching between short and long conversation modes",
    )
    short_term_rounds: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of recent rounds to keep in short-term memory",
    )
    summary_model: str = Field(
        default="Qwen/QwQ-32B",
        description="Model for generating conversation summaries",
    )
    summary_max_tokens: int = Field(
        default=100,
        ge=10,
        le=500,
        description="Maximum tokens for conversation summary generation",
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
        description="Log level",
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


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    
    # 是否启用监控
    enable_monitoring: bool = Field(
        default=False,
        description="Enable monitoring and instrumentation",
    )
    
    # OpenTelemetry 配置
    enable_opentelemetry: bool = Field(
        default=True,
        description="Enable OpenTelemetry integration",
    )
    
    # 监控组件配置
    enable_agent_tracing: bool = Field(
        default=True,
        description="Enable Agent method tracing",
    )
    enable_tool_tracing: bool = Field(
        default=True,
        description="Enable tool execution tracing",
    )
    enable_memory_tracing: bool = Field(
        default=True,
        description="Enable memory operation tracing",
    )
    enable_llm_tracing: bool = Field(
        default=True,
        description="Enable LLM call tracing",
    )
    
    # 性能指标配置
    enable_performance_metrics: bool = Field(
        default=True,
        description="Enable performance metrics collection",
    )
    enable_error_tracking: bool = Field(
        default=True,
        description="Enable error tracking",
    )
    
    # 执行步骤追踪配置
    enable_step_tracking: bool = Field(
        default=True,
        description="Enable Think-Act-Observe-Response step tracking",
    )
    enable_metadata_collection: bool = Field(
        default=True,
        description="Enable metadata collection (timestamps, status, errors)",
    )
    
    # 数据存储配置
    enable_local_backup: bool = Field(
        default=True,
        description="Enable local file storage as backup",
    )
    backup_directory: str = Field(
        default="./monitoring_data",
        description="Directory for monitoring data backup",
    )
    
    # 服务配置
    service_name: str = Field(
        default="jollyagent",
        description="Service name for monitoring",
    )
    service_version: str = Field(
        default="1.0.0",
        description="Service version for monitoring",
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
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

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
