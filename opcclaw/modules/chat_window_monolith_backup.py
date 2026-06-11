"""
OPCclaw - AI Agent 对话窗口 (v3)
类似 QClaw 的对话框界面, 带侧栏配置面板。

功能:
- 💬 对话面板 — 流式聊天, 工具调用, 多轮对话
- 🔐 登录系统 — 使用一人公司注册账号, 可独立/嵌入
- ☁️ 云端模型 — 多供应商管理 (DeepSeek/OpenAI/Qwen/GLM...)
- 🖥️ 本地模型 — Ollama/LM Studio 连接
- 📚 技能管理 — 浏览/启用/禁用技能
- ⚙️ 通用设置 — 主题/自动保存/清除数据
"""

import os, sys, json, sqlite3, hashlib, secrets, string
from datetime import datetime
from typing import Optional


from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QFrame, QScrollArea, QApplication, QDialog,
    QFormLayout, QComboBox, QLineEdit, QMessageBox, QSizePolicy,
    QStackedWidget, QListWidget, QListWidgetItem, QTabWidget,
    QCheckBox, QSpinBox, QGroupBox, QSplitter,
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QEvent,
)
from PyQt5.QtGui import QFont, QColor, QPalette

# ── OPCclaw 核心 ──
from opcclaw.core.llm_backend import (
    BaseLLMBackend, BackendFactory, ProviderConfig,
    PROVIDER_TEMPLATES, get_available_models,
    list_all_providers, batch_scan_platforms,
)
from opcclaw.core.tool_registry import ToolRegistry
from opcclaw.core.chat_engine import ChatEngine
from opcclaw.core.skill_loader import SkillLoader
from opcclaw.core.memory_store import MemoryStore
from opcclaw.core.super_intelligence import enhance_chat_engine, SuperIntelligence
from opcclaw.core.multi_model import MultiModelRouter, TaskType, BUILTIN_TASK_TYPES
from opcclaw.core.multi_model_chat_engine import MultiModelChatEngine
from opcclaw.core.agent_loop import AgentLoop
from opcclaw.core.rag_context import RAGContextInjector
from opcclaw.tools.builtin.system_tools import register_system_tools
from opcclaw.tools.builtin.developer_tools import register_developer_tools
from opcclaw.tools.builtin.git_tools import register_git_tools
from opcclaw.tools.builtin.code_tools import register_code_tools
from opcclaw.core.opcclaw_logging import logger
from opcclaw.core.secure_storage import SecureStorage
from opcclaw.tools.business_tools import register_business_tools
try:
    from opcclaw.modules.voice_manager import VoiceManager, check_voice_dependencies
except ImportError:
    VoiceManager = None
    check_voice_dependencies = lambda: {}


# ── 按钮动画辅助类 ────────────────────────────────
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, pyqtProperty, QRect, QObject
from PyQt5.QtWidgets import QGraphicsOpacityEffect

class ButtonAnimationHelper:
    """按钮悬停动画辅助类 - 缩放效果"""
    
    @staticmethod
    def apply_scale_animation(button, scale_factor=1.05):
        """为按钮应用缩放悬停动画"""
        # 保存原始尺寸
        original_size = button.sizeHint()
        button._original_size = original_size
        button._scale_factor = scale_factor
        
        # 创建动画
        animation = QPropertyAnimation(button, b"geometry")
        animation.setDuration(200)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        button._hover_animation = animation
        
        # 安装事件过滤器
        button.installEventFilter(button)
        
        # 保存原始事件处理方法
        original_enter = button.enterEvent
        original_leave = button.leaveEvent
        
        def new_enter(event):
            if original_enter != button.enterEvent:
                original_enter(event)
            ButtonAnimationHelper._animate_scale(button, True)
            QPushButton.enterEvent(button, event)
            
        def new_leave(event):
            if original_leave != button.leaveEvent:
                original_leave(event)
            ButtonAnimationHelper._animate_scale(button, False)
            QPushButton.leaveEvent(button, event)
            
        button.enterEvent = new_enter
        button.leaveEvent = new_leave
        
    @staticmethod
    def _animate_scale(button, hover):
        """执行缩放动画"""
        if not hasattr(button, '_hover_animation'):
            return
            
        animation = button._hover_animation
        rect = button.geometry()
        
        if hover:
            # 放大
            new_width = int(rect.width() * button._scale_factor)
            new_height = int(rect.height() * button._scale_factor)
            x_offset = (rect.width() - new_width) // 2
            y_offset = (rect.height() - new_height) // 2
            animation.setStartValue(rect)
            animation.setEndValue(QRect(rect.x() + x_offset, rect.y() + y_offset, 
                                       new_width, new_height))
        else:
            # 恢复原始尺寸
            new_width = int(rect.width() / button._scale_factor)
            new_height = int(rect.height() / button._scale_factor)
            x_offset = (rect.width() - new_width) // 2
            y_offset = (rect.height() - new_height) // 2
            animation.setStartValue(rect)
            animation.setEndValue(QRect(rect.x() + x_offset, rect.y() + y_offset, 
                                       new_width, new_height))
        
        animation.start()


class ButtonHoverFilter(QObject):
    """按钮悬停颜色过滤器的简化版本"""
    
    def __init__(self, button, hover_color, normal_color):
        super().__init__(button)
        self.button = button
        self.hover_color = hover_color
        self.normal_color = normal_color
        
    def eventFilter(self, obj, event):
        if obj == self.button:
            if event.type() == QEvent.Enter:
                obj.setStyleSheet(obj.styleSheet().replace(self.normal_color, self.hover_color))
            elif event.type() == QEvent.Leave:
                obj.setStyleSheet(obj.styleSheet().replace(self.hover_color, self.normal_color))
        return super().eventFilter(obj, event)


class LoadingAnimationHelper:
    """加载动画辅助类"""
    
    @staticmethod
    def set_loading(button, loading=True, original_text=None):
        """设置按钮加载状态"""
        if loading:
            button.setEnabled(False)
            button._original_text = button.text()
            button.setText("⏳ 加载中...")
        else:
            button.setEnabled(True)
            if hasattr(button, '_original_text'):
                button.setText(button._original_text)


# ═══════════════════════════════════════════
# 颜色常量
# ═══════════════════════════════════════════

COLORS = {
    "bg": "#F5F6FA",
    "sidebar": "#1E2A3A",
    "sidebar_hover": "#2C3E50",
    "sidebar_active": "#3498DB",
    "header": "#2C3E50",
    "card": "#FFFFFF",
    "border": "#E0E4EA",
    "primary": "#3498DB",
    "primary_hover": "#2980B9",
    "secondary": "#E8F4FD",
    "secondary_hover": "#D4ECFA",
    "success": "#27AE60",
    "warning": "#F39C12",
    "danger": "#E74C3C",
    "text": "#2C3E50",
    "text_light": "#7F8C8D",
    "text_white": "#FFFFFF",
    "input_bg": "#F8F9FA",
}


# ═══════════════════════════════════════════
# 消息气泡组件
# ═══════════════════════════════════════════

class MessageBubble(QFrame):
    """聊天消息气泡"""

    # AI 消息操作按钮信号
    like_clicked = pyqtSignal(str)     # 点赞
    dislike_clicked = pyqtSignal(str)  # 点踩
    play_clicked = pyqtSignal(str)     # 朗读
    share_clicked = pyqtSignal(str)    # 分享

    def __init__(self, text: str, sender: str = "ai", parent=None):
        super().__init__(parent)
        self.sender = sender
        self._text = text  # 保存原始文字

        bg_map = {
            "user": "#DCF8C6",
            "ai": "#FFFFFF",
            "tool": "#F0F4F8",
            "error": "#FDE8E8",
        }
        bg = bg_map.get(sender, "#FFFFFF")

        self.setStyleSheet(f"""
            MessageBubble {{
                background-color: {bg};
                border-radius: 12px;
                padding: 10px 14px;
                margin: 4px 8px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumWidth(200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)

        label_map = {"user": "我", "ai": "OPCclaw", "tool": "⚡ 工具", "error": "⚠️ 错误"}
        sender_label = QLabel(label_map.get(sender, ""))
        sender_label.setStyleSheet("font-size: 11px; color: #64748B; font-weight: bold;")
        align = Qt.AlignRight if sender == "user" else Qt.AlignLeft
        sender_label.setAlignment(align)
        layout.addWidget(sender_label)

        self.content = QLabel(text)
        self.content.setWordWrap(True)
        self.content.setTextFormat(Qt.PlainText)
        self.content.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.content.setStyleSheet("font-size: 18px; color: #1E293B; line-height: 1.6;")
        self.content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.content.setMinimumWidth(160)
        layout.addWidget(self.content)

        # AI 消息添加操作按钮行
        if sender == "ai":
            btn_row = QHBoxLayout()
            btn_row.setSpacing(8)
            btn_row.setContentsMargins(0, 6, 0, 0)

            # 通用按钮样式
            btn_style = """
                QPushButton {
                    background-color: #F1F3F4;
                    color: #5F6368;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #E8EAED;
                }
            """

            # 点赞按钮
            self.like_btn = QPushButton("👍 点赞")
            self.like_btn.setStyleSheet(btn_style)
            self.like_btn.clicked.connect(self._on_like_clicked)
            btn_row.addWidget(self.like_btn)

            # 点踩按钮
            self.dislike_btn = QPushButton("👎 点踩")
            self.dislike_btn.setStyleSheet(btn_style)
            self.dislike_btn.clicked.connect(self._on_dislike_clicked)
            btn_row.addWidget(self.dislike_btn)

            # 朗读按钮
            self.play_btn = QPushButton("🔊 朗读")
            self.play_btn.setStyleSheet(btn_style)
            self.play_btn.clicked.connect(self._on_play_clicked)
            btn_row.addWidget(self.play_btn)

            # 分享按钮
            self.share_btn = QPushButton("📤 分享")
            self.share_btn.setStyleSheet(btn_style)
            self.share_btn.clicked.connect(self._on_share_clicked)
            btn_row.addWidget(self.share_btn)

            btn_row.addStretch()  # 让按钮靠左，右侧留空
            layout.addLayout(btn_row)

        time_label = QLabel(datetime.now().strftime("%H:%M"))
        time_label.setStyleSheet("font-size: 10px; color: #94A3B8; margin-top: 4px;")
        time_label.setAlignment(align)
        layout.addWidget(time_label)

    def _on_like_clicked(self):
        """点赞"""
        self.like_clicked.emit(self._text)

    def _on_dislike_clicked(self):
        """点踩"""
        self.dislike_clicked.emit(self._text)

    def _on_play_clicked(self):
        """朗读"""
        self.play_clicked.emit(self._text)

    def _on_share_clicked(self):
        """分享"""
        self.share_clicked.emit(self._text)

    def set_text(self, text: str):
        self.content.setText(text)
        self._text = text  # 更新保存的文字


# ═══════════════════════════════════════════
# 登录对话框
# ═══════════════════════════════════════════

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
                f"无法加载一人公司认证模块: {e}\n请确保一人公司系统已正确安装。"
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


# ═══════════════════════════════════════════
# 配置管理器
# ═══════════════════════════════════════════

class ConfigManager:
    """管理 OPCclaw 全部配置: 云端模型 + 本地模型 + 技能状态 + 通用设置
    
    安全特性:
    - API Key 使用 Windows DPAPI 加密存储，不保存在明文 config.json 中
    - 加密文件绑定当前 Windows 用户账户
    """


    def _force_set_admin_password(self):
        """首次运行时自动生成管理员密码（仅显示一次）"""
        storage = SecureStorage()
        if storage.is_admin_configured():
            return  # 已设置，无需初始化

        # 自动生成随机 16 位密码
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(chars) for _ in range(16))
        storage.set_admin_password(password)

        dlg = QDialog(self)
        dlg.setWindowTitle("管理员密码已生成")
        dlg.setFixedSize(420, 320)
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
                font-family: 'Consolas', 'Courier New', monospace;
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
        copy_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover { background: #2980b9; }
        """)
        def do_copy():
            QApplication.clipboard().setText(password)
            copy_btn.setText(" 已复制")
        copy_btn.clicked.connect(do_copy)
        btn_row.addWidget(copy_btn)

        ok_btn = QPushButton("我已保存")
        ok_btn.setMinimumHeight(38)
        ok_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background: #2980b9; }
        """)
        ok_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(ok_btn)

        layout.addLayout(btn_row)

        hint = QLabel("密码使用 Windows 加密存储，不会保存在代码中\n可随时在设置中修改密码")
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size: 11px; color: #7f8c8d; padding: 4px;")
        layout.addWidget(hint)

        dlg.exec_()
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.config_path = os.path.join(data_dir, "opcclaw_config.json")
        self._data = self._load_defaults()
        self._secure = self._init_secure_storage()
        self._load()

    def _load_defaults(self) -> dict:
        return {
            "active_provider_id": "",
            "active_provider_type": "cloud",  # "cloud" | "local"
            "cloud_providers": {},
            "local_providers": {},
            "disabled_skills": [],
            "general": {
                "theme": "light",
                "auto_save": True,
                "max_tool_rounds": 5,
                "font_size": 14,
            },
        }

    def _init_secure_storage(self):
        """初始化安全存储（延迟导入避免循环依赖）"""
        try:
            import sys
            core_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core")
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)
            from secure_storage import SecureStorage
            return SecureStorage(app_name="opcclaw")
        except Exception as e:
            logger.error(f"[ConfigManager] 安全存储初始化失败: {e}")
            return None

    def _load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._data.update(saved)
                # 从安全存储恢复 API Key
                self._restore_api_keys()
            except Exception:
                pass
    
    def _restore_api_keys(self):
        """从安全存储恢复 API Key 到内存配置"""
        if not self._secure:
            return
        try:
            for ptype in ["cloud", "local"]:
                providers = self._data.get(f"{ptype}_providers", {})
                for pid, config in providers.items():
                    if not config.get("api_key"):
                        # 尝试从安全存储读取
                        secure_key = self._secure.load_api_key(f"{ptype}:{pid}")
                        if secure_key:
                            config["api_key"] = secure_key
                            logger.info(f"[ConfigManager] 已恢复 {ptype}:{pid} 的 API Key")
        except Exception as e:
            logger.error(f"[ConfigManager] 恢复 API Key 失败: {e}")
    
    def _secure_save_keys(self):
        """将 API Key 保存到安全存储，config.json 中留空"""
        if not self._secure:
            return
        try:
            for ptype in ["cloud", "local"]:
                providers = self._data.get(f"{ptype}_providers", {})
                for pid, config in providers.items():
                    key = config.get("api_key", "").strip()
                    if key:
                        # 保存到安全存储
                        self._secure.save_api_key(f"{ptype}:{pid}", key)
                        # 清空明文 config 中的 key
                        config["api_key"] = ""
                        logger.info(f"[ConfigManager] 已加密保存 {ptype}:{pid} 的 API Key")
        except Exception as e:
            logger.error(f"[ConfigManager] 加密保存失败: {e}")

    def save(self):
        os.makedirs(self.data_dir, exist_ok=True)
        # 先加密保存 API Key
        self._secure_save_keys()
        # 再保存明文配置（此时 api_key 已被清空）
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
        # 保存后恢复内存中的 Key（不影响运行）
        self._restore_api_keys()

    def get_active_provider(self) -> Optional[ProviderConfig]:
        pid = self._data["active_provider_id"]
        ptype = self._data["active_provider_type"]
        providers = self._data.get(f"{ptype}_providers", {})
        if pid and pid in providers:
            return ProviderConfig(**providers[pid])
        return None

    def set_active_provider(self, pid: str, ptype: str):
        self._data["active_provider_id"] = pid
        self._data["active_provider_type"] = ptype
        self.save()

    def add_provider(self, ptype: str, pid: str, config: dict):
        self._data[f"{ptype}_providers"][pid] = config
        self.save()

    def remove_provider(self, ptype: str, pid: str):
        providers = self._data[f"{ptype}_providers"]
        if pid in providers:
            del providers[pid]
            if self._data["active_provider_id"] == pid:
                self._data["active_provider_id"] = ""
            self.save()

    def list_providers(self, ptype: str) -> dict:
        return self._data.get(f"{ptype}_providers", {})

    def toggle_skill(self, skill_name: str, disabled: bool):
        if disabled:
            if skill_name not in self._data["disabled_skills"]:
                self._data["disabled_skills"].append(skill_name)
        else:
            if skill_name in self._data["disabled_skills"]:
                self._data["disabled_skills"].remove(skill_name)
        self.save()

    def is_skill_disabled(self, skill_name: str) -> bool:
        return skill_name in self._data["disabled_skills"]

    def get_general(self, key: str, default=None):
        return self._data["general"].get(key, default)

    def set_general(self, key: str, value):
        self._data["general"][key] = value
        self.save()


# ═══════════════════════════════════════════
# 通用工具函数
# ═══════════════════════════════════════════

def _styled_btn(text: str, color: str = COLORS["primary"], height: int = 36,
                font_size: int = 13) -> QPushButton:
    """创建统一样式的按钮"""
    btn = QPushButton(text)
    btn.setMinimumHeight(height)
    btn.setFont(QFont("PingFang SC", font_size))
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {color};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 6px 16px;
        }}
        QPushButton:hover {{ opacity: 0.9; }}
        QPushButton:disabled {{ background: #BDC3C7; }}
    """)
    return btn


