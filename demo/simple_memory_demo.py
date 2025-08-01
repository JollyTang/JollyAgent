#!/usr/bin/env python3
"""
简化记忆管理系统演示

快速测试分层记忆系统的基本功能
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_config
from src.memory import LayeredMemoryCoordinator

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def simple_demo():
    """简单的记忆系统演示."""
    logger.info("开始简化记忆系统演示")
    
    # 配置
    config = get_config()
    memory_config = {
        "persist_directory": "./simple_demo_db",
        "embedding_dimension": 1024,  # BAAI/bge-large-zh-v1.5的维度
        "index_type": "IVF100,Flat",
        "embedding_model": "BAAI/bge-large-zh-v1.5",  # 硅基流动的免费模型
        "max_memory_items": 50,
        "similarity_threshold": 0.7,
        "openai_api_key": config.llm.api_key,
        "conversation_length_threshold": 3,  # 3轮后切换到长对话模式
        "short_term_rounds": 2,  # 保留最近2轮
        "summary_model": "Qwen/QwQ-32B",
        "summary_max_tokens": 50
    }
    
    # 初始化记忆管理器
    memory_manager = LayeredMemoryCoordinator(memory_config)
    conversation_id = f"simple_demo_{datetime.now().strftime('%H%M%S')}"
    
    try:
        # 初始化
        await memory_manager.initialize()
        await memory_manager.start_conversation(conversation_id)
        logger.info(f"开始会话: {conversation_id}")
        
        # 添加一些测试消息
        test_messages = [
            ("user", "我想学习Python"),
            ("assistant", "Python是一个很好的编程语言！"),
            ("user", "Python适合做什么？"),
            ("assistant", "Python适合数据分析、机器学习、Web开发等"),
            ("user", "能给我一个Python例子吗？"),
            ("assistant", "当然！print('Hello, World!') 就是一个简单的例子"),
        ]
        
        # 逐条添加消息并查看记忆状态
        for i, (role, content) in enumerate(test_messages, 1):
            logger.info(f"\n--- 第{i}轮 ---")
            logger.info(f"[{role.upper()}] {content}")
            
            # 添加记忆
            metadata = {"conversation_id": conversation_id, "round": i}
            await memory_manager.add_memory(content, role, metadata)
            
            # 获取记忆上下文
            context = await memory_manager.get_memory_context(conversation_id, content)
            logger.info(f"记忆模式: {context.memory_mode}")
            logger.info(f"短期记忆: {len(context.short_term_messages)}条")
            logger.info(f"相关长期记忆: {len(context.relevant_memories)}条")
        
        # 测试搜索
        logger.info("\n--- 测试搜索 ---")
        search_results = await memory_manager.search_memory("Python", limit=3)
        logger.info(f"搜索'Python'结果: {len(search_results)}条")
        for result in search_results:
            logger.info(f"  [{result.role}] {result.content[:30]}...")
        
        # 显示统计
        stats = await memory_manager.get_memory_stats()
        logger.info(f"\n--- 统计信息 ---")
        logger.info(f"短期记忆: {stats['short_term']['total_messages']}条")
        logger.info(f"长期记忆: {stats['long_term'].get('total_memory_items', 0)}条")
        logger.info(f"会话摘要: {stats['long_term']['conversation_summaries_count']}个")
        
        # 结束会话
        messages_for_summary = [{"role": role, "content": content} for role, content in test_messages]
        summary = await memory_manager.end_conversation(conversation_id, messages_for_summary)
        logger.info(f"\n会话摘要: {summary}")
        
    except Exception as e:
        logger.error(f"演示出错: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
    finally:
        await memory_manager.close()
        logger.info("演示结束")


if __name__ == "__main__":
    asyncio.run(simple_demo()) 