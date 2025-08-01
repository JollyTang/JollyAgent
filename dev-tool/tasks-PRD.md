# JollyAgent ReAct 框架 - 任务清单

**基于PRD：** PRD.md  
**生成日期：** 2025-08-01  
**状态：** 草稿

---

## 相关文件

- `src/agent.py` - 主要的Agent类，实现ReAct循环
- `src/agent.py` - CLI入口点，使用Typer框架
- `src/tools/` - 工具模块目录
- `src/tools/base.py` - 工具基类抽象
- `src/tools/shell.py` - run_shell工具实现
- `src/tools/file.py` - read_file和write_file工具实现
- `src/tools/mcp.py` - MCP协议客户端实现
- `src/memory/` - 记忆管理模块
- `src/memory/manager.py` - 记忆管理器实现
- `src/sandbox/` - 沙箱执行模块
- `src/sandbox/docker.py` - Docker沙箱实现
- `src/executor.py` - 工具执行器
- `src/config.py` - 配置管理（完整实现，包含硅基流动API配置）
- `tests/` - 测试目录
- `tests/test_basic.py` - 基础测试文件
- `tests/test_config.py` - 配置模块测试文件
- `tests/test_api_connection.py` - API连接测试文件
- `pyproject.toml` - 项目配置文件（uv管理）
- `.venv/` - uv虚拟环境
- `.gitignore` - Git忽略文件配置
- `README.md` - 项目文档

### 注意事项

- 所有Python文件都应该有对应的测试文件
- 使用 `python -m pytest tests/` 运行测试
- 确保代码覆盖率 > 80%
- 遵循Python PEP 8代码规范

---

## 任务清单

- [x] 1.0 项目基础架构搭建
  - [x] 1.1 创建项目目录结构和基础文件
  - [x] 1.2 设置Python虚拟环境和依赖管理
  - [x] 1.3 配置开发工具（pytest, black, flake8）
  - [x] 1.4 创建基础配置文件（config.py）
  - [x] 1.5 设置Git仓库和.gitignore

- [ ] 2.0 ReAct循环核心实现
  - [ ] 2.1 创建Agent基类和数据模型
  - [ ] 2.2 实现LLM集成（支持硅基流动API）
  - [ ] 2.3 实现思考-行动-观察循环逻辑
  - [ ] 2.4 添加工具调用解析和分发机制
  - [ ] 2.5 实现多轮ReAct循环控制
  - [ ] 2.6 添加错误处理和重试机制

- [ ] 3.0 工具调用系统开发
  - [ ] 3.1 创建工具基类抽象（Tool ABC）
  - [ ] 3.2 实现run_shell工具
  - [ ] 3.3 实现read_file工具
  - [ ] 3.4 实现write_file工具
  - [ ] 3.5 创建MCP协议客户端
  - [ ] 3.6 实现工具注册和发现机制
  - [ ] 3.7 添加工具参数验证
  - [ ] 3.8 实现工具执行器（Executor）

- [ ] 4.0 记忆管理系统实现
  - [ ] 4.1 创建记忆管理器基类
  - [ ] 4.2 集成Chroma向量数据库
  - [ ] 4.3 实现对话历史的向量化存储
  - [ ] 4.4 实现基于相似度的记忆检索
  - [ ] 4.5 实现时间倒序的记忆注入
  - [ ] 4.6 添加记忆摘要和压缩功能
  - [ ] 4.7 实现本地记忆存储管理

- [ ] 5.0 CLI接口和用户确认机制
  - [ ] 5.1 使用Typer创建CLI框架
  - [ ] 5.2 实现chat命令和参数解析
  - [ ] 5.3 添加流式输出显示思考过程
  - [ ] 5.4 实现交互式用户确认机制
  - [ ] 5.5 添加命令撤销功能
  - [ ] 5.6 实现帮助信息和错误提示
  - [ ] 5.7 添加日志记录功能

- [ ] 6.0 安全沙箱和Docker集成
  - [ ] 6.1 创建沙箱抽象基类
  - [ ] 6.2 实现Docker沙箱环境
  - [ ] 6.3 配置容器安全限制（内存、网络、文件系统）
  - [ ] 6.4 实现本地bash备选方案
  - [ ] 6.5 添加沙箱环境监控和清理
  - [ ] 6.6 实现工作目录挂载和权限控制

- [ ] 7.0 测试、文档和发布准备
  - [ ] 7.1 为所有模块编写单元测试
  - [ ] 7.2 编写集成测试和端到端测试
  - [ ] 7.3 实现测试覆盖率监控
  - [ ] 7.4 编写详细的README文档
  - [ ] 7.5 创建使用示例和演示脚本
  - [ ] 7.6 准备发布包和版本管理
  - [ ] 7.7 进行安全审查和性能测试 