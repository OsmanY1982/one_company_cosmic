"""
财务管理 · ORBIT — 独立弹窗模块
"""
import os
import sqlite3
import random
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QHeaderView, QMessageBox,
    QFormLayout, QComboBox, QTextEdit, QDoubleSpinBox, QDateEdit, QGroupBox
)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QLinearGradient, QFont, QPainterPath
)

# ── 路径 ──
from core.data import FINANCE_DB
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── 数据库初始化 ──
def _init_finance_db():
    os.makedirs(os.path.dirname(FINANCE_DB), exist_ok=True)
    conn = sqlite3.connect(FINANCE_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS finance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        category TEXT DEFAULT '',
        amount REAL NOT NULL,
        date TEXT NOT NULL,
        description TEXT DEFAULT '',
        order_no TEXT DEFAULT '',
        finance_no TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    # 迁移：为已有 finance 表补充业务字段
    for col, col_def in [
        ("order_no", "TEXT DEFAULT ''"),
        ("finance_no", "TEXT DEFAULT ''"),
    ]:
        try: c.execute(f"ALTER TABLE finance ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError: pass
    conn.commit()
    conn.close()


# ── QSS ──
FINANCE_QSS = """
QDialog {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #10081a, stop:1 #200e2e);
    border: 1px solid rgba(128,80,210,40);
    border-radius: 12px;
}
QLabel {
    color: #c0a0e8;
    background: transparent;
}
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
    background: rgba(20,10,30,200);
    color: #c0a0e8;
    border: 1px solid rgba(128,80,210,40);
    border-radius: 4px;
    padding: 4px 8px;
}
QTableWidget {
    background: rgba(16,8,26,220);
    color: #c0a0e8;
    border: 1px solid rgba(128,80,210,40);
    border-radius: 8px;
    gridline-color: rgba(100,50,180,30);
    selection-background-color: rgba(128,80,210,60);
}
QTableWidget::item {
    padding: 4px 8px;
}
QHeaderView::section {
    background: rgba(40,20,60,180);
    color: #a080d0;
    border: 1px solid rgba(128,80,210,30);
    padding: 6px;
    font-weight: bold;
}
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(128,80,210,200), stop:1 rgba(160,120,240,200));
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: bold;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(150,100,230,230), stop:1 rgba(180,140,255,230));
}
QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(100,50,180,220), stop:1 rgba(130,80,210,220));
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background: rgba(20,10,30,240);
    color: #c0a0e8;
    selection-background-color: rgba(128,80,210,80);
    border: 1px solid rgba(128,80,210,40);
}
QGroupBox {
    color: #a080d0;
    border: 1px solid rgba(128,80,210,40);
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
"""

# ── 收支分类 ──
INCOME_CATEGORIES = ["订单收入", "会员续费", "其他"]
EXPENSE_CATEGORIES = ["采购", "工资", "租金", "运营", "其他"]


# ═══════════════════════════════════════════════════════
#  SummaryCard — 带光晕的统计卡片 (QPainter 自绘)
# ═══════════════════════════════════════════════════════

class SummaryCard(QLabel):
    """用 QPainter 绘制带光晕渐变的数字卡片"""

    def __init__(self, title, color, parent=None):
        super().__init__(parent)
        self._title = title
        self._card_color = color
        self._value = "¥0.00"
        self.setMinimumSize(180, 80)
        self.setMaximumHeight(80)

    def set_value(self, value):
        self._value = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # 背景光晕
        glow = QRadialGradient(QPointF(w / 2, h / 2), max(w, h) / 2)
        glow.setColorAt(0, QColor(self._card_color.red(), self._card_color.green(),
                                   self._card_color.blue(), 40))
        glow.setColorAt(0.6, QColor(self._card_color.red(), self._card_color.green(),
                                     self._card_color.blue(), 10))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(glow))
        painter.drawRoundedRect(0, 0, w, h, 10, 10)

        # 卡片背景
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0, QColor(30, 15, 50, 180))
        bg.setColorAt(1, QColor(16, 8, 26, 200))
        painter.setBrush(QBrush(bg))
        pen = QPen(QColor(self._card_color.red(), self._card_color.green(),
                           self._card_color.blue(), 60))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRoundedRect(2, 2, w - 4, h - 4, 8, 8)

        # 标题
        painter.setPen(QColor(self._card_color.red(), self._card_color.green(),
                               self._card_color.blue(), 180))
        title_font = QFont("Arial", 9)
        painter.setFont(title_font)
        painter.drawText(QRectF(8, 6, w - 16, 20), Qt.AlignLeft | Qt.AlignVCenter, self._title)

        # 数值 — 带光晕
        value_font = QFont("Arial", 20, QFont.Bold)
        painter.setFont(value_font)
        # 光晕层
        glow_path = QPainterPath()
        glow_path.addText(8, 56, value_font, self._value)
        glow_pen = QPen(QColor(self._card_color.red(), self._card_color.green(),
                                self._card_color.blue(), 80), 4)
        painter.setPen(glow_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(glow_path)
        # 前景
        painter.setPen(QColor(255, 255, 255))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(glow_path)

        painter.end()


# ═══════════════════════════════════════════════════════
#  FinanceAddDialog — 新增记账弹窗
# ═══════════════════════════════════════════════════════

class FinanceAddDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新增记账")
        self.resize(400, 380)
        self.setStyleSheet(FINANCE_QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("新增记账")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #a080d0;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["收入", "支出"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)

        self.category_combo = QComboBox()
        self.category_combo.addItems(INCOME_CATEGORIES)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 99999999.99)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("¥ ")

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(datetime.now().date())

        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)

        form.addRow("类型:", self.type_combo)
        form.addRow("分类:", self.category_combo)
        form.addRow("金额:", self.amount_spin)
        form.addRow("日期:", self.date_edit)
        form.addRow("描述:", self.desc_edit)

        layout.addLayout(form)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("记账")
        save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(40,30,60,150);
                color: #8877aa;
                border: 1px solid rgba(128,80,210,40);
                border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton:hover { background: rgba(60,50,80,180); }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _on_type_changed(self, text):
        self.category_combo.clear()
        if text == "收入":
            self.category_combo.addItems(INCOME_CATEGORIES)
        else:
            self.category_combo.addItems(EXPENSE_CATEGORIES)

    def _on_save(self):
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "提示", "请输入金额")
            return
        self.accept()

    def get_data(self):
        return {
            "type": self.type_combo.currentText(),
            "category": self.category_combo.currentText(),
            "amount": self.amount_spin.value(),
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "description": self.desc_edit.toPlainText().strip(),
        }


