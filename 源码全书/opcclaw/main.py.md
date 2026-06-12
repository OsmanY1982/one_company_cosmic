# `opcclaw/main.py`

> 路径：`opcclaw/main.py` | 行数：116


---


```python
"""
OPCclaw - 独立启动入口 (v2)
===========================

双击运行或在终端执行:
    python main.py

依赖: PyQt5 (一人公司项目已安装)
"""

import sys
import os

# 直接将 opcclaw/添加到 path（最简单高效）
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# 把 opcclaw/ 本身加入 path，让 opcclaw.core 能正确解析
sys.path.insert(0, os.path.dirname(PROJECT_ROOT))
# 同时把 opcclaw/ 目录本身加入，支持 modules/ 直接导入
sys.path.insert(0, PROJECT_ROOT)

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

# 直接 import modules/
from modules.chat_window import ChatWindow
from core import opcclaw_logging as logging_module
from core.config_validator import ConfigValidator


def show_startup_message(msg):
    """在控制台显示启动信息"""
    print(f"[OPCclaw] {msg}")


def main():
    # 1. 初始化日志系统 (必须在创建 App 之前)
    try:
        logging_module.install()  # 设置全局异常处理器
        logger = logging_module.get_logger("main")
        logger.info("Initializing OPCclaw...")
    except Exception as e:
        # 如果日志模块本身崩了，至少打印到控制台
        print(f"[OPCclaw] [ERROR] Failed to init logging: {e}")
        def fallback_hook(exctype, value, tb):
            print(f"[OPCclaw] FATAL ERROR: {value}")
            sys.__excepthook__(exctype, value, tb)
        sys.excepthook = fallback_hook

    # 2. 创建应用实例 (必须最先实例化)
    app = QApplication(sys.argv)
    
    # 3. 开启高 DPI 支持 (实例化后设置才生效)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app.setStyle("Fusion")
    app.setFont(QFont("PingFang SC", 10))
    app.setApplicationName("OPCclaw")

    # 4. 配置校验
    config_path = os.path.join(PROJECT_ROOT, "data", "opcclaw_config.json")
    try:
        validator = ConfigValidator(config_path)
        result = validator.validate()
        
        if not result.ok:
            # 尝试自动修复
            logger.warning(f"Config validation failed, attempting auto-fix: {result.summary()}")
            fix_result = validator.apply_fixes()
            if fix_result.fixes:
                logger.info(f"Auto-fixed config: {fix_result.summary()}")
            else:
                logger.error("Failed to auto-fix config.")
        elif result.warnings:
            for w in result.warnings:
                logger.warning(w)
        else:
            logger.info("Configuration valid.")
    except Exception as e:
        logger.critical(f"Config handling error: {e}")

    # 5. 全局未捕获异常处理：防止程序静默崩溃
    def exception_hook(exctype, value, traceback):
        logger.critical("Uncaught exception", exc_info=(exctype, value, traceback))
        print(f"ERROR: {''.join(traceback)}")
        
        # 弹窗提示用户（防止后台运行无声崩溃）
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("OPCclaw 遇到严重错误")
        msg_box.setText(f"程序发生致命错误:\n{str(value)}\n\n日志已保存。")
        msg_box.exec_()
        
        sys.__excepthook__(exctype, value, traceback)
    sys.excepthook = exception_hook

    # 6. 启动主窗口
    show_startup_message("Starting GUI...")
    try:
        win = ChatWindow()
        win.setWindowTitle("OPCclaw - 一人公司 AI 助手")
        win.resize(800, 900)  # 稍微调大窗口，适配大屏
        win.show()
    except Exception as e:
        show_startup_message(f"Failed to load window: {e}")
        QMessageBox.critical(None, "启动失败", f"无法加载主界面:\n{e}\n\n请检查 PyQt5 是否正确安装。")
        return

    show_startup_message("Ready.")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

```
