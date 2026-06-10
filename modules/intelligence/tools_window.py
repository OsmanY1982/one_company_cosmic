"""
工具箱 · NEURAL — 导航窗口
点击按钮卡片打开编辑器子窗口或保险箱子窗口
"""
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

# ═══════ QSS ═══════
CARD_STYLE = """
    QPushButton {
        background: rgba(18,10,32,220);
        color: #ccbbdd;
        border: 1px solid rgba(170,80,255,40);
        border-radius: 16px;
        padding: 24px 32px;
        font-size: 15px;
        font-weight: 700;
        letter-spacing: 3px;
        text-align: center;
    }
    QPushButton:hover {
        background: rgba(30,16,48,235);
        border: 1px solid rgba(200,100,255,100);
        color: #eeeeff;
    }
"""


class ToolsWindow(QDialog):
    """工具箱 · NEURAL — 导航窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("工具箱 · NEURAL")
        self.setMinimumSize(440, 320)
        self.setStyleSheet("background: rgba(10,5,20,240);")
        self._build_ui()

    def _build_ui(self):
        from core.cosmic import CosmicBackground
        self._bg = CosmicBackground()
        self._bg.setFixedSize(self.minimumWidth(), self.minimumHeight())

        l = QVBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(self._bg)

        # ── HUD 叠加层 ──
        overlay = QWidget(self._bg)
        overlay.setAttribute(Qt.WA_TranslucentBackground)
        overlay.setGeometry(0, 0, self.minimumWidth(), self.minimumHeight())

        ol = QVBoxLayout(overlay)
        ol.setSpacing(0)
        ol.setContentsMargins(0, 0, 0, 0)

        ol.addStretch(1)

        # 标题
        title = QLabel("工具箱")
        title.setStyleSheet("color: #ddaaff; font-size: 22px; font-weight: 800; letter-spacing: 8px; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        ol.addWidget(title)

        subtitle = QLabel("选择工具模块")
        subtitle.setStyleSheet("color: #776699; font-size: 11px; letter-spacing: 3px; background: transparent;")
        subtitle.setAlignment(Qt.AlignCenter)
        ol.addWidget(subtitle)
        ol.addSpacing(28)

        # ── 按钮卡片区 ──
        card_row = QHBoxLayout()
        card_row.setSpacing(24)
        card_row.setAlignment(Qt.AlignCenter)

        btn_editor = QPushButton("文本编辑器")
        btn_editor.setStyleSheet(CARD_STYLE)
        btn_editor.setFixedSize(160, 80)
        btn_editor.setCursor(Qt.PointingHandCursor)
        btn_editor.clicked.connect(self._open_editor)
        card_row.addWidget(btn_editor)

        btn_vault = QPushButton("密码保险箱")
        btn_vault.setStyleSheet(CARD_STYLE)
        btn_vault.setFixedSize(160, 80)
        btn_vault.setCursor(Qt.PointingHandCursor)
        btn_vault.clicked.connect(self._open_vault)
        card_row.addWidget(btn_vault)

        ol.addLayout(card_row)

        ol.addSpacing(2)

        # 底部提示
        hint = QLabel("NEURAL · 智能工具箱")
        hint.setStyleSheet("color: #443366; font-size: 10px; background: transparent;")
        hint.setAlignment(Qt.AlignCenter)
        ol.addWidget(hint)

        ol.addStretch(1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self.width()
        h = self.height()
        if w > 0 and h > 0:
            self._bg.setFixedSize(w, h)

    # ═══════ 导航路由 ═══════
    def _open_editor(self):
        from modules.intelligence.editor_window import EditorWindow
        dlg = EditorWindow(self)
        dlg.exec_()

    def _open_vault(self):
        from modules.intelligence.vault_window import VaultWindow
        dlg = VaultWindow(self)
        dlg.exec_()
