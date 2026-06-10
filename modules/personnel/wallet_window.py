"""
钱包管理 · CREW
独立的 QDialog 子窗口，暖橙渐变主题
"""
import sqlite3, os, math
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QComboBox,
    QDoubleSpinBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QLinearGradient, QPen,
    QBrush, QFont, QPainterPath
)

# ═══════ 数据库路径 ═══════
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
DB_PATH = os.path.join(DATA_DIR, "personnel_db.sqlite")
os.makedirs(DATA_DIR, exist_ok=True)

# ═══════ 暖橙 QSS ═══════
BTN_ORANGE = """
    QPushButton {
        background: rgba(255,140,40,40);
        color: #ffccaa;
        border: 1px solid rgba(255,140,40,40);
        border-radius: 16px; padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(255,160,60,70); }
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
DIALOG_QSS = """
    QDialog {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #1a0c04, stop:1 #2e1008);
        border: 1px solid rgba(255,140,40,40); border-radius: 12px;
    }
    QLabel { color: #ccaa99; font-size: 12px; background: transparent; }
    QComboBox {
        background: rgba(15,8,5,230); color: #ddbbaa;
        border: 1px solid rgba(255,140,40,35); border-radius: 6px;
        padding: 6px 10px; font-size: 12px;
    }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background: rgba(20,10,6,240); color: #ddbbaa;
        selection-background-color: rgba(255,140,40,60);
        border: 1px solid rgba(255,140,40,30);
    }
    QDoubleSpinBox {
        background: rgba(15,8,5,230); color: #ffccaa;
        border: 1px solid rgba(255,140,40,35); border-radius: 6px;
        padding: 6px 10px; font-size: 13px; font-weight: 600;
    }
