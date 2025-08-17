#!/bin/bash
# Kafka Topic 创建脚本
# 用于创建 JollyAgent 监控系统的 Topic

KAFKA_HOME=${KAFKA_HOME:-/opt/kafka}
KAFKA_BROKERS=${KAFKA_BROKERS:-localhost:9092}

echo '开始创建 JollyAgent 监控系统 Topic...'

echo '创建 Topic: jollyagent.executions'
$KAFKA_HOME/bin/kafka-topics.sh --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic jollyagent.executions \
  --partitions 3 \
  --replication-factor 2 \
  --config retention.ms=604800000 \
  --config cleanup.policy=delete \
  --config compression.type=lz4

echo '创建 Topic: jollyagent.metrics'
$KAFKA_HOME/bin/kafka-topics.sh --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic jollyagent.metrics \
  --partitions 5 \
  --replication-factor 2 \
  --config retention.ms=2592000000 \
  --config cleanup.policy=delete \
  --config compression.type=lz4

echo '创建 Topic: jollyagent.events'
$KAFKA_HOME/bin/kafka-topics.sh --create \
  --bootstrap-server $KAFKA_BROKERS \
  --topic jollyagent.events \
  --partitions 3 \
  --replication-factor 2 \
  --config retention.ms=604800000 \
  --config cleanup.policy=delete \
  --config compression.type=lz4

echo 'Topic 创建完成！'
echo '列出所有 Topic:'
$KAFKA_HOME/bin/kafka-topics.sh --list --bootstrap-server $KAFKA_BROKERS