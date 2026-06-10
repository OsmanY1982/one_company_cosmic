"""
分销管理 · CREW
独立的 QDialog 子窗口，金色渐变主题
"""
import sqlite3, os, hashlib, time
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QComboBox,
    QSpinBox, QDoubleSpinBox, QLineEdit, QFormLayout, QFrame
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


# ═══════ DAO ═══════
def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def dist_generate_no():
    ts = str(int(time.time() * 1000))[-8:]
    rand = hashlib.md5(str(time.time()).encode()).hexdigest()[:4].upper()
    return f"D{ts}{rand}"

def dist_init_db():
    conn = _get_conn()
    conn.execute('''CREATE TABLE IF NOT EXISTS distributions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dist_no TEXT, name TEXT, phone TEXT,
        level TEXT DEFAULT '初级', parent_id INTEGER,
        commission_rate REAL DEFAULT 5,
        total_referrals INTEGER DEFAULT 0,
        total_commission REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS commissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dist_id INTEGER, dist_name TEXT,
        order_no TEXT, order_amount REAL,
        commission_amount REAL, level TEXT DEFAULT '一级',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def dist_get_all(search=""):
    conn = _get_conn()
    if search:
        rows = conn.execute(
            "SELECT * FROM distributions WHERE name LIKE ? OR phone LIKE ? OR dist_no LIKE ? ORDER BY id DESC",
            (f"%{search}%", f"%{search}%", f"%{search}%")).fetchall()
    else:
        rows = conn.execute("SELECT * FROM distributions ORDER BY id DESC").fetchall()
    conn.close()
    return rows

def dist_add(name, phone, level, commission_rate, parent_id=None):
    conn = _get_conn()
    dist_no = dist_generate_no()
    conn.execute(
        "INSERT INTO distributions(dist_no,name,phone,level,parent_id,commission_rate) VALUES(?,?,?,?,?,?)",
        (dist_no, name, phone, level, parent_id, commission_rate))
    conn.commit()
    conn.close()

def dist_update(did, name, phone, level, commission_rate, parent_id=None):
    conn = _get_conn()
    conn.execute(
        "UPDATE distributions SET name=?,phone=?,level=?,commission_rate=?,parent_id=? WHERE id=?",
        (name, phone, level, commission_rate, parent_id, did))
    conn.commit()
    conn.close()

def dist_delete(did):
    conn = _get_conn()
    conn.execute("DELETE FROM commissions WHERE dist_id=?", (did,))
    conn.execute("DELETE FROM distributions WHERE id=?", (did,))
    conn.commit()
    conn.close()

def dist_get_stats():
    conn = _get_conn()
    total = conn.execute("SELECT COUNT(*) FROM distributions").fetchone()[0]
    total_ref = conn.execute("SELECT COALESCE(SUM(total_referrals),0) FROM distributions").fetchone()[0]
    total_comm = conn.execute("SELECT COALESCE(SUM(total_commission),0) FROM distributions").fetchone()[0]
    conn.close()
    return total, total_ref, total_comm

def dist_get_commissions(dist_id):
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM commissions WHERE dist_id=? ORDER BY id DESC", (dist_id,)).fetchall()
    conn.close()
    return rows


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


# ═══════════════ 分销商表单对话框 ═══════════════
class DistributionDialog(QDialog):
    def __init__(self, parent=None, row=None):
        super().__init__(parent)
        self.row = row
        self.setWindowTitle("编辑分销商" if row else "新增分销商")
        self.setMinimumWidth(380)
        self.setStyleSheet(DIALOG_QSS)
        self._build_ui()
        if row:
            self._fill_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("分销商信息" if not self.row else "编辑分销商信息")
        title.setStyleSheet(
            "color: #ffddaa; font-size: 16px; font-weight: 700; letter-spacing: 3px; background: transparent;"
        )
        layout.addWidget(title, alignment=Qt.AlignCenter)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("请输入姓名")
        form.addRow("姓名", self._name_edit)

        self._phone_edit = QLineEdit()
        self._phone_edit.setPlaceholderText("请输入电话")
        form.addRow("电话", self._phone_edit)

        self._level_combo = QComboBox()
        self._level_combo.addItems(["初级", "中级", "高级", "合伙人"])
        form.addRow("等级", self._level_combo)

        self._rate_spin = QDoubleSpinBox()
        self._rate_spin.setRange(0, 50)
        self._rate_spin.setSuffix(" %")
        self._rate_spin.setValue(5)
        self._rate_spin.setDecimals(1)
        form.addRow("佣金率", self._rate_spin)

        layout.addLayout(form)

        layout.addSpacing(8)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(BTN_DANGER)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setStyleSheet(BTN_GOLD)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _fill_data(self):
        r = self.row
        self._name_edit.setText(r['name'] or '')
        self._phone_edit.setText(r['phone'] or '')
        idx = self._level_combo.findText(r['level'] or '初级')
        if idx >= 0:
            self._level_combo.setCurrentIndex(idx)
        self._rate_spin.setValue(r['commission_rate'] or 5)

    def _save(self):
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入姓名")
            return
        phone = self._phone_edit.text().strip()
        level = self._level_combo.currentText()
        rate = self._rate_spin.value()
        self._result = (name, phone, level, rate)
        self.accept()

    def get_data(self):
        return self._result


# ═══════════════ 佣金明细对话框 ═══════════════
class CommissionDialog(QDialog):
    def __init__(self, parent=None, dist_id=None, dist_name=""):
        super().__init__(parent)
        self.dist_id = dist_id
        self.setWindowTitle(f"佣金明细 · {dist_name}")
        self.setMinimumSize(550, 400)
        self.setStyleSheet(DIALOG_QSS)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 16, 20, 16)

        title = QLabel(self.windowTitle())
        title.setStyleSheet(
            "color: #ffddaa; font-size: 16px; font-weight: 700; letter-spacing: 3px; background: transparent;"
        )
        layout.addWidget(title, alignment=Qt.AlignCenter)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(["订单号", "订单金额", "佣金金额", "佣金等级", "时间", "分销商"])
        self._table.setStyleSheet(TABLE_STYLE)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

    def _load(self):
        if not self.dist_id:
            return
        rows = dist_get_commissions(self.dist_id)
        self._table.setRowCount(len(rows))
        total_comm = 0.0
        for i, r in enumerate(rows):
            self._table.setItem(i, 0, QTableWidgetItem(r['order_no'] or '-'))
            self._table.setItem(i, 1, QTableWidgetItem(f"¥{r['order_amount']:,.2f}" if r['order_amount'] else '-'))
            self._table.setItem(i, 2, QTableWidgetItem(f"¥{r['commission_amount']:,.2f}" if r['commission_amount'] else '-'))
            self._table.setItem(i, 3, QTableWidgetItem(r['level'] or ''))
            self._table.setItem(i, 4, QTableWidgetItem(r['created_at'] or ''))
            self._table.setItem(i, 5, QTableWidgetItem(r['dist_name'] or ''))
            total_comm += (r['commission_amount'] or 0)

        # 合计行
        row_count = self._table.rowCount()
        self._table.insertRow(row_count)
        sum_item = QTableWidgetItem("合计")
        sum_item.setFont(QFont("sans-serif", 12, QFont.Bold))
        self._table.setItem(row_count, 0, sum_item)
        self._table.setItem(row_count, 2, QTableWidgetItem(f"¥{total_comm:,.2f}"))


# ═══════════════ 分销管理窗口 ═══════════════
class DistributionWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("分销管理 · CREW")
        self.setFixedSize(650, 550)
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
        self._card_total = GoldStatCard("分销商总数", (180, 140, 20), (120, 80, 10))
        self._card_ref = GoldStatCard("总推荐数", (200, 150, 30), (130, 90, 15))
        self._card_comm = GoldStatCard("总佣金(万)", (210, 160, 40), (140, 100, 20))
        cards_layout.addWidget(self._card_total)
        cards_layout.addWidget(self._card_ref)
        cards_layout.addWidget(self._card_comm)
        main.addLayout(cards_layout)

        # ── 搜索栏 ──
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        search_label = QLabel("搜索")
        search_label.setStyleSheet("color: #ccaa88; font-size: 12px; background: transparent;")
        search_layout.addWidget(search_label)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("姓名 / 电话 / 编号")
        self._search_edit.textChanged.connect(self._on_search)
        self._search_edit.setStyleSheet(
            "background: rgba(15,10,5,230); color: #ddccaa; "
            "border: 1px solid rgba(210,160,40,35); border-radius: 6px; "
            "padding: 6px 10px; font-size: 12px;"
        )
        search_layout.addWidget(self._search_edit)

        search_layout.addStretch()

        self._add_btn = QPushButton("+ 新增")
        self._add_btn.setStyleSheet(BTN_GOLD)
        self._add_btn.clicked.connect(self._do_add)
        search_layout.addWidget(self._add_btn)

        self._edit_btn = QPushButton("编辑")
        self._edit_btn.setStyleSheet(BTN_GREEN)
        self._edit_btn.clicked.connect(self._do_edit)
        search_layout.addWidget(self._edit_btn)

        self._del_btn = QPushButton("删除")
        self._del_btn.setStyleSheet(BTN_DANGER)
        self._del_btn.clicked.connect(self._do_delete)
        search_layout.addWidget(self._del_btn)

        main.addLayout(search_layout)

        # ── 表格 (8列) ──
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(
            ["编号", "姓名", "电话", "等级", "推荐数", "佣金率", "累计佣金", "时间"])
        self._table.setStyleSheet(TABLE_STYLE)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        main.addWidget(self._table)

        # ── 底部按钮 ──
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        self._comm_btn = QPushButton("佣金记录")
        self._comm_btn.setStyleSheet(BTN_GOLD)
        self._comm_btn.clicked.connect(self._show_commissions)
        bottom_layout.addWidget(self._comm_btn)

        main.addLayout(bottom_layout)

    def _load_data(self):
        self._refresh_stats()
        self._load_table()

    def _refresh_stats(self):
        total, refs, comm = dist_get_stats()
        self._card_total.set_value(total)
        self._card_ref.set_value(refs)
        self._card_comm.set_value(comm / 10000)

    def _load_table(self):
        search = self._search_edit.text().strip()
        rows = dist_get_all(search)
        self._rows = rows
        self._table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self._table.setItem(i, 0, QTableWidgetItem(r['dist_no'] or ''))
            self._table.setItem(i, 1, QTableWidgetItem(r['name'] or ''))
            self._table.setItem(i, 2, QTableWidgetItem(r['phone'] or ''))
            self._table.setItem(i, 3, QTableWidgetItem(r['level'] or '初级'))
            self._table.setItem(i, 4, QTableWidgetItem(str(r['total_referrals'] or 0)))
            self._table.setItem(i, 5, QTableWidgetItem(f"{r['commission_rate']:.1f}%"))
            self._table.setItem(i, 6, QTableWidgetItem(f"¥{r['total_commission']:,.2f}"))
            self._table.setItem(i, 7, QTableWidgetItem(r['created_at'] or ''))

    def _on_search(self):
        self._load_table()

    def _get_selected_row(self):
        idx = self._table.currentRow()
        if idx < 0 or idx >= len(self._rows):
            return None
        return self._rows[idx]

    def _do_add(self):
        dlg = DistributionDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            dist_add(*data)
            self._load_data()

    def _do_edit(self):
        row = self._get_selected_row()
        if not row:
            QMessageBox.warning(self, "提示", "请先选择一条记录")
            return
        dlg = DistributionDialog(self, row=row)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            dist_update(row['id'], *data)
            self._load_data()

    def _do_delete(self):
        row = self._get_selected_row()
        if not row:
            QMessageBox.warning(self, "提示", "请先选择一条记录")
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除分销商「{row['name']}」及其佣金记录吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            dist_delete(row['id'])
            self._load_data()

    def _show_commissions(self):
        row = self._get_selected_row()
        if not row:
            QMessageBox.warning(self, "提示", "请先选择一位分销商")
            return
        dlg = CommissionDialog(self, dist_id=row['id'], dist_name=row['name'])
        dlg.exec_()


# ═══════ 初始化数据库 ═══════
try:
    dist_init_db()
except Exception:
    pass
