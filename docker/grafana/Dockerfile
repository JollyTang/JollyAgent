# Grafana Docker 配置 - 使用OpenAnolis镜像
FROM registry.openanolis.cn/openanolis/grafana:7.5.11-8.6

# 设置环境变量
ENV GF_SECURITY_ADMIN_PASSWORD=admin
ENV GF_SECURITY_ADMIN_USER=admin
ENV GF_USERS_ALLOW_SIGN_UP=false
ENV GF_INSTALL_PLUGINS=grafana-clickhouse-datasource

# 创建数据目录
RUN mkdir -p /var/lib/grafana /etc/grafana

# 复制配置文件（如果需要自定义配置）
# COPY grafana.ini /etc/grafana/grafana.ini
# COPY provisioning /etc/grafana/provisioning

# 暴露端口
# 3000: Grafana Web UI
EXPOSE 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:3000/api/health || exit 1

# 设置工作目录
WORKDIR /usr/share/grafana

# 启动Grafana服务器
CMD ["grafana-server", "--config=/etc/grafana/grafana.ini", "--homepath=/usr/share/grafana"] 