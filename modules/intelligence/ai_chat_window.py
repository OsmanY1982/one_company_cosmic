"""
AI助手 · NEURAL v4 — 统一 AgentBridge 对话窗口
全部模型调用通过 AgentBridge（opcclaw 引擎），废弃独立 llm_config.json
模型切换通过 AgentBridge.switch_model() 同步更新后端
降级路径：AgentBridge.chat_stream → AgentBridge.chat → 离线分析
"""
import traceback
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QComboBox,
)
from PyQt5.QtCore import Qt

from modules.intelligence.ai_chat_styles import (
    INPUT_STYLE, BTN_PRIMARY, BTN_DANGER, BTN_SETTINGS,
)
from modules.intelligence.offline_analyzer import gather_context, offline_analysis


class AIChatWindow(QDialog):
    """AI助手 · NEURAL v4 — 统一 AgentBridge，无独立 LLM 配置"""

    def __init__(self, parent=None, opcclaw_engine=None):
        super().__init__(parent)
        self.setWindowTitle("AI助手 · NEURAL v4")
        self.setMinimumSize(750, 580)
        self.setStyleSheet("background: rgba(10,5,20,240);")

        self._bridge = opcclaw_engine  # AgentBridge 实例（唯一引擎）
        self._streaming = False
        self._stream_buffer = ""
        self._all_models = []  # 全量模型列表（云端+本地）
        self._current_model = ""
        if self._bridge and hasattr(self._bridge, "get_model"):
            self._current_model = self._bridge.get_model()

        self._build_ui()
        self._refresh_model_list()

    # ─── UI ───
    def _build_ui(self):
        l = QVBoxLayout(self)
        l.setSpacing(10)
        l.setContentsMargins(16, 12, 16, 12)

        # 顶部信息行
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

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

        # 模型切换下拉框
        model_lbl = QLabel("模型:")
        model_lbl.setStyleSheet("color: #9988aa; font-size: 11px; background: transparent;")
        top_row.addWidget(model_lbl)

        self.cb_model = QComboBox()
        self.cb_model.setMinimumWidth(200)
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
        self.cb_model.currentIndexChanged.connect(self._on_model_changed)
        top_row.addWidget(self.cb_model)

        # 刷新模型按钮
        refresh_btn = QPushButton("⟳")
        refresh_btn.setToolTip("刷新本地模型列表")
        refresh_btn.setFixedSize(28, 24)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: rgba(100,140,200,35); color: #99bbee; border: none;
                border-radius: 12px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(120,160,220,60); }
        """)
        refresh_btn.clicked.connect(self._refresh_model_list)
        top_row.addWidget(refresh_btn)

        l.addLayout(top_row)

        # 对话区域
        self.ai_chat = QTextEdit()
        self.ai_chat.setReadOnly(True)
        self.ai_chat.setStyleSheet("""
            QTextEdit {
                background: rgba(8,4,16,230); color: #bb99dd;
                border: 1px solid rgba(170,80,255,35); border-radius: 10px;
                padding: 12px; font-size: 12px; line-height: 1.6;
            }
        """)
        l.addWidget(self.ai_chat, 1)

        # 快捷提示按钮
        prompts_row = QHBoxLayout()
        prompts_row.setSpacing(6)
        quick_prompts = [
            ("今日经营分析", "请分析今天的经营数据，包括销售额、订单量和客户活跃度"),
            ("查看销售数据", "查询并汇总最近的销售数据，按产品和时间段展示"),
            ("库存预警检查", "检查当前库存状态，列出需要补货的产品"),
            ("生成日报", "根据今日订单数据自动生成一份经营日报"),
            ("客户洞察", "分析客户购买行为，识别高价值客户和流失风险"),
        ]
        for label, prompt_text in quick_prompts:
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(150,60,220,20); color: #bb99dd;
                    border: 1px solid rgba(170,80,255,25); border-radius: 12px;
                    padding: 4px 10px; font-size: 10px;
                }
                QPushButton:hover { background: rgba(170,80,240,50); color: #ddaaff; }
            """)
            btn.clicked.connect(lambda _, pt=prompt_text: self._ai_quick_prompt(pt))
            prompts_row.addWidget(btn)
        prompts_row.addStretch()
        l.addLayout(prompts_row)

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
        clear_btn.clicked.connect(lambda: self.ai_chat.clear())
        ir.addWidget(clear_btn)
        l.addLayout(ir)

    # ─── 模型管理（通过 AgentBridge 统一管理）───
    def _format_size(self, size_bytes: int) -> str:
        if size_bytes >= 1024 ** 3:
            return f"{size_bytes / (1024**3):.1f} GB"
        if size_bytes >= 1024 ** 2:
            return f"{size_bytes / (1024**2):.0f} MB"
        return f"{size_bytes / 1024:.0f} KB"

    def _refresh_model_list(self):
        """从 AgentBridge 拉取全量模型列表（云端+自定义+本地）"""
        self.cb_model.blockSignals(True)
        self.cb_model.clear()
        self._all_models = []  # 存储 {provider_id, model, category, ...} 用于切换查找

        if self._bridge and hasattr(self._bridge, "list_all_models"):
            try:
                all_models = self._bridge.list_all_models()
            except Exception:
                all_models = []
        else:
            all_models = []

        cloud_models = [m for m in all_models if m.get("category") == "cloud"]
        local_models = [m for m in all_models if m.get("category") == "local"]

        # 云端模型分组
        if cloud_models:
            self.cb_model.addItem("── 云端模型 ──")
            self._all_models.append(None)  # 分隔项占位
            for m in cloud_models:
                display = f"  {m['provider_name']} · {m['model']}"
                self.cb_model.addItem(display, m)
                self._all_models.append(m)

        # 本地模型分组
        if local_models:
            self.cb_model.addItem("── 本地模型 ──")
            self._all_models.append(None)
            for m in local_models:
                size_info = ""
                if m.get("size"):
                    size_info = f" ({self._format_size(m['size'])})"
                display = f"  {m['model']}{size_info}"
                self.cb_model.addItem(display, m)
                self._all_models.append(m)

        # 无模型时占位
        if not cloud_models and not local_models:
            self.cb_model.addItem("（暂无已配置模型）")

        # 选中当前模型
        if self._current_model:
            for i in range(self.cb_model.count()):
                data = self.cb_model.itemData(i)
                if data and isinstance(data, dict) and data.get("model") == self._current_model:
                    self.cb_model.setCurrentIndex(i)
                    break

        self.cb_model.blockSignals(False)

    def _on_model_changed(self, idx: int):
        data = self.cb_model.itemData(idx)
        if not data or not isinstance(data, dict):
            return

        provider_id = data.get("provider_id", "")
        model = data.get("model", "")
        if not model or model == self._current_model:
            return

        self._current_model = model

        if self._bridge and hasattr(self._bridge, "switch_model"):
            try:
                self._bridge.switch_model(provider_id, model)
                prov_name = data.get("provider_name", provider_id)
                self.ai_chat.append(
                    f'<p style="color:#44cc88;font-size:10px;">[系统] AgentBridge 已切换到: {prov_name} / {model}</p>'
                )
                prov = self._bridge.get_provider_info() if hasattr(self._bridge, "get_provider_info") else {}
                self.lbl_status.setText(
                    f"AgentBridge: {prov.get('name', prov_name)} / {model}"
                )
            except Exception as e:
                self.ai_chat.append(
                    f'<p style="color:#ffaa44;font-size:10px;">[系统] 切换失败: {e}</p>'
                )
        else:
            self.ai_chat.append(
                f'<p style="color:#ffaa44;font-size:10px;">[系统] 已选择模型: {model}（需 AgentBridge 支持实时切换）</p>'
            )

    # ─── 交互逻辑 ───
    def _ai_quick_prompt(self, prompt_text):
        self.ai_input.setText(prompt_text)
        self._ai_send()

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
        self.ai_chat.append(
            f'<p style="color:#44ccff;font-weight:700;">[{now}] AI:</p>'
            f'<p id="stream-line" style="color:#ccaaff;">▌</p>'
        )

    def _stream_chunk(self, chunk: str):
        self._stream_buffer += chunk
        content = self.ai_chat.toHtml()
        # 找到最后一个 stream-line 并更新
        import re
        updated = re.sub(
            r'<p id="stream-line" style="color:#ccaaff;">.*?</p>',
            '<p id="stream-line" style="color:#ccaaff;">'
            + self._stream_buffer.replace("\n", "<br>").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            + "▌</p>",
            content,
        )
        self.ai_chat.setHtml(updated)
        sb = self.ai_chat.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _stream_tool(self, tool_name: str, status: str):
        color = {"running": "#99bbee", "OK": "#44cc88", "Failed": "#ff6644"}.get(status, "#888")
        icon = {"running": "⚙", "OK": "✓", "Failed": "✗"}.get(status, "?")
        self.ai_chat.append(
            f'<p style="color:{color};font-size:10px;margin:0;">{icon} 工具: {tool_name} [{status}]</p>'
        )

    def _stream_done(self, full_text: str):
        self._streaming = False
        content = self.ai_chat.toHtml()
        final = content.replace("▌</p>", "</p>")
        self.ai_chat.setHtml(final)
        self._stream_buffer = ""

    def _stream_error(self, err_msg: str):
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

        # ── 优先级 1: AgentBridge 流式输出 ──
        if self._bridge is not None and hasattr(self._bridge, "chat_stream"):
            try:
                self._stream_begin()
                self._bridge.chat_stream(
                    text,
                    on_chunk=self._stream_chunk,
                    on_done=self._stream_done,
                    on_tool=self._stream_tool,
                )
                return
            except Exception as e:
                self.ai_chat.append(
                    f'<p style="color:#ffaa44;font-size:10px;">[系统] 流式启动失败 ({e})，回退同步模式</p>'
                )

        # ── 优先级 2: AgentBridge 同步 chat ──
        if self._bridge is not None:
            try:
                if hasattr(self._bridge, "chat"):
                    reply = self._bridge.chat(text)
                    self._append_ai_msg(reply)
                    return
                elif hasattr(self._bridge, "query"):
                    reply = self._bridge.query(text)
                    self._append_ai_msg(reply)
                    return
            except Exception as e:
                self.ai_chat.append(
                    f'<p style="color:#ffaa44;font-size:10px;">[系统] AgentBridge 调用失败 ({e})，回退离线分析</p>'
                )

        # ── 优先级 3: 离线分析兜底 ──
        try:
            offline_resp = offline_analysis(text)
            self._append_ai_msg(offline_resp, offline=True)
        except Exception as e:
            self.ai_chat.append(f'<p style="color:#ff6666;">错误: {e}</p>')
            traceback.print_exc()
