# 自定义 Instrumentation 使用指南

## 概述

自定义 Instrumentation 模块为 JollyAgent 提供了详细的监控和追踪功能。

## 功能特性

- Agent 方法追踪（process_message, \_think, \_act, \_observe, \_call_llm）
- 工具执行追踪
- 记忆操作追踪
- 性能指标收集
- 错误追踪

## 使用方法

```python
import asyncio
from src.monitoring.opentelemetry_integration import initialize_global_integration
from src.monitoring.custom_instrumentation import instrument_agent, InstrumentationConfig
from src.agent import Agent

async def main():
    # 初始化 OpenTelemetry
    ot_integration = initialize_global_integration()

    # 创建配置
    config = InstrumentationConfig(
        enable_agent_tracing=True,
        enable_tool_tracing=True,
        enable_memory_tracing=True,
        enable_llm_tracing=True
    )

    # 创建 Agent 并添加 instrumentation
    agent = Agent()
    instrumentation = instrument_agent(agent, config)

    # 开始对话
    await agent.start_conversation("test_session")

    # 发送消息
    response = await agent.process_message("你好")

    # 查看性能指标
    metrics = instrumentation.get_performance_metrics()
    print(f"性能指标: {metrics}")

    # 结束对话
    await agent.end_conversation()

    # 关闭 OpenTelemetry
    ot_integration.shutdown()

# 运行
asyncio.run(main())
```

## 配置选项

```python
config = InstrumentationConfig(
    enable_agent_tracing=True,      # 启用 Agent 追踪
    enable_tool_tracing=True,       # 启用工具追踪
    enable_memory_tracing=True,     # 启用记忆追踪
    enable_llm_tracing=True,        # 启用 LLM 追踪
    enable_performance_metrics=True, # 启用性能指标
    enable_error_tracking=True      # 启用错误追踪
)
```

## 性能指标

- agent_executions: Agent 执行次数
- tool_executions: 工具执行次数
- llm_calls: LLM 调用次数
- memory_operations: 记忆操作次数
- total_errors: 错误总数
