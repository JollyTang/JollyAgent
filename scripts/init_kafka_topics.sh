#!/bin/bash

# Kafka Topic 初始化脚本
# 用于在启动监控系统时自动创建所需的 Topic

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 配置
KAFKA_HOME=${KAFKA_HOME:-/opt/kafka}
KAFKA_BROKERS=${KAFKA_BROKERS:-localhost:9092}
MAX_RETRIES=30
RETRY_INTERVAL=5

# 检查 Kafka 服务是否可用
wait_for_kafka() {
    log_info "等待 Kafka 服务启动..."
    
    local retries=0
    while [ $retries -lt $MAX_RETRIES ]; do
        if docker-compose exec -T kafka kafka-topics.sh --bootstrap-server localhost:9092 --list > /dev/null 2>&1; then
            log_success "Kafka 服务已就绪"
            return 0
        fi
        
        log_info "Kafka 服务未就绪，等待 ${RETRY_INTERVAL} 秒... (${retries}/${MAX_RETRIES})"
        sleep $RETRY_INTERVAL
        retries=$((retries + 1))
    done
    
    log_error "Kafka 服务启动超时"
    return 1
}

# 检查 Topic 是否已存在
topic_exists() {
    local topic_name=$1
    docker-compose exec -T kafka kafka-topics.sh --bootstrap-server localhost:9092 --list | grep -q "^${topic_name}$"
}

# 创建单个 Topic
create_topic() {
    local topic_name=$1
    local partitions=$2
    local replication_factor=$3
    local retention_ms=$4
    
    if topic_exists "$topic_name"; then
        log_info "Topic '$topic_name' 已存在，跳过创建"
        return 0
    fi
    
    log_info "创建 Topic: $topic_name"
    
    if docker-compose exec -T kafka kafka-topics.sh --create \
        --bootstrap-server localhost:9092 \
        --topic "$topic_name" \
        --partitions "$partitions" \
        --replication-factor "$replication_factor" \
        --config retention.ms="$retention_ms" \
        --config cleanup.policy=delete \
        --config compression.type=lz4; then
        log_success "Topic '$topic_name' 创建成功"
        return 0
    else
        log_error "Topic '$topic_name' 创建失败"
        return 1
    fi
}

# 主函数
main() {
    log_info "开始初始化 Kafka Topics..."
    
    # 等待 Kafka 服务就绪
    if ! wait_for_kafka; then
        log_error "无法连接到 Kafka 服务，Topic 初始化失败"
        exit 1
    fi
    
    # 定义 Topics
    local topics=(
        "jollyagent.executions:3:2:604800000"
        "jollyagent.metrics:5:2:2592000000"
        "jollyagent.events:3:2:604800000"
    )
    
    local success_count=0
    local total_count=${#topics[@]}
    
    # 创建每个 Topic
    for topic_config in "${topics[@]}"; do
        IFS=':' read -r topic_name partitions replication_factor retention_ms <<< "$topic_config"
        
        if create_topic "$topic_name" "$partitions" "$replication_factor" "$retention_ms"; then
            success_count=$((success_count + 1))
        fi
    done
    
    # 显示结果
    echo ""
    log_info "Topic 初始化完成: $success_count/$total_count 个 Topic 创建成功"
    
    if [ $success_count -eq $total_count ]; then
        log_success "所有 Topics 初始化成功！"
        echo ""
        log_info "已创建的 Topics:"
        docker-compose exec -T kafka kafka-topics.sh --bootstrap-server localhost:9092 --list | grep "jollyagent"
        return 0
    else
        log_warning "部分 Topics 创建失败，请检查日志"
        return 1
    fi
}

# 执行主函数
main "$@" 