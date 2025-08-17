"""
Kafka Topic 设计演示

演示如何使用 Kafka Topic 设计来创建和管理监控数据。

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


def demo_topic_design():
    """演示 Topic 设计功能"""
    print("=== Kafka Topic 设计演示 ===\n")
    
    # 获取 Topic 设计实例
    topic_design = get_topic_design()
    
    # 显示所有 Topic 配置
    print("1. Topic 配置:")
    for topic_type, config in topic_design.get_all_topics().items():
        print(f"   - {config['name']}: {config['description']}")
        print(f"     分区数: {config['partitions']}, 副本数: {config['replication_factor']}")
        print(f"     保留时间: {config['retention_ms'] // (24 * 60 * 60 * 1000)} 天")
        print(f"     压缩类型: {config['compression_type']}")
        print()


def demo_execution_record():
    """演示执行记录数据结构"""
    print("2. 执行记录数据结构演示:")
    
    # 创建执行记录
    execution = ExecutionRecord(
        execution_id="demo_exec_001",
        session_id="demo_session_001",
        agent_id="demo_agent_001",
        user_message="请帮我计算 2 + 3 的结果",
        start_time=datetime.now().timestamp(),
        status=ExecutionStatus.SUCCESS,
        final_response="2 + 3 = 5",
        metadata={
            "user_id": "user_001",
            "request_type": "calculation",
            "complexity": "simple"
        }
    )
    
    # 转换为 JSON
    execution_json = execution.to_json()
    print("   执行记录 JSON:")
    print(json.dumps(json.loads(execution_json), indent=4, ensure_ascii=False))
    print()


def demo_metric_record():
    """演示指标记录数据结构"""
    print("3. 指标记录数据结构演示:")
    
    # 创建指标记录
    metric = MetricRecord(
        metric_id="demo_metric_001",
        metric_name=MetricNames.EXECUTION_DURATION,
        metric_type="histogram",
        value=1.25,
        unit="seconds",
        labels={
            "session_id": "demo_session_001",
            "agent_id": "demo_agent_001",
            "execution_type": "calculation"
        }
    )
    
    # 转换为 JSON
    metric_json = metric.to_json()
    print("   指标记录 JSON:")
    print(json.dumps(json.loads(metric_json), indent=4, ensure_ascii=False))
    print()


def demo_event_record():
    """演示事件记录数据结构"""
    print("4. 事件记录数据结构演示:")
    
    # 创建事件记录
    event = EventRecord(
        event_id="demo_event_001",
        event_type=EventType.AGENT_START,
        session_id="demo_session_001",
        execution_id="demo_exec_001",
        event_data={
            "user_message": "请帮我计算 2 + 3 的结果",
            "user_message_length": 15,
            "agent_version": "1.0.0"
        },
        severity="info"
    )
    
    # 转换为 JSON
    event_json = event.to_json()
    print("   事件记录 JSON:")
    print(json.dumps(json.loads(event_json), indent=4, ensure_ascii=False))
    print()


def demo_metric_names():
    """演示预定义的指标名称"""
    print("5. 预定义指标名称:")
    print("   执行相关指标:")
    print(f"     - {MetricNames.EXECUTION_DURATION}")
    print(f"     - {MetricNames.EXECUTION_SUCCESS_RATE}")
    print(f"     - {MetricNames.EXECUTION_COUNT}")
    print()
    
    print("   步骤相关指标:")
    print(f"     - {MetricNames.STEP_DURATION}")
    print(f"     - {MetricNames.STEP_COUNT}")
    print(f"     - {MetricNames.STEP_SUCCESS_RATE}")
    print()
    
    print("   LLM 相关指标:")
    print(f"     - {MetricNames.LLM_CALL_DURATION}")
    print(f"     - {MetricNames.LLM_CALL_COUNT}")
    print(f"     - {MetricNames.LLM_TOKEN_USAGE}")
    print()
    
    print("   工具相关指标:")
    print(f"     - {MetricNames.TOOL_EXECUTION_DURATION}")
    print(f"     - {MetricNames.TOOL_EXECUTION_COUNT}")
    print(f"     - {MetricNames.TOOL_SUCCESS_RATE}")
    print()


def demo_topic_creation_script():
    """演示 Topic 创建脚本生成"""
    print("6. Topic 创建脚本生成:")
    
    topic_design = get_topic_design()
    script = topic_design.create_topic_config_script()
    
    print("   生成的脚本内容:")
    print("   " + "\n   ".join(script.split('\n')))
    print()


def main():
    """主函数"""
    try:
        demo_topic_design()
        demo_execution_record()
        demo_metric_record()
        demo_event_record()
        demo_metric_names()
        demo_topic_creation_script()
        
        print("=== 演示完成 ===")
        print("Kafka Topic 设计已成功实现！")
        print("包含以下功能:")
        print("- 三个主要 Topic: executions, metrics, events")
        print("- 完整的数据结构定义")
        print("- JSON 序列化支持")
        print("- 预定义指标名称")
        print("- Topic 创建脚本生成")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 