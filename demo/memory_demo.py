#!/usr/bin/env python3
"""
分层记忆管理系统演示

这个demo展示了JollyAgent的分层记忆管理系统功能：
1. 短期记忆：保留最近N轮对话
2. 长期记忆：向量化存储和会话摘要
3. 智能切换：根据对话长度自动选择记忆策略
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_config
from src.memory import LayeredMemoryCoordinator, MemoryContext

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MemoryDemo:
    """记忆管理系统演示类."""
    
    def __init__(self):
        """初始化演示环境."""
        self.config = get_config()
        
        # 配置分层记忆管理器
        memory_config = {
            "persist_directory": "./demo_memory_db",
            "embedding_dimension": 1024,  # BAAI/bge-large-zh-v1.5的维度
            "index_type": "IVF100,Flat",
            "embedding_model": "BAAI/bge-large-zh-v1.5",  # 硅基流动的免费模型
            "max_memory_items": 100,
            "similarity_threshold": 0.7,
            "openai_api_key": self.config.llm.api_key,
            # 分层记忆配置
            "conversation_length_threshold": 5,  # 5轮后切换到长对话模式
            "short_term_rounds": 3,  # 保留最近3轮
            "summary_model": "Qwen/QwQ-32B",
            "summary_max_tokens": 100
        }
        
        self.memory_manager = LayeredMemoryCoordinator(memory_config)
        self.conversation_id = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info("Memory demo initialized")
    
    async def initialize(self):
        """初始化记忆管理器."""
        await self.memory_manager.initialize()
        await self.memory_manager.start_conversation(self.conversation_id)
        logger.info(f"Started demo conversation: {self.conversation_id}")
    
    async def simulate_conversation(self, messages: List[Dict[str, str]]):
        """模拟对话过程."""
        logger.info("=" * 60)
        logger.info("开始模拟对话")
        logger.info("=" * 60)
        
        for i, msg in enumerate(messages, 1):
            role = msg["role"]
            content = msg["content"]
            
            logger.info(f"\n轮次 {i}: [{role.upper()}] {content}")
            
            # 添加消息到记忆
            metadata = {
                "conversation_id": self.conversation_id,
                "round": i,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.memory_manager.add_memory(content, role, metadata)
            
            # 获取记忆上下文
            memory_context = await self.memory_manager.get_memory_context(
                self.conversation_id, content
            )
            
            # 显示记忆状态
            await self._show_memory_status(memory_context, i)
    
    async def _show_memory_status(self, context: MemoryContext, round_num: int):
        """显示记忆状态."""
        logger.info(f"\n--- 记忆状态 (第{round_num}轮) ---")
        logger.info(f"记忆模式: {context.memory_mode}")
        logger.info(f"短期记忆数量: {len(context.short_term_messages)}")
        logger.info(f"相关长期记忆数量: {len(context.relevant_memories)}")
        logger.info(f"会话摘要: {context.conversation_summary or '无'}")
        
        # 显示短期记忆内容
        if context.short_term_messages:
            logger.info("\n短期记忆内容:")
            for msg in context.short_term_messages:
                logger.info(f"  [{msg.role}] {msg.content[:50]}...")
        
        # 显示相关长期记忆
        if context.relevant_memories:
            logger.info("\n相关长期记忆:")
            for memory in context.relevant_memories:
                logger.info(f"  [{memory.role}] {memory.content[:50]}...")
    
    async def test_memory_search(self, query: str):
        """测试记忆搜索功能."""
        logger.info("\n" + "=" * 60)
        logger.info(f"测试记忆搜索: '{query}'")
        logger.info("=" * 60)
        
        # 搜索记忆
        search_result = await self.memory_manager.search_memory(query, limit=5)
        
        logger.info(f"搜索结果数量: {len(search_result)}")
        for i, memory in enumerate(search_result, 1):
            logger.info(f"{i}. [{memory.role}] {memory.content}")
    
    async def test_conversation_summary(self):
        """测试会话摘要生成."""
        logger.info("\n" + "=" * 60)
        logger.info("测试会话摘要生成")
        logger.info("=" * 60)
        
        # 获取所有消息用于生成摘要
        all_messages = await self.memory_manager.short_term_manager.list_memories(100)
        
        if all_messages:
            # 转换为摘要生成格式
            messages_for_summary = []
            for msg in all_messages:
                messages_for_summary.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # 生成摘要
            summary = await self.memory_manager.generate_conversation_summary(
                self.conversation_id, messages_for_summary
            )
            
            logger.info(f"生成的会话摘要: {summary}")
        else:
            logger.info("没有消息可以生成摘要")
    
    async def show_memory_stats(self):
        """显示记忆统计信息."""
        logger.info("\n" + "=" * 60)
        logger.info("记忆统计信息")
        logger.info("=" * 60)
        
        stats = await self.memory_manager.get_memory_stats()
        
        logger.info("协调器状态:")
        for key, value in stats["coordinator"].items():
            logger.info(f"  {key}: {value}")
        
        logger.info("\n短期记忆状态:")
        for key, value in stats["short_term"].items():
            logger.info(f"  {key}: {value}")
        
        logger.info("\n长期记忆状态:")
        for key, value in stats["long_term"].items():
            logger.info(f"  {key}: {value}")
    
    async def cleanup(self):
        """清理资源."""
        await self.memory_manager.close()
        logger.info("Memory demo cleaned up")


async def main():
    """主演示函数."""
    demo = MemoryDemo()
    
    try:
        await demo.initialize()
        
        # 模拟一个关于编程的对话
        conversation_messages = [
            {"role": "user", "content": "你好，我想学习Python编程"},
            {"role": "assistant", "content": "你好！Python是一个很好的编程语言选择。你想从哪个方面开始学习呢？"},
            {"role": "user", "content": "我想学习数据分析和机器学习"},
            {"role": "assistant", "content": "很好的选择！对于数据分析和机器学习，我推荐你先学习pandas、numpy和scikit-learn库。"},
            {"role": "user", "content": "pandas是什么？"},
            {"role": "assistant", "content": "pandas是Python中最流行的数据处理库，它提供了DataFrame数据结构，可以轻松处理表格数据。"},
            {"role": "user", "content": "能给我一个pandas的简单例子吗？"},
            {"role": "assistant", "content": "当然！这里是一个简单的例子：import pandas as pd; df = pd.DataFrame({'name': ['Alice', 'Bob'], 'age': [25, 30]})"},
            {"role": "user", "content": "这个例子很好，我想了解更多关于DataFrame的操作"},
            {"role": "assistant", "content": "DataFrame有很多强大的操作，比如筛选、分组、排序等。你想了解哪个具体的操作？"},
            {"role": "user", "content": "我想学习如何筛选数据"},
            {"role": "assistant", "content": "筛选数据可以使用布尔索引，比如：df[df['age'] > 25] 会返回年龄大于25的所有行。"},
        ]
        
        # 执行对话模拟
        await demo.simulate_conversation(conversation_messages)
        
        # 测试记忆搜索
        await demo.test_memory_search("pandas")
        await demo.test_memory_search("数据分析")
        
        # 测试会话摘要
        await demo.test_conversation_summary()
        
        # 显示统计信息
        await demo.show_memory_stats()
        
        # 结束会话
        summary = await demo.memory_manager.end_conversation(
            demo.conversation_id, 
            [{"role": msg["role"], "content": msg["content"]} for msg in conversation_messages]
        )
        logger.info(f"\n会话结束，最终摘要: {summary}")
        
    except Exception as e:
        logger.error(f"Demo执行出错: {e}")
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 