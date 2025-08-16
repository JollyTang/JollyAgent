#!/bin/bash

# Kafka 主题初始化脚本
# 用于创建 JollyAgent 监控系统所需的 Kafka 主题

set -e

echo "正在初始化 Kafka 主题..."

# 等待 Kafka 服务启动
echo "等待 Kafka 服务启动..."
until docker exec jollyagent-kafka /opt/bitnami/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list > /dev/null 2>&1; do
    echo "等待 Kafka 服务就绪..."
    sleep 5
done

echo "Kafka 服务已就绪，开始创建主题..."

# 创建执行记录主题
echo "创建执行记录主题: jollyagent-executions"
docker exec jollyagent-kafka /opt/bitnami/kafka/bin/kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --create \
    --topic jollyagent-executions \
    --partitions 3 \
    --replication-factor 1 \
    --config retention.ms=604800000 \
    --config cleanup.policy=delete

# 创建指标主题
echo "创建指标主题: jollyagent-metrics"
docker exec jollyagent-kafka /opt/bitnami/kafka/bin/kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --create \
    --topic jollyagent-metrics \
    --partitions 3 \
    --replication-factor 1 \
    --config retention.ms=2592000000 \
    --config cleanup.policy=delete

# 创建事件主题
echo "创建事件主题: jollyagent-events"
docker exec jollyagent-kafka /opt/bitnami/kafka/bin/kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --create \
    --topic jollyagent-events \
    --partitions 3 \
    --replication-factor 1 \
    --config retention.ms=604800000 \
    --config cleanup.policy=delete

# 创建错误主题
echo "创建错误主题: jollyagent-errors"
docker exec jollyagent-kafka /opt/bitnami/kafka/bin/kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --create \
    --topic jollyagent-errors \
    --partitions 1 \
    --replication-factor 1 \
    --config retention.ms=31536000000 \
    --config cleanup.policy=delete

echo "所有主题创建完成！"

# 列出所有主题
echo "当前所有主题:"
docker exec jollyagent-kafka /opt/bitnami/kafka/bin/kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --list

echo "主题详情:"
docker exec jollyagent-kafka /opt/bitnami/kafka/bin/kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --describe \
    --topic jollyagent-executions

docker exec jollyagent-kafka /opt/bitnami/kafka/bin/kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --describe \
    --topic jollyagent-metrics

docker exec jollyagent-kafka /opt/bitnami/kafka/bin/kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --describe \
    --topic jollyagent-events

docker exec jollyagent-kafka /opt/bitnami/kafka/bin/kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --describe \
    --topic jollyagent-errors

echo "Kafka 主题初始化完成！" 