#!/bin/bash

# JollyAgent 监控系统状态检查脚本
# 作者: JollyAgent Team
# 版本: 1.0.0

set -e

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

# 检查服务状态
check_service_status() {
    local service=$1
    local status=$(docker-compose ps "$service" 2>/dev/null | tail -n +2 | awk '{print $4}')
    
    if [ -z "$status" ]; then
        echo "未运行"
    else
        echo "$status"
    fi
}

# 检查端口是否可访问
check_port() {
    local port=$1
    local service=$2
    
    if nc -z localhost "$port" 2>/dev/null; then
        log_success "$service 端口 $port 可访问"
        return 0
    else
        log_warning "$service 端口 $port 不可访问"
        return 1
    fi
}

# 检查Flink集群状态
check_flink_cluster() {
    log_info "检查Flink集群状态..."
    
    if curl -s http://localhost:8081/overview > /dev/null 2>&1; then
        local flink_status=$(curl -s http://localhost:8081/overview)
        local taskmanagers=$(echo "$flink_status" | grep -o '"taskmanagers":[0-9]*' | cut -d':' -f2)
        local slots_total=$(echo "$flink_status" | grep -o '"slots-total":[0-9]*' | cut -d':' -f2)
        local slots_available=$(echo "$flink_status" | grep -o '"slots-available":[0-9]*' | cut -d':' -f2)
        
        log_success "Flink集群正常"
        echo "  TaskManager数量: $taskmanagers"
        echo "  总槽位: $slots_total"
        echo "  可用槽位: $slots_available"
    else
        log_warning "Flink集群不可访问"
    fi
}

# 检查Kafka主题
check_kafka_topics() {
    log_info "检查Kafka主题..."
    
    if docker exec jollyagent-kafka /opt/bitnami/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list 2>/dev/null; then
        log_success "Kafka主题列表获取成功"
    else
        log_warning "无法获取Kafka主题列表"
    fi
}

# 显示服务状态
show_service_status() {
    log_info "服务状态概览："
    echo ""
    
    local services=(
        "zookeeper:Zookeeper:2181"
        "kafka:Kafka:9092"
        "clickhouse:ClickHouse:8123"
        "flink-jobmanager:Flink JobManager:8081"
        "flink-taskmanager:Flink TaskManager:6124"
        "grafana:Grafana:3000"
    )
    
    echo "服务名称              状态              端口检查"
    echo "------------------------------------------------"
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r service_name display_name port <<< "$service_info"
        local status=$(check_service_status "$service_name")
        
        printf "%-20s %-18s" "$display_name" "$status"
        
        if [ "$status" = "Up (healthy)" ] || [ "$status" = "Up" ]; then
            if check_port "$port" "$display_name" > /dev/null 2>&1; then
                echo "✅"
            else
                echo "⚠️"
            fi
        else
            echo "❌"
        fi
    done
}

# 显示访问地址
show_access_urls() {
    echo ""
    log_info "服务访问地址："
    echo "  Grafana: http://localhost:3000 (admin/admin)"
    echo "  Flink Web UI: http://localhost:8081"
    echo "  ClickHouse HTTP: http://localhost:8123"
    echo "  Kafka: localhost:9092"
    echo "  Zookeeper: localhost:2181"
}

# 显示系统资源使用情况
show_resource_usage() {
    echo ""
    log_info "系统资源使用情况："
    
    # Docker容器资源使用
    echo "Docker容器资源使用："
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null || log_warning "无法获取资源使用情况"
}

# 显示日志摘要
show_log_summary() {
    echo ""
    log_info "最近日志摘要："
    
    local services=("kafka" "flink-jobmanager" "flink-taskmanager" "clickhouse" "grafana")
    
    for service in "${services[@]}"; do
        if docker-compose ps "$service" | grep -q "Up"; then
            echo ""
            echo "=== $service 最近日志 ==="
            docker-compose logs --tail=3 "$service" 2>/dev/null || echo "无法获取日志"
        fi
    done
}

# 主函数
main() {
    echo "=========================================="
    echo "  JollyAgent 监控系统状态检查"
    echo "=========================================="
    echo ""
    
    # 切换到脚本所在目录
    cd "$(dirname "$0")/.."
    
    # 检查Docker Compose文件是否存在
    if [ ! -f "docker-compose.yml" ]; then
        log_error "docker-compose.yml 文件不存在"
        exit 1
    fi
    
    # 显示服务状态
    show_service_status
    
    # 显示访问地址
    show_access_urls
    
    # 检查Flink集群
    check_flink_cluster
    
    # 检查Kafka主题
    check_kafka_topics
    
    # 显示资源使用情况
    show_resource_usage
    
    # 显示日志摘要
    show_log_summary
    
    echo ""
    log_success "状态检查完成！"
}

# 执行主函数
main "$@" 