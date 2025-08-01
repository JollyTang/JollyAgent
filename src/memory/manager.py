"""记忆管理模块."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MemoryItem(BaseModel):
    """记忆项数据模型."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str = Field(..., description="记忆内容")
    role: str = Field(..., description="角色：user/assistant/tool")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    embedding: Optional[List[float]] = Field(default=None, description="向量嵌入")
    similarity_score: Optional[float] = Field(default=None, description="相似度分数")


class MemoryQuery(BaseModel):
    """记忆查询模型."""
    
    query: str = Field(..., description="查询内容")
    limit: int = Field(default=10, ge=1, le=100, description="返回结果数量限制")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="相似度阈值")
    filter_metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据过滤条件")


class MemoryResult(BaseModel):
    """记忆查询结果模型."""
    
    items: List[MemoryItem] = Field(default_factory=list, description="记忆项列表")
    total_count: int = Field(default=0, description="总数量")
    query_time: float = Field(default=0.0, description="查询耗时（秒）")


class MemoryManager(ABC):
    """记忆管理器抽象基类."""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化记忆管理器."""
        self.config = config
        self._is_initialized = False
        logger.info("MemoryManager initialized")
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化记忆管理器."""
        pass
    
    @abstractmethod
    async def add_memory(self, content: str, role: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加记忆项."""
        pass
    
    @abstractmethod
    async def search_memory(self, query: Union[str, MemoryQuery]) -> MemoryResult:
        """搜索记忆."""
        pass
    
    @abstractmethod
    async def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """获取指定记忆项."""
        pass
    
    @abstractmethod
    async def update_memory(self, memory_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """更新记忆项."""
        pass
    
    @abstractmethod
    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆项."""
        pass
    
    @abstractmethod
    async def list_memories(self, limit: int = 100, offset: int = 0) -> List[MemoryItem]:
        """列出记忆项."""
        pass
    
    @abstractmethod
    async def clear_memories(self) -> int:
        """清空所有记忆."""
        pass
    
    @abstractmethod
    async def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息."""
        pass
    
    async def add_conversation_memory(self, messages: List[Dict[str, Any]]) -> List[str]:
        """批量添加对话记忆."""
        memory_ids = []
        for message in messages:
            memory_id = await self.add_memory(
                content=message.get("content", ""),
                role=message.get("role", "user"),
                metadata=message.get("metadata", {})
            )
            memory_ids.append(memory_id)
        return memory_ids
    
    async def search_relevant_memories(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """搜索相关记忆（简化接口）."""
        # 使用实例的相似度阈值
        similarity_threshold = getattr(self, 'similarity_threshold', 0.7)
        memory_query = MemoryQuery(
            query=query, 
            limit=limit,
            similarity_threshold=similarity_threshold
        )
        result = await self.search_memory(memory_query)
        return result.items
    
    async def close(self) -> None:
        """关闭记忆管理器."""
        if self._is_initialized:
            logger.info("MemoryManager closed")
            self._is_initialized = False
