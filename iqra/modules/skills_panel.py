"""
Iqra - 技能管理面板
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ._shared import COLORS, _styled_btn


class SkillsPanel(QWidget):
    """浏览、启用/禁用技能"""

    skills_changed = pyqtSignal()

    def __init__(self, config, skill_loader, parent=None):
        super().__init__(parent)
        self.config = config
        self.skill_loader = skill_loader
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("📚 技能管理")
        title.setFont(QFont("PingFang SC", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text']};")
        layout.addWidget(title)

        desc = QLabel("管理 Iqra 的技能模块。技能是 AI Agent 的\"灵魂\", 定义了何时使用什么工具。")
        desc.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 刷新按钮
        refresh_btn = _styled_btn("🔄 重新加载技能", COLORS["primary"])
        refresh_btn.clicked.connect(lambda: (self.skill_loader.list_skills(), self._refresh(), self.skills_changed.emit()))
        layout.addWidget(refresh_btn)

        # 技能列表
        self.skill_list = QListWidget()
        self.skill_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                background: {COLORS['card']};
                font-size: 13px;
            }}
            QListWidget::item {{ padding: 10px 14px; border-bottom: 1px solid {COLORS['border']}; }}
        """)
        layout.addWidget(self.skill_list, stretch=1)

        # 操作按钮
        btn_row = QHBoxLayout()
        self.toggle_btn = _styled_btn("启用/禁用", COLORS["warning"])
        self.toggle_btn.clicked.connect(self._toggle_selected)
        btn_row.addWidget(self.toggle_btn)

        view_btn = _styled_btn("查看详情", COLORS["primary"])
        view_btn.clicked.connect(self._view_selected)
        btn_row.addWidget(view_btn)
        btn_row.addStretch()

        layout.addLayout(btn_row)

        # 统计
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        layout.addWidget(self.stats_label)

        self._refresh()

    def _refresh(self):
        self.skill_list.clear()
        try:
            skills = self.skill_loader.list_skills()
        except Exception:
            self.stats_label.setText("技能系统未初始化")
            return
        for skill in skills:
            name = skill['name']
            disabled = self.config.is_skill_disabled(name)
            status_icon = "🚫" if disabled else "✅"
            item = QListWidgetItem(
                f"{status_icon}  {skill['emoji']}  {skill['name']}  |  {skill['description'][:50]}"
            )
            item.setData(Qt.UserRole, name)
            self.skill_list.addItem(item)

        enabled = sum(1 for s in skills if not self.config.is_skill_disabled(s['name']))
        self.stats_label.setText(
            f"共 {len(skills)} 个技能, {enabled} 个已启用, "
            f"{len(skills) - enabled} 个已禁用"
        )

    def _toggle_selected(self):
        item = self.skill_list.currentItem()
        if not item:
            return
        name = item.data(Qt.UserRole)
        current = self.config.is_skill_disabled(name)
        self.config.toggle_skill(name, not current)
        self._refresh()
        self.skills_changed.emit()

    def _view_selected(self):
        item = self.skill_list.currentItem()
        if not item:
            return
        name = item.data(Qt.UserRole)
        skill = self.skill_loader.get_skill(name)
        if not skill:
            return
        detail = (
            f"名称: {skill['name']}\n"
            f"描述: {skill['description']}\n"
            f"版本: {skill['version']}\n"
            f"emoji: {skill['emoji']}\n"
            f"路径: {skill['path']}\n\n"
            f"指令体 (前500字):\n{skill['body'][:500]}..."
        )
        QMessageBox.information(self, f"技能: {name}", detail)


