#!/bin/bash
# LLM服务生产环境启动脚本 - 支持并发

set -e

echo "🚀 启动LLM服务 (生产模式 - Gunicorn)"
echo "================================"

# 环境变量配置
export WORKERS=${WORKERS:-2}          # Worker数量（默认2个）
export WORKER_CLASS=${WORKER_CLASS:-sync}  # Worker类型
export THREADS=${THREADS:-2}          # 每个worker的线程数
export PORT=${PORT:-8611}

# 创建日志目录
mkdir -p logs

echo "📋 配置："
echo "   - Workers: $WORKERS"
echo "   - Worker Class: $WORKER_CLASS"
echo "   - Threads: $THREADS"
echo "   - Port: $PORT"
echo ""

# 使用配置文件启动
gunicorn \
    --config gunicorn_config.py \
    "api_interface_optimized:app"

# 如果不想使用配置文件，可以用：
# gunicorn \
#     --workers $WORKERS \
#     --worker-class $WORKER_CLASS \
#     --threads $THREADS \
#     --bind 0.0.0.0:$PORT \
#     --timeout 180 \
#     --max-requests 100 \
#     --access-logfile logs/llm_access.log \
#     --error-logfile logs/llm_error.log \
#     --log-level info \
#     --preload \
#     "api_interface_optimized:app"





