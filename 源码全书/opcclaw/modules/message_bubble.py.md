# `opcclaw/modules/message_bubble.py`

> 路径：`opcclaw/modules/message_bubble.py` | 行数：267


---


```python
"""
聊天消息气泡组件
"""

import re
from datetime import datetime
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QTextEdit, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QTextOption

from ._shared import COLORS

# ── Markdown 检测正则（简单启发式）──
_MD_PATTERNS = [
    r'^#{1,6}\s',           # 标题
    r'\*\*.*\*\*',          # 加粗
    r'`[^`]+`',             # 行内代码
    r'```',                 # 代码块
    r'^\s*[-*+]\s',         # 无序列表
    r'^\s*\d+\.\s',         # 有序列表
    r'\[.+\]\(.+\)',        # 链接
    r'^\s*>\s',             # 引用
    r'\|.*\|.*\|',          # 表格
]


def _detect_markdown(text: str) -> bool:
    """检测文本是否包含 Markdown 语法"""
    return any(re.search(p, text, re.MULTILINE) for p in _MD_PATTERNS)


def _markdown_to_html(text: str) -> str:
    """将 Markdown 文本转换为带样式的 HTML"""
    import markdown as mdlib
    raw_html = mdlib.markdown(text, extensions=['fenced_code', 'tables'])
    css = (
        "<style>"
        "body { font-size: 14px; color: #1E293B; line-height: 1.6; margin: 0; }"
        "code { font-family: 'SF Mono', 'Menlo', 'Monaco', 'Courier New', monospace; "
        "background: #F1F5F9; padding: 1px 5px; border-radius: 3px; font-size: 13px; }"
        "pre { background-color: #1E293B; color: #E2E8F0; padding: 12px; border-radius: 8px; "
        "overflow-x: auto; font-size: 13px; line-height: 1.5; }"
        "pre code { background: transparent; color: inherit; padding: 0; font-size: 13px; }"
        "p { margin: 4px 0; }"
        "h1, h2, h3, h4, h5, h6 { margin: 10px 0 4px 0; }"
        "ul, ol { margin: 4px 0; padding-left: 22px; }"
        "table { border-collapse: collapse; width: 100%; margin: 6px 0; }"
        "th, td { border: 1px solid #E2E8F0; padding: 6px 10px; text-align: left; }"
        "th { background-color: #F1F5F9; font-weight: 600; }"
        "blockquote { border-left: 3px solid #94A3B8; padding-left: 12px; "
        "color: #64748B; margin: 8px 0; }"
        "a { color: #2563EB; }"
        "</style>"
    )
    return css + raw_html


