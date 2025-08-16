#!/bin/bash

# Kafka 连接测试脚本
# 用于测试 Kafka 服务的连接和基本功能

set -e

echo "=========================================="
echo "  Kafka 连接测试"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Kafka容器状态
log_info "检查Kafka容器状态..."
if docker ps | grep -q "jollyagent-kafka"; then
    log_success "Kafka容器正在运行"
else
    log_error "Kafka容器未运行"
    exit 1
fi

# 检查Zookeeper容器状态
log_info "检查Zookeeper容器状态..."
if docker ps | grep -q "jollyagent-zookeeper"; then
    log_success "Zookeeper容器正在运行"
else
    log_error "Zookeeper容器未运行"
    exit 1
fi

# 等待Kafka服务就绪
log_info "等待Kafka服务就绪..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if docker exec jollyagent-kafka /opt/bitnami/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list > /dev/null 2>&1; then
        log_success "Kafka服务已就绪"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        log_error "Kafka服务启动超时"
        exit 1
    fi
    
    log_info "等待Kafka服务启动... (尝试 $attempt/$max_attempts)"
    sleep 10
    attempt=$((attempt + 1))
done

# 测试主题列表
log_info "测试Kafka主题列表..."
if docker exec jollyagent-kafka /opt/bitnami/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list; then
    log_success "Kafka主题列表获取成功"
else
    log_error "Kafka主题列表获取失败"
    exit 1
fi

# 创建测试主题
log_info "创建测试主题..."
docker exec jollyagent-kafka /opt/bitnami/kafka/bin/kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --create \
    --topic test-topic \
    --partitions 1 \
    --replication-factor 1 \
    --if-not-exists

log_success "测试主题创建成功"

# 测试生产者
log_info "测试Kafka生产者..."
echo "Hello Kafka!" | docker exec -i jollyagent-kafka /opt/bitnami/kafka/bin/kafka-console-producer.sh \
    --bootstrap-server localhost:9092 \
    --topic test-topic

log_success "消息发送成功"

# 测试消费者
log_info "测试Kafka消费者..."
timeout 10s docker exec jollyagent-kafka /opt/bitnami/kafka/bin/kafka-console-consumer.sh \
    --bootstrap-server localhost:9092 \
    --topic test-topic \
    --from-beginning \
    --max-messages 1 || true

log_success "消息消费测试完成"

# 删除测试主题
log_info "清理测试主题..."
docker exec jollyagent-kafka /opt/bitnami/kafka/bin/kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --delete \
    --topic test-topic

log_success "测试主题已删除"

# 显示Kafka配置信息
log_info "Kafka配置信息："
echo "  Bootstrap Servers: localhost:9092"
echo "  Zookeeper: localhost:2181"
echo "  JMX Port: 9101"

log_success "Kafka连接测试完成！" 