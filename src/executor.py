"""工具执行器模块."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Type

from src.tools.base import Tool, ToolResult, ToolSchema

logger = logging.getLogger(__name__)


class ToolExecutor:
    """工具执行器."""
    
    def __init__(self):
        """初始化工具执行器."""
        self.tools: Dict[str, Tool] = {}
        self.tool_classes: Dict[str, Type[Tool]] = {}
        logger.info("ToolExecutor initialized")
    
    def register_tool(self, tool_class: Type[Tool]) -> None:
        """注册工具类."""
        tool_instance = tool_class()
        tool_name = tool_instance.schema.name
        
        if tool_name in self.tools:
            logger.warning(f"Tool {tool_name} already registered, overwriting")
        
        self.tools[tool_name] = tool_instance
        self.tool_classes[tool_name] = tool_class
        logger.info(f"Registered tool: {tool_name}")
    
    def register_tools(self, tool_classes: List[Type[Tool]]) -> None:
        """批量注册工具类."""
        for tool_class in tool_classes:
            self.register_tool(tool_class)
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """获取工具实例."""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """列出所有可用工具."""
        return list(self.tools.keys())
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的模式定义."""
        return [tool.get_schema_dict() for tool in self.tools.values()]
    
    def get_tool_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定工具的模式定义."""
        tool = self.get_tool(name)
        return tool.get_schema_dict() if tool else None
    
    async def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """执行工具."""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                success=False,
                result=None,
                error=f"Tool '{name}' not found"
            )
        
        # 验证参数
        if not tool.validate_parameters(**kwargs):
            return ToolResult(
                success=False,
                result=None,
                error=f"Invalid parameters for tool '{name}'"
            )
        
        try:
            logger.info(f"Executing tool: {name} with args: {kwargs}")
            result = await tool.execute(**kwargs)
            logger.info(f"Tool {name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {name} execution failed: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=str(e)
            )
    
    async def execute_tools(self, tool_calls: List[Dict[str, Any]]) -> List[ToolResult]:
        """批量执行工具."""
        results = []
        for tool_call in tool_calls:
            name = tool_call.get('name')
            arguments = tool_call.get('arguments', {})
            
            if not name:
                results.append(ToolResult(
                    success=False,
                    result=None,
                    error="Tool name is required"
                ))
                continue
            
            result = await self.execute_tool(name, **arguments)
            results.append(result)
        
        return results
    
    def get_dangerous_tools(self) -> List[str]:
        """获取危险工具列表."""
        return [
            name for name, tool in self.tools.items()
            if tool.schema.dangerous
        ]
    
    def get_tools_by_category(self, category: str) -> List[str]:
        """按类别获取工具列表."""
        return [
            name for name, tool in self.tools.items()
            if tool.schema.category == category
        ]
    
    def unregister_tool(self, name: str) -> bool:
        """注销工具."""
        if name in self.tools:
            del self.tools[name]
            del self.tool_classes[name]
            logger.info(f"Unregistered tool: {name}")
            return True
        return False
    
    def clear_tools(self) -> None:
        """清空所有工具."""
        self.tools.clear()
        self.tool_classes.clear()
        logger.info("Cleared all tools")


# 全局工具执行器实例
_executor_instance: Optional[ToolExecutor] = None


def get_executor() -> ToolExecutor:
    """获取全局工具执行器实例."""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = ToolExecutor()
    return _executor_instance


def reset_executor() -> None:
    """重置全局工具执行器实例."""
    global _executor_instance
    _executor_instance = None
