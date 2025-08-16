# JollyAgent 监控功能使用指南

## 概述

JollyAgent 提供了完整的监控系统，可以追踪 Agent 的执行过程、性能指标和错误信息。监控功能可以通过配置灵活控制，支持启用和禁用。

## 功能特性

### 1. 执行步骤追踪（Think-Act-Observe-Response）

- 追踪每个 ReAct 循环的完整执行过程
- 记录思考、行动、观察和响应步骤的详细信息
- 支持步骤级别的性能分析和错误追踪

### 2. 自定义 Instrumentation

- 非侵入式的方法包装
- 自动收集性能指标和错误信息
- 支持 Agent、执行器、记忆管理器的监控

### 3. OpenTelemetry 集成

- 标准化的遥测数据收集
- 支持分布式追踪
- 可扩展的指标和日志系统

### 4. 配置化控制

- 通过配置文件控制监控功能的启用/禁用
- 支持细粒度的功能开关
- 不影响正常使用

## 配置说明

### 监控配置选项

在 `src/config.py` 中的 `MonitoringConfig` 类包含以下配置选项：

```python
class MonitoringConfig(BaseModel):
    # 是否启用监控
    enable_monitoring: bool = False

    # OpenTelemetry 配置
    enable_opentelemetry: bool = True

    # 监控组件配置
    enable_agent_tracing: bool = True
    enable_tool_tracing: bool = True
    enable_memory_tracing: bool = True
    enable_llm_tracing: bool = True

    # 性能指标配置
    enable_performance_metrics: bool = True
    enable_error_tracking: bool = True

    # 执行步骤追踪配置
    enable_step_tracking: bool = True
    enable_metadata_collection: bool = True

    # 数据存储配置
    enable_local_backup: bool = True
    backup_directory: str = "./monitoring_data"

    # 服务配置
    service_name: str = "jollyagent"
    service_version: str = "1.0.0"
```

### 配置示例

#### 启用完整监控

```python
from src.config import get_config

config = get_config()
config.monitoring.enable_monitoring = True
config.monitoring.enable_step_tracking = True
config.monitoring.enable_agent_tracing = True
config.monitoring.enable_llm_tracing = True
```

#### 禁用监控

```python
config.monitoring.enable_monitoring = False
```

#### 仅启用步骤追踪

```python
config.monitoring.enable_monitoring = True
config.monitoring.enable_step_tracking = True
config.monitoring.enable_agent_tracing = False
config.monitoring.enable_llm_tracing = False
```

## 使用方法

### 1. 基本使用

监控功能会在 Agent 初始化时自动启用（如果配置中启用了监控）：

```python
from src.agent import Agent
from src.config import get_config

# 获取配置并启用监控
config = get_config()
config.monitoring.enable_monitoring = True

# 创建 Agent 实例（会自动启用监控）
agent = Agent(config=config)

# 正常使用 Agent
await agent.start_conversation("test_session")
response = await agent.process_message("请帮我计算 2 + 3")
```

### 2. 获取监控统计信息

```python
from src.monitoring.monitoring_manager import get_monitoring_manager

manager = get_monitoring_manager()
stats = manager.get_statistics()
print(stats)
```

### 3. 导出监控数据

```python
# 导出到指定文件
success = manager.export_data("./my_monitoring_data.json")

# 导出到默认位置
success = manager.export_data()
```

### 4. 检查监控状态

```python
is_enabled = manager.is_monitoring_enabled()
print(f"监控是否启用: {is_enabled}")
```

## 监控数据格式

### 执行步骤追踪数据

```json
{
  "completed_cycles": [
    {
      "cycle_id": "session_123_cycle_1_1234567890",
      "session_id": "session_123",
      "cycle_number": 1,
      "start_time": 1234567890.123,
      "end_time": 1234567895.456,
      "duration": 5.333,
      "user_message": "请帮我计算 2 + 3",
      "final_response": "2 + 3 = 5",
      "success": true,
      "steps": [
        {
          "step_id": "cycle_1_step_1_think",
          "step_type": "think",
          "step_number": 1,
          "start_time": 1234567890.123,
          "end_time": 1234567891.234,
          "duration": 1.111,
          "status": "success",
          "input_data": { "step_number": 1 },
          "output_data": { "has_thought": true, "tool_calls_count": 0 }
        }
      ]
    }
  ],
  "statistics": {
    "total_cycles": 1,
    "active_cycles": 0,
    "success_rate": 1.0,
    "average_duration": 5.333,
    "step_counts": {
      "think": 1,
      "act": 0,
      "observe": 0
    }
  }
}
```

### 性能指标数据

```json
{
  "performance_metrics": {
    "agent_executions": 1,
    "tool_executions": 0,
    "llm_calls": 1,
    "memory_operations": 0,
    "total_errors": 0
  },
  "monitoring_enabled": true,
  "step_tracking_enabled": true,
  "opentelemetry_enabled": true
}
```

## 演示脚本

运行演示脚本来查看监控功能的效果：

```bash
# 运行监控演示
uv run python examples/monitoring_demo.py

# 运行简单演示
uv run python examples/simple_instrumentation_demo.py
```

## 测试

运行监控功能的测试：

```bash
# 运行所有监控测试
uv run pytest tests/monitoring/ -v

# 运行特定测试
uv run pytest tests/monitoring/step_tracker_test.py -v
uv run pytest tests/monitoring/custom_instrumentation_test.py -v
```

## 故障排查

### 常见问题

1. **监控未启用**

   - 检查 `config.monitoring.enable_monitoring` 是否为 `True`
   - 查看日志中是否有监控初始化信息

2. **OpenTelemetry 依赖缺失**

   - 安装 OpenTelemetry 依赖：`uv add opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation`

3. **权限问题**
   - 确保监控数据目录有写入权限
   - 检查日志文件路径是否正确

### 日志信息

监控系统会输出详细的日志信息：

```
INFO - 监控系统初始化完成
INFO - OpenTelemetry 集成已初始化
INFO - 执行步骤追踪器已初始化
INFO - Agent 监控已启用
INFO - 开始 ReAct 循环: session_123_cycle_1_1234567890
INFO - 结束 ReAct 循环: session_123_cycle_1_1234567890, 持续时间: 5.333秒
```

## 扩展开发

### 添加新的监控指标

1. 在 `CustomInstrumentation` 类中添加新的指标收集逻辑
2. 在 `StepTracker` 中添加新的步骤类型
3. 更新配置类以支持新的监控选项

### 集成外部监控系统

1. 实现自定义的数据导出器
2. 集成 Prometheus、Grafana 等监控工具
3. 添加实时告警功能

## 总结

JollyAgent 的监控系统提供了完整的可观测性解决方案，支持：

- 非侵入式的监控集成
- 灵活的配置控制
- 详细的执行步骤追踪
- 标准化的遥测数据
- 易于扩展的架构

通过合理配置，可以在不影响正常使用的情况下获得丰富的监控数据，帮助分析和优化 Agent 的性能。
