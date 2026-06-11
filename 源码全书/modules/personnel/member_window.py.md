# `modules/personnel/member_window.py`

> 路径：`modules/personnel/member_window.py` | 行数：440


---


```python
"""
会员管理 · CREW
独立的 QDialog 子窗口，暖橙主题
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QFormLayout,
    QLineEdit, QComboBox, QTextEdit, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from modules.personnel.personnel_window import (
    member_get_all, member_add, member_update, member_delete, member_stats
)
from modules.auth.auth_service import AuthService

# ═══════ 暖橙 QSS ═══════
BTN_PRIMARY = """
    QPushButton {
        background: rgba(255,100,60,40);
        color: #ffccaa;
        border: 1px solid rgba(255,120,70,60);
        border-radius: 16px; padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(255,120,70,70); }
"""
BTN_DANGER = """
    QPushButton {
        background: rgba(200,60,40,40);
        color: #ffaaaa;
        border: 1px solid rgba(200,80,50,60);
        border-radius: 16px; padding: 6px 18px; font-size: 11px;
    }
    QPushButton:hover { background: rgba(220,80,50,70); }
"""
TABLE_STYLE = """
    QTableWidget {
        background: rgba(15,8,5,220);
        color: #ddbbaa;
        border: 1px solid rgba(180,80,50,30);
        border-radius: 8px; gridline-color: rgba(80,40,20,25);
        font-size: 12px; selection-background-color: rgba(255,100,60,60);
    }
    QTableWidget::item { padding: 5px 10px; }
    QHeaderView::section {
        background: rgba(25,12,8,230);
        color: #bb9988; padding: 8px 10px; border: none;
        border-bottom: 1px solid rgba(255,100,60,40);
        font-weight: 700; font-size: 11px; letter-spacing: 1px;
    }
"""
CARD_STYLE = """
    background: rgba(20,10,6,230);
    border: 1px solid rgba(255,100,60,35);
    border-radius: 10px;
    padding: 10px;
    min-width: 130px;
"""


# ═══════════════ 会员表单对话框 ═══════════════
class MemberDialog(QDialog):
    def __init__(self, parent=None, row=None):
        super().__init__(parent)
        self.row = row
        self.setWindowTitle("编辑会员" if row else "添加会员")
        self.setMinimumWidth(440)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0e0604, stop:1 #1a0d08);
                border: 1px solid rgba(255,100,60,45); border-radius: 12px;
            }
            QLabel { color: #ccaa99; font-size: 12px; background: transparent; }
            QLineEdit, QComboBox, QTextEdit {
                background: rgba(15,8,5,230); color: #ddbbaa;
                border: 1px solid rgba(255,120,60,35); border-radius: 6px;
                padding: 7px 10px; font-size: 12px;
            }
        """)
        layout = QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 20)

        self.edit_name = QLineEdit()
        self.edit_name.setText(row['name'] if row else '')
        self.edit_phone = QLineEdit()
        self.edit_phone.setText(row['phone'] if row else '')
        self.edit_email = QLineEdit()
        self.edit_email.setText(row['email'] if row else '')
        self.edit_level = QComboBox()
        self.edit_level.addItems(['体验', 'VIP', '永久'])
        if row:
            self.edit_level.setCurrentText(row['level'])
        self.edit_points = QLineEdit()
        self.edit_points.setText(str(row['points']) if row else '0')
        self.edit_rights = QTextEdit()
        self.edit_rights.setMaximumHeight(60)
        if row:
            self.edit_rights.setText(row['rights'] or '')
        self.edit_vip_expire = QLineEdit()
        self.edit_vip_expire.setText(row['vip_expire'] if row else '')
        self.edit_status = QComboBox()
        self.edit_status.addItems(['正常', '冻结', '过期'])
        if row:
            self.edit_status.setCurrentText(row['status'])

        layout.addRow("姓名:", self.edit_name)
        layout.addRow("电话:", self.edit_phone)
        layout.addRow("邮箱:", self.edit_email)
        layout.addRow("等级:", self.edit_level)
        layout.addRow("积分:", self.edit_points)
        layout.addRow("权益:", self.edit_rights)
        layout.addRow("VIP到期:", self.edit_vip_expire)
        layout.addRow("状态:", self.edit_status)

        btn_row = QHBoxLayout()
        save = QPushButton("保存")
        save.clicked.connect(self.accept)
        cancel = QPushButton("取消")
        cancel.clicked.connect(self.reject)
        save.setStyleSheet(BTN_PRIMARY)
        cancel.setStyleSheet(BTN_DANGER)
        btn_row.addStretch()
        btn_row.addWidget(save)
        btn_row.addWidget(cancel)
        layout.addRow(btn_row)

    def get_data(self):
        return {
            "name": self.edit_name.text().strip(),
            "phone": self.edit_phone.text().strip(),
            "email": self.edit_email.text().strip(),
            "level": self.edit_level.currentText(),
            "points": int(self.edit_points.text() or 0),
            "rights": self.edit_rights.toPlainText().strip(),
            "vip_expire": self.edit_vip_expire.text().strip(),
            "status": self.edit_status.currentText(),
        }


# ═══════════════ 管理员升级对话框 ═══════════════
class AdminUpgradeDialog(QDialog):
    """管理员直接升级会员（无需激活码）"""

    def __init__(self, username, current_membership, current_expire, parent=None):
        super().__init__(parent)
        self._username = username
        self._auth = AuthService()

        self.setWindowTitle(f"升级会员 — {username}")
        self.setFixedSize(400, 220)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a0402, stop:1 #140a06);
                border: 1px solid rgba(255,100,60,45); border-radius: 12px;
            }
            QLabel { color: #ccaa99; font-size: 12px; background: transparent; }
            QComboBox {
                background: rgba(15,8,5,230); color: #ddbbaa;
                border: 1px solid rgba(255,120,60,35); border-radius: 6px;
                padding: 7px 10px; font-size: 12px;
            }
            QComboBox QAbstractItemView {
                background: #140a06; color: #ddbbaa;
                selection-background-color: rgba(255,100,60,60);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 20)

        # 当前状态
        info_label = QLabel(f"当前等级：{current_membership}　|　到期：{current_expire or '永久'}")
        info_label.setStyleSheet("color: #ffccaa; font-size: 13px; font-weight: 600;")
        layout.addWidget(info_label)

        # 目标等级
        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("目标等级："))
        self._level_combo = QComboBox()
        self._level_combo.addItems(["VIP", "永久"])
        target_row.addWidget(self._level_combo, 1)
        layout.addLayout(target_row)

        layout.addStretch()

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(200,60,40,40); color: #ffaaaa;
                border: 1px solid rgba(200,80,50,60); border-radius: 16px;
                padding: 6px 18px; font-size: 11px;
            }
            QPushButton:hover { background: rgba(220,80,50,70); }
        """)
        btn_row.addWidget(cancel_btn)

        confirm_btn = QPushButton("确认升级")
        confirm_btn.clicked.connect(self._do_upgrade)
        confirm_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,100,60,40); color: #ffccaa;
                border: 1px solid rgba(255,120,70,60); border-radius: 16px;
                padding: 6px 18px; font-size: 11px; font-weight: 600;
            }
            QPushButton:hover { background: rgba(255,120,70,70); }
        """)
        btn_row.addWidget(confirm_btn)
        layout.addLayout(btn_row)

    def _do_upgrade(self):
        target = self._level_combo.currentText()
        target_key = "vip" if target == "VIP" else "permanent"
        ok, msg = self._auth.upgrade_membership(self._username, target_key)
        if ok:
            QMessageBox.information(self, "升级成功", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "升级失败", msg)


# ═══════════════ 会员管理主窗口 ═══════════════
class MemberWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("会员管理 · CREW")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a0402, stop:1 #140a06);
            }
        """)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 16, 20, 16)

        # 标题
        title = QLabel("会员管理 · CREW")
        title.setStyleSheet(
            "color: #ffccaa; font-size: 20px; font-weight: 800; "
            "letter-spacing: 4px; background: transparent; padding: 8px 0;"
        )
        layout.addWidget(title, alignment=Qt.AlignCenter)

        # 辉光线
        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(255,100,60,50),
                stop:0.5 rgba(255,140,80,120),
                stop:0.7 rgba(255,100,60,50), stop:1 transparent);
            border: none;
        """)
        layout.addWidget(line)

        # 统计卡片行
        cards_layout = QHBoxLayout()
        self.card_total = self._make_card("总会员")
        self.card_vip = self._make_card("VIP / 永久")
        self.card_normal = self._make_card("体验会员")
        cards_layout.addWidget(self.card_total)
        cards_layout.addWidget(self.card_vip)
        cards_layout.addWidget(self.card_normal)
        cards_layout.addStretch()
        layout.addLayout(cards_layout)

        # 搜索 + 等级筛选 + 添加按钮
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("搜索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("姓名 / 电话")
        self.search_input.setMaximumWidth(180)
        self.search_input.setStyleSheet(
            "background: rgba(15,8,5,230); color: #ddbbaa; "
            "border: 1px solid rgba(255,120,60,35); border-radius: 6px; "
            "padding: 6px 10px; font-size: 12px;"
        )
        self.search_input.textChanged.connect(self._load)
        toolbar.addWidget(self.search_input)

        toolbar.addWidget(QLabel("等级:"))
        self.level_filter = QComboBox()
        self.level_filter.addItems(['全部', '体验', 'VIP', '永久'])
        self.level_filter.setStyleSheet(
            "background: rgba(15,8,5,230); color: #ddbbaa; "
            "border: 1px solid rgba(255,120,60,35); border-radius: 6px; "
            "padding: 6px 10px; font-size: 12px;"
        )
        self.level_filter.currentTextChanged.connect(self._load)
        toolbar.addWidget(self.level_filter)
        toolbar.addStretch()

        btn_upgrade = QPushButton("升级")
        btn_upgrade.setStyleSheet("""
            QPushButton {
                background: rgba(255,180,45,40); color: #ffdd88;
                border: 1px solid rgba(255,200,60,60); border-radius: 16px;
                padding: 6px 18px; font-size: 11px; font-weight: 600;
            }
            QPushButton:hover { background: rgba(255,200,60,70); }
        """)
        btn_upgrade.clicked.connect(self._upgrade)
        toolbar.addWidget(btn_upgrade)

        btn_add = QPushButton("+ 添加会员")
        btn_add.setStyleSheet(BTN_PRIMARY)
        btn_add.clicked.connect(self._add)
        toolbar.addWidget(btn_add)
        layout.addLayout(toolbar)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            ["ID", "姓名", "电话", "邮箱", "等级", "积分", "权益", "VIP到期", "状态"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

        # 操作按钮
        act_row = QHBoxLayout()
        btn_edit = QPushButton("编辑")
        btn_edit.setStyleSheet(BTN_PRIMARY)
        btn_edit.clicked.connect(self._edit)
        btn_del = QPushButton("删除")
        btn_del.setStyleSheet(BTN_DANGER)
        btn_del.clicked.connect(self._delete)
        act_row.addStretch()
        act_row.addWidget(btn_edit)
        act_row.addWidget(btn_del)
        layout.addLayout(act_row)

    def _make_card(self, label_text):
        card = QFrame()
        card.setStyleSheet(CARD_STYLE)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label_text)
        lbl.setStyleSheet(
            "color: #aa8877; font-size: 11px; background: transparent;"
        )
        value = QLabel("0")
        value.setStyleSheet(
            "color: #ffccaa; font-size: 22px; font-weight: 700; background: transparent;"
        )
        value.setObjectName("card_value")
        cl.addWidget(lbl)
        cl.addWidget(value)
        return card

    # ═══════════ 业务逻辑 ═══════════
    def _load(self):
        search = self.search_input.text().strip()
        level = self.level_filter.currentText()
        if level == '全部':
            level = ""
        rows = member_get_all(search, level)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, k in enumerate([
                'id', 'name', 'phone', 'email', 'level', 'points',
                'rights', 'vip_expire', 'status'
            ]):
                val = r[k] if r[k] is not None else ""
                self.table.setItem(i, j, QTableWidgetItem(str(val)))

        # 更新统计
        stats = member_stats()
        self.card_total.findChild(QLabel, "card_value").setText(str(stats['total']))
        vip_cnt = stats['levels'].get('VIP', 0) + stats['levels'].get('永久', 0)
        self.card_vip.findChild(QLabel, "card_value").setText(str(vip_cnt))
        self.card_normal.findChild(QLabel, "card_value").setText(
            str(stats['levels'].get('体验', 0))
        )

    def _add(self):
        dlg = MemberDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            member_add(**dlg.get_data())
            self._load()

    def _edit(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "提示", "请先选中一行")
        mid = int(self.table.item(row, 0).text())
        rows = member_get_all()
        target = next((r for r in rows if r['id'] == mid), None)
        if not target:
            return
        dlg = MemberDialog(self, target)
        if dlg.exec_() == QDialog.Accepted:
            member_update(mid, **dlg.get_data())
            self._load()

    def _delete(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "提示", "请先选中一行")
        mid = int(self.table.item(row, 0).text())
        if QMessageBox.Yes == QMessageBox.question(
            self, "确认", f"确定删除会员 #{mid} 吗？"
        ):
            member_delete(mid)
            self._load()

    def _upgrade(self):
        """管理员升级会员等级"""
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "提示", "请先选中一行")

        name = self.table.item(row, 1).text().strip()  # 姓名列
        level = self.table.item(row, 4).text().strip()  # 等级列
        expire = self.table.item(row, 7).text().strip() if self.table.item(row, 7) else ""  # VIP到期列

        # 映射 personnel level → auth membership
        level_map = {"体验": "trial", "VIP": "vip", "永久": "permanent"}
        current_membership = level_map.get(level, "trial")

        dlg = AdminUpgradeDialog(name, current_membership, expire, self)
        if dlg.exec_() == QDialog.Accepted:
            self._load()
```
