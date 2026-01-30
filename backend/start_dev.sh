#!/bin/bash
# Backend开发环境启动脚本 - 使用Flask开发服务器

set -e

echo "🔧 启动Backend (开发模式 - Flask Dev Server)"
echo "=========================================="
echo "⚠️  警告：开发服务器不支持并发，仅用于开发和调试"
echo ""

# 设置端口
export PORT=${PORT:-8203}

# 启动Flask开发服务器
python run.py