def _styled_input(placeholder: str = "", password: bool = False,
                  height: int = 38) -> QLineEdit:
    """创建统一样式的输入框"""
    inp = QLineEdit()
    if password:
        inp.setEchoMode(QLineEdit.Password)
    inp.setPlaceholderText(placeholder)
    inp.setMinimumHeight(height)
    inp.setStyleSheet(f"""
        QLineEdit {{
            border: 2px solid {COLORS['border']};
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 13px;
            background: {COLORS['input_bg']};
        }}
        QLineEdit:focus {{ border-color: {COLORS['primary']}; background: white; }}
    """)
    return inp


# ═══════════════════════════════════════════
# 侧栏导航
# ═══════════════════════════════════════════

class Sidebar(QFrame):
    """左侧导航栏"""

    nav_changed = pyqtSignal(int)

    NAV_ITEMS = [
        ("💬 对话", 0),
        ("☁️ 云端模型", 1),
        ("🖥️ 本地模型", 2),
        ("📚 技能管理", 3),
        ("⚙️ 通用设置", 4),
        ("🔀 Git", 5),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(160)
        self.setStyleSheet(f"""
            QFrame {{ background: {COLORS['sidebar']}; border: none; }}
        """)
        self._buttons: list[QPushButton] = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo (hidden to avoid duplication with tab name)
        logo = QLabel("")
        logo.setFont(QFont("PingFang SC", 16, QFont.Bold))
        logo.setStyleSheet(f"color: white; padding: 20px 16px 24px; background: transparent;")
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        # 导航按钮
        for label, idx in self.NAV_ITEMS:
            btn = QPushButton(f"  {label}")
            btn.setFixedHeight(48)
            btn.setFont(QFont("PingFang SC", 11))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    color: {COLORS['text_light']};
                    background: transparent;
                    border: none;
                    text-align: left;
                    padding-left: 20px;
                }}
                QPushButton:hover {{
                    background: {COLORS['sidebar_hover']};
                    color: white;
                }}
            """)
            btn.clicked.connect(lambda checked, i=idx: self._on_nav(i))
            self._buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # 工具数量显示
        self.tool_count_label = QLabel("🛠️ 0 工具")
        self.tool_count_label.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 10px; padding: 4px 16px; background: transparent;")
        self.tool_count_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.tool_count_label)

        # 版本信息
        version = QLabel("v1.0.0")
        version.setStyleSheet(f"""
            color: {COLORS['text_light']};
            font-size: 10px;
            padding: 12px 16px;
            background: transparent;
        """)
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        self._set_active(0)

    def _on_nav(self, idx: int):
        self._set_active(idx)
        self.nav_changed.emit(idx)

    def _set_active(self, idx: int):
        for i, btn in enumerate(self._buttons):
            if i == idx:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        color: white;
                        background: {COLORS['sidebar_active']};
                        border: none;
                        text-align: left;
                        padding-left: 20px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        color: {COLORS['text_light']};
                        background: transparent;
                        border: none;
                        text-align: left;
                        padding-left: 20px;
                    }}
                    QPushButton:hover {{
                        background: {COLORS['sidebar_hover']};
                        color: white;
                    }}
                """)


# ═══════════════════════════════════════════
# 云端模型配置面板
# ═══════════════════════════════════════════

