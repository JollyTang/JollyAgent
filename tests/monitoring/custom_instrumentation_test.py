"""
自定义 Instrumentation 测试模块

测试自定义 instrumentation 的基本功能。
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from src.monitoring.custom_instrumentation import (
    CustomInstrumentation, 
    InstrumentationConfig,
    instrument_agent
)


class MockAgent:
    """模拟 Agent 类"""
    
    def __init__(self):
        self.state = Mock()
        self.state.conversation_id = "test_session_123"
        self.state.react_steps = []
        self.config = Mock()
        self.config.llm = Mock()
        self.config.llm.model = "gpt-3.5-turbo"
        
    async def process_message(self, user_message: str) -> str:
        """模拟处理消息"""
        await asyncio.sleep(0.1)
        return f"处理结果: {user_message}"


@pytest.fixture
def instrumentation_config():
    """创建测试配置"""
    return InstrumentationConfig(
        enable_agent_tracing=True,
        enable_tool_tracing=True,
        enable_memory_tracing=True,
        enable_llm_tracing=True
    )


class TestCustomInstrumentation:
    """测试自定义 Instrumentation 类"""
    
    def test_initialization(self, instrumentation_config):
        """测试初始化"""
        instrumentation = CustomInstrumentation(instrumentation_config)
        
        assert instrumentation.config == instrumentation_config
        assert instrumentation.performance_metrics["agent_executions"] == 0
        assert instrumentation.performance_metrics["tool_executions"] == 0
        
    def test_instrument_agent_methods(self, instrumentation_config):
        """测试为 Agent 方法添加 instrumentation"""
        with patch('src.monitoring.custom_instrumentation.get_global_integration') as mock:
            mock_integration = Mock()
            mock_integration.is_available.return_value = True
            mock_integration.trace_execution.return_value.__enter__ = Mock()
            mock_integration.trace_execution.return_value.__exit__ = Mock()
            mock.return_value = mock_integration
            
            instrumentation = CustomInstrumentation(instrumentation_config)
            agent = MockAgent()
            
            # 添加 instrumentation
            instrumentation.instrument_agent_methods(agent)
            
            # 验证方法已被包装
            assert hasattr(agent.process_message, '__wrapped__')
            
    @pytest.mark.asyncio
    async def test_process_message_instrumentation(self, instrumentation_config):
        """测试 process_message 的 instrumentation"""
        with patch('src.monitoring.custom_instrumentation.get_global_integration') as mock:
            mock_integration = Mock()
            mock_integration.is_available.return_value = True
            mock_integration.trace_execution.return_value.__enter__ = Mock()
            mock_integration.trace_execution.return_value.__exit__ = Mock()
            mock_integration.record_execution = Mock()
            mock.return_value = mock_integration
            
            instrumentation = CustomInstrumentation(instrumentation_config)
            agent = MockAgent()
            
            # 添加 instrumentation
            instrumentation.instrument_agent_methods(agent)
            
            # 执行方法
            result = await agent.process_message("测试消息")
            
            # 验证结果
            assert result == "处理结果: 测试消息"
            assert instrumentation.performance_metrics["agent_executions"] == 1
            assert instrumentation.performance_metrics["total_errors"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 