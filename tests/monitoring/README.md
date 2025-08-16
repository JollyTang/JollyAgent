# 监控模块测试

本目录包含 JollyAgent 监控系统的所有测试文件。

## 测试文件

- `opentelemetry_integration_test.py` - OpenTelemetry 集成测试
- `data_collector_test.py` - 数据收集器测试
- `run_tests.py` - 测试运行脚本

## 运行测试

### 运行所有监控测试

```bash
# 从项目根目录运行
python tests/monitoring/run_tests.py

# 或者使用 pytest
pytest tests/monitoring/
```

### 运行单个测试文件

```bash
# 运行 OpenTelemetry 集成测试
python -m pytest tests/monitoring/opentelemetry_integration_test.py

# 运行数据收集器测试
python -m pytest tests/monitoring/data_collector_test.py
```

### 运行特定测试类

```bash
# 运行 OpenTelemetry 集成测试类
python -m pytest tests/monitoring/opentelemetry_integration_test.py::TestOpenTelemetryIntegration

# 运行数据收集器测试类
python -m pytest tests/monitoring/data_collector_test.py::TestDataCollector
```

## 测试覆盖

### OpenTelemetry 集成测试

- ✅ 初始化测试（有/无 OpenTelemetry）
- ✅ 执行追踪上下文管理器测试
- ✅ 指标记录测试
- ✅ 全局集成实例测试
- ✅ 错误处理测试

### 数据收集器测试

- ✅ 会话管理测试
- ✅ 事件记录测试
- ✅ 错误事件处理测试
- ✅ 上下文管理器测试
- ✅ 统计信息测试
- ✅ 异常处理测试

## 注意事项

1. 测试文件会自动处理 OpenTelemetry 未安装的情况
2. 所有测试都使用 mock 对象，不依赖外部服务
3. 测试覆盖了正常和异常情况
4. 测试结果会显示详细的执行信息
