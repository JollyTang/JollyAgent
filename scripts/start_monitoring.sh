#!/bin/bash

# JollyAgent 监控系统一键启动脚本
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
        "confluentinc/cp-zookeeper:7.4.0"
        "confluentinc/cp-kafka:7.4.0"
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

# 停止现有服务
stop_existing_services() {
    log_info "停止现有服务..."
    if docker-compose ps | grep -q "Up"; then
        docker-compose down
        log_success "现有服务已停止"
    else
        log_info "没有运行中的服务"
    fi
}

# 启动监控服务
start_services() {
    log_info "启动监控服务..."
    
    # 启动服务
    docker-compose up -d
    
    log_success "服务启动命令已执行"
}

# 等待服务启动
wait_for_services() {
    log_info "等待服务启动..."
    
    local services=(
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
                log_error "$service 服务启动超时"
                return 1
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
        "kafka"
        "clickhouse"
        "flink-jobmanager"
        "flink-taskmanager"
        "grafana"
    )
    
    for service in "${services[@]}"; do
        if docker-compose ps "$service" | grep -q "healthy"; then
            log_success "$service 健康检查通过"
        else
            log_warning "$service 健康检查未通过，但服务可能仍在启动中"
        fi
    done
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
}

# 主函数
main() {
    echo "=========================================="
    echo "  JollyAgent 监控系统启动脚本"
    echo "=========================================="
    echo ""
    
    # 切换到脚本所在目录
    cd "$(dirname "$0")/.."
    
    check_docker
    check_docker_compose
    check_images
    create_directories
    stop_existing_services
    start_services
    wait_for_services
    check_health
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