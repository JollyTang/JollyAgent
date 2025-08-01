#!/usr/bin/env python3
"""MCP调试脚本"""

import sys
import os
import asyncio
import json
import websockets

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

async def debug_mcp():
    """调试MCP连接"""
    server_url = "ws://localhost:3000"
    
    print("=== MCP调试 ===")
    print(f"连接地址: {server_url}")
    
    try:
        # 直接使用websockets连接
        async with websockets.connect(server_url) as websocket:
            print("✅ WebSocket连接成功")
            
            # 测试tools/list
            list_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            
            print(f"发送请求: {json.dumps(list_request, indent=2)}")
            await websocket.send(json.dumps(list_request))
            
            response = await websocket.recv()
            print(f"收到响应: {response}")
            
            # 测试tools/call
            call_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "echo",
                    "arguments": {"test": "hello"}
                }
            }
            
            print(f"发送请求: {json.dumps(call_request, indent=2)}")
            await websocket.send(json.dumps(call_request))
            
            response = await websocket.recv()
            print(f"收到响应: {response}")
            
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_mcp()) 