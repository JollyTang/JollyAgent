"""Tests for Agent class and data models."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent import (
    Agent,
    AgentState,
    Message,
    Observation,
    ReActStep,
    Thought,
    ToolCall,
    get_agent,
    reset_agent,
)


class TestDataModels:
    """Test data models."""
    
    def test_message_model(self):
        """Test Message model."""
        message = Message(
            role="user",
            content="Hello, world!",
            metadata={"test": "data"}
        )
        
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.metadata == {"test": "data"}
        assert isinstance(message.timestamp, datetime)
    
    def test_tool_call_model(self):
        """Test ToolCall model."""
        tool_call = ToolCall(
            name="run_shell",
            arguments={"command": "ls -la"},
            id="test-123"
        )
        
        assert tool_call.name == "run_shell"
        assert tool_call.arguments == {"command": "ls -la"}
        assert tool_call.id == "test-123"
    
    def test_thought_model(self):
        """Test Thought model."""
        thought = Thought(
            content="I need to list files",
            reasoning="User wants to see directory contents",
            plan=["run_shell with ls command"]
        )
        
        assert thought.content == "I need to list files"
        assert thought.reasoning == "User wants to see directory contents"
        assert thought.plan == ["run_shell with ls command"]
    
    def test_observation_model(self):
        """Test Observation model."""
        observation = Observation(
            tool_name="run_shell",
            result="total 12\n-rw-r--r-- 1 user user 1234 file.txt",
            success=True
        )
        
        assert observation.tool_name == "run_shell"
        assert "total 12" in observation.result
        assert observation.success is True
        assert observation.error is None
    
    def test_react_step_model(self):
        """Test ReActStep model."""
        step = ReActStep(
            thought=Thought(content="Test thought"),
            tool_calls=[ToolCall(name="test", arguments={})],
            observations=[Observation(tool_name="test", result="test", success=True)],
            final_answer="Test answer"
        )
        
        assert step.thought.content == "Test thought"
        assert len(step.tool_calls) == 1
        assert len(step.observations) == 1
        assert step.final_answer == "Test answer"
    
    def test_agent_state_model(self):
        """Test AgentState model."""
        state = AgentState(conversation_id="test-conv-123")
        
        assert state.conversation_id == "test-conv-123"
        assert len(state.messages) == 0
        assert len(state.react_steps) == 0
        assert state.is_completed is False


class TestAgent:
    """Test Agent class."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_agent()
    
    def test_agent_initialization(self):
        """Test Agent initialization."""
        agent = Agent()
        
        assert agent.state is None
        assert agent.config is not None
        assert agent.client is not None
    
    def test_start_conversation(self):
        """Test starting a conversation."""
        agent = Agent()
        state = agent.start_conversation("test-conv-123")
        
        assert state.conversation_id == "test-conv-123"
        assert agent.state == state
        assert len(state.messages) == 0
    
    def test_add_message(self):
        """Test adding messages."""
        agent = Agent()
        agent.start_conversation("test-conv-123")
        
        message = agent.add_message("user", "Hello, world!")
        
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert len(agent.state.messages) == 1
    
    def test_add_message_without_conversation(self):
        """Test adding message without active conversation."""
        agent = Agent()
        
        with pytest.raises(ValueError, match="No active conversation"):
            agent.add_message("user", "Hello")
    
    def test_build_system_prompt(self):
        """Test system prompt building."""
        agent = Agent()
        prompt = agent._build_system_prompt()
        
        assert "ReAct" in prompt
        assert "思考" in prompt
        assert "行动" in prompt
        assert "观察" in prompt
        assert "run_shell" in prompt
    
    def test_build_messages_for_llm(self):
        """Test building messages for LLM."""
        agent = Agent()
        agent.start_conversation("test-conv-123")
        agent.add_message("user", "Hello")
        agent.add_message("assistant", "Hi there!")
        
        messages = agent._build_messages_for_llm()
        
        assert len(messages) == 3  # system + 2 messages
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"
    
    def test_parse_llm_response_json(self):
        """Test parsing JSON LLM response."""
        agent = Agent()
        
        response = '''{
            "thought": "I need to list files",
            "tool_calls": [
                {
                    "name": "run_shell",
                    "arguments": {"command": "ls -la"}
                }
            ],
            "final_answer": "Here are the files"
        }'''
        
        step = agent._parse_llm_response(response)
        
        assert step.thought.content == "I need to list files"
        assert len(step.tool_calls) == 1
        assert step.tool_calls[0].name == "run_shell"
        assert step.final_answer == "Here are the files"
    
    def test_parse_llm_response_text(self):
        """Test parsing text LLM response."""
        agent = Agent()
        
        response = """Thought: I need to list files
Action: run_shell ls -la
Answer: Here are the files"""
        
        step = agent._parse_llm_response(response)
        
        assert step.thought.content == "I need to list files"
        assert len(step.tool_calls) == 1
        assert step.tool_calls[0].name == "run_shell"
        assert step.final_answer == "Here are the files"
    
    def test_parse_llm_response_invalid(self):
        """Test parsing invalid LLM response."""
        agent = Agent()
        
        response = "Invalid response format"
        step = agent._parse_llm_response(response)
        
        assert step.thought.content == "Invalid response format"
        assert len(step.tool_calls) == 0
        assert step.final_answer is None
    
    @pytest.mark.asyncio
    @patch('src.agent.openai.OpenAI')
    async def test_call_llm(self, mock_openai):
        """Test LLM API call."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage = MagicMock()
        mock_response.usage.dict.return_value = {"total_tokens": 100}
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        agent = Agent()
        messages = [{"role": "user", "content": "Hello"}]
        
        result = await agent._call_llm(messages)
        
        assert result["content"] == "Test response"
        assert result["usage"]["total_tokens"] == 100
    
    @pytest.mark.asyncio
    async def test_think_phase(self):
        """Test think phase."""
        agent = Agent()
        agent.start_conversation("test-conv-123")
        agent.add_message("user", "List files")
        
        step = ReActStep()
        
        with patch.object(agent, '_call_llm', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "content": '{"thought": "I need to list files", "tool_calls": [{"name": "run_shell", "arguments": {"command": "ls"}}]}'
            }
            
            await agent._think(step)
            
            assert step.thought.content == "I need to list files"
            assert len(step.tool_calls) == 1
            assert step.tool_calls[0].name == "run_shell"
    
    @pytest.mark.asyncio
    async def test_act_phase(self):
        """Test act phase."""
        agent = Agent()
        step = ReActStep()
        step.tool_calls = [
            ToolCall(name="run_shell", arguments={"command": "ls"})
        ]
        
        await agent._act(step)
        
        assert len(step.observations) == 1
        assert step.observations[0].tool_name == "run_shell"
        assert step.observations[0].success is True
    
    @pytest.mark.asyncio
    async def test_observe_phase(self):
        """Test observe phase."""
        agent = Agent()
        agent.start_conversation("test-conv-123")
        agent.add_message("user", "List files")
        
        step = ReActStep()
        step.observations = [
            Observation(tool_name="run_shell", result="file1.txt file2.txt", success=True)
        ]
        
        with patch.object(agent, '_call_llm', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "content": '{"final_answer": "Found 2 files: file1.txt and file2.txt"}'
            }
            
            await agent._observe(step)
            
            assert step.final_answer == "Found 2 files: file1.txt and file2.txt"
    
    @pytest.mark.asyncio
    async def test_process_message_simple(self):
        """Test processing a simple message."""
        agent = Agent()
        agent.start_conversation("test-conv-123")
        
        with patch.object(agent, '_call_llm', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "content": '{"thought": "Simple response", "final_answer": "Hello there!"}'
            }
            
            result = await agent.process_message("Hello")
            
            assert result == "Hello there!"
            assert agent.state.is_completed is True
            assert len(agent.state.messages) == 2  # user + assistant
    
    @pytest.mark.asyncio
    async def test_process_message_with_tools(self):
        """Test processing message with tool calls."""
        agent = Agent()
        agent.start_conversation("test-conv-123")
        
        with patch.object(agent, '_call_llm', new_callable=AsyncMock) as mock_call:
            # First call: think and act
            mock_call.return_value = {
                "content": '{"thought": "Need to list files", "tool_calls": [{"name": "run_shell", "arguments": {"command": "ls"}}]}'
            }
            
            # Second call: observe and answer
            mock_call.side_effect = [
                {"content": '{"thought": "Need to list files", "tool_calls": [{"name": "run_shell", "arguments": {"command": "ls"}}]}'},
                {"content": '{"final_answer": "Files listed successfully"}'}
            ]
            
            result = await agent.process_message("List files")
            
            assert result == "Files listed successfully"
            assert agent.state.is_completed is True
            assert len(agent.state.react_steps) == 1
    
    def test_get_conversation_summary(self):
        """Test getting conversation summary."""
        agent = Agent()
        agent.start_conversation("test-conv-123")
        agent.add_message("user", "Hello")
        agent.add_message("assistant", "Hi!")
        
        summary = agent.get_conversation_summary()
        
        assert summary["conversation_id"] == "test-conv-123"
        assert summary["message_count"] == 2
        assert summary["react_steps_count"] == 0
        assert summary["is_completed"] is False
    
    def test_get_conversation_summary_no_state(self):
        """Test getting summary without active conversation."""
        agent = Agent()
        summary = agent.get_conversation_summary()
        
        assert summary == {}


class TestGlobalAgent:
    """Test global agent functions."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_agent()
    
    def test_get_agent_singleton(self):
        """Test get_agent returns singleton."""
        agent1 = get_agent()
        agent2 = get_agent()
        
        assert agent1 is agent2
    
    def test_reset_agent(self):
        """Test reset_agent function."""
        agent1 = get_agent()
        reset_agent()
        agent2 = get_agent()
        
        assert agent1 is not agent2


if __name__ == "__main__":
    pytest.main([__file__]) 