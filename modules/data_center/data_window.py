"""
数据中心 → 星云观测站 · NEBULA OBSERVATORY
宇宙主题窗口：数据报表 / 数据大屏
"""
import os, sqlite3, csv
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QHeaderView, QTextEdit, QLineEdit,
    QComboBox, QGroupBox, QFrame, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from core.cosmic import CosmicBackground

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

# ═══════ 宇宙 QSS ═══════
TAB_STYLE = """
    QTabWidget::pane {
        background: transparent;
        border: 1px solid rgba(0,180,170,30);
        border-radius: 10px;
    }
    QTabBar::tab {
        background: rgba(8,22,24,220);
        color: #88aaaa; padding: 10px 22px;
        border: none; border-bottom: 2px solid transparent;
        font-size: 12px; font-weight: 600; letter-spacing: 2px; min-width: 70px;
    }
    QTabBar::tab:selected {
        color: #aaeecc;
        border-bottom: 2px solid #00b4aa;
        background: rgba(12,28,30,235);
    }
    QTabBar::tab:hover { color: #88ddbb; }
"""
TABLE_STYLE = """
    QTableWidget {
        background: rgba(6,18,20,220); color: #aacccc;
        border: 1px solid rgba(0,160,140,30); border-radius: 8px;
        gridline-color: rgba(0,100,80,25); font-size: 12px;
        selection-background-color: rgba(0,180,150,60);
    }
    QTableWidget::item { padding: 5px 10px; }
    QHeaderView::section {
        background: rgba(10,22,24,230); color: #88aaaa; padding: 8px 10px;
        border: none; border-bottom: 1px solid rgba(0,180,160,40);
        font-weight: 700; font-size: 11px; letter-spacing: 1px;
    }
"""
INPUT_STYLE = """
    QLineEdit, QComboBox, QTextEdit {
        background: rgba(6,18,20,230); color: #aacccc;
        border: 1px solid rgba(0,160,140,35); border-radius: 6px;
        padding: 6px 10px; font-size: 12px;
    }
    QLineEdit:focus { border: 1px solid rgba(0,200,160,180); }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background: #0a1618; color: #aacccc; selection-background-color: rgba(0,180,150,80);
    }
"""
BTN_PRIMARY = """
    QPushButton {
        background: rgba(0,160,140,40); color: #aaeecc;
        border: 1px solid rgba(0,180,150,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(0,200,160,70); }
"""