# ═══════════════════════════════════════════════════════
#  FinanceEditDialog — 编辑记账弹窗
# ═══════════════════════════════════════════════════════

class FinanceEditDialog(QDialog):
    def __init__(self, parent=None, cur_type="", cur_category="", cur_amount=0.0,
                 cur_date="", cur_desc=""):
        super().__init__(parent)
        self.setWindowTitle("编辑记账")
        self.resize(400, 380)
        self.setStyleSheet(FINANCE_QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title_label = QLabel("编辑记账")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #a080d0;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        form = QFormLayout()
        form.setSpacing(10)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["收入", "支出"])
        self.type_combo.setCurrentText(cur_type)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)

        self.category_combo = QComboBox()
        if cur_type == "收入":
            self.category_combo.addItems(INCOME_CATEGORIES)
        else:
            self.category_combo.addItems(EXPENSE_CATEGORIES)
        idx = self.category_combo.findText(cur_category)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 99999999.99)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("¥ ")
        self.amount_spin.setValue(cur_amount)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        if cur_date:
            self.date_edit.setDate(datetime.strptime(cur_date, "%Y-%m-%d").date())
        else:
            self.date_edit.setDate(datetime.now().date())

        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setText(cur_desc)

        form.addRow("类型:", self.type_combo)
        form.addRow("分类:", self.category_combo)
        form.addRow("金额:", self.amount_spin)
        form.addRow("日期:", self.date_edit)
        form.addRow("描述:", self.desc_edit)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(40,30,60,150);
                color: #8877aa;
                border: 1px solid rgba(128,80,210,40);
                border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton:hover { background: rgba(60,50,80,180); }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _on_type_changed(self, text):
        self.category_combo.clear()
        if text == "收入":
            self.category_combo.addItems(INCOME_CATEGORIES)
        else:
            self.category_combo.addItems(EXPENSE_CATEGORIES)

    def _on_save(self):
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "提示", "请输入金额")
            return
        self.accept()

    def get_data(self):
        return {
            "type": self.type_combo.currentText(),
            "category": self.category_combo.currentText(),
            "amount": self.amount_spin.value(),
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "description": self.desc_edit.toPlainText().strip(),
        }


