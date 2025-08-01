"""Agent记忆管理集成测试."""

import asyncio
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from src.agent import Agent, get_agent, reset_agent
from src.config import get_config


class TestAgentMemoryIntegration:
    """Agent记忆管理集成测试."""
    
    @pytest.fixture
    def temp_dir(self):
        """临时目录fixture."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def agent_config(self, temp_dir):
        """Agent配置fixture."""
        config = get_config()
        # 修改记忆配置使用临时目录
        config.memory.persist_directory = temp_dir
        config.memory.embedding_dimension = 128  # 使用较小的维度进行测试
        config.memory.similarity_threshold = 0.001  # 降低阈值
        return config
    
    @pytest_asyncio.fixture
    async def agent(self, agent_config):
        """Agent实例fixture."""
        agent = Agent(agent_config)
        await agent.start_conversation("test_conversation")
        yield agent
        # 清理
        try:
            await agent.memory_manager.close()
        except Exception:
            pass
    
    @pytest.mark.asyncio
    async def test_agent_memory_initialization(self, agent):
        """测试Agent记忆管理器初始化."""
        assert agent.memory_manager is not None
        assert agent.memory_manager._is_initialized is True
    
    @pytest.mark.asyncio
    async def test_memory_retrieval_during_conversation(self, agent):
        """测试对话过程中的记忆检索."""
        # 添加一些历史记忆
        await agent.memory_manager.add_memory(
            content="用户之前询问过Python编程问题",
            role="user"
        )
        await agent.memory_manager.add_memory(
            content="我解释了Python的基本语法",
            role="assistant"
        )
        
        # 处理新消息，应该能检索到相关记忆
        response = await agent.process_message("我想继续学习Python")
        
        # 验证响应不为空
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_memory_saving_after_conversation(self, agent):
        """测试对话结束后记忆保存."""
        # 处理消息
        response = await agent.process_message("你好，我想了解机器学习")
        
        # 验证记忆被保存
        stats = await agent.memory_manager.get_memory_stats()
        assert stats["total_memories"] > 0
        
        # 验证可以检索到相关记忆
        memories = await agent.memory_manager.search_relevant_memories("机器学习", limit=5)
        assert len(memories) > 0
    
    @pytest.mark.asyncio
    async def test_memory_context_injection(self, agent):
        """测试记忆上下文注入."""
        # 添加特定记忆
        await agent.memory_manager.add_memory(
            content="用户喜欢使用Python进行数据分析",
            role="user"
        )
        
        # 构建消息列表
        messages = await agent._build_messages_for_llm()
        
        # 验证是否包含记忆上下文
        has_memory_context = any(
            msg.get("role") == "system" and "相关历史记忆" in msg.get("content", "")
            for msg in messages
        )
        assert has_memory_context
    
    @pytest.mark.asyncio
    async def test_global_agent_memory(self, agent_config):
        """测试全局Agent的记忆管理."""
        # 重置全局Agent
        reset_agent()
        
        # 获取全局Agent
        agent = await get_agent()
        
        # 开始对话
        await agent.start_conversation("global_test")
        
        # 处理消息
        response = await agent.process_message("测试全局Agent记忆功能")
        
        # 验证响应
        assert response is not None
        
        # 验证记忆被保存
        stats = await agent.memory_manager.get_memory_stats()
        assert stats["total_memories"] > 0
    
    @pytest.mark.asyncio
    async def test_memory_persistence_across_conversations(self, agent):
        """测试跨对话的记忆持久化."""
        # 第一个对话
        await agent.process_message("我喜欢Python编程")
        
        # 获取记忆统计
        stats1 = await agent.memory_manager.get_memory_stats()
        initial_count = stats1["total_memories"]
        
        # 开始新对话
        await agent.start_conversation("new_conversation")
        
        # 第二个对话
        response = await agent.process_message("我想继续学习编程")
        
        # 验证新记忆被添加
        stats2 = await agent.memory_manager.get_memory_stats()
        assert stats2["total_memories"] > initial_count
    
    @pytest.mark.asyncio
    async def test_memory_metadata(self, agent):
        """测试记忆元数据."""
        # 处理消息
        await agent.process_message("测试消息")
        
        # 获取记忆列表
        memories = await agent.memory_manager.list_memories(limit=5)
        
        # 验证元数据
        for memory in memories:
            assert "conversation_id" in memory.metadata
            assert "timestamp" in memory.metadata
            assert memory.metadata["conversation_id"] == "test_conversation"


if __name__ == "__main__":
    pytest.main([__file__]) 