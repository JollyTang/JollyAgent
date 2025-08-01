"""工具系统测试."""

import asyncio
import os
import tempfile
import pytest
from unittest.mock import patch

from src.tools.base import Tool, ToolParameter, ToolResult, ToolSchema
from src.tools.shell import RunShellTool
from src.tools.file import ReadFileTool, WriteFileTool
from src.executor import ToolExecutor


class TestToolBase:
    """工具基类测试."""
    
    def test_tool_parameter(self):
        """测试工具参数定义."""
        param = ToolParameter(
            name="test_param",
            type="string",
            description="测试参数",
            required=True
        )
        
        assert param.name == "test_param"
        assert param.type == "string"
        assert param.required is True
    
    def test_tool_schema(self):
        """测试工具模式定义."""
        schema = ToolSchema(
            name="test_tool",
            description="测试工具",
            parameters=[
                ToolParameter(name="param1", type="string", description="参数1")
            ],
            returns="测试结果"
        )
        
        assert schema.name == "test_tool"
        assert len(schema.parameters) == 1
        assert schema.returns == "测试结果"


class TestToolExecutor:
    """工具执行器测试."""
    
    def setup_method(self):
        """设置测试环境."""
        self.executor = ToolExecutor()
    
    def test_register_tool(self):
        """测试工具注册."""
        self.executor.register_tool(RunShellTool)
        
        assert "run_shell" in self.executor.list_tools()
        assert len(self.executor.list_tools()) == 1
    
    def test_get_tool_schema(self):
        """测试获取工具模式."""
        self.executor.register_tool(RunShellTool)
        
        schema = self.executor.get_tool_schema("run_shell")
        assert schema is not None
        assert schema["name"] == "run_shell"
        assert schema["description"] == "执行系统Shell命令"
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """测试执行不存在的工具."""
        result = await self.executor.execute_tool("nonexistent_tool")
        
        assert result.success is False
        assert "not found" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_tool_with_invalid_params(self):
        """测试使用无效参数执行工具."""
        self.executor.register_tool(RunShellTool)
        
        result = await self.executor.execute_tool("run_shell")
        
        assert result.success is False
        assert "Invalid parameters" in result.error


class TestShellTool:
    """Shell工具测试."""
    
    def setup_method(self):
        """设置测试环境."""
        self.tool = RunShellTool()
    
    def test_schema(self):
        """测试工具模式."""
        schema = self.tool.schema
        
        assert schema.name == "run_shell"
        assert schema.dangerous is True
        assert len(schema.parameters) == 3
    
    @pytest.mark.asyncio
    async def test_execute_simple_command(self):
        """测试执行简单命令."""
        result = await self.tool.execute(command="echo 'hello world'")
        
        assert result.success is True
        assert "hello world" in result.result["stdout"]
        assert result.result["exit_code"] == 0
    
    @pytest.mark.asyncio
    async def test_execute_invalid_command(self):
        """测试执行无效命令."""
        result = await self.tool.execute(command="nonexistent_command_12345")
        
        assert result.success is False
        assert result.result["exit_code"] != 0
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout(self):
        """测试命令超时."""
        result = await self.tool.execute(command="sleep 10", timeout=1)
        
        assert result.success is False
        assert "timed out" in result.error


class TestFileTools:
    """文件工具测试."""
    
    def setup_method(self):
        """设置测试环境."""
        self.read_tool = ReadFileTool()
        self.write_tool = WriteFileTool()
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
    
    def teardown_method(self):
        """清理测试环境."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_write_and_read_file(self):
        """测试文件写入和读取."""
        test_content = "Hello, World!\n这是测试内容。"
        
        # 写入文件
        write_result = await self.write_tool.execute(
            file_path=self.test_file,
            content=test_content
        )
        
        assert write_result.success is True
        assert os.path.exists(self.test_file)
        
        # 读取文件
        read_result = await self.read_tool.execute(file_path=self.test_file)
        
        assert read_result.success is True
        assert read_result.result["content"] == test_content
    
    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self):
        """测试读取不存在的文件."""
        result = await self.read_tool.execute(file_path="nonexistent_file.txt")
        
        assert result.success is False
        assert "not found" in result.error
    
    @pytest.mark.asyncio
    async def test_write_file_with_append_mode(self):
        """测试追加模式写入文件."""
        content1 = "第一行\n"
        content2 = "第二行\n"
        
        # 第一次写入
        result1 = await self.write_tool.execute(
            file_path=self.test_file,
            content=content1
        )
        assert result1.success is True
        
        # 追加写入
        result2 = await self.write_tool.execute(
            file_path=self.test_file,
            content=content2,
            mode="a"
        )
        assert result2.success is True
        
        # 读取验证
        read_result = await self.read_tool.execute(file_path=self.test_file)
        assert read_result.success is True
        assert read_result.result["content"] == content1 + content2


if __name__ == "__main__":
    pytest.main([__file__]) 