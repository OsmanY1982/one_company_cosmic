# `opcclaw/modules/login_dialog.py`

> 路径：`opcclaw/modules/login_dialog.py` | 行数：346


---


```python
"""
OPCclaw 登录对话框
"""

import os
import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
    QMessageBox, QFrame, QFont
)
from PyQt5.QtCore import Qt, pyqtSignal

from opcclaw.core.secure_storage import SecureStorage

from ._shared import COLORS


class LoginDialog(QDialog):
    """OPCclaw 登录 - 使用一人公司注册账号"""

    login_success = pyqtSignal(dict)  # {username, role, ...}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OPCclaw - 登录")
        self.setFixedSize(400, 490)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {COLORS['card']}; }}
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(16)

        # Logo / 标题
        title = QLabel("OPCclaw")
        title.setFont(QFont("PingFang SC", 26, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("一人公司 AI 助手 · 登录")
        subtitle.setFont(QFont("PingFang SC", 12))
        subtitle.setStyleSheet(f"color: {COLORS['text_light']};")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        layout.addSpacing(8)

        # 账号
        self.account_input = QLineEdit()
        self.account_input.setPlaceholderText("请输入一人公司注册账号")
        self.account_input.setMinimumHeight(42)
        self.account_input.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 14px;
                background: {COLORS['input_bg']};
            }}
            QLineEdit:focus {{ border-color: {COLORS['primary']}; background: white; }}
        """)
        layout.addWidget(self.account_input)

        # 密码
        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText("请输入密码")
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setMinimumHeight(42)
        self.pwd_input.setStyleSheet(self.account_input.styleSheet())
        self.pwd_input.returnPressed.connect(self._do_login)
        layout.addWidget(self.pwd_input)

        # 登录按钮
        self.login_btn = QPushButton("登 录")
        self.login_btn.setMinimumHeight(44)
        self.login_btn.setFont(QFont("PingFang SC", 14, QFont.Bold))
        self.login_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{ background: {COLORS['primary_hover']}; }}
            QPushButton:disabled {{ background: #BDC3C7; }}
        """)
        self.login_btn.clicked.connect(self._do_login)
        layout.addWidget(self.login_btn)

        # 注册提示
        hint = QLabel("没有账号？请在一人公司 APP 注册")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        layout.addWidget(hint)

        layout.addSpacing(6)

        # ── 分隔线 ──
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(sep)
        layout.addSpacing(8)

        # 👤 管理员登录
        admin_btn = QPushButton("👤 管理员登录")
        admin_btn.setMinimumHeight(34)
        admin_btn.setFont(QFont("PingFang SC", 11))
        admin_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['primary']};
                border: 1px solid {COLORS['primary']};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {COLORS['primary']};
                color: white;
            }}
        """)
        admin_btn.clicked.connect(self._show_admin_login)
        layout.addWidget(admin_btn)

        layout.addStretch()

    def _do_login(self):
        account = self.account_input.text().strip()
        pwd = self.pwd_input.text().strip()

        if not account or not pwd:
            QMessageBox.warning(self, "提示", "账号密码不能为空")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("登录中...")

        try:
            # 添加一人公司路径到 sys.path, 确保能导入 AuthService
            one_company_root = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            )
            if one_company_root not in sys.path:
                sys.path.insert(0, one_company_root)

            from modules.login.service.auth_service import AuthService
            auth = AuthService()
            ok, msg = auth.login(account, pwd)

            if ok:
                self.login_success.emit({
                    "username": account,
                    "role": "user",
                    "message": msg,
                })
                self.accept()
            else:
                QMessageBox.warning(self, "登录失败", msg)
                self.login_btn.setEnabled(True)
                self.login_btn.setText("登 录")
        except ImportError as e:
            QMessageBox.warning(
                self, "错误",
                f"无法加载一人公司认证模块: {e}\\n请确保一人公司系统已正确安装。"
            )
            self.login_btn.setEnabled(True)
            self.login_btn.setText("登 录")
        except Exception as e:
            QMessageBox.critical(self, "异常", f"登录过程出错: {e}")
            self.login_btn.setEnabled(True)
            self.login_btn.setText("登 录")

    def _show_admin_login(self):
        """显示管理员登录对话框（首次运行会强制设置管理员密码）"""
        # 首次运行检测
        storage = SecureStorage()
        if not storage.is_admin_configured():
            self._force_set_admin_password()
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("管理员登录")
        dlg.setFixedSize(340, 260)
        dlg.setStyleSheet(f"QDialog {{ background-color: {COLORS['card']}; }}")

        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setContentsMargins(28, 24, 28, 24)
        dlg_layout.setSpacing(14)

        dlg_title = QLabel("🔑 管理员登录")
        dlg_title.setFont(QFont("PingFang SC", 16, QFont.Bold))
        dlg_title.setStyleSheet(f"color: {COLORS['primary']};")
        dlg_title.setAlignment(Qt.AlignCenter)
        dlg_layout.addWidget(dlg_title)

        dlg_user = QLineEdit()
        dlg_user.setPlaceholderText("管理员账号")
        dlg_user.setMinimumHeight(38)
        dlg_user.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {COLORS['primary']}; }}
        """)
        dlg_layout.addWidget(dlg_user)

        dlg_pwd = QLineEdit()
        dlg_pwd.setPlaceholderText("管理员密码")
        dlg_pwd.setEchoMode(QLineEdit.Password)
        dlg_pwd.setMinimumHeight(38)
        dlg_pwd.setStyleSheet(dlg_user.styleSheet())
        dlg_pwd.returnPressed.connect(
            lambda: self._do_admin_auth(dlg, dlg_user.text().strip(), dlg_pwd.text().strip())
        )
        dlg_layout.addWidget(dlg_pwd)

        dlg_btn = QPushButton("管理员登录")
        dlg_btn.setMinimumHeight(38)
        dlg_btn.setFont(QFont("PingFang SC", 12, QFont.Bold))
        dlg_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{ background: {COLORS['primary_hover']}; }}
        """)
        dlg_btn.clicked.connect(
            lambda: self._do_admin_auth(dlg, dlg_user.text().strip(), dlg_pwd.text().strip())
        )
        dlg_layout.addWidget(dlg_btn)

        dlg.exec_()

    def _do_admin_auth(self, dlg, username, pwd):
        """验证管理员身份（从DPAPI加密存储读取密码）"""
        storage = SecureStorage()
        
        # 检查是否配置了管理员密码
        if not storage.is_admin_configured():
            QMessageBox.warning(dlg, "未配置", "管理员密码未配置，请联系开发者")
            return
        
        # 验证密码
        stored_pwd = storage.get_admin_password()
        if username == "admin" and pwd == stored_pwd:
            self.login_success.emit({
                "username": "admin",
                "role": "admin",
                "message": "管理员登录成功",
            })
            dlg.accept()
            self.accept()
        else:
            QMessageBox.warning(dlg, "验证失败", "管理员账号或密码错误")

    def _force_set_admin_password(self):
        """强制设置管理员密码（首次运行时）"""
        dlg = QDialog(self)
        dlg.setWindowTitle("设置管理员密码")
        dlg.setFixedSize(360, 280)
        dlg.setStyleSheet(f"QDialog {{ background-color: {COLORS['card']}; }}")

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel("🔐 首次运行 - 设置管理员密码")
        title.setFont(QFont("PingFang SC", 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        hint = QLabel("请设置管理员密码，用于后续管理操作")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        layout.addWidget(hint)
        layout.addSpacing(8)

        pwd1 = QLineEdit()
        pwd1.setPlaceholderText("请输入管理员密码")
        pwd1.setEchoMode(QLineEdit.Password)
        pwd1.setMinimumHeight(38)
        pwd1.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {COLORS['primary']}; }}
        """)
        layout.addWidget(pwd1)

        pwd2 = QLineEdit()
        pwd2.setPlaceholderText("请再次输入密码")
        pwd2.setEchoMode(QLineEdit.Password)
        pwd2.setMinimumHeight(38)
        pwd2.setStyleSheet(pwd1.styleSheet())
        pwd2.returnPressed.connect(
            lambda: self._do_set_admin_pwd(dlg, pwd1.text().strip(), pwd2.text().strip())
        )
        layout.addWidget(pwd2)

        btn = QPushButton("设置密码")
        btn.setMinimumHeight(38)
        btn.setFont(QFont("PingFang SC", 12, QFont.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{ background: {COLORS['primary_hover']}; }}
        """)
        btn.clicked.connect(
            lambda: self._do_set_admin_pwd(dlg, pwd1.text().strip(), pwd2.text().strip())
        )
        layout.addWidget(btn)

        dlg.exec_()

    def _do_set_admin_pwd(self, dlg, pwd1, pwd2):
        """执行管理员密码设置"""
        if not pwd1 or not pwd2:
            QMessageBox.warning(dlg, "提示", "密码不能为空")
            return

        if pwd1 != pwd2:
            QMessageBox.warning(dlg, "提示", "两次输入的密码不一致")
            return

        if len(pwd1) < 6:
            QMessageBox.warning(dlg, "提示", "密码长度不能少于6位")
            return

        storage = SecureStorage()
        storage.set_admin_password(pwd1)
        QMessageBox.information(dlg, "成功", "管理员密码设置成功")
        dlg.accept()
```
