"""文件操作工具模块."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from src.tools.base import Tool, ToolParameter, ToolResult, ToolSchema

logger = logging.getLogger(__name__)


class ReadFileTool(Tool):
    """读取文件内容的工具."""
    
    def _get_schema(self) -> ToolSchema:
        """获取工具模式定义."""
        return ToolSchema(
            name="read_file",
            description="读取文件内容",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type="string",
                    description="文件路径",
                    required=True
                ),
                ToolParameter(
                    name="encoding",
                    type="string",
                    description="文件编码",
                    required=False,
                    default="utf-8"
                ),
                ToolParameter(
                    name="max_size",
                    type="integer",
                    description="最大读取大小（字节）",
                    required=False,
                    default=1024 * 1024  # 1MB
                )
            ],
            returns="文件内容",
            category="file",
            dangerous=False
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """读取文件内容."""
        file_path = kwargs.get("file_path")
        encoding = kwargs.get("encoding", "utf-8")
        max_size = kwargs.get("max_size", 1024 * 1024)
        
        if not file_path:
            return ToolResult(
                success=False,
                result=None,
                error="File path is required"
            )
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"File not found: {file_path}"
                )
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size > max_size:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"File too large: {file_size} bytes (max: {max_size})"
                )
            
            # 检查是否为文件
            if not os.path.isfile(file_path):
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Path is not a file: {file_path}"
                )
            
            logger.info(f"Reading file: {file_path}")
            
            # 异步读取文件
            def read_file_sync():
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            
            content = await asyncio.to_thread(read_file_sync)
            
            result = {
                "content": content,
                "file_path": file_path,
                "file_size": file_size,
                "encoding": encoding
            }
            
            logger.info(f"File read successfully: {file_path} ({file_size} bytes)")
            
            return ToolResult(
                success=True,
                result=result,
                error=None
            )
            
        except UnicodeDecodeError as e:
            logger.error(f"File encoding error: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=f"File encoding error: {e}"
            )
        except Exception as e:
            logger.error(f"File read failed: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=str(e)
            )


class WriteFileTool(Tool):
    """写入文件内容的工具."""
    
    def _get_schema(self) -> ToolSchema:
        """获取工具模式定义."""
        return ToolSchema(
            name="write_file",
            description="写入文件内容",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type="string",
                    description="文件路径",
                    required=True
                ),
                ToolParameter(
                    name="content",
                    type="string",
                    description="要写入的内容",
                    required=True
                ),
                ToolParameter(
                    name="encoding",
                    type="string",
                    description="文件编码",
                    required=False,
                    default="utf-8"
                ),
                ToolParameter(
                    name="mode",
                    type="string",
                    description="写入模式：w（覆盖）或 a（追加）",
                    required=False,
                    default="w",
                    enum=["w", "a"]
                )
            ],
            returns="写入结果",
            category="file",
            dangerous=True
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """写入文件内容."""
        file_path = kwargs.get("file_path")
        content = kwargs.get("content")
        encoding = kwargs.get("encoding", "utf-8")
        mode = kwargs.get("mode", "w")
        
        if not file_path:
            return ToolResult(
                success=False,
                result=None,
                error="File path is required"
            )
        
        if content is None:
            return ToolResult(
                success=False,
                result=None,
                error="Content is required"
            )
        
        try:
            # 确保目录存在
            file_dir = os.path.dirname(file_path)
            if file_dir and not os.path.exists(file_dir):
                os.makedirs(file_dir, exist_ok=True)
            
            logger.info(f"Writing file: {file_path} (mode: {mode})")
            
            # 异步写入文件
            def write_file_sync():
                with open(file_path, mode, encoding=encoding) as f:
                    f.write(content)
            
            await asyncio.to_thread(write_file_sync)
            
            # 获取文件信息
            file_size = os.path.getsize(file_path)
            
            result = {
                "file_path": file_path,
                "file_size": file_size,
                "encoding": encoding,
                "mode": mode,
                "content_length": len(content)
            }
            
            logger.info(f"File written successfully: {file_path} ({file_size} bytes)")
            
            return ToolResult(
                success=True,
                result=result,
                error=None
            )
            
        except Exception as e:
            logger.error(f"File write failed: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=str(e)
            )