"""


# ═══════ DAO ═══════
def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def wallet_init_db():
    conn = _get_conn()
    conn.execute('''CREATE TABLE IF NOT EXISTS wallets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        staff_id INTEGER, staff_name TEXT,
        balance REAL DEFAULT 0, total_income REAL DEFAULT 0,
        total_withdraw REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(staff_id) REFERENCES staff(id)
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        staff_id INTEGER, staff_name TEXT,
        type TEXT, amount REAL, balance_after REAL,
        remark TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def wallet_get_or_create(staff_id, staff_name):
    conn = _get_conn()
    row = conn.execute("SELECT * FROM wallets WHERE staff_id=?", (staff_id,)).fetchone()
    if not row:
        conn.execute(
            "INSERT INTO wallets(staff_id,staff_name,balance,total_income,total_withdraw) VALUES(?,?,0,0,0)",
            (staff_id, staff_name))
        conn.commit()
        row = conn.execute("SELECT * FROM wallets WHERE staff_id=?", (staff_id,)).fetchone()
    else:
        if row['staff_name'] != staff_name:
            conn.execute("UPDATE wallets SET staff_name=? WHERE staff_id=?", (staff_name, staff_id))
            conn.commit()
            row = conn.execute("SELECT * FROM wallets WHERE staff_id=?", (staff_id,)).fetchone()
    conn.close()
    return dict(row)

def wallet_recharge(staff_id, staff_name, amount):
    conn = _get_conn()
    w = wallet_get_or_create(staff_id, staff_name)
    new_balance = w['balance'] + amount
    new_income = w['total_income'] + amount
    conn.execute("UPDATE wallets SET balance=?,total_income=? WHERE staff_id=?",
                 (new_balance, new_income, staff_id))
    conn.execute(
        "INSERT INTO transactions(staff_id,staff_name,type,amount,balance_after,remark) VALUES(?,?,?,?,?,?)",
        (staff_id, staff_name, '充值', amount, new_balance, '余额充值'))
    conn.commit()
    conn.close()
    return new_balance

def wallet_withdraw(staff_id, staff_name, amount):
    conn = _get_conn()
    w = wallet_get_or_create(staff_id, staff_name)
    if amount > w['balance']:
        conn.close()
        return None, f"余额不足，当前余额: {w['balance']:.2f}"
    new_balance = w['balance'] - amount
    new_withdraw = w['total_withdraw'] + amount
    conn.execute("UPDATE wallets SET balance=?,total_withdraw=? WHERE staff_id=?",
                 (new_balance, new_withdraw, staff_id))
    conn.execute(
        "INSERT INTO transactions(staff_id,staff_name,type,amount,balance_after,remark) VALUES(?,?,?,?,?,?)",
        (staff_id, staff_name, '提现', amount, new_balance, '余额提现'))
    conn.commit()
    conn.close()
    return new_balance, None

def wallet_get_all_transactions(limit=200):
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM transactions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return rows

def wallet_get_stats():
    conn = _get_conn()
    total_balance = conn.execute("SELECT COALESCE(SUM(balance),0) FROM wallets").fetchone()[0]
    total_income = conn.execute("SELECT COALESCE(SUM(total_income),0) FROM wallets").fetchone()[0]
    total_withdraw = conn.execute("SELECT COALESCE(SUM(total_withdraw),0) FROM wallets").fetchone()[0]
    conn.close()
    return total_balance, total_income, total_withdraw

def staff_get_all_names():
    db = os.path.join(DATA_DIR, "staff.db")
    if not os.path.exists(db):
        return []
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, name FROM staff ORDER BY id").fetchall()
    conn.close()
    return rows


# ═══════ 余额卡片自绘 ═══════
class BalanceCard(QFrame):
    def __init__(self, title, color_start, color_end, parent=None):
        super().__init__(parent)
        self._title = title
        self._value = 0.0
        self._color_start = QColor(*color_start)
        self._color_end = QColor(*color_end)
        self.setFixedSize(180, 90)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def set_value(self, v):
        self._value = v
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # 卡面背景
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 12, 12)
        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0, self._color_start)
        grad.setColorAt(1, self._color_end)
        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(QColor(255, 140, 40, 60), 1))
        painter.drawPath(path)

        # 标题
        painter.setPen(QColor(255, 200, 160, 180))
        painter.setFont(QFont("sans-serif", 10))
        painter.drawText(14, 24, self._title)

        # 数值
        painter.setPen(QColor(255, 230, 200))
        painter.setFont(QFont("sans-serif", 22, QFont.Bold))
        painter.drawText(14, 60, f"¥{self._value:,.2f}")

        painter.end()


# ═══════════════ 钱包管理窗口 ═══════════════
class WalletWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("钱包管理 · CREW")
        self.setFixedSize(600, 550)
        self.setStyleSheet(DIALOG_QSS)
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(10)
        main.setContentsMargins(20, 16, 20, 16)

        # ── 标题 ──
        title = QLabel("钱包管理")
        title.setStyleSheet(
            "color: #ffccaa; font-size: 18px; font-weight: 800; "
            "letter-spacing: 6px; background: transparent;"
        )
        main.addWidget(title, alignment=Qt.AlignCenter)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(255,140,40,40),
                stop:0.5 rgba(255,140,40,80),
                stop:0.7 rgba(255,140,40,40), stop:1 transparent);
            border: none;
        """)
        main.addWidget(line)

        # ── 3 个余额卡片 ──
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)
        self._card_balance = BalanceCard("总余额", (255, 100, 40), (200, 60, 20))
        self._card_income = BalanceCard("累计收入", (255, 140, 60), (200, 80, 30))
        self._card_withdraw = BalanceCard("累计提现", (255, 120, 50), (180, 50, 15))
        cards_layout.addWidget(self._card_balance)
        cards_layout.addWidget(self._card_income)
        cards_layout.addWidget(self._card_withdraw)
        main.addLayout(cards_layout)

        # ── 分隔线 ──
        line2 = QFrame()
        line2.setFixedHeight(1)
        line2.setStyleSheet("background: rgba(255,140,40,20); border: none;")
        main.addWidget(line2)

        # ── 员工选择 + 余额 ──
        staff_layout = QHBoxLayout()
        staff_layout.setSpacing(12)
        staff_label = QLabel("选择员工")
        staff_label.setStyleSheet("color: #ccaa99; font-size: 12px; background: transparent;")
        staff_layout.addWidget(staff_label)

        self._staff_combo = QComboBox()
        self._staff_combo.setMinimumWidth(160)
        self._staff_combo.currentIndexChanged.connect(self._on_staff_changed)
        staff_layout.addWidget(self._staff_combo)

        staff_layout.addStretch()

        self._balance_label = QLabel("余额: ¥0.00")
        self._balance_label.setStyleSheet(
            "color: #ffcc88; font-size: 16px; font-weight: 700; background: transparent;"
        )
        staff_layout.addWidget(self._balance_label)
        main.addLayout(staff_layout)

        # ── 操作区 ──
        op_layout = QHBoxLayout()
        op_layout.setSpacing(10)

        recharge_label = QLabel("充值")
        recharge_label.setStyleSheet("color: #ccaa99; font-size: 11px; background: transparent;")
        op_layout.addWidget(recharge_label)

        self._recharge_spin = QDoubleSpinBox()
        self._recharge_spin.setRange(0, 999999)
        self._recharge_spin.setPrefix("¥ ")
        self._recharge_spin.setValue(100)
        self._recharge_spin.setFixedWidth(120)
        op_layout.addWidget(self._recharge_spin)

        self._recharge_btn = QPushButton("充值")
        self._recharge_btn.setStyleSheet(BTN_ORANGE)
        self._recharge_btn.clicked.connect(self._do_recharge)
        op_layout.addWidget(self._recharge_btn)

        op_layout.addSpacing(20)

        withdraw_label = QLabel("提现")
        withdraw_label.setStyleSheet("color: #ccaa99; font-size: 11px; background: transparent;")
        op_layout.addWidget(withdraw_label)

        self._withdraw_spin = QDoubleSpinBox()
        self._withdraw_spin.setRange(0, 999999)
        self._withdraw_spin.setPrefix("¥ ")
        self._withdraw_spin.setValue(50)
        self._withdraw_spin.setFixedWidth(120)
        op_layout.addWidget(self._withdraw_spin)

        self._withdraw_btn = QPushButton("提现")
        self._withdraw_btn.setStyleSheet(BTN_DANGER)
        self._withdraw_btn.clicked.connect(self._do_withdraw)
        op_layout.addWidget(self._withdraw_btn)

        op_layout.addStretch()
        main.addLayout(op_layout)

        # ── 交易记录表格 ──
        table_label = QLabel("交易记录")
        table_label.setStyleSheet(
            "color: #bb9988; font-size: 13px; font-weight: 700; letter-spacing: 2px; background: transparent;"
        )
        main.addWidget(table_label)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(["员工", "类型", "金额", "余额", "时间", "备注"])
        self._table.setStyleSheet(TABLE_STYLE)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        main.addWidget(self._table)

    def _load_data(self):
        # 加载员工下拉
        self._staff_data = {}
        self._staff_combo.blockSignals(True)
        self._staff_combo.clear()
        staff_rows = staff_get_all_names()
        for row in staff_rows:
            sid = row['id']
            name = row['name']
            self._staff_data[sid] = name
            self._staff_combo.addItem(f"{name} (ID:{sid})", sid)
        self._staff_combo.blockSignals(False)

        # 更新统计卡片
        self._refresh_stats()

        # 加载交易记录
        self._load_transactions()

        # 当前选中员工余额
        self._on_staff_changed()

    def _refresh_stats(self):
        bal, inc, wd = wallet_get_stats()
        self._card_balance.set_value(bal)
        self._card_income.set_value(inc)
        self._card_withdraw.set_value(wd)

    def _load_transactions(self):
        rows = wallet_get_all_transactions()
        self._table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self._table.setItem(i, 0, QTableWidgetItem(r['staff_name'] or ''))
            type_item = QTableWidgetItem(r['type'] or '')
            if r['type'] == '充值':
                type_item.setForeground(QColor(136, 255, 187))
            elif r['type'] == '提现':
                type_item.setForeground(QColor(255, 170, 170))
            self._table.setItem(i, 1, type_item)
            self._table.setItem(i, 2, QTableWidgetItem(f"¥{r['amount']:,.2f}"))
            self._table.setItem(i, 3, QTableWidgetItem(f"¥{r['balance_after']:,.2f}"))
            self._table.setItem(i, 4, QTableWidgetItem(r['created_at'] or ''))
            self._table.setItem(i, 5, QTableWidgetItem(r['remark'] or ''))

    def _on_staff_changed(self):
        sid = self._staff_combo.currentData()
        if sid is None:
            self._balance_label.setText("余额: ¥0.00")
            return
        name = self._staff_data.get(sid, "")
        w = wallet_get_or_create(sid, name)
        self._balance_label.setText(f"余额: ¥{w['balance']:,.2f}")

    def _do_recharge(self):
        sid = self._staff_combo.currentData()
        if sid is None:
            QMessageBox.warning(self, "提示", "请先选择员工")
            return
        amount = self._recharge_spin.value()
        if amount <= 0:
            QMessageBox.warning(self, "提示", "请输入有效充值金额")
            return
        name = self._staff_data.get(sid, "")
        new_bal = wallet_recharge(sid, name, amount)
        self._balance_label.setText(f"余额: ¥{new_bal:,.2f}")
        self._refresh_stats()
        self._load_transactions()
        self._recharge_spin.setValue(100)

    def _do_withdraw(self):
        sid = self._staff_combo.currentData()
        if sid is None:
            QMessageBox.warning(self, "提示", "请先选择员工")
            return
        amount = self._withdraw_spin.value()
        if amount <= 0:
            QMessageBox.warning(self, "提示", "请输入有效提现金额")
            return
        name = self._staff_data.get(sid, "")
        new_bal, err = wallet_withdraw(sid, name, amount)
        if err:
            QMessageBox.warning(self, "提现失败", err)
            return
        self._balance_label.setText(f"余额: ¥{new_bal:,.2f}")
        self._refresh_stats()
        self._load_transactions()
        self._withdraw_spin.setValue(50)


# ═══════ 初始化数据库 ═══════
try:
    wallet_init_db()
except Exception:
    pass
