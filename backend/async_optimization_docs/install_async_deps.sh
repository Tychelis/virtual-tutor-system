#!/bin/bash
# 安装异步优化所需的依赖

echo "=================================="
echo "Backend异步优化 - 依赖安装脚本"
echo "=================================="
echo ""

# 检查是否在backend目录
if [ ! -f "requirements.txt" ]; then
    echo "❌ 错误: 请在backend目录下运行此脚本"
    exit 1
fi

echo "📦 安装httpx异步HTTP客户端..."
pip install httpx==0.28.1

if [ $? -eq 0 ]; then
    echo "✅ httpx安装成功"
else
    echo "❌ httpx安装失败"
    exit 1
fi

echo ""
echo "=================================="
echo "✅ 所有依赖安装完成！"
echo "=================================="
echo ""
echo "📝 后续步骤:"
echo "  1. 重启Backend服务: python run.py"
echo "  2. 运行性能测试: python test_async_performance.py"
echo "  3. 查看优化文档: cat ASYNC_OPTIMIZATION.md"
echo ""

