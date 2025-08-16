"""
自定义 Instrumentation 模块

为 JollyAgent 的核心组件提供自定义的监控和追踪功能。
实现任务 1.3: 实现自定义 instrumentation
"""

import time
import logging
import functools
import asyncio
from typing import Dict, Any, Optional, Callable, Union
from contextlib import contextmanager, asynccontextmanager
from dataclasses import dataclass, asdict

from .opentelemetry_integration import get_global_integration
from .data_collector import DataCollector

logger = logging.getLogger(__name__)


@dataclass
class InstrumentationConfig:
    """Instrumentation 配置"""
    enable_agent_tracing: bool = True
    enable_tool_tracing: bool = True
    enable_memory_tracing: bool = True
    enable_llm_tracing: bool = True
    enable_performance_metrics: bool = True
    enable_error_tracking: bool = True
    enable_custom_attributes: bool = True
    trace_sql_queries: bool = False
    trace_http_requests: bool = True
    trace_file_operations: bool = True


class CustomInstrumentation:
    """自定义 Instrumentation 类"""
    
    def __init__(self, config: Optional[InstrumentationConfig] = None):
        self.config = config or InstrumentationConfig()
        self.ot_integration = get_global_integration()
        self.data_collector = DataCollector()
        
        # 性能指标
        self.performance_metrics = {
            "agent_executions": 0,
            "tool_executions": 0,
            "llm_calls": 0,
            "memory_operations": 0,
            "total_errors": 0
        }
        
        logger.info("自定义 Instrumentation 初始化完成")
        
    def instrument_agent_methods(self, agent_instance):
        """为 Agent 实例的方法添加 instrumentation"""
        if not self.config.enable_agent_tracing:
            return
            
        # 将 instrumentation 实例附加到 agent 上
        agent_instance._instrumentation = self
            
        # 包装核心方法
        wrapped_process_message = self._instrument_process_message(
            agent_instance.process_message
        )
        wrapped_process_message._agent_instance = agent_instance
        agent_instance.process_message = wrapped_process_message
        
        wrapped_think = self._instrument_think(agent_instance._think)
        wrapped_think._agent_instance = agent_instance
        agent_instance._think = wrapped_think
        
        wrapped_act = self._instrument_act(agent_instance._act)
        wrapped_act._agent_instance = agent_instance
        agent_instance._act = wrapped_act
        
        wrapped_observe = self._instrument_observe(agent_instance._observe)
        wrapped_observe._agent_instance = agent_instance
        agent_instance._observe = wrapped_observe
        
        wrapped_llm_call = self._instrument_llm_call(agent_instance._call_llm)
        wrapped_llm_call._agent_instance = agent_instance
        agent_instance._call_llm = wrapped_llm_call
        
        logger.info("Agent 方法已添加 instrumentation")
        
    def instrument_tool_executor(self, executor_instance):
        """为工具执行器添加 instrumentation"""
        if not self.config.enable_tool_tracing:
            return
            
        # 包装工具执行方法
        if hasattr(executor_instance, 'execute_tool'):
            executor_instance.execute_tool = self._instrument_tool_execution(
                executor_instance.execute_tool
            )
            
        logger.info("工具执行器已添加 instrumentation")
        
    def instrument_memory_manager(self, memory_instance):
        """为记忆管理器添加 instrumentation"""
        if not self.config.enable_memory_tracing:
            return
            
        # 包装记忆操作方法
        if hasattr(memory_instance, 'add_memory'):
            memory_instance.add_memory = self._instrument_memory_operation(
                memory_instance.add_memory, 'add_memory'
            )
            
        if hasattr(memory_instance, 'search_memory'):
            memory_instance.search_memory = self._instrument_memory_operation(
                memory_instance.search_memory, 'search_memory'
            )
            
        if hasattr(memory_instance, 'end_conversation'):
            memory_instance.end_conversation = self._instrument_memory_operation(
                memory_instance.end_conversation, 'end_conversation'
            )
            
        logger.info("记忆管理器已添加 instrumentation")
        
    def _instrument_process_message(self, original_method):
        """为 process_message 方法添加 instrumentation"""
        instrumentation = self  # 捕获当前的 instrumentation 实例
        
        async def wrapper(user_message: str) -> str:
            # 获取 agent_instance (通过闭包访问)
            agent_instance = wrapper._agent_instance
            
            session_id = getattr(agent_instance.state, 'conversation_id', 'unknown')
            
            # 开始追踪会话
            instrumentation.data_collector.start_session(session_id, {
                "user_message_length": len(user_message),
                "agent_id": id(agent_instance)
            })
            
            start_time = time.time()
            success = True
            error_message = None
            result = None
            
            try:
                with instrumentation._trace_span("agent.process_message", {
                    "session.id": session_id,
                    "user.message.length": len(user_message),
                    "user.message.preview": user_message[:100]
                }):
                    # 调用原始方法
                    result = await original_method(user_message)
                    
            except Exception as e:
                success = False
                error_message = str(e)
                instrumentation.performance_metrics["total_errors"] += 1
                raise
            finally:
                duration = time.time() - start_time
                instrumentation.performance_metrics["agent_executions"] += 1
                
                # 记录事件
                instrumentation.data_collector.record_event(
                    session_id=session_id,
                    event_type="process_message",
                    component="agent",
                    data={
                        "user_message": user_message,
                        "result": result,
                        "duration": duration,
                        "success": success
                    },
                    duration=duration,
                    success=success,
                    error_message=error_message
                )
                
                # 记录指标
                instrumentation._record_execution_metric("agent.process_message", duration, success)
                
            return result
            
        # 保持原始方法的签名信息
        wrapper.__name__ = original_method.__name__
        wrapper.__doc__ = original_method.__doc__
        wrapper.__module__ = original_method.__module__
        
        return wrapper 
        
    def _instrument_think(self, original_method):
        """为 _think 方法添加 instrumentation"""
        async def wrapper(agent_instance, step):
            # 获取 instrumentation 实例
            instrumentation = getattr(agent_instance, '_instrumentation', None)
            if not instrumentation:
                return await original_method(agent_instance, step)
                
            session_id = getattr(agent_instance.state, 'conversation_id', 'unknown')
            start_time = time.time()
            
            try:
                with instrumentation._trace_span("agent.think", {
                    "session.id": session_id,
                    "step.number": len(agent_instance.state.react_steps) + 1
                }):
                    await original_method(agent_instance, step)
                    
                    # 记录思考结果
                    thought_data = {
                        "has_thought": bool(step.thought),
                        "tool_calls_count": len(step.tool_calls),
                        "has_final_answer": bool(step.final_answer)
                    }
                    
                    if step.thought:
                        thought_data["thought_content"] = step.thought.content[:200]
                        
                    if step.tool_calls:
                        thought_data["tool_names"] = [tc.name for tc in step.tool_calls]
                        
            except Exception as e:
                instrumentation.performance_metrics["total_errors"] += 1
                raise
            finally:
                duration = time.time() - start_time
                
                # 记录事件
                instrumentation.data_collector.record_event(
                    session_id=session_id,
                    event_type="think",
                    component="agent",
                    data=thought_data,
                    duration=duration,
                    success=True
                )
                
                # 记录指标
                instrumentation._record_execution_metric("agent.think", duration, True)
                
        # 保持原始方法的签名信息
        wrapper.__name__ = original_method.__name__
        wrapper.__doc__ = original_method.__doc__
        wrapper.__module__ = original_method.__module__
        
        return wrapper 
        
    def _instrument_act(self, original_method):
        """为 _act 方法添加 instrumentation"""
        @functools.wraps(original_method)
        async def wrapper(self, step):
            session_id = getattr(self.state, 'conversation_id', 'unknown')
            start_time = time.time()
            
            try:
                with self._trace_span("agent.act", {
                    "session.id": session_id,
                    "step.number": len(self.state.react_steps) + 1,
                    "tool.calls.count": len(step.tool_calls)
                }):
                    await original_method(step)
                    
                    # 记录执行结果
                    act_data = {
                        "tool_calls_count": len(step.tool_calls),
                        "observations_count": len(step.observations),
                        "successful_tools": sum(1 for obs in step.observations if obs.success),
                        "failed_tools": sum(1 for obs in step.observations if not obs.success)
                    }
                    
            except Exception as e:
                self.performance_metrics["total_errors"] += 1
                raise
            finally:
                duration = time.time() - start_time
                
                # 记录事件
                self.data_collector.record_event(
                    session_id=session_id,
                    event_type="act",
                    component="agent",
                    data=act_data,
                    duration=duration,
                    success=True
                )
                
                # 记录指标
                self._record_execution_metric("agent.act", duration, True)
                
        return wrapper 
        
    def _instrument_observe(self, original_method):
        """为 _observe 方法添加 instrumentation"""
        @functools.wraps(original_method)
        async def wrapper(self, step):
            session_id = getattr(self.state, 'conversation_id', 'unknown')
            start_time = time.time()
            
            try:
                with self._trace_span("agent.observe", {
                    "session.id": session_id,
                    "step.number": len(self.state.react_steps) + 1,
                    "observations.count": len(step.observations)
                }):
                    await original_method(step)
                    
                    # 记录观察结果
                    observe_data = {
                        "observations_count": len(step.observations),
                        "has_final_answer": bool(step.final_answer)
                    }
                    
                    if step.final_answer:
                        observe_data["final_answer_length"] = len(step.final_answer)
                        
            except Exception as e:
                self.performance_metrics["total_errors"] += 1
                raise
            finally:
                duration = time.time() - start_time
                
                # 记录事件
                self.data_collector.record_event(
                    session_id=session_id,
                    event_type="observe",
                    component="agent",
                    data=observe_data,
                    duration=duration,
                    success=True
                )
                
                # 记录指标
                self._record_execution_metric("agent.observe", duration, True)
                
        return wrapper 
        
    def _instrument_llm_call(self, original_method):
        """为 _call_llm 方法添加 instrumentation"""
        @functools.wraps(original_method)
        async def wrapper(self, messages):
            session_id = getattr(self.state, 'conversation_id', 'unknown')
            start_time = time.time()
            
            # 准备 LLM 调用数据
            llm_data = {
                "messages_count": len(messages),
                "total_tokens_estimate": sum(len(msg.get("content", "")) for msg in messages),
                "model": getattr(self.config.llm, 'model', 'unknown')
            }
            
            try:
                with self._trace_span("agent.llm_call", {
                    "session.id": session_id,
                    "llm.messages.count": len(messages),
                    "llm.model": llm_data["model"]
                }):
                    result = await original_method(messages)
                    
                    # 记录 LLM 响应数据
                    llm_data.update({
                        "response_length": len(result.get("content", "")),
                        "usage_tokens": result.get("usage", {}).get("total_tokens", 0),
                        "usage_prompt_tokens": result.get("usage", {}).get("prompt_tokens", 0),
                        "usage_completion_tokens": result.get("usage", {}).get("completion_tokens", 0)
                    })
                    
            except Exception as e:
                self.performance_metrics["total_errors"] += 1
                raise
            finally:
                duration = time.time() - start_time
                self.performance_metrics["llm_calls"] += 1
                
                # 记录事件
                self.data_collector.record_event(
                    session_id=session_id,
                    event_type="llm_call",
                    component="agent",
                    data=llm_data,
                    duration=duration,
                    success=True
                )
                
                # 记录指标
                self._record_execution_metric("agent.llm_call", duration, True)
                
            return result
            
        return wrapper 
        
    def _instrument_tool_execution(self, original_method):
        """为工具执行方法添加 instrumentation"""
        @functools.wraps(original_method)
        async def wrapper(self, tool_name: str, **kwargs):
            start_time = time.time()
            
            # 准备工具执行数据
            tool_data = {
                "tool_name": tool_name,
                "arguments": kwargs,
                "arguments_count": len(kwargs)
            }
            
            try:
                with self._trace_span("tool.execution", {
                    "tool.name": tool_name,
                    "tool.arguments.count": len(kwargs)
                }):
                    result = await original_method(tool_name, **kwargs)
                    
                    # 记录工具执行结果
                    tool_data.update({
                        "success": result.success,
                        "result_length": len(str(result.result)) if result.success else 0,
                        "error_message": result.error if not result.success else None
                    })
                    
            except Exception as e:
                self.performance_metrics["total_errors"] += 1
                raise
            finally:
                duration = time.time() - start_time
                self.performance_metrics["tool_executions"] += 1
                
                # 记录事件
                self.data_collector.record_event(
                    session_id="tool_execution",
                    event_type="tool_execution",
                    component="executor",
                    data=tool_data,
                    duration=duration,
                    success=tool_data.get("success", False)
                )
                
                # 记录指标
                self._record_execution_metric(f"tool.{tool_name}", duration, tool_data.get("success", False))
                
            return result
            
        return wrapper 
        
    def _instrument_memory_operation(self, original_method, operation_name: str):
        """为记忆操作添加 instrumentation"""
        @functools.wraps(original_method)
        async def wrapper(self, *args, **kwargs):
            start_time = time.time()
            
            # 准备记忆操作数据
            memory_data = {
                "operation": operation_name,
                "args_count": len(args),
                "kwargs_count": len(kwargs)
            }
            
            try:
                with self._trace_span("memory.operation", {
                    "memory.operation": operation_name
                }):
                    result = await original_method(*args, **kwargs)
                    
                    # 记录记忆操作结果
                    if operation_name == "add_memory":
                        memory_data["content_length"] = len(args[0]) if args else 0
                    elif operation_name == "search_memory":
                        memory_data["query_length"] = len(args[0]) if args else 0
                        memory_data["results_count"] = len(result) if isinstance(result, list) else 1
                    elif operation_name == "end_conversation":
                        memory_data["summary_length"] = len(result) if result else 0
                        
            except Exception as e:
                self.performance_metrics["total_errors"] += 1
                raise
            finally:
                duration = time.time() - start_time
                self.performance_metrics["memory_operations"] += 1
                
                # 记录事件
                self.data_collector.record_event(
                    session_id="memory_operation",
                    event_type="memory_operation",
                    component="memory",
                    data=memory_data,
                    duration=duration,
                    success=True
                )
                
                # 记录指标
                self._record_execution_metric(f"memory.{operation_name}", duration, True)
                
            return result
            
        return wrapper
        
    @contextmanager
    def _trace_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """创建追踪 span 的上下文管理器"""
        if self.ot_integration and self.ot_integration.is_available():
            with self.ot_integration.trace_execution(name, attributes or {}) as span:
                yield span
        else:
            yield None
            
    def _record_execution_metric(self, name: str, duration: float, success: bool):
        """记录执行指标"""
        if self.ot_integration and self.ot_integration.is_available():
            self.ot_integration.record_execution(name, duration, success)
            
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.performance_metrics.copy()
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "performance_metrics": self.get_performance_metrics(),
            "data_collector_stats": self.data_collector.get_statistics()
        }