class CloudModelPanel(QWidget):
    """管理云端 LLM 供应商"""

    providers_changed = pyqtSignal()

    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)
        self.config = config
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 标题
        title = QLabel("☁️ 云端模型管理")
        title.setFont(QFont("PingFang SC", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text']};")
        layout.addWidget(title)

        desc = QLabel("管理云端 LLM 供应商 (DeepSeek, OpenAI, 通义千问 等)")
        desc.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addSpacing(8)

        # ── 快速连接：选平台 + 贴Key → 一键聊天 ──
        quick_group = QGroupBox("⚡ 快速连接")
        quick_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                color: {COLORS['text']};
                border: 2px solid {COLORS['primary']};
                border-radius: 8px;
                margin-top: 12px;
                padding: 16px 12px 12px 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
            }}
        """)
        quick_layout = QVBoxLayout(quick_group)
        quick_layout.setSpacing(8)

        # 平台选择行
        plat_row = QHBoxLayout()
        plat_row.addWidget(QLabel("平台:"))
        self.quick_platform = QComboBox()
        self.quick_platform.setMinimumWidth(180)
        templates = BackendFactory.list_templates()
        cloud_templates = [t for t in templates if not t["local"]]
        self._quick_template_ids = []
        for t in cloud_templates:
            self.quick_platform.addItem(f"{t['name']}", t["id"])
            self._quick_template_ids.append(t["id"])
        plat_row.addWidget(self.quick_platform)
        plat_row.addStretch()
        quick_layout.addLayout(plat_row)

        # Key 输入行
        key_row = QHBoxLayout()
        key_row.addWidget(QLabel("Key :"))
        self.quick_key = QLineEdit()
        self.quick_key.setPlaceholderText("在此粘贴 API Key，如 sk-xxx...")
        self.quick_key.setEchoMode(QLineEdit.Password)
        self.quick_key.setMinimumHeight(34)
        self.quick_key.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                background: {COLORS['input_bg']};
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
            }}
        """)
        self.quick_key.returnPressed.connect(self._quick_connect)
        key_row.addWidget(self.quick_key)
        quick_layout.addLayout(key_row)

        # 连接按钮 + 显示/隐藏 Key
        btn_row = QHBoxLayout()
        self.quick_show_key = QCheckBox("显示 Key")
        self.quick_show_key.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        self.quick_show_key.toggled.connect(lambda checked: self.quick_key.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        ))
        btn_row.addWidget(self.quick_show_key)
        btn_row.addStretch()

        connect_btn = _styled_btn("🚀 连接并开始聊天", COLORS["primary"], height=38)
        connect_btn.setFont(QFont("PingFang SC", 11, QFont.Bold))
        connect_btn.clicked.connect(self._quick_connect)
        btn_row.addWidget(connect_btn)
        quick_layout.addLayout(btn_row)

        layout.addWidget(quick_group)
        layout.addSpacing(8)

        # 当前活跃
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # 添加按钮 + 探测按钮
        btn_row = QHBoxLayout()
        add_btn = _styled_btn("+ 添加供应商", COLORS["success"])
        add_btn.clicked.connect(self._show_add_dialog)
        btn_row.addWidget(add_btn)

        scan_btn = _styled_btn("🔍 一键探测", COLORS["primary"])
        scan_btn.clicked.connect(self._scan_all_providers)
        btn_row.addWidget(scan_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # 供应商列表
        self.provider_list = QListWidget()
        self.provider_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                background: {COLORS['card']};
                padding: 4px;
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 10px 14px;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QListWidget::item:selected {{
                background: {COLORS['primary']};
                color: white;
            }}
        """)
        self.provider_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.provider_list, stretch=1)

        # 操作按钮
        btn_row = QHBoxLayout()
        use_btn = _styled_btn("设为活跃", COLORS["primary"])
        use_btn.clicked.connect(self._use_selected)
        btn_row.addWidget(use_btn)

        edit_btn = _styled_btn("编辑 Key", COLORS["warning"])
        edit_btn.clicked.connect(self._edit_selected)
        btn_row.addWidget(edit_btn)

        del_btn = _styled_btn("删除", COLORS["danger"])
        del_btn.clicked.connect(self._delete_selected)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._refresh()

    def _refresh(self):
        self.provider_list.clear()
        providers = self.config.list_providers("cloud")
        active_id = self.config._data["active_provider_id"]
        active_type = self.config._data["active_provider_type"]

        for pid, pdata in providers.items():
            name = pdata.get("name", pid)
            model = pdata.get("model", "")
            active_mark = " ★" if (active_type == "cloud" and active_id == pid) else ""
            item = QListWidgetItem(f"{name}{active_mark}  |  {model}")
            item.setData(Qt.UserRole, pid)
            self.provider_list.addItem(item)

        if active_type == "cloud" and active_id:
            active_p = providers.get(active_id, {})
            self.status_label.setText(
                f"当前活跃: {active_p.get('name', active_id)} "
                f"({active_p.get('model', '')})"
            )
            self.status_label.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold; font-size: 13px;")
        else:
            self.status_label.setText("⚠️ 未选择活跃供应商, 对话功能不可用")
            self.status_label.setStyleSheet(f"color: {COLORS['warning']}; font-size: 13px;")

    def _quick_connect(self):
        """快速连接：用当前选中的平台 + 手动输入的 Key 直接开始聊天"""
        key = self.quick_key.text().strip()
        if not key:
            QMessageBox.warning(self, "提示", "请先粘贴 API Key")
            return

        pid = self.quick_platform.currentData()
        t = PROVIDER_TEMPLATES.get(pid)
        if not t:
            QMessageBox.warning(self, "提示", "请选择平台")
            return

        name = t.name
        url = t.base_url
        model = t.model

        # 测试连接
        try:
            cfg = ProviderConfig(
                name=name, provider_type="openai_compatible",
                base_url=url, api_key=key, model=model,
            )
            backend = BackendFactory.create(cfg)
            resp = backend.chat([{"role": "user", "content": "hi"}])
            QMessageBox.information(self, "连接成功", f"{name} 测试通过!\n模型: {resp.model}")
        except Exception as e:
            QMessageBox.critical(self, "连接失败", f"{name} 连接失败:\n{e}")
            return

        # 保存
        pid = name.lower().replace(" ", "_")
        self.config.add_provider("cloud", pid, {
            "name": name,
            "provider_type": "openai_compatible",
            "base_url": url,
            "api_key": key,
            "model": model,
        })
        self.config.set_active_provider(pid, "cloud")
        self._refresh()
        self.providers_changed.emit()

    def _show_add_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("添加云端 LLM 供应商")
        dlg.setMinimumWidth(480)
        layout = QFormLayout(dlg)
        layout.setSpacing(12)

        # 模板选择
        template_combo = QComboBox()
        templates = BackendFactory.list_templates()
        cloud_templates = [t for t in templates if not t["local"]]
        for t in cloud_templates:
            template_combo.addItem(f"{t['name']} ({t['model']})", t["id"])
        layout.addRow("模板:", template_combo)

        # 自定义名称
        name_input = _styled_input("显示名称")
        layout.addRow("名称:", name_input)

        # API Key
        key_input = _styled_input("API Key", password=True)
        layout.addRow("API Key:", key_input)

        # Base URL
        url_input = _styled_input("API 地址 (自动填充)")
        layout.addRow("API 地址:", url_input)

        # 模型选择 (可编辑下拉框 + 获取按钮)
        model_row = QHBoxLayout()
        self._add_model_combo = QComboBox()
        self._add_model_combo.setEditable(True)
        self._add_model_combo.setMinimumWidth(280)
        self._add_model_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                background: {COLORS['card']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
        """)
        model_row.addWidget(self._add_model_combo)

        fetch_btn = QPushButton("📋 获取平台模型列表")
        fetch_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #2980B9;
            }}
        """)
        fetch_btn.clicked.connect(lambda: self._fetch_models_into_combo(
            self._add_model_combo, url_input.text(), key_input.text()
        ))
        model_row.addWidget(fetch_btn)
        layout.addRow("模型:", model_row)

        def _on_template_changed(idx):
            tid = template_combo.currentData()
            t = PROVIDER_TEMPLATES.get(tid)
            if t:
                url_input.setText(t.base_url)
                name_input.setText(t.name)
                # 填模型下拉列表
                self._add_model_combo.clear()
                if t.available_models:
                    self._add_model_combo.addItems(t.available_models)
                self._add_model_combo.setEditText(t.model)

        template_combo.currentIndexChanged.connect(_on_template_changed)
        _on_template_changed(0)

        # 按钮
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dlg.reject)
        save_btn = _styled_btn("测试并保存", COLORS["success"])
        save_btn.clicked.connect(lambda: self._save_cloud_provider(
            dlg, name_input.text(), key_input.text(), url_input.text(),
            self._add_model_combo.currentText()
        ))
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        layout.addRow("", btn_layout)

        dlg.exec_()

    def _save_cloud_provider(self, dlg, name, key, url, model):
        if not name:
            QMessageBox.warning(dlg, "提示", "请输入供应商名称")
            return
        if not key:
            QMessageBox.warning(dlg, "提示", "云端模型需要 API Key")
            return

        # 测试连接
        try:
            cfg = ProviderConfig(
                name=name, provider_type="openai_compatible",
                base_url=url.strip(), api_key=key.strip(), model=model.strip(),
            )
            backend = BackendFactory.create(cfg)
            resp = backend.chat([{"role": "user", "content": "hi"}])
            QMessageBox.information(dlg, "连接成功", f"测试成功! 模型: {resp.model}")
        except Exception as e:
            reply = QMessageBox.question(
                dlg, "连接失败",
                f"测试失败: {e}\n\n是否仍然保存此供应商?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # 保存
        pid = name.lower().replace(" ", "_")
        self.config.add_provider("cloud", pid, {
            "name": name.strip(),
            "provider_type": "openai_compatible",
            "base_url": url.strip(),
            "api_key": key.strip(),
            "model": model.strip(),
        })
        dlg.accept()
        self._refresh()
        self.providers_changed.emit()

    def _on_item_double_clicked(self, item):
        self._use_selected()

    def _use_selected(self):
        item = self.provider_list.currentItem()
        if not item:
            return
        pid = item.data(Qt.UserRole)
        self.config.set_active_provider(pid, "cloud")
        self._refresh()
        self.providers_changed.emit()

    def _edit_selected(self):
        """编辑已有供应商的 API Key / URL / Model"""
        item = self.provider_list.currentItem()
        if not item:
            return
        pid = item.data(Qt.UserRole)
        providers = self.config.list_providers("cloud")
        pdata = providers.get(pid)
        if not pdata:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"编辑供应商: {pdata.get('name', pid)}")
        dlg.setMinimumWidth(480)
        layout = QFormLayout(dlg)
        layout.setSpacing(12)

        name_input = _styled_input("显示名称")
        name_input.setText(pdata.get("name", ""))
        layout.addRow("名称:", name_input)

        key_input = _styled_input("API Key (仅替换, 不显示原值)", password=True)
        key_input.setPlaceholderText("输入新 Key 替换, 留空保持不变")
        layout.addRow("API Key:", key_input)

        url_input = _styled_input("API 地址")
        url_input.setText(pdata.get("base_url", ""))
        layout.addRow("API 地址:", url_input)

        # 模型选择 (可编辑下拉框 + 获取按钮)
        model_row = QHBoxLayout()
        edit_model_combo = QComboBox()
        edit_model_combo.setEditable(True)
        edit_model_combo.setMinimumWidth(280)
        edit_model_combo.setEditText(pdata.get("model", ""))
        # 尝试按 base_url 匹配模板, 预填模型列表
        for tpl in PROVIDER_TEMPLATES.values():
            if tpl.base_url == pdata.get("base_url", ""):
                if tpl.available_models:
                    edit_model_combo.addItems(tpl.available_models)
                    edit_model_combo.setEditText(pdata.get("model", ""))
                break
        edit_model_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                background: {COLORS['card']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
        """)
        model_row.addWidget(edit_model_combo)

        fetch_btn = QPushButton("📋 获取平台模型列表")
        fetch_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #2980B9;
            }}
        """)
        fetch_btn.clicked.connect(lambda: self._fetch_models_into_combo(
            edit_model_combo, url_input.text(),
            key_input.text() or pdata.get("api_key", "")
        ))
        model_row.addWidget(fetch_btn)
        layout.addRow("模型:", model_row)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dlg.reject)
        save_btn = _styled_btn("保存", COLORS["success"])
        save_btn.clicked.connect(lambda: self._do_edit_save(
            dlg, pid, name_input.text(), key_input.text(),
            url_input.text(), edit_model_combo.currentText()
        ))
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        layout.addRow("", btn_layout)

        dlg.exec_()

    def _do_edit_save(self, dlg, pid, name, key, url, model):
        providers = self.config.list_providers("cloud")
        pdata = providers.get(pid, {})
        pdata["name"] = name.strip() or pdata.get("name", pid)
        if key.strip():
            pdata["api_key"] = key.strip()
        pdata["base_url"] = url.strip() or pdata.get("base_url", "")
        pdata["model"] = model.strip() or pdata.get("model", "")
        self.config._data["cloud_providers"][pid] = pdata
        self.config.save()
        dlg.accept()
        self._refresh()
        self.providers_changed.emit()

    def _delete_selected(self):
        item = self.provider_list.currentItem()
        if not item:
            return
        pid = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "确认", f"确定要删除供应商 \"{pid}\" 吗?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.config.remove_provider("cloud", pid)
            self._refresh()
            self.providers_changed.emit()

    def _scan_all_providers(self):
        """一键探测所有预置供应商的连通性"""
        from opcclaw.core.llm_backend import BackendFactory, ProviderConfig

        self.status_label.setText("正在探测所有供应商...")
        self.status_label.setStyleSheet(f"color: {COLORS['primary']};")
        QApplication.processEvents()

        results = []
        for pid, template in PROVIDER_TEMPLATES.items():
            try:
                cfg = ProviderConfig(
                    name=template.name,
                    provider_type="openai_compatible",
                    base_url=template.base_url,
                    api_key="",  # 空key测试
                    model=template.model,
                )
                backend = BackendFactory.create(cfg)
                # 只测试连接，不发送真实请求
                results.append((template.name, "需要API Key", "info"))
            except Exception as e:
                results.append((template.name, f"错误: {str(e)[:50]}", "error"))

        # 显示结果
        msg = "供应商探测结果:\n\n"
        for name, status, level in results:
            icon = "✅" if level == "ok" else "⚠️" if level == "info" else "❌"
            msg += f"{icon} {name}: {status}\n"

        QMessageBox.information(self, "探测结果", msg)
        self._refresh()

    def _fetch_models_into_combo(self, combo: QComboBox, base_url: str, api_key: str):
        """从平台拉取模型列表并填入下拉框"""
        if not base_url.strip():
            QMessageBox.warning(self, "提示", "请先填写 API 地址")
            return
        if not api_key.strip():
            QMessageBox.warning(self, "提示", "云端模型需要 API Key 才能获取模型列表")
            return

        original = combo.currentText()
        combo.clear()
        combo.addItem("⏳ 正在获取模型列表...")
        combo.setEnabled(False)
        QApplication.processEvents()

        try:
            models = get_available_models(base_url.strip(), api_key.strip())
            combo.clear()
            if models:
                combo.addItems(models)
                # 恢复/选择原模型 (如果还在列表里)
                idx = combo.findText(original)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                else:
                    combo.setEditText(original or (models[0] if models else ""))
                QMessageBox.information(self, "成功", f"获取到 {len(models)} 个模型")
            else:
                combo.addItem(original)
                combo.setEditText(original)
                QMessageBox.information(self, "提示", "该平台未返回模型列表")
        except Exception as e:
            combo.clear()
            combo.addItem(original)
            combo.setEditText(original)
            QMessageBox.warning(self, "获取失败", str(e))
        finally:
            combo.setEnabled(True)


# ═══════════════════════════════════════════
# 本地模型配置面板
# ═══════════════════════════════════════════

class LocalModelPanel(QWidget):
    """管理本地 LLM (Ollama / LM Studio)"""

    providers_changed = pyqtSignal()

    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)
        self.config = config
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("🖥️ 本地模型管理")
        title.setFont(QFont("PingFang SC", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text']};")
        layout.addWidget(title)

        desc = QLabel("连接本地大模型 (Ollama / LM Studio / vLLM)\n无需联网, 数据安全, 零成本")
        desc.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 13px; line-height: 1.5;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addSpacing(8)

        # 当前活跃状态
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # 快捷添加: Ollama
        ollama_group = QGroupBox("Ollama (推荐)")
        ollama_layout = QVBoxLayout(ollama_group)
        ollama_hint = QLabel("Ollama 默认地址: http://localhost:11434/v1")
        ollama_hint.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        ollama_layout.addWidget(ollama_hint)

        ollama_row = QHBoxLayout()
        self.ollama_model = QComboBox()
        self.ollama_model.setEditable(True)
        self.ollama_model.setMinimumWidth(200)
        self.ollama_model.addItems(["qwen2.5:7b", "qwen2.5:14b", "deepseek-r1:8b",
                                     "llama3.1:8b", "mistral:7b", "gemma2:9b"])
        ollama_row.addWidget(QLabel("模型:"))
        ollama_row.addWidget(self.ollama_model, stretch=1)

        self.ollama_url = QLineEdit("http://localhost:11434/v1")
        self.ollama_url.setMinimumHeight(32)
        ollama_row.addWidget(QLabel("地址:"))
        ollama_row.addWidget(self.ollama_url)

        ollama_btn = _styled_btn("连接 Ollama", COLORS["success"])
        ollama_btn.clicked.connect(self._connect_ollama)
        ollama_row.addWidget(ollama_btn)
        ollama_layout.addLayout(ollama_row)
        layout.addWidget(ollama_group)

        # 快捷添加: LM Studio
        lm_group = QGroupBox("LM Studio")
        lm_layout = QVBoxLayout(lm_group)
        lm_hint = QLabel("LM Studio 默认地址: http://localhost:1234/v1")
        lm_hint.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        lm_layout.addWidget(lm_hint)

        lm_row = QHBoxLayout()
        self.lm_model = QComboBox()
        self.lm_model.setEditable(True)
        self.lm_model.addItems(["local-model", "qwen2.5", "deepseek-r1-distill-qwen"])
        self.lm_model.setMinimumWidth(200)
        lm_row.addWidget(QLabel("模型:"))
        lm_row.addWidget(self.lm_model, stretch=1)

        self.lm_url = QLineEdit("http://localhost:1234/v1")
        self.lm_url.setMinimumHeight(32)
        lm_row.addWidget(QLabel("地址:"))
        lm_row.addWidget(self.lm_url)

        lm_btn = _styled_btn("连接 LM Studio", COLORS["success"])
        lm_btn.clicked.connect(self._connect_lm_studio)
        lm_row.addWidget(lm_btn)
        lm_layout.addLayout(lm_row)
        layout.addWidget(lm_group)

        # 自定义
        custom_group = QGroupBox("自定义本地服务")
        custom_layout = QFormLayout(custom_group)
        custom_name = _styled_input("服务名称 (如: vLLM, text-gen-webui)")
        custom_url = _styled_input("服务地址 (如: http://localhost:8000/v1)")
        custom_model = _styled_input("模型名称")
        custom_layout.addRow("名称:", custom_name)
        custom_layout.addRow("地址:", custom_url)
        custom_layout.addRow("模型:", custom_model)

        custom_btn = _styled_btn("添加自定义服务", COLORS["primary"])
        custom_btn.clicked.connect(lambda: self._add_custom(
            custom_name.text(), custom_url.text(), custom_model.text()
        ))
        custom_layout.addRow("", custom_btn)
        layout.addWidget(custom_group)

        # 已连接的本地服务列表
        self.provider_list = QListWidget()
        self.provider_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                background: {COLORS['card']};
                font-size: 13px;
            }}
            QListWidget::item {{ padding: 10px 14px; border-bottom: 1px solid {COLORS['border']}; }}
            QListWidget::item:selected {{ background: {COLORS['primary']}; color: white; }}
        """)
        self.provider_list.itemDoubleClicked.connect(self._use_local_selected)
        layout.addWidget(self.provider_list, stretch=1)

        btn_row = QHBoxLayout()
        use_btn = _styled_btn("设为活跃", COLORS["primary"])
        use_btn.clicked.connect(self._use_local_selected)
        btn_row.addWidget(use_btn)
        del_btn = _styled_btn("删除", COLORS["danger"])
        del_btn.clicked.connect(self._delete_local_selected)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.custom_name = custom_name
        self.custom_url = custom_url
        self.custom_model = custom_model
        self._refresh()

    def _connect_ollama(self):
        self._add_local("Ollama", self.ollama_url.text().strip(),
                        self.ollama_model.currentText().strip())

    def _connect_lm_studio(self):
        self._add_local("LM Studio", self.lm_url.text().strip(),
                        self.lm_model.currentText().strip())

    def _add_custom(self, name: str, url: str, model: str):
        if not name or not url:
            QMessageBox.warning(self, "提示", "请填写名称和地址")
            return
        self._add_local(name, url, model)

    def _add_local(self, name: str, url: str, model: str):
        try:
            cfg = ProviderConfig(
                name=name, provider_type="openai_compatible",
                base_url=url, api_key="local", model=model,
            )
            backend = BackendFactory.create(cfg)
            resp = backend.chat([{"role": "user", "content": "hi"}])
            QMessageBox.information(self, "连接成功", f"{name} 已连接!\n模型: {resp.model}")
        except Exception as e:
            QMessageBox.warning(self, "连接失败",
                               f"无法连接到 {name}: {e}\n请确保服务已启动。")
            return

        pid = name.lower().replace(" ", "_")
        self.config.add_provider("local", pid, {
            "name": name, "provider_type": "openai_compatible",
            "base_url": url, "api_key": "local", "model": model,
        })
        self._refresh()
        self.providers_changed.emit()

    def _refresh(self):
        self.provider_list.clear()
        providers = self.config.list_providers("local")
        active_id = self.config._data["active_provider_id"]
        active_type = self.config._data["active_provider_type"]

        for pid, pdata in providers.items():
            name = pdata.get("name", pid)
            model = pdata.get("model", "")
            url = pdata.get("base_url", "")
            active_mark = " ★" if (active_type == "local" and active_id == pid) else ""
            item = QListWidgetItem(f"{name}{active_mark}  |  {model}  |  {url}")
            item.setData(Qt.UserRole, pid)
            self.provider_list.addItem(item)

        if active_type == "local" and active_id:
            active_p = providers.get(active_id, {})
            self.status_label.setText(
                f"当前活跃: {active_p.get('name', active_id)} "
                f"({active_p.get('model', '')}) [本地]"
            )
            self.status_label.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold; font-size: 13px;")
        else:
            self.status_label.setText("ℹ️ 未使用本地模型, 可在此配置")

    def _use_local_selected(self):
        item = self.provider_list.currentItem()
        if not item:
            return
        pid = item.data(Qt.UserRole)
        self.config.set_active_provider(pid, "local")
        self._refresh()
        self.providers_changed.emit()

    def _delete_local_selected(self):
        item = self.provider_list.currentItem()
        if not item:
            return
        pid = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "确认", f"确定要删除 \"{pid}\" 吗?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.config.remove_provider("local", pid)
            self._refresh()
            self.providers_changed.emit()


