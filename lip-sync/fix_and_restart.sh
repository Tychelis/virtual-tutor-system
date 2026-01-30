#!/bin/bash

echo "========================================"
echo "清理并重启Avatar服务"
echo "========================================"
echo

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 步骤1: 显示当前运行的进程
echo "【步骤1】当前运行的app.py进程："
ps aux | grep "app.py" | grep -v grep
echo

# 步骤2: 杀掉所有app.py进程
echo "【步骤2】清理所有app.py进程..."
pkill -9 -f "app.py"
sleep 2

# 确认清理
REMAINING=$(ps aux | grep "app.py" | grep -v grep | wc -l)
if [ $REMAINING -eq 0 ]; then
    echo -e "${GREEN}✅ 所有旧进程已清理${NC}"
else
    echo -e "${YELLOW}⚠️  仍有 $REMAINING 个进程残留${NC}"
    ps aux | grep "app.py" | grep -v grep
fi
echo

# 步骤3: 等待端口释放
echo "【步骤3】等待端口8615释放..."
sleep 3

if netstat -tln | grep ":8615 " > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  端口8615仍被占用${NC}"
else
    echo -e "${GREEN}✅ 端口8615已释放${NC}"
fi
echo

# 步骤4: 通过API重新启动
echo "【步骤4】通过live_server API重新启动avatar..."
echo "发送请求到: http://localhost:8606/switch_avatar"
echo "参数: avatar_id=yongen, ref_file=ref_audio/complete_silence.wav"
echo

RESPONSE=$(curl -s -X POST "http://localhost:8606/switch_avatar?avatar_id=yongen&ref_file=ref_audio/complete_silence.wav")
echo "API响应:"
echo "$RESPONSE"
echo

# 步骤5: 等待服务启动
echo "【步骤5】等待服务启动（30秒）..."
for i in {1..30}; do
    if netstat -tln | grep ":8615 " > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 服务已启动！ (用时 ${i} 秒)${NC}"
        break
    fi
    echo -n "."
    sleep 1
done
echo

# 步骤6: 最终检查
echo "【步骤6】最终状态检查..."

# 检查进程
if ps aux | grep "app.py.*8615" | grep -v grep > /dev/null; then
    echo -e "${GREEN}✅ Avatar服务正在运行${NC}"
    ps aux | grep "app.py.*8615" | grep -v grep | head -2
else
    echo -e "${RED}❌ Avatar服务未运行${NC}"
fi
echo

# 检查端口
if netstat -tln | grep ":8615 " > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 端口8615正在监听${NC}"
else
    echo -e "${RED}❌ 端口8615未监听${NC}"
fi
echo

# 测试HTTP访问
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8615/webrtcapi.html)
if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ webrtcapi.html可以访问 (HTTP $HTTP_STATUS)${NC}"
else
    echo -e "${RED}❌ webrtcapi.html无法访问 (HTTP $HTTP_STATUS)${NC}"
fi
echo

echo "========================================"
echo "修复完成！"
echo "========================================"
echo
echo "【下一步操作】"
echo
echo "1. 在VSCode中配置端口转发："
echo "   - 按 Ctrl+Shift+P (Mac: Cmd+Shift+P)"
echo "   - 输入 'Forward a Port'"
echo "   - 输入端口号: 8615"
echo
echo "2. 或者查看VSCode底部的'PORTS'标签"
echo "   - 确认8615端口已转发"
echo "   - 如果没有，点击'+'号添加"
echo
echo "3. 在你的本地浏览器访问:"
echo "   http://localhost:8615/webrtcapi.html"
echo
echo "【故障排查】"
echo "如果仍然无法访问："
echo "  1. 检查VSCode的PORTS标签，8615端口状态"
echo "  2. 尝试删除并重新添加端口转发"
echo "  3. 重启VSCode Remote SSH连接"
echo "  4. 检查本地浏览器控制台错误(F12)"
echo
echo "========================================"






