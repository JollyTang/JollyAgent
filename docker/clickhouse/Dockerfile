# ClickHouse Docker 配置 - 使用阿里云镜像
FROM ac2-registry.cn-hangzhou.cr.aliyuncs.com/ac2/clickhouse:25.3.1.2703-ubuntu22.04

# 设置环境变量
ENV CLICKHOUSE_DB=default
ENV CLICKHOUSE_USER=default
ENV CLICKHOUSE_PASSWORD=password
ENV CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1

# 创建数据目录
RUN mkdir -p /var/lib/clickhouse /var/log/clickhouse-server /etc/clickhouse-server

# 复制配置文件（如果需要自定义配置）
# COPY config.xml /etc/clickhouse-server/config.xml
# COPY users.xml /etc/clickhouse-server/users.xml

# 暴露端口
# 8123: HTTP端口
# 9000: Native端口
# 9009: 端口间通信
EXPOSE 8123 9000 9009

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8123/ping || exit 1

# 设置工作目录
WORKDIR /var/lib/clickhouse

# 启动ClickHouse服务器
CMD ["clickhouse-server"] 