#!/bin/bash
# 切换回原版LLM服务的脚本

echo "======================================================================="
echo "🔄 切换回原版 LLM 服务"
echo "======================================================================="
echo ""

# 1. 停止优化版服务
echo "1️⃣  停止优化版服务 (8611端口)..."
pkill -f "python.*api_interface_optimized.py" && sleep 2
echo "✅ 优化版服务已停止"
echo ""

# 2. 恢复Backend配置
echo "2️⃣  恢复Backend配置..."
cd /workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/backend/routes

if [ -f chat.py.backup ]; then
    cp chat.py.backup chat.py
    echo "✅ Backend配置已恢复"
else
    # 手动修改回8610
    sed -i 's|http://localhost:8611/chat/stream|http://localhost:8610/chat/stream|g' chat.py
    echo "✅ Backend配置已恢复为使用原版 (8610)"
fi
echo ""

# 3. 确保原版服务运行
echo "3️⃣  检查原版服务..."
if curl -s http://localhost:8610/health > /dev/null; then
    echo "✅ 原版服务正在运行 (8610端口)"
else
    echo "⚠️  原版服务未运行，正在启动..."
    cd /workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/llm
    nohup python api_interface.py > /tmp/llm_original.log 2>&1 &
    sleep 3
    echo "✅ 原版服务已启动"
fi
echo ""

# 4. 重启Backend
echo "4️⃣  重启Backend服务..."
cd /workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2

pkill -f "python.*backend.*app.py"
sleep 2

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
echo "   - 原版LLM: http://localhost:8610 (正在运行)"
echo "   - Backend: http://localhost:8203 (调用8610)"
echo ""
echo "🧪 验证方式:"
echo "   cd /workspace/murphy/capstone-project-25t3-9900-virtual-tutor-phase-2/llm"
echo "   python compare_latency.py --check"
echo ""

