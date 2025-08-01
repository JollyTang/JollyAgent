"""MCP协议客户端工具模块."""

import asyncio
import json
import logging
import websockets
from typing import Any, Dict, List, Optional

from src.tools.base import Tool, ToolParameter, ToolResult, ToolSchema

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP协议客户端."""
    
    def __init__(self, server_url: str = "ws://localhost:3000"):
        """初始化MCP客户端."""
        self.server_url = server_url
        self.websocket = None
        self.request_id = 0
    
    async def connect(self):
        """连接到MCP服务器."""
        try:
            self.websocket = await websockets.connect(self.server_url)
            logger.info(f"Connected to MCP server: {self.server_url}")
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise
    
    async def disconnect(self):
        """断开与MCP服务器的连接."""
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from MCP server")
    
    def _get_next_request_id(self) -> int:
        """获取下一个请求ID."""
        self.request_id += 1
        return self.request_id
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用MCP工具."""
        if not self.websocket:
            await self.connect()
        
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_request_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        try:
            await self.websocket.send(json.dumps(request))
            response = await self.websocket.recv()
            response_data = json.loads(response)
            
            if "error" in response_data:
                raise Exception(f"MCP server error: {response_data['error']}")
            
            return response_data.get("result", {})
            
        except Exception as e:
            logger.error(f"MCP tool call failed: {e}")
            raise
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表."""
        if not self.websocket:
            await self.connect()
        
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_request_id(),
            "method": "tools/list",
            "params": {}
        }
        
        try:
            await self.websocket.send(json.dumps(request))
            response = await self.websocket.recv()
            response_data = json.loads(response)
            
            if "error" in response_data:
                raise Exception(f"MCP server error: {response_data['error']}")
            
            return response_data.get("result", {}).get("tools", [])
            
        except Exception as e:
            logger.error(f"Failed to list MCP tools: {e}")
            raise


class MCPCallTool(Tool):
    """MCP协议调用工具."""
    
    def __init__(self, server_url: str = "ws://localhost:3000"):
        """初始化MCP调用工具."""
        self.server_url = server_url
        self.client = MCPClient(server_url)
        super().__init__()
    
    def _get_schema(self) -> ToolSchema:
        """获取工具模式定义."""
        return ToolSchema(
            name="mcp_call",
            description="通过MCP协议调用外部工具",
            parameters=[
                ToolParameter(
                    name="tool_name",
                    type="string",
                    description="要调用的MCP工具名称",
                    required=True
                ),
                ToolParameter(
                    name="arguments",
                    type="object",
                    description="传递给工具的参数（JSON对象）",
                    required=True
                ),
                ToolParameter(
                    name="server_url",
                    type="string",
                    description="MCP服务器URL",
                    required=False,
                    default="ws://localhost:3000"
                )
            ],
            returns="MCP工具执行结果",
            category="mcp",
            dangerous=False
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行MCP工具调用."""
        tool_name = kwargs.get("tool_name")
        arguments = kwargs.get("arguments", {})
        server_url = kwargs.get("server_url", self.server_url)
        
        if not tool_name:
            return ToolResult(
                success=False,
                result=None,
                error="Tool name is required"
            )
        
        if not isinstance(arguments, dict):
            return ToolResult(
                success=False,
                result=None,
                error="Arguments must be a dictionary"
            )
        
        try:
            logger.info(f"Calling MCP tool: {tool_name}")
            
            # 创建新的客户端实例（如果URL不同）
            if server_url != self.server_url:
                client = MCPClient(server_url)
            else:
                client = self.client
            
            # 调用MCP工具
            result = await client.call_tool(tool_name, arguments)
            
            logger.info(f"MCP tool {tool_name} executed successfully")
            
            return ToolResult(
                success=True,
                result=result,
                error=None
            )
            
        except Exception as e:
            logger.error(f"MCP tool call failed: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=str(e)
            )


class MCPListToolsTool(Tool):
    """MCP工具列表查询工具."""
    
    def __init__(self, server_url: str = "ws://localhost:3000"):
        """初始化MCP工具列表查询工具."""
        self.server_url = server_url
        self.client = MCPClient(server_url)
        super().__init__()
    
    def _get_schema(self) -> ToolSchema:
        """获取工具模式定义."""
        return ToolSchema(
            name="mcp_list_tools",
            description="获取MCP服务器上可用的工具列表",
            parameters=[
                ToolParameter(
                    name="server_url",
                    type="string",
                    description="MCP服务器URL",
                    required=False,
                    default="ws://localhost:3000"
                )
            ],
            returns="可用工具列表",
            category="mcp",
            dangerous=False
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """获取MCP工具列表."""
        server_url = kwargs.get("server_url", self.server_url)
        
        try:
            logger.info(f"Listing MCP tools from: {server_url}")
            
            # 创建新的客户端实例（如果URL不同）
            if server_url != self.server_url:
                client = MCPClient(server_url)
            else:
                client = self.client
            
            # 获取工具列表
            tools = await client.list_tools()
            
            logger.info(f"Found {len(tools)} MCP tools")
            
            return ToolResult(
                success=True,
                result={"tools": tools, "count": len(tools)},
                error=None
            )
            
        except Exception as e:
            logger.error(f"Failed to list MCP tools: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=str(e)
            )


# 便捷函数
async def mcp_test_connection(server_url: str = "ws://localhost:3000") -> bool:
    """测试MCP连接."""
    try:
        client = MCPClient(server_url)
        await client.connect()
        await client.disconnect()
        return True
    except Exception as e:
        logger.error(f"MCP connection test failed: {e}")
        return False


async def get_mcp_tools(server_url: str = "ws://localhost:3000") -> List[Dict[str, Any]]:
    """获取MCP工具列表."""
    try:
        client = MCPClient(server_url)
        tools = await client.list_tools()
        await client.disconnect()
        return tools
    except Exception as e:
        logger.error(f"Failed to get MCP tools: {e}")
        return []
