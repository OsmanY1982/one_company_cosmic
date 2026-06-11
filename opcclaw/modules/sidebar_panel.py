"""
OPCclaw - 侧栏导航
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ._shared import COLORS


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
