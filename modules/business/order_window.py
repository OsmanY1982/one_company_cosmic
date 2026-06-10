"""
订单管理 · ORBIT — 独立弹窗模块
"""
import os
import sqlite3
import random
import csv
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QHeaderView, QMessageBox,
    QFormLayout, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox,
    QDateEdit, QFileDialog, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# ── 路径 ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ORDER_DB = os.path.join(BASE_DIR, "modules", "business", "order_db.sqlite")
FINANCE_DB = os.path.join(BASE_DIR, "modules", "business", "finance_db.sqlite")


# ── 数据库初始化 ──
def _init_order_db():
    os.makedirs(os.path.dirname(ORDER_DB), exist_ok=True)
    conn = sqlite3.connect(ORDER_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_no TEXT,
        customer TEXT,
        product TEXT,
        quantity INTEGER,
        amount REAL,
        date TEXT,
        status TEXT DEFAULT '待处理',
        remark TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()


def _init_finance_db():
    os.makedirs(os.path.dirname(FINANCE_DB), exist_ok=True)
    conn = sqlite3.connect(FINANCE_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS finance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        amount REAL,
        date TEXT,
        desc TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()


# ── QSS ──
ORDER_QSS = """
QDialog {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #080e1a, stop:1 #0d1f3c);
    border: 1px solid rgba(68,136,255,40);
    border-radius: 12px;
}
QLabel {
    color: #aaccff;
    background: transparent;
}
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
    background: rgba(10,18,40,200);
    color: #ccddef;
    border: 1px solid rgba(68,136,255,40);
    border-radius: 4px;
    padding: 4px 8px;
}
QTableWidget {
    background: rgba(8,14,26,220);
    color: #ccddef;
    border: 1px solid rgba(68,136,255,40);
    border-radius: 8px;
    gridline-color: rgba(40,80,140,30);
    selection-background-color: rgba(68,136,255,60);
}
QTableWidget::item {
    padding: 4px 8px;
}
QHeaderView::section {
    background: rgba(20,40,80,180);
    color: #88aadd;
    border: 1px solid rgba(68,136,255,30);
    padding: 6px;
    font-weight: bold;
}
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(68,136,255,200), stop:1 rgba(100,160,255,200));
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: bold;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(80,150,255,230), stop:1 rgba(120,180,255,230));
}
QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(40,100,220,220), stop:1 rgba(60,120,240,220));
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background: rgba(10,18,40,240);
    color: #ccddef;
    selection-background-color: rgba(68,136,255,80);
    border: 1px solid rgba(68,136,255,40);
}
"""


# ═══════════════════════════════════════════════════════
#  OrderDialog — 新增/编辑表单
# ═══════════════════════════════════════════════════════

class OrderDialog(QDialog):
    def __init__(self, parent=None, order_data=None):
        super().__init__(parent)
        self.setWindowTitle("新增订单" if order_data is None else "编辑订单")
        self.resize(460, 480)
        self.setStyleSheet(ORDER_QSS)
        self._order_data = order_data

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("新增订单" if order_data is None else "编辑订单")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #aaccff;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.customer_edit = QLineEdit()
        self.customer_edit.setPlaceholderText("客户名称")
        self.product_edit = QLineEdit()
        self.product_edit.setPlaceholderText("产品名称")
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 99999)
        self.quantity_spin.setValue(1)
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 99999999.99)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("¥ ")
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(datetime.now().date())
        self.status_combo = QComboBox()
        self.status_combo.addItems(["待处理", "处理中", "已完成", "已取消"])
        self.remark_edit = QTextEdit()
        self.remark_edit.setMaximumHeight(80)

        form.addRow("客户:", self.customer_edit)
        form.addRow("产品:", self.product_edit)
        form.addRow("数量:", self.quantity_spin)
        form.addRow("金额:", self.amount_spin)
        form.addRow("日期:", self.date_edit)
        form.addRow("状态:", self.status_combo)
        form.addRow("备注:", self.remark_edit)

        layout.addLayout(form)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(60,60,80,150);
                color: #8899bb;
                border: 1px solid rgba(100,120,160,40);
                border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton:hover { background: rgba(80,80,100,180); }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # 编辑时填充
        if order_data:
            self._fill_data(order_data)

    def _fill_data(self, data):
        self.customer_edit.setText(data.get("customer", ""))
        self.product_edit.setText(data.get("product", ""))
        self.quantity_spin.setValue(data.get("quantity", 1))
        self.amount_spin.setValue(data.get("amount", 0))
        self.remark_edit.setPlainText(data.get("remark", ""))
        date_str = data.get("date", "")
        if date_str:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                self.date_edit.setDate(dt.date())
            except ValueError:
                pass
        status = data.get("status", "待处理")
        idx = self.status_combo.findText(status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)

    def _on_save(self):
        if not self.customer_edit.text().strip():
            QMessageBox.warning(self, "提示", "请输入客户名称")
            return
        self.accept()

    def get_data(self):
        return {
            "customer": self.customer_edit.text().strip(),
            "product": self.product_edit.text().strip(),
            "quantity": self.quantity_spin.value(),
            "amount": self.amount_spin.value(),
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "status": self.status_combo.currentText(),
            "remark": self.remark_edit.toPlainText().strip(),
        }