# ═══════════════════════════════════════════
# 技能管理面板
# ═══════════════════════════════════════════

class SkillsPanel(QWidget):
    """浏览、启用/禁用技能"""

    skills_changed = pyqtSignal()

    def __init__(self, config: ConfigManager, skill_loader: SkillLoader, parent=None):
        super().__init__(parent)
        self.config = config
        self.skill_loader = skill_loader
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("📚 技能管理")
        title.setFont(QFont("PingFang SC", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text']};")
        layout.addWidget(title)

        desc = QLabel("管理 OPCclaw 的技能模块。技能是 AI Agent 的\"灵魂\", 定义了何时使用什么工具。")
        desc.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 刷新按钮
        refresh_btn = _styled_btn("🔄 重新加载技能", COLORS["primary"])
        refresh_btn.clicked.connect(lambda: (self.skill_loader.list_skills(), self._refresh(), self.skills_changed.emit()))
        layout.addWidget(refresh_btn)

        # 技能列表
        self.skill_list = QListWidget()
        self.skill_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                background: {COLORS['card']};
                font-size: 13px;
            }}
            QListWidget::item {{ padding: 10px 14px; border-bottom: 1px solid {COLORS['border']}; }}
        """)
        layout.addWidget(self.skill_list, stretch=1)

        # 操作按钮
        btn_row = QHBoxLayout()
        self.toggle_btn = _styled_btn("启用/禁用", COLORS["warning"])
        self.toggle_btn.clicked.connect(self._toggle_selected)
        btn_row.addWidget(self.toggle_btn)

        view_btn = _styled_btn("查看详情", COLORS["primary"])
        view_btn.clicked.connect(self._view_selected)
        btn_row.addWidget(view_btn)
        btn_row.addStretch()

        # 添加技能按钮
        add_btn = _styled_btn("+ 添加技能目录", COLORS["success"])
        add_btn.clicked.connect(self._add_skill_dir)
        btn_row.addWidget(add_btn)
        layout.addLayout(btn_row)

        # 统计
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        layout.addWidget(self.stats_label)

        self._refresh()

    def _refresh(self):
        self.skill_list.clear()
        try:
            skills = self.skill_loader.list_skills()
        except Exception:
            self.stats_label.setText("技能系统未初始化")
            return
        for skill in skills:
            name = skill['name']
            disabled = self.config.is_skill_disabled(name)
            status_icon = "🚫" if disabled else "✅"
            item = QListWidgetItem(
                f"{status_icon}  {skill['emoji']}  {skill['name']}  |  {skill['description'][:50]}"
            )
            item.setData(Qt.UserRole, name)
            self.skill_list.addItem(item)

        enabled = sum(1 for s in skills if not self.config.is_skill_disabled(s['name']))
        self.stats_label.setText(
            f"共 {len(skills)} 个技能, {enabled} 个已启用, "
            f"{len(skills) - enabled} 个已禁用"
        )

    def _toggle_selected(self):
        item = self.skill_list.currentItem()
        if not item:
            return
        name = item.data(Qt.UserRole)
        current = self.config.is_skill_disabled(name)
        self.config.toggle_skill(name, not current)
        self._refresh()
        self.skills_changed.emit()

    def _view_selected(self):
        item = self.skill_list.currentItem()
        if not item:
            return
        name = item.data(Qt.UserRole)
        skill = self.skill_loader.get_skill(name)
        if not skill:
            return
        detail = (
            f"名称: {skill['name']}\n"
            f"描述: {skill['description']}\n"
            f"版本: {skill['version']}\n"
            f"emoji: {skill['emoji']}\n"
            f"路径: {skill['path']}\n\n"
            f"指令体 (前500字):\n{skill['body'][:500]}..."
        )
        QMessageBox.information(self, f"技能: {name}", detail)

    def _add_skill_dir(self):
        from PyQt5.QtWidgets import QFileDialog
        d = QFileDialog.getExistingDirectory(self, "选择技能目录")
        if d:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "提示", "自定义技能目录功能暂未实现\n\n技能将从默认目录加载")
            # TODO: 未来支持自定义技能目录


# ═══════════════════════════════════════════
# 通用设置面板
# ═══════════════════════════════════════════

class GeneralSettingsPanel(QWidget):
    """通用设置: 主题/自动保存/数据清除"""

    settings_changed = pyqtSignal()

    def __init__(self, config: ConfigManager, memory_store: MemoryStore, parent=None):
        super().__init__(parent)
        self.config = config
        self.memory_store = memory_store
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("⚙️ 通用设置")
        title.setFont(QFont("PingFang SC", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text']};")
        layout.addWidget(title)

        # ── 对话设置 ──
        chat_group = QGroupBox("对话设置")
        chat_form = QFormLayout(chat_group)

        self.auto_save_cb = QCheckBox("自动保存对话历史")
        self.auto_save_cb.setChecked(self.config.get_general("auto_save", True))
        self.auto_save_cb.stateChanged.connect(
            lambda: self._update_general("auto_save", self.auto_save_cb.isChecked())
        )
        chat_form.addRow(self.auto_save_cb)

        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("字体大小:"))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(10, 24)
        self.font_spin.setValue(self.config.get_general("font_size", 14))
        self.font_spin.valueChanged.connect(lambda v: self._update_general("font_size", v))
        font_layout.addWidget(self.font_spin)
        font_layout.addStretch()
        chat_form.addRow(font_layout)

        tool_layout = QHBoxLayout()
        tool_layout.addWidget(QLabel("最大工具调用轮次:"))
        self.tool_spin = QSpinBox()
        self.tool_spin.setRange(1, 20)
        self.tool_spin.setValue(self.config.get_general("max_tool_rounds", 5))
        self.tool_spin.valueChanged.connect(lambda v: self._update_general("max_tool_rounds", v))
        tool_layout.addWidget(self.tool_spin)
        tool_layout.addStretch()
        chat_form.addRow(tool_layout)
        layout.addWidget(chat_group)

        # ── 数据管理 ──
        data_group = QGroupBox("数据管理")
        data_form = QFormLayout(data_group)

        clear_chat_btn = _styled_btn("清除所有对话历史", COLORS["warning"])
        clear_chat_btn.clicked.connect(self._clear_all_sessions)
        data_form.addRow("对话数据:", clear_chat_btn)

        clear_memory_btn = _styled_btn("清除长期记忆", COLORS["danger"])
        clear_memory_btn.clicked.connect(self._clear_memories)
        data_form.addRow("记忆数据:", clear_memory_btn)

        reset_btn = _styled_btn("恢复出厂设置", COLORS["danger"])
        reset_btn.clicked.connect(self._reset_all)
        data_form.addRow("全部重置:", reset_btn)
        layout.addWidget(data_group)

        # ── 会话统计 ──
        info_group = QGroupBox("系统信息")
        info_form = QFormLayout(info_group)
        sessions = self.memory_store.list_sessions()
        memories = self.memory_store.list_memories()
        info_form.addRow("对话会话:", QLabel(f"{len(sessions)} 个"))
        info_form.addRow("记忆条目:", QLabel(f"{len(memories)} 条"))
        info_form.addRow("数据目录:", QLabel(self.memory_store.base_dir))
        layout.addWidget(info_group)


        layout.addStretch()

    def _update_general(self, key: str, value):
        self.config.set_general(key, value)
        self.settings_changed.emit()

    def _clear_all_sessions(self):
        reply = QMessageBox.question(
            self, "确认", "确定要清除所有对话历史吗？此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for s in self.memory_store.list_sessions():
                self.memory_store.delete_session(s["id"])
            QMessageBox.information(self, "完成", "所有对话历史已清除")

    def _clear_memories(self):
        reply = QMessageBox.question(
            self, "确认", "确定要清除所有长期记忆吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for m in self.memory_store.list_memories():
                self.memory_store.write_memory(m, "")
            QMessageBox.information(self, "完成", "所有记忆已清除")

    def _reset_all(self):
        reply = QMessageBox.question(
            self, "⚠️ 最终确认",
            "确定要恢复出厂设置吗？\n\n这将清除:\n"
            "- 所有 LLM 供应商配置\n"
            "- 所有对话历史\n"
            "- 所有长期记忆\n"
            "- 所有自定义设置\n\n此操作不可恢复!",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.config._data = self.config._load_defaults()
            self.config.save()
            for s in self.memory_store.list_sessions():
                self.memory_store.delete_session(s["id"])
            for m in self.memory_store.list_memories():
                self.memory_store.write_memory(m, "")
            QMessageBox.information(self, "完成", "已恢复出厂设置。请重新配置 LLM 供应商。")
            self.settings_changed.emit()


# ═══════════════════════════════════════════
# 工作线程
# ═══════════════════════════════════════════

    def _show_change_admin_password(self):
        """显示修改管理员密码对话框"""
        dlg = QDialog(self)
        dlg.setWindowTitle("修改管理员密码")
        dlg.setFixedSize(400, 280)
        dlg.setModal(True)
        
        layout2 = QVBoxLayout(dlg)
        layout2.setContentsMargins(24, 20, 24, 20)
        layout2.setSpacing(14)
        
        info = QLabel("修改管理员密码：")
        info.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout2.addWidget(info)
        
        old_pwd = QLineEdit()
        old_pwd.setPlaceholderText("输入旧密码")
        old_pwd.setEchoMode(QLineEdit.Password)
        old_pwd.setMinimumHeight(38)
        layout2.addWidget(old_pwd)
        
        new_pwd1 = QLineEdit()
        new_pwd1.setPlaceholderText("输入新密码（至少6位）")
        new_pwd1.setEchoMode(QLineEdit.Password)
        new_pwd1.setMinimumHeight(38)
        layout2.addWidget(new_pwd1)
        
        new_pwd2 = QLineEdit()
        new_pwd2.setPlaceholderText("再次输入新密码")
        new_pwd2.setEchoMode(QLineEdit.Password)
        new_pwd2.setMinimumHeight(38)
        layout2.addWidget(new_pwd2)
        
        btn = QPushButton("确认修改")
        btn.setMinimumHeight(38)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }}
            QPushButton:hover {{ background: {COLORS['primary_hover']}; }}
        """)
        
        def do_change():
            old = old_pwd.text().strip()
            n1 = new_pwd1.text().strip()
            n2 = new_pwd2.text().strip()
            
            storage = SecureStorage()
            stored = storage.get_admin_password()
            
            if old != stored:
                QMessageBox.warning(dlg, "错误", "旧密码不正确")
                return
            
            if len(n1) < 6:
                QMessageBox.warning(dlg, "错误", "新密码至少6位")
                return
            
            if n1 != n2:
                QMessageBox.warning(dlg, "错误", "两次新密码不一致")
                return
            
            if storage.set_admin_password(n1):
                QMessageBox.information(dlg, "成功", "密码修改成功")
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "错误", "密码保存失败")
        
        btn.clicked.connect(do_change)
        layout2.addWidget(btn)
        
        dlg.exec_()


class ChatWorker(QThread):
    """后台 LLM 调用, 通过信号更新 UI"""
    text_chunk = pyqtSignal(str)
    finished = pyqtSignal(str, dict)  # text, usage_info
    error = pyqtSignal(str)

    def __init__(self, engine: ChatEngine, user_message: str):
        super().__init__()
        self.engine = engine
        self.user_message = user_message

    def run(self):
        try:
            usage_info = {}
            for chunk in self.engine.chat_stream(self.user_message):
                # 检查是否是 usage 信息（JSON 格式）
                if chunk.startswith('{"usage":'):
                    try:
                        import json
                        data = json.loads(chunk)
                        usage_info = data.get("usage", {})
                    except (json.JSONDecodeError, ValueError, AttributeError):
                        pass  # usage 信息是可选的，解析失败不影响主功能
                else:
                    self.text_chunk.emit(chunk)
            self.finished.emit("", usage_info)
        except Exception as e:
            self.error.emit(str(e))


