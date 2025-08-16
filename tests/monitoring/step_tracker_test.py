"""
执行步骤追踪器测试模块

测试执行步骤追踪（Think-Act-Observe-Response）功能。
"""

import pytest
import asyncio
import json
import tempfile
from unittest.mock import Mock, patch

from src.monitoring.step_tracker import (
    StepTracker, 
    StepType, 
    StepStatus, 
    ReActCycle, 
    StepData,
    get_global_step_tracker,
    initialize_global_step_tracker
)


class TestStepTracker:
    """测试执行步骤追踪器"""
    
    def test_initialization(self):
        """测试初始化"""
        tracker = StepTracker()
        assert tracker.active_cycles == {}
        assert tracker.completed_cycles == []
        
    def test_start_cycle(self):
        """测试开始循环"""
        tracker = StepTracker()
        session_id = "test_session"
        cycle_number = 1
        user_message = "测试消息"
        
        cycle_id = tracker.start_cycle(session_id, cycle_number, user_message)
        
        assert cycle_id is not None
        assert session_id in tracker.active_cycles
        cycle = tracker.active_cycles[session_id]
        assert cycle.session_id == session_id
        assert cycle.cycle_number == cycle_number
        assert cycle.user_message == user_message
        assert cycle.steps == []
        
    def test_end_cycle(self):
        """测试结束循环"""
        tracker = StepTracker()
        session_id = "test_session"
        cycle_number = 1
        
        # 开始循环
        cycle_id = tracker.start_cycle(session_id, cycle_number, "测试消息")
        
        # 结束循环
        final_response = "最终响应"
        completed_cycle = tracker.end_cycle(session_id, final_response, True)
        
        assert completed_cycle is not None
        assert completed_cycle.final_response == final_response
        assert completed_cycle.success is True
        assert session_id not in tracker.active_cycles
        assert len(tracker.completed_cycles) == 1
        
    def test_start_and_end_step(self):
        """测试开始和结束步骤"""
        tracker = StepTracker()
        session_id = "test_session"
        
        # 开始循环
        tracker.start_cycle(session_id, 1, "测试消息")
        
        # 开始步骤
        step_id = tracker.start_step(session_id, StepType.THINK, {"input": "test"})
        assert step_id is not None
        
        # 获取当前循环
        cycle = tracker.get_current_cycle(session_id)
        assert len(cycle.steps) == 1
        step = cycle.steps[0]
        assert step.step_type == StepType.THINK
        assert step.input_data == {"input": "test"}
        
        # 结束步骤
        completed_step = tracker.end_step(session_id, step_id, {"output": "result"}, StepStatus.SUCCESS)
        assert completed_step is not None
        assert completed_step.output_data == {"output": "result"}
        assert completed_step.status == StepStatus.SUCCESS
        
    def test_get_statistics(self):
        """测试获取统计信息"""
        tracker = StepTracker()
        session_id = "test_session"
        
        # 创建一些测试数据
        tracker.start_cycle(session_id, 1, "消息1")
        step_id1 = tracker.start_step(session_id, StepType.THINK)
        tracker.end_step(session_id, step_id1, {}, StepStatus.SUCCESS)
        tracker.end_cycle(session_id, "响应1", True)
        
        tracker.start_cycle(session_id, 2, "消息2")
        step_id2 = tracker.start_step(session_id, StepType.ACT)
        tracker.end_step(session_id, step_id2, {}, StepStatus.FAILED)
        tracker.end_cycle(session_id, "响应2", False)
        
        stats = tracker.get_statistics()
        
        assert stats["total_cycles"] == 2
        assert stats["active_cycles"] == 0
        assert stats["success_rate"] == 0.5
        assert "think" in stats["step_counts"]
        assert "act" in stats["step_counts"]
        
    def test_export_data(self):
        """测试导出数据"""
        tracker = StepTracker()
        session_id = "test_session"
        
        # 创建测试数据
        tracker.start_cycle(session_id, 1, "测试消息")
        step_id = tracker.start_step(session_id, StepType.THINK)
        tracker.end_step(session_id, step_id, {"result": "success"}, StepStatus.SUCCESS)
        tracker.end_cycle(session_id, "最终响应", True)
        
        # 导出数据
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name
            
        try:
            success = tracker.export_data(export_path)
            assert success is True
            
            # 验证导出的数据
            with open(export_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            assert "completed_cycles" in data
            assert "statistics" in data
            assert "export_timestamp" in data
            assert len(data["completed_cycles"]) == 1
            
        finally:
            import os
            os.unlink(export_path)
            
    def test_get_cycle_history(self):
        """测试获取循环历史"""
        tracker = StepTracker()
        session_id = "test_session"
        
        # 创建多个循环
        tracker.start_cycle(session_id, 1, "消息1")
        tracker.end_cycle(session_id, "响应1", True)
        
        tracker.start_cycle(session_id, 2, "消息2")
        tracker.end_cycle(session_id, "响应2", True)
        
        # 测试另一个会话
        other_session = "other_session"
        tracker.start_cycle(other_session, 1, "其他消息")
        tracker.end_cycle(other_session, "其他响应", True)
        
        # 获取历史
        history = tracker.get_cycle_history(session_id)
        assert len(history) == 2
        
        other_history = tracker.get_cycle_history(other_session)
        assert len(other_history) == 1


class TestGlobalFunctions:
    """测试全局函数"""
    
    def test_global_step_tracker(self):
        """测试全局步骤追踪器"""
        # 初始化全局追踪器
        tracker = initialize_global_step_tracker()
        assert tracker is not None
        
        # 获取全局追踪器
        global_tracker = get_global_step_tracker()
        assert global_tracker is tracker
        
    def test_multiple_initialization(self):
        """测试多次初始化"""
        # 第一次初始化
        tracker1 = initialize_global_step_tracker()
        
        # 第二次初始化应该返回同一个实例
        tracker2 = initialize_global_step_tracker()
        assert tracker1 is tracker2


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 