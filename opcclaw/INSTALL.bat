@echo off
title OPCclaw-Hermes 同步安装器 v1.0
chcp 65001 >nul

echo.
echo 🚀 OPCclaw-Hermes 三地同步安装器 v1.0
echo =====================================
echo.

:: 检查权威源
if not exist "D:\\one_company_desktop\\opcclaw\\openclaw_adapter.py" (
    echo ❌ 错误：D:\\one_company_desktop\\opcclaw\\ 不存在或不完整。
    pause
    exit /b 1
)

:: 注入 hermes-agent-source
echo [1/3] 注入 D:\\hermes-agent-source...
if exist "D:\\hermes-agent-source\\hermes_bootstrap.py" (
    echo    → 已存在，跳过创建
) else (
    echo import sys > "D:\\hermes-agent-source\\hermes_bootstrap.py"
    echo sys.path.insert(0, r'D:\\one_company_desktop\\opcclaw') >> "D:\\hermes-agent-source\\hermes_bootstrap.py"
    echo    → 已创建 hermes_bootstrap.py
)

:: 注入 D:\\one_company_desktop\\hermes
echo [2/3] 注入 D:\\one_company_desktop\\hermes...
if exist "D:\\one_company_desktop\\hermes\\hermes_bootstrap.py" (
    echo    → 已存在，跳过创建
) else (
    echo import sys > "D:\\one_company_desktop\\hermes\\hermes_bootstrap.py"
    echo sys.path.insert(0, r'D:\\one_company_desktop\\opcclaw') >> "D:\\one_company_desktop\\hermes\\hermes_bootstrap.py"
    echo    → 已创建 hermes_bootstrap.py
)

:: 注入 registry.py 补铁
echo [3/3] 注入 tools/registry.py 补铁...
set "REG_PATH=D:\\hermes-agent-source\\tools\\registry.py"
if exist "%REG_PATH%" (
    findstr /c:"OPCclaw business tools" "%REG_PATH%" >nul
    if %errorlevel% equ 0 (
        echo    → 已打补铁，跳过
    ) else (
        echo. >> "%REG_PATH%"
        echo # OPCclaw business tools (auto-synced) >> "%REG_PATH%"
        echo try: >> "%REG_PATH%"
        echo     from opcclaw.tools.business_tools import register_business_tools >> "%REG_PATH%"
        echo     register_business_tools(registry, data_dir="D:/one_company_desktop/data") >> "%REG_PATH%"
        echo except ImportError as e: >> "%REG_PATH%"
        echo     pass  # opcclaw not available, skip silently >> "%REG_PATH%"
        echo    → 已追加 registry.py 补铁
    )
) else (
    echo ❌ 错误：D:\\hermes-agent-source\\tools\\registry.py 未找到。
    pause
    exit /b 1
)

echo.
echo ✅ 安装完成！三地同步已就绪。
echo    - PyQt5：启动 main.py，点击「双AI智能协作」按钮
echo    - Hermes CLI：进入 D:\\hermes-agent-source，运行 python cli.py
echo    - 守护进程：可运行 sync_guardian.py（后台监控）
echo.
pause