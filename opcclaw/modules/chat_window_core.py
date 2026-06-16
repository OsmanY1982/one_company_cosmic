"""
OPCclaw - ChatWindow 主类 (拆分自 chat_window.py)
"""

import os, sys, json
from datetime import datetime
from typing import Optional, Union

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QFrame, QScrollArea, QApplication, QFileDialog,
    QComboBox, QMessageBox, QStackedWidget, QCheckBox, QGroupBox, QDialog,
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QEvent,
)
from PyQt5.QtGui import QFont

# ── OPCclaw 核心 ──
from opcclaw.core.llm_backend import (
    BaseLLMBackend, BackendFactory, ProviderConfig,
)
from opcclaw.core.tool_registry import ToolRegistry
from opcclaw.core.chat_engine import ChatEngine
from opcclaw.core.skill_loader import SkillLoader
from opcclaw.core.memory_store import MemoryStore
from opcclaw.core.multi_model import MultiModelRouter
from opcclaw.core.multi_model_chat_engine import MultiModelChatEngine
from opcclaw.core.agent_loop import AgentLoop
from opcclaw.core.rag_context import RAGContextInjector
from opcclaw.tools.builtin.system_tools import register_system_tools
from opcclaw.tools.builtin.developer_tools import register_developer_tools
from opcclaw.tools.builtin.git_tools import register_git_tools
from opcclaw.tools.builtin.code_tools import register_code_tools
from opcclaw.core.opcclaw_logging import logger
from opcclaw.tools.business_tools import register_business_tools

# ── 拆分出的模块 ──
from opcclaw.modules._shared import COLORS, _styled_btn, _styled_input
from opcclaw.modules.animations import ButtonAnimationHelper, ButtonHoverFilter, LoadingAnimationHelper
from opcclaw.modules.message_bubble import MessageBubble
from opcclaw.modules.login_dialog import LoginDialog
from opcclaw.modules.config_manager import ConfigManager
from opcclaw.modules.sidebar_panel import Sidebar
from opcclaw.modules.cloud_model_panel import CloudModelPanel
from opcclaw.modules.local_model_panel import LocalModelPanel
from opcclaw.modules.skills_panel import SkillsPanel
from opcclaw.modules.general_settings_panel import GeneralSettingsPanel
from opcclaw.modules.chat_worker import ChatWorker

try:
    from opcclaw.modules.voice_manager import VoiceManager, check_voice_dependencies
except ImportError:
    VoiceManager = None
    check_voice_dependencies = lambda: {}


# ═══════════════════════════════════════════
# 多模型辅助函数
# ═══════════════════════════════════════════

def _guess_deep_model(current_model: str) -> str:
    """根据当前模型名猜测同供应商的深度模型"""
    model_lower = current_model.lower()
    mappings = {
        "deepseek-chat": "deepseek-reasoner",
        "deepseek-v3": "deepseek-r1",
        "qwen-turbo": "qwen-plus",
        "qwen-plus": "qwen-max",
        "qwen2.5-7b": "qwen2.5-32b",
        "qwen2.5-14b": "qwen2.5-72b",
        "qwen2.5-32b": "qwen2.5-72b",
        "gpt-4o-mini": "gpt-4o",
        "gpt-4o": "o1",
        "gpt-4-turbo": "gpt-4o",
        "claude-3-haiku": "claude-3.5-sonnet",
        "claude-3.5-haiku": "claude-3.5-sonnet",
        "claude-sonnet": "claude-opus",
        "gemini-1.5-flash": "gemini-1.5-pro",
        "gemini-2.0-flash": "gemini-2.0-pro",
        "glm-4-flash": "glm-4-plus",
        "glm-4": "glm-4-plus",
    }
    for key, value in mappings.items():
        if key in model_lower:
            return value
    return ""


