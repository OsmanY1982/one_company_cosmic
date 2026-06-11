@echo off
chcp 65001 >nul
echo ════════════════════════════════════════════
echo OPCclaw HTTP API Server - 安装脚本
echo ════════════════════════════════════════════
echo.

echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python 已安装

echo.
echo [2/4] 安装 Playwright...
pip install playwright -q
if errorlevel 1 (
    echo ❌ 安装 Playwright 失败
    pause
    exit /b 1
)
echo ✅ Playwright 已安装

echo.
echo [3/4] 安装 Chromium 浏览器...
echo ⏳ 这可能需要几分钟，请耐心等待...
playwright install chromium
if errorlevel 1 (
    echo ❌ 安装 Chromium 失败
    pause
    exit /b 1
)
echo ✅ Chromium 已安装

echo.
echo [4/4] 检查 Flask...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo ⏳ 安装 Flask...
    pip install flask -q
    echo ✅ Flask 已安装
) else (
    echo ✅ Flask 已安装
)

echo.
echo ════════════════════════════════════════════
echo ✅ 安装完成！
echo ════════════════════════════════════════════
echo.
echo 启动服务器:
echo   python D:/one_company_desktop/opcclaw/skills/flybook_bot/server.py
echo.
echo 运行测试:
echo   python D:/one_company_desktop/opcclaw/skills/flybook_bot/test_server.py
echo.
echo 查看文档:
echo   D:/one_company_desktop/opcclaw/skills/flybook_bot/README.md
echo.
pause
