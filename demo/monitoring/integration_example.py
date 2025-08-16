"""
监控集成示例

展示如何在 JollyAgent 核心代码中集成监控功能
"""

import time
import logging
from typing import Dict, Any, Optional
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.monitoring.opentelemetry_integration import initialize_global_integration, get_global_integration
from src.monitoring.data_collector import DataCollector

logger = logging.getLogger(__name__)


class MonitoredAgent:
    """
    带监控功能的 Agent 示例
    
    展示如何在 Agent 核心代码中集成监控功能
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化带监控的 Agent
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 初始化 OpenTelemetry 集成
        self.ot_integration = initialize_global_integration(self.config.get("opentelemetry", {}))
        
        # 初始化数据收集器
        self.data_collector = DataCollector(self.config.get("data_collector", {}))
        
        logger.info("MonitoredAgent 初始化完成")
        
    def execute_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务（带监控）
        
        Args:
            task_id: 任务ID
            task_data: 任务数据
            
        Returns:
            执行结果
        """
        session_id = f"task_{task_id}_{int(time.time())}"
        
        # 开始会话
        session = self.data_collector.start_session(session_id, {
            "task_id": task_id,
            "task_type": task_data.get("type", "unknown")
        })
        
        try:
            # 执行 Think 阶段
            with self.data_collector.trace_event(
                session_id=session_id,
                event_type="think",
                component="reasoning_engine",
                data={"input": task_data.get("input", "")},
                metadata={"phase": "analysis"}
            ):
                thought_result = self._think_phase(task_data)
                
            # 执行 Act 阶段
            with self.data_collector.trace_event(
                session_id=session_id,
                event_type="act",
                component="action_executor",
                data={"action": thought_result.get("action", "")},
                metadata={"phase": "execution"}
            ):
                action_result = self._act_phase(thought_result)
                
            # 执行 Observe 阶段
            with self.data_collector.trace_event(
                session_id=session_id,
                event_type="observe",
                component="observation_module",
                data={"observation": action_result.get("result", "")},
                metadata={"phase": "evaluation"}
            ):
                observation_result = self._observe_phase(action_result)
                
            # 执行 Response 阶段
            with self.data_collector.trace_event(
                session_id=session_id,
                event_type="response",
                component="response_generator",
                data={"response": observation_result.get("response", "")},
                metadata={"phase": "synthesis"}
            ):
                final_response = self._response_phase(observation_result)
                
            # 记录成功完成
            self.data_collector.record_event(
                session_id=session_id,
                event_type="completion",
                component="task_manager",
                data={"status": "success", "result": final_response},
                success=True,
                metadata={"total_phases": 4}
            )
            
            return final_response
            
        except Exception as e:
            # 记录错误
            self.data_collector.record_event(
                session_id=session_id,
                event_type="error",
                component="task_manager",
                data={"error": str(e)},
                success=False,
                error_message=str(e),
                metadata={"error_type": type(e).__name__}
            )
            raise
            
        finally:
            # 结束会话
            self.data_collector.end_session(session_id, {
                "completion_time": time.time(),
                "status": "completed"
            })
            
    def _think_phase(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """思考阶段"""
        # 模拟思考过程
        time.sleep(0.1)
        return {
            "action": "process_data",
            "reasoning": "Analyzing input data",
            "confidence": 0.85
        }
        
    def _act_phase(self, thought_result: Dict[str, Any]) -> Dict[str, Any]:
        """行动阶段"""
        # 模拟执行动作
        time.sleep(0.2)
        return {
            "result": "Data processed successfully",
            "action": thought_result.get("action"),
            "execution_time": 0.2
        }
        
    def _observe_phase(self, action_result: Dict[str, Any]) -> Dict[str, Any]:
        """观察阶段"""
        # 模拟观察结果
        time.sleep(0.05)
        return {
            "response": "Observation completed",
            "observation": action_result.get("result"),
            "quality_score": 0.9
        }
        
    def _response_phase(self, observation_result: Dict[str, Any]) -> Dict[str, Any]:
        """响应阶段"""
        # 模拟生成响应
        time.sleep(0.1)
        return {
            "final_response": f"Task completed: {observation_result.get('response')}",
            "summary": "All phases executed successfully",
            "timestamp": time.time()
        }
        
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """获取监控统计信息"""
        return {
            "opentelemetry": {
                "available": self.ot_integration.is_available() if self.ot_integration else False
            },
            "data_collector": self.data_collector.get_statistics()
        }
        
    def shutdown(self):
        """关闭监控"""
        if self.ot_integration:
            self.ot_integration.shutdown()


def example_usage():
    """使用示例"""
    # 配置
    config = {
        "opentelemetry": {
            "enable_console_export": True
        },
        "data_collector": {
            "enable_local_storage": True,
            "local_storage_path": "data/monitoring"
        }
    }
    
    # 创建带监控的 Agent
    agent = MonitoredAgent(config)
    
    # 执行任务
    task_data = {
        "type": "data_analysis",
        "input": "Analyze user behavior data",
        "parameters": {"time_range": "last_7_days"}
    }
    
    try:
        result = agent.execute_task("task_001", task_data)
        print(f"任务执行结果: {result}")
        
        # 获取监控统计
        stats = agent.get_monitoring_stats()
        print(f"监控统计: {stats}")
        
    except Exception as e:
        print(f"任务执行失败: {e}")
        
    finally:
        agent.shutdown()


if __name__ == "__main__":
    example_usage() 