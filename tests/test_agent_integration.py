"""Agent集成测试."""

import asyncio
import pytest
from unittest.mock import patch, MagicMock

from src.agent import Agent, get_agent, reset_agent
from src.executor import get_executor, reset_executor


class TestAgentIntegration:
    """Agent集成测试."""
    
    def setup_method(self):
        """设置测试环境."""
        reset_agent()
        reset_executor()
    
    def teardown_method(self):
        """清理测试环境."""
        reset_agent()
        reset_executor()
    
    def test_agent_initialization(self):
        """测试Agent初始化."""
        agent = Agent()
        
        assert agent is not None
        assert agent.state is None
        
        # 检查工具是否已注册
        executor = get_executor()
        tools = executor.list_tools()
        assert "run_shell" in tools
        assert "read_file" in tools
        assert "write_file" in tools
    
    def test_agent_singleton(self):
        """测试Agent单例模式."""
        agent1 = get_agent()
        agent2 = get_agent()
        
        assert agent1 is agent2
    
    def test_start_conversation(self):
        """测试开始对话."""
        agent = Agent()
        state = agent.start_conversation("test_conversation")
        
        assert state.conversation_id == "test_conversation"
        assert len(state.messages) == 0
        assert state.is_completed is False
    
    def test_add_message(self):
        """测试添加消息."""
        agent = Agent()
        agent.start_conversation("test_conversation")
        
        message = agent.add_message("user", "Hello, Agent!")
        
        assert message.role == "user"
        assert message.content == "Hello, Agent!"
        assert len(agent.state.messages) == 1
    
    @pytest.mark.asyncio
    async def test_process_message_with_mock_llm(self):
        """测试使用模拟LLM处理消息."""
        agent = Agent()
        agent.start_conversation("test_conversation")
        
        # 模拟LLM响应
        mock_response = {
            "content": '{"thought": "我需要读取一个文件", "tool_calls": [{"name": "read_file", "arguments": {"file_path": "test.txt"}}], "final_answer": null}',
            "usage": {"total_tokens": 100}
        }
        
        with patch.object(agent, '_call_llm', return_value=mock_response):
            result = await agent.process_message("请读取test.txt文件")
            
            # 验证ReAct步骤
            assert len(agent.state.react_steps) > 0
            assert agent.state.is_completed is True
    
    @pytest.mark.asyncio
    async def test_process_message_with_final_answer(self):
        """测试直接返回最终答案的消息处理."""
        agent = Agent()
        agent.start_conversation("test_conversation")
        
        # 模拟LLM直接返回最终答案
        mock_response = {
            "content": '{"thought": "这是一个简单的问题", "tool_calls": [], "final_answer": "这是最终答案"}',
            "usage": {"total_tokens": 50}
        }
        
        with patch.object(agent, '_call_llm', return_value=mock_response):
            result = await agent.process_message("你好")
            
            assert "这是最终答案" in result
            assert agent.state.is_completed is True
    
    def test_build_system_prompt(self):
        """测试系统提示词构建."""
        agent = Agent()
        prompt = agent._build_system_prompt()
        
        # 检查是否包含工具信息
        assert "run_shell" in prompt
        assert "read_file" in prompt
        assert "write_file" in prompt
        assert "工具调用格式" in prompt
    
    def test_parse_llm_response_json(self):
        """测试JSON格式的LLM响应解析."""
        agent = Agent()
        
        json_response = '{"thought": "测试思考", "tool_calls": [{"name": "read_file", "arguments": {"file_path": "test.txt"}}], "final_answer": "测试答案"}'
        
        step = agent._parse_llm_response(json_response)
        
        assert step.thought is not None
        assert step.thought.content == "测试思考"
        assert len(step.tool_calls) == 1
        assert step.tool_calls[0].name == "read_file"
        assert step.final_answer == "测试答案"
    
    def test_parse_llm_response_text(self):
        """测试文本格式的LLM响应解析."""
        agent = Agent()
        
        text_response = """Thought: 这是一个测试思考
Action: run_shell echo "hello"
Answer: 这是最终答案"""
        
        step = agent._parse_llm_response(text_response)
        
        assert step.thought is not None
        assert "测试思考" in step.thought.content
        assert step.final_answer == "这是最终答案"
    
    def test_get_conversation_summary(self):
        """测试获取对话摘要."""
        agent = Agent()
        agent.start_conversation("test_conversation")
        agent.add_message("user", "Hello")
        agent.add_message("assistant", "Hi")
        
        summary = agent.get_conversation_summary()
        
        assert summary["conversation_id"] == "test_conversation"
        assert summary["message_count"] == 2
        assert summary["is_completed"] is False


if __name__ == "__main__":
    pytest.main([__file__]) 