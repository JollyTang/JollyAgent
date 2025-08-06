# JollyAgent - ReAct AI Agent 框架

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

一个基于 ReAct（思考-行动-观察）循环的 AI Agent 框架，支持工具调用、分层记忆管理和用户确认机制。

## 🚀 特性

- **🤖 ReAct 循环**：实现思考-行动-观察的智能循环
- **🛠️ 工具调用**：支持内置工具和 MCP 协议扩展
- **🧠 分层记忆管理**：短期记忆 + 长期记忆的智能协调
- **✅ 用户确认**：命令行交互式确认机制
- **🎮 交互式模式**：友好的菜单式操作界面
- **⚡ 高性能**：优化的硅基流动 API 集成
- **🔧 开发友好**：完整的测试套件和开发工具
- **🚀 便捷激活**：一键环境激活脚本

## 📋 功能列表

### ✅ 已完成功能

- [x] **ReAct 思考-行动-观察循环** - 完整的智能循环实现
- [x] **硅基流动 API 集成** - 支持 Qwen/QwQ-32B 模型
- [x] **工具调用系统** - shell、文件操作、MCP 协议
- [x] **分层记忆管理** - 短期记忆 + 长期记忆协调
- [x] **CLI 用户界面** - 基于 Typer 的命令行接口
- [x] **交互式模式** - 友好的菜单式操作界面
- [x] **用户确认机制** - 交互式确认和撤销功能
- [x] **环境激活脚本** - 一键环境设置和别名配置
- [x] **完整测试套件** - 单元测试、集成测试、API 测试

### 🚧 开发中功能

- [ ] **Docker 安全沙箱** - 容器化执行环境
- [ ] **性能优化** - 响应时间优化和并发支持

### 🔧 开发工具

- [x] **代码格式化** - Black 格式化
- [x] **代码检查** - Flake8 风格检查
- [x] **类型检查** - MyPy 类型验证
- [x] **依赖管理** - uv 现代化包管理
- [x] **测试覆盖** - pytest + coverage

## 🛠️ 安装

### 环境要求

- Python 3.11+
- uv（推荐）或 pip
- 硅基流动 API 密钥

### 快速开始

1. **克隆项目**

```bash
git clone https://github.com/your-username/jollyagent.git
cd jollyagent
```

2. **安装依赖**

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -e .
```

3. **配置 API 密钥**

```bash
export JOLLYAGENT_API_KEY="your-siliconflow-api-key"
```

4. **激活环境（推荐）**

```bash
# 使用激活脚本，自动设置虚拟环境和别名
source activate_jollyagent.sh

# 激活后即可使用 jollyagent 命令
jollyagent start
```

5. **运行测试**

```bash
uv run pytest tests/ -v
```

### 手动设置（可选）

如果不使用激活脚本，可以手动设置：

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装项目
pip install -e .

# 设置别名
alias jollyagent="python -m src.cli.cli"
```

## 🎯 使用方法

### 环境激活

JollyAgent 提供了便捷的环境激活脚本：

```bash
# 激活环境并设置别名
source activate_jollyagent.sh

# 激活后即可在任何目录使用 jollyagent 命令
jollyagent start    # 启动交互式模式
jollyagent chat     # 开始对话
jollyagent config   # 查看配置
jollyagent help     # 查看帮助
```

### 基本使用

#### 1. 交互式模式（推荐）

```bash
# 启动交互式模式，通过菜单选择操作
jollyagent start

# 或者直接运行
uv run python -m src.cli.cli start
```

交互式模式提供以下功能：

- **开始对话** - 配置参数后启动对话
- **查看配置** - 显示当前配置信息
- **重置状态** - 重置 Agent 状态
- **撤销操作** - 撤销历史操作
- **查看历史** - 显示撤销历史记录
- **显示帮助** - 查看帮助信息

#### 2. 直接对话模式

```bash
# 基本对话
jollyagent chat

# 带参数的对话
jollyagent chat --stream --no-confirm --verbose

# 指定对话ID
jollyagent chat --conversation-id "my-chat-001"

# 自动确认模式
jollyagent chat --auto-confirm

# 隐藏思考过程
jollyagent chat --hide-thoughts
```

#### 3. 其他命令

```bash
# 查看配置
jollyagent config

# 重置Agent状态
jollyagent reset

# 撤销操作
jollyagent undo --last

# 查看撤销历史
jollyagent history --limit 10

# 查看帮助
jollyagent help
```

### 命令行参数说明

| 参数                              | 说明              | 默认值            |
| --------------------------------- | ----------------- | ----------------- |
| `--stream/--no-stream`            | 启用/禁用流式输出 | `--stream`        |
| `--conversation-id`               | 指定对话 ID       | 自动生成          |
| `--max-steps`                     | 最大 ReAct 步骤数 | `10`              |
| `--verbose`                       | 详细输出模式      | `False`           |
| `--confirm/--no-confirm`          | 启用/禁用用户确认 | `--confirm`       |
| `--auto-confirm`                  | 自动确认所有操作  | `False`           |
| `--show-thoughts/--hide-thoughts` | 显示/隐藏思考过程 | `--show-thoughts` |
| `--log-file`                      | 日志文件路径      | 默认路径          |

### 配置选项

项目支持丰富的配置选项，可以通过环境变量或配置文件自定义：

```python
from src.config import get_config

config = get_config()

# LLM 配置
print(config.llm.model)  # "Qwen/QwQ-32B"
print(config.llm.base_url)  # "https://api.siliconflow.cn/v1"

# 记忆配置
print(config.memory.persist_directory)  # "./memory_db"

# 工具配置
print(config.tools.max_iterations)  # 10
```

