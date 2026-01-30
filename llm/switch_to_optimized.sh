#!/bin/bash
# 切换到优化版LLM服务的脚本

echo "======================================================================="
echo "🔄 切换到优化版 LLM 服务"
echo "======================================================================="
echo ""

# 1. 停止原版服务
echo "1️⃣  停止原版服务 (8610端口)..."
pkill -f "python.*api_interface.py" && sleep 2
echo "✅ 原版服务已停止"
echo ""

# 2. 停止优化版（如果在运行）
echo "2️⃣  停止优化版服务 (8611端口)..."
pkill -f "python.*api_interface_optimized.py" && sleep 2
echo "✅ 优化版服务已停止"
echo ""

# 3. 修改Backend配置，使其调用8611端口
echo "3️⃣  更新Backend配置..."
cd /workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/backend/routes

# 备份原文件
if [ ! -f chat.py.backup ]; then
    cp chat.py chat.py.backup
    echo "✅ 已备份 chat.py"
fi

# 修改LLM服务端口（8610 -> 8611）
sed -i 's|http://localhost:8610/chat/stream|http://localhost:8611/chat/stream|g' chat.py

if grep -q "8611" chat.py; then
    echo "✅ Backend配置已更新为使用优化版 (8611)"
else
    echo "❌ 配置更新失败"
    exit 1
fi
echo ""

# 4. 启动优化版服务在8611端口
echo "4️⃣  启动优化版服务..."
cd /workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/llm
nohup python api_interface_optimized.py > /tmp/llm_optimized.log 2>&1 &
sleep 3

# 验证服务是否启动
if curl -s http://localhost:8611/health > /dev/null; then
    echo "✅ 优化版服务已启动 (8611端口)"
else
    echo "❌ 优化版服务启动失败"
    exit 1
fi
echo ""

# 5. 重启Backend
echo "5️⃣  重启Backend服务..."
cd /workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2

# 停止Backend
pkill -f "python.*backend.*app.py"
sleep 2

# 启动Backend
cd backend
nohup python app.py > /tmp/backend.log 2>&1 &
sleep 3

if curl -s http://localhost:8203/api/health > /dev/null 2>&1; then
    echo "✅ Backend已重启"
else
    echo "⚠️  Backend可能需要手动重启"
fi
echo ""

echo "======================================================================="
echo "✅ 切换完成!"
echo "======================================================================="
echo ""
echo "📊 当前状态:"
echo "   - 优化版LLM: http://localhost:8611 (正在运行)"
echo "   - Backend: http://localhost:8203 (调用8611)"
echo ""
echo "🧪 验证方式:"
echo "   cd /workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/llm"
echo "   python compare_latency.py --check"
echo ""
echo "📝 查看日志:"
echo "   tail -f /tmp/llm_optimized.log"
echo "   tail -f /tmp/backend.log"
echo ""

