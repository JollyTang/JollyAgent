#!/bin/bash

# JollyAgent 监控系统健康检查脚本
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
    local service_name=$1
    local container_name="jollyagent-$service_name"
    
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container_name.*Up"; then
        log_success "$service_name 服务运行正常"
        return 0
    else
        log_error "$service_name 服务未运行或状态异常"
        return 1
    fi
}

# 检查端口连通性
check_port_connectivity() {
    local service_name=$1
    local port=$2
    local host=${3:-localhost}
    
    if timeout 5 bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
        log_success "$service_name 端口 $port 连通正常"
        return 0
    else
        log_error "$service_name 端口 $port 无法连通"
        return 1
    fi
}

# 检查HTTP服务
check_http_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_status"; then
        log_success "$service_name HTTP服务正常"
        return 0
    else
        log_error "$service_name HTTP服务异常"
        return 1
    fi
}

# 检查Kafka
check_kafka() {
    log_info "检查Kafka服务..."
    
    check_service_status "kafka"
    local kafka_ok=$?
    
    check_port_connectivity "Kafka" 9092
    local port_ok=$?
    
    # 检查Kafka主题列表
    if docker exec jollyagent-kafka kafka-topics --bootstrap-server localhost:9092 --list >/dev/null 2>&1; then
        log_success "Kafka主题列表查询正常"
        local cmd_ok=0
    else
        log_error "Kafka主题列表查询异常"
        local cmd_ok=1
    fi
    
    return $((kafka_ok + port_ok + cmd_ok))
}

# 检查ClickHouse
check_clickhouse() {
    log_info "检查ClickHouse服务..."
    
    check_service_status "clickhouse"
    local clickhouse_ok=$?
    
    check_port_connectivity "ClickHouse HTTP" 8123
    local http_ok=$?
    
    check_port_connectivity "ClickHouse Native" 9000
    local native_ok=$?
    
    check_http_service "ClickHouse" "http://localhost:8123/ping"
    local ping_ok=$?
    
    # 检查ClickHouse查询
    if curl -s "http://localhost:8123/?query=SELECT%201" | grep -q "1"; then
        log_success "ClickHouse查询功能正常"
        local query_ok=0
    else
        log_error "ClickHouse查询功能异常"
        local query_ok=1
    fi
    
    return $((clickhouse_ok + http_ok + native_ok + ping_ok + query_ok))
}

# 检查Flink
check_flink() {
    log_info "检查Flink服务..."
    
    check_service_status "flink-jobmanager"
    local jobmanager_ok=$?
    
    check_service_status "flink-taskmanager"
    local taskmanager_ok=$?
    
    check_port_connectivity "Flink JobManager" 8081
    local web_ok=$?
    
    check_http_service "Flink Web UI" "http://localhost:8081"
    local http_ok=$?
    
    return $((jobmanager_ok + taskmanager_ok + web_ok + http_ok))
}

# 检查Grafana
check_grafana() {
    log_info "检查Grafana服务..."
    
    check_service_status "grafana"
    local grafana_ok=$?
    
    check_port_connectivity "Grafana" 3000
    local port_ok=$?
    
    check_http_service "Grafana" "http://localhost:3000/api/health"
    local health_ok=$?
    
    return $((grafana_ok + port_ok + health_ok))
}

# 检查系统资源
check_system_resources() {
    log_info "检查系统资源..."
    
    # 检查磁盘空间
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -lt 80 ]; then
        log_success "磁盘空间充足 ($disk_usage%)"
        local disk_ok=0
    else
        log_warning "磁盘空间不足 ($disk_usage%)"
        local disk_ok=1
    fi
    
    # 检查内存使用
    local mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ "$mem_usage" -lt 80 ]; then
        log_success "内存使用正常 ($mem_usage%)"
        local mem_ok=0
    else
        log_warning "内存使用较高 ($mem_usage%)"
        local mem_ok=1
    fi
    
    # 检查CPU负载
    local cpu_load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    local cpu_num=$(nproc)
    local cpu_threshold=$(echo "$cpu_num * 0.8" | bc)
    
    if (( $(echo "$cpu_load < $cpu_threshold" | bc -l) )); then
        log_success "CPU负载正常 ($cpu_load)"
        local cpu_ok=0
    else
        log_warning "CPU负载较高 ($cpu_load)"
        local cpu_ok=1
    fi
    
    return $((disk_ok + mem_ok + cpu_ok))
}

# 检查网络连接
check_network() {
    log_info "检查网络连接..."
    
    # 检查Docker网络
    if docker network ls | grep -q jollyagent-network; then
        log_success "Docker网络 jollyagent-network 存在"
        local network_ok=0
    else
        log_error "Docker网络 jollyagent-network 不存在"
        local network_ok=1
    fi
    
    # 检查容器间通信（Kafka到ClickHouse）
    if docker exec jollyagent-kafka ping -c 1 clickhouse >/dev/null 2>&1; then
        log_success "Kafka到ClickHouse网络连通"
        local kafka_clickhouse_ok=0
    else
        log_error "Kafka到ClickHouse网络不通"
        local kafka_clickhouse_ok=1
    fi
    
    return $((network_ok + kafka_clickhouse_ok))
}

# 生成健康报告
generate_report() {
    local total_checks=$1
    local failed_checks=$2
    
    echo ""
    echo "=========================================="
    echo "  健康检查报告"
    echo "=========================================="
    echo "总检查项: $total_checks"
    echo "失败项: $failed_checks"
    echo "成功率: $(( (total_checks - failed_checks) * 100 / total_checks ))%"
    echo ""
    
    if [ $failed_checks -eq 0 ]; then
        log_success "所有服务运行正常！"
        return 0
    else
        log_warning "发现 $failed_checks 个问题，请检查相关服务"
        return 1
    fi
}

# 主函数
main() {
    echo "=========================================="
    echo "  JollyAgent 监控系统健康检查"
    echo "=========================================="
    echo ""
    
    # 切换到脚本所在目录
    cd "$(dirname "$0")/.."
    
    local total_checks=0
    local failed_checks=0
    
    # 检查各个服务
    check_kafka || failed_checks=$((failed_checks + 1))
    total_checks=$((total_checks + 3))
    
    check_clickhouse || failed_checks=$((failed_checks + 1))
    total_checks=$((total_checks + 5))
    
    check_flink || failed_checks=$((failed_checks + 1))
    total_checks=$((total_checks + 4))
    
    check_grafana || failed_checks=$((failed_checks + 1))
    total_checks=$((total_checks + 3))
    
    check_system_resources || failed_checks=$((failed_checks + 1))
    total_checks=$((total_checks + 3))
    
    check_network || failed_checks=$((failed_checks + 1))
    total_checks=$((total_checks + 2))
    
    # 生成报告
    generate_report $total_checks $failed_checks
    
    return $failed_checks
}

# 执行主函数
main "$@" 