"""
聊天消息气泡组件
"""

from datetime import datetime
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QTextOption

from ._shared import COLORS


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

        self.content = QTextEdit()
        self.content.setReadOnly(True)
        self.content.setPlainText(text)
        self.content.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.content.setFrameShape(QFrame.NoFrame)
        self.content.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content.setStyleSheet("font-size: 18px; color: #1E293B; line-height: 1.6; background: transparent; border: none; padding: 0;")
        self.content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.content.setMinimumWidth(160)
        self.content.document().setDocumentMargin(0)
        # 禁止 QTextEdit 接管 Ctrl+Scroll 缩放，但保留文本选择
        self.content.setContextMenuPolicy(Qt.NoContextMenu)
        # 自适应高度：内容变化时更新 QTextEdit 的固定高度
        self.content.document().contentsChanged.connect(self._update_height)
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
        self.content.setPlainText(text)
        self._text = text  # 更新保存的文字

    def _update_height(self):
        """根据文档内容动态调整 QTextEdit 高度"""
        doc = self.content.document()
        doc.setTextWidth(self.content.viewport().width())
        h = int(doc.size().height())
        if h != self.content.height():
            self.content.setFixedHeight(h + 4)  # +4 避免底部裁切