# ═══════════════════════════════════════════
# 主窗口
# ═══════════════════════════════════════════

class ChatWindow(QWidget):
    """
    OPCclaw 主窗口 - 类似 QClaw 的 AI Agent 对话框。

    特性:
    - 侧栏导航: 对话 / 云端模型 / 本地模型 / 技能 / 设置
    - 登录集成: 使用一人公司注册账号
    - 独立运行 + 可嵌入一人公司 APP

    用法:
        # 独立运行 (自动弹出登录)
        win = ChatWindow()
        win.show()

        # 嵌入一人公司 APP (无需登录, 传入用户上下文)
        win = ChatWindow(user_context={"username": "123", "role": "user"})
        layout.addWidget(win)
    """

    def __init__(self, user_context: Optional[dict] = None, parent=None):
        """
        Args:
            user_context: 用户上下文, 嵌入时传入。
                          {"username": "xxx", "role": "user|admin"}
                          为 None 时独立运行, 弹出登录对话框。
        """
        super().__init__(parent)
        self.setWindowTitle("OPCclaw - AI Agent 助手")
        self.setMinimumSize(900, 600)

        self.user_context = user_context

        # ── 核心组件 ──
        project_root = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), ".."
        )
        data_dir = os.path.join(project_root, "data")
        self.config = ConfigManager(data_dir)
        self.memory_store = MemoryStore()
        self.skill_loader = SkillLoader()
        self.registry = ToolRegistry()

        # ── 引擎状态 ──
        self.backend: BaseLLMBackend = None
        self.engine: ChatEngine = None
        self.worker: ChatWorker = None
        self.current_bubble: MessageBubble = None
        self.accumulated_text = ""

        # ── 多模型 ──
        self.multi_model_router: MultiModelRouter = None
        self.multi_model_enabled: bool = False
        self._multi_model_roles: dict = {}  # role_name → backend 的缓存
        self._multi_model_switch: QCheckBox = None  # 多模型开关
        self._multi_model_status_label: QLabel = None  # 状态指示
        self._agent_mode_switch: QCheckBox = None  # Agent 模式开关
        self.agent_mode_enabled: bool = False  # Agent 自主模式

        # Phase 2: 工作区索引 + RAG
        self._workspace_switch: QCheckBox = None  # 工作区 RAG 开关
        self._workspace_status_label: QLabel = None  # 状态标签
        self._workspace_btn_build: QPushButton = None  # 构建索引按钮
        self._workspace_btn_project: QPushButton = None  # 选择项目按钮
        self._workspace_project_path: str = ""  # 当前项目路径
        self._rag_injector: RAGContextInjector = RAGContextInjector()

        # ── 会话管理 ──
        self._session_id = self._load_last_session_id() or self._gen_session_id()
        self._session_combo: QComboBox = None
        self._quick_btns: list = []  # 快捷操作按钮
        
        # ── Token 统计 ──
        self._session_tokens = {"prompt": 0, "completion": 0, "total": 0}  # 当前会话累计
        self._token_label: QLabel = None  # Token 显示标签

        # ── 语音功能 ──
        self._voice_manager = None
        self._tts_enabled = True
        try:
            self._voice_manager = VoiceManager()
            self._voice_manager.text_ready.connect(self._on_voice_text)
            self._voice_manager.input_error.connect(self._on_voice_error)
            self._voice_manager.listening_state.connect(self._on_listening_state)
            self._voice_manager.tts_error.connect(lambda msg: self._add_message(f"🔊 {msg}", "error"))
        except Exception as e:
            logger.error(f"[OPCclaw] Voice init failed: {e}")
            self._voice_manager = None

        # 初始化技能
        self._init_skills()

        # 构建 UI
        self._init_ui()

        # 注册工具
        self._register_tools()

        # 尝试加载活跃的 LLM 配置
        self._apply_provider()

        # 恢复历史
        self._restore_history()

        # 刷新会话列表
        self._refresh_sessions()

        # 检查是否需要配置 API Key（首次使用或 Key 为空）
        QTimer.singleShot(500, self._check_api_key_config)

        # AI助手嵌入一人公司APP，无需独立登录
        if self.user_context is None:
            self.user_context = {"username": "user", "role": "user"}

    # ── API Key 检查 ──

    def _check_api_key_config(self):
        """延迟检查 API Key 配置，首次启动时若未配置则提示"""
        cfg = self.config.get_active_provider()
        if cfg and cfg.api_key:
            return  # 已配置，无需提示
        ptype = self.config._data.get("active_provider_type", "cloud")
        if not cfg:
            if not self.config._data.get("cloud_providers") and not self.config._data.get("local_providers"):
                self._add_message(
                    "👋 欢迎使用 OPCclaw!\n\n"
                    "开始前请先配置 LLM 供应商:\n"
                    "1. 点击左侧 ☁️ 云端模型\n"
                    "2. 点击 + 添加供应商\n"
                    "3. 输入 API Key 并测试保存",
                    "tool"
                )
        elif ptype == "cloud" and not cfg.api_key:
            self._add_message(
                f"🔑 供应商 {cfg.name} 缺少 API Key\n"
                f"请点击左侧 ☁️ 云端模型 → 双击 {cfg.name} 填入 Key",
                "tool"
            )

    # ── 技能初始化 ──

    def _init_skills(self):
        try:
            project_root = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), ".."
            )
            builtin = os.path.join(project_root, "skills", "builtin")
            self.skill_loader.add_dir(builtin)
            user_skills = os.path.expanduser("~/.opcclaw/skills")
            self.skill_loader.add_dir(user_skills)
            count = self.skill_loader.load_all()
            logger.info(f"[OPCclaw] {count} skills loaded: {self.skill_loader.list_names()}")

        # ── UI 构建 ──

        except Exception:
            pass  # SkillLoader API mismatch

    def _get_skills_context(self):
        """安全获取技能上下文，避免 SkillLoader API 不匹配崩溃"""
        try:
            # 尝试新版 API
            if hasattr(self.skill_loader, 'get_all_skill_summaries'):
                return self.skill_loader.get_all_skill_summaries()
            # 尝试其他方式
            if hasattr(self.skill_loader, 'build_skills_prompt'):
                return self.skill_loader.build_skills_prompt()
            if hasattr(self.skill_loader, 'list_skills'):
                names = self.skill_loader.list_skills()
                return f"可用技能: {', '.join(names)}" if names else ""
        except Exception:
            pass
        return ""  # 降级：没有技能上下文


    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 顶部栏 ──
        header = QFrame()
        header.setStyleSheet(f"background: {COLORS['header']}; padding: 10px 20px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)

        self.title_label = QLabel("OPCclaw")
        self.title_label.setFont(QFont("PingFang SC", 16, QFont.Bold))
        self.title_label.setStyleSheet(f"color: white;")
        header_layout.addWidget(self.title_label)

        self.user_label = QLabel("未登录")
        self.user_label.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        header_layout.addWidget(self.user_label)
        header_layout.addStretch()

        # 会话选择器
        self._session_combo = QComboBox()
        self._session_combo.setMinimumWidth(140)
        self._session_combo.setStyleSheet(f"""
            QComboBox {{
                color: white;
                background: rgba(255,255,255,0.12);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{ border: none; width: 18px; }}
            QComboBox QAbstractItemView {{
                color: {COLORS['text']};
                background: {COLORS['card']};
                selection-background-color: {COLORS['primary']};
            }}
        """)
        self._session_combo.activated.connect(self._on_session_switch)
        header_layout.addWidget(self._session_combo)

        new_session_btn = QPushButton("新建会话")
        new_session_btn.setFixedSize(90, 32)
        new_session_btn.setStyleSheet(f"""
            QPushButton {{
                color: #FFFFFF;
                background: rgba(100, 180, 255, 0.6);
                border: 1px solid rgba(100, 180, 255, 0.8);
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: rgba(100, 180, 255, 0.85); }}
        """)
        new_session_btn.clicked.connect(self._on_new_session)
        header_layout.addWidget(new_session_btn)

        self.model_label = QLabel("无活跃模型")
        self.model_label.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        header_layout.addWidget(self.model_label)
        
        # Token 用量标签（空时隐藏）
        self._token_label = QLabel("")
        self._token_label.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 11px; padding: 2px 8px;")
        self._token_label.setToolTip("本轮 / 会话累计 Token 用量")
        self._token_label.hide()
        header_layout.addWidget(self._token_label)

        logout_btn = QPushButton("登出")
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                color: {COLORS['text_light']};
                background: transparent;
                border: 1px solid {COLORS['text_light']};
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{ color: white; border-color: white; }}
        """)
        logout_btn.clicked.connect(self._logout)
        header_layout.addWidget(logout_btn)

        main_layout.addWidget(header)

        # ── 主体: 侧栏 + 内容 ──
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.nav_changed.connect(self._on_nav_changed)
        body_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        body_layout.addWidget(self.stack, stretch=1)

        # ── 0: 对话面板 ──
        self.chat_panel = self._build_chat_panel()
        self.stack.addWidget(self.chat_panel)

        # ── 1: 云端模型面板 ──
        self.cloud_panel = CloudModelPanel(self.config)
        self.cloud_panel.providers_changed.connect(self._apply_provider)
        # 多模型路由配置（追加到云端模型面板底部）
        self._add_multi_model_section(self.cloud_panel.layout())
        self._add_workspace_section(self.cloud_panel.layout())
        self.stack.addWidget(self.cloud_panel)

        # ── 2: 本地模型面板 ──
        self.local_panel = LocalModelPanel(self.config)
        self.local_panel.providers_changed.connect(self._apply_provider)
        self.stack.addWidget(self.local_panel)

        # ── 3: 技能管理 ──
        try:
            self.skills_panel = SkillsPanel(self.config, self.skill_loader)
        except Exception:
            self.skills_panel = QLabel("技能面板未初始化")
            self.skills_panel.setStyleSheet("color: #888; padding: 20px;")
        self.skills_panel.skills_changed.connect(lambda: (
            self.engine.refresh_skills() if self.engine else None
        ))
        self.stack.addWidget(self.skills_panel)

        # ── 4: 通用设置 ──
        self.settings_panel = GeneralSettingsPanel(self.config, self.memory_store)
        self.settings_panel.settings_changed.connect(self._apply_provider)
        self.stack.addWidget(self.settings_panel)

        # ── 5: Git 面板 ──
        from opcclaw.modules.git_panel import GitPanel
        self.git_panel = GitPanel()
        self.stack.addWidget(self.git_panel)

        main_layout.addWidget(body, stretch=1)

        self._update_user_display()

    def _build_chat_panel(self) -> QWidget:
        """构建对话面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 消息区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"QScrollArea {{ border: none; background: {COLORS['bg']}; }}")

        self.msg_container = QWidget()
        self.msg_container.setStyleSheet(f"background: {COLORS['bg']};")
        self.msg_layout = QVBoxLayout(self.msg_container)
        self.msg_layout.setAlignment(Qt.AlignTop)
        self.msg_layout.setSpacing(6)
        self.msg_layout.addStretch()

        self.scroll_area.setWidget(self.msg_container)
        layout.addWidget(self.scroll_area, stretch=1)

        # ── 快捷操作栏 ──
        quick_frame = QFrame()
        quick_frame.setStyleSheet(f"background: white; border-top: 1px solid {COLORS['border']};")
        quick_layout = QHBoxLayout(quick_frame)
        quick_layout.setContentsMargins(12, 8, 12, 8)
        quick_layout.setSpacing(8)

        quick_actions = [
            ("📊 营收", "#27AE60", "帮我查询营收概况"),
            ("📝 订单", "#2980B9", "帮我查询最近的订单"),
            ("📦 库存", "#8E44AD", "帮我查询产品库存"),
            ("👥 会员", "#E67E22", "帮我查询会员到期情况"),
            ("💰 财务", "#2C3E50", "帮我查询财务收支概况"),
            ("👷 员工", "#16A085", "帮我查询员工列表"),
        ]

        for label, color, prompt in quick_actions:
            btn = QPushButton(label)
            btn.setMinimumHeight(34)
            btn.setFont(QFont("PingFang SC", 11))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 14px;
                }}
                QPushButton:hover {{ opacity: 0.85; }}
                QPushButton:disabled {{ background: #BDC3C7; color: #999; }}
                QPushButton:pressed {{ padding-top: 7px; padding-bottom: 5px; }}
            """)
            btn.clicked.connect(lambda checked, p=prompt: self._quick_action(p))
            btn.setEnabled(False)
            self._quick_btns.append(btn)
            # 添加悬停缩放动画
            ButtonAnimationHelper.apply_scale_animation(btn, 1.05)
            quick_layout.addWidget(btn)

        quick_layout.addStretch()

        # 清空对话
        clear_btn = QPushButton("🧹 清空")
        clear_btn.setMinimumHeight(34)
        clear_btn.setFont(QFont("PingFang SC", 11))
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['danger']};
                border: 1px solid {COLORS['danger']};
                border-radius: 6px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{ background: {COLORS['danger']}; color: white; }}
            QPushButton:pressed {{ padding-top: 7px; padding-bottom: 5px; }}
        """)
        clear_btn.clicked.connect(self._clear_chat)
        # 添加悬停缩放动画
        ButtonAnimationHelper.apply_scale_animation(clear_btn, 1.05)
        quick_layout.addWidget(clear_btn)

        layout.addWidget(quick_frame)

        # 输入区
        input_frame = QFrame()
        input_frame.setStyleSheet(f"background: white; border-top: 1px solid {COLORS['border']};")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(16, 12, 16, 12)

        self.input_field = QTextEdit()
        self._input = self.input_field  # 兼容 ai_assistant_window 的引用
        self.input_field.setPlaceholderText("输入消息, Ctrl+Enter 发送...")
        self.input_field.setMaximumHeight(100)
        self.input_field.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                background: {COLORS['input_bg']};
            }}
            QTextEdit:focus {{ border-color: {COLORS['primary']}; background: white; }}
        """)
        self.input_field.installEventFilter(self)
        input_layout.addWidget(self.input_field, stretch=1)

        self.send_btn = QPushButton("发送")
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {COLORS['primary_hover']}; }}
            QPushButton:disabled {{ background: #BDC3C7; }}
            QPushButton:pressed {{ padding-top: 11px; padding-bottom: 9px; }}
        """)
        self.send_btn.clicked.connect(self._send_message)
        self.send_btn.setEnabled(False)
        # 添加悬停缩放动画
        ButtonAnimationHelper.apply_scale_animation(self.send_btn, 1.03)
        input_layout.addWidget(self.send_btn)

        # 语音输入按钮
        self.voice_btn = QPushButton("🎤")
        self.voice_btn.setFixedSize(40, 40)
        self.voice_btn.setToolTip("语音输入 (点击开始说话)")
        self.voice_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['secondary']};
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 16px;
            }}
            QPushButton:hover {{ background: {COLORS['secondary_hover']}; }}
            QPushButton:disabled {{ background: #BDC3C7; }}
            QPushButton[listening="true"] {{
                background: #E74C3C;
                animation: pulse 1s infinite;
            }}
            QPushButton:pressed {{ padding-top: 1px; padding-bottom: -1px; }}
        """)
        self.voice_btn.clicked.connect(self._toggle_voice_input)
        # 添加悬停缩放动画
        ButtonAnimationHelper.apply_scale_animation(self.voice_btn, 1.1)
        input_layout.addWidget(self.voice_btn)

        # 语音播报开关
        self.tts_btn = QPushButton("🔊")
        self.tts_btn.setFixedSize(40, 40)
        self.tts_btn.setToolTip("语音播报: 开启")
        self.tts_btn.setCheckable(True)
        self.tts_btn.setChecked(True)
        self.tts_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['success']};
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 16px;
            }}
            QPushButton:hover {{ background: #27AE60; }}
            QPushButton:checked {{ background: {COLORS['success']}; }}
            QPushButton:!checked {{ background: #BDC3C7; }}
            QPushButton:pressed {{ padding-top: 1px; padding-bottom: -1px; }}
        """)
        self.tts_btn.clicked.connect(self._toggle_tts)
        # 添加悬停缩放动画
        ButtonAnimationHelper.apply_scale_animation(self.tts_btn, 1.1)
        input_layout.addWidget(self.tts_btn)

        layout.addWidget(input_frame)
        return panel

    def eventFilter(self, obj, event):
        if obj == self.input_field and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
                self._send_message()
                return True
        return super().eventFilter(obj, event)

    def _on_nav_changed(self, idx: int):
        self.stack.setCurrentIndex(idx)
        # 切换到 Git 面板时自动刷新
        if idx == 5 and hasattr(self, 'git_panel'):
            self.git_panel._refresh()

    # ── 登录 ──

    def _show_login(self):
        """弹出登录对话框"""
        dlg = LoginDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            # 不用 dlg 直接读, 等信号
            pass
        else:
            # 用户关闭了登录, 仍然显示窗口但不登录
            self._add_message("已取消登录。请配置 LLM 供应商后开始对话。", "tool")
            return

    def _handle_login_success(self, ctx: dict):
        self.user_context = ctx
        self._update_user_display()
        self._add_message(
            f"欢迎回来, {ctx.get('username', '用户')}! 👋\n我是 OPCclaw, 你的 AI Agent 助手。",
            "ai"
        )

    def _update_user_display(self):
        if self.user_context:
            u = self.user_context.get("username", "?")
            self.user_label.setText(f"👤 {u}")
            self.title_label.setText(f"OPCclaw")
        else:
            self.user_label.setText("未登录")

    def _logout(self):
        self.user_context = {"username": "user", "role": "user"}
        self._update_user_display()
        self._add_message("已登出。当前使用默认用户身份。", "tool")

    # ── LLM 引擎 ──

    def _apply_provider(self):
        """加载活跃的 LLM 供应商配置, 重建引擎"""
        cfg = self.config.get_active_provider()
        if not cfg:
            self.model_label.setText("⚠️ 未选择模型")
            self.send_btn.setEnabled(False)
            self._set_quick_btns_enabled(False)
            self._add_message(
                "👋 欢迎使用 OPCclaw!\n\n"
                "开始前请先配置 LLM 供应商:\n"
                "1. 点击左侧 ☁️ 云端模型\n"
                "2. 点击 + 添加供应商, 选择 DeepSeek 模板\n"
                "3. 输入你的 API Key\n"
                "4. 点击 测试并保存\n\n"
                "💡 也支持本地模型 (Ollama/LM Studio), 在 🖥️ 本地模型 中配置。",
                "tool"
            )
            return

        ptype = self.config._data["active_provider_type"]

        # 云端模型必须有 API Key
        if ptype == "cloud" and not cfg.api_key:
            self.model_label.setText("🔑 需要 API Key")
            self.send_btn.setEnabled(False)
            self._set_quick_btns_enabled(False)
            self._add_message(
                f"🔑 {cfg.name} 已配置, 但缺少 API Key。\n"
                "请点击左侧 ☁️ 云端模型 → 双击 {0} → 填入 Key。".format(cfg.name),
                "tool"
            )
            return

        try:
            self.backend = BackendFactory.create(cfg)
        except Exception as e:
            self.model_label.setText(f"❌ {e}")
            self._add_message(f"❌ 无法连接 {cfg.name}: {e}", "tool")
            return

        # 多模型状态恢复：开关已开但 router 为空 → 自动配置
        if self.multi_model_enabled and self.multi_model_router and not self.multi_model_router.has_multi_model():
            self._auto_config_multi_model()

        type_label = "☁️" if ptype == "cloud" else "🖥️"

        # 构建增强 system prompt，注入技能上下文和工具列表
        tool_names = self.registry.list_tools() if self.registry else []
        tool_summary = ', '.join(sorted(tool_names)) if tool_names else "无"
        skills_ctx = self._get_skills_context()

        system_prompt = (
            "你是 OPCclaw, 一人公司管理系统中的 AI Agent 助手。\n"
            "用中文回复, 保持简洁、专业、友好。主动使用工具完成任务。\n\n"
            f"[可用工具 {len(tool_names)} 个]\n{tool_summary}\n\n"
            f"{skills_ctx}"
        )

        # ── 创建引擎（支持多模型）──
        if self.multi_model_enabled and self.multi_model_router:
            # 多模型模式：创建 MultiModelChatEngine
            self.engine = MultiModelChatEngine(
                router=self.multi_model_router,
                backend=self.backend,
                registry=self.registry,
                system_prompt=system_prompt,
                skill_loader=self.skill_loader,
                memory_store=self.memory_store,
                auto_save=self.config.get_general("auto_save", True),
                session_id=self._session_id,
            )
            self.engine.on_model_switch.connect(self._on_model_switch)
            self._update_multi_model_status()
        else:
            # 单模型模式
            self.engine = ChatEngine(
                self.backend,
                self.registry,
                system_prompt=system_prompt,
                skill_loader=self.skill_loader,
                memory_store=self.memory_store,
                auto_save=self.config.get_general("auto_save", True),
                session_id=self._session_id,
            )

        # Agent 自主模式：包装 ChatEngine
        if self.agent_mode_enabled:
            self.engine = AgentLoop(self.engine)

        self.engine.on_tool_start.connect(self._on_tool_start)
        self.engine.on_tool_result.connect(self._on_tool_result)

        # 模型标签
        if self.multi_model_enabled:
            self.model_label.setText(f"🧠 多模型 · {type_label} {cfg.name}")
        elif self.agent_mode_enabled:
            self.model_label.setText(f"🤖 Agent · {type_label} {cfg.name} | {cfg.model}")
        else:
            self.model_label.setText(f"{type_label} {cfg.name} | {cfg.model}")
        self.send_btn.setEnabled(True)
        self._set_quick_btns_enabled(True)
        
        # 更新工具数量显示
        tool_count = self.registry.count() if self.registry else 0
        if hasattr(self, 'tool_count_label'):
            self.tool_count_label.setText(f"🛠️ {tool_count} 工具")

        ptype_cn = "云端" if ptype == "cloud" else "本地"
        self._add_message(f"✅ 已连接 {ptype_cn}模型: {cfg.name} ({cfg.model})", "tool")

    # ── 工具注册 ──

    def _register_tools(self):
        register_system_tools(self.registry)
        self._register_business_tools()
        register_developer_tools(self.registry)
        register_git_tools(self.registry)
        register_code_tools(self.registry)
    def _register_business_tools(self):
        data_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", "data"
        )
        register_business_tools(self.registry, data_dir)

    # ── 工具回调 ──

    def _on_tool_start(self, name: str, args: dict):
        self._add_message(f"🔧 调用: {name}({json.dumps(args, ensure_ascii=False)[:100]})", "tool")

    def _on_tool_result(self, name: str, success: bool, preview: str):
        tag = "✅" if success else "❌"
        self._add_message(f"{tag} [{name}] {preview[:300]}", "tool" if success else "error")

    # ── 多模型回调 ──

    def _on_model_switch(self, task_type: str, model_name: str):
        """多模型路由切换时回调"""
        task_names = {
            "chat": "闲聊", "code": "编程", "analysis": "分析",
            "reasoning": "推理", "tools": "工具", "vision": "视觉",
        }
        task_cn = task_names.get(task_type, task_type)
        self._update_multi_model_status()
        self._add_message(
            f"🧠 任务分类: {task_cn} → 路由到 {model_name}", "tool"
        )

    def _update_multi_model_status(self):
        """更新多模型状态指示器"""
        if not self._multi_model_status_label:
            return
        if self.multi_model_enabled and hasattr(self, 'engine') and self.engine:
            model_name = getattr(self.engine, 'current_model_name', '未知')
            self._multi_model_status_label.setText(f"🧠 {model_name}")
            self._multi_model_status_label.setStyleSheet(
                f"color: {COLORS['primary']}; font-weight: bold; font-size: 12px;"
            )
        else:
            self._multi_model_status_label.setText("")
            self._multi_model_status_label.setStyleSheet("")

    def _build_multi_model_router(self) -> MultiModelRouter:
        """从已保存的供应商配置构建多模型路由器"""
        router = MultiModelRouter()

        # 角色映射：从 profile_config 或 providers 中读取
        mm_config = self.config._data.get("multi_model", {})
        if not mm_config:
            return router

        provider_data = self.config._data.get("providers", {}).get("cloud", {})

        # 按角色注册模型
        role_configs = mm_config.get("roles", {})
        for role_name, role_info in role_configs.items():
            provider_id = role_info.get("provider_id", "")
            provider = provider_data.get(provider_id, {})
            if not provider:
                continue
            try:
                cfg = ProviderConfig.from_dict(provider)
                backend = BackendFactory.create(cfg)
                router.register_role(
                    name=role_name,
                    backend=backend,
                    priority=role_info.get("priority", 0),
                    fallback_role=role_info.get("fallback_role", ""),
                )
            except Exception as e:
                logger.warning(f"多模型角色 {role_name} 注册失败: {e}")

        return router

    # ── 多模型 UI ──

    def _add_multi_model_section(self, layout: QVBoxLayout):
        """在侧边栏添加多模型配置区域"""
        group = QGroupBox("🧠 多模型路由")
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLORS['text']};
                border: 2px solid {COLORS['primary']};
                border-radius: 8px;
                margin-top: 12px;
                padding: 16px 12px 12px 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
            }}
        """)
        mm_layout = QVBoxLayout(group)
        mm_layout.setSpacing(8)

        # 开关
        self._multi_model_switch = QCheckBox("启用多模型智能路由")
        self._multi_model_switch.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 13px;")
        self._multi_model_switch.toggled.connect(self._on_multi_model_toggled)
        mm_layout.addWidget(self._multi_model_switch)

        # 说明
        desc = QLabel(
            "不同任务自动选择最优模型:\n"
            "  💬 闲聊 → 快速模型  |  📊 分析 → 深度模型\n"
            "  💻 编程 → 深度模型  |  🧩 推理 → 推理模型"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 11px; padding: 4px 0;")
        mm_layout.addWidget(desc)

        # 状态标签
        self._multi_model_status_label = QLabel("")
        self._multi_model_status_label.setWordWrap(True)
        mm_layout.addWidget(self._multi_model_status_label)

        # Agent 自主模式开关
        self._agent_mode_switch = QCheckBox("🤖 Agent 自主模式（对标 Codex）")
        self._agent_mode_switch.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 13px; margin-top: 8px;")
        self._agent_mode_switch.toggled.connect(self._on_agent_mode_toggled)
        mm_layout.addWidget(self._agent_mode_switch)

        agent_desc = QLabel(
            "Think → Plan → Act → Observe → Reflect\n"
            "自主多步执行，自动纠错，最高 50 轮迭代"
        )
        agent_desc.setWordWrap(True)
        agent_desc.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 11px; padding: 0 0 4px 20px;")
        mm_layout.addWidget(agent_desc)

        layout.addWidget(group)

        # 恢复上次的多模型开关状态
        if self.config._data.get("multi_model", {}).get("enabled", False):
            self._multi_model_switch.setChecked(True)

        # 恢复上次的 Agent 模式状态
        if self.config._data.get("multi_model", {}).get("agent_mode", False):
            self._agent_mode_switch.setChecked(True)

    def _on_multi_model_toggled(self, checked: bool):
        """多模型开关切换"""
        self.multi_model_enabled = checked
        self.config._data.setdefault("multi_model", {})["enabled"] = checked
        self.config.save()

        if checked:
            # 尝试构建路由器
            self.multi_model_router = self._build_multi_model_router()
            if not self.multi_model_router.has_multi_model():
                # 没有足够的模型，使用当前连接的主模型 + 同一供应商的其他模型
                self._auto_config_multi_model()

            if self.multi_model_router.has_multi_model():
                role_count = self.multi_model_router.role_count()
                self._multi_model_status_label.setText(f"✅ 已激活 {role_count} 个模型角色")
                self._multi_model_status_label.setStyleSheet(
                    f"color: {COLORS['success']}; font-size: 12px; font-weight: bold;"
                )
                # 如果已连接，重新创建引擎
                if self.backend:
                    self._reconnect_with_multi_model()
            else:
                self._multi_model_status_label.setText(
                    "⚠️ 需要先注册至少 2 个模型角色\n请先添加多个云端供应商"
                )
                self._multi_model_status_label.setStyleSheet(
                    f"color: {COLORS['warning']}; font-size: 12px;"
                )
        else:
            self._multi_model_status_label.setText("")
            if self.backend:
                self._reconnect_with_multi_model()  # 重新创建为单模型引擎

    def _on_agent_mode_toggled(self, checked: bool):
        """Agent 自主模式开关切换"""
        self.agent_mode_enabled = checked
        self.config._data.setdefault("multi_model", {})["agent_mode"] = checked
        self.config.save()

        if self.backend:
            self._reconnect_with_multi_model()

    # ═══════════════════════════════════════════
    # Phase 2: 工作区索引 + RAG
    # ═══════════════════════════════════════════

    def _add_workspace_section(self, layout: QVBoxLayout):
        """在侧边栏添加工作区 RAG 配置区域"""
        group = QGroupBox("📂 工作区上下文（RAG）")
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLORS['text']};
                border: 2px solid {COLORS['secondary']};
                border-radius: 8px;
                margin-top: 12px;
                padding: 16px 12px 12px 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
            }}
        """)
        ws_layout = QVBoxLayout(group)
        ws_layout.setSpacing(8)

        # 选择项目按钮
        self._workspace_btn_project = QPushButton("📁 选择项目目录...")
        self._workspace_btn_project.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_alt']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }}
            QPushButton:hover {{ border-color: {COLORS['primary']}; }}
        """)
        self._workspace_btn_project.clicked.connect(self._on_select_workspace)
        ws_layout.addWidget(self._workspace_btn_project)

        # 状态标签
        self._workspace_status_label = QLabel("未选择项目")
        self._workspace_status_label.setWordWrap(True)
        self._workspace_status_label.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px; padding: 2px 0;")
        ws_layout.addWidget(self._workspace_status_label)

        # 构建索引按钮
        self._workspace_btn_build = QPushButton("🔨 构建/更新代码索引")
        self._workspace_btn_build.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['secondary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
            QPushButton:disabled {{ background: {COLORS['bg_alt']}; color: {COLORS['border']}; }}
        """)
        self._workspace_btn_build.clicked.connect(self._on_build_workspace_index)
        self._workspace_btn_build.setEnabled(False)
        ws_layout.addWidget(self._workspace_btn_build)

        # RAG 开关
        self._workspace_switch = QCheckBox("自动注入代码上下文")
        self._workspace_switch.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 13px;")
        self._workspace_switch.toggled.connect(self._on_workspace_rag_toggled)
        self._workspace_switch.setEnabled(False)
        ws_layout.addWidget(self._workspace_switch)

        desc = QLabel(
            "将项目代码自动注入 AI 上下文。\n"
            "每次提问时，AI 能看到最相关的代码文件。\n"
            "支持 .gitignore、增量索引、BM25 检索。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 11px; padding: 4px 0;")
        ws_layout.addWidget(desc)

        layout.addWidget(group)

        # 恢复上次状态
        ws_cfg = self.config._data.get("workspace", {})
        if ws_cfg.get("project_path"):
            self._restore_workspace(ws_cfg["project_path"])

    def _on_select_workspace(self):
        """选择项目工作区目录"""
        from PyQt5.QtWidgets import QFileDialog
        path = QFileDialog.getExistingDirectory(self, "选择项目目录", os.path.expanduser("~"))
        if not path:
            return
        self._set_workspace_project(path)

    def _set_workspace_project(self, path: str):
        """设置项目路径并启用索引"""
        self._workspace_project_path = path
        self._rag_injector.set_project(path)
        self._workspace_btn_build.setEnabled(True)
        self._workspace_switch.setEnabled(True)
        self._workspace_status_label.setText(f"📁 {os.path.basename(path)}\n{path}")
        self._workspace_status_label.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px;")
        self._workspace_btn_project.setText("📁 更换项目目录...")

        # 保存配置
        self.config._data.setdefault("workspace", {})["project_path"] = path
        self.config.save()

    def _restore_workspace(self, path: str):
        """恢复上次的工作区设置"""
        if os.path.isdir(path):
            self._set_workspace_project(path)

    def _on_build_workspace_index(self):
        """构建/更新工作区索引"""
        if not self._workspace_project_path:
            return

        self._workspace_btn_build.setText("⏳ 索引中...")
        self._workspace_btn_build.setEnabled(False)
        QApplication.processEvents()

        try:
            stats = self._rag_injector.build_index()
            self._workspace_status_label.setText(
                f"📁 {os.path.basename(self._workspace_project_path)}\n"
                f"✅ {stats.total_files} 文件, {stats.total_chunks} 块 | "
                f"{stats.total_size_bytes / 1024:.0f} KB | "
                f"耗时 {stats.last_build_time:.1f}s"
            )
            self._workspace_status_label.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px;")
            self._workspace_switch.setEnabled(True)
            # 默认开启 RAG
            if not self._workspace_switch.isChecked():
                self._workspace_switch.setChecked(True)
        except Exception as e:
            self._workspace_status_label.setText(f"❌ 索引失败: {e}")
            self._workspace_status_label.setStyleSheet(f"color: {COLORS['error']}; font-size: 12px;")

        self._workspace_btn_build.setText("🔨 重新构建索引")
        self._workspace_btn_build.setEnabled(True)

    def _on_workspace_rag_toggled(self, checked: bool):
        """工作区 RAG 开关切换"""
        self._rag_injector.enabled = checked
        self.config._data.setdefault("workspace", {})["rag_enabled"] = checked
        self.config.save()

    def _auto_config_multi_model(self):
        """自动配置多模型：使用主模型的同一 API Key 尝试不同模型"""
        if not self.backend:
            return

        cfg = self.backend.config
        router = self.multi_model_router or MultiModelRouter()
        base_url = cfg.base_url
        api_key = cfg.api_key

        # 角色 → 模型建议（同一供应商下）
        role_models = {
            "deep": _guess_deep_model(cfg.model),
            "reasoning": _guess_reasoning_model(cfg.model),
        }

        for role_name, model_name in role_models.items():
            if not model_name or model_name == cfg.model:
                continue
            try:
                role_cfg = ProviderConfig(
                    name=f"{cfg.name}-{role_name}",
                    provider_type="openai_compatible",
                    base_url=base_url,
                    api_key=api_key,
                    model=model_name,
                )
                backend = BackendFactory.create(role_cfg)
                router.register_role(
                    name=role_name,
                    backend=backend,
                    priority=1 if role_name == "deep" else 0,
                    fallback_role="fast",
                )
            except Exception as e:
                logger.debug(f"自动配置 {role_name} 模型失败: {e}")

        # 主模型作为 fast 角色
        router.register_role(
            name="fast",
            backend=self.backend,
            priority=0,
            fallback_role="deep",
        )

        self.multi_model_router = router

    def _reconnect_with_multi_model(self):
        """用多模型模式重新连接"""
        if not self.backend:
            return
        self._apply_provider()

    def _update_token_usage(self, usage: dict):
        """更新 Token 用量显示"""
        prompt_tokens = usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0) or usage.get("output_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
        
        if not total_tokens and (prompt_tokens or completion_tokens):
            total_tokens = prompt_tokens + completion_tokens
        
        # 累加到会话统计
        self._session_tokens["prompt"] += prompt_tokens
        self._session_tokens["completion"] += completion_tokens
        self._session_tokens["total"] += total_tokens
        
        # 更新显示
        if self._token_label:
            self._token_label.setText(
                f"💰 Token: 本轮 ↑{prompt_tokens} ↓{completion_tokens} = {total_tokens} | "
                f"会话 ↑{self._session_tokens['prompt']} ↓{self._session_tokens['completion']} = {self._session_tokens['total']}"
            )
            self._token_label.show()
    
    def _reset_token_stats(self):
        """重置 Token 统计"""
        self._session_tokens = {"prompt": 0, "completion": 0, "total": 0}
        if self._token_label:
            self._token_label.setText("💰 Token: 本轮 0 | 会话 0")
            self._token_label.show()

    # ── 语音控制 ──

    def _on_voice_text(self, text: str):
        """语音识别结果回调"""
        if text and self.input_box:
            # 追加到输入框末尾
            current = self.input_box.toPlainText()
            if current:
                self.input_box.setPlainText(current + text)
            else:
                self.input_box.setPlainText(text)
            self._add_message(f"🎤 语音输入: {text[:50]}{'...' if len(text) > 50 else ''}", "tool")

    def _on_voice_error(self, error_msg: str):
        """语音识别错误回调"""
        self._add_message(f"🎤 语音识别失败: {error_msg}", "error")
        if self.voice_btn:
            self.voice_btn.setProperty("listening", False)
            self.voice_btn.style().unpolish(self.voice_btn)
            self.voice_btn.style().polish(self.voice_btn)

    def _on_listening_state(self, is_listening: bool):
        """监听状态变化回调"""
        if self.voice_btn:
            self.voice_btn.setProperty("listening", is_listening)
            self.voice_btn.style().unpolish(self.voice_btn)
            self.voice_btn.style().polish(self.voice_btn)
            if is_listening:
                self.voice_btn.setToolTip("正在聆听... (点击停止)")
            else:
                self.voice_btn.setToolTip("语音输入")

    def _toggle_voice_input(self):
        """切换语音输入开关"""
        if not hasattr(self, '_voice_manager') or not self._voice_manager:
            self._add_message("🎤 语音功能未初始化", "error")
            return

        if self._voice_manager.is_listening():
            self._voice_manager.stop_listening()
        else:
            self._voice_manager.start_listening(timeout=10)

    def _toggle_tts(self, checked: bool):
        """切换语音播报开关"""
        self._tts_enabled = checked
        if self.tts_btn:
            self.tts_btn.setToolTip(f"语音播报: {'开启' if checked else '关闭'}")
        status = "已开启" if checked else "已关闭"
        self._add_message(f"🔊 语音播报 {status}", "tool")

    # ── 消息管理 ──

    def _add_message(self, text: str, sender: str):
        if self.msg_layout.count() > 0:
            item = self.msg_layout.itemAt(self.msg_layout.count() - 1)
            if item.spacerItem():
                self.msg_layout.removeItem(item)

        bubble = MessageBubble(text, sender)

        # AI 消息的操作按钮信号连接
        if sender == "ai":
            bubble.like_clicked.connect(self._on_like_message)
            bubble.dislike_clicked.connect(self._on_dislike_message)
            bubble.play_clicked.connect(self._on_play_message)
            bubble.share_clicked.connect(self._on_share_message)

        # 使用水平布局包装，让气泡能获得合理的宽度（word-wrap 正常工作）
        wrapper = QHBoxLayout()
        wrapper.setContentsMargins(0, 0, 0, 0)
        if sender == "user":
            bubble.setMinimumWidth(100)
            wrapper.addStretch()
            wrapper.addWidget(bubble)
        else:
            wrapper.addWidget(bubble)
            wrapper.addStretch()

        self.msg_layout.addLayout(wrapper)
        self.msg_layout.addStretch()
        QTimer.singleShot(50, self._scroll_bottom)

    def _on_like_message(self, text: str):
        """点赞 AI 消息"""
        try:
            self._add_message("👍 感谢您的点赞！", "tool")
            QTimer.singleShot(100, self._scroll_bottom)
        except Exception as e:
            logger.error(f"[Chat] Error in like: {e}")

    def _on_dislike_message(self, text: str):
        """点踩 AI 消息"""
        try:
            self._add_message("📝 感谢反馈，我们会努力改进！", "tool")
            QTimer.singleShot(100, self._scroll_bottom)
        except Exception as e:
            logger.error(f"[Chat] Error in dislike: {e}")

    def _on_play_message(self, text: str):
        """播放 AI 消息全文"""
        if not text:
            return
        try:
            if not hasattr(self, '_voice_manager') or not self._voice_manager:
                self._add_message("🔊 语音功能未初始化", "error")
                QTimer.singleShot(100, self._scroll_bottom)
                return
            if not self._voice_manager.is_tts_available():
                self._add_message("🔊 当前没有可用的语音引擎", "error")
                QTimer.singleShot(100, self._scroll_bottom)
                return
            # 停止之前的播报
            self._voice_manager.stop_speaking()
            # 播放新内容
            self._voice_manager.speak(text)
        except Exception as e:
            logger.error(f"[Chat] Error in play: {e}")
            self._add_message(f"🔊 播放出错: {e}", "error")
            QTimer.singleShot(100, self._scroll_bottom)

    def _on_share_message(self, text: str):
        """分享 AI 消息 - 复制到剪贴板"""
        try:
            from PyQt5.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self._add_message("📋 已复制到剪贴板", "tool")
            QTimer.singleShot(100, self._scroll_bottom)
        except Exception as e:
            logger.error(f"[Chat] Error in share: {e}")

    def _ensure_streaming_bubble(self):
        if self.current_bubble and self.current_bubble.sender == "ai":
            return
        if self.msg_layout.count() > 0:
            item = self.msg_layout.itemAt(self.msg_layout.count() - 1)
            if item.spacerItem():
                self.msg_layout.removeItem(item)
        self.current_bubble = MessageBubble("", "ai")
        # 使用水平布局包装，让气泡能获得合理的宽度
        wrapper = QHBoxLayout()
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(self.current_bubble)
        wrapper.addStretch()
        self.msg_layout.addLayout(wrapper)
        self.msg_layout.addStretch()
        self.accumulated_text = ""

    def _scroll_bottom(self):
        vbar = self.scroll_area.verticalScrollBar()
        vbar.setValue(vbar.maximum())
        # 确保 viewport 正确更新，避免按钮点击无响应
        self.scroll_area.viewport().update()

    def _append_streaming_text(self, chunk: str):
        self._ensure_streaming_bubble()
        self.accumulated_text += chunk
        self.current_bubble.set_text(self.accumulated_text)
        self._scroll_bottom()

    # ── 发送消息 ──

    def send_message(self, message: str):
        """外部接口：双AI协作注入消息"""
        self.input_field.setPlainText(message)
        self._send_message()

    def _send_message(self):
        text = self.input_field.toPlainText().strip()
        if not text:
            return
        if not self.engine:
            self._add_message("⚠️ 请先在侧栏配置 LLM 模型 (云端或本地)", "error")
            return

        self._add_message(text, "user")
        self.input_field.clear()

        self.send_btn.setEnabled(False)
        self.send_btn.setText("思考中...")
        self.current_bubble = None
        self.accumulated_text = ""

        # 如果有正在运行的 worker, 先终止
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait(2000)

        self.worker = ChatWorker(self.engine, text)
        self.worker.text_chunk.connect(self._append_streaming_text)
        self.worker.finished.connect(self._on_chat_finished)
        self.worker.error.connect(self._on_chat_error)
        self.worker.start()

    def _on_chat_finished(self, _, usage_info: dict = None):
        # 保存会话到磁盘 (chat_stream 内部也会保存，这里做二次保障)
        if self.engine:
            self.engine.save()
            self._save_last_session(self._session_id)

        # 更新 Token 统计
        if usage_info:
            self._update_token_usage(usage_info)

        # 注意：语音播报已改为手动模式，用户点击 "🔊 播放全文" 按钮播放

        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送")
        self.current_bubble = None
        self.accumulated_text = ""
        self.worker = None

    def _on_chat_error(self, error_msg: str):
        # 即使出错也保存当前进度
        if self.engine:
            self.engine.save()
        self._add_message(f"❌ {error_msg}", "error")
        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送")
        self.current_bubble = None
        self.accumulated_text = ""
        self.worker = None

    def _restore_history(self):
        """恢复当前会话的历史消息到界面"""
        messages = self.memory_store.load_session(self._session_id)
        for msg in messages:
            if msg.get("role") == "system":
                continue
            content = msg.get("content", "")
            if not content:
                continue
            role = msg.get("role", "")
            if role == "user":
                self._add_message(content, "user")
            elif role == "assistant":
                self._add_message(content, "ai")
            elif role == "tool":
                self._add_message(f"🔧 {content[:200]}", "tool")

        if messages:
            self._add_message("─ 以上为历史消息 ─", "tool")

    # ── 会话管理 ──

    @staticmethod
    def _gen_session_id() -> str:
        """生成时间戳会话 ID"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _load_last_session_id(self) -> str:
        """从配置文件读取上次活跃的会话 ID"""
        try:
            last_file = os.path.join(self.memory_store.base_dir, "last_session.txt")
            if os.path.exists(last_file):
                with open(last_file, "r", encoding="utf-8") as f:
                    sid = f.read().strip()
                    if sid and os.path.exists(
                        os.path.join(self.memory_store.sessions_dir, f"{sid}.json")
                    ):
                        return sid
        except Exception:
            pass
        return ""

    def _save_last_session(self, sid: str):
        """保存当前会话 ID 到文件"""
        try:
            last_file = os.path.join(self.memory_store.base_dir, "last_session.txt")
            with open(last_file, "w", encoding="utf-8") as f:
                f.write(sid)
        except Exception:
            pass

    def _refresh_sessions(self):
        """刷新会话下拉列表"""
        if not self._session_combo:
            return
        self._session_combo.blockSignals(True)
        self._session_combo.clear()
        sessions = self.memory_store.list_sessions()
        for s in sessions:
            label = s["id"]
            # 用更新时间做友好显示
            updated = s.get("updated_at", "")[:16].replace("T", " ")
            if updated:
                label = f"{updated} | {s['id']}"
            self._session_combo.addItem(label, s["id"])
            if s["id"] == self._session_id:
                self._session_combo.setCurrentIndex(self._session_combo.count() - 1)
        self._session_combo.blockSignals(False)

    def _on_new_session(self):
        """创建新会话"""
        # 先保存当前会话
        if self.engine:
            self.memory_store.save_session(self.engine.get_history(), self._session_id)
        # 切换到新会话
        self._session_id = self._gen_session_id()
        self._save_last_session(self._session_id)
        # 清除界面并重建引擎
        self._clear_chat_messages()
        if self.engine:
            self.engine.session_id = self._session_id
            self.engine.reset()
        self._refresh_sessions()

    def _on_session_switch(self, idx: int):
        """切换到选中的会话"""
        if not self._session_combo or idx < 0:
            return
        new_id = self._session_combo.itemData(idx)
        if not new_id or new_id == self._session_id:
            return
        # 保存当前会话
        if self.engine:
            self.memory_store.save_session(self.engine.get_history(), self._session_id)
        # 切换
        self._session_id = new_id
        self._save_last_session(self._session_id)
        self._clear_chat_messages()
        if self.engine:
            self.engine.session_id = self._session_id
            self.engine.messages = self.memory_store.load_session(self._session_id)
            self.engine.initialize_session()
        self._restore_history()

    def _clear_chat_messages(self):
        """清空聊天界面的消息气泡"""
        def _clear_layout(layout):
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                elif child.layout():
                    _clear_layout(child.layout())
        # 移除除末尾 stretch 之外的所有子控件/子布局
        while self.msg_layout.count() > 1:
            item = self.msg_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                _clear_layout(item.layout())
        self.accumulated_text = ""
        self.current_bubble = None

    # ── 快捷操作 ──

    def _quick_action(self, prompt: str):
        """快捷操作: 直接发送预设 prompt"""
        if not self.engine or not self.send_btn.isEnabled():
            self._add_message("⚠️ 请先在左侧「☁️ 云端模型」配置 API Key。", "tool")
            return
        self.input_field.setPlainText(prompt)
        self._send_message()

    def _clear_chat(self):
        """清空对话"""
        reply = QMessageBox.question(
            self, "确认清空", "确定要清空当前对话吗?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._clear_chat_messages()
            if self.engine:
                self.engine.reset()
            self._add_message("🧹 对话已清空", "tool")

    def _set_quick_btns_enabled(self, enabled: bool):
        """启用/禁用快捷操作按钮"""
        for btn in self._quick_btns:
            btn.setEnabled(enabled)

    # ── 语音功能 ──

    def _toggle_voice_input(self):
        """切换语音输入状态"""
        if not self._voice_manager:
            self._add_message("🔊 语音功能不可用，请检查依赖是否安装", "error")
            return

        if not self._voice_manager.is_stt_available():
            self._add_message("🔊 语音识别依赖未安装，请安装 speech_recognition", "error")
            return

        if self._voice_manager.is_listening():
            self._voice_manager.stop_listening()
            self.voice_btn.setProperty("listening", "false")
            self.voice_btn.setStyleSheet(self.voice_btn.styleSheet())
            self.voice_btn.setToolTip("语音输入 (点击开始说话)")
        else:
            self._voice_manager.start_listening()
            self.voice_btn.setProperty("listening", "true")
            self.voice_btn.setStyleSheet(self.voice_btn.styleSheet())
            self.voice_btn.setToolTip("正在监听... (点击停止)")

    def _toggle_tts(self, checked: bool):
        """切换语音播报状态"""
        self._tts_enabled = checked
        if checked:
            self.tts_btn.setToolTip("语音播报: 开启")
        else:
            self.tts_btn.setToolTip("语音播报: 关闭")

    def _on_voice_text(self, text: str):
        """处理语音识别结果"""
        if text:
            self.input_field.setPlainText(text)
            self._add_message(f"🔊 识别结果: {text}", "tool")

    def _on_voice_error(self, error_msg: str):
        """处理语音识别错误"""
        self._add_message(f"🔊 {error_msg}", "error")

    def _on_listening_state(self, listening: bool):
        """处理监听状态变化"""
        if not listening:
            self.voice_btn.setProperty("listening", "false")
            self.voice_btn.setStyleSheet(self.voice_btn.styleSheet())
            self.voice_btn.setToolTip("语音输入 (点击开始说话)")

    def _speak_text(self, text: str):
        """语音播报文本"""
        if self._tts_enabled and self._voice_manager:
            self._voice_manager.speak(text)

    def closeEvent(self, event):
        """切换语音输入状态"""
        if not self._voice_manager:
            self._add_message("🔊 语音功能不可用，请检查依赖是否安装", "error")
            return

        if not self._voice_manager.is_stt_available():
            self._add_message("🔊 语音识别依赖未安装，请安装 speech_recognition", "error")
            return

        if self._voice_manager.is_listening():
            self._voice_manager.stop_listening()
            self.voice_btn.setProperty("listening", "false")
            self.voice_btn.setStyleSheet(self.voice_btn.styleSheet())
            self.voice_btn.setToolTip("语音输入 (点击开始说话)")
        else:
            self._voice_manager.start_listening()
            self.voice_btn.setProperty("listening", "true")
            self.voice_btn.setStyleSheet(self.voice_btn.styleSheet())
            self.voice_btn.setToolTip("正在监听... (点击停止)")

    def _toggle_tts(self, checked: bool):
        """切换语音播报状态"""
        self._tts_enabled = checked
        if checked:
            self.tts_btn.setToolTip("语音播报: 开启")
        else:
            self.tts_btn.setToolTip("语音播报: 关闭")

    def _on_voice_text(self, text: str):
        """处理语音识别结果"""
        if text:
            self.input_field.setPlainText(text)
            self._add_message(f"🔊 识别结果: {text}", "tool")

    def _on_voice_error(self, error_msg: str):
        """处理语音识别错误"""
        self._add_message(f"🔊 {error_msg}", "error")

    def _on_listening_state(self, listening: bool):
        """处理监听状态变化"""
        if not listening:
            self.voice_btn.setProperty("listening", "false")
            self.voice_btn.setStyleSheet(self.voice_btn.styleSheet())
            self.voice_btn.setToolTip("语音输入 (点击开始说话)")

    def _speak_text(self, text: str):
        """语音播报文本"""
        if self._tts_enabled and self._voice_manager:
            self._voice_manager.speak(text)

    def closeEvent(self, event):
        """关闭窗口时清理资源并保存会话"""
        # 1. 停止语音管理器（资源清理）
        if self._voice_manager:
            try:
                self._voice_manager.stop_speaking()
                self._voice_manager.stop_listening()
            except Exception:
                pass
        # 2. 保存当前会话
        if self.engine and self.memory_store:
            try:
                self.memory_store.save_session(self.engine.get_history(), self._session_id)
                self._save_last_session(self._session_id)
            except Exception:
                pass
        super().closeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        if self.user_context is None and not hasattr(self, "_login_shown"):
            self._login_shown = True


# ═══════════════════════════════════════════
# 多模型辅助函数
# ═══════════════════════════════════════════

def _guess_deep_model(current_model: str) -> str:
    """根据当前模型名猜测同供应商的深度模型"""
    model_lower = current_model.lower()
    mappings = {
        # DeepSeek 系列
        "deepseek-chat": "deepseek-reasoner",
        "deepseek-v3": "deepseek-r1",
        # Qwen 系列
        "qwen-turbo": "qwen-plus",
        "qwen-plus": "qwen-max",
        "qwen2.5-7b": "qwen2.5-32b",
        "qwen2.5-14b": "qwen2.5-72b",
        "qwen2.5-32b": "qwen2.5-72b",
        # OpenAI 系列
        "gpt-4o-mini": "gpt-4o",
        "gpt-4o": "o1",
        "gpt-4-turbo": "gpt-4o",
        # Claude 系列
        "claude-3-haiku": "claude-3.5-sonnet",
        "claude-3.5-haiku": "claude-3.5-sonnet",
        "claude-sonnet": "claude-opus",
        # Gemini 系列
        "gemini-1.5-flash": "gemini-1.5-pro",
        "gemini-2.0-flash": "gemini-2.0-pro",
        # GLM 系列
        "glm-4-flash": "glm-4-plus",
        "glm-4": "glm-4-plus",
        # 通用 fallback
    }
    for key, value in mappings.items():
        if key in model_lower:
            return value
    return ""


def _guess_reasoning_model(current_model: str) -> str:
    """根据当前模型名猜测同供应商的推理模型"""
    model_lower = current_model.lower()
    mappings = {
        # DeepSeek 系列
        "deepseek-chat": "deepseek-reasoner",
        "deepseek-v3": "deepseek-r1",
        "deepseek": "deepseek-reasoner",
        # OpenAI 系列
        "gpt-4o-mini": "o1-mini",
        "gpt-4o": "o1",
        "gpt-4-turbo": "o1",
        # Qwen 系列
        "qwen-turbo": "qwq-32b",
        "qwen-plus": "qwq-32b",
        "qwen-max": "qwq-32b",
        "qwen2.5": "qwq-32b",
        # Gemini
        "gemini-1.5-flash": "gemini-2.0-flash-thinking",
        # 通用
    }
    for key, value in mappings.items():
        if key in model_lower:
            return value
    return ""


# ═══════════════════════════════════════════
# 独立运行入口
# ═══════════════════════════════════════════

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QFont("PingFang SC", 10)
    app.setFont(font)

    win = ChatWindow()
    win.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()


