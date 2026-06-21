# `iqra/modules/general_settings_panel.py`

> 路径：`iqra/modules/general_settings_panel.py` | 行数：230


---


```python
"""
Iqra - 通用设置面板
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QCheckBox, QSpinBox, QGroupBox, QMessageBox, QPushButton,
    QDialog, QLineEdit,
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont

from ._shared import COLORS, _styled_btn
from iqra.core.secure_storage import SecureStorage


class GeneralSettingsPanel(QWidget):
    """通用设置: 主题/自动保存/数据清除"""

    settings_changed = pyqtSignal()

    def __init__(self, config, memory_store, parent=None):
        super().__init__(parent)
        self.config = config
        self.memory_store = memory_store
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("⚙️ 通用设置")
        title.setFont(QFont("PingFang SC", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text']};")
        layout.addWidget(title)

        # ── 对话设置 ──
        chat_group = QGroupBox("对话设置")
        chat_form = QFormLayout(chat_group)

        self.auto_save_cb = QCheckBox("自动保存对话历史")
        self.auto_save_cb.setChecked(self.config.get_general("auto_save", True))
        self.auto_save_cb.stateChanged.connect(
            lambda: self._update_general("auto_save", self.auto_save_cb.isChecked())
        )
        chat_form.addRow(self.auto_save_cb)

        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("字体大小:"))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(10, 24)
        self.font_spin.setValue(self.config.get_general("font_size", 14))
        self.font_spin.valueChanged.connect(lambda v: self._update_general("font_size", v))
        font_layout.addWidget(self.font_spin)
        font_layout.addStretch()
        chat_form.addRow(font_layout)

        tool_layout = QHBoxLayout()
        tool_layout.addWidget(QLabel("最大工具调用轮次:"))
        self.tool_spin = QSpinBox()
        self.tool_spin.setRange(1, 20)
        self.tool_spin.setValue(self.config.get_general("max_tool_rounds", 5))
        self.tool_spin.valueChanged.connect(lambda v: self._update_general("max_tool_rounds", v))
        tool_layout.addWidget(self.tool_spin)
        tool_layout.addStretch()
        chat_form.addRow(tool_layout)
        layout.addWidget(chat_group)

        # ── 数据管理 ──
        data_group = QGroupBox("数据管理")
        data_form = QFormLayout(data_group)

        clear_chat_btn = _styled_btn("清除所有对话历史", COLORS["warning"])
        clear_chat_btn.clicked.connect(self._clear_all_sessions)
        data_form.addRow("对话数据:", clear_chat_btn)

        clear_memory_btn = _styled_btn("清除长期记忆", COLORS["danger"])
        clear_memory_btn.clicked.connect(self._clear_memories)
        data_form.addRow("记忆数据:", clear_memory_btn)

        reset_btn = _styled_btn("恢复出厂设置", COLORS["danger"])
        reset_btn.clicked.connect(self._reset_all)
        data_form.addRow("全部重置:", reset_btn)
        layout.addWidget(data_group)

        # ── 会话统计 ──
        info_group = QGroupBox("系统信息")
        info_form = QFormLayout(info_group)
        if self.memory_store is not None:
            sessions = self.memory_store.list_sessions()
            memories = self.memory_store.list_memories()
            info_form.addRow("对话会话:", QLabel(f"{len(sessions)} 个"))
            info_form.addRow("记忆条目:", QLabel(f"{len(memories)} 条"))
            info_form.addRow("数据目录:", QLabel(self.memory_store.base_dir))
        else:
            info_form.addRow("状态:", QLabel("记忆存储未连接"))
        layout.addWidget(info_group)

        layout.addStretch()

    def _update_general(self, key: str, value):
        self.config.set_general(key, value)
        self.settings_changed.emit()

    def _clear_all_sessions(self):
        if self.memory_store is None:
            QMessageBox.warning(self, "不可用", "记忆存储未连接")
            return
        reply = QMessageBox.question(
            self, "确认", "确定要清除所有对话历史吗？此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for s in self.memory_store.list_sessions():
                self.memory_store.delete_session(s["id"])
            QMessageBox.information(self, "完成", "所有对话历史已清除")

    def _clear_memories(self):
        if self.memory_store is None:
            QMessageBox.warning(self, "不可用", "记忆存储未连接")
            return
        reply = QMessageBox.question(
            self, "确认", "确定要清除所有长期记忆吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for m in self.memory_store.list_memories():
                self.memory_store.write_memory(m, "")
            QMessageBox.information(self, "完成", "所有记忆已清除")

    def _reset_all(self):
        if self.memory_store is None:
            QMessageBox.warning(self, "不可用", "记忆存储未连接")
            return
        reply = QMessageBox.question(
            self, "⚠️ 最终确认",
            "确定要恢复出厂设置吗？\n\n这将清除:\n"
            "- 所有 LLM 供应商配置\n"
            "- 所有对话历史\n"
            "- 所有长期记忆\n"
            "- 所有自定义设置\n\n此操作不可恢复!",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.config._data = self.config._load_defaults()
            self.config.save()
            for s in self.memory_store.list_sessions():
                self.memory_store.delete_session(s["id"])
            for m in self.memory_store.list_memories():
                self.memory_store.write_memory(m, "")
            QMessageBox.information(self, "完成", "已恢复出厂设置。请重新配置 LLM 供应商。")
            self.settings_changed.emit()

    def _show_change_admin_password(self):
        """显示修改管理员密码对话框"""
        dlg = QDialog(self)
        dlg.setWindowTitle("修改管理员密码")
        dlg.setFixedSize(400, 280)
        dlg.setModal(True)

        layout2 = QVBoxLayout(dlg)
        layout2.setContentsMargins(24, 20, 24, 20)
        layout2.setSpacing(14)

        info = QLabel("修改管理员密码：")
        info.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout2.addWidget(info)

        old_pwd = QLineEdit()
        old_pwd.setPlaceholderText("输入旧密码")
        old_pwd.setEchoMode(QLineEdit.Password)
        old_pwd.setMinimumHeight(38)
        layout2.addWidget(old_pwd)

        new_pwd1 = QLineEdit()
        new_pwd1.setPlaceholderText("输入新密码（至少6位）")
        new_pwd1.setEchoMode(QLineEdit.Password)
        new_pwd1.setMinimumHeight(38)
        layout2.addWidget(new_pwd1)

        new_pwd2 = QLineEdit()
        new_pwd2.setPlaceholderText("再次输入新密码")
        new_pwd2.setEchoMode(QLineEdit.Password)
        new_pwd2.setMinimumHeight(38)
        layout2.addWidget(new_pwd2)

        btn = QPushButton("确认修改")
        btn.setMinimumHeight(38)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }}
            QPushButton:hover {{ background: {COLORS['primary_hover']}; }}
        """)

        def do_change():
            old = old_pwd.text().strip()
            n1 = new_pwd1.text().strip()
            n2 = new_pwd2.text().strip()

            storage = SecureStorage()
            stored = storage.get_admin_password()

            if old != stored:
                QMessageBox.warning(dlg, "错误", "旧密码不正确")
                return

            if len(n1) < 6:
                QMessageBox.warning(dlg, "错误", "新密码至少6位")
                return

            if n1 != n2:
                QMessageBox.warning(dlg, "错误", "两次新密码不一致")
                return

            if storage.set_admin_password(n1):
                QMessageBox.information(dlg, "成功", "密码修改成功")
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "错误", "密码保存失败")

        btn.clicked.connect(do_change)
        layout2.addWidget(btn)

        dlg.exec_()

```
