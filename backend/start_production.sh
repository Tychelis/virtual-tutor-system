#!/bin/bash
# Backend生产环境启动脚本 - 支持真正的并发

set -e

echo "🚀 启动Backend (生产模式 - Gunicorn)"
echo "================================"

# 环境变量配置（可以根据需要调整）
export WORKERS=${WORKERS:-4}              # Worker进程数（默认4个）
export WORKER_CLASS=${WORKER_CLASS:-gevent}  # Worker类型：sync/gevent/eventlet
export THREADS=${THREADS:-1}              # 每个worker的线程数
export PORT=${PORT:-8203}                 # 端口

# 创建日志目录
mkdir -p logs

# 使用配置文件启动
echo "📋 配置："
echo "   - Workers: $WORKERS"
echo "   - Worker Class: $WORKER_CLASS"
echo "   - Port: $PORT"
echo ""

# 启动Gunicorn
gunicorn \
    --config gunicorn_config.py \
    "app:create_app()"

# 如果不想使用配置文件，可以用下面的命令：
# gunicorn \
#     --workers $WORKERS \
#     --worker-class $WORKER_CLASS \
#     --bind 0.0.0.0:$PORT \
#     --timeout 120 \
#     --max-requests 1000 \
#     --max-requests-jitter 100 \
#     --access-logfile logs/backend_access.log \
#     --error-logfile logs/backend_error.log \
#     --log-level info \
#     --preload \
#     "app:create_app()"





