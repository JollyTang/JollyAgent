"""
执行步骤追踪器

专门用于追踪 Think-Act-Observe-Response 循环的执行步骤。
实现任务 1.4: 实现执行步骤追踪（Think-Act-Observe-Response）
"""

import time
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from .opentelemetry_integration import get_global_integration

logger = logging.getLogger(__name__)


class StepType(Enum):
    """执行步骤类型"""
    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"
    RESPONSE = "response"


class StepStatus(Enum):
    """步骤状态"""
    STARTED = "started"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepData:
    """步骤数据"""
    step_id: str
    step_type: StepType
    step_number: int
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    status: StepStatus = StepStatus.STARTED
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ReActCycle:
    """ReAct 循环数据"""
    cycle_id: str
    session_id: str
    cycle_number: int
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    steps: List[StepData] = None
    user_message: Optional[str] = None
    final_response: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []


class StepTracker:
    """执行步骤追踪器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.ot_integration = get_global_integration()
        self.active_cycles: Dict[str, ReActCycle] = {}
        self.completed_cycles: List[ReActCycle] = []
        
        logger.info("执行步骤追踪器初始化完成")
        
    def start_cycle(self, session_id: str, cycle_number: int, user_message: Optional[str] = None) -> str:
        """开始一个新的 ReAct 循环"""
        cycle_id = f"{session_id}_cycle_{cycle_number}_{int(time.time() * 1000)}"
        
        cycle = ReActCycle(
            cycle_id=cycle_id,
            session_id=session_id,
            cycle_number=cycle_number,
            start_time=time.time(),
            user_message=user_message,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "cycle_id": cycle_id
            }
        )
        
        self.active_cycles[session_id] = cycle
        
        # 记录到 OpenTelemetry
        if self.ot_integration and self.ot_integration.is_available():
            with self.ot_integration.trace_execution("react_cycle.start", {
                "cycle.id": cycle_id,
                "session.id": session_id,
                "cycle.number": cycle_number,
                "user.message.length": len(user_message) if user_message else 0
            }):
                pass
                
        logger.info(f"开始 ReAct 循环: {cycle_id}")
        return cycle_id
        
    def end_cycle(self, session_id: str, final_response: Optional[str] = None, 
                  success: bool = True, error_message: Optional[str] = None) -> Optional[ReActCycle]:
        """结束当前的 ReAct 循环"""
        cycle = self.active_cycles.get(session_id)
        if not cycle:
            logger.warning(f"没有找到活跃的循环: {session_id}")
            return None
            
        cycle.end_time = time.time()
        cycle.duration = cycle.end_time - cycle.start_time
        cycle.final_response = final_response
        cycle.success = success
        cycle.error_message = error_message
        
        # 更新元数据
        if cycle.metadata is None:
            cycle.metadata = {}
        cycle.metadata.update({
            "end_timestamp": datetime.now().isoformat(),
            "total_steps": len(cycle.steps),
            "success": success
        })
        
        # 记录到 OpenTelemetry
        if self.ot_integration and self.ot_integration.is_available():
            self.ot_integration.record_execution(
                "react_cycle.end",
                cycle.duration,
                success,
                {
                    "cycle.id": cycle.cycle_id,
                    "session.id": session_id,
                    "cycle.number": cycle.cycle_number,
                    "total.steps": len(cycle.steps),
                    "final.response.length": len(final_response) if final_response else 0
                }
            )
            
        # 移动到已完成列表
        self.completed_cycles.append(cycle)
        del self.active_cycles[session_id]
        
        logger.info(f"结束 ReAct 循环: {cycle.cycle_id}, 持续时间: {cycle.duration:.3f}秒")
        return cycle
        
    def start_step(self, session_id: str, step_type: StepType, 
                   input_data: Optional[Dict[str, Any]] = None) -> str:
        """开始一个新的执行步骤"""
        cycle = self.active_cycles.get(session_id)
        if not cycle:
            logger.warning(f"没有找到活跃的循环: {session_id}")
            return ""
            
        step_number = len(cycle.steps) + 1
        step_id = f"{cycle.cycle_id}_step_{step_number}_{step_type.value}"
        
        step = StepData(
            step_id=step_id,
            step_type=step_type,
            step_number=step_number,
            session_id=session_id,
            start_time=time.time(),
            input_data=input_data,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "step_id": step_id
            }
        )
        
        cycle.steps.append(step)
        
        # 记录到 OpenTelemetry
        if self.ot_integration and self.ot_integration.is_available():
            with self.ot_integration.trace_execution(f"react_step.{step_type.value}.start", {
                "step.id": step_id,
                "cycle.id": cycle.cycle_id,
                "session.id": session_id,
                "step.number": step_number,
                "step.type": step_type.value
            }):
                pass
                
        logger.debug(f"开始步骤: {step_id} ({step_type.value})")
        return step_id
        
    def end_step(self, session_id: str, step_id: str, 
                 output_data: Optional[Dict[str, Any]] = None,
                 status: StepStatus = StepStatus.SUCCESS,
                 error_message: Optional[str] = None) -> Optional[StepData]:
        """结束一个执行步骤"""
        cycle = self.active_cycles.get(session_id)
        if not cycle:
            logger.warning(f"没有找到活跃的循环: {session_id}")
            return None
            
        # 查找步骤
        step = None
        for s in cycle.steps:
            if s.step_id == step_id:
                step = s
                break
                
        if not step:
            logger.warning(f"没有找到步骤: {step_id}")
            return None
            
        step.end_time = time.time()
        step.duration = step.end_time - step.start_time
        step.output_data = output_data
        step.status = status
        step.error_message = error_message
        
        # 更新元数据
        if step.metadata is None:
            step.metadata = {}
        step.metadata.update({
            "end_timestamp": datetime.now().isoformat(),
            "status": status.value
        })
        
        # 记录到 OpenTelemetry
        if self.ot_integration and self.ot_integration.is_available():
            self.ot_integration.record_execution(
                f"react_step.{step.step_type.value}.end",
                step.duration,
                status == StepStatus.SUCCESS,
                {
                    "step.id": step_id,
                    "cycle.id": cycle.cycle_id,
                    "session.id": session_id,
                    "step.number": step.step_number,
                    "step.type": step.step_type.value,
                    "step.status": status.value
                }
            )
            
        logger.debug(f"结束步骤: {step_id} ({step.step_type.value}), 状态: {status.value}")
        return step
        
    def get_current_cycle(self, session_id: str) -> Optional[ReActCycle]:
        """获取当前活跃的循环"""
        return self.active_cycles.get(session_id)
        
    def get_cycle_history(self, session_id: str) -> List[ReActCycle]:
        """获取会话的循环历史"""
        return [cycle for cycle in self.completed_cycles if cycle.session_id == session_id]
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_cycles = len(self.completed_cycles)
        active_cycles = len(self.active_cycles)
        
        step_counts = {}
        total_duration = 0
        success_count = 0
        
        for cycle in self.completed_cycles:
            total_duration += cycle.duration or 0
            if cycle.success:
                success_count += 1
                
            for step in cycle.steps:
                step_type = step.step_type.value
                step_counts[step_type] = step_counts.get(step_type, 0) + 1
                
        return {
            "total_cycles": total_cycles,
            "active_cycles": active_cycles,
            "success_rate": success_count / total_cycles if total_cycles > 0 else 0,
            "average_duration": total_duration / total_cycles if total_cycles > 0 else 0,
            "step_counts": step_counts,
            "ot_integration_available": self.ot_integration.is_available() if self.ot_integration else False
        }
        
    def export_data(self, filepath: str) -> bool:
        """导出追踪数据到文件"""
        try:
            data = {
                "completed_cycles": [asdict(cycle) for cycle in self.completed_cycles],
                "statistics": self.get_statistics(),
                "export_timestamp": datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                
            logger.info(f"追踪数据已导出到: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"导出追踪数据失败: {e}")
            return False


# 全局实例
_global_step_tracker: Optional[StepTracker] = None


def get_global_step_tracker() -> Optional[StepTracker]:
    """获取全局执行步骤追踪器实例"""
    return _global_step_tracker


def initialize_global_step_tracker(config: Optional[Dict[str, Any]] = None) -> StepTracker:
    """初始化全局执行步骤追踪器"""
    global _global_step_tracker
    if _global_step_tracker is None:
        _global_step_tracker = StepTracker(config)
    return _global_step_tracker 