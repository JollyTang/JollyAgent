"""
Kafka 集成演示

演示 Kafka Topic 设计与启动脚本的集成功能。

Author: JollyAgent Team
Date: 2025-01-17
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_pipeline.kafka_topic_design import (
    TopicType, ExecutionStatus, StepType, EventType,
    ExecutionRecord, MetricRecord, EventRecord,
    KafkaTopicDesign, MetricNames, get_topic_design
)


def demo_topic_integration():
    """演示 Topic 集成功能"""
    print("=== Kafka Topic 集成演示 ===\n")
    
    # 获取 Topic 设计实例
    topic_design = get_topic_design()
    
    print("1. Topic 配置与启动脚本集成:")
    print("   - 启动脚本: scripts/start_monitoring.sh")
    print("   - Topic 初始化脚本: scripts/init_kafka_topics.sh")
    print("   - 自动创建 Topics 在服务启动后")
    print()
    
    # 显示 Topic 配置
    print("2. 将在启动时自动创建的 Topics:")
    for topic_type, config in topic_design.get_all_topics().items():
        print(f"   - {config['name']}: {config['description']}")
        print(f"     分区数: {config['partitions']}, 副本数: {config['replication_factor']}")
        print(f"     保留时间: {config['retention_ms'] // (24 * 60 * 60 * 1000)} 天")
        print(f"     压缩类型: {config['compression_type']}")
        print()


def demo_data_flow():
    """演示数据流转"""
    print("3. 数据流转示例:")
    
    # 模拟一个完整的执行流程
    session_id = "demo_session_001"
    execution_id = "demo_exec_001"
    
    # 1. Agent 开始执行事件
    agent_start_event = EventRecord(
        event_id=f"event_{session_id}_start",
        event_type=EventType.AGENT_START,
        session_id=session_id,
        execution_id=execution_id,
        event_data={
            "user_message": "请帮我计算 2 + 3 的结果",
            "agent_version": "1.0.0"
        }
    )
    
    # 2. 执行记录
    execution_record = ExecutionRecord(
        execution_id=execution_id,
        session_id=session_id,
        agent_id="demo_agent_001",
        user_message="请帮我计算 2 + 3 的结果",
        start_time=datetime.now().timestamp(),
        status=ExecutionStatus.SUCCESS,
        final_response="2 + 3 = 5",
        steps=[
            {
                "step_type": "think",
                "step_number": 1,
                "duration": 0.1,
                "status": "success"
            },
            {
                "step_type": "act",
                "step_number": 2,
                "duration": 0.05,
                "status": "success"
            }
        ]
    )
    
    # 3. 性能指标
    execution_metric = MetricRecord(
        metric_id=f"metric_{execution_id}_duration",
        metric_name=MetricNames.EXECUTION_DURATION,
        metric_type="histogram",
        value=0.15,
        unit="seconds",
        labels={
            "session_id": session_id,
            "agent_id": "demo_agent_001",
            "execution_type": "calculation"
        }
    )
    
    # 4. Agent 结束事件
    agent_end_event = EventRecord(
        event_id=f"event_{session_id}_end",
        event_type=EventType.AGENT_END,
        session_id=session_id,
        execution_id=execution_id,
        event_data={
            "success": True,
            "duration": 0.15,
            "final_response": "2 + 3 = 5"
        }
    )
    
    print("   数据将发送到以下 Topics:")
    print(f"   - jollyagent.events: {agent_start_event.event_type.value}, {agent_end_event.event_type.value}")
    print(f"   - jollyagent.executions: {execution_record.execution_id}")
    print(f"   - jollyagent.metrics: {execution_metric.metric_name}")
    print()


def demo_usage_instructions():
    """演示使用说明"""
    print("4. 使用说明:")
    print("   启动监控系统:")
    print("   $ ./scripts/start_monitoring.sh")
    print()
    print("   启动过程包括:")
    print("   1. 检查 Docker 环境")
    print("   2. 启动 Zookeeper")
    print("   3. 启动 Kafka")
    print("   4. 启动 ClickHouse 和 Grafana")
    print("   5. 启动 Flink 集群")
    print("   6. 自动创建 Kafka Topics")
    print("   7. 验证服务健康状态")
    print()
    print("   停止监控系统:")
    print("   $ ./scripts/stop_monitoring.sh")
    print()
    print("   查看服务状态:")
    print("   $ docker-compose ps")
    print()
    print("   访问服务:")
    print("   - Grafana: http://localhost:3000 (admin/admin)")
    print("   - Flink Web UI: http://localhost:8081")
    print("   - ClickHouse: http://localhost:8123")
    print("   - Kafka: localhost:9092")
    print()


def demo_test_integration():
    """演示测试集成"""
    print("5. 测试集成:")
    print("   运行 Kafka Topic 设计测试:")
    print("   $ python -m pytest tests/kafka_topic_design_test.py -v")
    print()
    print("   运行所有测试:")
    print("   $ python -m pytest tests/ -v")
    print()
    print("   测试文件位置:")
    print("   - tests/kafka_topic_design_test.py")
    print("   - tests/monitoring/ (监控相关测试)")
    print()


def main():
    """主函数"""
    try:
        demo_topic_integration()
        demo_data_flow()
        demo_usage_instructions()
        demo_test_integration()
        
        print("=== 集成演示完成 ===")
        print("Kafka Topic 设计与启动脚本集成成功！")
        print("现在用户可以通过以下方式使用:")
        print("1. 运行 ./scripts/start_monitoring.sh 启动完整监控系统")
        print("2. Topics 将自动创建，无需手动配置")
        print("3. 测试文件已移动到 tests/ 目录")
        print("4. 所有功能都已集成到启动流程中")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 