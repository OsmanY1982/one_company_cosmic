# `modules/intelligence/ai_center_window.py`

> 路径：`modules/intelligence/ai_center_window.py` | 行数：355


---


```python
"""
智能中心 · NEURAL — 独立子窗口
统计卡片（读取 order.db + product.db）+ 数据分析 + 智能报表 + 业务洞察
轨道式独立子窗口布局，不使用 QTabWidget
"""
import traceback
import os, sqlite3
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QHeaderView, QTextEdit, QWidget, QFrame, QScrollArea,
)
from PyQt5.QtCore import Qt

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

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
SECTION_TITLE = "color: #aa88dd; font-size: 13px; font-weight: 700; background: transparent; padding: 4px 0;"
SECTION_FRAME = "background: rgba(12,6,22,200); border: 1px solid rgba(170,80,255,25); border-radius: 10px;"


class AICenterWindow(QDialog):
    """智能中心 · NEURAL — 轨道式独立子窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("智能中心 · NEURAL")
        self.setMinimumSize(900, 750)
        self.setStyleSheet("background: rgba(10,5,20,240);")
        self._build_ui()
        self._load_all()

    def _section_title(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(SECTION_TITLE)
        return lbl

    def _section_frame(self, spacing=8):
        f = QFrame()
        f.setStyleSheet(SECTION_FRAME)
        l = QVBoxLayout(f)
        l.setSpacing(spacing)
        l.setContentsMargins(12, 10, 12, 10)
        return f, l

    def _build_ui(self):
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        l = QVBoxLayout(scroll_content)
        l.setSpacing(10)
        l.setContentsMargins(16, 12, 16, 12)

        # ── 顶部KPI卡片 ──
        cards = QHBoxLayout()
        self.overview_labels = {}
        for name, color, icon in [
            ("订单总数", "#4488ff", "📦"), ("产品数量", "#44cc88", "🏷"),
            ("订单金额", "#ffaa44", "💰"), ("最近订单", "#cc88ff", "🕐")
        ]:
            card = QFrame()
            card.setStyleSheet(
                f"background: rgba(16,8,28,230); border: 1px solid rgba(170,80,255,30);"
                f" border-radius: 10px; padding: 12px; min-width: 140px;"
            )
            cll = QVBoxLayout(card)
            cll.setContentsMargins(0, 0, 0, 0)
            lb = QLabel(f"{icon}  {name}")
            lb.setStyleSheet("color: #776699; font-size: 11px; background:transparent;")
            vl = QLabel("—")
            vl.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: 700; background:transparent;")
            cll.addWidget(lb)
            cll.addWidget(vl)
            self.overview_labels[name] = vl
            cards.addWidget(card)
        cards.addStretch()

        # 扫码工具快捷入口
        btn_scan = QPushButton("📷  扫码工具")
        btn_scan.setStyleSheet(
            "background: rgba(160,80,240,50); color: #ddaaff;"
            "border: 1px solid rgba(180,100,255,60); border-radius: 16px;"
            "padding: 8px 20px; font-size: 12px; font-weight: 600;"
        )
        btn_scan.setCursor(Qt.PointingHandCursor)
        btn_scan.clicked.connect(self._open_scan)
        cards.addWidget(btn_scan)

        l.addLayout(cards)

        # ── 第1区：智能总览表格 ──
        f1, fl1 = self._section_frame()
        fl1.addWidget(self._section_title("智能总览"))
        self.overview_table = QTableWidget()
        self.overview_table.setColumnCount(5)
        self.overview_table.setHorizontalHeaderLabels(["ID", "订单号", "客户", "金额", "时间"])
        self.overview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.overview_table.setStyleSheet(TABLE_STYLE)
        self.overview_table.setEditTriggers(QTableWidget.NoEditTriggers)
        fl1.addWidget(self.overview_table)
        l.addWidget(f1)

        # ── 第2区：数据分析 ──
        f2, fl2 = self._section_frame()
        header2 = QHBoxLayout()
        header2.addWidget(self._section_title("数据分析"))
        header2.addStretch()
        btn = QPushButton("刷新分析")
        btn.setStyleSheet(BTN_PRIMARY)
        btn.clicked.connect(self._run_analysis)
        header2.addWidget(btn)
        fl2.addLayout(header2)
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setMaximumHeight(200)
        self.analysis_text.setStyleSheet(INPUT_STYLE)
        fl2.addWidget(self.analysis_text)
        l.addWidget(f2)

        # ── 第3区：智能报表 ──
        f3, fl3 = self._section_frame()
        fl3.addWidget(self._section_title("智能报表"))
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setMaximumHeight(180)
        self.report_text.setStyleSheet(INPUT_STYLE)
        fl3.addWidget(self.report_text)
        l.addWidget(f3)

        # ── 第4区：业务洞察 ──
        f4, fl4 = self._section_frame()
        fl4.addWidget(self._section_title("业务洞察"))
        self.insight_text = QTextEdit()
        self.insight_text.setReadOnly(True)
        self.insight_text.setMaximumHeight(200)
        self.insight_text.setStyleSheet(INPUT_STYLE)
        fl4.addWidget(self.insight_text)
        l.addWidget(f4)

        l.addStretch()
        scroll.setWidget(scroll_content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _open_scan(self):
        """打开扫码工具"""
        from modules.intelligence.scan_window import ScanWindow
        dlg = ScanWindow(self)
        dlg.exec_()

    def _run_analysis(self):
        db_path = os.path.join(DATA_DIR, "order.db")
        if not os.path.exists(db_path):
            self.analysis_text.setText("暂无订单数据。")
            return
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        total = conn.execute("SELECT COUNT(*) as c, COALESCE(SUM(total_amount),0) as s FROM orders").fetchone()
        top = conn.execute(
            "SELECT product_name, COUNT(*) as cnt FROM orders "
            "GROUP BY product_name ORDER BY cnt DESC LIMIT 5"
        ).fetchall()
        # 月度趋势
        monthly = conn.execute(
            "SELECT strftime('%Y-%m', created_at) as m, COUNT(*) as cnt, "
            "COALESCE(SUM(total_amount),0) as amt FROM orders "
            "GROUP BY m ORDER BY m DESC LIMIT 6"
        ).fetchall()
        conn.close()

        lines = [
            f"订单总数: {total['c']}   |   总金额: ¥{total['s']:.2f}",
            f"客单价: ¥{total['s'] / total['c']:.2f}" if total['c'] > 0 else "客单价: —",
            "",
            "◆ 热门产品 TOP 5:",
        ]
        for i, r in enumerate(top, 1):
            lines.append(f"  {i}. {r['product_name']}: {r['cnt']} 单")
        lines.append("")
        lines.append("◆ 月度趋势:")
        for r in reversed(monthly):
            lines.append(f"  {r['m']}: {r['cnt']}单 / ¥{r['amt']:.2f}")
        self.analysis_text.setText("\n".join(lines))

    def _load_all(self):
        try:
            db_path = os.path.join(DATA_DIR, "order.db")
            if not os.path.exists(db_path):
                for k in self.overview_labels:
                    self.overview_labels[k].setText("0")
                self.overview_table.setRowCount(0)
                self.analysis_text.setText("暂无订单数据，请先在业务模块录入订单。")
                self.report_text.setText("暂无数据可生成报表。")
                self.insight_text.setText("暂无数据可用。录入订单后系统将自动分析业务趋势。")
                return

            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            total = conn.execute(
                "SELECT COUNT(*) as c, COALESCE(SUM(total_amount),0) as s FROM orders"
            ).fetchone()
            prod_db = os.path.join(DATA_DIR, "product.db")
            prod_cnt = 0
            if os.path.exists(prod_db):
                pc = sqlite3.connect(prod_db)
                prod_cnt = pc.execute("SELECT COUNT(*) FROM product").fetchone()[0]
                pc.close()
            recent = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 10").fetchall()

            # 产品销量排名
            top_products = conn.execute(
                "SELECT product_name, COUNT(*) as cnt, COALESCE(SUM(total_amount),0) as amt "
                "FROM orders GROUP BY product_name ORDER BY cnt DESC LIMIT 5"
            ).fetchall()

            # 客户排名
            top_customers = conn.execute(
                "SELECT customer_name, COUNT(*) as cnt, COALESCE(SUM(total_amount),0) as amt "
                "FROM orders GROUP BY customer_name ORDER BY amt DESC LIMIT 5"
            ).fetchall()

            # 月度一览
            monthly = conn.execute(
                "SELECT strftime('%Y-%m', created_at) as m, COUNT(*) as cnt, "
                "COALESCE(SUM(total_amount),0) as amt FROM orders "
                "GROUP BY m ORDER BY m DESC LIMIT 6"
            ).fetchall()
            conn.close()

            # ── 更新KPI卡片 ──
            self.overview_labels["订单总数"].setText(str(total['c']))
            self.overview_labels["订单金额"].setText(f"\u00a5{total['s']:.0f}")
            self.overview_labels["产品数量"].setText(str(prod_cnt))
            self.overview_labels["最近订单"].setText("已加载")

            # ── 智能总览表格 ──
            self.overview_table.setRowCount(len(recent))
            for i, r in enumerate(recent):
                for j, k in enumerate(['id', 'order_no', 'customer_name', 'total_amount', 'created_at']):
                    self.overview_table.setItem(i, j, QTableWidgetItem(
                        str(r[k]) if r[k] is not None else ""
                    ))

            # ── 数据分析 ──
            self._run_analysis()

            # ── 智能报表（真实数据） ──
            report_lines = [
                f"{'═' * 52}",
                f"  OPCclaw 智能中心 · 数据报表",
                f"{'═' * 52}",
                f"",
                f"  报告时间: {self._now_str()}",
                f"  订单总数: {total['c']}        总金额: ¥{total['s']:,.2f}",
                f"  产品种类: {prod_cnt}         客单价: ¥{total['s'] / total['c']:.2f}" if total['c'] > 0 else f"  产品种类: {prod_cnt}",
                f"",
                f"  ── 产品销量 TOP 5 ──",
            ]
            for i, r in enumerate(top_products, 1):
                report_lines.append(
                    f"    {i}. {r['product_name']:12s}  销量 {r['cnt']:4d}  营收 ¥{r['amt']:,.2f}"
                )
            report_lines.append("")
            report_lines.append("  ── 客户贡献 TOP 5 ──")
            for i, r in enumerate(top_customers, 1):
                report_lines.append(
                    f"    {i}. {r['customer_name']:12s}  订单 {r['cnt']:4d}  消费 ¥{r['amt']:,.2f}"
                )
            report_lines.append(f"")
            report_lines.append(f"{'═' * 52}")
            self.report_text.setText("\n".join(report_lines))

            # ── 业务洞察（真实推理） ──
            insight_lines = []
            if total['c'] > 0:
                avg = total['s'] / total['c']
                if avg > 1000:
                    insight_lines.append(f"◆ 客单价 ¥{avg:.2f} — 高客单价模式，建议关注复购率与VIP服务。")
                elif avg > 300:
                    insight_lines.append(f"◆ 客单价 ¥{avg:.2f} — 中等客单价，可尝试套餐组合提升单笔价值。")
                else:
                    insight_lines.append(f"◆ 客单价 ¥{avg:.2f} — 低客单价，建议通过满减/包邮策略提升客单。")

                if len(monthly) >= 2:
                    cur = monthly[0]['amt']
                    prev = monthly[1]['amt']
                    if prev > 0:
                        change = (cur - prev) / prev * 100
                        insight_lines.append(
                            f"◆ 月度营收环比 {'增长' if change >= 0 else '下降'} {abs(change):.1f}%"
                            f" (本月¥{cur:.0f} vs 上月¥{prev:.0f})"
                        )

                if top_products:
                    insight_lines.append(
                        f"◆ 核心产品: 「{top_products[0]['product_name']}」"
                        f" 占比 {top_products[0]['cnt'] / total['c'] * 100:.0f}%，"
                        f"累计 ¥{top_products[0]['amt']:,.2f}"
                    )

                customer_db = os.path.join(DATA_DIR, "customer.db")
                if os.path.exists(customer_db):
                    cc = sqlite3.connect(customer_db)
                    cust_total = cc.execute("SELECT COUNT(*) FROM customer").fetchone()[0]
                    cc.close()
                    insight_lines.append(
                        f"◆ 客户池: {cust_total} 人，活跃订单 {total['c']} 单，"
                        f"建议持续运营老客户。"
                    )

            if not insight_lines:
                insight_lines.append("◆ 数据量不足，录入更多业务数据后系统将自动生成洞察。")

            self.insight_text.setText("\n".join(insight_lines))

        except Exception:
            traceback.print_exc()

    @staticmethod
    def _now_str():
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

```
