#!/bin/bash
# ──────────────────────────────────────────────
# 悬浮星球守护进程 · 控制面板
# 首次运行时请在弹出的权限对话框中选择"允许"以启用语音唤醒
# ──────────────────────────────────────────────

PLIST_LABEL="com.opcclaw.planet-daemon"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_LABEL}.plist"
LOG_FILE="/tmp/planet_daemon.log"
PROJECT_DIR="/Volumes/D盘工作区/一人公司/one_company_cosmic"
PYTHON="/usr/bin/python3"

cd "$PROJECT_DIR" || { echo "项目目录不存在"; read -n 1 -s; exit 1; }

echo "============================================"
echo "  悬浮星球守护进程 · 控制面板"
echo "============================================"
echo ""

# 检查二进制
if [ ! -f "./MicCapture.app/Contents/MacOS/mic_capture_v2" ]; then
    echo "[ERROR] MicCapture.app/mic_capture_v2 未找到"
    read -n 1 -s
    exit 1
fi

# 显示状态
PID=$(ps aux | grep "planet_daemon.py" | grep -v grep | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "[状态] 运行中 (PID=$PID)"
else
    echo "[状态] 已停止"
fi

echo ""
echo "  1) 启动守护进程（含语音唤醒）"
echo "  2) 仅启动守护进程（无语音）"
echo "  3) 停止守护进程"
echo "  4) 查看日志"
echo "  5) 开机自启"
echo "  6) 取消开机自启"
echo "  0) 退出"
echo ""
read -p " 选择: " CHOICE

case $CHOICE in
    1)
        # 停止旧进程
        launchctl unload "$PLIST_PATH" 2>/dev/null
        [ -n "$PID" ] && kill "$PID" 2>/dev/null
        sleep 1

        # 启动：mic_capture_v2（16000Hz）管道录音 → python 守护进程
        echo "[1/1] 正在启动守护进程（含语音唤醒）..."
        echo "      首次运行会弹出麦克风权限对话框，请选择「允许」"
        export STT_STDIN_AUDIO=1
        nohup ./MicCapture.app/Contents/MacOS/mic_capture_v2 2>/tmp/mic_capture_err.log | nohup "$PYTHON" planet_daemon.py >> "$LOG_FILE" 2>&1 &
        DAEMON_PID=$!
        echo "$DAEMON_PID" > /tmp/planet_daemon.pid
        echo "[OK] 守护进程已启动 (PID=$DAEMON_PID)"
        echo "[OK] 关闭本窗口不影响守护进程运行"
        ;;

    2)
        launchctl unload "$PLIST_PATH" 2>/dev/null
        [ -n "$PID" ] && kill "$PID" 2>/dev/null
        sleep 1
        echo "正在启动守护进程（离线模式）..."
        nohup "$PYTHON" planet_daemon.py >> "$LOG_FILE" 2>&1 &
        DAEMON_PID=$!
        echo "$DAEMON_PID" > /tmp/planet_daemon.pid
        echo "[OK] 守护进程已启动 (PID=$DAEMON_PID)"
        ;;

    3)
        launchctl unload "$PLIST_PATH" 2>/dev/null
        [ -n "$PID" ] && kill "$PID" 2>/dev/null
        pkill -f "mic_capture" 2>/dev/null
        echo "[OK] 守护进程已停止"
        ;;

    4)
        echo ""
        echo "======== 最近 30 行 ========"
        tail -30 "$LOG_FILE" 2>/dev/null
        echo "============================"
        ;;

    5)
        if [ -f "$PLIST_PATH" ]; then
            launchctl load "$PLIST_PATH" 2>/dev/null
            echo "[OK] 已启用开机自启"
        else
            echo "[ERROR] LaunchAgent 配置文件不存在，请联系管理员"
        fi
        ;;

    6)
        launchctl unload "$PLIST_PATH" 2>/dev/null
        echo "[OK] 已取消开机自启"
        ;;

    0)
        echo "再见。"
        exit 0
        ;;

    *)
        echo "无效选择"
        ;;
esac

echo ""
echo "  日志: tail -f $LOG_FILE"
echo ""

# 如果选择了启动，让窗口保持2秒再关
if [ "$CHOICE" = "1" ] || [ "$CHOICE" = "2" ]; then
    sleep 2
else
    read -p "按任意键关闭..." -n 1 -s
fi
