#!/bin/bash

# JollyAgent 监控系统重启脚本
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

# 显示使用说明
show_usage() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  restart   重启所有服务（默认）"
    echo "  soft      软重启（仅重启容器）"
    echo "  hard      硬重启（清理后重启）"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 restart  # 重启服务"
    echo "  $0 soft     # 软重启"
    echo "  $0 hard     # 硬重启"
}

# 软重启（仅重启容器）
soft_restart() {
    log_info "执行软重启..."
    
    # 停止服务
    if docker-compose ps | grep -q "Up"; then
        log_info "停止现有服务..."
        docker-compose stop
    fi
    
    # 启动服务
    log_info "重新启动服务..."
    docker-compose up -d
    
    log_success "软重启完成"
}

# 硬重启（清理后重启）
hard_restart() {
    log_info "执行硬重启..."
    
    # 停止并清理
    if docker-compose ps | grep -q "Up\|Exit"; then
        log_info "停止并清理现有服务..."
        docker-compose down --volumes
    fi
    
    # 清理Docker缓存
    log_info "清理Docker缓存..."
    docker system prune -f > /dev/null 2>&1 || true
    
    # 重新启动
    log_info "重新启动服务..."
    if [ -f "./scripts/start_monitoring.sh" ]; then
        ./scripts/start_monitoring.sh
    else
        docker-compose up -d
    fi
    
    log_success "硬重启完成"
}

# 主函数
main() {
    local action=${1:-restart}
    
    echo "=========================================="
    echo "  JollyAgent 监控系统重启脚本"
    echo "=========================================="
    echo ""
    
    # 切换到脚本所在目录
    cd "$(dirname "$0")/.."
    
    case $action in
        "restart"|"")
            log_info "执行标准重启..."
            hard_restart
            ;;
        "soft")
            soft_restart
            ;;
        "hard")
            hard_restart
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
    log_success "重启操作完成！"
}

# 执行主函数
main "$@" 