"""基于FAISS的记忆管理器实现."""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import faiss
import numpy as np
from openai import OpenAI

from src.memory.manager import MemoryItem, MemoryQuery, MemoryResult, MemoryManager

logger = logging.getLogger(__name__)


class FAISSMemoryManager(MemoryManager):
    """基于FAISS的记忆管理器."""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化FAISS记忆管理器."""
        super().__init__(config)
        
        # 配置参数
        self.persist_directory = config.get("persist_directory", "./memory_db")
        self.index_type = config.get("index_type", "IVF100,Flat")
        self.embedding_dimension = config.get("embedding_dimension", 1024)  # 更新默认维度
        self.embedding_model = config.get("embedding_model", "BAAI/bge-large-zh-v1.5")
        self.max_memory_items = config.get("max_memory_items", 1000)
        self.similarity_threshold = config.get("similarity_threshold", 0.7)
        
        # FAISS索引和存储
        self.index = None
        self.memory_items: Dict[str, MemoryItem] = {}
        self.memory_ids: List[str] = []
        
        # 硅基流动API客户端（用于生成嵌入）
        self.api_key = config.get("openai_api_key")  # 使用相同的API密钥
        self.api_base_url = "https://api.siliconflow.cn/v1"
        
        # 文件路径
        self.db_path = Path(self.persist_directory)
        self.index_file = self.db_path / "faiss.index"
        self.metadata_file = self.db_path / "metadata.json"
        
        logger.info(f"FAISSMemoryManager initialized with config: {config}")
    
    async def initialize(self) -> None:
        """初始化FAISS索引和加载现有数据."""
        try:
            # 创建目录
            self.db_path.mkdir(parents=True, exist_ok=True)
            
            # 加载现有数据
            await self._load_existing_data()
            
            # 初始化或加载FAISS索引
            await self._initialize_index()
            
            self._is_initialized = True
            logger.info("FAISSMemoryManager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize FAISSMemoryManager: {e}")
            raise
    
    async def _load_existing_data(self) -> None:
        """加载现有的记忆数据."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.memory_items = {
                        item_id: MemoryItem(**item_data) 
                        for item_id, item_data in data.get("memory_items", {}).items()
                    }
                    self.memory_ids = data.get("memory_ids", [])
                logger.info(f"Loaded {len(self.memory_items)} existing memory items")
            except Exception as e:
                logger.warning(f"Failed to load existing data: {e}")
    
    async def _initialize_index(self) -> None:
        """初始化FAISS索引."""
        if self.index_file.exists() and len(self.memory_items) > 0:
            # 加载现有索引
            try:
                self.index = faiss.read_index(str(self.index_file))
                logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors")
            except Exception as e:
                logger.warning(f"Failed to load existing index: {e}")
                self._create_new_index()
        else:
            # 创建新索引
            self._create_new_index()
    
    def _create_new_index(self) -> None:
        """创建新的FAISS索引."""
        dimension = self.embedding_dimension
        
        if "IVF" in self.index_type:
            # IVF索引需要训练数据，先用Flat索引
            self.index = faiss.IndexFlatL2(dimension)
            logger.info(f"Created new FlatL2 index with dimension {dimension}")
        elif "HNSW" in self.index_type:
            # HNSW索引
            self.index = faiss.IndexHNSWFlat(dimension, 32)  # 32是M参数
            logger.info(f"Created new HNSW index with dimension {dimension}")
        else:
            # 默认使用Flat索引
            self.index = faiss.IndexFlatL2(dimension)
            logger.info(f"Created new FlatL2 index with dimension {dimension}")
    
    async def _call_siliconflow_api(self, text: str) -> Dict[str, Any]:
        """调用硅基流动API生成嵌入."""
        import json
        import urllib.request
        import urllib.parse
        
        url = f"{self.api_base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.embedding_model,
            "input": text
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
        result = await loop.run_in_executor(None, make_request)
        return result
    
    async def _get_embedding(self, text: str) -> List[float]:
        """获取文本的向量嵌入."""
        if not self.api_key:
            # 如果没有API密钥，返回随机向量（仅用于测试）
            logger.warning("No API key available, using random embedding")
            # 使用固定的随机种子确保测试的一致性
            np.random.seed(hash(text) % 2**32)
            return list(np.random.normal(0, 1, self.embedding_dimension))
        
        try:
            # 使用硅基流动API生成嵌入
            response = await self._call_siliconflow_api(text)
            return response["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            # 如果API调用失败，返回随机向量
            np.random.seed(hash(text) % 2**32)
            return list(np.random.normal(0, 1, self.embedding_dimension))
    
    async def add_memory(self, content: str, role: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加记忆项."""
        if not self._is_initialized:
            await self.initialize()
        
        # 创建记忆项
        memory_item = MemoryItem(
            content=content,
            role=role,
            metadata=metadata or {}
        )
        
        # 获取向量嵌入
        embedding = await self._get_embedding(content)
        memory_item.embedding = embedding
        
        # 添加到内存存储
        self.memory_items[memory_item.id] = memory_item
        self.memory_ids.append(memory_item.id)
        
        # 添加到FAISS索引
        embedding_array = np.array([embedding], dtype=np.float32)
        self.index.add(embedding_array)
        
        # 限制记忆数量
        if len(self.memory_items) > self.max_memory_items:
            await self._trim_memories()
        
        # 保存到磁盘
        await self._save_data()
        
        logger.info(f"Added memory item: {memory_item.id}")
        return memory_item.id
    
    async def search_memory(self, query: Union[str, MemoryQuery]) -> MemoryResult:
        """搜索记忆."""
        if not self._is_initialized:
            await self.initialize()
        
        start_time = time.time()
        
        # 处理查询参数
        if isinstance(query, str):
            query_text = query
            limit = 10
            similarity_threshold = self.similarity_threshold
        else:
            query_text = query.query
            limit = query.limit
            similarity_threshold = query.similarity_threshold
        
        # 获取查询的向量嵌入
        query_embedding = await self._get_embedding(query_text)
        query_array = np.array([query_embedding], dtype=np.float32)
        
        # 执行向量搜索
        if self.index.ntotal == 0:
            return MemoryResult(items=[], total_count=0, query_time=time.time() - start_time)
        
        # 搜索最相似的向量
        scores, indices = self.index.search(query_array, min(limit * 2, self.index.ntotal))
        
        # 过滤和排序结果
        results = []
        for distance, idx in zip(scores[0], indices[0]):
            if idx < len(self.memory_ids):
                memory_id = self.memory_ids[idx]
                memory_item = self.memory_items.get(memory_id)
                if memory_item:
                    # 将L2距离转换为相似度分数 (0-1范围)
                    # 使用距离的倒数作为相似度，避免距离过大的问题
                    similarity_score = 1.0 / (1.0 + distance)
                    if similarity_score >= similarity_threshold:
                        memory_item.similarity_score = float(similarity_score)
                        results.append(memory_item)
        
        # 按相似度排序并限制数量
        results.sort(key=lambda x: x.similarity_score or 0, reverse=True)
        results = results[:limit]
        
        query_time = time.time() - start_time
        logger.info(f"Memory search completed in {query_time:.3f}s, found {len(results)} results")
        
        return MemoryResult(
            items=results,
            total_count=len(results),
            query_time=query_time
        )
    
    async def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """获取指定记忆项."""
        return self.memory_items.get(memory_id)
    
    async def update_memory(self, memory_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """更新记忆项."""
        if memory_id not in self.memory_items:
            return False
        
        # 获取新的向量嵌入
        embedding = await self._get_embedding(content)
        
        # 更新记忆项
        memory_item = self.memory_items[memory_id]
        memory_item.content = content
        memory_item.embedding = embedding
        if metadata:
            memory_item.metadata.update(metadata)
        memory_item.timestamp = datetime.now()
        
        # 重新构建索引（FAISS不支持直接更新）
        await self._rebuild_index()
        
        # 保存到磁盘
        await self._save_data()
        
        logger.info(f"Updated memory item: {memory_id}")
        return True
    
    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆项."""
        if memory_id not in self.memory_items:
            return False
        
        # 从内存中删除
        del self.memory_items[memory_id]
        if memory_id in self.memory_ids:
            self.memory_ids.remove(memory_id)
        
        # 重新构建索引
        await self._rebuild_index()
        
        # 保存到磁盘
        await self._save_data()
        
        logger.info(f"Deleted memory item: {memory_id}")
        return True
    
    async def list_memories(self, limit: int = 100, offset: int = 0) -> List[MemoryItem]:
        """列出记忆项."""
        items = list(self.memory_items.values())
        items.sort(key=lambda x: x.timestamp, reverse=True)
        return items[offset:offset + limit]
    
    async def clear_memories(self) -> int:
        """清空所有记忆."""
        count = len(self.memory_items)
        self.memory_items.clear()
        self.memory_ids.clear()
        
        # 重新创建索引
        self._create_new_index()
        
        # 保存到磁盘
        await self._save_data()
        
        logger.info(f"Cleared {count} memory items")
        return count
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息."""
        return {
            "total_memories": len(self.memory_items),
            "index_size": self.index.ntotal if self.index else 0,
            "embedding_dimension": self.embedding_dimension,
            "max_memory_items": self.max_memory_items,
            "similarity_threshold": self.similarity_threshold,
            "persist_directory": str(self.persist_directory),
            "index_type": self.index_type
        }
    
    async def _rebuild_index(self) -> None:
        """重新构建FAISS索引."""
        if not self.memory_items:
            self._create_new_index()
            return
        
        # 创建新索引
        self._create_new_index()
        
        # 重新添加所有向量
        embeddings = []
        for memory_id in self.memory_ids:
            memory_item = self.memory_items.get(memory_id)
            if memory_item and memory_item.embedding:
                embeddings.append(memory_item.embedding)
        
        if embeddings:
            embedding_array = np.array(embeddings, dtype=np.float32)
            self.index.add(embedding_array)
        
        logger.info(f"Rebuilt index with {len(embeddings)} vectors")
    
    async def _trim_memories(self) -> None:
        """修剪记忆数量，保留最新的."""
        if len(self.memory_items) <= self.max_memory_items:
            return
        
        # 按时间排序，保留最新的
        sorted_items = sorted(
            self.memory_items.items(),
            key=lambda x: x[1].timestamp,
            reverse=True
        )
        
        # 保留最新的max_memory_items个
        keep_items = sorted_items[:self.max_memory_items]
        
        # 更新存储
        self.memory_items = dict(keep_items)
        self.memory_ids = [item[0] for item in keep_items]
        
        # 重新构建索引
        await self._rebuild_index()
        
        logger.info(f"Trimmed memories to {len(self.memory_items)} items")
    
    async def _save_data(self) -> None:
        """保存数据到磁盘."""
        try:
            # 保存元数据
            metadata = {
                "memory_items": {
                    item_id: item.model_dump() 
                    for item_id, item in self.memory_items.items()
                },
                "memory_ids": self.memory_ids
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)
            
            # 保存FAISS索引
            if self.index:
                faiss.write_index(self.index, str(self.index_file))
            
            logger.debug("Memory data saved to disk")
            
        except Exception as e:
            logger.error(f"Failed to save memory data: {e}")
    
    async def close(self) -> None:
        """关闭记忆管理器."""
        if self._is_initialized:
            await self._save_data()
            self._is_initialized = False
            logger.info("MemoryManager closed") 