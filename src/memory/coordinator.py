"""分层记忆协调器实现."""

import logging
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
from datetime import datetime

from pydantic import BaseModel, Field

from src.memory.manager import MemoryManager, MemoryItem
from src.memory.short_term import ShortTermMemoryManager, ShortTermMessage
from src.memory.long_term import LongTermMemoryManager

logger = logging.getLogger(__name__)


class MemoryContext(BaseModel):
    """记忆上下文模型."""
    
    conversation_id: str = Field(..., description="会话ID")
    short_term_messages: List[ShortTermMessage] = Field(default_factory=list, description="短期记忆消息")
    conversation_summary: Optional[str] = Field(default=None, description="会话摘要")
    relevant_memories: List[MemoryItem] = Field(default_factory=list, description="相关长期记忆")
    memory_mode: str = Field(default="short", description="记忆模式：short/long/hybrid")


class LayeredMemoryCoordinator(MemoryManager):
    """分层记忆协调器 - 协调短期和长期记忆管理器."""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化分层记忆协调器."""
        super().__init__(config)
        
        # 配置参数
        self.conversation_length_threshold = config.get("conversation_length_threshold", 10)
        self.short_term_rounds = config.get("short_term_rounds", 5)
        
        # 初始化记忆管理器
        self.short_term_manager = ShortTermMemoryManager(config)
        self.long_term_manager = LongTermMemoryManager(config)
        
        # 当前会话状态
        self.current_conversation_id: Optional[str] = None
        self.conversation_message_count = 0
        
        logger.info(f"LayeredMemoryCoordinator initialized: threshold={self.conversation_length_threshold}")
    
    async def initialize(self) -> None:
        """初始化分层记忆协调器."""
        await self.short_term_manager.initialize()
        await self.long_term_manager.initialize()
        self._is_initialized = True
        logger.info("LayeredMemoryCoordinator initialized successfully")
    
    def _determine_memory_mode(self, conversation_id: str, message_count: int) -> str:
        """确定记忆模式."""
        if message_count <= self.conversation_length_threshold:
            return "short"  # 短对话模式
        else:
            return "long"   # 长对话模式
    
    async def add_memory(self, content: str, role: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加记忆到合适的层级."""
        if not self._is_initialized:
            await self.initialize()
        
        # 更新会话消息计数
        if metadata and metadata.get("conversation_id"):
            self.current_conversation_id = metadata["conversation_id"]
            self.conversation_message_count += 1
        
        # 添加到短期记忆（总是添加）
        short_term_id = await self.short_term_manager.add_memory(content, role, metadata)
        
        # 根据对话长度决定是否添加到长期记忆
        memory_mode = self._determine_memory_mode(self.current_conversation_id or "", self.conversation_message_count)
        
        if memory_mode == "long":
            # 长对话模式：同时添加到长期记忆
            long_term_id = await self.long_term_manager.add_memory(content, role, metadata)
            logger.debug(f"Added memory to both layers: short={short_term_id}, long={long_term_id}")
        else:
            logger.debug(f"Added memory to short-term only: {short_term_id}")
        
        return short_term_id
    
    async def get_memory_context(self, conversation_id: str, query: str = "") -> MemoryContext:
        """获取记忆上下文."""
        if not self._is_initialized:
            await self.initialize()
        
        # 确定记忆模式
        memory_mode = self._determine_memory_mode(conversation_id, self.conversation_message_count)
        
        # 获取短期记忆
        short_term_messages = await self.short_term_manager.get_recent_messages(self.short_term_rounds)
        
        # 获取会话摘要
        conversation_summary = await self.long_term_manager.get_conversation_summary(conversation_id)
        
        # 获取相关长期记忆（跨对话ID搜索）
        relevant_memories = []
        if query:
            # 不限制对话ID，搜索所有相关记忆
            search_result = await self.long_term_manager.search_memory_with_summary(
                query, None, limit=5  # 移除conversation_id限制
            )
            relevant_memories = search_result.get("vector_memories", [])
            
            # 如果当前对话有摘要，也包含进去
            if conversation_summary:
                # 将当前对话摘要作为相关记忆添加
                from src.memory.manager import MemoryItem
                summary_memory = MemoryItem(
                    id=f"summary_{conversation_id}",
                    content=conversation_summary,
                    role="system",
                    timestamp=datetime.now(),
                    metadata={"type": "conversation_summary", "conversation_id": conversation_id}
                )
                relevant_memories.insert(0, summary_memory)  # 将摘要放在最前面
        
        context = MemoryContext(
            conversation_id=conversation_id,
            short_term_messages=short_term_messages,
            conversation_summary=conversation_summary,
            relevant_memories=relevant_memories,
            memory_mode=memory_mode
        )
        
        logger.debug(f"Generated memory context: mode={memory_mode}, short_messages={len(short_term_messages)}, relevant_memories={len(relevant_memories)}")
        return context
    
    async def generate_conversation_summary(self, conversation_id: str, messages: List[Dict[str, Any]]) -> str:
        """生成会话摘要."""
        if not self._is_initialized:
            await self.initialize()
        
        return await self.long_term_manager.generate_conversation_summary(conversation_id, messages)
    
    async def search_memory(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """搜索记忆（智能选择搜索策略）."""
        if not self._is_initialized:
            await self.initialize()
        
        # 根据当前对话长度选择搜索策略
        memory_mode = self._determine_memory_mode(self.current_conversation_id or "", self.conversation_message_count)
        
        if memory_mode == "short":
            # 短对话模式：主要搜索短期记忆
            short_term_results = await self.short_term_manager.search_memory(query, limit)
            # 转换为MemoryItem格式
            memory_items = []
            for msg in short_term_results:
                memory_items.append(MemoryItem(
                    id=msg.id,
                    content=msg.content,
                    role=msg.role,
                    timestamp=msg.timestamp,
                    metadata=msg.metadata
                ))
            return memory_items
        else:
            # 长对话模式：主要搜索长期记忆
            return await self.long_term_manager.search_relevant_memories(query, limit)
    
    async def get_conversation_summary(self, conversation_id: str) -> Optional[str]:
        """获取会话摘要."""
        if not self._is_initialized:
            await self.initialize()
        
        return await self.long_term_manager.get_conversation_summary(conversation_id)
    
    async def start_conversation(self, conversation_id: str) -> None:
        """开始新会话."""
        self.current_conversation_id = conversation_id
        self.conversation_message_count = 0
        logger.info(f"Started new conversation: {conversation_id}")
    
    async def end_conversation(self, conversation_id: str, messages: List[Dict[str, Any]]) -> str:
        """结束会话并生成摘要."""
        if not self._is_initialized:
            await self.initialize()
        
        # 生成会话摘要
        summary = await self.generate_conversation_summary(conversation_id, messages)
        
        # 重置会话状态
        self.current_conversation_id = None
        self.conversation_message_count = 0
        
        logger.info(f"Ended conversation {conversation_id} with summary: {summary[:50]}...")
        return summary
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息."""
        if not self._is_initialized:
            await self.initialize()
        
        short_term_stats = await self.short_term_manager.get_memory_stats()
        long_term_stats = await self.long_term_manager.get_memory_stats()
        
        return {
            "coordinator": {
                "conversation_length_threshold": self.conversation_length_threshold,
                "current_conversation_id": self.current_conversation_id,
                "conversation_message_count": self.conversation_message_count,
                "is_initialized": self._is_initialized
            },
            "short_term": short_term_stats,
            "long_term": long_term_stats
        }
    
    async def clear_memories(self) -> int:
        """清空所有记忆."""
        if not self._is_initialized:
            await self.initialize()
        
        short_term_count = await self.short_term_manager.clear_memories()
        long_term_count = await self.long_term_manager.clear_memories()
        
        total_count = short_term_count + long_term_count
        logger.info(f"Cleared all memories: short_term={short_term_count}, long_term={long_term_count}")
        return total_count
    
    # 以下方法委托给相应的管理器
    async def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """获取指定记忆项."""
        # 先尝试从短期记忆获取
        short_term_memory = await self.short_term_manager.get_memory(memory_id)
        if short_term_memory:
            return MemoryItem(
                id=short_term_memory.id,
                content=short_term_memory.content,
                role=short_term_memory.role,
                timestamp=short_term_memory.timestamp,
                metadata=short_term_memory.metadata
            )
        
        # 再从长期记忆获取
        return await self.long_term_manager.get_memory(memory_id)
    
    async def update_memory(self, memory_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """更新记忆项."""
        # 先尝试更新短期记忆
        if await self.short_term_manager.update_memory(memory_id, content, metadata):
            return True
        
        # 再尝试更新长期记忆
        return await self.long_term_manager.update_memory(memory_id, content, metadata)
    
    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆项."""
        # 先尝试删除短期记忆
        if await self.short_term_manager.delete_memory(memory_id):
            return True
        
        # 再尝试删除长期记忆
        return await self.long_term_manager.delete_memory(memory_id)
    
    async def list_memories(self, limit: int = 100, offset: int = 0) -> List[MemoryItem]:
        """列出记忆项（优先返回短期记忆）."""
        short_term_memories = await self.short_term_manager.list_memories(limit, offset)
        memory_items = []
        
        for msg in short_term_memories:
            memory_items.append(MemoryItem(
                id=msg.id,
                content=msg.content,
                role=msg.role,
                timestamp=msg.timestamp,
                metadata=msg.metadata
            ))
        
        # 如果短期记忆不够，补充长期记忆
        if len(memory_items) < limit:
            remaining_limit = limit - len(memory_items)
            long_term_memories = await self.long_term_manager.list_memories(remaining_limit, 0)
            memory_items.extend(long_term_memories)
        
        return memory_items
    
    async def close(self) -> None:
        """关闭分层记忆协调器."""
        await self.short_term_manager.close()
        await self.long_term_manager.close()
        self._is_initialized = False
        logger.info("LayeredMemoryCoordinator closed") 