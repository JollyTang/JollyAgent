#!/usr/bin/env python3
"""JollyAgent 演示脚本."""

import asyncio
import logging
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agent import Agent, get_agent

# 配置日志
logging.basicConfig(level=logging.INFO)


async def demo_basic_conversation():
    """演示基本对话功能."""
    print("=== JollyAgent 基本对话演示 ===")
    
    # 在切换目录之前初始化Agent
    agent = await get_agent()
    await agent.start_conversation("demo_conversation")
    
    # 切换到demo目录
    demo_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(demo_dir)
    print(f"工作目录: {os.getcwd()}")
    
    # 演示1：简单问候
    print("\n1. 简单问候")
    response = await agent.process_message("你好，请介绍一下你自己")
    print(f"Agent: {response}")
    
    # 演示2：文件操作
    print("\n2. 文件操作演示")
    response = await agent.process_message("请创建一个名为demo.txt的文件，内容为'Hello, JollyAgent!'")
    print(f"Agent: {response}")
    
    # 演示3：读取文件
    print("\n3. 读取文件演示")
    response = await agent.process_message("请读取demo.txt文件的内容")
    print(f"Agent: {response}")
    
    # 演示4：系统命令
    print("\n4. 系统命令演示")
    response = await agent.process_message("请执行命令'ls -la'来查看当前目录")
    print(f"Agent: {response}")


async def demo_tool_system():
    """演示工具系统."""
    print("\n=== 工具系统演示 ===")
    
    from src.executor import get_executor
    
    executor = get_executor()
    
    print(f"可用工具: {executor.list_tools()}")
    
    # 演示工具模式
    print("\n工具模式信息:")
    for tool_name in executor.list_tools():
        schema = executor.get_tool_schema(tool_name)
        print(f"- {tool_name}: {schema['description']}")
        for param in schema['parameters']:
            required = "必需" if param['required'] else "可选"
            print(f"  - {param['name']} ({param['type']}, {required}): {param['description']}")


async def demo_react_cycle():
    """演示ReAct循环."""
    print("\n=== ReAct循环演示 ===")
    
    # 在切换目录之前初始化Agent
    agent = await get_agent()
    await agent.start_conversation("react_demo")
    
    # 切换到demo目录
    demo_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(demo_dir)
    
    # 演示多步骤任务
    print("\n多步骤任务演示:")
    response = await agent.process_message("请创建一个名为test.txt的文件，写入'测试内容'，然后读取它并告诉我内容")
    print(f"Agent: {response}")
    
    # 显示ReAct步骤
    print(f"\nReAct步骤数量: {len(agent.state.react_steps)}")
    for i, step in enumerate(agent.state.react_steps, 1):
        print(f"\n步骤 {i}:")
        if step.thought:
            print(f"  思考: {step.thought.content[:100]}...")
        if step.tool_calls:
            print(f"  工具调用: {len(step.tool_calls)} 个")
            for tool_call in step.tool_calls:
                print(f"    - {tool_call.name}: {tool_call.arguments}")
        if step.observations:
            print(f"  观察结果: {len(step.observations)} 个")
            for obs in step.observations:
                print(f"    - {obs.tool_name}: {'成功' if obs.success else '失败'}")


async def demo_file_operations():
    """演示文件操作功能."""
    print("\n=== 文件操作演示 ===")
    
    # 在切换目录之前初始化Agent
    agent = await get_agent()
    await agent.start_conversation("file_demo")
    
    # 切换到demo目录
    demo_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(demo_dir)
    
    # 创建多个文件
    print("\n1. 创建多个文件")
    response = await agent.process_message("请创建三个文件：file1.txt内容为'文件1'，file2.txt内容为'文件2'，file3.txt内容为'文件3'")
    print(f"Agent: {response}")
    
    # 列出文件
    print("\n2. 列出当前目录文件")
    response = await agent.process_message("请执行'ls -la'命令查看当前目录的所有文件")
    print(f"Agent: {response}")
    
    # 读取所有文件
    print("\n3. 读取所有文件内容")
    response = await agent.process_message("请读取file1.txt、file2.txt和file3.txt的内容并告诉我")
    print(f"Agent: {response}")


async def main():
    """主函数."""
    try:
        await demo_tool_system()
        await demo_basic_conversation()
        # await demo_react_cycle()
        # await demo_file_operations()
        
        print("\n=== 演示完成 ===")
        print("JollyAgent 已成功实现以下功能:")
        print("- ReAct循环核心逻辑")
        print("- 工具调用系统（run_shell, read_file, write_file）")
        print("- LLM集成（支持硅基流动API）")
        print("- 多轮对话管理")
        print("- 错误处理和重试机制")
        
        # 显示演示目录中的文件
        demo_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"\n演示过程中创建的文件（在 {demo_dir} 目录中）:")
        if os.path.exists(demo_dir):
            for file in os.listdir(demo_dir):
                if file.endswith('.txt'):
                    print(f"  - {file}")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        logging.exception("演示错误")


if __name__ == "__main__":
    asyncio.run(main()) 