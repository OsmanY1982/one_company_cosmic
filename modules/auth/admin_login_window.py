# -*- coding: utf-8 -*-
"""独立的管理员登录窗口 — 专业优化版
视觉亮点：暗色渐变背景 + 白色卡片面板 + 盾牌图标 + 现代化交互
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QCheckBox,
    QApplication, QInputDialog, QDialog, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, pyqtProperty, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor, QPalette, QLinearGradient, QPainter, QBrush
from core.paths import CONFIG_DIR, BASE_DIR
from core.app_state import app_state
import os
import hashlib as _hashlib, uuid as _uuid, platform as _platform

def get_machine_code():
    raw = f"{_platform.node()}-{_uuid.getnode()}"
    return _hashlib.sha256(raw.encode()).hexdigest()[:16]
import secrets, string
import json
import base64
from core.dark_theme import apply_dark_theme, BG_MAIN, BG_CARD, BG_INPUT, BTN_NORMAL, BTN_HOVER, BTN_PRESSED, TEXT_WHITE, TEXT_LIGHT, TEXT_MUTED, ACCENT, SUCCESS, WARNING, DANGER, BORDER, BORDER_LIGHT

SAVE_FILE = os.path.join(CONFIG_DIR, "admin_remember.json")
LOGO_FILE = os.path.join(BASE_DIR, "opc_logo.ico")
ADMIN_CONFIG = os.path.join(CONFIG_DIR, "admin.json")
_KEY_FILE = os.path.join(CONFIG_DIR, ".remember_key")

# 配色方案
COLORS = {
    "bg_gradient_start": "#0a0e27",      # 深黑蓝
    "bg_gradient_end": "#0d1140",        # 深海军蓝
    "card_bg": "#111936",
    "accent": "#1a237e",                 # 深蓝紫
    "accent_hover": "#283593",
    "accent_pressed": "#0d1642",
    "text_primary": "#ffffff",
    "text_secondary": "#e0e0e0",
    "text_muted": "#8899aa",
    "input_border": "#1a237e",
    "input_border_focus": "#00d4ff",
    "input_bg": "#1a1f3a",
    "divider": "#2a3378",
    "danger": "#ef4444",
    "danger_light": "#2a1215",
    "success": "#10b981",
    "warning": "#f59e0b",
}

# ── 密码加密工具（与 login_window.py 共用同一个密钥文件）──

def _get_encryption_key():
    """获取或生成本地加密密钥（机器绑定）"""
    if os.path.exists(_KEY_FILE):
        with open(_KEY_FILE, 'r') as f:
            return base64.b64decode(f.read().strip())
    key = secrets.token_bytes(32)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(_KEY_FILE, 'w') as f:
        f.write(base64.b64encode(key).decode())
    return key


def _encrypt_password(password: str) -> str:
    """XOR 加密密码（可逆，用于记住密码功能）"""
    key = _get_encryption_key()
    data = password.encode('utf-8')
    encrypted = bytes(data[i] ^ key[i % len(key)] for i in range(len(data)))
    return base64.b64encode(encrypted).decode()


def _decrypt_password(encoded: str) -> str:
    """解密密码"""
    key = _get_encryption_key()
    data = base64.b64decode(encoded)
    decrypted = bytes(data[i] ^ key[i % len(key)] for i in range(len(data)))
    return decrypted.decode('utf-8')


def _load_admin_config():
    if os.path.exists(ADMIN_CONFIG):
        try:
            with open(ADMIN_CONFIG, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_admin_config(data):
    os.makedirs(os.path.dirname(ADMIN_CONFIG), exist_ok=True)
    with open(ADMIN_CONFIG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)



def _hash_password(password: str) -> str:
    """密码哈希（优先bcrypt，降级SHA256）"""
    try:
        import bcrypt
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    except Exception:
        import hashlib
        return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _verify_password(password: str, stored_hash: str) -> bool:
    """验证密码（自动检测bcrypt/SHA256/明文兼容）"""
    if not stored_hash:
        return False
    # bcrypt ($2b$...)
    if stored_hash.startswith("$2"):
        try:
            import bcrypt
            return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
        except Exception:
            pass
    # SHA256 (64位hex)
    if len(stored_hash) == 64:
        try:
            import hashlib
            return hashlib.sha256(password.encode("utf-8")).hexdigest() == stored_hash
        except Exception:
            pass
    # 兼容：明文（过渡期）
    return password == stored_hash


class _GradientBackground(QWidget):
    """渐变背景容器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        apply_dark_theme(self)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor(COLORS["bg_gradient_start"]))
        gradient.setColorAt(1.0, QColor(COLORS["bg_gradient_end"]))
        painter.fillRect(self.rect(), QBrush(gradient))