## 🏗️ 项目结构

```
JollyAgent/
├── src/                    # 源代码
│   ├── agent.py           # 主要的 Agent 类（ReAct 循环）
│   ├── config.py          # 配置管理
│   ├── executor.py        # 工具执行器
│   ├── cli/               # CLI 用户界面
│   │   ├── cli.py         # 主 CLI 入口
│   │   ├── confirm.py     # 用户确认机制
│   │   ├── undo.py        # 撤销功能
│   │   └── logging.py     # 日志管理
│   ├── tools/             # 工具模块
│   │   ├── base.py        # 工具基类抽象
│   │   ├── shell.py       # Shell 工具
│   │   ├── file.py        # 文件操作工具
│   │   └── mcp.py         # MCP 协议工具
│   ├── memory/            # 记忆管理
│   │   ├── manager.py     # 记忆管理器基类
│   │   ├── faiss_manager.py  # FAISS 向量数据库
│   │   ├── short_term.py  # 短期记忆管理
│   │   ├── long_term.py   # 长期记忆管理
│   │   └── coordinator.py # 分层记忆协调器
│   └── sandbox/           # 沙箱执行（开发中）
│       └── docker.py      # Docker 沙箱
├── tests/                 # 测试文件
│   ├── test_agent.py      # Agent 核心测试
│   ├── test_config.py     # 配置测试
│   ├── test_memory.py     # 记忆管理测试
│   ├── test_tools.py      # 工具测试
│   ├── test_mcp.py        # MCP 协议测试
│   └── test_api_connection.py  # API 连接测试
├── dev-tool/              # 开发工具
│   └── tasks-PRD.md       # 任务清单
├── pyproject.toml         # 项目配置
├── .gitignore            # Git 忽略文件
└── README.md             # 项目文档
```

## 🧠 记忆管理系统

JollyAgent 实现了先进的分层记忆管理架构：

### 短期记忆 (ShortTermMemoryManager)

- **轮次控制**：智能管理对话轮次（默认 10 轮）
- **快速检索**：基于最近对话的记忆检索
- **内存存储**：无需持久化的快速内存存储
- **消息修剪**：自动移除超出轮次限制的旧消息

### 长期记忆 (LongTermMemoryManager)

- **向量存储**：使用 FAISS 进行高效向量检索
- **会话摘要**：自动生成对话摘要
- **持久化存储**：本地向量数据库

### 分层协调 (LayeredMemoryCoordinator)

- **智能切换**：根据对话长度自动选择记忆策略
- **记忆注入**：时间倒序的记忆注入机制
- **相似度检索**：基于语义相似度的记忆检索

## 🔧 开发指南

### 运行测试

```bash
# 运行所有测试
uv run pytest tests/ -v

# 运行特定测试
uv run pytest tests/test_agent.py -v

# 生成覆盖率报告
uv run pytest tests/ --cov=src --cov-report=html
```

### 代码格式化

```bash
# 格式化代码
uv run black src/ tests/

# 检查代码风格
uv run flake8 src/ tests/

# 类型检查
uv run mypy src/
```

### 添加新工具

1. 在 `src/tools/` 目录下创建新工具文件
2. 继承 `Tool` 基类
3. 实现 `execute` 方法
4. 添加测试用例

```python
from src.tools.base import Tool

class MyTool(Tool):
    name = "my_tool"
    description = "我的自定义工具"

    def execute(self, **kwargs):
        # 实现工具逻辑
        return "工具执行结果"
```

## 📊 测试覆盖

- **总测试数**: 88
- **通过测试**: 88 ✅
- **失败测试**: 0 ✅
- **代码覆盖率**: 51%
- **测试类型**: 单元测试、集成测试、API 测试

```bash
# 查看测试覆盖率
uv run pytest tests/ --cov=src --cov-report=term-missing
```

### 测试状态说明

**✅ 通过测试模块:**

- 配置管理 (100% 覆盖率)
- 工具系统 (81% 覆盖率)
- MCP 协议 (86% 覆盖率)
- FAISS 记忆管理 (89% 覆盖率)
- Agent 核心功能 (73% 覆盖率)

**📝 测试改进成果:**

- 修复了异步函数调用问题
- 更新了配置默认值测试
- 清理了过时和重复的测试文件
- 所有测试现在都能正常通过

## 🔒 安全特性

- **用户确认**：危险操作需要用户确认
- **命令撤销**：支持操作撤销功能
- **日志记录**：完整的操作日志
- **错误处理**：健壮的错误处理机制

## 🚀 性能指标

- **响应时间**: < 3 秒（单轮对话）
- **记忆检索**: 毫秒级向量检索
- **API 优化**: 优化的硅基流动 API 调用
- **内存管理**: 智能的分层记忆管理

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

### 开发规范

- 遵循 PEP 8 代码规范
- 使用 Black 格式化代码
- 添加完整的测试用例
- 更新相关文档

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [硅基流动](https://www.siliconflow.cn/) - 提供强大的 AI API 服务
- [FAISS](https://github.com/facebookresearch/faiss) - 高效的向量检索
- [Typer](https://typer.tiangolo.com/) - 现代化的 CLI 框架
- [Pydantic](https://pydantic-docs.helpmanual.io/) - 数据验证

## 📞 联系方式

- 项目主页: [https://github.com/your-username/jollyagent](https://github.com/your-username/jollyagent)
- 问题反馈: [Issues](https://github.com/your-username/jollyagent/issues)
- 讨论区: [Discussions](https://github.com/your-username/jollyagent/discussions)

---

**JollyAgent** - 让 AI Agent 开发更简单、更智能、更高效！ 🚀
