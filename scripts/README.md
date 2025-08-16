# JollyAgent 监控系统脚本使用指南

## 脚本概览

本目录包含了 JollyAgent 监控系统的管理脚本，提供了完整的服务生命周期管理功能。

## 脚本列表

### 1. 启动脚本

- **`start_monitoring.sh`** - 一键启动监控系统

### 2. 停止脚本

- **`stop_monitoring.sh`** - 停止和清理监控系统

### 3. 重启脚本

- **`restart_monitoring.sh`** - 重启监控系统

### 4. 状态检查脚本

- **`status_monitoring.sh`** - 检查监控系统状态

### 5. 辅助脚本

- **`init_kafka_topics.sh`** - 初始化 Kafka 主题
- **`test_kafka_connection.sh`** - 测试 Kafka 连接

## 使用方法

### 启动监控系统

```bash
# 标准启动（推荐）
./scripts/start_monitoring.sh

# 强制重新拉取镜像启动（解决ContainerConfig错误时使用）
./scripts/start_monitoring.sh --force-pull

# 显示帮助信息
./scripts/start_monitoring.sh --help

# 启动脚本会自动：
# 1. 检查Docker环境
# 2. 清理Docker缓存（解决ContainerConfig错误）
# 3. 分步启动所有服务
# 4. 验证服务健康状态
# 5. 初始化Kafka主题
```

### 停止监控系统

```bash
# 仅停止服务
./scripts/stop_monitoring.sh stop

# 停止并移除容器
./scripts/stop_monitoring.sh down

# 清理所有数据（危险操作）
./scripts/stop_monitoring.sh clean

# 完全重置系统（危险操作）
./scripts/stop_monitoring.sh reset
```

### 重启监控系统

```bash
# 标准重启（推荐）
./scripts/restart_monitoring.sh

# 软重启（仅重启容器）
./scripts/restart_monitoring.sh soft

# 硬重启（清理后重启）
./scripts/restart_monitoring.sh hard
```

### 检查系统状态

```bash
# 检查所有服务状态
./scripts/status_monitoring.sh

# 状态检查包括：
# - 服务运行状态
# - 端口可访问性
# - Flink集群状态
# - Kafka主题状态
# - 系统资源使用
# - 最近日志摘要
```

## 服务访问地址

启动成功后，可以通过以下地址访问服务：

- **Grafana**: http://localhost:3000 (admin/admin)
- **Flink Web UI**: http://localhost:8081
- **ClickHouse HTTP**: http://localhost:8123
- **Kafka**: localhost:9092
- **Zookeeper**: localhost:2181

## 故障排除

### 常见问题

1. **ContainerConfig 错误**

   - 原因：Docker Compose 配置缓存损坏
   - 解决：启动脚本会自动清理缓存

2. **Flink TaskManager 连接失败**

   - 原因：JobManager 和 TaskManager 配置不匹配
   - 解决：使用自定义配置文件已解决

3. **Kafka 主题创建失败**
   - 原因：Kafka 服务未完全启动
   - 解决：启动脚本会等待服务就绪

### 日志查看

```bash
# 查看特定服务日志
docker-compose logs [service_name]

# 查看所有服务日志
docker-compose logs

# 实时查看日志
docker-compose logs -f [service_name]
```

### 手动修复

如果自动修复失败，可以手动执行：

```bash
# 完全清理环境
docker-compose down --volumes
docker system prune -f
docker rmi apache/flink:1.18.1
docker pull apache/flink:1.18.1

# 重新启动
./scripts/start_monitoring.sh
```

## 脚本特性

### 启动脚本特性

- ✅ 自动环境检查
- ✅ Docker 缓存清理
- ✅ 分步服务启动
- ✅ 健康状态验证
- ✅ Flink 集群验证
- ✅ Kafka 主题初始化
- ✅ 详细状态报告

### 停止脚本特性

- ✅ 多种停止模式
- ✅ 数据备份功能
- ✅ 安全确认机制
- ✅ 完整清理功能
- ✅ 错误处理

### 重启脚本特性

- ✅ 软重启和硬重启
- ✅ 自动调用启动脚本
- ✅ 状态保持

### 状态检查脚本特性

- ✅ 服务状态概览
- ✅ 端口可访问性检查
- ✅ Flink 集群状态
- ✅ Kafka 主题状态
- ✅ 资源使用监控
- ✅ 日志摘要

## 注意事项

1. **数据安全**: 使用`clean`或`reset`选项会删除所有数据，请先备份
2. **权限要求**: 脚本需要 Docker 和 Docker Compose 权限
3. **网络要求**: 确保端口 3000, 8081, 8123, 9092, 2181 未被占用
4. **资源要求**: 建议至少 4GB 内存和 2 个 CPU 核心

## 版本信息

- 脚本版本: 2.0.0
- 支持 Docker 版本: 20.10+
- 支持 Docker Compose 版本: 1.29+
- 测试环境: Ubuntu 20.04+, CentOS 7+, macOS 10.15+
