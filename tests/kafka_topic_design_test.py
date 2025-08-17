"""
Kafka Topic 设计测试

测试 Kafka Topic 结构设计的各种功能。

Author: JollyAgent Team
Date: 2025-08-17
"""

import unittest
import json
import sys
import os
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data_pipeline.kafka_topic_design import (
    TopicType, ExecutionStatus, StepType, EventType,
    ExecutionRecord, MetricRecord, EventRecord,
    KafkaTopicDesign, MetricNames, get_topic_design
)


class TestKafkaTopicDesign(unittest.TestCase):
    """Kafka Topic 设计测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.topic_design = KafkaTopicDesign()
    
    def test_topic_configs(self):
        """测试 Topic 配置"""
        # 测试所有 Topic 配置
        all_topics = self.topic_design.get_all_topics()
        self.assertEqual(len(all_topics), 3)
        
        # 测试 executions topic
        executions_config = self.topic_design.get_topic_config(TopicType.EXECUTIONS)
        self.assertEqual(executions_config["name"], "jollyagent.executions")
        self.assertEqual(executions_config["partitions"], 3)
        self.assertEqual(executions_config["replication_factor"], 2)
        
        # 测试 metrics topic
        metrics_config = self.topic_design.get_topic_config(TopicType.METRICS)
        self.assertEqual(metrics_config["name"], "jollyagent.metrics")
        self.assertEqual(metrics_config["partitions"], 5)
        
        # 测试 events topic
        events_config = self.topic_design.get_topic_config(TopicType.EVENTS)
        self.assertEqual(events_config["name"], "jollyagent.events")
        self.assertEqual(events_config["partitions"], 3)
    
    def test_execution_record(self):
        """测试执行记录数据结构"""
        record = ExecutionRecord(
            execution_id="test_exec_001",
            session_id="test_session_001",
            agent_id="test_agent_001",
            user_message="请帮我计算 2 + 3",
            start_time=datetime.now().timestamp(),
            status=ExecutionStatus.SUCCESS,
            final_response="2 + 3 = 5",
            metadata={"test": "data"}
        )
        
        # 测试转换为字典
        record_dict = record.to_dict()
        self.assertEqual(record_dict["execution_id"], "test_exec_001")
        self.assertEqual(record_dict["session_id"], "test_session_001")
        self.assertEqual(record_dict["status"], "success")
        self.assertEqual(record_dict["final_response"], "2 + 3 = 5")
        
        # 测试转换为 JSON
        record_json = record.to_json()
        parsed_json = json.loads(record_json)
        self.assertEqual(parsed_json["execution_id"], "test_exec_001")
    
    def test_metric_record(self):
        """测试指标记录数据结构"""
        record = MetricRecord(
            metric_id="test_metric_001",
            metric_name=MetricNames.EXECUTION_DURATION,
            metric_type="histogram",
            value=1.5,
            unit="seconds",
            labels={"session_id": "test_session_001", "agent_id": "test_agent_001"}
        )
        
        # 测试转换为字典
        record_dict = record.to_dict()
        self.assertEqual(record_dict["metric_name"], "execution_duration")
        self.assertEqual(record_dict["value"], 1.5)
        self.assertEqual(record_dict["unit"], "seconds")
        self.assertEqual(record_dict["labels"]["session_id"], "test_session_001")
        
        # 测试转换为 JSON
        record_json = record.to_json()
        parsed_json = json.loads(record_json)
        self.assertEqual(parsed_json["metric_name"], "execution_duration")
    
    def test_event_record(self):
        """测试事件记录数据结构"""
        record = EventRecord(
            event_id="test_event_001",
            event_type=EventType.AGENT_START,
            session_id="test_session_001",
            execution_id="test_exec_001",
            event_data={"user_message": "请帮我计算 2 + 3"},
            severity="info"
        )
        
        # 测试转换为字典
        record_dict = record.to_dict()
        self.assertEqual(record_dict["event_type"], "agent_start")
        self.assertEqual(record_dict["session_id"], "test_session_001")
        self.assertEqual(record_dict["severity"], "info")
        self.assertEqual(record_dict["event_data"]["user_message"], "请帮我计算 2 + 3")
        
        # 测试转换为 JSON
        record_json = record.to_json()
        parsed_json = json.loads(record_json)
        self.assertEqual(parsed_json["event_type"], "agent_start")
    
    def test_topic_creation_script(self):
        """测试 Topic 创建脚本生成"""
        script = self.topic_design.create_topic_config_script()
        
        # 验证脚本包含必要的命令
        self.assertIn("kafka-topics.sh --create", script)
        self.assertIn("jollyagent.executions", script)
        self.assertIn("jollyagent.metrics", script)
        self.assertIn("jollyagent.events", script)
        self.assertIn("--partitions", script)
        self.assertIn("--replication-factor", script)
    
    def test_metric_names(self):
        """测试预定义的指标名称"""
        # 测试执行相关指标
        self.assertEqual(MetricNames.EXECUTION_DURATION, "execution_duration")
        self.assertEqual(MetricNames.EXECUTION_SUCCESS_RATE, "execution_success_rate")
        self.assertEqual(MetricNames.EXECUTION_COUNT, "execution_count")
        
        # 测试步骤相关指标
        self.assertEqual(MetricNames.STEP_DURATION, "step_duration")
        self.assertEqual(MetricNames.STEP_COUNT, "step_count")
        
        # 测试 LLM 相关指标
        self.assertEqual(MetricNames.LLM_CALL_DURATION, "llm_call_duration")
        self.assertEqual(MetricNames.LLM_TOKEN_USAGE, "llm_token_usage")
        
        # 测试工具相关指标
        self.assertEqual(MetricNames.TOOL_EXECUTION_DURATION, "tool_execution_duration")
        self.assertEqual(MetricNames.TOOL_SUCCESS_RATE, "tool_success_rate")
    
    def test_global_topic_design(self):
        """测试全局 Topic 设计实例"""
        global_design = get_topic_design()
        self.assertIsInstance(global_design, KafkaTopicDesign)
        
        # 验证全局实例的配置
        executions_config = global_design.get_topic_config(TopicType.EXECUTIONS)
        self.assertEqual(executions_config["name"], "jollyagent.executions")


class TestDataStructures(unittest.TestCase):
    """数据结构测试类"""
    
    def test_enum_values(self):
        """测试枚举值"""
        # 测试 TopicType
        self.assertEqual(TopicType.EXECUTIONS.value, "executions")
        self.assertEqual(TopicType.METRICS.value, "metrics")
        self.assertEqual(TopicType.EVENTS.value, "events")
        
        # 测试 ExecutionStatus
        self.assertEqual(ExecutionStatus.STARTED.value, "started")
        self.assertEqual(ExecutionStatus.SUCCESS.value, "success")
        self.assertEqual(ExecutionStatus.FAILED.value, "failed")
        
        # 测试 StepType
        self.assertEqual(StepType.THINK.value, "think")
        self.assertEqual(StepType.ACT.value, "act")
        self.assertEqual(StepType.OBSERVE.value, "observe")
        self.assertEqual(StepType.RESPONSE.value, "response")
        
        # 测试 EventType
        self.assertEqual(EventType.AGENT_START.value, "agent_start")
        self.assertEqual(EventType.AGENT_END.value, "agent_end")
        self.assertEqual(EventType.ERROR.value, "error")
    
    def test_record_serialization(self):
        """测试记录序列化"""
        # 测试执行记录序列化
        execution = ExecutionRecord(
            execution_id="test_001",
            session_id="session_001",
            agent_id="agent_001",
            user_message="test message",
            start_time=1234567890.0
        )
        
        # 序列化
        execution_dict = execution.to_dict()
        execution_json = execution.to_json()
        
        # 反序列化
        execution_parsed = json.loads(execution_json)
        
        # 验证
        self.assertEqual(execution_dict["execution_id"], "test_001")
        self.assertEqual(execution_parsed["execution_id"], "test_001")
        self.assertEqual(execution_dict["start_time"], 1234567890.0)
        self.assertEqual(execution_parsed["start_time"], 1234567890.0)


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2) 