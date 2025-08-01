#!/usr/bin/env python3
"""MCP客户端测试脚本 - 用于验证与本地MCP服务端的连接"""

import sys
import os
import asyncio
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.tools.mcp import MCPClient, mcp_test_connection, get_mcp_tools

async def test_mcp_server():
    """测试MCP服务端连接和功能"""
    server_url = "ws://localhost:3000"
    
    print("=== MCP客户端测试 ===")
    print(f"目标服务端: {server_url}")
    print()
    
    # 1. 测试连接
    print("1. 测试连接...")
    try:
        is_connected = await mcp_test_connection(server_url)
        if is_connected:
            print("✅ 连接成功!")
        else:
            print("❌ 连接失败!")
            return
    except Exception as e:
        print(f"❌ 连接异常: {e}")
        return
    
    print()
    
    # 2. 获取工具列表
    print("2. 获取工具列表...")
    try:
        tools = await get_mcp_tools(server_url)
        print(f"✅ 找到 {len(tools)} 个工具:")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description']}")
    except Exception as e:
        print(f"❌ 获取工具列表失败: {e}")
        return
    
    print()
    
    # 3. 测试工具调用
    print("3. 测试工具调用...")
    try:
        client = MCPClient(server_url)
        await client.connect()
        
        # 测试echo工具
        test_args = {"message": "Hello MCP!", "number": 42, "list": [1, 2, 3]}
        result = await client.call_tool("echo", test_args)
        print(f"✅ echo工具调用成功:")
        print(f"   输入: {test_args}")
        print(f"   输出: {result}")
        
        await client.disconnect()
    except Exception as e:
        print(f"❌ 工具调用失败: {e}")
        return
    
    print()
    print("🎉 所有测试通过! MCP客户端工作正常!")

if __name__ == "__main__":
    asyncio.run(test_mcp_server()) 