# `opcclaw/modules/agent_event_panel.py`

> 路径：`opcclaw/modules/agent_event_panel.py` | 行数：372


---


```python
# -*- coding: utf-8 -*-
"""
AgentEventPanel — 聊天消息流中嵌入的 Agent 执行过程可视化组件

用法:
    panel = AgentEventPanel()
    panel.add_event({'type': 'THINK', 'step': 1, 'total_steps': 5,
                     'message': '分析需求...', 'data': {}})
    panel.set_complete("查询到 3 条结果")
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QWidget, QLabel,
    QProgressBar, QTextEdit, QPushButton, QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont

from opcclaw.modules._shared import COLORS


# ═══════════════════════════════════════════
# 单条事件条目 Widget
# ═══════════════════════════════════════════

class _EventEntry(QFrame):
    """单条事件显示组件，包含可展开的参数/结果区"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._expanded = False
        self._detail_widget: QWidget = None
        self._detail_text: str = ""
        self._build_ui()

    def _build_ui(self):
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(8, 4, 8, 4)
        self._main_layout.setSpacing(4)

        # 标题行
        self._header_row = QHBoxLayout()
        self._header_row.setSpacing(4)

        self._icon_label = QLabel("")
        self._icon_label.setFixedWidth(22)
        self._icon_label.setAlignment(Qt.AlignCenter)
        self._header_row.addWidget(self._icon_label)

        self._msg_label = QLabel("")
        self._msg_label.setWordWrap(True)
        self._msg_label.setTextFormat(Qt.PlainText)
        self._header_row.addWidget(self._msg_label, stretch=1)

        self._expand_btn = QPushButton("▸")
        self._expand_btn.setFixedSize(20, 20)
        self._expand_btn.setFlat(True)
        self._expand_btn.setCursor(Qt.PointingHandCursor)
        self._expand_btn.clicked.connect(self._toggle_expand)
        self._expand_btn.hide()
        self._header_row.addWidget(self._expand_btn)

        self._main_layout.addLayout(self._header_row)

    def set_event(self, icon: str, message: str, bg_color: str, text_color: str,
                  detail_text: str = ""):
        self._icon_label.setText(icon)
        self._msg_label.setText(message)
        self.setStyleSheet(f"""
            _EventEntry {{
                background: {bg_color};
                border-radius: 6px;
                margin: 1px 0px;
            }}
        """)
        self._msg_label.setStyleSheet(f"color: {text_color}; font-size: 12px;")

        self._detail_text = detail_text
        if detail_text:
            self._expand_btn.show()
        else:
            self._expand_btn.hide()

    def _toggle_expand(self):
        if self._expanded:
            self._collapse()
        else:
            self._expand()

    def _expand(self):
        if self._detail_widget:
            return
        self._detail_widget = QTextEdit()
        self._detail_widget.setReadOnly(True)
        self._detail_widget.setPlainText(self._detail_text)
        self._detail_widget.setMaximumHeight(200)
        self._detail_widget.setStyleSheet(f"""
            QTextEdit {{
                background: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3C3C3C;
                border-radius: 4px;
                font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
                font-size: 11px;
                padding: 6px;
            }}
        """)
        self._main_layout.addWidget(self._detail_widget)
        self._expand_btn.setText("▾")
        self._expanded = True

    def _collapse(self):
        if self._detail_widget:
            self._main_layout.removeWidget(self._detail_widget)
            self._detail_widget.deleteLater()
            self._detail_widget = None
        self._expand_btn.setText("▸")
        self._expanded = False


# ═══════════════════════════════════════════
# AgentEventPanel 主组件
# ═══════════════════════════════════════════

class AgentEventPanel(QFrame):
    """
    Agent 执行过程可视化面板，内嵌在聊天消息流中。

    提供 add_event / set_complete / set_error / set_cancelled 方法。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self._complete = False
        self._entries: list[_EventEntry] = []

        self.setObjectName("AgentEventPanel")
        self.setStyleSheet(f"""
            #AgentEventPanel {{
                background: {COLORS['card']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
            }}
        """)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # ── 标题栏 ──
        self._header = QFrame()
        self._header.setCursor(Qt.PointingHandCursor)
        self._header.mousePressEvent = self._on_header_click
        self._header.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['primary']};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                padding: 8px 12px;
            }}
        """)
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(12, 6, 12, 6)
        header_layout.setSpacing(8)

        self._title_label = QLabel("Agent 执行中...")
        self._title_label.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
        header_layout.addWidget(self._title_label)

        header_layout.addStretch()

        self._step_label = QLabel("")
        self._step_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 11px;")
        header_layout.addWidget(self._step_label)

        self._collapse_btn = QPushButton("▾")
        self._collapse_btn.setFixedSize(22, 22)
        self._collapse_btn.setFlat(True)
        self._collapse_btn.setStyleSheet("color: white; font-size: 14px; border: none;")
        self._collapse_btn.clicked.connect(self._toggle_panel)
        header_layout.addWidget(self._collapse_btn)

        self._layout.addWidget(self._header)

        # ── 条目容器 ──
        self._body = QWidget()
        self._body.setStyleSheet(f"background: {COLORS['card']};")
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(6, 4, 6, 4)
        self._body_layout.setSpacing(2)
        self._layout.addWidget(self._body)

        # ── 底部圆角补丁 (body 区域) ──
        self._bottom = QWidget()
        self._bottom.setFixedHeight(6)
        self._bottom.setStyleSheet(f"""
            background: {COLORS['card']};
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
        """)
        self._layout.addWidget(self._bottom)

    # ── 事件类型 → 样式映射 ──

    _EVENT_STYLES = {
        "THINK":     ("💭",  "#E8F0FE", COLORS["text"]),       # 灰蓝色
        "PLAN":      ("📋", "#D4E6F1", COLORS["text"]),       # 蓝色
        "ACT":       ("🔧", "#FFF3CD", "#856404"),              # 黄色
        "OBSERVE":   ("👁", "#D5F5E3", "#145A32"),            # 绿色
        "REFLECT":   ("🔄", "#E8D5F5", "#4A235A"),            # 紫色
        "ERROR":     ("❌", "#FADBD8", "#922B21"),            # 红色
        "COMPLETE":  ("✅", "#D5F5E3", "#145A32"),            # 绿色
        "CANCELLED": ("⏹", "#F2F3F4", COLORS["text_light"]),
    }

    # ── 公开方法 ──

    def add_event(self, event: dict):
        """
        添加一个事件条目。

        event 格式:
            {
                'type': 'THINK',      # THINK / PLAN / ACT / OBSERVE / REFLECT /
                                      #   COMPLETE / ERROR / CANCELLED / PROGRESS
                'step': 1,
                'total_steps': 5,
                'message': '...',
                'data': {...},         # ACT 时为工具参数
                'value': 30,           # PROGRESS 时为进度百分比
            }
        """
        etype = event.get("type", "UNKNOWN")
        step = event.get("step", 0)
        total = event.get("total_steps", 0)

        # 更新步骤计数
        if step and total:
            self._step_label.setText(f"步骤 {step}/{total}")
        elif step:
            self._step_label.setText(f"步骤 {step}")

        # PROGRESS 事件 → 进度条
        if etype == "PROGRESS":
            self._add_progress_bar(event.get("value", 0))
            return

        # 终结事件
        if etype == "COMPLETE":
            summary = event.get("message", "完成")
            self.set_complete(summary)
            return
        if etype == "ERROR":
            self.set_error(event.get("message", "错误"))
            return
        if etype == "CANCELLED":
            self.set_cancelled()
            return

        # 普通事件条目
        style = self._EVENT_STYLES.get(etype, ("📌", COLORS["card"], COLORS["text"]))
        icon, bg, text_color = style

        detail = ""
        data = event.get("data", {})
        if etype == "ACT" and data:
            tool_name = event.get("message", "调用工具")
            import json
            detail = json.dumps(data, ensure_ascii=False, indent=2)
        elif etype == "OBSERVE" and data:
            import json
            detail = json.dumps(data, ensure_ascii=False, indent=2)
            if len(detail) > 500:
                detail = detail[:500] + "\n... (截断)"

        entry = _EventEntry(self._body)
        entry.set_event(icon, event.get("message", ""), bg, text_color, detail)
        self._body_layout.addWidget(entry)
        self._entries.append(entry)

    def _add_progress_bar(self, value: int):
        bar = QProgressBar()
        bar.setMinimum(0)
        bar.setMaximum(100)
        bar.setValue(value)
        bar.setTextVisible(True)
        bar.setFormat(f"进度: {value}%")
        bar.setFixedHeight(18)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background: {COLORS['border']};
                border: none;
                border-radius: 4px;
                text-align: center;
                font-size: 10px;
                color: {COLORS['text']};
            }}
            QProgressBar::chunk {{
                background: {COLORS['primary']};
                border-radius: 4px;
            }}
        """)
        self._body_layout.addWidget(bar)

    def set_complete(self, summary: str = ""):
        """标记任务完成，标题变色为绿色并折叠为一行小结"""
        self._complete = True
        self._header.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['success']};
                border-radius: 10px;
                padding: 8px 12px;
            }}
        """)
        self._title_label.setText(f"✅ Agent 完成{f'：{summary}' if summary else ''}")
        self._title_label.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
        self._collapse_btn.hide()
        self._collapse_panel()

    def set_error(self, error: str = ""):
        """标记任务失败"""
        self._complete = True
        self._header.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['danger']};
                border-radius: 10px;
                padding: 8px 12px;
            }}
        """)
        self._title_label.setText(f"❌ {error or '执行出错'}")
        self._title_label.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
        self._collapse_btn.hide()

    def set_cancelled(self):
        """标记任务已取消"""
        self._complete = True
        self._header.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['text_light']};
                border-radius: 10px;
                padding: 8px 12px;
            }}
        """)
        self._title_label.setText("⏹ 已取消")
        self._title_label.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
        self._collapse_btn.hide()
        self._collapse_panel()

    # ── 折叠/展开 ──

    def _on_header_click(self, event):
        if not self._complete:
            self._toggle_panel()

    def _toggle_panel(self):
        if self._collapsed:
            self._expand_panel()
        else:
            self._collapse_panel()

    def _collapse_panel(self):
        self._body.setVisible(False)
        self._bottom.setVisible(False)
        self._collapse_btn.setText("▸")
        self._collapsed = True

    def _expand_panel(self):
        self._body.setVisible(True)
        self._bottom.setVisible(True)
        self._collapse_btn.setText("▾")
        self._collapsed = False

```
