"""
Kafka Topic 结构设计

本模块定义了 JollyAgent 监控系统的 Kafka Topic 结构，
包括 executions、metrics、events 三个主要 Topic 的设计。

Author: JollyAgent Team
Date: 2025-08-17
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import json
from datetime import datetime


class TopicType(Enum):
    """Topic 类型枚举"""
    EXECUTIONS = "executions"
    METRICS = "metrics"
    EVENTS = "events"


class ExecutionStatus(Enum):
    """执行状态枚举"""
    STARTED = "started"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class StepType(Enum):
    """步骤类型枚举"""
    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"
    RESPONSE = "response"


class EventType(Enum):
    """事件类型枚举"""
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    STEP_START = "step_start"
    STEP_END = "step_end"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    LLM_CALL = "llm_call"
    LLM_RESPONSE = "llm_response"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ExecutionRecord:
    """执行记录数据结构 - executions topic"""
    # 基础信息
    execution_id: str
    session_id: str
    agent_id: str
    user_message: str
    
    # 时间信息
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    
    # 状态信息
    status: ExecutionStatus = ExecutionStatus.STARTED
    error_message: Optional[str] = None
    
    # 执行详情
    steps: List[Dict[str, Any]] = field(default_factory=list)
    final_response: Optional[str] = None
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "execution_id": self.execution_id,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "user_message": self.user_message,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "status": self.status.value,
            "error_message": self.error_message,
            "steps": self.steps,
            "final_response": self.final_response,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    def to_json(self) -> str:
        """转换为 JSON 格式"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class MetricRecord:
    """指标记录数据结构 - metrics topic"""
    # 基础信息
    metric_id: str
    metric_name: str
    metric_type: str  # counter, gauge, histogram, summary
    
    # 值信息
    value: float
    unit: Optional[str] = None
    
    # 标签信息
    labels: Dict[str, str] = field(default_factory=dict)
    
    # 时间信息
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "metric_id": self.metric_id,
            "metric_name": self.metric_name,
            "metric_type": self.metric_type,
            "value": self.value,
            "unit": self.unit,
            "labels": self.labels,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """转换为 JSON 格式"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class EventRecord:
    """事件记录数据结构 - events topic"""
    # 基础信息
    event_id: str
    event_type: EventType
    session_id: Optional[str] = None
    execution_id: Optional[str] = None
    
    # 事件详情
    event_data: Dict[str, Any] = field(default_factory=dict)
    
    # 时间信息
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    
    # 严重程度
    severity: str = "info"  # debug, info, warning, error, critical
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "session_id": self.session_id,
            "execution_id": self.execution_id,
            "event_data": self.event_data,
            "timestamp": self.timestamp,
            "severity": self.severity,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """转换为 JSON 格式"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2) 


class KafkaTopicDesign:
    """Kafka Topic 设计类"""
    
    def __init__(self):
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
            TopicType.METRICS: {
                "name": "jollyagent.metrics",
                "partitions": 5,
                "replication_factor": 2,
                "retention_ms": 30 * 24 * 60 * 60 * 1000,  # 30天
                "cleanup_policy": "delete",
                "compression_type": "lz4",
                "description": "性能指标数据，用于实时监控和告警"
            },
            TopicType.EVENTS: {
                "name": "jollyagent.events",
                "partitions": 3,
                "replication_factor": 2,
                "retention_ms": 7 * 24 * 60 * 60 * 1000,  # 7天
                "cleanup_policy": "delete",
                "compression_type": "lz4",
                "description": "系统事件日志，用于审计和调试"
            }
        }
    
    def get_topic_config(self, topic_type: TopicType) -> Dict[str, Any]:
        """获取指定 Topic 的配置"""
        return self.topics.get(topic_type, {})
    
    def get_all_topics(self) -> Dict[str, Dict[str, Any]]:
        """获取所有 Topic 配置"""
        return {topic_type.value: config for topic_type, config in self.topics.items()}
    
    def create_topic_config_script(self) -> str:
        """生成 Kafka Topic 创建脚本"""
        script_lines = [
            "#!/bin/bash",
            "# Kafka Topic 创建脚本",
            "# 用于创建 JollyAgent 监控系统的 Topic",
            "",
            "KAFKA_HOME=${KAFKA_HOME:-/opt/kafka}",
            "KAFKA_BROKERS=${KAFKA_BROKERS:-localhost:9092}",
            "",
            "echo '开始创建 JollyAgent 监控系统 Topic...'",
            ""
        ]
        
        for topic_type, config in self.topics.items():
            script_lines.extend([
                f"echo '创建 Topic: {config['name']}'",
                f"$KAFKA_HOME/bin/kafka-topics.sh --create \\",
                f"  --bootstrap-server $KAFKA_BROKERS \\",
                f"  --topic {config['name']} \\",
                f"  --partitions {config['partitions']} \\",
                f"  --replication-factor {config['replication_factor']} \\",
                f"  --config retention.ms={config['retention_ms']} \\",
                f"  --config cleanup.policy={config['cleanup_policy']} \\",
                f"  --config compression.type={config['compression_type']}",
                ""
            ])
        
        script_lines.extend([
            "echo 'Topic 创建完成！'",
            "echo '列出所有 Topic:'",
            "$KAFKA_HOME/bin/kafka-topics.sh --list --bootstrap-server $KAFKA_BROKERS"
        ])
        
        return "\n".join(script_lines)


# 预定义的指标名称
class MetricNames:
    """预定义的指标名称"""
    # 执行相关指标
    EXECUTION_DURATION = "execution_duration"
    EXECUTION_SUCCESS_RATE = "execution_success_rate"
    EXECUTION_COUNT = "execution_count"
    
    # 步骤相关指标
    STEP_DURATION = "step_duration"
    STEP_COUNT = "step_count"
    STEP_SUCCESS_RATE = "step_success_rate"
    
    # LLM 相关指标
    LLM_CALL_DURATION = "llm_call_duration"
    LLM_CALL_COUNT = "llm_call_count"
    LLM_TOKEN_USAGE = "llm_token_usage"
    
    # 工具相关指标
    TOOL_EXECUTION_DURATION = "tool_execution_duration"
    TOOL_EXECUTION_COUNT = "tool_execution_count"
    TOOL_SUCCESS_RATE = "tool_success_rate"
    
    # 内存相关指标
    MEMORY_OPERATION_DURATION = "memory_operation_duration"
    MEMORY_OPERATION_COUNT = "memory_operation_count"
    
    # 系统资源指标
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"


# 全局 Topic 设计实例
topic_design = KafkaTopicDesign()


def get_topic_design() -> KafkaTopicDesign:
    """获取全局 Topic 设计实例"""
    return topic_design


if __name__ == "__main__":
    # 生成 Topic 创建脚本
    script = topic_design.create_topic_config_script()
    
    # 确保 scripts 目录存在
    import os
    os.makedirs("scripts", exist_ok=True)
    
    with open("scripts/create_kafka_topics.sh", "w") as f:
        f.write(script)
    
    print("Kafka Topic 设计完成！")
    print("已生成 Topic 创建脚本: scripts/create_kafka_topics.sh")
    
    # 打印 Topic 配置
    print("\nTopic 配置:")
    for topic_type, config in topic_design.get_all_topics().items():
        print(f"- {config['name']}: {config['description']}")
        print(f"  分区数: {config['partitions']}, 副本数: {config['replication_factor']}")
        print(f"  保留时间: {config['retention_ms'] // (24 * 60 * 60 * 1000)} 天")
        print() 