# `modules/data_center/report_window.py`

> 路径：`modules/data_center/report_window.py` | 行数：391


---


```python
"""
数据报表 · OBSERVATORY
QDialog：时间维度选择 + 统计类型 + 数据表格 + QPainter图表 + 导出CSV
"""
import os, sqlite3, csv
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QHeaderView, QTextEdit,
    QComboBox, QFrame, QFileDialog
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush,
    QLinearGradient, QRadialGradient, QFont, QPainterPath
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

# ═══════ QSS ═══════
QSS = """
    QDialog {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(4,12,16,245), stop:1 rgba(8,18,24,245));
        border: 2px solid rgba(0,180,150,50);
        border-radius: 14px;
    }
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
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background: #0a1618; color: #aacccc;
        selection-background-color: rgba(0,180,150,80);
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


class ChartWidget(QFrame):
    """QPainter 自绘宇宙主题柱状图/折线图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []          # list of (label, value)
        self._chart_type = "bar" # "bar" or "line"
        self.setMinimumHeight(200)
        self.setStyleSheet("background: rgba(6,16,18,230); border: 1px solid rgba(0,160,140,35); border-radius: 10px;")

    def set_data(self, data, chart_type="bar"):
        self._data = data
        self._chart_type = chart_type
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        margin_l, margin_r, margin_t, margin_b = 60, 30, 30, 50
        plot_w = w - margin_l - margin_r
        plot_h = h - margin_t - margin_b

        if plot_w <= 0 or plot_h <= 0:
            painter.end(); return

        # 背景网格
        painter.setPen(QPen(QColor(0, 120, 100, 25), 0.5))
        grid_lines = 5
        for i in range(grid_lines + 1):
            y = margin_t + plot_h * i / grid_lines
            painter.drawLine(margin_l, int(y), w - margin_r, int(y))

        # 计算最大值
        values = [v for _, v in self._data]
        vmax = max(values) if values else 1
        vmax = vmax * 1.15 if vmax > 0 else 1

        bar_w = min(plot_w / len(self._data) * 0.6, 40) if self._data else 20
        gap = plot_w / len(self._data) if self._data else 0

        points = []

        for i, (label, val) in enumerate(self._data):
            cx = margin_l + gap * i + gap / 2
            bar_h = (val / vmax) * plot_h if vmax > 0 else 0

            # 柱状图 / 折线图点
            if self._chart_type == "bar":
                x = cx - bar_w / 2
                y = margin_t + plot_h - bar_h

                # 渐变柱
                grad = QLinearGradient(x, y, x, margin_t + plot_h)
                grad.setColorAt(0, QColor(0, 200, 160, 180))
                grad.setColorAt(0.5, QColor(0, 160, 130, 140))
                grad.setColorAt(1, QColor(0, 100, 80, 80))
                painter.setPen(QPen(QColor(0, 200, 160, 100), 1))
                painter.setBrush(QBrush(grad))
                rect = QRectF(x, y, bar_w, bar_h)
                painter.drawRoundedRect(rect, 4, 4)

                # 顶部辉光
                glow = QRadialGradient(cx, y, bar_w * 0.8)
                glow.setColorAt(0, QColor(0, 255, 200, 80))
                glow.setColorAt(1, QColor(0, 0, 0, 0))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(glow))
                painter.drawEllipse(QRectF(cx - bar_w * 0.35, y - 6, bar_w * 0.7, 12))

                # 数值标签
                painter.setPen(QColor(170, 240, 220))
                painter.setFont(QFont("Menlo", 9))
                painter.drawText(QRectF(x - 5, y - 22, bar_w + 10, 18),
                                 Qt.AlignCenter, f"{val:.0f}")
            else:
                points.append(QPointF(cx, margin_t + plot_h - bar_h))

            # X 轴标签
            painter.setPen(QColor(100, 160, 150))
            painter.setFont(QFont("PingFang SC", 8))
            painter.drawText(QRectF(cx - 30, margin_t + plot_h + 6, 60, 30),
                             Qt.AlignHCenter | Qt.TextWordWrap, label)

        # 折线图
        if self._chart_type == "line" and len(points) >= 2:
            path = QPainterPath()
            path.moveTo(points[0])
            for pt in points[1:]:
                path.lineTo(pt)
            painter.setPen(QPen(QColor(0, 220, 180, 200), 2.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

            # 数据点
            for pt in points:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(0, 240, 200, 220)))
                painter.drawEllipse(pt, 4, 4)

        # Y 轴标签
        painter.setPen(QColor(80, 140, 130, 120))
        painter.setFont(QFont("Menlo", 8))
        for i in range(grid_lines + 1):
            val = vmax * (1 - i / grid_lines)
            y = margin_t + plot_h * i / grid_lines
            painter.drawText(QRectF(2, int(y) - 10, margin_l - 8, 20),
                             Qt.AlignRight | Qt.AlignVCenter, f"{val:.0f}")

        painter.end()


class ReportWindow(QDialog):
    """数据报表 · OBSERVATORY"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据报表 · OBSERVATORY")
        self.setMinimumSize(1000, 680)
        self.setStyleSheet(QSS)
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(22, 18, 22, 18)

        # ── 标题 ──
        title = QLabel("数据报表 · OBSERVATORY")
        title.setStyleSheet("color: #aaeecc; font-size: 18px; font-weight: 800; letter-spacing: 4px; background: transparent;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        # ── KPI 卡片 ──
        cards = QHBoxLayout()
        self.kpi_labels = {}
        for name, color in [("财务收入","#44cc88"),("会员总数","#4488ff"),("客户数量","#ffaa44"),("订单总数","#cc88ff"),("团队人数","#ff6688")]:
            card = QFrame()
            card.setStyleSheet(f"background: rgba(8,20,22,230); border: 1px solid rgba(0,160,140,30); border-radius: 10px; padding: 12px; min-width: 120px;")
            cll = QVBoxLayout(card); cll.setContentsMargins(0, 0, 0, 0)
            lb = QLabel(name)
            lb.setStyleSheet("color: #558877; font-size: 11px; background:transparent;")
            vl = QLabel("—")
            vl.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: 700; background:transparent;")
            cll.addWidget(lb); cll.addWidget(vl)
            self.kpi_labels[name] = vl
            cards.addWidget(card)
        cards.addStretch()
        layout.addLayout(cards)

        # ── 控制栏 ──
        ctrl = QHBoxLayout()

        ctrl.addWidget(QLabel("时间维度:"))
        self.time_dim = QComboBox()
        self.time_dim.addItems(["累计","今日","本周","本月","本年"])
        self.time_dim.setStyleSheet(INPUT_STYLE)
        self.time_dim.currentTextChanged.connect(self._refresh)
        ctrl.addWidget(self.time_dim)

        ctrl.addSpacing(20)
        ctrl.addWidget(QLabel("统计类型:"))
        self.report_type = QComboBox()
        self.report_type.addItems(["收入概览","订单明细","会员统计","客户分析","产品销售"])
        self.report_type.setStyleSheet(INPUT_STYLE)
        self.report_type.currentTextChanged.connect(self._refresh)
        ctrl.addWidget(self.report_type)

        ctrl.addStretch()
        export = QPushButton("导出CSV")
        export.setStyleSheet(BTN_PRIMARY)
        export.clicked.connect(self._export)
        ctrl.addWidget(export)
        layout.addLayout(ctrl)

        # ── 图表 ──
        self.chart = ChartWidget(self)
        layout.addWidget(self.chart, 1)

        # ── 数据表格 ──
        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table, 2)

        # ── 摘要 ──
        self.summary = QTextEdit()
        self.summary.setReadOnly(True)
        self.summary.setMaximumHeight(70)
        self.summary.setStyleSheet(INPUT_STYLE)
        layout.addWidget(self.summary)

    def _setup_table(self, headers):
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def _refresh(self):
        rtype = self.report_type.currentText()
        # 更新团队人数KPI（所有报表类型通用）
        self._load_team_kpi()
        try:
            if rtype == "收入概览":
                self._load_finance()
            elif rtype == "订单明细":
                self._load_orders()
            elif rtype == "会员统计":
                self._load_members()
            elif rtype == "客户分析":
                self._load_customers()
            elif rtype == "产品销售":
                self._load_products()
        except Exception as e:
            self.summary.setText(f"加载异常: {e}")

    def _load_team_kpi(self):
        """加载团队人数 KPI"""
        db = os.path.join(DATA_DIR, "staff.db")
        if os.path.exists(db):
            try:
                conn = sqlite3.connect(db)
                total = conn.execute("SELECT COUNT(*) FROM staff").fetchone()[0]
                conn.close()
                self.kpi_labels["团队人数"].setText(str(total))
            except Exception:
                self.kpi_labels["团队人数"].setText("—")
        else:
            self.kpi_labels["团队人数"].setText("—")

    def _load_finance(self):
        db = os.path.join(DATA_DIR, "finance.db")
        if not os.path.exists(db):
            self._setup_table(["提示"]); self.summary.setText("暂无财务数据"); return
        conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM finance ORDER BY id DESC LIMIT 50").fetchall(); conn.close()
        self._setup_table(["ID","类型","类别","金额","备注","日期"])
        self.table.setRowCount(len(rows))
        inc = exp = 0
        for i, r in enumerate(rows):
            for j, k in enumerate(['id', 'type', 'category', 'amount', 'note', 'created_at']):
                self.table.setItem(i, j, QTableWidgetItem(str(r[k]) if r[k] is not None else ""))
            amt = float(r['amount'] or 0)
            if r['type'] and '收入' in str(r['type']): inc += amt
            else: exp += amt
        self.kpi_labels["财务收入"].setText(f"¥{inc:.0f}")
        self.summary.setText(f"总收入: ¥{inc:.2f} | 总支出: ¥{exp:.2f} | 利润: ¥{inc - exp:.2f}")
        self.chart.set_data([("收入", inc), ("支出", exp), ("利润", inc - exp)], "bar")

    def _load_orders(self):
        db = os.path.join(DATA_DIR, "order.db")
        if not os.path.exists(db): self._setup_table(["提示"]); self.summary.setText("暂无订单"); return
        conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 50").fetchall()
        t = conn.execute("SELECT COUNT(*), COALESCE(SUM(total_amount),0) FROM orders").fetchone(); conn.close()
        self._setup_table(["ID","订单号","客户","金额","时间","状态"])
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, k in enumerate(['id', 'order_no', 'customer_name', 'total_amount', 'created_at', 'status']):
                self.table.setItem(i, j, QTableWidgetItem(str(r[k]) if r[k] is not None else ""))
        self.kpi_labels["订单总数"].setText(str(t[0]))
        self.summary.setText(f"订单总数: {t[0]} | 总金额: ¥{t[1]:.2f}")
        self.chart.set_data([("订单数", t[0]), ("总金额(元)", int(t[1]))], "bar")

    def _load_members(self):
        db = os.path.join(DATA_DIR, "member.db")
        if not os.path.exists(db): self._setup_table(["提示"]); self.summary.setText("暂无会员"); return
        conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM member ORDER BY id DESC LIMIT 50").fetchall()
        stats = conn.execute("SELECT level, COUNT(*) as c FROM member GROUP BY level").fetchall(); conn.close()
        self._setup_table(["ID","姓名","电话","等级","积分","VIP到期","状态"])
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, k in enumerate(['id', 'name', 'phone', 'level', 'points', 'vip_expire', 'status']):
                self.table.setItem(i, j, QTableWidgetItem(str(r[k]) if r[k] is not None else ""))
        total = sum(s['c'] for s in stats)
        self.kpi_labels["会员总数"].setText(str(total))
        levels = " | ".join([f"{s['level']}:{s['c']}" for s in stats])
        self.summary.setText(f"总计: {total} | {levels}")
        chart_data = [(s['level'], s['c']) for s in stats]
        self.chart.set_data(chart_data, "bar")

    def _load_customers(self):
        db = os.path.join(DATA_DIR, "customer.db")
        if not os.path.exists(db): self._setup_table(["提示"]); self.summary.setText("暂无客户"); return
        conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM customer ORDER BY id DESC LIMIT 50").fetchall()
        total = conn.execute("SELECT COUNT(*) FROM customer").fetchone()[0]; conn.close()
        self._setup_table(["ID","姓名","电话","公司","等级","备注"])
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, k in enumerate(['id', 'name', 'phone', 'company', 'level', 'note']):
                self.table.setItem(i, j, QTableWidgetItem(str(r[k]) if r[k] is not None else ""))
        self.kpi_labels["客户数量"].setText(str(total))
        self.summary.setText(f"客户总数: {total}")
        self.chart.set_data([("客户总数", total)], "bar")

    def _load_products(self):
        db = os.path.join(DATA_DIR, "product.db")
        if not os.path.exists(db): self._setup_table(["提示"]); self.summary.setText("暂无产品"); return
        conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM product ORDER BY id DESC LIMIT 50").fetchall()
        total = conn.execute("SELECT COUNT(*) FROM product").fetchone()[0]; conn.close()
        self._setup_table(["ID","名称","类别","价格","库存","状态"])
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, k in enumerate(['id', 'name', 'category', 'price', 'stock', 'status']):
                self.table.setItem(i, j, QTableWidgetItem(str(r[k]) if r[k] is not None else ""))
        self.summary.setText(f"产品总数: {total}")
        self.chart.set_data([("产品总数", total)], "bar")

    def _export(self):
        fp, _ = QFileDialog.getSaveFileName(self, "导出", f"report_{datetime.now().strftime('%Y%m%d')}.csv", "CSV (*.csv)")
        if not fp: return
        with open(fp, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f)
            headers = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
            w.writerow(headers)
            for row in range(self.table.rowCount()):
                w.writerow([self.table.item(row, c).text() if self.table.item(row, c) else "" for c in range(self.table.columnCount())])
        self.summary.setText(f"已导出: {fp}")
```
