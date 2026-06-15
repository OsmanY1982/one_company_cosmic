"""
ChatSessionManager — AI对话 · 会话列表管理面板（左侧边栏）
用于 AIChatWindow 左侧，展示所有历史会话并提供切换/搜索/删除/导出能力。
"""
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QLineEdit, QLabel, QMenu,
    QMessageBox, QFileDialog,
)
from PyQt5.QtCore import pyqtSignal, Qt


class ChatSessionManager(QWidget):
    """AI对话 — 会话列表管理面板（左侧边栏）"""

    session_selected = pyqtSignal(str, str)     # session_id, title
    session_deleted = pyqtSignal(str)            # session_id（通知外部）
    new_chat_requested = pyqtSignal()            # 请求新建会话
    session_copy_requested = pyqtSignal(str)     # session_id（请求复制会话）

    def __init__(self, agent_bridge, parent=None):
        super().__init__(parent)
        self._agent = agent_bridge
        self._sessions = []
        self.setFixedWidth(240)
        self.setStyleSheet("""
            ChatSessionManager {
                background-color: #1a1a2e;
                border-right: 1px solid #2a2a4a;
            }
            QLabel#section_title {
                color: #8888aa;
                font-size: 11px;
                font-weight: bold;
                padding: 4px 8px;
                text-transform: uppercase;
            }
            QPushButton#new_chat_btn {
                background-color: #3a3a6e;
                color: #e0e0ff;
                border: 1px solid #5a5a8e;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton#new_chat_btn:hover {
                background-color: #4a4a8e;
                border-color: #7a7aae;
            }
            QLineEdit#search_box {
                background-color: #12122a;
                color: #ccccdd;
                border: 1px solid #2a2a4a;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QListWidget#session_list {
                background-color: transparent;
                border: none;
                outline: none;
                color: #ccccdd;
                font-size: 12px;
            }
            QListWidget#session_list::item {
                padding: 8px 10px;
                border-bottom: 1px solid #1f1f3a;
            }
            QListWidget#session_list::item:hover {
                background-color: #252545;
            }
            QListWidget#session_list::item:selected {
                background-color: #2a2a5a;
                border-left: 2px solid #6a6aff;
            }
        """)
        self._init_ui()
        self._load_sessions()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题栏
        header = QHBoxLayout()
        header.setContentsMargins(10, 10, 10, 6)
        title_label = QLabel("对话历史")
        title_label.setObjectName("section_title")
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)

        # 新建按钮
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(10, 0, 10, 8)
        new_btn = QPushButton("+ 新建对话")
        new_btn.setObjectName("new_chat_btn")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.clicked.connect(self._on_new_chat)
        btn_layout.addWidget(new_btn)
        layout.addLayout(btn_layout)

        # 搜索框
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(10, 0, 10, 8)
        self._search_box = QLineEdit()
        self._search_box.setObjectName("search_box")
        self._search_box.setPlaceholderText("搜索对话...")
        self._search_box.textChanged.connect(self._on_search)
        search_layout.addWidget(self._search_box)
        layout.addLayout(search_layout)

        # 会话列表
        self._list_widget = QListWidget()
        self._list_widget.setObjectName("session_list")
        self._list_widget.itemClicked.connect(self._on_item_clicked)
        self._list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list_widget.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self._list_widget, 1)

        # 底部信息
        bottom = QHBoxLayout()
        bottom.setContentsMargins(10, 6, 10, 8)
        self._count_label = QLabel("")
        self._count_label.setStyleSheet("color: #666688; font-size: 10px;")
        bottom.addWidget(self._count_label)
        layout.addLayout(bottom)

    def _load_sessions(self):
        """从 agent_bridge 加载所有会话列表"""
        try:
            sessions = self._agent.list_sessions()
            self._sessions = sorted(
                sessions,
                key=lambda x: x.get("updated_at", ""),
                reverse=True,
            )
            self._refresh_list()
        except Exception as e:
            print(f"[ChatSessionManager] 加载会话列表失败: {e}")
            self._sessions = []

    def _refresh_list(self, filter_text: str = ""):
        """刷新列表显示"""
        self._list_widget.clear()
        filtered = self._sessions
        if filter_text:
            ft = filter_text.lower()
            filtered = [
                s for s in self._sessions
                if ft in s.get("title", "").lower()
            ]

        for s in filtered:
            sid = s.get("session_id", "")
            title = s.get("title", "未命名对话")[:30]
            msg_count = s.get("message_count", 0)
            updated = s.get("updated_at", "")
            try:
                dt = datetime.fromisoformat(updated)
                if dt.date() == datetime.now().date():
                    time_str = dt.strftime("今天 %H:%M")
                else:
                    time_str = dt.strftime("%m-%d %H:%M")
            except Exception:
                time_str = ""

            # 自定义行控件: 标题 + 信息 + 操作按钮
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 4, 4, 4)
            row_layout.setSpacing(4)

            # 左侧文本区域
            text_widget = QWidget()
            text_layout = QVBoxLayout(text_widget)
            text_layout.setContentsMargins(0, 0, 0, 0)
            text_layout.setSpacing(1)

            title_lbl = QLabel(title)
            title_lbl.setStyleSheet("color: #ccccdd; font-size: 12px; font-weight: bold; background: transparent;")
            title_lbl.setCursor(Qt.PointingHandCursor)
            title_lbl.mousePressEvent = lambda e, sid=sid, t=title: self._select_session(sid, t)
            text_layout.addWidget(title_lbl)

            info_lbl = QLabel(f"{msg_count}条消息 · {time_str}")
            info_lbl.setStyleSheet("color: #666688; font-size: 10px; background: transparent;")
            text_layout.addWidget(info_lbl)

            row_layout.addWidget(text_widget, 1)

            # ⧉ 复制按钮
            copy_btn = QPushButton("⧉")
            copy_btn.setFixedSize(20, 18)
            copy_btn.setCursor(Qt.PointingHandCursor)
            copy_btn.setToolTip(f"复制会话 {sid}")
            copy_btn.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #666688; border: none;
                    border-radius: 2px; font-size: 11px;
                }
                QPushButton:hover { background: rgba(100,180,255,30); color: #88aaff; }
            """)
            copy_btn.clicked.connect(lambda checked, ses=sid: self.session_copy_requested.emit(ses))
            row_layout.addWidget(copy_btn)

            # ✕ 删除按钮
            del_btn = QPushButton("✕")
            del_btn.setFixedSize(18, 18)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setToolTip(f"删除会话 {sid}")
            del_btn.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #664444; border: none;
                    border-radius: 2px; font-size: 11px;
                }
                QPushButton:hover { background: rgba(255,100,100,30); color: #ff6666; }
            """)
            del_btn.clicked.connect(lambda checked, ses=sid: self._delete_session(ses))
            row_layout.addWidget(del_btn)

            item = QListWidgetItem()
            item.setData(Qt.UserRole, sid)
            item.setSizeHint(row.sizeHint())
            self._list_widget.addItem(item)
            self._list_widget.setItemWidget(item, row)

        self._count_label.setText(f"共 {len(filtered)} 个会话")

    def _on_search(self, text: str):
        self._refresh_list(text)

    def _on_item_clicked(self, item: QListWidgetItem):
        session_id = item.data(Qt.UserRole)
        title = "对话"
        for s in self._sessions:
            if s.get("session_id") == session_id:
                title = s.get("title", "对话")
                break
        self.session_selected.emit(session_id, title)

    def _on_new_chat(self):
        self.new_chat_requested.emit()

    def _select_session(self, session_id: str, title: str):
        """选中会话（从自定义 item widget 触发）"""
        self.session_selected.emit(session_id, title)

    def _delete_session(self, session_id: str):
        """删除会话（从删除按钮触发）"""
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这个会话吗？\n删除后不可恢复。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                self._agent._memory.delete_session(session_id)
            except Exception as e:
                print(f"[ChatSessionManager] 删除会话失败: {e}")
            self._load_sessions()
            self.session_deleted.emit(session_id)

    def _show_context_menu(self, pos):
        item = self._list_widget.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e3a;
                color: #ccccdd;
                border: 1px solid #2a2a4a;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #2a2a5a;
            }
        """)

        export_action = menu.addAction("导出会话")

        action = menu.exec_(self._list_widget.mapToGlobal(pos))
        session_id = item.data(Qt.UserRole)

        if action == export_action:
            try:
                default_name = f"chat_{session_id}"
                path, selected_filter = QFileDialog.getSaveFileName(
                    self, "导出会话",
                    default_name,
                    "JSON文件 (*.json);;Markdown文件 (*.md)",
                )
                if not path:
                    return

                # 读取会话数据
                msgs = self._agent.load_session(session_id)
                # 查找会话元信息
                info = None
                for s in self._sessions:
                    if s.get("session_id") == session_id:
                        info = s
                        break

                if path.endswith(".md"):
                    # 导出为 Markdown
                    lines = [
                        f"# {info.get('title', session_id) if info else session_id}\n",
                        f"*Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
                        "---\n",
                    ]
                    for msg in msgs:
                        role = msg.get("role", "unknown").upper()
                        content = msg.get("content", "")
                        if isinstance(content, str):
                            lines.append(f"\n### {role}\n")
                            lines.append(content)
                            lines.append("")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write("\n".join(lines))
                else:
                    # 导出为 JSON
                    import json
                    data = {
                        "session_id": session_id,
                        "title": info.get("title", "Untitled") if info else "Untitled",
                        "exported_at": datetime.now().isoformat(),
                        "messages": msgs,
                    }
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                QMessageBox.information(self, "导出成功", f"已导出到:\n{path}")
            except Exception as e:
                QMessageBox.warning(self, "导出失败", str(e))