class _CardPanel(QFrame):
    """白色卡片面板，带圆角和阴影"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("cardPanel")
        self.setStyleSheet(f"""
            #cardPanel {{
                background-color: {COLORS['card_bg']};
                border-radius: 16px;
            }}
        """)
        # 阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)


class _StyledInput(QLineEdit):
    """统一样式的输入框"""
    def __init__(self, placeholder="", echo_mode=None, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(44)
        self.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {COLORS['input_border']};
                border-radius: 10px;
                padding: 8px 16px;
                font-size: 14px;
                background: {COLORS['input_bg']};
                color: {COLORS['text_primary']};
            }}
            QLineEdit:focus {{
                border-color: {COLORS['input_border_focus']};
            }}
            QLineEdit:disabled {{
                background: #1a1a2e;
                color: {COLORS['text_muted']};
            }}
        """)
        if echo_mode is not None:
            self.setEchoMode(echo_mode)


class AdminLoginWindow(QMainWindow):
    MAX_ATTEMPTS = 5
    LOCKOUT_SECONDS = 30

    def __init__(self, on_success=None, parent=None):
        super().__init__(parent)
        apply_dark_theme(self)
        self.on_success = on_success
        self._login_attempts = 0
        self._lockout_remaining = 0
        self._lockout_timer = None
        
        if os.path.exists(LOGO_FILE):
            self.setWindowIcon(QIcon(LOGO_FILE))
        
        self.setWindowTitle("管理员登录 — 一人公司管理系统")
        self.setFixedSize(480, 620)
        self.setStyleSheet(f"background-color: {COLORS['bg_gradient_start']};")
        
        self._setup_ui()
        self._load_remember()

    def _setup_ui(self):
        """构建完整的现代化 UI"""
        # ── 渐变背景 ──
        bg = _GradientBackground(self)
        self.setCentralWidget(bg)
        
        # 主布局：垂直居中
        main_layout = QVBoxLayout(bg)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(40, 20, 40, 20)
        
        # ── 卡片面板 ──
        card = _CardPanel()
        card.setMaximumWidth(400)
        card.setMinimumWidth(380)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 36, 32, 32)
        card_layout.setSpacing(0)

        # ── 盾牌图标 ──
        shield_label = QLabel("🛡️")
        shield_label.setAlignment(Qt.AlignCenter)
        shield_label.setStyleSheet(f"font-size: 48px; background: transparent;")
        card_layout.addWidget(shield_label)
        card_layout.addSpacing(8)

        # ── 标题 ──
        title = QLabel("管理员登录")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("PingFang SC", 22, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        card_layout.addWidget(title)
        card_layout.addSpacing(6)

        # ── 副标题 ──
        subtitle = QLabel("安全认证 · 仅限管理员访问")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("PingFang SC", 10))
        subtitle.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(28)

        # ── 分割线 ──
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"background-color: {COLORS['divider']}; max-height: 1px;")
        card_layout.addWidget(divider)
        card_layout.addSpacing(24)

        # ── 账号字段（admin 固定，不可改）──
        user_label = QLabel("管理员账号")
        user_label.setFont(QFont("PingFang SC", 11, QFont.Bold))
        user_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; padding-left: 2px;")
        card_layout.addWidget(user_label)
        card_layout.addSpacing(8)
        
        user_container = QWidget()
        user_container.setStyleSheet("background: transparent;")
        user_hlayout = QHBoxLayout(user_container)
        user_hlayout.setContentsMargins(0, 0, 0, 0)
        user_hlayout.setSpacing(0)
        
        self.user_input = _StyledInput()
        self.user_input.setText("admin")
        self.user_input.setReadOnly(True)
        self.user_input.setMinimumHeight(44)
        user_hlayout.addWidget(self.user_input)
        
        # 管理员徽章
        badge = QLabel("👑 超级管理员")
        badge.setStyleSheet(f"""
            background-color: {COLORS['accent']}15;
            color: {COLORS['accent']};
            font-size: 11px;
            font-weight: bold;
            padding: 4px 10px;
            border-radius: 12px;
            margin-left: 10px;
        """)
        badge.setFixedHeight(28)
        user_hlayout.addWidget(badge)
        card_layout.addWidget(user_container)
        card_layout.addSpacing(18)

        # ── 密码字段 ──
        pwd_label = QLabel("管理员密码")
        pwd_label.setFont(QFont("PingFang SC", 11, QFont.Bold))
        pwd_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; padding-left: 2px;")
        card_layout.addWidget(pwd_label)
        card_layout.addSpacing(8)
        
        pwd_container = QWidget()
        pwd_container.setStyleSheet("background: transparent;")
        pwd_hlayout = QHBoxLayout(pwd_container)
        pwd_hlayout.setContentsMargins(0, 0, 0, 0)
        pwd_hlayout.setSpacing(0)
        
        self.pwd_input = _StyledInput("请输入管理员密码", QLineEdit.Password)
        self.pwd_input.returnPressed.connect(self._do_login)
        self.pwd_input.textChanged.connect(self._on_password_changed)
        pwd_hlayout.addWidget(self.pwd_input)
        
        # 显示/隐藏密码按钮
        self.eye_btn = QPushButton("👁")
        self.eye_btn.setFixedSize(36, 36)
        self.eye_btn.setCursor(Qt.PointingHandCursor)
        self.eye_btn.setToolTip("显示/隐藏密码")
        self.eye_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                font-size: 16px;
                margin-left: -40px;
                z-index: 10;
            }}
            QPushButton:hover {{ background: {COLORS['input_bg']}; border-radius: 8px; }}
        """)
        self.eye_btn.clicked.connect(self._toggle_password_visibility)
        pwd_hlayout.addWidget(self.eye_btn)
        card_layout.addWidget(pwd_container)
        card_layout.addSpacing(6)

        # ── Caps Lock 警告 ──
        self.caps_lock_warning = QLabel("⚠ 大写锁定已开启")
        self.caps_lock_warning.setStyleSheet(f"""
            color: {COLORS['warning']}; 
            font-size: 11px; 
            background: transparent; 
            padding-left: 4px;
        """)
        self.caps_lock_warning.setVisible(False)
        card_layout.addWidget(self.caps_lock_warning)

        # ── 错误提示 ──
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"""
            color: {COLORS['danger']}; 
            font-size: 12px; 
            background: {COLORS['danger_light']}; 
            padding: 8px 12px;
            border-radius: 8px;
        """)
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        card_layout.addSpacing(8)
        card_layout.addWidget(self.error_label)

        # ── 记住密码 ──
        remember_row = QWidget()
        remember_row.setStyleSheet("background: transparent;")
        remember_layout = QHBoxLayout(remember_row)
        remember_layout.setContentsMargins(0, 8, 0, 8)
        
        self.remember_checkbox = QCheckBox("记住密码（30天内有效）")
        self.remember_checkbox.setFont(QFont("PingFang SC", 10))
        self.remember_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS['text_secondary']};
                background: transparent;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border: 2px solid {COLORS['input_border']};
                border-radius: 4px;
                background: white;
            }}
            QCheckBox::indicator:checked {{
                background: {COLORS['accent']};
                border-color: {COLORS['accent']};
            }}
            QCheckBox::indicator:hover {{
                border-color: {COLORS['accent']};
            }}
        """)
        remember_layout.addWidget(self.remember_checkbox)
        remember_layout.addStretch()
        card_layout.addWidget(remember_row)

        # ── 登录按钮 ──
        self.btn_login = QPushButton("🔐 安全登录")
        self.btn_login.setMinimumHeight(48)
        self.btn_login.setFont(QFont("PingFang SC", 13, QFont.Bold))
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['accent']}, stop:1 {COLORS['accent_hover']});
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['accent_hover']}, stop:1 {COLORS['accent_pressed']});
            }}
            QPushButton:pressed {{
                background: {COLORS['accent_pressed']};
            }}
            QPushButton:disabled {{
                background: #cbd5e1;
                color: #94a3b8;
            }}
        """)
        self.btn_login.clicked.connect(self._do_login)
        card_layout.addWidget(self.btn_login)
        card_layout.addSpacing(10)

        # ── 返回用户登录 ──
        btn_back = QPushButton("← 返回用户登录")
        btn_back.setMinimumHeight(36)
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setFont(QFont("PingFang SC", 10))
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['accent']};
                border: none;
            }}
            QPushButton:hover {{
                color: {COLORS['accent_hover']};
                text-decoration: underline;
            }}
        """)
        btn_back.clicked.connect(self._go_back)
        card_layout.addWidget(btn_back)

        # ── 底部提示 ──
        card_layout.addSpacing(8)
        hint = QLabel("需要修改管理员密码？请在登录后的系统设置中操作")
        hint.setAlignment(Qt.AlignCenter)
        hint.setFont(QFont("PingFang SC", 9))
        hint.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent;")
        card_layout.addWidget(hint)

        main_layout.addWidget(card, alignment=Qt.AlignCenter)

        # ── 窗口底部版权 ──
        copyright_label = QLabel("© 2026 一人公司管理系统 · 安全连接 🔒")
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setFont(QFont("PingFang SC", 9))
        copyright_label.setStyleSheet(f"color: rgba(255,255,255,0.3); background: transparent;")
        main_layout.addWidget(copyright_label)

    def _on_password_changed(self, text):
        """密码变化时检查 Caps Lock"""
        # PyQt5 没有直接的 caps lock API，用平台判断
        import ctypes
        try:
            caps_state = ctypes.windll.user32.GetKeyState(0x14) & 0x0001
            self.caps_lock_warning.setVisible(bool(caps_state))
        except Exception:
            self.caps_lock_warning.setVisible(False)
        
        # 清除错误提示
        if self.error_label.isVisible():
            self.error_label.setVisible(False)

    def _toggle_password_visibility(self):
        """切换密码显示/隐藏"""
        if self.pwd_input.echoMode() == QLineEdit.Password:
            self.pwd_input.setEchoMode(QLineEdit.Normal)
            self.eye_btn.setText("🙈")
        else:
            self.pwd_input.setEchoMode(QLineEdit.Password)
            self.eye_btn.setText("👁")

    def _load_remember(self):
        """加载记住的密码"""
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, encoding='utf-8') as f:
                    data = json.load(f)
                if data.get('remember'):
                    pwd = data.get('password', '')
                    if pwd:
                        try:
                            self.pwd_input.setText(_decrypt_password(pwd))
                        except Exception:
                            pass
                    self.remember_checkbox.setChecked(True)
            except Exception:
                pass

    def _save_remember(self, pwd):
        """保存/清除记住的密码"""
        try:
            if self.remember_checkbox.isChecked():
                data = {
                    'remember': True,
                    'user_id': 'admin',
                    'password': _encrypt_password(pwd),
                    'saved_at': __import__('datetime').datetime.now().isoformat()
                }
            else:
                data = {'remember': False}
            os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
            with open(SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _do_login(self):
        """执行登录验证"""
        # 检查是否在锁定状态
        if self._lockout_remaining > 0:
            self._show_error(f"⏳ 登录已锁定，请等待 {self._lockout_remaining} 秒后再试")
            return

        pwd = self.pwd_input.text().strip()
        if not pwd:
            self._show_error("请输入管理员密码")
            self.pwd_input.setFocus()
            self._shake_widget(self.pwd_input)
            return

        cfg = _load_admin_config()
        
        # 首次运行：自动生成随机密码
        if not cfg.get("password"):
            # 生成 16 位随机密码
            import secrets, string
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(secrets.choice(chars) for _ in range(16))
            cfg["password"] = _hash_password(password)
            _save_admin_config(cfg)
            
            # 弹窗显示密码（仅一次）
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QApplication
            dlg = QDialog()
            dlg.setWindowTitle("管理员密码已生成")
            dlg.setFixedSize(420, 280)
            dlg.setModal(True)
            
            layout = QVBoxLayout(dlg)
            layout.setSpacing(12)
            
            info = QLabel("你的管理员密码已自动生成\n仅显示一次，请立即保存！")
            info.setWordWrap(True)
            info.setStyleSheet("font-size: 13px; padding: 8px; color: #e67e22; font-weight: bold;")
            layout.addWidget(info)
            
            pwd_display = QLineEdit(password)
            pwd_display.setReadOnly(True)
            pwd_display.setAlignment(Qt.AlignCenter)
            pwd_display.setStyleSheet("""
                QLineEdit {
                    font-size: 20px;
                    font-family: 'Menlo', 'Courier New', monospace;
                    letter-spacing: 2px;
                    padding: 12px;
                    background: #2c3e50;
                    color: #2ecc71;
                    border: 2px solid #2ecc71;
                    border-radius: 6px;
                }
            """)
            pwd_display.setMinimumHeight(50)
            layout.addWidget(pwd_display)
            
            btn_row = QHBoxLayout()
            
            copy_btn = QPushButton("复制密码")
            copy_btn.setMinimumHeight(38)
            def do_copy():
                QApplication.clipboard().setText(password)
                copy_btn.setText("✅ 已复制")
            copy_btn.clicked.connect(do_copy)
            btn_row.addWidget(copy_btn)
            
            ok_btn = QPushButton("我已保存")
            ok_btn.setMinimumHeight(38)
            ok_btn.clicked.connect(dlg.accept)
            btn_row.addWidget(ok_btn)
            
            layout.addLayout(btn_row)
            
            hint = QLabel("密码已安全存储（bcrypt加密）\n不会以明文形式保存")
            hint.setWordWrap(True)
            hint.setStyleSheet("font-size: 11px; color: #7f8c8d; padding: 4px;")
            layout.addWidget(hint)
            
            dlg.exec_()
        
        correct_pwd = cfg.get("password")

        if not _verify_password(pwd, correct_pwd):
            self._login_attempts += 1
            remaining = self.MAX_ATTEMPTS - self._login_attempts
            
            if remaining > 0:
                self._show_error(f"❌ 密码不正确（还剩 {remaining} 次尝试机会）")
            else:
                self._lockout_remaining = self.LOCKOUT_SECONDS
                self._show_error(f"🔒 尝试次数过多，已锁定 {self.LOCKOUT_SECONDS} 秒")
                self.btn_login.setEnabled(False)
                self._start_lockout_timer()
            
            self.pwd_input.clear()
            self.pwd_input.setFocus()
            self._shake_widget(self.btn_login)
            return

        # ── 登录成功 ──
        self._login_attempts = 0
        self.btn_login.setEnabled(False)
        # 直接跳转，不需要延迟
        self._proceed_login()

    def _proceed_login(self):
        """执行登录成功后的逻辑"""
        pwd = self.pwd_input.text().strip()
        
        # 注册云端会话
        session_token = None
        try:
            from core.supabase_client import CloudSession
            session_token = CloudSession.register_login(
                "admin", get_machine_code(),
                device_type=CloudSession.DEVICE_TYPE_DESKTOP
            )
        except Exception as e:
            QMessageBox.warning(self, "云端同步", f"云端会话注册失败：{e}\n将使用本地模式继续。")

        # 记住密码
        self._save_remember(pwd)

        # 写入登录状态
        app_state.login(
            user_id="admin",
            username="admin",
            role="admin",
            session_token=session_token,
            device_type="desktop"
        )

        # 跳转
        self._redirect_to_dashboard()

    def _show_error(self, msg):
        """显示错误提示（带动画）"""
        self.error_label.setText(msg)
        self.error_label.setVisible(True)
        # 3 秒后自动消失
        QTimer.singleShot(5000, lambda: self.error_label.setVisible(False))

    def _shake_widget(self, widget):
        """抖动动画（密码错误时）"""
        animation = QPropertyAnimation(widget, b"pos")
        original_pos = widget.pos()
        animation.setDuration(400)
        animation.setEasingCurve(QEasingCurve.OutElastic)
        animation.setLoopCount(2)
        
        # 左右抖动
        animation.setKeyValueAt(0.0, original_pos)
        animation.setKeyValueAt(0.1, original_pos + QPoint(-8, 0))
        animation.setKeyValueAt(0.2, original_pos + QPoint(8, 0))
        animation.setKeyValueAt(0.3, original_pos + QPoint(-6, 0))
        animation.setKeyValueAt(0.4, original_pos + QPoint(6, 0))
        animation.setKeyValueAt(0.5, original_pos + QPoint(-3, 0))
        animation.setKeyValueAt(0.6, original_pos + QPoint(3, 0))
        animation.setKeyValueAt(1.0, original_pos)
        
        animation.start()

    def _start_lockout_timer(self):
        """启动锁定倒计时"""
        self._lockout_timer = QTimer(self)
        self._lockout_timer.timeout.connect(self._tick_lockout)
        self._lockout_timer.start(1000)

    def _tick_lockout(self):
        """锁定倒计时"""
        self._lockout_remaining -= 1
        if self._lockout_remaining <= 0:
            self._lockout_timer.stop()
            self._lockout_timer = None
            self._login_attempts = 0
            self.btn_login.setEnabled(True)
            self.error_label.setVisible(False)
        else:
            self._show_error(f"🔒 登录已锁定，请等待 {self._lockout_remaining} 秒")

    def _redirect_to_dashboard(self):
        """跳转到主面板"""
        self.setVisible(False)
        if app_state._current_dashboard:
            try:
                app_state._current_dashboard.close()
            except Exception:
                pass
            app_state._current_dashboard = None
        
        try:
            from modules.dashboard.dashboard_window import DashboardWindow
            dash = DashboardWindow()
            app_state._current_dashboard = dash
            dash.show()
            dash.raise_()
            dash.activateWindow()
            self.close()
            if self.on_success:
                self.on_success()
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(None, "跳转失败", f"无法进入系统：\n{str(e)}")
            self.setVisible(True)
            self.btn_login.setEnabled(True)
            self.btn_login.setText("🔐 安全登录")

    def _go_back(self):
        """返回用户登录窗口"""
        self.close()
        if self.on_success:
            self.on_success()
