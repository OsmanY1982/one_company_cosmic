"""
智能中心 · NEURAL — 独立子窗口
统计卡片（读取 order.db）+ 数据表格 + 分析报告
"""
import os, sqlite3
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QHeaderView, QTextEdit, QWidget, QFrame,
)
from PyQt5.QtCore import Qt

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

TAB_STYLE = """
    QTabWidget::pane {
        background: transparent;
        border: 1px solid rgba(170,80,255,30);
        border-radius: 10px;
    }
    QTabBar::tab {
        background: rgba(16,8,28,220);
        color: #9988bb; padding: 10px 22px;
        border: none; border-bottom: 2px solid transparent;
        font-size: 12px; font-weight: 600; letter-spacing: 2px; min-width: 70px;
    }
    QTabBar::tab:selected {
        color: #ddaaff;
        border-bottom: 2px solid #aa44ff;
        background: rgba(24,12,38,235);
    }
    QTabBar::tab:hover { color: #cc88ee; }
"""
TABLE_STYLE = """
    QTableWidget {
        background: rgba(12,6,22,220); color: #ccbbdd;
        border: 1px solid rgba(140,60,200,30); border-radius: 8px;
        gridline-color: rgba(60,20,100,25); font-size: 12px;
        selection-background-color: rgba(150,60,220,60);
    }
    QTableWidget::item { padding: 5px 10px; }
    QHeaderView::section {
        background: rgba(20,10,32,230); color: #aa99cc; padding: 8px 10px;
        border: none; border-bottom: 1px solid rgba(170,80,255,40);
        font-weight: 700; font-size: 11px; letter-spacing: 1px;
    }
"""
INPUT_STYLE = """
    QTextEdit {
        background: rgba(12,6,22,230); color: #ccbbdd;
        border: 1px solid rgba(170,80,255,35); border-radius: 6px;
        padding: 6px 10px; font-size: 12px;
    }
"""
BTN_PRIMARY = """
    QPushButton {
        background: rgba(150,60,220,40); color: #ddaaff;
        border: 1px solid rgba(170,80,240,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(170,80,240,70); }
"""


class AiCenterWindow(QDialog):
    """智能中心 · NEURAL"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("智能中心 · NEURAL")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("background: rgba(10,5,20,240);")
        self._build_ui()
        self._load_all()

    def _build_ui(self):
        l = QVBoxLayout(self)
        l.setSpacing(10)
        l.setContentsMargins(16, 12, 16, 12)

        cards = QHBoxLayout()
        self.overview_labels = {}
        for name, color in [("订单总数", "#4488ff"), ("产品数量", "#44cc88"), ("订单金额", "#ffaa44"), ("最近订单", "#cc88ff")]:
            card = QFrame()
            card.setStyleSheet(f"background: rgba(16,8,28,230); border: 1px solid rgba(170,80,255,30); border-radius: 10px; padding: 12px; min-width: 140px;")
            cll = QVBoxLayout(card)
            cll.setContentsMargins(0, 0, 0, 0)
            lb = QLabel(name)
            lb.setStyleSheet("color: #776699; font-size: 11px; background:transparent;")
            vl = QLabel("—")
            vl.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: 700; background:transparent;")
            cll.addWidget(lb)
            cll.addWidget(vl)
            self.overview_labels[name] = vl
            cards.addWidget(card)
        cards.addStretch()
        l.addLayout(cards)

        inner = QTabWidget()
        inner.setStyleSheet(TAB_STYLE)

        # 智能总览
        ow = QWidget()
        ol = QVBoxLayout(ow)
        ol.setContentsMargins(10, 10, 10, 10)
        self.overview_table = QTableWidget()
        self.overview_table.setColumnCount(5)
        self.overview_table.setHorizontalHeaderLabels(["ID", "订单号", "客户", "金额", "时间"])
        self.overview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.overview_table.setStyleSheet(TABLE_STYLE)
        self.overview_table.setEditTriggers(QTableWidget.NoEditTriggers)
        ol.addWidget(self.overview_table)
        inner.addTab(ow, "智能总览")

        # 数据分析
        aw = QWidget()
        al = QVBoxLayout(aw)
        al.setContentsMargins(10, 10, 10, 10)
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setStyleSheet(INPUT_STYLE)
        al.addWidget(self.analysis_text)
        btn = QPushButton("刷新分析")
        btn.setStyleSheet(BTN_PRIMARY)
        btn.clicked.connect(self._run_analysis)
        al.addWidget(btn, alignment=Qt.AlignLeft)
        inner.addTab(aw, "数据分析")

        # 智能报表
        rw = QWidget()
        rl = QVBoxLayout(rw)
        rl.setContentsMargins(10, 10, 10, 10)
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setStyleSheet(INPUT_STYLE)
        rl.addWidget(self.report_text)
        inner.addTab(rw, "智能报表")

        # 业务洞察
        iw = QWidget()
        il = QVBoxLayout(iw)
        il.setContentsMargins(10, 10, 10, 10)
        self.insight_text = QTextEdit()
        self.insight_text.setReadOnly(True)
        self.insight_text.setStyleSheet(INPUT_STYLE)
        il.addWidget(self.insight_text)
        inner.addTab(iw, "业务洞察")

        l.addWidget(inner)

    def _run_analysis(self):
        db_path = os.path.join(DATA_DIR, "order.db")
        if not os.path.exists(db_path):
            self.analysis_text.setText("暂无订单数据。")
            return
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        total = conn.execute("SELECT COUNT(*) as c, COALESCE(SUM(total_amount),0) as s FROM orders").fetchone()
        top = conn.execute("SELECT product_name, COUNT(*) as cnt FROM orders GROUP BY product_name ORDER BY cnt DESC LIMIT 5").fetchall()
        conn.close()
        lines = [f"订单总数: {total['c']} | 总金额: ¥{total['s']:.2f}", "", "热门产品 TOP 5:"]
        for i, r in enumerate(top, 1):
            lines.append(f"  {i}. {r['product_name']}: {r['cnt']} 单")
        self.analysis_text.setText("\n".join(lines))

    def _load_all(self):
        try:
            db_path = os.path.join(DATA_DIR, "order.db")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                total = conn.execute("SELECT COUNT(*) as c, COALESCE(SUM(total_amount),0) as s FROM orders").fetchone()
                prod_db = os.path.join(DATA_DIR, "product.db")
                prod_cnt = 0
                if os.path.exists(prod_db):
                    pc = sqlite3.connect(prod_db)
                    prod_cnt = pc.execute("SELECT COUNT(*) FROM product").fetchone()[0]
                    pc.close()
                recent = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 10").fetchall()
                conn.close()

                self.overview_labels["订单总数"].setText(str(total['c']))
                self.overview_labels["订单金额"].setText(f"\u00a5{total['s']:.0f}")
                self.overview_labels["产品数量"].setText(str(prod_cnt))
                self.overview_labels["最近订单"].setText("已加载")

                self.overview_table.setRowCount(len(recent))
                for i, r in enumerate(recent):
                    for j, k in enumerate(['id', 'order_no', 'customer_name', 'total_amount', 'created_at']):
                        self.overview_table.setItem(i, j, QTableWidgetItem(str(r[k]) if r[k] is not None else ""))

                self._run_analysis()
                self.report_text.setText(f"报表数据已加载。订单总数: {total['c']}, 总金额: \u00a5{total['s']:.2f}")
                self.insight_text.setText(f"业务洞察: 系统检测到 {total['c']} 条订单记录。热门产品分析已就绪。")
        except Exception:
            pass