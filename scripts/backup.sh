#!/bin/bash

# 数据库备份脚本

set -e

# 配置
BACKUP_DIR="/app/backups"
DATA_DIR="/app/data"
DB_FILE="$DATA_DIR/quant.db"
RETENTION_DAYS=30

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 生成备份文件名
timestamp=$(date +"%Y%m%d_%H%M%S")
backup_file="$BACKUP_DIR/yxquant_backup_${timestamp}.sql"

# 备份数据库
echo "开始备份数据库..."
sqlite3 "$DB_FILE" ".dump" > "$backup_file"

# 压缩备份文件
gzip "$backup_file"
backup_file="${backup_file}.gz"

echo "数据库备份完成: $backup_file"

# 清理旧备份
echo "清理超过 $RETENTION_DAYS 天的旧备份..."
find "$BACKUP_DIR" -name "yxquant_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "备份任务完成"
