#!/bin/bash

# JollyAgent 监控系统一键启动脚本
# 作者: JollyAgent Team
# 版本: 2.0.0

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

# 检查Docker是否运行
check_docker() {
    log_info "检查Docker服务状态..."
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker服务未运行，请先启动Docker"
        exit 1
    fi
    log_success "Docker服务运行正常"
}

# 检查Docker Compose是否可用
check_docker_compose() {
    log_info "检查Docker Compose..."
    if ! docker-compose --version > /dev/null 2>&1; then
        log_error "Docker Compose未安装或不可用"
        exit 1
    fi
    log_success "Docker Compose可用"
}

# 检查必要的镜像是否存在
check_images() {
    log_info "检查必要的Docker镜像..."
    
    local required_images=(
        "zookeeper:3.9.1"
        "bitnami/kafka:3.5.1"
        "apache/flink:1.18.1"
        "clickhouse/clickhouse-server:23.8"
        "grafana/grafana:10.1.0"
    )
    
    for image in "${required_images[@]}"; do
        if ! docker image inspect "$image" > /dev/null 2>&1; then
            log_warning "镜像 $image 不存在，将尝试拉取..."
            docker pull "$image" || {
                log_error "无法拉取镜像 $image"
                exit 1
            }
        fi
    done
    log_success "所有必要镜像检查完成"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    local directories=(
        "logs"
        "config"
        "backup"
        "data"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
    done
    log_success "目录创建完成"
}

# 清理Docker环境（解决ContainerConfig错误）
clean_docker_environment() {
    local force_pull=${1:-false}
    
    log_info "清理Docker环境..."
    
    # 停止并移除所有容器和网络
    if docker-compose ps | grep -q "Up\|Exit"; then
        log_info "停止现有服务..."
        docker-compose down --volumes 2>/dev/null || true
    fi
    
    # 清理Docker系统
    log_info "清理Docker缓存..."
    docker system prune -f > /dev/null 2>&1 || true
    
    # 只有在强制拉取或镜像不存在时才重新拉取Flink镜像
    if [ "$force_pull" = "true" ] || ! docker image inspect apache/flink:1.18.1 > /dev/null 2>&1; then
        log_info "重新拉取Flink镜像..."
        docker rmi apache/flink:1.18.1 2>/dev/null || true
        docker pull apache/flink:1.18.1
    else
        log_info "Flink镜像已存在，跳过重新拉取"
    fi
    
    log_success "Docker环境清理完成"
}

# 分步启动服务
start_services_step_by_step() {
    log_info "分步启动监控服务..."
    
    # 1. 启动Zookeeper
    log_info "启动Zookeeper..."
    docker-compose up -d zookeeper
    sleep 10
    
    # 2. 启动Kafka
    log_info "启动Kafka..."
    docker-compose up -d kafka
    sleep 15
    
    # 3. 启动ClickHouse和Grafana
    log_info "启动ClickHouse和Grafana..."
    docker-compose up -d clickhouse grafana
    sleep 10
    
    # 4. 启动Flink JobManager
    log_info "启动Flink JobManager..."
    docker-compose up -d flink-jobmanager
    sleep 15
    
    # 5. 启动Flink TaskManager
    log_info "启动Flink TaskManager..."
    docker-compose up -d flink-taskmanager
    sleep 10
    
    log_success "所有服务启动命令已执行"
}

# 等待服务启动
wait_for_services() {
    log_info "等待服务启动..."
    
    local services=(
        "zookeeper"
        "kafka"
        "clickhouse"
        "flink-jobmanager"
        "flink-taskmanager"
        "grafana"
    )
    
    for service in "${services[@]}"; do
        log_info "等待 $service 服务启动..."
        local max_attempts=30
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if docker-compose ps "$service" | grep -q "Up"; then
                log_success "$service 服务已启动"
                break
            fi
            
            if [ $attempt -eq $max_attempts ]; then
                log_warning "$service 服务启动超时，但继续执行..."
                break
            fi
            
            sleep 10
            attempt=$((attempt + 1))
        done
    done
}

# 检查服务健康状态
check_health() {
    log_info "检查服务健康状态..."
    
    # 等待一段时间让服务完全启动
    sleep 30
    
    local services=(
        "zookeeper"
        "kafka"
        "clickhouse"
        "flink-jobmanager"
        "flink-taskmanager"
        "grafana"
    )
    
    local healthy_count=0
    local total_count=${#services[@]}
    
    for service in "${services[@]}"; do
        if docker-compose ps "$service" | grep -q "healthy"; then
            log_success "$service 健康检查通过"
            ((healthy_count++))
        else
            log_warning "$service 健康检查未通过，但服务可能仍在启动中"
        fi
    done
    
    log_info "健康检查结果: $healthy_count/$total_count 个服务健康"
}

# 验证Flink集群
verify_flink_cluster() {
    log_info "验证Flink集群状态..."
    
    # 等待Flink服务完全启动
    sleep 20
    
    # 检查Flink Web UI
    if curl -s http://localhost:8081/overview > /dev/null 2>&1; then
        local flink_status=$(curl -s http://localhost:8081/overview)
        local taskmanagers=$(echo "$flink_status" | grep -o '"taskmanagers":[0-9]*' | cut -d':' -f2)
        
        if [ "$taskmanagers" -gt 0 ]; then
            log_success "Flink集群正常，TaskManager数量: $taskmanagers"
        else
            log_warning "Flink集群启动中，TaskManager数量: $taskmanagers"
        fi
    else
        log_warning "无法访问Flink Web UI，集群可能仍在启动中"
    fi
}

# 初始化Kafka主题
init_kafka_topics() {
    log_info "初始化Kafka主题..."
    
    # 等待Kafka服务完全就绪
    sleep 15
    
    if [ -f "./scripts/init_kafka_topics.sh" ]; then
        ./scripts/init_kafka_topics.sh
        log_success "Kafka主题初始化完成"
    else
        log_warning "Kafka主题初始化脚本不存在，跳过主题创建"
    fi
}

# 显示服务状态
show_status() {
    log_info "显示服务状态..."
    docker-compose ps
    
    echo ""
    log_info "服务访问地址："
    echo "  Grafana: http://localhost:3000 (admin/admin)"
    echo "  Flink Web UI: http://localhost:8081"
    echo "  ClickHouse HTTP: http://localhost:8123"
    echo "  Kafka: localhost:9092"
    echo "  Zookeeper: localhost:2181"
    
    echo ""
    log_info "常用命令："
    echo "  查看日志: docker-compose logs [service_name]"
    echo "  停止服务: ./scripts/stop_monitoring.sh"
    echo "  重启服务: ./scripts/restart_monitoring.sh"
}

# 主函数
main() {
    local force_pull=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force-pull)
                force_pull=true
                shift
                ;;
            -h|--help)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --force-pull    强制重新拉取Docker镜像"
                echo "  -h, --help      显示此帮助信息"
                exit 0
                ;;
            *)
                echo "未知参数: $1"
                echo "使用 -h 或 --help 查看帮助信息"
                exit 1
                ;;
        esac
    done
    
    echo "=========================================="
    echo "  JollyAgent 监控系统启动脚本 v2.0"
    echo "=========================================="
    echo ""
    
    # 切换到脚本所在目录
    cd "$(dirname "$0")/.."
    
    check_docker
    check_docker_compose
    check_images
    create_directories
    clean_docker_environment "$force_pull"
    start_services_step_by_step
    wait_for_services
    check_health
    verify_flink_cluster
    init_kafka_topics
    show_status
    
    echo ""
    log_success "监控系统启动完成！"
    echo ""
    echo "如果遇到问题，请查看日志："
    echo "  docker-compose logs [service_name]"
    echo ""
    echo "停止服务："
    echo "  ./scripts/stop_monitoring.sh"
}

# 执行主函数
main "$@" 