#!/bin/bash

# JollyAgent 监控系统停止和清理脚本
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

# 显示使用说明
show_usage() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  stop     停止所有服务（默认）"
    echo "  down     停止并移除容器"
    echo "  clean    停止并清理所有数据"
    echo "  reset    完全重置（停止、清理、重建）"
    echo "  help     显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 stop    # 停止服务"
    echo "  $0 clean   # 清理数据"
    echo "  $0 reset   # 完全重置"
}

# 检查Docker是否运行
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker服务未运行"
        exit 1
    fi
}

# 停止服务
stop_services() {
    log_info "停止监控服务..."
    
    if docker-compose ps | grep -q "Up"; then
        docker-compose stop
        log_success "服务已停止"
    else
        log_info "没有运行中的服务"
    fi
}

# 停止并移除容器
down_services() {
    log_info "停止并移除容器..."
    
    if docker-compose ps | grep -q "Up\|Exit"; then
        docker-compose down
        log_success "容器已停止并移除"
    else
        log_info "没有需要移除的容器"
    fi
}

# 清理数据卷
clean_volumes() {
    log_info "清理数据卷..."
    
    local volumes=(
        "jollyagent_zookeeper_data"
        "jollyagent_zookeeper_logs"
        "jollyagent_kafka_data"
        "jollyagent_kafka_logs"
        "jollyagent_flink_data"
        "jollyagent_flink_logs"
        "jollyagent_clickhouse_data"
        "jollyagent_clickhouse_logs"
        "jollyagent_clickhouse_config"
        "jollyagent_grafana_data"
        "jollyagent_grafana_config"
    )
    
    for volume in "${volumes[@]}"; do
        if docker volume ls -q | grep -q "^$volume$"; then
            log_warning "删除数据卷: $volume"
            docker volume rm "$volume" 2>/dev/null || log_error "无法删除数据卷 $volume"
        fi
    done
    
    log_success "数据卷清理完成"
}

# 清理网络
clean_networks() {
    log_info "清理网络..."
    
    if docker network ls | grep -q jollyagent-network; then
        log_warning "删除网络: jollyagent-network"
        docker network rm jollyagent-network 2>/dev/null || log_error "无法删除网络 jollyagent-network"
    fi
    
    log_success "网络清理完成"
}

# 清理镜像
clean_images() {
    log_info "清理镜像..."
    
    local images=(
        "apache/flink:1.18.1"
        "bitnami/kafka:3.5.1"
        "zookeeper:3.9.1"
        "clickhouse/clickhouse-server:23.8"
        "grafana/grafana:10.1.0"
    )
    
    for image in "${images[@]}"; do
        if docker images | grep -q "$(echo $image | cut -d':' -f1)"; then
            log_warning "删除镜像: $image"
            docker rmi "$image" 2>/dev/null || log_error "无法删除镜像 $image"
        fi
    done
    
    log_success "镜像清理完成"
}

# 清理日志文件
clean_logs() {
    log_info "清理日志文件..."
    
    if [ -d "logs" ]; then
        log_warning "删除日志目录"
        rm -rf logs/*
        log_success "日志文件清理完成"
    fi
}

# 清理临时文件
clean_temp_files() {
    log_info "清理临时文件..."
    
    # 清理Docker Compose临时文件
    if [ -f ".env" ]; then
        rm -f .env
    fi
    
    # 清理可能的临时文件
    find . -name "*.tmp" -delete 2>/dev/null || true
    find . -name "*.log" -delete 2>/dev/null || true
    
    log_success "临时文件清理完成"
}

# 备份数据（在清理前）
backup_data() {
    log_info "备份重要数据..."
    
    local backup_dir="backup/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # 备份配置文件
    if [ -d "config" ]; then
        cp -r config "$backup_dir/"
        log_success "配置文件已备份到 $backup_dir"
    fi
    
    # 备份Docker Compose文件
    if [ -f "docker-compose.yml" ]; then
        cp docker-compose.yml "$backup_dir/"
        log_success "Docker Compose文件已备份"
    fi
    
    # 备份脚本文件
    if [ -d "scripts" ]; then
        cp -r scripts "$backup_dir/"
        log_success "脚本文件已备份"
    fi
    
    log_success "数据备份完成: $backup_dir"
}

# 显示清理确认
show_clean_confirmation() {
    echo ""
    log_warning "警告：此操作将删除所有监控数据！"
    echo ""
    echo "将删除以下内容："
    echo "  - 所有容器"
    echo "  - 所有数据卷"
    echo "  - 所有网络"
    echo "  - 所有镜像"
    echo "  - 日志文件"
    echo ""
    echo "备份的数据将保存在 backup/ 目录中"
    echo ""
    
    read -p "确认要清理所有数据吗？(yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "操作已取消"
        exit 0
    fi
}

# 显示重置确认
show_reset_confirmation() {
    echo ""
    log_warning "警告：此操作将完全重置监控系统！"
    echo ""
    echo "将执行以下操作："
    echo "  1. 停止所有服务"
    echo "  2. 清理所有数据"
    echo "  3. 重新拉取镜像"
    echo "  4. 重新启动服务"
    echo ""
    
    read -p "确认要完全重置吗？(yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "操作已取消"
        exit 0
    fi
}

# 重新拉取镜像
pull_images() {
    log_info "重新拉取镜像..."
    
    local images=(
        "zookeeper:3.9.1"
        "bitnami/kafka:3.5.1"
        "apache/flink:1.18.1"
        "clickhouse/clickhouse-server:23.8"
        "grafana/grafana:10.1.0"
    )
    
    for image in "${images[@]}"; do
        log_info "拉取镜像: $image"
        docker pull "$image" || log_error "无法拉取镜像 $image"
    done
    
    log_success "镜像拉取完成"
}

# 重启服务
restart_services() {
    log_info "重新启动服务..."
    
    # 调用启动脚本
    if [ -f "./scripts/start_monitoring.sh" ]; then
        ./scripts/start_monitoring.sh
    else
        log_error "启动脚本不存在"
        exit 1
    fi
}

# 显示当前状态
show_status() {
    log_info "当前服务状态："
    docker-compose ps 2>/dev/null || log_info "没有运行的服务"
}

# 主函数
main() {
    local action=${1:-stop}
    
    echo "=========================================="
    echo "  JollyAgent 监控系统停止和清理脚本 v2.0"
    echo "=========================================="
    echo ""
    
    # 切换到脚本所在目录
    cd "$(dirname "$0")/.."
    
    # 检查Docker
    check_docker
    
    case $action in
        "stop")
            log_info "执行停止操作..."
            show_status
            stop_services
            ;;
        "down")
            log_info "执行停止并移除操作..."
            show_status
            down_services
            ;;
        "clean")
            log_info "执行清理操作..."
            backup_data
            show_clean_confirmation
            down_services
            clean_volumes
            clean_networks
            clean_images
            clean_logs
            clean_temp_files
            log_success "清理操作完成"
            ;;
        "reset")
            log_info "执行重置操作..."
            backup_data
            show_reset_confirmation
            down_services
            clean_volumes
            clean_networks
            clean_images
            clean_logs
            clean_temp_files
            pull_images
            restart_services
            log_success "重置操作完成"
            ;;
        "help"|"-h"|"--help")
            show_usage
            exit 0
            ;;
        *)
            log_error "未知操作: $action"
            show_usage
            exit 1
            ;;
    esac
    
    echo ""
    log_success "操作完成！"
}

# 执行主函数
main "$@" 