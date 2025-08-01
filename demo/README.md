# 记忆管理系统演示

这个目录包含了JollyAgent分层记忆管理系统的演示脚本。

## 文件说明

- `memory_demo.py` - 完整的分层记忆管理系统演示
- `simple_memory_demo.py` - 简化的记忆系统演示（推荐先运行）
- `README.md` - 本说明文件

## 快速开始

### 1. 运行简化演示

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行简化演示
python demo/simple_memory_demo.py
```

这个演示会：
- 模拟一个关于Python学习的对话
- 展示短期记忆和长期记忆的切换
- 测试记忆搜索功能
- 生成会话摘要

### 2. 运行完整演示

```bash
# 运行完整演示
python demo/memory_demo.py
```

这个演示会：
- 模拟更长的对话（12轮）
- 详细展示记忆状态变化
- 测试多种搜索查询
- 显示详细的统计信息

## 演示功能

### 分层记忆管理

1. **短期记忆**
   - 保留最近N轮对话（可配置）
   - 快速内存存储，无需持久化
   - 适合短对话场景

2. **长期记忆**
   - 向量化存储重要对话片段
   - 会话摘要生成和存储
   - 适合长对话场景

3. **智能切换**
   - 根据对话长度自动选择记忆策略
   - 短对话：主要使用短期记忆
   - 长对话：结合向量检索和会话摘要

### 核心特性

- **会话摘要生成**：使用LLM将整段对话总结成1-2句话
- **向量检索**：基于语义相似度检索相关记忆
- **记忆上下文**：提供完整的记忆上下文（短期+长期+摘要）
- **配置灵活**：支持多种配置选项

## 配置选项

在演示脚本中可以调整以下配置：

```python
memory_config = {
    "conversation_length_threshold": 5,  # 对话长度阈值
    "short_term_rounds": 3,              # 短期记忆保留轮数
    "summary_model": "Qwen/QwQ-32B",     # 摘要生成模型
    "summary_max_tokens": 100,           # 摘要最大token数
    # ... 其他配置
}
```

## 输出示例

运行演示后，你会看到类似这样的输出：

```
2024-01-01 10:00:00 - INFO - 开始简化记忆系统演示
2024-01-01 10:00:01 - INFO - 开始会话: simple_demo_100001

--- 第1轮 ---
[USER] 我想学习Python
记忆模式: short
短期记忆: 1条
相关长期记忆: 0条

--- 第2轮 ---
[ASSISTANT] Python是一个很好的编程语言！
记忆模式: short
短期记忆: 2条
相关长期记忆: 0条

...

--- 测试搜索 ---
搜索'Python'结果: 3条
  [user] 我想学习Python...
  [assistant] Python是一个很好的编程语言！...
  [user] Python适合做什么？...

--- 统计信息 ---
短期记忆: 2条
长期记忆: 4条
会话摘要: 1个

会话摘要: 用户想学习Python编程，讨论了Python的用途和基本语法
```

## 故障排除

### 常见问题

1. **API密钥错误**
   - 确保在`src/config.py`中设置了正确的API密钥
   - 或者设置环境变量`JOLLYAGENT_API_KEY`

2. **依赖缺失**
   - 确保安装了所有依赖：`pip install -r requirements.txt`

3. **内存不足**
   - 减少`max_memory_items`配置值
   - 或者减少`short_term_rounds`值

### 调试模式

要查看更详细的日志，可以修改日志级别：

```python
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
```

## 扩展开发

这些演示脚本可以作为开发新功能的起点：

1. **自定义对话场景**：修改`conversation_messages`列表
2. **测试新功能**：在演示类中添加新的测试方法
3. **性能测试**：添加大量消息测试系统性能
4. **集成测试**：与其他模块集成测试

## 相关文件

- `src/memory/` - 记忆管理核心模块
- `src/config.py` - 配置管理
- `src/agent.py` - Agent集成 