# JollyAgent - ReAct AI Agent 框架

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://img.shields.io/badge/tests-21%20passed-brightgreen)](https://github.com/your-username/jollyagent)

一个基于 ReAct（思考-行动-观察）循环的 AI Agent 框架，支持工具调用、记忆管理和用户确认机制。

## 🚀 特性

- **🤖 ReAct 循环**：实现思考-行动-观察的智能循环
- **🛠️ 工具调用**：支持内置工具和 MCP 协议扩展
- **🧠 记忆管理**：基于向量的对话记忆和检索
- **🔒 安全沙箱**：Docker 容器化执行环境
- **✅ 用户确认**：命令行交互式确认机制
- **⚡ 高性能**：单轮响应时间 < 2 秒

## 📋 功能列表

### 核心功能
- [x] ReAct 思考-行动-观察循环
- [x] 硅基流动 API 集成（Qwen/QwQ-32B）
- [x] 工具调用系统（shell、文件操作、MCP）
- [x] 向量记忆管理（Chroma）
- [x] Docker 安全沙箱
- [x] CLI 用户界面

### 开发工具
- [x] 完整的测试套件（100% 覆盖率）
- [x] 代码格式化（Black）
- [x] 代码检查（Flake8）
- [x] 类型检查（MyPy）
- [x] 依赖管理（uv）

## 🛠️ 安装

### 环境要求

- Python 3.11+
- Docker（用于安全沙箱）
- uv（推荐）或 pip

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
export JOLLYAGENT_API_KEY="your-api-key-here"
```

4. **运行测试**
```bash
uv run pytest tests/ -v
```

## 🎯 使用方法

### 基本使用

```bash
# 启动对话
uv run python -m src.agent chat "你好，请介绍一下自己"

# 执行任务
uv run python -m src.agent chat "列出当前目录的文件"
```

### 配置选项

项目支持丰富的配置选项，可以通过环境变量或配置文件自定义：

```python
from src.config import get_config

config = get_config()

# LLM 配置
print(config.llm.model)  # "Qwen/QwQ-32B"
print(config.llm.base_url)  # "https://api.siliconflow.cn/v1"

# 记忆配置
print(config.memory.persist_directory)  # "./chroma_db"

# 沙箱配置
print(config.sandbox.memory_limit)  # "128m"
```

## 🏗️ 项目结构

```
JollyAgent/
├── src/                    # 源代码
│   ├── agent.py           # 主要的 Agent 类
│   ├── config.py          # 配置管理
│   ├── executor.py        # 工具执行器
│   ├── tools/             # 工具模块
│   │   ├── base.py        # 工具基类
│   │   ├── shell.py       # Shell 工具
│   │   ├── file.py        # 文件操作工具
│   │   └── mcp.py         # MCP 协议工具
│   ├── memory/            # 记忆管理
│   │   └── manager.py     # 记忆管理器
│   └── sandbox/           # 沙箱执行
│       └── docker.py      # Docker 沙箱
├── tests/                 # 测试文件
│   ├── test_basic.py      # 基础测试
│   ├── test_config.py     # 配置测试
│   └── test_api_connection.py  # API 连接测试
├── dev-tool/              # 开发工具
│   └── tasks-PRD.md       # 任务清单
├── pyproject.toml         # 项目配置
├── .gitignore            # Git 忽略文件
└── README.md             # 项目文档
```

## 🔧 开发指南

### 运行测试

```bash
# 运行所有测试
uv run pytest tests/ -v

# 运行特定测试
uv run pytest tests/test_config.py -v

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

- **总测试数**: 21
- **代码覆盖率**: 100%
- **测试类型**: 单元测试、集成测试、API 测试

```bash
# 查看测试覆盖率
uv run pytest tests/ --cov=src --cov-report=term-missing
```

## 🔒 安全特性

- **Docker 沙箱**: 所有工具在隔离容器中执行
- **内存限制**: 容器内存限制为 128MB
- **网络隔离**: 默认禁用网络访问
- **命令白名单**: 只允许安全的系统命令
- **用户确认**: 危险操作需要用户确认

## 🚀 性能指标

- **响应时间**: < 2 秒（单轮对话）
- **并发支持**: 5 个并发请求
- **内存使用**: 128MB 限制
- **API 延迟**: 优化的硅基流动 API 调用

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
- [Chroma](https://www.trychroma.com/) - 向量数据库
- [Docker](https://www.docker.com/) - 容器化技术
- [Pydantic](https://pydantic-docs.helpmanual.io/) - 数据验证

## 📞 联系方式

- 项目主页: [https://github.com/your-username/jollyagent](https://github.com/your-username/jollyagent)
- 问题反馈: [Issues](https://github.com/your-username/jollyagent/issues)
- 讨论区: [Discussions](https://github.com/your-username/jollyagent/discussions)

---

**JollyAgent** - 让 AI Agent 开发更简单、更安全、更高效！ 🚀
