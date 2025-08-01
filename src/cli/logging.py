"""CLI日志记录功能模块."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

console = Console()


class CLILogger:
    """CLI日志管理器."""
    
    def __init__(self, log_file: Optional[str] = None, level: str = "INFO"):
        """初始化CLI日志管理器.
        
        Args:
            log_file: 日志文件路径
            level: 日志级别
        """
        self.log_file = log_file
        self.level = getattr(logging, level.upper())
        self.logger = None
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志记录器."""
        # 创建日志记录器
        self.logger = logging.getLogger("jollyagent_cli")
        self.logger.setLevel(self.level)
        
        # 清除现有的处理器
        self.logger.handlers.clear()
        
        # 添加Rich控制台处理器
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True
        )
        console_handler.setLevel(self.level)
        self.logger.addHandler(console_handler)
        
        # 添加文件处理器（如果指定了日志文件）
        if self.log_file:
            self._setup_file_handler()
        
        # 设置格式
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        for handler in self.logger.handlers:
            handler.setFormatter(formatter)
    
    def _setup_file_handler(self):
        """设置文件处理器."""
        try:
            # 确保日志目录存在
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            # 创建文件处理器
            file_handler = logging.FileHandler(
                self.log_file, 
                encoding='utf-8'
            )
            file_handler.setLevel(self.level)
            self.logger.addHandler(file_handler)
            
        except Exception as e:
            console.print(f"[red]设置文件日志失败: {e}[/red]")
    
    def log_session_start(self, session_info: Dict[str, Any]):
        """记录会话开始."""
        if not self.logger:
            return
        
        self.logger.info("=" * 60)
        self.logger.info("JollyAgent CLI 会话开始")
        self.logger.info(f"会话ID: {self.session_id}")
        self.logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        for key, value in session_info.items():
            self.logger.info(f"{key}: {value}")
        
        self.logger.info("=" * 60)
    
    def log_session_end(self, session_summary: Dict[str, Any]):
        """记录会话结束."""
        if not self.logger:
            return
        
        self.logger.info("=" * 60)
        self.logger.info("JollyAgent CLI 会话结束")
        self.logger.info(f"会话ID: {self.session_id}")
        self.logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        for key, value in session_summary.items():
            self.logger.info(f"{key}: {value}")
        
        self.logger.info("=" * 60)
    
    def log_user_input(self, user_input: str):
        """记录用户输入."""
        if not self.logger:
            return
        
        self.logger.info(f"用户输入: {user_input}")
    
    def log_agent_response(self, response: str):
        """记录Agent响应."""
        if not self.logger:
            return
        
        self.logger.info(f"Agent响应: {response[:200]}...")
    
    def log_tool_call(self, tool_name: str, arguments: Dict[str, Any], result: Dict[str, Any]):
        """记录工具调用."""
        if not self.logger:
            return
        
        self.logger.info(f"工具调用: {tool_name}")
        self.logger.info(f"参数: {arguments}")
        self.logger.info(f"结果: {result}")
    
    def log_error(self, error: str, exception: Optional[Exception] = None):
        """记录错误."""
        if not self.logger:
            return
        
        self.logger.error(f"错误: {error}")
        if exception:
            self.logger.exception(exception)
    
    def log_confirmation(self, tool_name: str, confirmed: bool, reason: str = ""):
        """记录用户确认."""
        if not self.logger:
            return
        
        status = "确认" if confirmed else "拒绝"
        self.logger.info(f"用户{status}工具调用: {tool_name}")
        if reason:
            self.logger.info(f"原因: {reason}")
    
    def log_undo_action(self, action_type: str, description: str, success: bool):
        """记录撤销操作."""
        if not self.logger:
            return
        
        status = "成功" if success else "失败"
        self.logger.info(f"撤销操作{status}: {action_type} - {description}")
    
    def get_session_log(self) -> str:
        """获取会话日志内容."""
        if not self.log_file or not os.path.exists(self.log_file):
            return "无日志文件"
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"读取日志文件失败: {e}"
    
    def show_session_summary(self):
        """显示会话摘要."""
        if not self.logger:
            return
        
        # 这里可以添加更复杂的会话摘要逻辑
        console.print("[green]会话日志已记录[/green]")


# 全局CLI日志管理器实例
_cli_logger: Optional[CLILogger] = None


def get_cli_logger() -> CLILogger:
    """获取全局CLI日志管理器实例."""
    global _cli_logger
    if _cli_logger is None:
        # 默认日志文件路径
        log_file = "logs/jollyagent_cli.log"
        _cli_logger = CLILogger(log_file=log_file, level="WARNING")  # 改为WARNING级别
    return _cli_logger


def setup_cli_logging(log_file: Optional[str] = None, level: str = "INFO"):
    """设置CLI日志记录."""
    global _cli_logger
    _cli_logger = CLILogger(log_file=log_file, level=level)
    return _cli_logger


def reset_cli_logger():
    """重置全局CLI日志管理器实例."""
    global _cli_logger
    _cli_logger = None 