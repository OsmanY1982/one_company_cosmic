#!/bin/bash
# 悬浮球守护进程独立启动脚本

pkill -f planet_daemon 2>/dev/null
rm -f /tmp/opcclaw_floating_planet.pid
sleep 0.5

export QT_PLUGIN_PATH=/Users/opc/Library/Python/3.9/lib/python/site-packages/PyQt5/Qt5/plugins
export DYLD_FRAMEWORK_PATH=/Users/opc/Library/Python/3.9/lib/python/site-packages/PyQt5/Qt5/lib
cd "/Volumes/D盘工作区/一人公司宇宙版/one_company_cosmic"

nohup /usr/bin/python3 planet_daemon.py > /dev/null 2>&1 &

sleep 1
if pgrep -f planet_daemon > /dev/null; then
    PID=$(pgrep -f planet_daemon)
    echo "悬浮球已启动 (PID $PID)"
else
    echo "启动失败，请检查 /Volumes/D盘工作区/一人公司宇宙版/one_company_cosmic/planet_daemon.py"
    read -p "按回车关闭..."
fi
