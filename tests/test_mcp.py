"""MCP工具测试."""

import asyncio
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.tools.mcp import MCPClient, MCPCallTool, MCPListToolsTool, mcp_test_connection


class TestMCPClient:
    """MCP客户端测试."""
    
    def setup_method(self):
        """设置测试环境."""
        self.client = MCPClient("ws://localhost:3000")
    
    def test_initialization(self):
        """测试客户端初始化."""
        assert self.client.server_url == "ws://localhost:3000"
        assert self.client.websocket is None
        assert self.client.request_id == 0
    
    def test_get_next_request_id(self):
        """测试请求ID生成."""
        id1 = self.client._get_next_request_id()
        id2 = self.client._get_next_request_id()
        
        assert id1 == 1
        assert id2 == 2
        assert self.client.request_id == 2
    
    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self):
        """测试连接和断开连接."""
        with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_websocket = AsyncMock()
            mock_connect.return_value = mock_websocket
            
            await self.client.connect()
            
            mock_connect.assert_called_once_with("ws://localhost:3000")
            assert self.client.websocket == mock_websocket
            
            await self.client.disconnect()
            mock_websocket.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """测试成功调用工具."""
        with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_websocket = AsyncMock()
            mock_connect.return_value = mock_websocket
            
            # 模拟响应
            response_data = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {"output": "test result"}
            }
            mock_websocket.recv.return_value = json.dumps(response_data)
            
            result = await self.client.call_tool("test_tool", {"arg": "value"})
            
            assert result == {"output": "test result"}
            mock_websocket.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_call_tool_error(self):
        """测试工具调用错误."""
        with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_websocket = AsyncMock()
            mock_connect.return_value = mock_websocket
            
            # 模拟错误响应
            response_data = {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {"code": -1, "message": "Tool not found"}
            }
            mock_websocket.recv.return_value = json.dumps(response_data)
            
            with pytest.raises(Exception, match="MCP server error"):
                await self.client.call_tool("nonexistent_tool", {})
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """测试获取工具列表."""
        with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_websocket = AsyncMock()
            mock_connect.return_value = mock_websocket
            
            # 模拟响应
            response_data = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "tools": [
                        {"name": "tool1", "description": "Test tool 1"},
                        {"name": "tool2", "description": "Test tool 2"}
                    ]
                }
            }
            mock_websocket.recv.return_value = json.dumps(response_data)
            
            tools = await self.client.list_tools()
            
            assert len(tools) == 2
            assert tools[0]["name"] == "tool1"
            assert tools[1]["name"] == "tool2"


class TestMCPCallTool:
    """MCP调用工具测试."""
    
    def setup_method(self):
        """设置测试环境."""
        self.tool = MCPCallTool()
    
    def test_schema(self):
        """测试工具模式."""
        schema = self.tool.schema
        
        assert schema.name == "mcp_call"
        assert schema.category == "mcp"
        assert len(schema.parameters) == 3
    
    @pytest.mark.asyncio
    async def test_execute_success(self):
        """测试成功执行."""
        with patch.object(self.tool.client, 'call_tool', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"result": "success"}
            
            result = await self.tool.execute(
                tool_name="test_tool",
                arguments={"arg": "value"}
            )
            
            assert result.success is True
            assert result.result == {"result": "success"}
            mock_call.assert_called_once_with("test_tool", {"arg": "value"})
    
    @pytest.mark.asyncio
    async def test_execute_missing_tool_name(self):
        """测试缺少工具名称."""
        result = await self.tool.execute(arguments={"arg": "value"})
        
        assert result.success is False
        assert "Tool name is required" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_invalid_arguments(self):
        """测试无效参数."""
        result = await self.tool.execute(
            tool_name="test_tool",
            arguments="invalid"
        )
        
        assert result.success is False
        assert "Arguments must be a dictionary" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_connection_error(self):
        """测试连接错误."""
        with patch.object(self.tool.client, 'call_tool', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("Connection failed")
            
            result = await self.tool.execute(
                tool_name="test_tool",
                arguments={"arg": "value"}
            )
            
            assert result.success is False
            assert "Connection failed" in result.error


class TestMCPListToolsTool:
    """MCP工具列表查询工具测试."""
    
    def setup_method(self):
        """设置测试环境."""
        self.tool = MCPListToolsTool()
    
    def test_schema(self):
        """测试工具模式."""
        schema = self.tool.schema
        
        assert schema.name == "mcp_list_tools"
        assert schema.category == "mcp"
        assert len(schema.parameters) == 1
    
    @pytest.mark.asyncio
    async def test_execute_success(self):
        """测试成功执行."""
        with patch.object(self.tool.client, 'list_tools', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [
                {"name": "tool1", "description": "Test tool 1"},
                {"name": "tool2", "description": "Test tool 2"}
            ]
            
            result = await self.tool.execute()
            
            assert result.success is True
            assert result.result["count"] == 2
            assert len(result.result["tools"]) == 2
    
    @pytest.mark.asyncio
    async def test_execute_connection_error(self):
        """测试连接错误."""
        with patch.object(self.tool.client, 'list_tools', new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = Exception("Connection failed")
            
            result = await self.tool.execute()
            
            assert result.success is False
            assert "Connection failed" in result.error


class TestMCPUtilityFunctions:
    """MCP工具函数测试."""
    
    @pytest.mark.asyncio
    async def test_test_mcp_connection_success(self):
        """测试连接测试成功."""
        with patch('src.tools.mcp.MCPClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock()
            mock_client.disconnect = AsyncMock()
            mock_client_class.return_value = mock_client
            
            result = await mcp_test_connection("ws://localhost:3000")
            
            assert result is True
            mock_client.connect.assert_called_once()
            mock_client.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_test_mcp_connection_failure(self):
        """测试连接测试失败."""
        with patch('src.tools.mcp.MCPClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.connect = AsyncMock(side_effect=Exception("Connection failed"))
            mock_client_class.return_value = mock_client
            
            result = await mcp_test_connection("ws://localhost:3000")
            
            assert result is False


if __name__ == "__main__":
    pytest.main([__file__]) 