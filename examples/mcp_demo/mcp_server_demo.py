import asyncio
import websockets
import json
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOLS = [
    {"name": "echo", "description": "回显参数"}
]

def make_response(id, result=None, error=None):
    """创建JSON-RPC响应"""
    resp = {"jsonrpc": "2.0", "id": id}
    if error:
        resp["error"] = error
    else:
        resp["result"] = result
    return resp

async def handler(websocket, path):
    """处理WebSocket连接"""
    logger.info(f"新的WebSocket连接: {websocket.remote_address}")
    
    try:
        async for message in websocket:
            try:
                logger.info(f"收到消息: {message}")
                req = json.loads(message)
                method = req.get("method")
                id = req.get("id")
                
                logger.info(f"处理请求: method={method}, id={id}")
                
                if method == "tools/list":
                    response = make_response(id, {"tools": TOOLS})
                    response_str = json.dumps(response)
                    logger.info(f"返回工具列表: {response_str}")
                    await websocket.send(response_str)
                    
                elif method == "tools/call":
                    params = req.get("params", {})
                    name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    logger.info(f"调用工具: {name}, 参数: {arguments}")
                    
                    if name == "echo":
                        response = make_response(id, {"output": arguments})
                        response_str = json.dumps(response)
                        logger.info(f"echo工具返回: {response_str}")
                        await websocket.send(response_str)
                    else:
                        error_response = make_response(id, error={"code": -1, "message": f"Tool '{name}' not found"})
                        error_response_str = json.dumps(error_response)
                        logger.warning(f"工具未找到: {error_response_str}")
                        await websocket.send(error_response_str)
                        
                else:
                    error_response = make_response(id, error={"code": -32601, "message": f"Method '{method}' not found"})
                    error_response_str = json.dumps(error_response)
                    logger.warning(f"方法未找到: {error_response_str}")
                    await websocket.send(error_response_str)
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {e}")
                error_response = {
                    "jsonrpc": "2.0", 
                    "id": None, 
                    "error": {"code": -32700, "message": "Parse error"}
                }
                await websocket.send(json.dumps(error_response))
                
            except Exception as e:
                logger.error(f"处理消息时发生错误: {e}")
                error_response = {
                    "jsonrpc": "2.0", 
                    "id": None, 
                    "error": {"code": -32000, "message": str(e)}
                }
                await websocket.send(json.dumps(error_response))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("WebSocket连接已关闭")
    except Exception as e:
        logger.error(f"WebSocket处理异常: {e}")

async def main():
    """主函数，启动WebSocket服务器"""
    print("MCP Demo Server starting at ws://localhost:3000 ...")
    async with websockets.serve(handler, "localhost", 3000):
        print("MCP Demo Server is running! Press Ctrl+C to stop.")
        await asyncio.Future()  # 保持服务器运行

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMCP Demo Server stopped.") 