# 全局实例
_global_instrumentation: Optional[CustomInstrumentation] = None


def get_global_instrumentation() -> Optional[CustomInstrumentation]:
    """获取全局自定义 instrumentation 实例"""
    return _global_instrumentation


def initialize_global_instrumentation(config: Optional[InstrumentationConfig] = None) -> CustomInstrumentation:
    """初始化全局自定义 instrumentation"""
    global _global_instrumentation
    if _global_instrumentation is None:
        _global_instrumentation = CustomInstrumentation(config)
    return _global_instrumentation


def instrument_agent(agent_instance, config: Optional[InstrumentationConfig] = None):
    """为 Agent 实例添加 instrumentation"""
    instrumentation = get_global_instrumentation() or initialize_global_instrumentation(config)
    instrumentation.instrument_agent_methods(agent_instance)
    return instrumentation


def instrument_executor(executor_instance, config: Optional[InstrumentationConfig] = None):
    """为执行器实例添加 instrumentation"""
    instrumentation = get_global_instrumentation() or initialize_global_instrumentation(config)
    instrumentation.instrument_tool_executor(executor_instance)
    return instrumentation


def instrument_memory(memory_instance, config: Optional[InstrumentationConfig] = None):
    """为记忆管理器实例添加 instrumentation"""
    instrumentation = get_global_instrumentation() or initialize_global_instrumentation(config)
    instrumentation.instrument_memory_manager(memory_instance)
    return instrumentation