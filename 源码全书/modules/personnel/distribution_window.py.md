# `modules/personnel/distribution_window.py`

> 路径：`modules/personnel/distribution_window.py` | 行数：373


---


```python
"""
分销管理 · CREW
独立的 QDialog 子窗口，金色渐变主题
对接 personnel_window DAO 层（distribution.db）
"""
import traceback
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QComboBox,
    QDoubleSpinBox, QLineEdit, QFormLayout, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QPainter, QColor, QLinearGradient, QPen,
    QBrush, QFont, QPainterPath
)

from modules.personnel.personnel_window import (
    dist_get_links, dist_get_commissions, dist_get_team,
)

# ═══════ 金色 QSS ═══════
BTN_GOLD = """
    QPushButton {
        background: rgba(210,160,40,40);
        color: #ffddaa;
        border: 1px solid rgba(210,160,40,40);
        border-radius: 16px; padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(230,180,50,70); }
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
BTN_GREEN = """
    QPushButton {
        background: rgba(40,160,100,40);
        color: #88ffbb;
        border: 1px solid rgba(60,180,120,60);
        border-radius: 16px; padding: 6px 18px; font-size: 11px;
    }
    QPushButton:hover { background: rgba(50,200,120,70); }
"""
TABLE_STYLE = """
    QTableWidget {
        background: rgba(15,10,5,220);
        color: #ddccaa;
        border: 1px solid rgba(180,140,40,30);
        border-radius: 8px; gridline-color: rgba(80,60,20,25);
        font-size: 12px; selection-background-color: rgba(210,160,40,60);
    }
    QTableWidget::item { padding: 5px 8px; }
    QHeaderView::section {
        background: rgba(25,18,8,230);
        color: #ccaa77; padding: 8px 10px; border: none;
        border-bottom: 1px solid rgba(210,160,40,40);
        font-weight: 700; font-size: 11px; letter-spacing: 1px;
    }
"""
DIALOG_QSS = """
    QDialog {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #1a1004, stop:1 #2e1c08);
        border: 1px solid rgba(210,160,40,40); border-radius: 12px;
    }
    QLabel { color: #ccaa88; font-size: 12px; background: transparent; }
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
        background: rgba(15,10,5,230); color: #ddccaa;
        border: 1px solid rgba(210,160,40,35); border-radius: 6px;
        padding: 6px 10px; font-size: 12px;
    }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background: rgba(20,14,6,240); color: #ddccaa;
        selection-background-color: rgba(210,160,40,60);
        border: 1px solid rgba(210,160,40,30);
    }
"""


# ═══════ 金色统计卡片 ═══════
class GoldStatCard(QFrame):
    def __init__(self, title, color_start, color_end, parent=None):
        super().__init__(parent)
        self._title = title
        self._value_int = 0
        self._color_start = QColor(*color_start)
        self._color_end = QColor(*color_end)
        self.setFixedSize(180, 80)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def set_value(self, v):
        self._value_int = int(v)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 12, 12)
        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0, self._color_start)
        grad.setColorAt(1, self._color_end)
        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(QColor(210, 160, 40, 60), 1))
        painter.drawPath(path)

        painter.setPen(QColor(210, 180, 120, 180))
        painter.setFont(QFont("sans-serif", 10))
        painter.drawText(14, 24, self._title)

        painter.setPen(QColor(255, 230, 180))
        painter.setFont(QFont("sans-serif", 24, QFont.Bold))
        painter.drawText(14, 58, str(self._value_int))

        painter.end()


# ═══════════════ 佣金明细对话框 ═══════════════
class CommissionDetailDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("佣金明细")
        self.setMinimumSize(600, 450)
        self.setStyleSheet(DIALOG_QSS)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 16, 20, 16)

        # 过滤栏
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)
        filter_row.addWidget(QLabel("用户:"))
        self._user_edit = QLineEdit()
        self._user_edit.setPlaceholderText("搜索用户ID")
        self._user_edit.textChanged.connect(self._load)
        filter_row.addWidget(self._user_edit)

        filter_row.addWidget(QLabel("状态:"))
        self._status_combo = QComboBox()
        self._status_combo.addItems(["全部", "pending", "approved", "rejected"])
        self._status_combo.currentTextChanged.connect(self._load)
        filter_row.addWidget(self._status_combo)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(["用户", "来源", "金额", "类型", "状态", "时间"])
        self._table.setStyleSheet(TABLE_STYLE)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

    def _load(self):
        user = self._user_edit.text().strip()
        status = self._status_combo.currentText()
        if status == "全部":
            status = ""
        rows = dist_get_commissions(user=user, status=status)
        self._table.setRowCount(len(rows))
        total = 0.0
        for i, r in enumerate(rows):
            self._table.setItem(i, 0, QTableWidgetItem(r["user_id"] or ""))
            self._table.setItem(i, 1, QTableWidgetItem(r["source_user"] or ""))
            amt = float(r["amount"]) if r.get("amount") else 0
            self._table.setItem(i, 2, QTableWidgetItem(f"¥{amt:,.2f}"))
            self._table.setItem(i, 3, QTableWidgetItem(r["comm_type"] or ""))
            status_item = QTableWidgetItem(r["status"] or "")
            if r["status"] == "approved":
                status_item.setForeground(QColor(136, 255, 187))
            elif r["status"] == "rejected":
                status_item.setForeground(QColor(255, 170, 170))
            self._table.setItem(i, 4, status_item)
            self._table.setItem(i, 5, QTableWidgetItem(r["created_at"] or ""))
            total += amt

        # 合计行
        rc = self._table.rowCount()
        self._table.insertRow(rc)
        self._table.setItem(rc, 0, QTableWidgetItem("合计"))
        total_item = QTableWidgetItem(f"¥{total:,.2f}")
        total_item.setFont(QFont("sans-serif", 12, QFont.Bold))
        self._table.setItem(rc, 2, total_item)


# ═══════════════ 团队结构树对话框 ═══════════════
class TeamTreeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("团队结构")
        self.setMinimumSize(600, 450)
        self.setStyleSheet(DIALOG_QSS)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 16, 20, 16)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("搜索 leader_id 或 member_id")
        self._search_edit.textChanged.connect(self._load)
        search_layout.addWidget(self._search_edit)
        search_layout.addStretch()
        layout.addLayout(search_layout)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["队长", "成员ID", "成员名", "加入时间", "ID"])
        self._table.setStyleSheet(TABLE_STYLE)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

    def _load(self):
        search = self._search_edit.text().strip()
        rows = dist_get_team(search)
        self._table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self._table.setItem(i, 0, QTableWidgetItem(r["leader_id"] or ""))
            self._table.setItem(i, 1, QTableWidgetItem(r["member_id"] or ""))
            self._table.setItem(i, 2, QTableWidgetItem(r["member_name"] or ""))
            self._table.setItem(i, 3, QTableWidgetItem(r["joined_at"] or ""))
            self._table.setItem(i, 4, QTableWidgetItem(str(r["id"])))


# ═══════════════ 分销管理窗口 ═══════════════
class DistributionWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("分销管理 · CREW")
        self.setMinimumSize(650, 600)
        self.setStyleSheet(DIALOG_QSS)
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(10)
        main.setContentsMargins(20, 16, 20, 16)

        # ── 标题 ──
        title = QLabel("分销管理")
        title.setStyleSheet(
            "color: #ffddaa; font-size: 18px; font-weight: 800; "
            "letter-spacing: 6px; background: transparent;"
        )
        main.addWidget(title, alignment=Qt.AlignCenter)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(210,160,40,40),
                stop:0.5 rgba(210,160,40,80),
                stop:0.7 rgba(210,160,40,40), stop:1 transparent);
            border: none;
        """)
        main.addWidget(line)

        # ── 3 个金色统计卡片 ──
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)
        self._card_total = GoldStatCard("链接总数", (180, 140, 20), (120, 80, 10))
        self._card_clicks = GoldStatCard("总点击", (200, 150, 30), (130, 90, 15))
        self._card_regs = GoldStatCard("总注册", (210, 160, 40), (140, 100, 20))
        cards_layout.addWidget(self._card_total)
        cards_layout.addWidget(self._card_clicks)
        cards_layout.addWidget(self._card_regs)
        main.addLayout(cards_layout)

        # ── 搜索栏 ──
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        search_label = QLabel("搜索")
        search_label.setStyleSheet("color: #ccaa88; font-size: 12px; background: transparent;")
        search_layout.addWidget(search_label)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("用户ID / 邀请码")
        self._search_edit.textChanged.connect(self._do_search)
        self._search_edit.setStyleSheet(
            "background: rgba(15,10,5,230); color: #ddccaa; "
            "border: 1px solid rgba(210,160,40,35); border-radius: 6px; "
            "padding: 6px 10px; font-size: 12px;"
        )
        search_layout.addWidget(self._search_edit)
        search_layout.addStretch()

        self._comm_btn = QPushButton("佣金明细")
        self._comm_btn.setStyleSheet(BTN_GREEN)
        self._comm_btn.clicked.connect(self._show_commissions)
        search_layout.addWidget(self._comm_btn)

        self._team_btn = QPushButton("团队结构")
        self._team_btn.setStyleSheet(BTN_GOLD)
        self._team_btn.clicked.connect(self._show_team)
        search_layout.addWidget(self._team_btn)

        main.addLayout(search_layout)

        # ── 表格 7 列 ──
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["用户ID", "邀请码", "链接", "点击", "注册", "状态", "创建时间"])
        self._table.setStyleSheet(TABLE_STYLE)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        main.addWidget(self._table)

    def _load_data(self):
        self._refresh_stats()
        self._do_search()

    def _refresh_stats(self):
        rows = dist_get_links()
        total = len(rows)
        clicks = sum(r["clicks"] or 0 for r in rows)
        regs = sum(r["registrations"] or 0 for r in rows)
        self._card_total.set_value(total)
        self._card_clicks.set_value(clicks)
        self._card_regs.set_value(regs)

    def _do_search(self):
        search = self._search_edit.text().strip()
        rows = dist_get_links(search)
        self._table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self._table.setItem(i, 0, QTableWidgetItem(r["user_id"] or ""))
            self._table.setItem(i, 1, QTableWidgetItem(r["code"] or ""))
            self._table.setItem(i, 2, QTableWidgetItem(r["url"] or ""))
            self._table.setItem(i, 3, QTableWidgetItem(str(r["clicks"] or 0)))
            self._table.setItem(i, 4, QTableWidgetItem(str(r["registrations"] or 0)))
            status_item = QTableWidgetItem(r["status"] or "")
            if r["status"] == "active":
                status_item.setForeground(QColor(136, 255, 187))
            elif r["status"] == "inactive":
                status_item.setForeground(QColor(255, 170, 170))
            self._table.setItem(i, 5, status_item)
            self._table.setItem(i, 6, QTableWidgetItem(r["created_at"] or ""))

    def _show_commissions(self):
        dlg = CommissionDetailDialog(self)
        dlg.exec_()

    def _show_team(self):
        dlg = TeamTreeDialog(self)
        dlg.exec_()

```
