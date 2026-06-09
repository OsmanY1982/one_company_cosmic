"""
管理员入口 — 独立登录对话框
深色金属风格，预设管理员账号 admin/admin
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QLinearGradient, QFont, QPainterPath
)

from modules.auth.auth_service import AuthService, ADMIN_USERNAME


# ── 配色 ──
DARK_METAL_BG = QColor(14, 18, 30)
BORDER_COLOR = "rgba(80, 120, 180, 50)"
ACCENT_STEEL = "rgba(70, 90, 120, 200)"
INPUT_BG = "rgba(8, 12, 22, 230)"
TEXT_PRIMARY = "#ddeeff"
TEXT_MUTED = "#667788"
GLOW_COLOR = QColor(0, 160, 240)


class AdminLoginDialog(QDialog):
    """管理员登录对话框 — 深空金属风"""

    def __init__(self, on_success=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("管理员入口 · 指挥舱")
        self.setFixedSize(420, 380)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowTitleHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        self._on_success = on_success
        self._auth = AuthService()

        self._build_ui()
        self._apply_dark_style()

    def _build_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(14, 18, 30, 255), stop:1 rgba(10, 14, 24, 255));
                border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
            }}
            QLabel {{
                background: transparent;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(40, 30, 40, 28)
        layout.setAlignment(Qt.AlignCenter)

        # ── 盾牌图标占位 ──
        icon_label = QLabel("COMMAND")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(
            "color: #8899bb; font-size: 11px; font-weight: 700; letter-spacing: 8px;"
        )
        layout.addWidget(icon_label)

        # ── 标题 ──
        title = QLabel("管理员指挥舱")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "color: #ccddf0; font-size: 18px; font-weight: 800; letter-spacing: 4px;"
        )
        layout.addWidget(title)

        sub = QLabel("仅限最高权限者登录")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; letter-spacing: 2px;")
        layout.addWidget(sub)

        layout.addSpacing(6)

        # ── 分隔线 ──
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                              f"stop:0 transparent, stop:0.5 rgba(80, 120, 180, 60), "
                              f"stop:1 transparent); border: none;")
        layout.addWidget(divider)

        layout.addSpacing(4)

        # ── 账号 ──
        user_label = QLabel("指挥官代号")
        user_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; padding-left: 4px;")
        layout.addWidget(user_label)

        self._user_input = QLineEdit()
        self._user_input.setPlaceholderText("admin")
        self._user_input.setText("admin")
        self._user_input.setAlignment(Qt.AlignCenter)
        self._user_input.setStyleSheet(f"""
            QLineEdit {{
                background: {INPUT_BG};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid rgba(0, 180, 255, 160);
                background: rgba(10, 15, 26, 240);
            }}
        """)
        layout.addWidget(self._user_input)

        # ── 密码 ──
        pwd_label = QLabel("通行密钥")
        pwd_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; padding-left: 4px;")
        layout.addWidget(pwd_label)

        self._pwd_input = QLineEdit()
        self._pwd_input.setPlaceholderText("••••••••")
        self._pwd_input.setEchoMode(QLineEdit.Password)
        self._pwd_input.setAlignment(Qt.AlignCenter)
        self._pwd_input.setStyleSheet(f"""
            QLineEdit {{
                background: {INPUT_BG};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid rgba(0, 180, 255, 160);
                background: rgba(10, 15, 26, 240);
            }}
        """)
        self._pwd_input.returnPressed.connect(self._do_login)
        layout.addWidget(self._pwd_input)

        layout.addSpacing(8)

        # ── 登录按钮 ──
        self._login_btn = QPushButton("进入指挥舱")
        self._login_btn.setCursor(Qt.PointingHandCursor)
        self._login_btn.setFixedHeight(40)
        self._login_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(60, 85, 120, 220), stop:1 rgba(35, 50, 75, 220));
                color: #ddeeff;
                border: 1px solid rgba(80, 120, 180, 80);
                border-radius: 20px;
                font-size: 14px;
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
        self._login_btn.clicked.connect(self._do_login)
        layout.addWidget(self._login_btn)

        # ── 取消 ──
        cancel_btn = QPushButton("返回登舱口")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_MUTED};
                border: none;
                font-size: 11px;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                color: #99aabb;
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn, alignment=Qt.AlignCenter)

    def _apply_dark_style(self):
        pass  # 样式已通过 setStyleSheet 在 _build_ui 中设置

    def _do_login(self):
        username = self._user_input.text().strip()
        password = self._pwd_input.text().strip()

        if not password:
            QMessageBox.warning(self, "登录失败", "请输入通行密钥")
            return

        result = self._auth.login(username, password)
        if result["ok"] and result["user"]["role"] == "admin":
            self.accept()
            if self._on_success:
                self._on_success()
        else:
            QMessageBox.warning(self, "认证失败", "指挥官代号或通行密钥错误，或权限不足")

    def paintEvent(self, event):
        """装饰辉光"""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 顶部辉光线
        w = self.width()
        g = QLinearGradient(0, 0, w, 0)
        g.setColorAt(0, QColor(0, 0, 0, 0))
        g.setColorAt(0.5, QColor(0, 140, 220, 30))
        g.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(QPen(QBrush(g), 1))
        painter.drawLine(40, 1, w - 40, 1)

        painter.end()