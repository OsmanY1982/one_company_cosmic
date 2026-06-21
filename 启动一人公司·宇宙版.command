#!/bin/bash
# 停掉所有旧实例
launchctl unload ~/Library/LaunchAgents/com.iqra.one-company.plist 2>/dev/null
screen -X -S iqra quit 2>/dev/null
pkill -f "python.*main.py" 2>/dev/null
sleep 1

# 设置环境
export QT_PLUGIN_PATH=/Users/opc/Library/Python/3.9/lib/python/site-packages/PyQt5/Qt5/plugins
export DYLD_FRAMEWORK_PATH=/Users/opc/Library/Python/3.9/lib/python/site-packages/PyQt5/Qt5/lib
cd "/Volumes/D盘工作区/一人公司宇宙版/one_company_cosmic"

# 用 screen 启动（继承终端麦克风权限）
screen -dmS iqra /usr/bin/python3 main.py
if [ $? -eq 0 ]; then
    echo "一人公司·宇宙版 已启动"
else
    echo "启动失败，请检查日志"
    read -p "按回车关闭..."
fi
