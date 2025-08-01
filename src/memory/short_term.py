"""短期记忆管理器实现."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from src.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class ShortTermMessage(BaseModel):
    """短期记忆消息模型."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str = Field(..., description="消息内容")
    role: str = Field(..., description="角色：user/assistant/tool")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class ShortTermMemoryManager(MemoryManager):
    """短期记忆管理器 - 快速内存存储，无需持久化."""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化短期记忆管理器."""
        super().__init__(config)
        
        # 配置参数
        self.max_rounds = config.get("short_term_rounds", 10)
        self.messages: List[ShortTermMessage] = []
        
        logger.info(f"ShortTermMemoryManager initialized: max_rounds={self.max_rounds}")
    
    async def initialize(self) -> None:
        """初始化短期记忆管理器."""
        self._is_initialized = True
        logger.info("ShortTermMemoryManager initialized successfully")
    
    def _trim_messages(self) -> None:
        """修剪消息列表，确保不超过轮次限制."""
        while len(self.messages) > self.max_rounds:
            removed_msg = self.messages.pop(0)
            logger.debug(f"Removed old message: {removed_msg.id}")
    
    async def add_memory(self, content: str, role: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加短期记忆."""
        if not self._is_initialized:
            await self.initialize()
        
        # 创建消息
        message = ShortTermMessage(
            content=content,
            role=role,
            metadata=metadata
        )
        
        # 添加到消息列表
        self.messages.append(message)
        
        # 修剪消息列表
        self._trim_messages()
        
        logger.debug(f"Added short-term memory: {message.id}, total messages: {len(self.messages)}")
        return message.id
    
    async def search_memory(self, query: str, limit: int = 10) -> List[ShortTermMessage]:
        """搜索短期记忆（简单文本匹配）."""
        if not self._is_initialized:
            return []
        
        # 简单的文本匹配搜索
        results = []
        query_lower = query.lower()
        
        for message in reversed(self.messages):  # 从最新的开始搜索
            if query_lower in message.content.lower():
                results.append(message)
                if len(results) >= limit:
                    break
        
        return results
    
    async def get_recent_messages(self, rounds: Optional[int] = None) -> List[ShortTermMessage]:
        """获取最近N轮消息."""
        if not self._is_initialized:
            return []
        
        n = rounds or self.max_rounds
        return self.messages[-n:]
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """获取短期记忆统计信息."""
        return {
            "total_messages": len(self.messages),
            "max_rounds": self.max_rounds,
            "is_initialized": self._is_initialized
        }
    
    async def clear_memories(self) -> int:
        """清空短期记忆."""
        count = len(self.messages)
        self.messages.clear()
        logger.info(f"Cleared {count} short-term memories")
        return count
    
    # 以下方法在短期记忆中不适用，返回默认值
    async def get_memory(self, memory_id: str) -> Optional[ShortTermMessage]:
        """获取指定记忆项（短期记忆不支持）."""
        for msg in self.messages:
            if msg.id == memory_id:
                return msg
        return None
    
    async def update_memory(self, memory_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """更新记忆项（短期记忆不支持）."""
        for msg in self.messages:
            if msg.id == memory_id:
                msg.content = content
                msg.metadata = metadata
                msg.timestamp = datetime.now()
                
                logger.debug(f"Updated short-term memory: {memory_id}")
                return True
        return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆项."""
        for i, msg in enumerate(self.messages):
            if msg.id == memory_id:
                removed_msg = self.messages.pop(i)
                logger.debug(f"Deleted short-term memory: {memory_id}")
                return True
        return False
    
    async def list_memories(self, limit: int = 100, offset: int = 0) -> List[ShortTermMessage]:
        """列出记忆项."""
        start = offset
        end = start + limit
        return self.messages[start:end]
    
    async def close(self) -> None:
        """关闭短期记忆管理器."""
        self.messages.clear()
        self._is_initialized = False
        logger.info("ShortTermMemoryManager closed") 