# ═══════════════════════════════════════════════════════
#  FinanceWindow
# ═══════════════════════════════════════════════════════

class FinanceWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("财务管理 · ORBIT")
        self.resize(650, 550)
        self.setStyleSheet(FINANCE_QSS)

        _init_finance_db()

        self._init_ui()
        self._load_data()
        self._update_summary()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # 标题
        title = QLabel("财务管理 · ORBIT")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #a080d0;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ── 顶部统计卡片区 ──
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.income_card = SummaryCard("总收入", QColor(0, 200, 120), self)
        self.expense_card = SummaryCard("总支出", QColor(220, 80, 80), self)
        self.balance_card = SummaryCard("结余", QColor(128, 160, 255), self)

        stats_layout.addWidget(self.income_card)
        stats_layout.addWidget(self.expense_card)
        stats_layout.addWidget(self.balance_card)
        layout.addLayout(stats_layout)

        # ── 记账表单 ──
        form_group = QGroupBox("记账")
        form_group_layout = QHBoxLayout(form_group)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["收入", "支出"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)

        self.category_combo = QComboBox()
        self.category_combo.addItems(INCOME_CATEGORIES)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 99999999.99)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("¥ ")

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(datetime.now().date())

        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(32)
        self.desc_edit.setPlaceholderText("描述...")

        self.add_btn = QPushButton("记账")
        self.add_btn.clicked.connect(self._on_add)

        form_group_layout.addWidget(QLabel("类型:"))
        form_group_layout.addWidget(self.type_combo)
        form_group_layout.addWidget(QLabel("分类:"))
        form_group_layout.addWidget(self.category_combo)
        form_group_layout.addWidget(QLabel("金额:"))
        form_group_layout.addWidget(self.amount_spin)
        form_group_layout.addWidget(QLabel("日期:"))
        form_group_layout.addWidget(self.date_edit)
        form_group_layout.addWidget(self.desc_edit)
        form_group_layout.addWidget(self.add_btn)

        layout.addWidget(form_group)

        # ── 过滤栏 ──
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)
        filter_row.addWidget(QLabel("筛选:"))
        self.filter_type = QComboBox()
        self.filter_type.addItems(["全部", "收入", "支出"])
        self.filter_type.currentTextChanged.connect(self._load_data)
        filter_row.addWidget(self.filter_type)
        self.filter_category = QComboBox()
        self.filter_category.addItems(["全部"] + INCOME_CATEGORIES + EXPENSE_CATEGORIES)
        self.filter_category.currentTextChanged.connect(self._load_data)
        filter_row.addWidget(self.filter_category)
        self.filter_search = QLineEdit()
        self.filter_search.setPlaceholderText("搜索描述...")
        self.filter_search.setStyleSheet("""
            background: rgba(20,10,30,200); color: #c0a0e8;
            border: 1px solid rgba(128,80,210,40); border-radius: 4px;
            padding: 4px 8px;
        """)
        self.filter_search.textChanged.connect(self._load_data)
        filter_row.addWidget(self.filter_search)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        # ── 表格 ──
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "类型", "分类", "金额", "日期", "描述", "时间"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.table)

        # 按钮栏
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self._on_edit)
        self.del_btn = QPushButton("删除")
        self.del_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.del_btn)
        layout.addLayout(btn_layout)

    def _on_type_changed(self, text):
        self.category_combo.clear()
        if text == "收入":
            self.category_combo.addItems(INCOME_CATEGORIES)
        else:
            self.category_combo.addItems(EXPENSE_CATEGORIES)

    def _get_conn(self):
        conn = sqlite3.connect(FINANCE_DB)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_data(self):
        conn = self._get_conn()
        c = conn.cursor()

        sql = "SELECT * FROM finance WHERE 1=1"
        params = []

        ftype = self.filter_type.currentText()
        if ftype != "全部":
            sql += " AND type=?"
            params.append(ftype)

        fcat = self.filter_category.currentText()
        if fcat != "全部":
            sql += " AND category=?"
            params.append(fcat)

        fsearch = self.filter_search.text().strip()
        if fsearch:
            sql += " AND description LIKE ?"
            params.append(f"%{fsearch}%")

        sql += " ORDER BY date DESC, created_at DESC"
        c.execute(sql, params)
        rows = c.fetchall()
        conn.close()

        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            items = [
                str(row["id"]),
                row["type"] or "",
                row["category"] or "",
                f"¥{row['amount']:,.2f}" if row.get("amount") else "¥0.00",
                row["date"] or "",
                row["description"] or "",
                row["created_at"] or "",
            ]
            for j, val in enumerate(items):
                self.table.setItem(i, j, QTableWidgetItem(val))

    def _update_summary(self):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT COALESCE(SUM(CASE WHEN type='收入' THEN amount ELSE 0 END),0) FROM finance")
        income = c.fetchone()[0]
        c.execute("SELECT COALESCE(SUM(CASE WHEN type='支出' THEN amount ELSE 0 END),0) FROM finance")
        expense = c.fetchone()[0]
        conn.close()

        balance = income - expense
        self.income_card.set_value(f"¥{income:,.2f}")
        self.expense_card.set_value(f"¥{expense:,.2f}")
        self.balance_card.set_value(f"¥{balance:,.2f}")

    def _get_selected_id(self):
        idx = self.table.currentRow()
        if idx < 0:
            return None
        item = self.table.item(idx, 0)
        if item is None:
            return None
        try:
            return int(item.text())
        except ValueError:
            return None

    def _get_selected_row_data(self):
        idx = self.table.currentRow()
        if idx < 0:
            return None
        data = {}
        cols = ["id", "type", "category", "amount", "date", "description", "created_at"]
        for j, key in enumerate(cols):
            item = self.table.item(idx, j)
            data[key] = item.text() if item else ""
        return data

    def _on_add(self):
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "提示", "请输入金额")
            return

        ftype = self.type_combo.currentText()
        category = self.category_combo.currentText()
        amount = self.amount_spin.value()
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        desc = self.desc_edit.toPlainText().strip()
        finance_no = "FN" + datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100, 999))

        conn = self._get_conn()
        c = conn.cursor()
        c.execute("""INSERT INTO finance (type, category, amount, date, description, finance_no)
            VALUES (?,?,?,?,?,?)""",
            (ftype, category, amount, date_str, desc, finance_no))
        conn.commit()
        conn.close()

        self.amount_spin.setValue(0)
        self.desc_edit.clear()
        self._load_data()
        self._update_summary()

    def _on_edit(self):
        data = self._get_selected_row_data()
        if data is None:
            QMessageBox.information(self, "提示", "请先选择一条记录")
            return
        # 去除金额前缀 ¥
        raw = data["amount"].replace("¥", "").replace(",", "")
        try:
            cur_amount = float(raw)
        except ValueError:
            cur_amount = 0.0

        dlg = FinanceEditDialog(
            self,
            cur_type=data["type"],
            cur_category=data["category"],
            cur_amount=cur_amount,
            cur_date=data["date"],
            cur_desc=data["description"],
        )
        if dlg.exec_() == QDialog.Accepted:
            new_data = dlg.get_data()
            conn = self._get_conn()
            c = conn.cursor()
            c.execute("""UPDATE finance SET type=?, category=?, amount=?, date=?, description=?
                WHERE id=?""",
                (new_data["type"], new_data["category"], new_data["amount"],
                 new_data["date"], new_data["description"], int(data["id"])))
            conn.commit()
            conn.close()
            self._load_data()
            self._update_summary()

    def _on_delete(self):
        rid = self._get_selected_id()
        if rid is None:
            QMessageBox.information(self, "提示", "请先选择一条记录")
            return
        reply = QMessageBox.question(self, "确认删除", f"确定要删除记录 #{rid} 吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM finance WHERE id = ?", (rid,))
        conn.commit()
        conn.close()
        self._load_data()
        self._update_summary()
