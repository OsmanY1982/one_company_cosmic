"""
工具箱 · NEURAL — 导航窗口
点击按钮卡片打开：编辑器 / 保险箱 / 扫码工具 / 计算器
轨道式独立子窗口布局
"""
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QWidget,
    QLineEdit, QMessageBox, QFrame,
)
from PyQt5.QtCore import Qt

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

# ═══════ QSS ═══════
CARD_STYLE = """
    QPushButton {
        background: rgba(18,10,32,220);
        color: #ccbbdd;
        border: 1px solid rgba(170,80,255,40);
        border-radius: 16px;
        padding: 20px 16px;
        font-size: 14px;
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
CALC_BTN = """
    QPushButton {
        background: rgba(22,14,38,220);
        color: #ccbbdd;
        border: 1px solid rgba(170,80,255,35);
        border-radius: 10px;
        padding: 10px;
        font-size: 16px;
        font-weight: 700;
    }
    QPushButton:hover {
        background: rgba(36,22,56,235);
        border: 1px solid rgba(200,100,255,80);
    }
    QPushButton:pressed {
        background: rgba(50,30,70,220);
    }
"""
CALC_DISPLAY = """
    QLineEdit {
        background: rgba(14,8,26,230);
        color: #ddaaff;
        border: 1px solid rgba(170,80,255,40);
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 24px;
        font-weight: 700;
        font-family: 'Menlo', monospace;
    }
"""


class CalcDialog(QDialog):
    """计算器 · NEURAL — 内嵌轻量子窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("计算器 · NEURAL")
        self.setMinimumSize(340, 440)
        self.setStyleSheet("background: rgba(10,5,20,240);")
        self._expression = ""
        self._build_ui()

    def _build_ui(self):
        l = QVBoxLayout(self)
        l.setSpacing(10)
        l.setContentsMargins(16, 12, 16, 12)

        self._display = QLineEdit()
        self._display.setReadOnly(True)
        self._display.setAlignment(Qt.AlignRight)
        self._display.setStyleSheet(CALC_DISPLAY)
        self._display.setText("0")
        l.addWidget(self._display)

        grid = QGridLayout()
        grid.setSpacing(6)

        buttons = [
            ("C", 0, 0, self._clear), ("⌫", 0, 1, self._backspace),
            ("%", 0, 2, self._op), ("÷", 0, 3, self._op),
            ("7", 1, 0, self._digit), ("8", 1, 1, self._digit), ("9", 1, 2, self._digit),
            ("×", 1, 3, self._op),
            ("4", 2, 0, self._digit), ("5", 2, 1, self._digit), ("6", 2, 2, self._digit),
            ("−", 2, 3, self._op),
            ("1", 3, 0, self._digit), ("2", 3, 1, self._digit), ("3", 3, 2, self._digit),
            ("+", 3, 3, self._op),
            ("±", 4, 0, self._negate), ("0", 4, 1, self._digit), (".", 4, 2, self._dot),
            ("=", 4, 3, self._eval),
        ]
        for text, r, c, handler in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(CALC_BTN)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(handler)
            grid.addWidget(btn, r, c)

        l.addLayout(grid)

    def _digit(self):
        b = self.sender()
        self._expression += b.text()
        self._display.setText(self._expression)

    def _op(self):
        b = self.sender()
        op_map = {"×": "*", "÷": "/", "−": "-"}
        self._expression += op_map.get(b.text(), b.text())
        self._display.setText(self._expression)

    def _dot(self):
        self._expression += "."
        self._display.setText(self._expression)

    def _negate(self):
        if self._expression:
            self._expression = f"-({self._expression})" if self._expression[0] != "-" else self._expression[1:]
            self._display.setText(self._expression)

    def _clear(self):
        self._expression = ""
        self._display.setText("0")

    def _backspace(self):
        self._expression = self._expression[:-1]
        self._display.setText(self._expression or "0")

    def _eval(self):
        try:
            result = eval(self._expression, {"__builtins__": {}})
            if isinstance(result, float):
                result = round(result, 10)
                if result == int(result):
                    result = int(result)
            self._display.setText(str(result))
            self._expression = str(result)
        except Exception:
            QMessageBox.warning(self, "计算错误", "表达式无效")
            self._clear()


class ToolsWindow(QDialog):
    """工具箱 · NEURAL — 导航窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("工具箱 · NEURAL")
        self.setMinimumSize(560, 400)
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
        overlay = QWidget(self)
        overlay.setAttribute(Qt.WA_TranslucentBackground)
        overlay.setGeometry(0, 0, self.minimumWidth(), self.minimumHeight())
        overlay.raise_()

        ol = QVBoxLayout(overlay)
        ol.setSpacing(0)
        ol.setContentsMargins(0, 0, 0, 0)

        ol.addStretch(1)

        # 标题
        title = QLabel("工具箱")
        title.setStyleSheet(
            "color: #ddaaff; font-size: 22px; font-weight: 800; "
            "letter-spacing: 8px; background: transparent;"
        )
        title.setAlignment(Qt.AlignCenter)
        ol.addWidget(title)

        subtitle = QLabel("选择工具模块")
        subtitle.setStyleSheet(
            "color: #776699; font-size: 11px; letter-spacing: 3px; background: transparent;"
        )
        subtitle.setAlignment(Qt.AlignCenter)
        ol.addWidget(subtitle)
        ol.addSpacing(24)

        # ── 按钮卡片区 2×2 网格 ──
        grid = QGridLayout()
        grid.setSpacing(16)
        grid.setAlignment(Qt.AlignCenter)

        tools = [
            ("文本编辑器", 0, 0, self._open_editor),
            ("密码保险箱", 0, 1, self._open_vault),
            ("扫码工具", 1, 0, self._open_scan),
            ("计算器", 1, 1, self._open_calc),
        ]
        for text, r, c, handler in tools:
            btn = QPushButton(text)
            btn.setStyleSheet(CARD_STYLE)
            btn.setFixedSize(160, 80)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(handler)
            grid.addWidget(btn, r, c)

        ol.addLayout(grid)

        ol.addSpacing(16)

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

    def _open_scan(self):
        from modules.intelligence.scan_window import ScanWindow
        dlg = ScanWindow(self)
        dlg.exec_()

    def _open_calc(self):
        dlg = CalcDialog(self)
        dlg.exec_()
