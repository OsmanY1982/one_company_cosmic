"""
OPCclaw - 侧栏导航（含对话列表）
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem, QHBoxLayout, QWidget, QApplication
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QFont

from ._shared import COLORS


class SessionListWidget(QListWidget):
    """QListWidget 子类：点击嵌入按钮时不触发 itemClicked。
    注意：鼠标事件由 viewport 分发，不走 QListWidget.event()；
    此处仅为文档保留，实际拦截逻辑在 _on_session_clicked 中。"""
    pass


class Sidebar(QFrame):
    """左侧导航栏 + 对话列表"""

    nav_changed = pyqtSignal(int)
    session_selected = pyqtSignal(str)   # session_id
    new_chat_requested = pyqtSignal()
    session_delete_requested = pyqtSignal(str)  # session_id
    session_copy_requested = pyqtSignal(str)    # session_id
    session_pin_requested = pyqtSignal(str)     # session_id — 置顶/取消置顶
    session_rename_requested = pyqtSignal(str, str)  # session_id, new_title — 重命名

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
        self.setFixedWidth(200)
        self.setStyleSheet(f"""
            QFrame {{ background: {COLORS['sidebar']}; border: none; }}
        """)
        self._buttons: list[QPushButton] = []
        self._session_items: dict = {}  # session_id → QListWidgetItem
        self._current_session_id = None
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

        # ── 对话列表区域 ──
        # ── 调试横幅 ──
        self._debug_banner = QLabel(" SIDEBAR v2 LOADED [0 sessions]")
        self._debug_banner.setStyleSheet("color: #FF4444; background: #330000; font-size: 10px; padding: 3px 8px;")
        layout.addWidget(self._debug_banner)

        # 标题栏
        session_header = QHBoxLayout()
        session_label = QLabel("  对话列表")
        session_label.setFont(QFont("PingFang SC", 10, QFont.Bold))
        session_label.setStyleSheet(f"color: {COLORS['text_light']}; background: transparent; padding: 8px 0;")
        session_header.addWidget(session_label)

        self._new_chat_btn = QPushButton("+")
        self._new_chat_btn.setToolTip("新建对话")
        self._new_chat_btn.setFixedSize(24, 20)
        self._new_chat_btn.setCursor(Qt.PointingHandCursor)
        self._new_chat_btn.setStyleSheet(f"""
            QPushButton {{
                color: {COLORS['success']};
                background: rgba(39,174,96,0.15);
                border: 1px solid {COLORS['success']};
                border-radius: 3px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {COLORS['success']};
                color: white;
            }}
        """)
        self._new_chat_btn.clicked.connect(self.new_chat_requested.emit)
        session_header.addWidget(self._new_chat_btn)
        session_header.setContentsMargins(8, 0, 8, 0)
        layout.addLayout(session_header)

        # 对话 QListWidget
        self._session_list = SessionListWidget()
        self._session_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                color: {COLORS['text_light']};
                outline: none;
            }}
            QListWidget::item {{
                padding: 6px 12px;
                border: none;
                font-size: 11px;
            }}
            QListWidget::item:hover {{
                background: {COLORS['sidebar_hover']};
                color: white;
            }}
            QListWidget::item:selected {{
                background: {COLORS['sidebar_active']};
                color: white;
            }}
        """)
        self._session_list.itemClicked.connect(self._on_session_clicked)
        layout.addWidget(self._session_list)

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

    # ── 对话列表管理 ──

    def set_sessions(self, sessions: list, current_id: str):
        """从外部推送会话列表，sessions 为 [{'id': str, 'updated_at': str, ...}]"""
        print(f"[SIDEBAR] set_sessions: {len(sessions)} sessions, current={current_id}")
        self._session_list.blockSignals(True)
        # Qt 缺陷：clear() 不自动删除 setItemWidget 设置的 widget，导致泄漏和点击失效
        # 必须先逐个 removeItemWidget，再清空列表
        while self._session_list.count():
            item = self._session_list.takeItem(0)
            if item:
                self._session_list.removeItemWidget(item)
        self._session_items.clear()
        self._current_session_id = current_id
        self._debug_banner.setText(f" SIDEBAR v2 [{len(sessions)} sessions]" if sessions else " SIDEBAR v2 [EMPTY!]")

        for s in sessions:
            sid = s.get("id", "")
            updated = s.get("updated_at", "")[:16].replace("T", " ")
            label = updated if updated else sid

            item = QListWidgetItem()
            item.setData(Qt.UserRole, sid)
            item.setToolTip(sid)

            try:
                widget = self._make_session_item_widget_v2(label, sid, s.get("pinned", False), s.get("title", sid))
            except Exception:
                widget = self._make_session_item_widget(label, sid)
            self._session_list.addItem(item)
            self._session_list.setItemWidget(item, widget)
            self._session_items[sid] = item

            # 让 item 高度适配 widget
            item.setSizeHint(widget.sizeHint())

            if sid == current_id:
                self._session_list.setCurrentItem(item)

        self._session_list.blockSignals(False)

    def _make_session_item_widget(self, label: str, sid: str) -> QWidget:
        """构建单条会话列表项：标签 + 复制 + 删除"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 11px; background: transparent; border: none;")
        layout.addWidget(lbl, 1)

        copy_btn = QPushButton("⧉")
        copy_btn.setFixedSize(20, 18)
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.setToolTip(f"复制会话 {sid}")
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                color: {COLORS['text_light']};
                background: transparent;
                border: none;
                font-size: 12px;
                padding: 0;
            }}
            QPushButton:hover {{
                color: {COLORS['success']};
                background: rgba(39,174,96,0.15);
                border-radius: 3px;
            }}
        """)
        copy_btn.clicked.connect(lambda checked, s=sid: self.session_copy_requested.emit(s))
        layout.addWidget(copy_btn)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(26, 24)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setToolTip(f"删除会话 {sid}")
        del_btn.setStyleSheet(f"""
            QPushButton {{
                color: {COLORS['text_light']};
                background: transparent;
                border: none;
                font-size: 12px;
                padding: 0;
            }}
            QPushButton:hover {{
                color: {COLORS['danger']};
                background: rgba(231,76,60,0.15);
                border-radius: 3px;
            }}
        """)
        del_btn.clicked.connect(lambda checked, s=sid: self.session_delete_requested.emit(s))
        layout.addWidget(del_btn)

        return widget

    def _make_session_item_widget_v2(self, label: str, sid: str, pinned: bool = False, title: str = "") -> QWidget:
        """构建单条会话列表项 v2：置顶 + 标签（双击重命名） + 复制 + 删除"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        # 置顶按钮 — 预先计算样式避免 f-string 内联表达式
        pin_color = "#FFD700" if pinned else COLORS["text_light"]
        pin_bg = "rgba(255,215,0,0.08)" if pinned else "transparent"
        pin_hover_bg = "rgba(255,215,0,0.25)" if pinned else "rgba(255,215,0,0.1)"
        pin_char = "\U0001f4cc" if pinned else "\U0001f4cd"  # 📌 / 📍
        pin_tip = ("取消置顶" if pinned else "置顶") + " " + sid

        pin_btn = QPushButton(pin_char)
        pin_btn.setFixedSize(22, 20)
        pin_btn.setCursor(Qt.PointingHandCursor)
        pin_btn.setToolTip(pin_tip)
        pin_btn.setStyleSheet(
            "QPushButton {"
            "color: %s;"
            "background: %s;"
            "border: none;"
            "font-size: 11px;"
            "padding: 0;"
            "border-radius: 2px;"
            "}"
            "QPushButton:hover {"
            "background: %s;"
            "}" % (pin_color, pin_bg, pin_hover_bg)
        )
        pin_btn.clicked.connect(lambda checked, s=sid: self.session_pin_requested.emit(s))
        layout.addWidget(pin_btn)

        # 标签（可双击重命名）
        lbl = QLabel(label)
        lbl.setToolTip("双击重命名 | " + sid)
        lbl.setStyleSheet(
            "color: %s; font-size: 11px; background: transparent; border: none;" % COLORS["text_light"]
        )
        lbl.installEventFilter(self)
        lbl.setProperty("session_id", sid)
        lbl.setProperty("session_title", title)
        layout.addWidget(lbl, 1)

        # 复制按钮
        copy_btn = QPushButton("\u29c9")  # ⧉
        copy_btn.setFixedSize(20, 18)
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.setToolTip("复制会话 " + sid)
        copy_btn.setStyleSheet(
            "QPushButton {"
            "color: %s;"
            "background: transparent;"
            "border: none;"
            "font-size: 12px;"
            "padding: 0;"
            "}"
            "QPushButton:hover {"
            "color: %s;"
            "background: rgba(39,174,96,0.15);"
            "border-radius: 3px;"
            "}" % (COLORS["text_light"], COLORS["success"])
        )
        copy_btn.clicked.connect(lambda checked, s=sid: self.session_copy_requested.emit(s))
        layout.addWidget(copy_btn)

        # 删除按钮
        del_btn = QPushButton("\u2715")  # ✕
        del_btn.setFixedSize(26, 24)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setToolTip("删除会话 " + sid)
        del_btn.setStyleSheet(
            "QPushButton {"
            "color: %s;"
            "background: transparent;"
            "border: none;"
            "font-size: 12px;"
            "padding: 0;"
            "}"
            "QPushButton:hover {"
            "color: %s;"
            "background: rgba(231,76,60,0.15);"
            "border-radius: 3px;"
            "}" % (COLORS["text_light"], COLORS["danger"])
        )
        del_btn.clicked.connect(lambda checked, s=sid: self.session_delete_requested.emit(s))
        layout.addWidget(del_btn)

        return widget

    def eventFilter(self, obj, event):
        """拦截 QLabel 双击事件 → 触发重命名"""
        from PyQt5.QtCore import QEvent
        if event.type() == QEvent.MouseButtonDblClick and isinstance(obj, QLabel):
            sid = obj.property("session_id")
            if sid:
                self.session_rename_requested.emit(sid, obj.property("session_title") or sid)
                return True
        return super().eventFilter(obj, event)

    def _on_session_clicked(self, item):
        # 如果点击落在按钮上（删除/复制），不触发会话切换
        # QListWidget 的 itemClicked 在按钮 clicked 之前先触发，
        # 此检查可防止 itemClicked 触发 _switch_to_session 干扰按钮事件
        widget_under = QApplication.widgetAt(QCursor.pos())
        if isinstance(widget_under, QPushButton):
            return
        sid = item.data(Qt.UserRole)
        if sid and sid != self._current_session_id:
            self.session_selected.emit(sid)

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
