# 监控模块演示

本目录包含 JollyAgent 监控系统的演示和示例代码。

## 演示文件

- `integration_example.py` - 监控集成示例
- `run_demo.py` - 演示运行脚本

## 运行演示

### 运行完整演示

```bash
# 从项目根目录运行
python demo/monitoring/run_demo.py
```

### 直接运行示例

```bash
# 直接运行集成示例
python demo/monitoring/integration_example.py
```

## 演示内容

### MonitoredAgent 示例

`integration_example.py` 展示了如何在 JollyAgent 核心代码中集成监控功能：

1. **初始化监控系统**

   - OpenTelemetry 集成配置
   - 数据收集器配置

2. **执行任务监控**

   - Think-Act-Observe-Response 模式追踪
   - 会话管理
   - 事件记录

3. **错误处理**

   - 异常捕获和记录
   - 错误统计

4. **统计信息**
   - 执行统计
   - 性能指标

## 演示流程

1. **Think 阶段** - 分析输入数据
2. **Act 阶段** - 执行处理动作
3. **Observe 阶段** - 观察执行结果
4. **Response 阶段** - 生成最终响应

每个阶段都会被监控系统记录，包括：

- 执行时间
- 输入输出数据
- 成功/失败状态
- 错误信息（如果有）

## 输出示例

```
=== JollyAgent 监控系统演示 ===

任务执行结果: {
    'final_response': 'Task completed: Observation completed',
    'summary': 'All phases executed successfully',
    'timestamp': 1755355374.0383599
}

监控统计: {
    'opentelemetry': {'available': False},
    'data_collector': {
        'total_sessions': 1,
        'total_events': 5,
        'event_types': {
            'think': 1, 'act': 1, 'observe': 1,
            'response': 1, 'completion': 1
        },
        'ot_integration_available': False
    }
}

演示完成！
```

## 注意事项

1. 演示不依赖 OpenTelemetry 安装，会自动降级
2. 所有监控数据都在内存中，重启后丢失
3. 演示包含模拟的延迟，以展示时间追踪功能
4. 可以通过修改配置来启用不同的监控功能
