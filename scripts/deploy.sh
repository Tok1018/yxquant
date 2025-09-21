#!/bin/bash

# 量化交易AI系统部署脚本

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

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 命令未找到，请先安装"
        exit 1
    fi
}

# 检查Docker和Docker Compose
check_dependencies() {
    log_info "检查依赖..."
    check_command docker
    check_command docker-compose
    
    # 检查Docker是否运行
    if ! docker info &> /dev/null; then
        log_error "Docker未运行，请先启动Docker"
        exit 1
    fi
    
    log_success "依赖检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p data logs backups static/charts ssl monitoring
    mkdir -p scripts
    
    log_success "目录创建完成"
}

# 设置权限
set_permissions() {
    log_info "设置文件权限..."
    
    chmod +x scripts/*.sh
    chmod 755 data logs backups
    
    log_success "权限设置完成"
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."
    
    docker-compose build --no-cache
    
    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    docker-compose up -d
    
    log_success "服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."
    
    # 等待Web服务
    for i in {1..30}; do
        if curl -f http://localhost:8000/api/monitor/status &> /dev/null; then
            log_success "Web服务已就绪"
            break
        fi
        
        if [ $i -eq 30 ]; then
            log_error "Web服务启动超时"
            exit 1
        fi
        
        sleep 2
    done
    
    # 等待Redis服务
    for i in {1..10}; do
        if docker-compose exec redis redis-cli ping &> /dev/null; then
            log_success "Redis服务已就绪"
            break
        fi
        
        if [ $i -eq 10 ]; then
            log_warning "Redis服务启动超时"
        fi
        
        sleep 1
    done
}

# 运行健康检查
health_check() {
    log_info "运行健康检查..."
    
    # 检查Web服务
    if curl -f http://localhost:8000/api/monitor/status &> /dev/null; then
        log_success "Web服务健康检查通过"
    else
        log_error "Web服务健康检查失败"
        return 1
    fi
    
    # 检查数据库
    if docker-compose exec web python -c "from database import db_manager; print('OK')" &> /dev/null; then
        log_success "数据库连接正常"
    else
        log_error "数据库连接失败"
        return 1
    fi
    
    log_success "所有健康检查通过"
}

# 显示服务状态
show_status() {
    log_info "服务状态:"
    docker-compose ps
    
    echo ""
    log_info "访问地址:"
    echo "  Web界面: http://localhost:8000"
    echo "  API文档: http://localhost:8000/docs"
    echo "  监控面板: http://localhost:9090"
    
    echo ""
    log_info "日志查看:"
    echo "  docker-compose logs -f web"
    echo "  docker-compose logs -f nginx"
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    docker-compose down
    log_success "服务已停止"
}

# 清理资源
cleanup() {
    log_info "清理资源..."
    docker-compose down -v
    docker system prune -f
    log_success "清理完成"
}

# 备份数据
backup_data() {
    log_info "备份数据..."
    
    timestamp=$(date +"%Y%m%d_%H%M%S")
    backup_file="backups/yxquant_backup_${timestamp}.tar.gz"
    
    tar -czf "$backup_file" data/
    
    log_success "数据已备份到: $backup_file"
}

# 恢复数据
restore_data() {
    if [ -z "$1" ]; then
        log_error "请指定备份文件路径"
        exit 1
    fi
    
    log_info "恢复数据从: $1"
    
    if [ ! -f "$1" ]; then
        log_error "备份文件不存在: $1"
        exit 1
    fi
    
    tar -xzf "$1" -C ./
    log_success "数据恢复完成"
}

# 更新服务
update_services() {
    log_info "更新服务..."
    
    # 备份数据
    backup_data
    
    # 拉取最新代码
    git pull origin main
    
    # 重新构建和启动
    build_images
    start_services
    wait_for_services
    health_check
    
    log_success "服务更新完成"
}

# 显示帮助
show_help() {
    echo "量化交易AI系统部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  deploy      部署服务"
    echo "  start       启动服务"
    echo "  stop        停止服务"
    echo "  restart     重启服务"
    echo "  status      查看状态"
    echo "  logs        查看日志"
    echo "  backup      备份数据"
    echo "  restore     恢复数据"
    echo "  update      更新服务"
    echo "  cleanup     清理资源"
    echo "  help        显示帮助"
}

# 主函数
main() {
    case "${1:-deploy}" in
        deploy)
            check_dependencies
            create_directories
            set_permissions
            build_images
            start_services
            wait_for_services
            health_check
            show_status
            ;;
        start)
            start_services
            wait_for_services
            show_status
            ;;
        stop)
            stop_services
            ;;
        restart)
            stop_services
            start_services
            wait_for_services
            show_status
            ;;
        status)
            show_status
            ;;
        logs)
            docker-compose logs -f
            ;;
        backup)
            backup_data
            ;;
        restore)
            restore_data "$2"
            ;;
        update)
            update_services
            ;;
        cleanup)
            cleanup
            ;;
        help)
            show_help
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
