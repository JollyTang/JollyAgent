"""工具模块初始化."""

from src.tools.base import Tool
from src.tools.file import ReadFileTool, WriteFileTool, DeleteFileTool
from src.tools.shell import RunShellTool
from src.tools.mcp import MCPCallTool, MCPListToolsTool

# 所有可用的工具类
AVAILABLE_TOOLS = [
    RunShellTool,
    ReadFileTool,
    WriteFileTool,
    DeleteFileTool,
    MCPCallTool,
    MCPListToolsTool,
]

__all__ = [
    "Tool",
    "RunShellTool", 
    "ReadFileTool",
    "WriteFileTool",
    "DeleteFileTool",
    "MCPCallTool",
    "MCPListToolsTool",
    "AVAILABLE_TOOLS"
]
