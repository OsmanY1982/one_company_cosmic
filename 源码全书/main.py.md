# `main.py`

> 路径：`main.py` | 行数：61


---


```python
"""
一人公司 · 宇宙版
启动入口
"""
import sys
import os
import traceback
import threading
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

# ── 按需安装核心依赖（首次运行自动触发）──
from deps.install_deps import ensure_core_deps
ensure_core_deps()

# ── 全局异常捕获 ──
LOG_DIR = os.path.join(os.path.dirname(__file__), "log")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "crash.log"),
    level=logging.ERROR,
    format="%(asctime)s [%(threadName)s] %(message)s",
    encoding="utf-8"
)

def _global_excepthook(exc_type, exc_value, exc_tb):
    """捕获主线程未处理异常，记录日志后显示错误对话框"""
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logging.error(f"未捕获异常:\n{tb_str}")

    # 仅在 QApplication 已初始化时弹窗
    from PyQt5.QtWidgets import QApplication, QMessageBox
    app = QApplication.instance()
    if app:
        QMessageBox.critical(None, "系统错误",
            f"发生未处理的异常:\n\n{exc_value}\n\n详细日志已写入 log/crash.log")

    sys.__excepthook__(exc_type, exc_value, exc_tb)

def _thread_excepthook(args):
    """捕获子线程未处理异常"""
    tb_str = "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
    logging.error(f"子线程未捕获异常:\n{tb_str}")

sys.excepthook = _global_excepthook
threading.excepthook = _thread_excepthook

from PyQt5.QtWidgets import QApplication
from modules.auth.login_window import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    win = LoginWindow()
    win.show()

    sys.exit(app.exec_())
```
