# Flink Docker 配置 - 使用OpenAnolis镜像
FROM registry.openanolis.cn/openanolis/flink:latest

# 设置环境变量
ENV FLINK_HOME=/opt/flink
ENV PATH=$PATH:$FLINK_HOME/bin

# 设置Flink配置
ENV FLINK_PROPERTIES="jobmanager.rpc.address:flink-jobmanager"

# 创建数据目录
RUN mkdir -p /opt/flink/logs /opt/flink/data

# 暴露端口
# 8081: JobManager Web UI
# 6123: JobManager RPC
# 6124: TaskManager RPC
# 6125: TaskManager Data
EXPOSE 8081 6123 6124 6125

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8081/ || exit 1

# 设置工作目录
WORKDIR $FLINK_HOME

# 启动命令（将在docker-compose中覆盖）
CMD ["jobmanager"] 