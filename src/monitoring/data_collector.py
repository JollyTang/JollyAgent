"""
数据收集器模块

负责收集和管理监控数据，包括 trace、span、metrics 等。
实现任务 1.2: 配置 trace 和 span 收集机制
"""

import time
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from .opentelemetry_integration import get_global_integration

logger = logging.getLogger(__name__)


@dataclass
class ExecutionEvent:
    """执行事件数据结构"""
    event_id: str
    session_id: str
    timestamp: float
    event_type: str  # 'think', 'act', 'observe', 'response'
    component: str
    data: Dict[str, Any]
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DataCollector:
    """数据收集器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.ot_integration = get_global_integration()
        
        logger.info("数据收集器初始化完成")
        
    def start_session(self, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """开始新的执行会话"""
        session = {
            "session_id": session_id,
            "start_time": time.time(),
            "events": [],
            "metadata": metadata or {}
        }
        
        self.sessions[session_id] = session
        
        # 记录到 OpenTelemetry
        if self.ot_integration and self.ot_integration.is_available():
            attributes = {
                "session.id": session_id,
                "session.start_time": session["start_time"]
            }
            if metadata:
                attributes.update(metadata)
                
            with self.ot_integration.trace_execution(
                "session.start",
                attributes=attributes
            ):
                pass
                
        logger.info(f"开始会话: {session_id}")
        return session
        
    def record_event(self, session_id: str, event_type: str, component: str, 
                    data: Dict[str, Any], duration: Optional[float] = None,
                    success: bool = True, error_message: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Optional[ExecutionEvent]:
        """记录执行事件"""
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"会话不存在，无法记录事件: {session_id}")
            return None
            
        event = ExecutionEvent(
            event_id=f"{session_id}_{event_type}_{int(time.time() * 1000)}",
            session_id=session_id,
            timestamp=time.time(),
            event_type=event_type,
            component=component,
            data=data,
            duration=duration,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        session["events"].append(event)
        
        # 记录到 OpenTelemetry
        if self.ot_integration and self.ot_integration.is_available():
            attributes = {
                "session.id": session_id,
                "event.type": event_type,
                "event.component": component,
                "event.success": str(success).lower()
            }
            if metadata:
                attributes.update(metadata)
                
            if duration:
                attributes["event.duration"] = duration
                
            if error_message:
                attributes["event.error"] = error_message
                
            with self.ot_integration.trace_execution(
                f"event.{event_type}",
                attributes=attributes
            ):
                pass
                
            if duration:
                self.ot_integration.record_execution(
                    f"event.{event_type}",
                    duration,
                    success,
                    attributes
                )
                
        logger.debug(f"记录事件: {session_id} - {event_type} - {component}")
        return event
        
    @contextmanager
    def trace_event(self, session_id: str, event_type: str, component: str,
                   data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """追踪事件的上下文管理器"""
        start_time = time.time()
        success = True
        error_message = None
        
        try:
            yield
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            duration = time.time() - start_time
            self.record_event(
                session_id=session_id,
                event_type=event_type,
                component=component,
                data=data,
                duration=duration,
                success=success,
                error_message=error_message,
                metadata=metadata
            )
            
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        return self.sessions.get(session_id)
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_sessions = len(self.sessions)
        total_events = sum(len(s["events"]) for s in self.sessions.values())
        
        event_types = {}
        for session in self.sessions.values():
            for event in session["events"]:
                event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
                
        return {
            "total_sessions": total_sessions,
            "total_events": total_events,
            "event_types": event_types,
            "ot_integration_available": self.ot_integration.is_available() if self.ot_integration else False
        } 

    def end_session(self, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """结束执行会话"""
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"会话不存在: {session_id}")
            return None
            
        session["end_time"] = time.time()
        if metadata:
            session["metadata"].update(metadata)
            
        # 记录到 OpenTelemetry
        if self.ot_integration and self.ot_integration.is_available():
            duration = session["end_time"] - session["start_time"]
            attributes = {
                "session.id": session_id,
                "session.duration": duration,
                "session.event_count": len(session["events"])
            }
            if metadata:
                attributes.update(metadata)
                
            self.ot_integration.record_execution(
                "session.end",
                duration,
                success=True,
                attributes=attributes
            )
            
        logger.info(f"结束会话: {session_id}, 持续时间: {session['end_time'] - session['start_time']:.2f}秒")
        return session 