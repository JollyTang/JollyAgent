"""
数据收集器测试

测试数据收集功能
"""

import unittest
from unittest.mock import patch, MagicMock
import time
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.monitoring.data_collector import DataCollector, ExecutionEvent


class TestDataCollector(unittest.TestCase):
    """测试数据收集器"""
    
    def setUp(self):
        """测试前准备"""
        self.config = {
            "enable_local_storage": False
        }
        self.collector = DataCollector(self.config)
        
    def test_start_session(self):
        """测试开始会话"""
        session_id = "test_session_001"
        metadata = {"user_id": "user123", "task_type": "analysis"}
        
        session = self.collector.start_session(session_id, metadata)
        
        self.assertIsNotNone(session)
        self.assertEqual(session["session_id"], session_id)
        self.assertIn("start_time", session)
        self.assertEqual(session["metadata"], metadata)
        self.assertEqual(session["events"], [])
        
        # 验证会话已存储
        stored_session = self.collector.get_session(session_id)
        self.assertEqual(stored_session, session)
        
    def test_record_event(self):
        """测试记录事件"""
        session_id = "test_session_002"
        self.collector.start_session(session_id)
        
        event_data = {"input": "test input", "output": "test output"}
        event = self.collector.record_event(
            session_id=session_id,
            event_type="think",
            component="reasoning_engine",
            data=event_data,
            duration=1.5,
            success=True,
            metadata={"priority": "high"}
        )
        
        self.assertIsNotNone(event)
        self.assertEqual(event.session_id, session_id)
        self.assertEqual(event.event_type, "think")
        self.assertEqual(event.component, "reasoning_engine")
        self.assertEqual(event.data, event_data)
        self.assertEqual(event.duration, 1.5)
        self.assertTrue(event.success)
        self.assertEqual(event.metadata["priority"], "high")
        
        # 验证事件已添加到会话
        session = self.collector.get_session(session_id)
        self.assertEqual(len(session["events"]), 1)
        self.assertEqual(session["events"][0], event)
        
    def test_record_event_with_error(self):
        """测试记录错误事件"""
        session_id = "test_session_003"
        self.collector.start_session(session_id)
        
        event = self.collector.record_event(
            session_id=session_id,
            event_type="act",
            component="action_executor",
            data={"action": "test_action"},
            duration=0.5,
            success=False,
            error_message="Action failed due to invalid input",
            metadata={"retry_count": 3}
        )
        
        self.assertIsNotNone(event)
        self.assertFalse(event.success)
        self.assertEqual(event.error_message, "Action failed due to invalid input")
        self.assertEqual(event.metadata["retry_count"], 3)
        
    def test_trace_event_context_manager(self):
        """测试事件追踪上下文管理器"""
        session_id = "test_session_004"
        self.collector.start_session(session_id)
        
        event_data = {"operation": "test_operation"}
        
        # 测试正常执行
        with self.collector.trace_event(
            session_id=session_id,
            event_type="observe",
            component="observation_module",
            data=event_data,
            metadata={"level": "info"}
        ):
            time.sleep(0.1)  # 模拟一些工作
            
        # 验证事件被记录
        session = self.collector.get_session(session_id)
        self.assertEqual(len(session["events"]), 1)
        
        event = session["events"][0]
        self.assertEqual(event.event_type, "observe")
        self.assertEqual(event.component, "observation_module")
        self.assertEqual(event.data, event_data)
        self.assertTrue(event.success)
        self.assertIsNotNone(event.duration)
        self.assertEqual(event.metadata["level"], "info")
        
    def test_trace_event_context_manager_with_exception(self):
        """测试事件追踪上下文管理器中的异常处理"""
        session_id = "test_session_005"
        self.collector.start_session(session_id)
        
        # 测试异常情况
        with self.assertRaises(ValueError):
            with self.collector.trace_event(
                session_id=session_id,
                event_type="response",
                component="response_generator",
                data={"response": "test"},
                metadata={"format": "json"}
            ):
                raise ValueError("Test exception")
                
        # 验证错误事件被记录
        session = self.collector.get_session(session_id)
        self.assertEqual(len(session["events"]), 1)
        
        event = session["events"][0]
        self.assertFalse(event.success)
        self.assertEqual(event.error_message, "Test exception")
        
    def test_get_session_nonexistent(self):
        """测试获取不存在的会话"""
        session = self.collector.get_session("nonexistent_session")
        self.assertIsNone(session)
        
    def test_record_event_nonexistent_session(self):
        """测试为不存在的会话记录事件"""
        event = self.collector.record_event(
            session_id="nonexistent_session",
            event_type="think",
            component="test",
            data={}
        )
        self.assertIsNone(event)
        
    def test_get_statistics(self):
        """测试获取统计信息"""
        # 创建一些测试数据
        session1 = self.collector.start_session("session_001")
        session2 = self.collector.start_session("session_002")
        
        self.collector.record_event("session_001", "think", "component1", {"data": "test1"})
        self.collector.record_event("session_001", "act", "component1", {"data": "test2"})
        self.collector.record_event("session_002", "observe", "component2", {"data": "test3"})
        
        stats = self.collector.get_statistics()
        
        self.assertEqual(stats["total_sessions"], 2)
        self.assertEqual(stats["total_events"], 3)
        self.assertEqual(stats["event_types"]["think"], 1)
        self.assertEqual(stats["event_types"]["act"], 1)
        self.assertEqual(stats["event_types"]["observe"], 1)
        self.assertIn("ot_integration_available", stats)


if __name__ == '__main__':
    unittest.main() 