class MessageBubble(QFrame):
    """聊天消息气泡"""

    # AI 消息操作按钮信号
    like_clicked = pyqtSignal(str)       # 点赞
    dislike_clicked = pyqtSignal(str)    # 点踩
    play_clicked = pyqtSignal(str)       # 朗读
    share_clicked = pyqtSignal(str)      # 分享
    regenerate_requested = pyqtSignal()  # 重新生成

    def __init__(self, text: str, sender: str = "ai",
                 is_markdown: bool = None, parent=None):
        super().__init__(parent)
        self.sender = sender
        self._text = text       # 原始文字
        self._timestamp = datetime.now().strftime("%H:%M")

        # 自动检测 Markdown
        if is_markdown is None:
            self._is_markdown = _detect_markdown(text)
        else:
            self._is_markdown = is_markdown

        bg_map = {
            "user": "#DCF8C6",
            "ai": "#F8FAFC",
            "tool": "#F0F4F8",
            "error": "#FDE8E8",
        }
        bg = bg_map.get(sender, "#FFFFFF")

        self.setStyleSheet(f"""
            MessageBubble {{
                background-color: {bg};
                border-radius: 12px;
                padding: 10px 14px;
                margin: 2px 8px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumWidth(200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        # ── 头部行：发送者标签 + 时间 ──
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)

        label_map = {"user": "我", "ai": "OPCclaw", "tool": "⚡ 工具", "error": "⚠️ 错误"}
        sender_label = QLabel(label_map.get(sender, ""))
        sender_label.setStyleSheet("font-size: 11px; color: #64748B; font-weight: bold;")
        header_row.addWidget(sender_label)

        header_row.addStretch()

        time_label = QLabel(self._timestamp)
        time_label.setStyleSheet("font-size: 10px; color: #94A3B8;")
        header_row.addWidget(time_label)

        layout.addLayout(header_row)

        # ── 内容区：QTextEdit ──
        self.content = QTextEdit()
        self.content.setReadOnly(True)
        self.content.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.content.setFrameShape(QFrame.NoFrame)
        self.content.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content.setStyleSheet(
            "font-size: 14px; color: #1E293B; line-height: 1.6; "
            "background: transparent; border: none; padding: 0;"
        )
        self.content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.content.setMinimumWidth(160)
        self.content.document().setDocumentMargin(0)
        self.content.setContextMenuPolicy(Qt.NoContextMenu)
        self.content.document().contentsChanged.connect(self._update_height)

        # 按检测结果选择渲染方式
        self._render_content(text)
        layout.addWidget(self.content)

        # ── 用户消息：复制按钮 ──
        if sender == "user":
            btn_row = QHBoxLayout()
            btn_row.setSpacing(4)
            btn_row.setContentsMargins(0, 4, 0, 0)
            btn_row.addStretch()

            user_btn_style = """
                QPushButton {
                    background-color: transparent;
                    color: #94A3B8;
                    border: 1px solid #E2E8F0;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #F1F5F9;
                    color: #475569;
                }
            """
            copy_btn = QPushButton("📋 复制")
            copy_btn.setStyleSheet(user_btn_style)
            copy_btn.clicked.connect(self._on_copy)
            btn_row.addWidget(copy_btn)
            layout.addLayout(btn_row)

        # ── AI 消息操作按钮行 ──
        if sender == "ai":
            btn_row = QHBoxLayout()
            btn_row.setSpacing(8)
            btn_row.setContentsMargins(0, 6, 0, 0)

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

            self.like_btn = QPushButton("👍 点赞")
            self.like_btn.setStyleSheet(btn_style)
            self.like_btn.clicked.connect(self._on_like_clicked)
            btn_row.addWidget(self.like_btn)

            self.dislike_btn = QPushButton("👎 点踩")
            self.dislike_btn.setStyleSheet(btn_style)
            self.dislike_btn.clicked.connect(self._on_dislike_clicked)
            btn_row.addWidget(self.dislike_btn)

            self.play_btn = QPushButton("🔊 朗读")
            self.play_btn.setStyleSheet(btn_style)
            self.play_btn.clicked.connect(self._on_play_clicked)
            btn_row.addWidget(self.play_btn)

            self.share_btn = QPushButton("📤 分享")
            self.share_btn.setStyleSheet(btn_style)
            self.share_btn.clicked.connect(self._on_share_clicked)
            btn_row.addWidget(self.share_btn)

            # 重新生成按钮
            self.regenerate_btn = QPushButton("🔄 重新生成")
            self.regenerate_btn.setStyleSheet(btn_style)
            self.regenerate_btn.clicked.connect(self._on_regenerate_clicked)
            btn_row.addWidget(self.regenerate_btn)

            btn_row.addStretch()
            layout.addLayout(btn_row)

    # ── 内容渲染 ──

    def _render_content(self, text: str):
        """根据检测结果选择纯文本或 HTML 渲染"""
        if self._is_markdown:
            html = _markdown_to_html(text)
            self.content.setHtml(html)
            # 禁用 QTextEdit 默认字体放大/缩小（Ctrl+滚轮），保持 14px
            self.content.zoomIn(0)
        else:
            self.content.setPlainText(text)

    # ── 按钮回调 ──

    def _on_like_clicked(self):
        self.like_clicked.emit(self._text)

    def _on_dislike_clicked(self):
        self.dislike_clicked.emit(self._text)

    def _on_play_clicked(self):
        self.play_clicked.emit(self._text)

    def _on_share_clicked(self):
        self.share_clicked.emit(self._text)

    def _on_regenerate_clicked(self):
        self.regenerate_requested.emit()

    def _on_copy(self):
        """复制用户消息到剪贴板"""
        QApplication.clipboard().setText(self._text)

    def set_text(self, text: str):
        """流式更新文本：重新检测 Markdown 并渲染"""
        self._text = text
        self._is_markdown = _detect_markdown(text)
        self._render_content(text)

    def _update_height(self):
        """根据文档内容动态调整 QTextEdit 高度"""
        doc = self.content.document()
        doc.setTextWidth(self.content.viewport().width())
        h = int(doc.size().height())
        if h != self.content.height():
            self.content.setFixedHeight(h + 4)
```
