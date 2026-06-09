"""
一人公司 · 宇宙版
启动入口
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PyQt5.QtWidgets import QApplication
from modules.auth.login_window import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    win = LoginWindow()
    win.show()

    sys.exit(app.exec_())