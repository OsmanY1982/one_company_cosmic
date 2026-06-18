"""
修改密码对话框 — 通用（管理员和注册用户均可使用）
宇宙主题风格
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient

from modules.auth.auth_service import AuthService

# ── 配色（沿用 AdminLoginDialog 体系） ──
TEXT_PRIMARY = "#ddeeff"
TEXT_MUTED = "#667788"
BORDER_COLOR = "rgba(80, 120, 180, 50)"
INPUT_BG = "rgba(8, 12, 22, 230)"


class ChangePasswordDialog(QDialog):
    """修改密码对话框"""

    def __init__(self, username: str, role: str, parent=None):
        super().__init__(parent)
        self._username = username
        self._role = role
        role_label = "指挥官" if role == "admin" else "船员"
        self.setWindowTitle(f"修改密码 · {role_label}模式")
        self.setFixedSize(400, 350)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowTitleHint)

        self._auth = AuthService()
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(14, 18, 30, 255), stop:1 rgba(10, 14, 24, 255));
                border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
            }}
            QLabel {{ background: transparent; }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(36, 24, 36, 20)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("修改通行密钥")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "color: #ccddf0; font-size: 18px; font-weight: 800; letter-spacing: 4px;"
        )
        layout.addWidget(title)

        sub = QLabel(f"当前账号: {self._username}")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; letter-spacing: 2px;")
        layout.addWidget(sub)

        layout.addSpacing(4)

        # 分隔线
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            f"stop:0 transparent, stop:0.5 rgba(80, 120, 180, 60), "
            f"stop:1 transparent); border: none;"
        )
        layout.addWidget(divider)

        # ── 旧密码 ──
        layout.addWidget(self._make_label("当前密码"))
        self._old_pwd = self._make_input("输入当前密码")
        layout.addWidget(self._old_pwd)

        # ── 新密码 ──
        layout.addWidget(self._make_label("新密码"))
        self._new_pwd = self._make_input("输入新密码（至少4个字符）")
        layout.addWidget(self._new_pwd)

        # ── 确认新密码 ──
        layout.addWidget(self._make_label("确认新密码"))
        self._confirm_pwd = self._make_input("再次输入新密码")
        self._confirm_pwd.returnPressed.connect(self._do_change)
        layout.addWidget(self._confirm_pwd)

        layout.addSpacing(6)

        # ── 确认按钮 ──
        self._btn = QPushButton("更新密钥")
        self._btn.setCursor(Qt.PointingHandCursor)
        self._btn.setFixedHeight(38)
        self._btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(60, 85, 120, 220), stop:1 rgba(35, 50, 75, 220));
                color: #ddeeff;
                border: 1px solid rgba(80, 120, 180, 80);
                border-radius: 19px;
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 6px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(80, 110, 155, 240), stop:1 rgba(50, 70, 100, 240));
                border: 1px solid rgba(0, 180, 255, 120);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 45, 70, 220), stop:1 rgba(20, 30, 50, 220));
            }}
        """)
        self._btn.clicked.connect(self._do_change)
        layout.addWidget(self._btn)

        # ── 取消 ──
        cancel_btn = QPushButton("取 消")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_MUTED};
                border: none;
                font-size: 11px;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{ color: #99aabb; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn, alignment=Qt.AlignCenter)

    def _make_label(self, text):
        label = QLabel(text)
        label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; padding-left: 4px;")
        return label

    def _make_input(self, placeholder):
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setEchoMode(QLineEdit.Password)
        inp.setAlignment(Qt.AlignCenter)
        inp.setStyleSheet(f"""
            QLineEdit {{
                background: {INPUT_BG};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 9px 16px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid rgba(0, 180, 255, 160);
                background: rgba(10, 15, 26, 240);
            }}
        """)
        return inp

    def _do_change(self):
        old = self._old_pwd.text().strip()
        new = self._new_pwd.text().strip()
        confirm = self._confirm_pwd.text().strip()

        if not old or not new or not confirm:
            QMessageBox.warning(self, "输入不完整", "请填写所有密码字段")
            return
        if new != confirm:
            QMessageBox.warning(self, "密码不匹配", "两次输入的新密码不一致")
            return

        ok, msg = self._auth.change_password(self._username, old, new)
        if ok:
            QMessageBox.information(self, "修改成功", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "修改失败", msg)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        g = QLinearGradient(0, 0, w, 0)
        g.setColorAt(0, QColor(0, 0, 0, 0))
        g.setColorAt(0.5, QColor(0, 140, 220, 30))
        g.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(QPen(QBrush(g), 1))
        painter.drawLine(36, 1, w - 36, 1)
        painter.end()