def _guess_reasoning_model(current_model: str) -> str:
    """根据当前模型名猜测同供应商的推理模型"""
    model_lower = current_model.lower()
    mappings = {
        "deepseek-chat": "deepseek-reasoner",
        "deepseek-v3": "deepseek-r1",
        "deepseek": "deepseek-reasoner",
        "gpt-4o-mini": "o1-mini",
        "gpt-4o": "o1",
        "gpt-4-turbo": "o1",
        "qwen-turbo": "qwq-32b",
        "qwen-plus": "qwq-32b",
        "qwen-max": "qwq-32b",
        "qwen2.5": "qwq-32b",
        "gemini-1.5-flash": "gemini-2.0-flash-thinking",
    }
    for key, value in mappings.items():
        if key in model_lower:
            return value
    return ""


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
        self._deleting = False  # 删除操作进行中，阻塞 itemClicked 连锁
        self._session_cleared = False  # 当前会话已清屏，禁止切换时写回非空消息
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

        export_btn = QPushButton("导出记录")
        export_btn.setFixedSize(90, 32)
        export_btn.setStyleSheet(f"""
            QPushButton {{
                color: #FFFFFF;
                background: rgba(160, 120, 220, 0.6);
                border: 1px solid rgba(160, 120, 220, 0.8);
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: rgba(160, 120, 220, 0.85); }}
        """)
        export_btn.clicked.connect(self._export_current_session)
        header_layout.addWidget(export_btn)

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
        self.sidebar.session_selected.connect(self._on_session_selected)
        self.sidebar.new_chat_requested.connect(self._on_new_session)
        self.sidebar.session_delete_requested.connect(self._on_session_delete)
        self.sidebar.session_copy_requested.connect(self._on_session_copy)
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
        # MarkItDown: document-to-Markdown converter (P0)
        try:
            import opcclaw.tools.markitdown_tool  # noqa: F811 — side-effect registration
        except Exception:
            pass
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
        # 清屏后首次发消息：清除标记，后续会话保存恢复正常
        self._session_cleared = False
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
        """刷新会话列表（下拉框+侧边栏）"""
        sessions = self.memory_store.list_sessions()
        print(f"[CHAT_CORE] _refresh_sessions: {len(sessions)} sessions, current={self._session_id}")
        # 侧边栏列表
        self.sidebar.set_sessions(sessions, self._session_id)
        # 下拉框
        if self._session_combo:
            self._session_combo.blockSignals(True)
            self._session_combo.clear()
            for s in sessions:
                label = s["id"]
                updated = s.get("updated_at", "")[:16].replace("T", " ")
                if updated:
                    label = f"{updated} | {s['id']}"
                self._session_combo.addItem(label, s["id"])
                if s["id"] == self._session_id:
                    self._session_combo.setCurrentIndex(self._session_combo.count() - 1)
            self._session_combo.blockSignals(False)

    def _on_new_session(self):
        """创建新会话"""
        # 先保存当前会话（清屏或删除操作中跳过）
        if self.engine and not self._session_cleared and not self._deleting:
            self.memory_store.save_session(self.engine.get_history(), self._session_id)
        self._session_cleared = False
        # 切换到新会话
        self._session_id = self._gen_session_id()
        self._save_last_session(self._session_id)
        # 清除界面并重建引擎
        self._clear_chat_messages()
        if self.engine:
            self.engine.session_id = self._session_id
            self.engine.reset()
        # 显式落盘空会话，不依赖 engine.reset() 的 auto_save 副作用
        self.memory_store.save_session([], self._session_id)
        self._refresh_sessions()

    def _on_session_switch(self, idx: int):
        """切换到选中的会话（QComboBox 回调）"""
        if not self._session_combo or idx < 0:
            return
        new_id = self._session_combo.itemData(idx)
        if not new_id or new_id == self._session_id:
            return
        self._switch_to_session(new_id)

    def _on_session_selected(self, session_id: str):
        """侧边栏选中会话回调"""
        if self._deleting:
            return
        if not session_id or session_id == self._session_id:
            return
        # 防止切换到已被并发删除的会话（itemClicked 在 del 按钮点击时也会触发）
        existing = self.memory_store.list_sessions()
        existing_ids = {s["id"] for s in existing}
        if session_id not in existing_ids:
            return
        self._switch_to_session(session_id)

    def _on_session_delete(self, session_id: str):
        """侧边栏删除会话回调"""
        # 必须在弹窗之前设标记——QDialog.exec() 的嵌套事件循环会处理 itemClicked 信号
        self._deleting = True
        try:
            # 自定义暗色确认弹窗（QMessageBox 在 macOS 暗色主题下显示为黑片）
            dlg = QDialog(self)
            dlg.setWindowTitle("删除确认")
            dlg.setFixedSize(400, 160)
            dlg.setAttribute(Qt.WA_StyledBackground, True)
            dlg.setModal(True)
            dlg.setStyleSheet("""
                QDialog { background: #1e1e3a; border: 1px solid #3a3a5c; border-radius: 8px; }
                QLabel { color: #ccccdd; font-size: 14px; }
                QPushButton { padding: 6px 20px; border-radius: 4px; font-size: 13px; }
                QPushButton#confirm_btn { background: #c0392b; color: white; }
                QPushButton#confirm_btn:hover { background: #e74c3c; }
                QPushButton#cancel_btn { background: #3a3a5c; color: #ccccdd; }
                QPushButton#cancel_btn:hover { background: #4a4a6c; }
            """)

            layout = QVBoxLayout(dlg)
            label = QLabel(f"确定要删除会话吗？\n{session_id}\n此操作不可撤销。")
            label.setWordWrap(True)
            layout.addWidget(label)

            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            cancel_btn = QPushButton("取消")
            cancel_btn.setObjectName("cancel_btn")
            cancel_btn.clicked.connect(dlg.reject)
            confirm_btn = QPushButton("确认删除")
            confirm_btn.setObjectName("confirm_btn")
            confirm_btn.clicked.connect(dlg.accept)
            btn_layout.addWidget(cancel_btn)
            btn_layout.addWidget(confirm_btn)
            layout.addLayout(btn_layout)

            if dlg.exec_() != QDialog.Accepted:
                return

            self.memory_store.delete_session(session_id)
            # 如果删除的是当前会话，切换到第一个可用会话或新建
            if session_id == self._session_id:
                sessions = self.memory_store.list_sessions()
                if sessions:
                    next_id = sessions[0]["id"]
                    self._switch_to_session(next_id)
                else:
                    self._on_new_session()
            self._refresh_sessions()
        finally:
            self._deleting = False

    def _on_session_copy(self, session_id: str):
        """复制会话：读源会话消息 → 写入新 ID → 刷新列表"""
        messages = self.memory_store.load_session(session_id)
        new_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.memory_store.save_session(messages, new_id)
        self._refresh_sessions()

    def _export_current_session(self):
        """导出当前会话为 Markdown 文件到桌面"""
        import os as _os
        desktop = _os.path.join(_os.path.expanduser("~"), "Desktop")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"OPCclaw_对话记录_{ts}.md"
        filepath = _os.path.join(desktop, filename)

        messages = self.memory_store.load_session(self._session_id)
        lines = [f"# OPCclaw 对话记录\n", f"会话 ID: {self._session_id}\n",
                 f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
                 f"消息数: {len(messages)}\n", "---\n"]
        for m in messages:
            role = m.get("role", "unknown")
            content = m.get("content", "")
            if role == "system":
                continue
            if role == "user":
                lines.append(f"## 用户\n\n{content}\n\n")
            elif role == "assistant":
                lines.append(f"## AI\n\n{content}\n\n")
            elif role == "tool":
                lines.append(f"## 工具\n\n```\n{content[:500]}\n```\n\n")

        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(lines)

        QMessageBox.information(self, "导出成功",
            f"已导出到:\n{filepath}")

    def _switch_to_session(self, new_id: str):
        """切换会话核心逻辑"""
        # 保存当前会话（清屏或删除操作中跳过，避免写回无效数据）
        if self.engine and not self._session_cleared and not self._deleting:
            self.memory_store.save_session(self.engine.get_history(), self._session_id)
        self._session_cleared = False
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
                # engine.reset() 已保存空消息，但 initialize_session() 会给 self.messages 加系统消息。
                # 标记此会话已清屏，_switch_to_session 在切换前不再重新保存非空内容。
                self._session_cleared = True
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
        """关闭窗口时清理资源并保存会话"""
        # 1. 停止语音管理器（资源清理）
        if self._voice_manager:
            try:
                self._voice_manager.stop_speaking()
                self._voice_manager.stop_listening()
            except Exception:
                pass
        # 2. 保存当前会话（已清屏的跳过）
        if self.engine and self.memory_store and not self._session_cleared:
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