# ═══════════════════════════════════════════════════════
#  OrderWindow
# ═══════════════════════════════════════════════════════

class OrderWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("订单管理 · ORBIT")
        self.resize(600, 600)
        self.setStyleSheet(ORDER_QSS)

        _init_order_db()
        _init_finance_db()

        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 标题
        title = QLabel("订单管理 · ORBIT")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #aaccff;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 搜索栏
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索客户 / 产品 / 订单号...")
        self.search_edit.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["编号", "客户", "产品", "数量", "金额", "日期", "状态", "备注"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.table)

        # 按钮栏
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.add_btn = QPushButton("新增")
        self.add_btn.clicked.connect(self._on_add)
        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self._on_edit)
        self.del_btn = QPushButton("删除")
        self.del_btn.clicked.connect(self._on_delete)
        self.export_btn = QPushButton("导出CSV")
        self.export_btn.clicked.connect(self._on_export)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addWidget(self.export_btn)
        layout.addLayout(btn_layout)

    def _get_conn(self):
        conn = sqlite3.connect(ORDER_DB)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_data(self, search=""):
        conn = self._get_conn()
        c = conn.cursor()
        if search:
            c.execute("""SELECT * FROM orders
                WHERE customer LIKE ? OR product LIKE ? OR order_no LIKE ?
                ORDER BY created_at DESC""",
                (f"%{search}%", f"%{search}%", f"%{search}%"))
        else:
            c.execute("SELECT * FROM orders ORDER BY created_at DESC")
        rows = c.fetchall()
        conn.close()

        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            items = [
                row["order_no"] or "",
                row["customer"] or "",
                row["product"] or "",
                str(row["quantity"] or ""),
                f"¥{row['amount']:,.2f}" if row["amount"] else "",
                str(row["date"] or ""),
                row["status"] or "待处理",
                row["remark"] or "",
            ]
            for j, val in enumerate(items):
                self.table.setItem(i, j, QTableWidgetItem(val))

    def _on_search(self, text):
        self._load_data(text.strip())

    def _get_selected_id(self):
        idx = self.table.currentRow()
        if idx < 0:
            return None
        item = self.table.item(idx, 0)
        if item is None:
            return None
        return item.text()

    def _on_add(self):
        dlg = OrderDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        data = dlg.get_data()
        order_no = "OR" + datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100, 999))

        conn = self._get_conn()
        c = conn.cursor()
        c.execute("""INSERT INTO orders (order_no, customer, product, quantity, amount, date, status, remark)
            VALUES (?,?,?,?,?,?,?,?)""",
            (order_no, data["customer"], data["product"], data["quantity"],
             data["amount"], data["date"], data["status"], data["remark"]))
        conn.commit()
        conn.close()

        # 联动：写入财务收入
        self._sync_finance(order_no, data["amount"])

        self._load_data(self.search_edit.text().strip())

    def _on_edit(self):
        order_no = self._get_selected_id()
        if order_no is None:
            QMessageBox.information(self, "提示", "请先选择一条订单")
            return

        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM orders WHERE order_no = ?", (order_no,))
        row = c.fetchone()
        conn.close()
        if row is None:
            return

        data = dict(row)
        dlg = OrderDialog(self, order_data=data)
        if dlg.exec_() != QDialog.Accepted:
            return
        new_data = dlg.get_data()

        conn = self._get_conn()
        c = conn.cursor()
        c.execute("""UPDATE orders SET customer=?, product=?, quantity=?,
            amount=?, date=?, status=?, remark=? WHERE order_no=?""",
            (new_data["customer"], new_data["product"], new_data["quantity"],
             new_data["amount"], new_data["date"], new_data["status"],
             new_data["remark"], order_no))
        conn.commit()
        conn.close()
        self._load_data(self.search_edit.text().strip())

    def _on_delete(self):
        order_no = self._get_selected_id()
        if order_no is None:
            QMessageBox.information(self, "提示", "请先选择一条订单")
            return
        reply = QMessageBox.question(self, "确认删除", f"确定要删除订单 {order_no} 吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM orders WHERE order_no = ?", (order_no,))
        conn.commit()
        conn.close()
        self._load_data(self.search_edit.text().strip())

    def _on_export(self):
        desktop = os.path.expanduser("~/Desktop")
        default_name = f"订单导出_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "导出CSV", os.path.join(desktop, default_name),
                                              "CSV Files (*.csv)")
        if not path:
            return

        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM orders ORDER BY created_at DESC")
        rows = c.fetchall()
        conn.close()

        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["订单编号", "客户", "产品", "数量", "金额", "日期", "状态", "备注", "创建时间"])
            for row in rows:
                writer.writerow([
                    row["order_no"], row["customer"], row["product"],
                    row["quantity"], row["amount"], row["date"],
                    row["status"], row["remark"], row["created_at"],
                ])

        QMessageBox.information(self, "导出成功", f"已导出至:\n{path}")

    def _sync_finance(self, order_no, amount):
        try:
            conn = sqlite3.connect(FINANCE_DB)
            c = conn.cursor()
            c.execute("""INSERT INTO finance (type, amount, date, desc)
                VALUES (?,?,?,?)""",
                ("收入", amount, datetime.now().strftime("%Y-%m-%d"),
                 f"订单{order_no}"))
            conn.commit()
            conn.close()
        except Exception:
            pass
