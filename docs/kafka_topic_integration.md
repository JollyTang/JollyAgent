# Kafka Topic 设计与启动脚本集成

## 概述

本文档描述了 JollyAgent 监控系统中 Kafka Topic 设计与启动脚本的集成方案。通过这种集成，用户可以在启动监控系统时自动创建所需的 Kafka Topics，无需手动配置。

## 文件结构

```
JollyAgent/
├── src/data_pipeline/
│   └── kafka_topic_design.py          # Kafka Topic 设计核心文件
├── tests/
│   └── kafka_topic_design_test.py     # Topic 设计测试文件
├── scripts/
│   ├── start_monitoring.sh            # 监控系统启动脚本
│   └── init_kafka_topics.sh           # Topic 初始化脚本
├── examples/
│   ├── kafka_topic_demo.py            # Topic 设计演示
│   └── kafka_integration_demo.py      # 集成演示
└── docs/
    └── kafka_topic_integration.md     # 本文档
```

## 功能特性

### 1. 自动 Topic 创建

- **启动时自动创建**: 在运行 `./scripts/start_monitoring.sh` 时，系统会自动创建所需的 Kafka Topics
- **智能检测**: 如果 Topic 已存在，会跳过创建步骤
- **错误处理**: 包含完善的错误处理和重试机制

### 2. 预定义 Topics

系统会自动创建以下三个主要 Topics：

| Topic 名称              | 分区数 | 副本数 | 保留时间 | 用途           |
| ----------------------- | ------ | ------ | -------- | -------------- |
| `jollyagent.executions` | 3      | 2      | 7 天     | Agent 执行记录 |
| `jollyagent.metrics`    | 5      | 2      | 30 天    | 性能指标数据   |
| `jollyagent.events`     | 3      | 2      | 7 天     | 系统事件日志   |

### 3. 完整的数据结构

- **ExecutionRecord**: 执行记录数据结构
- **MetricRecord**: 指标记录数据结构
- **EventRecord**: 事件记录数据结构
- **预定义指标名称**: 标准化的指标命名

## 使用方法

### 启动监控系统

```bash
# 启动完整的监控系统（包括自动创建 Topics）
./scripts/start_monitoring.sh

# 强制重新拉取镜像
./scripts/start_monitoring.sh --force-pull
```

### 启动流程

1. **环境检查**: 检查 Docker 和 Docker Compose
2. **镜像准备**: 拉取必要的 Docker 镜像
3. **服务启动**: 按顺序启动各个服务
   - Zookeeper
   - Kafka
   - ClickHouse 和 Grafana
   - Flink 集群
4. **Topic 创建**: 自动创建 Kafka Topics
5. **健康检查**: 验证所有服务状态

### 停止监控系统

```bash
./scripts/stop_monitoring.sh
```

## 测试

### 运行 Topic 设计测试

```bash
# 运行 Kafka Topic 设计测试
python -m pytest tests/kafka_topic_design_test.py -v

# 运行所有测试
python -m pytest tests/ -v
```

### 演示脚本

```bash
# 运行 Topic 设计演示
python examples/kafka_topic_demo.py

# 运行集成演示
python examples/kafka_integration_demo.py
```

## 配置说明

### Topic 配置

Topics 的配置在 `src/data_pipeline/kafka_topic_design.py` 中定义：

```python
self.topics = {
    TopicType.EXECUTIONS: {
        "name": "jollyagent.executions",
        "partitions": 3,
        "replication_factor": 2,
        "retention_ms": 7 * 24 * 60 * 60 * 1000,  # 7天
        "cleanup_policy": "delete",
        "compression_type": "lz4",
        "description": "Agent 执行记录，包含完整的执行流程和结果"
    },
    # ... 其他 Topics
}
```

### 启动脚本配置

Topic 初始化在 `scripts/start_monitoring.sh` 中集成：

```bash
# 初始化Kafka主题
init_kafka_topics() {
    log_info "初始化Kafka主题..."

    # 等待Kafka服务完全就绪
    sleep 15

    if [ -f "./scripts/init_kafka_topics.sh" ]; then
        ./scripts/init_kafka_topics.sh
        log_success "Kafka主题初始化完成"
    else
        log_warning "Kafka主题初始化脚本不存在，跳过主题创建"
    fi
}
```

## 数据流转示例

### 执行流程数据

```python
# 1. Agent 开始执行事件
agent_start_event = EventRecord(
    event_type=EventType.AGENT_START,
    session_id="session_001",
    execution_id="exec_001"
)

# 2. 执行记录
execution_record = ExecutionRecord(
    execution_id="exec_001",
    session_id="session_001",
    status=ExecutionStatus.SUCCESS
)

# 3. 性能指标
execution_metric = MetricRecord(
    metric_name=MetricNames.EXECUTION_DURATION,
    value=1.25,
    unit="seconds"
)

# 4. Agent 结束事件
agent_end_event = EventRecord(
    event_type=EventType.AGENT_END,
    session_id="session_001"
)
```

### Topic 分配

- **jollyagent.events**: `agent_start_event`, `agent_end_event`
- **jollyagent.executions**: `execution_record`
- **jollyagent.metrics**: `execution_metric`

## 故障排查

### 常见问题

1. **Topic 创建失败**

   - 检查 Kafka 服务是否正常启动
   - 查看 Docker 容器日志: `docker-compose logs kafka`
   - 确认网络连接正常

2. **启动脚本执行失败**

   - 检查 Docker 和 Docker Compose 是否安装
   - 确认有足够的磁盘空间
   - 检查端口是否被占用

3. **测试失败**
   - 确认 Python 环境正确
   - 检查依赖包是否安装完整
   - 验证导入路径是否正确

### 日志查看

```bash
# 查看 Kafka 日志
docker-compose logs kafka

# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs [service_name]
```

## 扩展性

### 添加新的 Topic

1. 在 `src/data_pipeline/kafka_topic_design.py` 中添加新的 Topic 配置
2. 在 `scripts/init_kafka_topics.sh` 中添加创建逻辑
3. 更新测试和演示脚本

### 修改 Topic 配置

1. 修改 `KafkaTopicDesign` 类中的配置
2. 更新 `init_kafka_topics.sh` 中的参数
3. 重新运行启动脚本

## 总结

通过这种集成方案，用户可以获得以下优势：

1. **简化部署**: 一键启动，自动配置
2. **标准化**: 预定义的 Topic 结构和配置
3. **可维护性**: 集中的配置管理和测试
4. **可扩展性**: 易于添加新的 Topics 和功能
5. **可靠性**: 完善的错误处理和健康检查

这种设计确保了监控系统的易用性和可维护性，为用户提供了完整的开箱即用体验。
