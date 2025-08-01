"""长期记忆管理器实现."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from src.memory.faiss_manager import FAISSMemoryManager
from src.memory.manager import MemoryItem

logger = logging.getLogger(__name__)


class ConversationSummary(BaseModel):
    """会话摘要模型."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: str = Field(..., description="会话ID")
    summary: str = Field(..., description="会话摘要内容")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class LongTermMemoryManager(FAISSMemoryManager):
    """长期记忆管理器 - 基于FAISS的向量存储 + 会话摘要."""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化长期记忆管理器."""
        super().__init__(config)
        
        # 会话摘要存储
        self.summaries: Dict[str, ConversationSummary] = {}
        self.summary_file = self.db_path / "summaries.json"
        
        # 摘要生成配置
        self.summary_model = config.get("summary_model", "Qwen/QwQ-32B")
        self.summary_max_tokens = config.get("summary_max_tokens", 100)
        
        logger.info(f"LongTermMemoryManager initialized with summary model: {self.summary_model}")
    
    async def initialize(self) -> None:
        """初始化长期记忆管理器."""
        await super().initialize()
        await self._load_summaries()
        logger.info("LongTermMemoryManager initialized successfully")
    
    async def _load_summaries(self) -> None:
        """加载会话摘要."""
        if self.summary_file.exists():
            try:
                with open(self.summary_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.summaries = {
                        conv_id: ConversationSummary(**summary_data)
                        for conv_id, summary_data in data.get("summaries", {}).items()
                    }
                logger.info(f"Loaded {len(self.summaries)} conversation summaries")
            except Exception as e:
                logger.warning(f"Failed to load summaries: {e}")
    
    async def _save_summaries(self) -> None:
        """保存会话摘要."""
        try:
            data = {
                "summaries": {
                    conv_id: summary.dict()
                    for conv_id, summary in self.summaries.items()
                }
            }
            with open(self.summary_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            logger.debug(f"Saved {len(self.summaries)} conversation summaries")
        except Exception as e:
            logger.error(f"Failed to save summaries: {e}")
    
    async def generate_conversation_summary(self, conversation_id: str, messages: List[Dict[str, Any]]) -> str:
        """生成会话摘要."""
        if not self.api_key:  # 使用api_key而不是openai_client
            logger.warning("No API key available, cannot generate summary")
            return "会话摘要生成失败：缺少API密钥"
        
        try:
            # 构建对话内容
            conversation_text = ""
            for msg in messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                if role in ["user", "assistant"]:
                    conversation_text += f"{role}: {content}\n"
            
            # 生成摘要的提示词
            summary_prompt = f"""请将以下对话总结成1-2句话的摘要，突出主要内容和结论：

对话内容：
{conversation_text}

摘要："""
            
            # 调用LLM生成摘要
            response = await self._call_llm_for_summary(summary_prompt)
            
            if response:
                # 保存摘要
                summary = ConversationSummary(
                    conversation_id=conversation_id,
                    summary=response,
                    metadata={"message_count": len(messages)}
                )
                self.summaries[conversation_id] = summary
                await self._save_summaries()
                
                logger.info(f"Generated summary for conversation {conversation_id}: {response[:50]}...")
                return response
            else:
                return "会话摘要生成失败"
                
        except Exception as e:
            logger.error(f"Failed to generate conversation summary: {e}")
            return f"会话摘要生成失败：{str(e)}"
    
    async def _call_llm_for_summary(self, prompt: str) -> Optional[str]:
        """调用LLM生成摘要."""
        try:
            import json
            import urllib.request
            
            url = "https://api.siliconflow.cn/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.summary_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": self.summary_max_tokens,
                "stream": False
            }
            
            # 使用urllib进行同步调用，在异步函数中使用线程池
            import asyncio
            
            def make_request():
                req = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode('utf-8'),
                    headers=headers,
                    method='POST'
                )
                
                with urllib.request.urlopen(req) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    return result
            
            # 在线程池中执行同步请求
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, make_request)
            
            return response["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            logger.error(f"LLM call for summary failed: {e}")
            return None
    
    async def get_conversation_summary(self, conversation_id: str) -> Optional[str]:
        """获取会话摘要."""
        summary = self.summaries.get(conversation_id)
        return summary.summary if summary else None
    
    async def list_conversation_summaries(self) -> List[ConversationSummary]:
        """列出所有会话摘要."""
        return list(self.summaries.values())
    
    async def delete_conversation_summary(self, conversation_id: str) -> bool:
        """删除会话摘要."""
        if conversation_id in self.summaries:
            del self.summaries[conversation_id]
            await self._save_summaries()
            logger.info(f"Deleted summary for conversation {conversation_id}")
            return True
        return False
    
    async def search_memory_with_summary(self, query: str, conversation_id: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
        """搜索记忆（包含相关摘要）."""
        # 获取向量搜索结果
        vector_results = await self.search_relevant_memories(query, limit)
        
        # 获取相关会话摘要
        summary_results = []
        if conversation_id:
            # 如果指定了会话ID，获取该会话的摘要
            summary = await self.get_conversation_summary(conversation_id)
            if summary:
                summary_results.append({
                    "conversation_id": conversation_id,
                    "summary": summary,
                    "relevance": "current_session"
                })
        else:
            # 搜索相关摘要（简单文本匹配）
            query_lower = query.lower()
            for conv_id, summary in self.summaries.items():
                if query_lower in summary.summary.lower():
                    summary_results.append({
                        "conversation_id": conv_id,
                        "summary": summary.summary,
                        "relevance": "text_match"
                    })
                    if len(summary_results) >= 3:  # 最多返回3个相关摘要
                        break
        
        return {
            "vector_memories": vector_results,
            "conversation_summaries": summary_results,
            "query": query
        }
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """获取长期记忆统计信息."""
        base_stats = await super().get_memory_stats()
        base_stats.update({
            "conversation_summaries_count": len(self.summaries),
            "summary_model": self.summary_model
        })
        return base_stats
    
    async def close(self) -> None:
        """关闭长期记忆管理器."""
        await self._save_summaries()
        await super().close()
        logger.info("LongTermMemoryManager closed")


# 导入asyncio用于异步调用
import asyncio 