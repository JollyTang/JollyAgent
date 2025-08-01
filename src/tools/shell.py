"""Shell工具模块."""

import asyncio
import logging
import shlex
import subprocess
from typing import Any, Dict, Optional

from src.tools.base import Tool, ToolParameter, ToolResult, ToolSchema

logger = logging.getLogger(__name__)


class RunShellTool(Tool):
    """执行Shell命令的工具."""
    
    def _get_schema(self) -> ToolSchema:
        """获取工具模式定义."""
        return ToolSchema(
            name="run_shell",
            description="执行系统Shell命令",
            parameters=[
                ToolParameter(
                    name="command",
                    type="string",
                    description="要执行的Shell命令",
                    required=True
                ),
                ToolParameter(
                    name="timeout",
                    type="integer",
                    description="命令执行超时时间（秒）",
                    required=False,
                    default=30
                ),
                ToolParameter(
                    name="cwd",
                    type="string",
                    description="工作目录",
                    required=False,
                    default=None
                )
            ],
            returns="命令执行结果，包括标准输出、标准错误和退出码",
            category="system",
            dangerous=True
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行Shell命令."""
        command = kwargs.get("command")
        timeout = kwargs.get("timeout", 30)
        cwd = kwargs.get("cwd")
        
        if not command:
            return ToolResult(
                success=False,
                result=None,
                error="Command is required"
            )
        
        try:
            logger.info(f"Executing shell command: {command}")
            
            # 解析命令
            if isinstance(command, str):
                cmd_parts = shlex.split(command)
            else:
                cmd_parts = command
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Command execution timed out after {timeout} seconds"
                )
            
            # 解码输出
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            exit_code = process.returncode
            
            result = {
                "stdout": stdout_text,
                "stderr": stderr_text,
                "exit_code": exit_code,
                "command": command
            }
            
            success = exit_code == 0
            error = None if success else f"Command failed with exit code {exit_code}"
            
            if stderr_text and not success:
                error = f"{error}: {stderr_text}"
            
            logger.info(f"Shell command completed with exit code: {exit_code}")
            
            return ToolResult(
                success=success,
                result=result,
                error=error
            )
            
        except Exception as e:
            logger.error(f"Shell command execution failed: {e}")
            return ToolResult(
                success=False,
                result={
                    "stdout": "",
                    "stderr": str(e),
                    "exit_code": -1,
                    "command": command
                },
                error=str(e)
            )
