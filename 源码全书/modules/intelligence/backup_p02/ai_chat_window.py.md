# `modules/intelligence/backup_p02/ai_chat_window.py`

> 路径：`modules/intelligence/backup_p02/ai_chat_window.py` | 行数：703


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
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QComboBox, QApplication, QSplitter,
)
from PyQt5.QtCore import Qt, pyqtSignal

from modules.intelligence.ai_chat_styles import (
    INPUT_STYLE, BTN_PRIMARY, BTN_DANGER, BTN_SETTINGS,
)
from modules.intelligence.chat_session_manager import ChatSessionManager
from modules.intelligence.offline_analyzer import gather_context, offline_analysis
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


class AIChatWindow(QWidget):
    """AI助手 · NEURAL v5 — 统一 AgentBridge，顶部嵌入紧凑模型选择器"""

    chat_close_requested = pyqtSignal()

    def __init__(self, parent=None, opcclaw_engine=None, floating_mode=False, voice=None, embedded=False):
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
        self._current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._current_title = "新对话"
        self._messages = []       # [{role, content}, ...] 当前会话消息缓存

        self._all_models = []  # 全量模型列表（云端+本地）
        self._current_model = ""
        self._current_provider_id = ""
        if self._bridge and hasattr(self._bridge, "get_model"):
            self._current_model = self._bridge.get_model()

        self._build_ui()
        self._populate_provider_combo()
        self._refresh_model_list()

        # standalone 模式：窗口居中显示
        if not embedded:
            screen = QApplication.primaryScreen()
            if screen:
                geom = screen.availableGeometry()
                self.move((geom.width() - self.width()) // 2,
                           (geom.height() - self.height()) // 2)

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

        self.ai_chat = QTextEdit()
        self.ai_chat.setReadOnly(True)
        self.ai_chat.setStyleSheet("""
            QTextEdit {
                background: rgba(8,4,16,230); color: #bb99dd;
                border: 1px solid rgba(170,80,255,35); border-radius: 10px;
                padding: 12px; font-size: 12px; line-height: 1.6;
            }
        """)
        right_layout.addWidget(self.ai_chat, 1)

        # 输入行
        ir = QHBoxLayout()
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("输入问题，如：分析本月销售趋势...")
        self.ai_input.setStyleSheet(INPUT_STYLE)
        self.ai_input.returnPressed.connect(self._ai_send)
        ir.addWidget(self.ai_input, 1)

        send = QPushButton("发送")
        send.setStyleSheet(BTN_PRIMARY)
        send.clicked.connect(self._ai_send)
        ir.addWidget(send)

        clear_btn = QPushButton("清屏")
        clear_btn.setStyleSheet(BTN_DANGER)
        clear_btn.clicked.connect(self._on_clear_chat)
        ir.addWidget(clear_btn)
        right_layout.addLayout(ir)

        self._splitter.addWidget(right_widget)
        self._splitter.setStretchFactor(0, 0)  # 左侧不拉伸
        self._splitter.setStretchFactor(1, 1)  # 右侧拉伸

        l.addWidget(self._splitter, 1)

    def _on_clear_chat(self):
        """清屏并清空本地消息缓存"""
        self.ai_chat.clear()
        self._messages = []

    def closeEvent(self, event):
        """窗口关闭时保存当前会话"""
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
                pass
        super().closeEvent(event)

    # ─── 会话切换 ───
    def _on_session_selected(self, session_id: str, title: str):
        """切换会话"""
        self._switch_to_session(session_id, title)

    def _on_new_session(self):
        """新建空白会话"""
        new_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._switch_to_session(new_id, "新对话")

    def _on_session_deleted(self, session_id: str):
        """外部删除会话后：若为当前会话则切换到新会话"""
        if self._current_session_id == session_id:
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
                pass

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
                pass

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

    # ─── 交互逻辑 ───
    def _append_user_msg(self, text):
        now = datetime.now().strftime("%H:%M:%S")
        self.ai_chat.append(
            f'<p style="color:#ffaa44;font-weight:700;">[{now}] 你:</p>'
            f'<p style="color:#ddccff;">{text}</p>'
        )

    def _append_ai_msg(self, text, offline=False):
        now = datetime.now().strftime("%H:%M:%S")
        tag = "AI(离线)" if offline else "AI"
        self.ai_chat.append(
            f'<p style="color:#44ccff;font-weight:700;">[{now}] {tag}:</p>'
            f'<p style="color:#ccaaff;">{text}</p>'
        )

    # ─── 流式输出方法 ───
    def _stream_begin(self):
        self._streaming = True
        self._stream_buffer = ""
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
        # 用 QTextCursor 替换最后一个段落，移除闪烁光标
        cursor = self.ai_chat.textCursor()
        cursor.movePosition(cursor.End)
        cursor.movePosition(cursor.StartOfBlock, cursor.KeepAnchor)
        cursor.removeSelectedText()
        escaped = full_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        cursor.insertHtml(f'<p style="color:#ccaaff;">{escaped}</p>')
        self._stream_buffer = ""
        # 消息跟踪 + 增量保存
        self._messages.append({"role": "assistant", "content": full_text})
        if self._bridge:
            try:
                self._bridge.append_message("assistant", full_text, self._current_session_id)
            except Exception:
                pass

    def _stream_error(self, err_msg: str):
        import sys, datetime
        print(f"[DIAG][{datetime.datetime.now().strftime('%H:%M:%S')}] AIChatWindow._stream_error: {err_msg}", flush=True)
        self._streaming = False
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
            except Exception:
                pass

        # ── 优先级 1: AgentBridge 流式输出 ──
        if self._bridge is not None and hasattr(self._bridge, "chat_stream"):
            try:
                import sys, datetime
                print(f"[DIAG][{datetime.datetime.now().strftime('%H:%M:%S')}] AIChatWindow._ai_send — calling bridge.chat_stream()...", flush=True)
                self._stream_begin()
                self._bridge.chat_stream(
                    text,
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
                    reply = self._bridge.chat(text)
                elif hasattr(self._bridge, "query"):
                    reply = self._bridge.query(text)
                if reply:
                    self._append_ai_msg(reply)
                    self._messages.append({"role": "assistant", "content": reply})
                    if self._bridge:
                        try:
                            self._bridge.append_message("assistant", reply, self._current_session_id)
                        except Exception:
                            pass
                    return
            except Exception as e:
                self.ai_chat.append(
                    f'<p style="color:#ffaa44;font-size:10px;">[系统] AgentBridge 调用失败 ({e})，回退离线分析</p>'
                )

        # ── 优先级 3: 离线分析兜底 ──
        try:
            offline_resp = offline_analysis(text)
            self._append_ai_msg(offline_resp, offline=True)
            self._messages.append({"role": "assistant", "content": offline_resp})
        except Exception as e:
            self.ai_chat.append(f'<p style="color:#ff6666;">错误: {e}</p>')
            traceback.print_exc()

```