class DataWindow(QMainWindow):
    """星云观测站 · NEBULA OBSERVATORY"""

    def __init__(self, parent=None, role="admin"):
        super().__init__(parent)
        self._role = role
        self.setWindowTitle("一人公司 — 星云观测站 · NEBULA OBSERVATORY")
        self.setMinimumSize(1100, 720)
        self._build_ui()
        self._load_all()

    def _build_ui(self):
        bg = CosmicBackground()
        self.setCentralWidget(bg)

        hud = QWidget(bg)
        hud.setAttribute(Qt.WA_TranslucentBackground)
        hud.setGeometry(0, 0, self.width(), self.height())
        self._hud = hud

        layout = QVBoxLayout(hud)
        layout.setSpacing(0); layout.setContentsMargins(24, 16, 24, 16)

        header = QWidget(); header.setFixedHeight(80)
        header.setStyleSheet("background: transparent;")
        hl = QVBoxLayout(header); hl.setSpacing(4)

        title = QLabel("星云观测站")
        title.setStyleSheet("color: #aaeecc; font-size: 24px; font-weight: 800; letter-spacing: 8px; background: transparent;")
        hl.addWidget(title, alignment=Qt.AlignCenter)

        subtitle = QLabel("NEBULA OBSERVATORY · 数据洞察中枢")
        subtitle.setStyleSheet("color: #558877; font-size: 11px; letter-spacing: 3px; background: transparent;")
        hl.addWidget(subtitle, alignment=Qt.AlignCenter)

        line = QFrame(); line.setFixedHeight(2)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(0,180,150,50),
                stop:0.5 rgba(0,220,180,120),
                stop:0.7 rgba(0,180,150,50), stop:1 transparent);
            border: none;
        """)
        hl.addWidget(line)
        layout.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)
        layout.addWidget(self.tabs)

        self._build_report_tab()
        self._build_bi_tab()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_hud'):
            self._hud.setGeometry(0, 0, self.width(), self.height())

    def _build_report_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setSpacing(10); l.setContentsMargins(16, 12, 16, 12)

        cards = QHBoxLayout()
        self.kpi_labels = {}
        for name, color in [("财务收入","#44cc88"),("会员总数","#4488ff"),("客户数量","#ffaa44"),("订单总数","#cc88ff"),("团队人数","#ff6688")]:
            card = QFrame()
            card.setStyleSheet(f"background: rgba(8,20,22,230); border: 1px solid rgba(0,160,140,30); border-radius: 10px; padding: 12px; min-width: 130px;")
            cll = QVBoxLayout(card); cll.setContentsMargins(0,0,0,0)
            lb = QLabel(name); lb.setStyleSheet("color: #558877; font-size: 11px; background:transparent;")
            vl = QLabel("—"); vl.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: 700; background:transparent;")
            cll.addWidget(lb); cll.addWidget(vl)
            self.kpi_labels[name] = vl
            cards.addWidget(card)
        cards.addStretch()
        l.addLayout(cards)

        sr = QHBoxLayout()
        sr.addWidget(QLabel("报表类型:"))
        self.report_type = QComboBox()
        self.report_type.addItems(["收入概览","订单明细","会员统计","客户分析","产品销售"])
        self.report_type.setStyleSheet(INPUT_STYLE)
        self.report_type.currentTextChanged.connect(self._refresh_report)
        sr.addWidget(self.report_type); sr.addStretch()
        export = QPushButton("导出CSV"); export.setStyleSheet(BTN_PRIMARY); export.clicked.connect(self._export_report)
        sr.addWidget(export)
        l.addLayout(sr)

        self.report_table = QTableWidget()
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.report_table.setStyleSheet(TABLE_STYLE)
        self.report_table.setEditTriggers(QTableWidget.NoEditTriggers)
        l.addWidget(self.report_table)

        self.report_summary = QTextEdit()
        self.report_summary.setReadOnly(True); self.report_summary.setMaximumHeight(100)
        self.report_summary.setStyleSheet(INPUT_STYLE)
        l.addWidget(self.report_summary)

        self.tabs.addTab(tab, "数据报表")

    def _setup_table(self, headers):
        self.report_table.clear()
        self.report_table.setColumnCount(len(headers))
        self.report_table.setHorizontalHeaderLabels(headers)
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def _refresh_report(self):
        rtype = self.report_type.currentText()
        try:
            if rtype == "收入概览": self._load_finance()
            elif rtype == "订单明细": self._load_orders()
            elif rtype == "会员统计": self._load_members()
            elif rtype == "客户分析": self._load_customers()
            elif rtype == "产品销售": self._load_products()
        except Exception as e:
            self.report_summary.setText(f"加载异常: {e}")

    def _load_finance(self):
        db = os.path.join(DATA_DIR, "finance.db")
        if not os.path.exists(db):
            self._setup_table(["提示"]); self.report_summary.setText("暂无财务数据"); return
        conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM finance ORDER BY id DESC LIMIT 50").fetchall(); conn.close()
        self._setup_table(["ID","类型","金额","备注","日期"])
        self.report_table.setRowCount(len(rows))
        inc = exp = 0
        for i, r in enumerate(rows):
            for j, k in enumerate(['id','type','amount','note','date']):
                self.report_table.setItem(i, j, QTableWidgetItem(str(r[k]) if r[k] is not None else ""))
            amt = float(r['amount'] or 0)
            if r['type'] and '收入' in str(r['type']): inc += amt
            else: exp += amt
        self.report_summary.setText(f"总收入: ¥{inc:.2f} | 总支出: ¥{exp:.2f} | 利润: ¥{inc-exp:.2f}")

    def _load_orders(self):
        db = os.path.join(DATA_DIR, "order.db")
        if not os.path.exists(db): self._setup_table(["提示"]); self.report_summary.setText("暂无订单"); return
        conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 50").fetchall()
        t = conn.execute("SELECT COUNT(*), COALESCE(SUM(total_amount),0) FROM orders").fetchone(); conn.close()
        self._setup_table(["ID","订单号","客户","金额","时间","状态"])
        self.report_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, k in enumerate(['id','order_no','customer_name','total_amount','created_at','status']):
                self.report_table.setItem(i, j, QTableWidgetItem(str(r[k]) if r[k] is not None else ""))
        self.report_summary.setText(f"订单总数: {t[0]} | 总金额: ¥{t[1]:.2f}")

    def _load_members(self):
        db = os.path.join(DATA_DIR, "member.db")
        if not os.path.exists(db): self._setup_table(["提示"]); self.report_summary.setText("暂无会员"); return
        conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM member ORDER BY id DESC LIMIT 50").fetchall()
        stats = conn.execute("SELECT level, COUNT(*) as c FROM member GROUP BY level").fetchall(); conn.close()
        self._setup_table(["ID","姓名","电话","等级","积分","VIP到期","状态"])
        self.report_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, k in enumerate(['id','name','phone','level','points','vip_expire','status']):
                self.report_table.setItem(i, j, QTableWidgetItem(str(r[k]) if r[k] is not None else ""))
        levels = " | ".join([f"{s['level']}:{s['c']}" for s in stats])
        self.report_summary.setText(f"总计: {sum(s['c'] for s in stats)} | {levels}")

    def _load_customers(self):
        db = os.path.join(DATA_DIR, "customer.db")
        if not os.path.exists(db): self._setup_table(["提示"]); self.report_summary.setText("暂无客户"); return
        conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM customer ORDER BY id DESC LIMIT 50").fetchall()
        total = conn.execute("SELECT COUNT(*) FROM customer").fetchone()[0]; conn.close()
        self._setup_table(["ID","姓名","电话","公司","等级","备注"])
        self.report_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, k in enumerate(['id','name','phone','company','level','notes']):
                self.report_table.setItem(i, j, QTableWidgetItem(str(r[k]) if r[k] is not None else ""))
        self.report_summary.setText(f"客户总数: {total}")

    def _load_products(self):
        db = os.path.join(DATA_DIR, "product.db")
        if not os.path.exists(db): self._setup_table(["提示"]); self.report_summary.setText("暂无产品"); return
        conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM product ORDER BY id DESC LIMIT 50").fetchall()
        total = conn.execute("SELECT COUNT(*) FROM product").fetchone()[0]; conn.close()
        self._setup_table(["ID","名称","类别","价格","库存","状态"])
        self.report_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, k in enumerate(['id','name','category','price','stock','status']):
                self.report_table.setItem(i, j, QTableWidgetItem(str(r[k]) if r[k] is not None else ""))
        self.report_summary.setText(f"产品总数: {total}")

    def _export_report(self):
        fp, _ = QFileDialog.getSaveFileName(self, "导出", f"report_{datetime.now().strftime('%Y%m%d')}.csv", "CSV (*.csv)")
        if not fp: return
        with open(fp, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f)
            headers = [self.report_table.horizontalHeaderItem(c).text() for c in range(self.report_table.columnCount())]
            w.writerow(headers)
            for row in range(self.report_table.rowCount()):
                w.writerow([self.report_table.item(row, c).text() if self.report_table.item(row, c) else "" for c in range(self.report_table.columnCount())])
        self.report_summary.setText(f"已导出: {fp}")

    def _build_bi_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setSpacing(10); l.setContentsMargins(16, 12, 16, 12)

        fs = QPushButton("全屏 (F11)"); fs.setStyleSheet(BTN_PRIMARY); fs.clicked.connect(lambda: self.showFullScreen() if not self.isFullScreen() else self.showNormal())
        l.addWidget(fs, alignment=Qt.AlignRight)

        cards = QHBoxLayout()
        self.bi_kpi = {}
        for name, color, unit in [("总营收","#00ffaa","本月"),("订单数","#44ccff","本月"),("客单价","#ffaa44","平均"),("新增客户","#cc88ff","本月")]:
            card = QFrame()
            card.setStyleSheet(f"background: rgba(6,16,18,240); border: 1px solid rgba(0,180,150,40); border-radius: 14px; padding: 18px; min-width: 160px;")
            cll = QVBoxLayout(card); cll.setContentsMargins(0,0,0,0); cll.setSpacing(6)
            lb = QLabel(name); lb.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 700; background:transparent;")
            vl = QLabel("—"); vl.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: 800; background:transparent;")
            ul = QLabel(unit); ul.setStyleSheet("color: #447766; font-size: 10px; background:transparent;")
            cll.addWidget(lb); cll.addWidget(vl); cll.addWidget(ul)
            self.bi_kpi[name] = vl
            cards.addWidget(card)
        cards.addStretch()
        l.addLayout(cards)

        trend = QFrame()
        trend.setStyleSheet("background: rgba(8,18,20,220); border: 1px solid rgba(0,180,150,35); border-radius: 10px; padding: 14px;")
        tl = QVBoxLayout(trend)
        tl.addWidget(QLabel("数据趋势概览 (最近 30 天)")); tl.itemAt(0).widget().setStyleSheet("color: #88aaaa; font-size: 13px; font-weight: 700; background:transparent;")
        self.bi_trend = QTextEdit(); self.bi_trend.setReadOnly(True)
        self.bi_trend.setStyleSheet("background: rgba(4,12,14,220); color: #88ccaa; border: 1px solid rgba(0,150,120,30); border-radius: 8px; padding: 12px; font-size: 12px; font-family: 'Courier New', monospace;")
        tl.addWidget(self.bi_trend)
        l.addWidget(trend)

        l.addWidget(QLabel("详细数据"))
        self.bi_table = QTableWidget()
        self.bi_table.setColumnCount(5)
        self.bi_table.setHorizontalHeaderLabels(["日期","收入","订单","新增客户","客单价"])
        self.bi_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.bi_table.setStyleSheet(TABLE_STYLE)
        self.bi_table.setEditTriggers(QTableWidget.NoEditTriggers)
        l.addWidget(self.bi_table)

        self.tabs.addTab(tab, "数据大屏")

    def _load_all(self):
        try:
            total_revenue = total_orders = total_customers = 0

            db = os.path.join(DATA_DIR, "order.db")
            if os.path.exists(db):
                conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
                r = conn.execute("SELECT COUNT(*) as c, COALESCE(SUM(total_amount),0) as s FROM orders").fetchone()
                total_orders = r['c']; total_revenue = r['s']; conn.close()

            db = os.path.join(DATA_DIR, "customer.db")
            if os.path.exists(db):
                conn = sqlite3.connect(db); total_customers = conn.execute("SELECT COUNT(*) FROM customer").fetchone()[0]; conn.close()

            avg_order = total_revenue / total_orders if total_orders > 0 else 0

            self.kpi_labels["财务收入"].setText(f"¥{total_revenue:.0f}")
            self.kpi_labels["订单总数"].setText(str(total_orders))
            self.kpi_labels["客户数量"].setText(str(total_customers))

            self.bi_kpi["总营收"].setText(f"¥{total_revenue:.0f}")
            self.bi_kpi["订单数"].setText(str(total_orders))
            self.bi_kpi["客单价"].setText(f"¥{avg_order:.0f}")
            self.bi_kpi["新增客户"].setText(str(total_customers))

            self.bi_trend.setText("\n".join([
                f"  {'─' * 40}",
                f"  本月总营收: ¥{total_revenue:.2f}",
                f"  订单总数: {total_orders} 单",
                f"  客户数: {total_customers}",
                f"  平均客单价: ¥{avg_order:.2f}",
                f"  {'─' * 40}",
            ]))

            self.bi_table.setRowCount(1)
            self.bi_table.setItem(0, 0, QTableWidgetItem("当前汇总"))
            self.bi_table.setItem(0, 1, QTableWidgetItem(f"¥{total_revenue:.2f}"))
            self.bi_table.setItem(0, 2, QTableWidgetItem(str(total_orders)))
            self.bi_table.setItem(0, 3, QTableWidgetItem(str(total_customers)))
            self.bi_table.setItem(0, 4, QTableWidgetItem(f"¥{avg_order:.2f}"))

            self._load_finance()
        except Exception:
            pass