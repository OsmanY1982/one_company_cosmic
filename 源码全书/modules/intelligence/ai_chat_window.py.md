# `modules/intelligence/ai_chat_window.py`

> 路径：`modules/intelligence/ai_chat_window.py` | 行数：1417


---


```python
"""
AI助手 · NEURAL v5 — 统一 AgentBridge 对话窗口
全部模型调用通过 AgentBridge（opcclaw 引擎），废弃独立 llm_config.json
顶部嵌入紧凑模型选择器：供应商下拉 → 模型下拉 → 切换按钮
模型切换通过 AgentBridge.switch_model() 同步更新后端
降级路径：AgentBridge.chat_stream → AgentBridge.chat → 离线分析
"""
import traceback
import os
import subprocess
import threading
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QTextBrowser, QLineEdit,
    QPushButton, QLabel, QComboBox, QApplication, QSplitter, QFileDialog,
    QMenu, QAction,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

from modules.intelligence.ai_chat_styles import (
    INPUT_STYLE, BTN_PRIMARY, BTN_DANGER, BTN_SETTINGS,
)
from modules.intelligence.chat_session_manager import ChatSessionManager
from modules.intelligence.offline_analyzer import gather_context, offline_analysis
from modules.intelligence.session_context import session_ctx
from modules.intelligence.voice_interface import VoiceInterface
from modules.auth.model_config_panel import (
    PRESET_PROVIDERS, LOCAL_SERVICES, PROVIDER_MODELS, ModelConfigDialog,
)

# ── 紧凑工具栏样式 ──
PROVIDER_COMBO_STYLE = """
    QComboBox {
        background: rgba(20,12,40,200); color: #ccbbee;
        border: 1px solid rgba(120,200,80,35); border-radius: 6px;
        padding: 3px 8px; font-size: 11px;
    }
    QComboBox:hover { border: 1px solid rgba(140,220,100,120); }
    QComboBox::drop-down { border: none; width: 20px; }
    QComboBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #99bb88; margin-right: 6px; }
    QComboBox QAbstractItemView {
        background: rgba(15,8,30,240); color: #ccbbdd;
        border: 1px solid rgba(120,200,80,40); selection-background-color: rgba(100,180,60,50);
    }
"""

BTN_SWITCH = """
    QPushButton {
        background: rgba(0,180,100,50); color: #88ffcc;
        border: 1px solid rgba(0,220,120,80); border-radius: 6px;
        padding: 3px 12px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(0,210,120,80); color: #aaffdd; }
    QPushButton:disabled { background: rgba(0,100,60,25); color: #558866; border-color: rgba(0,120,60,30); }
"""

BTN_GEAR = """
    QPushButton {
        background: rgba(100,140,200,35); color: #99bbee; border: none;
        border-radius: 12px; font-size: 13px;
    }
    QPushButton:hover { background: rgba(120,160,220,60); }
"""

BTN_STOP = """
    QPushButton {
        background: #aa2222;
        color: #ffffff;
        border: 2px solid #ff4444;
        border-radius: 16px;
        padding: 6px 18px;
        font-size: 11px;
        font-weight: 700;
    }
    QPushButton:hover { background: #cc3333; }
"""

BTN_UPLOAD = """
    QPushButton {
        background: rgba(120,100,180,40);
        color: #bbaaee;
        border: 1px solid rgba(140,110,200,60);
        border-radius: 15px;
        padding: 0 12px;
        font-size: 12px;
        font-weight: 600;
    }
    QPushButton:hover { background: rgba(140,120,200,65); }
"""

FILE_PILL_STYLE = """
    QPushButton {
        background: rgba(255,170,80,40);
        color: #ffbb66;
        border: 1px solid rgba(255,170,80,70);
        border-radius: 10px;
        padding: 2px 8px;
        font-size: 10px;
    }
    QPushButton:hover { background: rgba(255,100,60,70); color: #ffffff; }
"""


class AIChatWindow(QWidget):
    """AI助手 · NEURAL v5 — 统一 AgentBridge，顶部嵌入紧凑模型选择器"""

    chat_close_requested = pyqtSignal()

    def __init__(self, parent=None, opcclaw_engine=None, floating_mode=False, voice=None, embedded=False, session_id=None):
        super().__init__(parent)
        self._embedded = embedded

        if not embedded:
            self.setWindowFlags(
                Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint
            )
            self.setAttribute(Qt.WA_DeleteOnClose)
            self.setWindowTitle("AI助手 · NEURAL v5")
            self.setMinimumSize(600, 400)
            self.resize(780, 580)

        self.setStyleSheet("background: rgba(10,5,20,240);")

        self._bridge = opcclaw_engine  # AgentBridge 实例（唯一引擎）
        self._streaming = False
        self._stream_buffer = ""

        # ── 对话会话管理 ──
        # 使用全局会话ID或传入的ID
        if session_id is None:
            session_id = session_ctx.current_session_id
        self._current_session_id = session_id
        self._current_title = session_ctx.current_title

        # 注册到全局上下文
        session_ctx.register_window(self)
        if self._bridge:
            session_ctx.set_agent_bridge(self._bridge)
        self._messages = []       # [{role, content}, ...] 当前会话消息缓存
        self._msg_copy_map = {}  # {msg_id: text} 消息按钮复制用
        self._next_msg_id = 0    # 递增消息ID

        # 监听外部消息（语音等入口）实时同步到当前窗口
        session_ctx.add_message_listener(self._on_external_message)

        # 语音输入
        self._voice_input = None   # 语音输入实例（点击录音时懒加载）
        self._voice_recording = False

        # 朗读
        self._speak_process = None  # 后台 say 朗读进程

        # 文件上传
        self._attached_files = []       # [(filepath, basename), ...]
        self._file_pills = []           # 附件标签按钮引用

        # 流式控制
        self._stop_requested = False    # 用户请求停止生成
        self._suppress_self_notify = False  # 阻止自通知导致的重复显示

        self._all_models = []  # 全量模型列表（云端+本地）
        self._current_model = ""
        self._current_provider_id = ""
        if self._bridge and hasattr(self._bridge, "get_model"):
            self._current_model = self._bridge.get_model()

        self._build_ui()
        self._populate_provider_combo()
        self._refresh_model_list()

        # DEBUG: verify input row widgets
        print(f"[AIChatWindow DEBUG] btn_upload: visible={self.btn_upload.isVisible()} size={self.btn_upload.size()} geo={self.btn_upload.geometry()}")
        print(f"[AIChatWindow DEBUG] btn_mic: visible={self.btn_mic.isVisible()} size={self.btn_mic.size()} geo={self.btn_mic.geometry()}")
        print(f"[AIChatWindow DEBUG] btn_send: visible={self.btn_send.isVisible()} size={self.btn_send.size()} geo={self.btn_send.geometry()}")
        print(f"[AIChatWindow DEBUG] btn_stop: visible={self.btn_stop.isVisible()} size={self.btn_stop.size()} geo={self.btn_stop.geometry()}")
        print(f"[AIChatWindow DEBUG] ai_input: visible={self.ai_input.isVisible()} size={self.ai_input.size()} geo={self.ai_input.geometry()}")
        print(f"[AIChatWindow DEBUG] btn_speak: visible={self.btn_speak.isVisible()} enabled={self.btn_speak.isEnabled()} size={self.btn_speak.size()} geo={self.btn_speak.geometry()}")

        # standalone 模式：窗口居中显示
        if not embedded:
            screen = QApplication.primaryScreen()
            if screen:
                geom = screen.availableGeometry()
                self.move((geom.width() - self.width()) // 2,
                           (geom.height() - self.height()) // 2)

        # ── 加载会话历史（确保悬浮球与智能中心共享同一会话消息）──
        if self._bridge and self._current_session_id:
            try:
                msgs = self._bridge.load_session(self._current_session_id)
                if msgs:
                    self._messages = msgs
                    for msg in msgs:
                        role = msg.get("role", "")
                        content = msg.get("content", "")
                        if role == "user":
                            self._append_user_msg(content)
                        elif role == "assistant":
                            self._append_ai_msg(content)
                    print(f"[AIChatWindow] 从引擎恢复 {len(msgs)} 条消息 (session={self._current_session_id})")
            except Exception as e:
                print(f"[AIChatWindow] 加载会话历史失败: {e}")

    # ─── UI ───
    def _build_ui(self):
        l = QVBoxLayout(self)
        l.setSpacing(10)
        l.setContentsMargins(16, 12, 16, 12)

        # ── 顶部工具栏：状态 | 供应商 | 模型 | 切换 | 刷新 | 设置 ──
        top_row = QHBoxLayout()
        top_row.setSpacing(5)

        if self._bridge is not None:
            prov = self._bridge.get_provider_info() if hasattr(self._bridge, "get_provider_info") else {}
            status_text = f"AgentBridge: {prov.get('name', 'OPCclaw')} / {prov.get('model', self._current_model)}"
            status_color = "#44cc88"
        else:
            status_text = "引擎未连接 — 离线分析模式"
            status_color = "#ff6644"

        self.lbl_status = QLabel(status_text)
        self.lbl_status.setStyleSheet(
            f"color: {status_color}; font-size: 11px; background: transparent;"
        )
        top_row.addWidget(self.lbl_status)

        # 侧边栏折叠按钮
        self._sidebar_visible = True
        self.btn_toggle_sidebar = QPushButton("◀")
        self.btn_toggle_sidebar.setToolTip("隐藏左侧会话列表")
        self.btn_toggle_sidebar.setFixedSize(24, 20)
        self.btn_toggle_sidebar.setStyleSheet("""
            QPushButton {
                background: rgba(170,80,255,30); color: #bb99dd; border: none;
                border-radius: 4px; font-size: 12px;
            }
            QPushButton:hover { background: rgba(170,80,255,60); color: #ddccff; }
        """)
        self.btn_toggle_sidebar.clicked.connect(self._toggle_sidebar)
        top_row.addWidget(self.btn_toggle_sidebar)

        # 新建对话按钮（工具栏常驻，侧边栏折叠时也能用）
        self.btn_new_chat = QPushButton("+")
        self.btn_new_chat.setToolTip("新建对话")
        self.btn_new_chat.setFixedSize(24, 20)
        self.btn_new_chat.setStyleSheet("""
            QPushButton {
                background: rgba(100,200,100,30); color: #88cc88; border: none;
                border-radius: 4px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(100,200,100,60); color: #aaffaa; }
        """)
        self.btn_new_chat.clicked.connect(self._on_new_session)
        top_row.addWidget(self.btn_new_chat)

        top_row.addStretch()

        # 供应商下拉（绿色边框，与模型紫色区分）
        prov_lbl = QLabel("供应商:")
        prov_lbl.setStyleSheet("color: #88aa88; font-size: 11px; background: transparent;")
        top_row.addWidget(prov_lbl)

        self.cb_provider = QComboBox()
        self.cb_provider.setMinimumWidth(130)
        self.cb_provider.setStyleSheet(PROVIDER_COMBO_STYLE)
        self.cb_provider.currentIndexChanged.connect(self._on_provider_changed)
        top_row.addWidget(self.cb_provider)

        # 模型下拉
        model_lbl = QLabel("模型:")
        model_lbl.setStyleSheet("color: #9988aa; font-size: 11px; background: transparent;")
        top_row.addWidget(model_lbl)

        self.cb_model = QComboBox()
        self.cb_model.setMinimumWidth(150)
        self.cb_model.setStyleSheet("""
            QComboBox {
                background: rgba(20,12,40,200); color: #ddccff;
                border: 1px solid rgba(170,80,255,35); border-radius: 6px;
                padding: 3px 8px; font-size: 11px;
            }
            QComboBox:hover { border: 1px solid rgba(180,100,255,120); }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #9988bb; margin-right: 6px; }
            QComboBox QAbstractItemView {
                background: rgba(15,8,30,240); color: #ccbbdd;
                border: 1px solid rgba(170,80,255,40); selection-background-color: rgba(150,60,220,50);
            }
        """)
        # 🔴 不连接 currentIndexChanged 自动切换 → 改为手动切换按钮触发
        top_row.addWidget(self.cb_model)

        # 切换按钮
        self.btn_switch = QPushButton("切换")
        self.btn_switch.setToolTip("切换到选中的供应商和模型")
        self.btn_switch.setStyleSheet(BTN_SWITCH)
        self.btn_switch.clicked.connect(self._on_switch_clicked)
        top_row.addWidget(self.btn_switch)

        # 刷新模型按钮
        self.btn_refresh = QPushButton("⟳")
        self.btn_refresh.setToolTip("刷新模型列表")
        self.btn_refresh.setFixedSize(28, 24)
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background: rgba(100,140,200,35); color: #99bbee; border: none;
                border-radius: 12px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(120,160,220,60); }
        """)
        self.btn_refresh.clicked.connect(self._refresh_model_list)
        top_row.addWidget(self.btn_refresh)

        # 设置按钮（打开完整 ModelConfigDialog）
        settings_btn = QPushButton("⚙")
        settings_btn.setToolTip("打开完整模型配置（设置 API Key 等）")
        settings_btn.setFixedSize(28, 24)
        settings_btn.setStyleSheet(BTN_GEAR)
        settings_btn.clicked.connect(self._open_model_settings)
        top_row.addWidget(settings_btn)

        # embedded 模式：最右侧"关闭对话"按钮
        if self._embedded:
            close_btn = QPushButton("关闭对话")
            close_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(220,60,60,50); color: #ff8888;
                    border: 1px solid rgba(255,80,80,80); border-radius: 6px;
                    padding: 3px 12px; font-size: 11px; font-weight: 600;
                }
                QPushButton:hover { background: rgba(255,70,70,80); color: #ffaaaa; }
            """)
            close_btn.clicked.connect(self.chat_close_requested.emit)
            top_row.addWidget(close_btn)

        l.addLayout(top_row)

        # ── 左右分栏：左侧会话列表 + 右侧对话区 ──
        self._session_manager = ChatSessionManager(self._bridge)
        self._session_manager.session_selected.connect(self._on_session_selected)
        self._session_manager.new_chat_requested.connect(self._on_new_session)
        self._session_manager.session_deleted.connect(self._on_session_deleted)

        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.addWidget(self._session_manager)

        # 右侧对话面板
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        self.ai_chat = QTextBrowser()
        self.ai_chat.setReadOnly(True)
        self.ai_chat.setOpenLinks(False)
        self.ai_chat.anchorClicked.connect(self._on_anchor_clicked)
        self.ai_chat.setAcceptDrops(True)
        self.ai_chat.dragEnterEvent = self._drag_enter_event
        self.ai_chat.dropEvent = self._drop_event
        self.ai_chat.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ai_chat.customContextMenuRequested.connect(self._on_chat_context_menu)
        self.ai_chat.setStyleSheet("""
            QTextBrowser {
                background: rgba(8,4,16,230); color: #bb99dd;
                border: 1px solid rgba(170,80,255,35); border-radius: 10px;
                padding: 12px; font-size: 12px; line-height: 1.6;
            }
        """)
        right_layout.addWidget(self.ai_chat, 1)

        # 附件标签行（拖拽/上传文件后显示）
        self._pills_container = QWidget()
        self._pills_layout = QHBoxLayout(self._pills_container)
        self._pills_layout.setContentsMargins(0, 0, 0, 0)
        self._pills_layout.setSpacing(4)
        self._pills_layout.addStretch()
        self._pills_container.setVisible(False)
        right_layout.addWidget(self._pills_container)

        # 输入行
        ir = QHBoxLayout()

        self.btn_upload = QPushButton("文件")
        self.btn_upload.setToolTip("上传文件或图片（支持拖拽到对话区）")
        self.btn_upload.setFixedSize(50, 30)
        self.btn_upload.setStyleSheet(BTN_UPLOAD)
        self.btn_upload.clicked.connect(self._on_upload_clicked)
        ir.addWidget(self.btn_upload)

        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("输入问题，或拖拽文件到对话区...")
        self.ai_input.setStyleSheet(INPUT_STYLE)
        self.ai_input.returnPressed.connect(self._ai_send)
        ir.addWidget(self.ai_input, 1)

        self.btn_mic = QPushButton("语音")
        self.btn_mic.setToolTip("点击开始语音输入（Apple 语音识别，6秒超时自动发送）")
        self.btn_mic.setFixedSize(60, 30)
        self.btn_mic.setStyleSheet("""
            QPushButton {
                background: #2d8a4e;
                color: #ffffff;
                border: 2px solid #44cc66;
                border-radius: 15px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover { background: #3aa85e; }
            QPushButton:pressed { background: #1e6b3a; }
        """)
        self.btn_mic.clicked.connect(self._toggle_voice_input)
        ir.addWidget(self.btn_mic)

        self.btn_send = QPushButton("发送")
        self.btn_send.setStyleSheet(BTN_PRIMARY)
        self.btn_send.clicked.connect(self._ai_send)
        ir.addWidget(self.btn_send)

        self.btn_stop = QPushButton("停止")
        self.btn_stop.setStyleSheet(BTN_STOP)
        self.btn_stop.clicked.connect(self._on_stop_generation)
        self.btn_stop.setVisible(False)
        ir.addWidget(self.btn_stop)

        self.btn_speak = QPushButton("朗读")
        self.btn_speak.setToolTip("朗读最后一条 AI 回复")
        self.btn_speak.setStyleSheet("""
            QPushButton {
                background: rgba(80,200,160,40);
                color: #88ffcc;
                border: 1px solid rgba(80,220,160,60);
                border-radius: 16px;
                padding: 6px 14px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover { background: rgba(100,230,180,65); }
        """)
        self.btn_speak.clicked.connect(self._on_speak_clicked)
        ir.addWidget(self.btn_speak)

        clear_btn = QPushButton("清屏")
        clear_btn.setStyleSheet(BTN_DANGER)
        clear_btn.clicked.connect(self._on_clear_chat)
        ir.addWidget(clear_btn)

        self.btn_export = QPushButton("导出")
        self.btn_export.setToolTip("导出当前对话（Markdown / JSON）")
        self.btn_export.setStyleSheet("""
            QPushButton {
                background: rgba(60,160,200,40);
                color: #88ccff;
                border: 1px solid rgba(80,180,220,60);
                border-radius: 16px;
                padding: 6px 14px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover { background: rgba(80,200,240,65); }
        """)
        self.btn_export.clicked.connect(self._on_export_chat)
        ir.addWidget(self.btn_export)

        right_layout.addLayout(ir)

        self._splitter.addWidget(right_widget)
        self._splitter.setStretchFactor(0, 0)  # 左侧不拉伸
        self._splitter.setStretchFactor(1, 1)  # 右侧拉伸

        l.addWidget(self._splitter, 1)

    def _on_clear_chat(self):
        """清屏并清空本地消息缓存"""
        self.ai_chat.clear()
        self._messages = []

    def _on_export_chat(self):
        """导出当前对话为 Markdown 或 JSON"""
        import json
        if not self._messages:
            # 尝试从 bridge 加载
            if self._bridge:
                try:
                    self._messages = self._bridge.load_session(self._current_session_id)
                except Exception:
                    pass
        if not self._messages:
            self.ai_chat.append(
                '<p style="color:#ff6644;font-size:10px;">当前对话为空，无需导出</p>'
            )
            return

        default_name = f"chat_{self._current_session_id}"
        path, selected_filter = QFileDialog.getSaveFileName(
            self, "导出当前对话", default_name,
            "Markdown文件 (*.md);;JSON文件 (*.json)",
        )
        if not path:
            return

        try:
            if path.endswith(".md"):
                lines = [
                    f"# {self._current_title}\n",
                    f"*导出于: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
                    "---\n",
                ]
                for msg in self._messages:
                    role = msg.get("role", "unknown").upper()
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        lines.append(f"\n### {role}\n")
                        lines.append(content)
                        lines.append("")
                with open(path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))
            else:
                data = {
                    "session_id": self._current_session_id,
                    "title": self._current_title,
                    "exported_at": datetime.now().isoformat(),
                    "messages": self._messages,
                }
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            self._session_manager._show_export_result_dialog(True, path)
        except Exception as e:
            self._session_manager._show_export_result_dialog(False, str(e))

    def _on_speak_clicked(self):
        """朗读最后一条 AI 回复（macOS say 命令，中文语音 Tingting）"""
        print("[Speak] _on_speak_clicked called", flush=True)
        try:
            self._do_speak()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[Speak] 按钮回调异常: {e}", flush=True)
            try:
                self.ai_chat.append(
                    f'<p style="color:#ff6644;font-size:10px;">[系统] 朗读失败: {e}</p>'
                )
            except Exception:
                import traceback; traceback.print_exc()

    def _do_speak(self):
        """执行朗读逻辑"""
        # 找到最后一条 assistant 消息
        last_ai = None
        for msg in reversed(self._messages):
            if msg.get("role") == "assistant":
                last_ai = msg["content"]
                break
        if not last_ai:
            self.ai_chat.append(
                '<p style="color:#ffaa44;font-size:10px;">[系统] 没有可朗读的 AI 回复</p>'
            )
            return

        # 终止之前的朗读进程
        self._terminate_speak()

        # 清理文本：去除 HTML 标签
        import re
        clean_text = re.sub(r'<[^>]+>', '', last_ai).strip()

        # 即时反馈：正在朗读（强制刷新 UI）
        self._set_speak_button("朗读中...", """
            QPushButton {
                background: rgba(255,180,60,60); color: #ffaa44;
                border: 1px solid rgba(255,180,60,100); border-radius: 16px;
                padding: 6px 14px; font-size: 11px; font-weight: 600;
            }
        """)

        from PyQt5.QtCore import QTimer
        def _run():
            try:
                proc = subprocess.Popen(
                    ['say', '-v', 'Tingting'],
                    stdin=subprocess.PIPE,
                )
                self._speak_process = proc
                proc.communicate(input=clean_text.encode('utf-8'))
            except Exception as e:
                print(f"[Speak] 朗读失败: {e}")
            # 在主线程恢复按钮
            QTimer.singleShot(0, self._restore_speak_button)

        threading.Thread(target=_run, daemon=True).start()

    def _set_speak_button(self, text, style):
        """安全设置朗读按钮文字（先刷事件队列确保立即可见）"""
        self.btn_speak.setText(text)
        self.btn_speak.setStyleSheet(style)
        QApplication.processEvents()

    def _restore_speak_button(self):
        """朗读完成后在主线程恢复按钮"""
        self.btn_speak.setText("朗读")
        self.btn_speak.setStyleSheet("""
            QPushButton {
                background: rgba(80,200,160,40); color: #88ffcc;
                border: 1px solid rgba(80,220,160,60); border-radius: 16px;
                padding: 6px 14px; font-size: 11px; font-weight: 600;
            }
            QPushButton:hover { background: rgba(100,230,180,65); }
        """)

    def _terminate_speak(self):
        """终止后台朗读进程"""
        if self._speak_process and self._speak_process.poll() is None:
            try:
                self._speak_process.terminate()
                self._speak_process.wait(timeout=2)
            except Exception:
                try:
                    self._speak_process.kill()
                except Exception:
                    pass
        self._speak_process = None

    def closeEvent(self, event):
        """窗口关闭时保存当前会话"""
        # 终止朗读进程
        self._terminate_speak()
        if self._messages and self._bridge:
            try:
                self._bridge.save_session(self._messages, self._current_session_id)
            except Exception as e:
                print(f"[AIChatWindow] closeEvent 保存失败: {e}")
        # 刷新会话列表
        if hasattr(self, '_session_manager'):
            try:
                self._session_manager._load_sessions()
            except Exception:
                import traceback; traceback.print_exc()
        # 注销全局上下文
        session_ctx.unregister_window(self)
        session_ctx.remove_message_listener(self._on_external_message)
        # 清理语音输入
        if self._voice_input:
            try:
                self._voice_input.stop_listening()
            except Exception:
                import traceback; traceback.print_exc()
        super().closeEvent(event)

    # ─── 语音输入 ───
    def _toggle_voice_input(self):
        """切换语音输入状态"""
        if self._voice_recording:
            self._stop_voice_input()
        else:
            self._start_voice_input()

    def _start_voice_input(self):
        """开始语音输入"""
        if self._voice_recording:
            return

        if self._voice_input is None:
            self._voice_input = VoiceInterface(stt_engine="apple")
            self._voice_input.recognition_result.connect(self._on_voice_input_result)
            self._voice_input.recognition_status.connect(self._on_voice_input_status)
            self._voice_input.error_occurred.connect(self._on_voice_input_error)

        self._voice_recording = True
        self.btn_mic.setText("⏹")
        self.btn_mic.setToolTip("录音中…点击停止")
        self.btn_mic.setStyleSheet("""
            QPushButton {
                background: rgba(220,60,50,60);
                color: #ff6666;
                border: 1px solid rgba(255,80,70,120);
                border-radius: 18px;
                font-size: 14px;
            }
            QPushButton:hover { background: rgba(240,70,60,80); }
        """)

        self.ai_chat.append(
            '<p style="color:#ffaa44;font-size:10px;">🎤 语音输入中…请说话（最长6秒）</p>'
        )

        try:
            self._voice_input.start_listening(timeout=6.0)
        except Exception as e:
            self._on_voice_input_error(f"启动语音输入失败: {e}")

    def _stop_voice_input(self):
        """停止语音输入"""
        self._voice_recording = False
        self.btn_mic.setText("🎤")
        self.btn_mic.setToolTip("点击开始语音输入（6秒超时自动发送）")
        self.btn_mic.setStyleSheet("""
            QPushButton {
                background: rgba(100,140,200,45);
                color: #99bbee;
                border: 1px solid rgba(100,140,200,70);
                border-radius: 18px;
                font-size: 14px;
            }
            QPushButton:hover { background: rgba(130,170,230,70); }
        """)
        if self._voice_input:
            try:
                self._voice_input.stop_listening()
            except Exception:
                import traceback; traceback.print_exc()

    def _on_voice_input_result(self, text: str):
        """语音识别结果 → 填入输入框并自动发送"""
        text = text.strip()
        if not text:
            return
        self._stop_voice_input()
        self.ai_chat.append(
            f'<p style="color:#88aa88;font-size:10px;">🎤 识别: {text}</p>'
        )
        self.ai_input.setText(text)
        self._ai_send()

    def _on_voice_input_status(self, status: str):
        """语音输入状态回调"""
        pass

    def _on_voice_input_error(self, error: str):
        """语音输入错误回调"""
        self._stop_voice_input()
        self.ai_chat.append(
            f'<p style="color:#ff6644;font-size:10px;">语音输入错误: {error}</p>'
        )

    # ─── 会话切换 ───
    def _on_session_selected(self, session_id: str, title: str):
        """切换会话"""
        self._switch_to_session(session_id, title)

    def _on_new_session(self):
        """新建空白会话"""
        new_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._switch_to_session(new_id, "新对话")
        # 立即保存空会话以使其出现在列表中，并刷新侧边栏
        if self._bridge:
            try:
                self._bridge.save_session([], new_id)
            except Exception:
                import traceback; traceback.print_exc()
        self._session_manager._load_sessions()

    def _on_session_deleted(self, session_id: str):
        """外部删除会话后：若为当前会话则切换到剩余的第一个，无剩余才新建"""
        if self._current_session_id != session_id:
            return
        sessions = self._session_manager._sessions
        if sessions:
            s = sessions[0]
            self._switch_to_session(s.get("session_id", ""), s.get("title", "对话"))
        else:
            self._on_new_session()

    def _switch_to_session(self, session_id: str, title: str):
        """切换到指定会话：保存当前 → 清屏 → 加载新会话"""
        # 保存当前会话
        if self._messages and self._bridge:
            try:
                self._bridge.save_session(self._messages, self._current_session_id)
            except Exception as e:
                print(f"[AIChatWindow] 保存会话失败: {e}")

        # 切换
        self._current_session_id = session_id
        self._current_title = title

        # 通知全局上下文
        session_ctx.switch_session(session_id, title)

        self.ai_chat.clear()
        self._messages = []

        # 加载新会话历史
        if self._bridge:
            try:
                msgs = self._bridge.load_session(session_id)
                if msgs:
                    self._messages = msgs
                    for msg in msgs:
                        role = msg.get("role", "")
                        content = msg.get("content", "")
                        if role == "user":
                            self._append_user_msg(content)
                        elif role == "assistant":
                            self._append_ai_msg(content)
            except Exception as e:
                print(f"[AIChatWindow] 加载会话失败: {e}")

        # 更新标题栏
        self.setWindowTitle(f"AI助手 · {title}")

        # 刷新侧边栏（消息数/时间戳等元信息已更新）
        self._session_manager._load_sessions()

    # ─── 模型管理（通过 AgentBridge 统一管理）───
    def _format_size(self, size_bytes: int) -> str:
        if size_bytes >= 1024 ** 3:
            return f"{size_bytes / (1024**3):.1f} GB"
        if size_bytes >= 1024 ** 2:
            return f"{size_bytes / (1024**2):.0f} MB"
        return f"{size_bytes / 1024:.0f} KB"

    # ─── 供应商下拉 ───
    def _populate_provider_combo(self):
        """填充供应商下拉：合并预设云端供应商 + 本地服务 + 已保存的自定义配置"""
        self.cb_provider.blockSignals(True)
        self.cb_provider.clear()

        # 读取已保存配置，获取当前激活的供应商
        from modules.auth.model_config_panel import _load_opcclaw_config
        config = _load_opcclaw_config()
        active_pid = config.get("active_provider_id", "")
        self._current_provider_id = active_pid

        # ── 云端供应商 ──
        self.cb_provider.addItem("── 云端 ──")
        self.cb_provider.model().item(self.cb_provider.count() - 1).setEnabled(False)
        for p in PRESET_PROVIDERS:
            self.cb_provider.addItem(f"☁  {p['name']}", p["id"])

        # 如果有已保存的自定义供应商（不在预设列表中）
        saved_cloud = config.get("cloud_providers", {})
        for pid, pdata in saved_cloud.items():
            if pid not in {p["id"] for p in PRESET_PROVIDERS}:
                self.cb_provider.addItem(f"☁  {pdata.get('name', pid)}", pid)

        # ── 本地服务 ──
        self.cb_provider.addItem("── 本地 ──")
        self.cb_provider.model().item(self.cb_provider.count() - 1).setEnabled(False)
        for s in LOCAL_SERVICES:
            self.cb_provider.addItem(f"🖥  {s['name']}", s["id"])

        # 已保存的本地供应商
        saved_local = config.get("local_providers", {})
        for pid, pdata in saved_local.items():
            if pid not in {s["id"] for s in LOCAL_SERVICES}:
                self.cb_provider.addItem(f"🖥  {pdata.get('name', pid)}", pid)

        # 选中当前激活的供应商
        if active_pid:
            for i in range(self.cb_provider.count()):
                if self.cb_provider.itemData(i) == active_pid:
                    self.cb_provider.setCurrentIndex(i)
                    break

        self.cb_provider.blockSignals(False)
        # 初始触发一次填充模型下拉
        self._on_provider_changed(self.cb_provider.currentIndex())

    def _on_provider_changed(self, idx: int):
        """供应商切换时：更新模型下拉列表，启用切换按钮"""
        if idx < 0:
            return
        pid = self.cb_provider.itemData(idx)
        if not pid:
            return  # 分隔项，忽略

        # 收集可用模型列表
        models = []

        # 1. 查找预设供应商
        preset = next((p for p in PRESET_PROVIDERS if p["id"] == pid), None)
        if preset:
            # 优先使用 PROVIDER_MODELS 硬编码列表（更全、即时可用）
            hardcoded = PROVIDER_MODELS.get(preset["name"], None)
            models = hardcoded if hardcoded else preset.get("models", [])
        else:
            # 2. 查找本地服务
            local = next((s for s in LOCAL_SERVICES if s["id"] == pid), None)
            if local:
                models = local.get("models", [])

        # 3. 从 AgentBridge 补充实时模型（Ollama 动态发现等）
        if self._bridge and hasattr(self._bridge, "list_all_models"):
            try:
                all_models = self._bridge.list_all_models()
                live_models = [m["model"] for m in all_models if m.get("provider_id") == pid]
                for lm in live_models:
                    if lm and lm not in models:
                        models.append(lm)
            except Exception:
                import traceback; traceback.print_exc()

        # 填充模型下拉
        self.cb_model.blockSignals(True)
        self.cb_model.clear()
        if models:
            for m in models:
                self.cb_model.addItem(m, m)
            # 选中当前模型或第一个
            if self._current_model:
                idx_m = self.cb_model.findText(self._current_model)
                if idx_m >= 0:
                    self.cb_model.setCurrentIndex(idx_m)
        else:
            self.cb_model.addItem("（无可用模型列表）", "")
        self.cb_model.blockSignals(False)

        # 启用切换按钮
        self.btn_switch.setEnabled(True)

    # ─── 切换按钮 ───
    def _on_switch_clicked(self):
        """手动点击切换按钮：调用 AgentBridge.switch_model()"""
        model = self.cb_model.currentData()
        if not model:
            self.ai_chat.append(
                '<p style="color:#ffaa44;font-size:10px;">[系统] 请先选择一个有效模型</p>'
            )
            return

        provider_id = self.cb_provider.currentData()
        if not provider_id:
            self.ai_chat.append(
                '<p style="color:#ffaa44;font-size:10px;">[系统] 请先选择一个供应商</p>'
            )
            return

        if not self._bridge or not hasattr(self._bridge, "switch_model"):
            self.ai_chat.append(
                '<p style="color:#ffaa44;font-size:10px;">[系统] AgentBridge 未连接，无法切换模型</p>'
            )
            return

        self.btn_switch.setEnabled(False)
        self.btn_switch.setText("切换中...")

        try:
            success = self._bridge.switch_model(provider_id, model)
            if success:
                self._current_model = model
                self._current_provider_id = provider_id
                prov = self._bridge.get_provider_info() if hasattr(self._bridge, "get_provider_info") else {}
                prov_name = prov.get("name", provider_id)
                self.lbl_status.setText(f"AgentBridge: {prov_name} / {model}")
                self.lbl_status.setStyleSheet("color: #44cc88; font-size: 11px; background: transparent;")
                self.ai_chat.append(
                    f'<p style="color:#44cc88;font-size:10px;">[系统] 已切换模型: {prov_name} / {model}</p>'
                )
                self._refresh_model_list()
            else:
                self.ai_chat.append(
                    f'<p style="color:#ffaa44;font-size:10px;">[系统] 切换失败: 未找到供应商配置（{provider_id}）。请先通过 ⚙ 设置配置 API Key。</p>'
                )
        except Exception as e:
            self.ai_chat.append(
                f'<p style="color:#ffaa44;font-size:10px;">[系统] 切换失败: {e}</p>'
            )
        finally:
            self.btn_switch.setEnabled(True)
            self.btn_switch.setText("切换")

    # ─── 打开完整模型配置 ───
    def _open_model_settings(self):
        """打开 ModelConfigDialog 弹窗进行完整模型配置（含 API Key 设置）"""
        dlg = ModelConfigDialog(self, bridge=self._bridge)
        if self._embedded:
            dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowStaysOnTopHint)
            dlg.setAttribute(Qt.WA_ShowWithoutActivating, False)
        dlg.accepted.connect(self._on_model_settings_closed)
        dlg.show()
        if self._embedded:
            dlg.raise_()
            dlg.activateWindow()

    def _on_model_settings_closed(self):
        if self._bridge and hasattr(self._bridge, "get_model"):
            self._current_model = self._bridge.get_model()
        self._populate_provider_combo()
        self._refresh_model_list()

    # ─── 刷新模型列表 ───
    def _refresh_model_list(self):
        """从 AgentBridge 拉取全量模型列表，同步到供应商+模型下拉框"""
        # 更新当前模型和供应商引用
        if self._bridge and hasattr(self._bridge, "get_model"):
            self._current_model = self._bridge.get_model()
        if self._bridge and hasattr(self._bridge, "get_provider_info"):
            prov = self._bridge.get_provider_info()
            prov_name = prov.get("name", "")
            # 尝试匹配 provider_id
            for i in range(self.cb_provider.count()):
                pid = self.cb_provider.itemData(i)
                if pid:
                    preset = next((p for p in PRESET_PROVIDERS if p["id"] == pid), None)
                    if preset and preset["name"] == prov_name:
                        self._current_provider_id = pid
                        break
                    local = next((s for s in LOCAL_SERVICES if s["id"] == pid), None)
                    if local and local["name"] == prov_name:
                        self._current_provider_id = pid
                        break

        # 重新同步模型下拉
        self._all_models = []
        if self._bridge and hasattr(self._bridge, "list_all_models"):
            try:
                self._all_models = self._bridge.list_all_models()
            except Exception:
                import traceback; traceback.print_exc()

        # 重新触发供应商变化（刷新模型列表）
        current_idx = self.cb_provider.currentIndex()
        if current_idx >= 0:
            self._on_provider_changed(current_idx)

        # 更新状态栏
        if self._bridge and hasattr(self._bridge, "get_provider_info"):
            prov = self._bridge.get_provider_info()
            self.lbl_status.setText(
                f"AgentBridge: {prov.get('name', 'OPCclaw')} / {prov.get('model', self._current_model)}"
            )
            self.lbl_status.setStyleSheet("color: #44cc88; font-size: 11px; background: transparent;")

    # ─── 外部消息监听（语音等入口实时同步到窗口）───
    def _on_external_message(self, session_id: str, role: str, content: str):
        """接收全局上下文中的消息通知，追加到当前会话 UI"""
        if self._suppress_self_notify:
            return  # 本窗口自己发出的消息，已在本地显示过，跳过
        if session_id != self._current_session_id:
            return  # 非当前会话，忽略
        if role == "user":
            self._messages.append({"role": "user", "content": content})
            self._append_user_msg(content)
        elif role == "assistant":
            self._messages.append({"role": "assistant", "content": content})
            self._append_ai_msg(content)

    # ─── 消息按钮 ───
    def _msg_action_row(self, mid: int, text: str) -> str:
        """生成消息操作行 HTML：复制 | 👍 | 👎"""
        self._msg_copy_map[mid] = text
        return (
            f'<p style="font-size:10px;color:#666;margin:2px 0;">'
            f'<a href="cmd:copy:{mid}" style="color:#888;text-decoration:none;">复制</a>'
            f' &nbsp;|&nbsp; '
            f'<a href="cmd:like:{mid}" style="color:#888;text-decoration:none;">👍</a>'
            f' &nbsp;|&nbsp; '
            f'<a href="cmd:dislike:{mid}" style="color:#888;text-decoration:none;">👎</a>'
            f'</p>'
        )

    def _on_anchor_clicked(self, url):
        """消息按钮点击处理：cmd:copy:MID / cmd:like:MID / cmd:dislike:MID"""
        scheme = url.toString()
        if not scheme.startswith("cmd:"):
            return
        _, action, mid_str = scheme.split(":", 2)
        mid = int(mid_str)
        text = self._msg_copy_map.get(mid, "")

        if action == "copy":
            QApplication.clipboard().setText(text)
            self.ai_chat.append(
                f'<p style="color:#44cc88;font-size:10px;">已复制到剪贴板 ✓</p>'
            )
        elif action == "like":
            self.ai_chat.append(
                f'<p style="color:#88ccff;font-size:10px;">已记录：这条回答有帮助 ✓</p>'
            )
        elif action == "dislike":
            self.ai_chat.append(
                f'<p style="color:#ff8866;font-size:10px;">已记录：这条回答不满意 ✗</p>'
            )

    # ─── 交互逻辑 ───
    def _append_user_msg(self, text):
        now = datetime.now().strftime("%H:%M:%S")
        mid = self._next_msg_id
        self._next_msg_id += 1
        self.ai_chat.append(
            f'<p style="color:#ffaa44;font-weight:700;">[{now}] 你:</p>'
            f'<p style="color:#ddccff;">{text}</p>'
            f'{self._msg_action_row(mid, text)}'
        )

    def _append_ai_msg(self, text, offline=False):
        now = datetime.now().strftime("%H:%M:%S")
        tag = "AI(离线)" if offline else "AI"
        mid = self._next_msg_id
        self._next_msg_id += 1
        self.ai_chat.append(
            f'<p style="color:#44ccff;font-weight:700;">[{now}] {tag}:</p>'
            f'<p style="color:#ccaaff;">{text}</p>'
            f'{self._msg_action_row(mid, text)}'
        )

    # ─── 流式输出方法 ───
    def _stream_begin(self):
        self._streaming = True
        self._stream_buffer = ""
        self._enter_streaming_ui()
        now = datetime.now().strftime("%H:%M:%S")
        # 先添加 AI 标签行，再添加流式占位行
        self.ai_chat.append(
            f'<p style="color:#44ccff;font-weight:700;">[{now}] AI:</p>'
        )
        # 流式内容行：追加后再记录光标位置（此时光标在文档末尾）
        self.ai_chat.append(
            f'<p style="color:#ccaaff;">▌</p>'
        )

    def _stream_chunk(self, chunk: str):
        import sys, datetime
        print(f"[DIAG][{datetime.datetime.now().strftime('%H:%M:%S')}] AIChatWindow._stream_chunk len={len(chunk)}", flush=True)
        self._stream_buffer += chunk
        # 用 QTextCursor 替换最后一个段落（避免 QTextEdit.toHtml() 重排破坏 id）
        cursor = self.ai_chat.textCursor()
        cursor.movePosition(cursor.End)
        cursor.movePosition(cursor.StartOfBlock, cursor.KeepAnchor)
        cursor.removeSelectedText()
        escaped = self._stream_buffer.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        cursor.insertHtml(f'<p style="color:#ccaaff;">{escaped}▌</p>')
        # 滚动到底
        sb = self.ai_chat.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _stream_tool(self, tool_name: str, status: str):
        color = {"running": "#99bbee", "OK": "#44cc88", "Failed": "#ff6644"}.get(status, "#888")
        icon = {"running": "⚙", "OK": "✓", "Failed": "✗"}.get(status, "?")
        self.ai_chat.append(
            f'<p style="color:{color};font-size:10px;margin:0;">{icon} 工具: {tool_name} [{status}]</p>'
        )

    def _stream_done(self, full_text: str):
        import sys, datetime
        print(f"[DIAG][{datetime.datetime.now().strftime('%H:%M:%S')}] AIChatWindow._stream_done len={len(full_text)}", flush=True)
        self._streaming = False
        self._exit_streaming_ui()
        # 用 QTextCursor 替换最后一个段落，移除闪烁光标
        cursor = self.ai_chat.textCursor()
        cursor.movePosition(cursor.End)
        cursor.movePosition(cursor.StartOfBlock, cursor.KeepAnchor)
        cursor.removeSelectedText()
        escaped = full_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        mid = self._next_msg_id
        self._next_msg_id += 1
        cursor.insertHtml(f'<p style="color:#ccaaff;">{escaped}</p>{self._msg_action_row(mid, full_text)}')
        self._stream_buffer = ""
        # 消息跟踪 + 增量保存
        self._messages.append({"role": "assistant", "content": full_text})
        if self._bridge:
            try:
                self._bridge.append_message("assistant", full_text, self._current_session_id)
                self._suppress_self_notify = True
                self._bridge.notify_message_added()
                self._suppress_self_notify = False
            except Exception:
                import traceback; traceback.print_exc()

    def _stream_error(self, err_msg: str):
        import sys, datetime
        print(f"[DIAG][{datetime.datetime.now().strftime('%H:%M:%S')}] AIChatWindow._stream_error: {err_msg}", flush=True)
        self._streaming = False
        self._exit_streaming_ui()
        self.ai_chat.append(f'<p style="color:#ff6644;font-size:10px;">{err_msg}</p>')
        self._stream_buffer = ""

    # ─── 核心发送逻辑（仅 AgentBridge）───
    def _ai_send(self):
        text = self.ai_input.text().strip()
        if not text:
            return
        if self._streaming:
            self.ai_chat.append(
                '<p style="color:#ffaa44;font-size:10px;">[系统] 请等待当前回复完成</p>'
            )
            return

        self.ai_input.clear()
        self._append_user_msg(text)
        self._messages.append({"role": "user", "content": text})
        # 实时增量保存
        if self._bridge:
            try:
                self._bridge.append_message("user", text, self._current_session_id)
                self._suppress_self_notify = True
                self._bridge.notify_message_added()
                self._suppress_self_notify = False
            except Exception:
                import traceback; traceback.print_exc()

        # 附带文件内容（如已上传）
        prompt = text
        if self._attached_files:
            file_contexts = []
            for fp, bn in self._attached_files:
                try:
                    with open(fp, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read(4000)  # 截断长文件
                    file_contexts.append(f"[文件: {bn}]\n{content}")
                except Exception:
                    file_contexts.append(f"[文件: {bn}] (二进制/不可读)")
            if file_contexts:
                prompt = text + "\n\n--- 附件内容 ---\n" + "\n\n".join(file_contexts)
            self._clear_file_pills()

        # ── 优先级 1: AgentBridge 流式输出 ──
        if self._bridge is not None and hasattr(self._bridge, "chat_stream"):
            try:
                import sys, datetime
                print(f"[DIAG][{datetime.datetime.now().strftime('%H:%M:%S')}] AIChatWindow._ai_send — calling bridge.chat_stream()...", flush=True)
                self._stream_begin()
                self._bridge.chat_stream(
                    prompt,
                    on_chunk=self._stream_chunk,
                    on_done=self._stream_done,
                    on_tool=self._stream_tool,
                    on_error=self._stream_error,
                )
                print(f"[DIAG][{datetime.datetime.now().strftime('%H:%M:%S')}] AIChatWindow._ai_send — bridge.chat_stream() returned (thread started)", flush=True)
                return
            except Exception as e:
                self.ai_chat.append(
                    f'<p style="color:#ffaa44;font-size:10px;">[系统] 流式启动失败 ({e})，回退同步模式</p>'
                )

        # ── 优先级 2: AgentBridge 同步 chat ──
        if self._bridge is not None:
            try:
                reply = ""
                if hasattr(self._bridge, "chat"):
                    reply = self._bridge.chat(prompt)
                elif hasattr(self._bridge, "query"):
                    reply = self._bridge.query(prompt)
                if reply:
                    self._append_ai_msg(reply)
                    self._messages.append({"role": "assistant", "content": reply})
                    if self._bridge:
                        try:
                            self._bridge.append_message("assistant", reply, self._current_session_id)
                            self._suppress_self_notify = True
                            self._bridge.notify_message_added()
                            self._suppress_self_notify = False
                        except Exception:
                            pass
                    return
            except Exception as e:
                self.ai_chat.append(
                    f'<p style="color:#ffaa44;font-size:10px;">[系统] AgentBridge 调用失败 ({e})，回退离线分析</p>'
                )

        # ── 优先级 3: 离线分析兜底 ──
        try:
            offline_resp = offline_analysis(prompt)
            self._append_ai_msg(offline_resp, offline=True)
            self._messages.append({"role": "assistant", "content": offline_resp})
        except Exception as e:
            self.ai_chat.append(f'<p style="color:#ff6666;">错误: {e}</p>')
            traceback.print_exc()

    # ─── 侧边栏折叠 ───
    def _toggle_sidebar(self):
        """切换左侧会话列表的显隐"""
        self._sidebar_visible = not self._sidebar_visible
        if self._sidebar_visible:
            self._session_manager.show()
            self.btn_toggle_sidebar.setText("◀")
            self.btn_toggle_sidebar.setToolTip("隐藏左侧会话列表")
        else:
            self._session_manager.hide()
            self.btn_toggle_sidebar.setText("▶")
            self.btn_toggle_sidebar.setToolTip("显示左侧会话列表")

    # ─── 停止生成 ───
    def _on_stop_generation(self):
        """用户点击停止按钮"""
        self._stop_requested = True
        if hasattr(self, '_bridge') and self._bridge and hasattr(self._bridge, 'cancel'):
            try:
                self._bridge.cancel()
            except Exception:
                import traceback; traceback.print_exc()

    # ─── 文件上传 ───
    def _on_upload_clicked(self):
        """打开文件选择对话框"""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "",
            "所有文件 (*.*);;图片 (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;文档 (*.pdf *.txt *.md *.py *.json *.csv *.xlsx *.docx)"
        )
        if paths:
            for p in paths:
                self._add_file_pill(p)

    def _add_file_pill(self, filepath):
        """添加附件标签到 pills 行"""
        basename = os.path.basename(filepath)
        # 去重
        if any(fp == filepath for fp, _ in self._attached_files):
            return
        self._attached_files.append((filepath, basename))

        pill = QPushButton(f" {basename} ×")
        pill.setToolTip(filepath)
        pill.setStyleSheet(FILE_PILL_STYLE)
        pill.clicked.connect(lambda checked, fp=filepath: self._remove_file_pill(fp))
        # 插入到 stretch 之前
        self._pills_layout.insertWidget(self._pills_layout.count() - 1, pill)
        self._file_pills.append(pill)
        self._pills_container.setVisible(True)

    def _remove_file_pill(self, filepath):
        """移除指定附件"""
        for i, (fp, _) in enumerate(self._attached_files):
            if fp == filepath:
                self._attached_files.pop(i)
                pill = self._file_pills.pop(i)
                pill.deleteLater()
                break
        if not self._attached_files:
            self._pills_container.setVisible(False)

    def _clear_file_pills(self):
        """清空所有附件标签"""
        for pill in self._file_pills:
            pill.deleteLater()
        self._file_pills.clear()
        self._attached_files.clear()
        self._pills_container.setVisible(False)

    # ─── 拖拽文件支持 ───
    def _drag_enter_event(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.ai_chat.setStyleSheet("""
                QTextBrowser {
                    background: rgba(20,10,40,230); color: #bb99dd;
                    border: 2px dashed rgba(255,170,80,180); border-radius: 10px;
                    padding: 12px; font-size: 12px; line-height: 1.6;
                }
            """)

    def _drop_event(self, event: QDropEvent):
        self.ai_chat.setStyleSheet("""
            QTextBrowser {
                background: rgba(8,4,16,230); color: #bb99dd;
                border: 1px solid rgba(170,80,255,35); border-radius: 10px;
                padding: 12px; font-size: 12px; line-height: 1.6;
            }
        """)
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if filepath and os.path.isfile(filepath):
                self._add_file_pill(filepath)
        event.acceptProposedAction()

    # ─── 右键菜单 ───
    def _on_chat_context_menu(self, pos):
        menu = QMenu(self)
        copy_action = QAction("复制选中文本", self)
        copy_action.triggered.connect(self.ai_chat.copy)
        menu.addAction(copy_action)

        copy_all_action = QAction("复制全部对话", self)
        copy_all_action.triggered.connect(lambda: QApplication.clipboard().setText(
            self.ai_chat.toPlainText()
        ))
        menu.addAction(copy_all_action)

        menu.addSeparator()

        regen_action = QAction("重新生成", self)
        regen_action.triggered.connect(self._on_regenerate)
        menu.addAction(regen_action)

        menu.exec_(self.ai_chat.mapToGlobal(pos))

    def _on_regenerate(self):
        """重新生成：移除最后一条 AI 回复，重新发送上一条用户消息"""
        if not self._messages:
            return
        # 找到最后一条 user 消息
        last_user_msg = None
        for i in range(len(self._messages) - 1, -1, -1):
            if self._messages[i]["role"] == "user":
                last_user_msg = self._messages[i]["content"]
                # 移除该 user 之后的所有消息
                self._messages = self._messages[:i]
                break
        if last_user_msg is None:
            return
        # 清屏重绘（简化：清空并重新 append 剩余消息）
        self.ai_chat.clear()
        for msg in self._messages:
            if msg["role"] == "user":
                self._append_user_msg(msg["content"])
            elif msg["role"] == "assistant":
                self._append_ai_msg(msg["content"])
        # 重新发送
        self.ai_input.setText(last_user_msg)
        self._ai_send()

    # ─── 流式状态切换 ───
    def _enter_streaming_ui(self):
        """进入流式输出 UI：发送变停止"""
        self.btn_send.setVisible(False)
        self.btn_stop.setVisible(True)
        self._stop_requested = False

    def _exit_streaming_ui(self):
        """退出流式输出 UI：停止变发送"""
        self.btn_stop.setVisible(False)
        self.btn_send.setVisible(True)

```
