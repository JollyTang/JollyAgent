"""
自定义 Instrumentation 使用示例

展示如何在 JollyAgent 中使用自定义 instrumentation 进行监控和追踪。
"""

import asyncio
import logging
from src.monitoring.opentelemetry_integration import initialize_global_integration
from src.monitoring.custom_instrumentation import (
    CustomInstrumentation,
    InstrumentationConfig,
    instrument_agent,
    instrument_executor,
    instrument_memory
)
from src.agent import Agent
from src.executor import get_executor
from src.memory import LayeredMemoryCoordinator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """主函数 - 演示自定义 instrumentation 的使用"""
    
    # 1. 初始化 OpenTelemetry 集成
    logger.info("初始化 OpenTelemetry 集成...")
    ot_integration = initialize_global_integration({
        "service_name": "jollyagent_with_instrumentation",
        "service_version": "1.0.0"
    })
    
    # 2. 创建自定义 instrumentation 配置
    logger.info("创建自定义 instrumentation 配置...")
    config = InstrumentationConfig(
        enable_agent_tracing=True,
        enable_tool_tracing=True,
        enable_memory_tracing=True,
        enable_llm_tracing=True,
        enable_performance_metrics=True,
        enable_error_tracking=True,
        enable_custom_attributes=True,
        trace_http_requests=True,
        trace_file_operations=True
    )
    
    # 3. 创建 Agent 实例
    logger.info("创建 Agent 实例...")
    agent = Agent()
    
    # 4. 为 Agent 添加 instrumentation
    logger.info("为 Agent 添加 instrumentation...")
    instrumentation = instrument_agent(agent, config)
    
    # 5. 为执行器添加 instrumentation
    logger.info("为执行器添加 instrumentation...")
    executor = get_executor()
    instrument_executor(executor, config)
    
    # 6. 为记忆管理器添加 instrumentation
    logger.info("为记忆管理器添加 instrumentation...")
    if hasattr(agent, 'memory_manager'):
        instrument_memory(agent.memory_manager, config)
    
    # 7. 开始对话并测试 instrumentation
    logger.info("开始对话测试...")
    await agent.start_conversation("test_conversation_001")
    
    # 发送一些测试消息
    test_messages = [
        "你好，请介绍一下你自己",
        "请帮我计算 123 + 456",
        "请告诉我今天的天气"
    ]
    
    for i, message in enumerate(test_messages, 1):
        logger.info(f"发送消息 {i}: {message}")
        
        try:
            response = await agent.process_message(message)
            logger.info(f"收到响应 {i}: {response[:100]}...")
            
            # 显示性能指标
            metrics = instrumentation.get_performance_metrics()
            logger.info(f"当前性能指标: {metrics}")
            
        except Exception as e:
            logger.error(f"处理消息 {i} 时出错: {e}")
    
    # 8. 结束对话
    logger.info("结束对话...")
    summary = await agent.end_conversation()
    if summary:
        logger.info(f"对话摘要: {summary[:100]}...")
    
    # 9. 显示最终统计信息
    logger.info("显示最终统计信息...")
    stats = instrumentation.get_statistics()
    
    print("\n" + "="*50)
    print("最终统计信息")
    print("="*50)
    
    print(f"性能指标:")
    for key, value in stats["performance_metrics"].items():
        print(f"  {key}: {value}")
    
    print(f"\n数据收集器统计:")
    for key, value in stats["data_collector_stats"].items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*50)
    
    # 10. 关闭 OpenTelemetry 集成
    logger.info("关闭 OpenTelemetry 集成...")
    ot_integration.shutdown()
    
    logger.info("示例执行完成！")


async def demo_simple_instrumentation():
    """演示简单的 instrumentation 使用"""
    
    logger.info("演示简单的 instrumentation 使用...")
    
    # 创建配置
    config = InstrumentationConfig(
        enable_agent_tracing=True,
        enable_tool_tracing=False,  # 禁用工具追踪
        enable_memory_tracing=False,  # 禁用记忆追踪
        enable_llm_tracing=True,
        enable_performance_metrics=True
    )
    
    # 创建 Agent 并添加 instrumentation
    agent = Agent()
    instrumentation = instrument_agent(agent, config)
    
    # 开始对话
    await agent.start_conversation("simple_demo_001")
    
    # 发送一个简单消息
    response = await agent.process_message("请说你好")
    logger.info(f"响应: {response}")
    
    # 显示指标
    metrics = instrumentation.get_performance_metrics()
    logger.info(f"性能指标: {metrics}")
    
    # 结束对话
    await agent.end_conversation()
    
    logger.info("简单演示完成！")


if __name__ == "__main__":
    # 运行主示例
    asyncio.run(main())
    
    # 运行简单演示
    # asyncio.run(demo_simple_instrumentation()) 