"""
业务管理模块 — 宇宙主题
订单 / 产品 / 客户 / 财务 四大板块
功能代码从旧项目 one_company_desktop 提取，UI 完全重写
"""
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QHeaderView, QMessageBox, QDialog, QFormLayout, QLineEdit,
    QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QLinearGradient, QFont, QPainterPath, QConicalGradient
)

from core.cosmic import CosmicBackground, ACCENT_CYAN
from core.data import init_all_dbs, ORDER_DB, PRODUCT_DB, CUSTOMER_DB, FINANCE_DB

ACCENT_BLUE = QColor(68, 136, 255)
ACCENT_GREEN = QColor(0, 204, 170)

# ── 宇宙样式常量 ──
DIALOG_BG = """
    QDialog {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #080e1a, stop:1 #101a2e);
        border: 1px solid rgba(68,136,255,40);
        border-radius: 12px;
    }
"""
TABLE_STYLE = """
    QTableWidget {
        background: rgba(8,14,26,220);
        color: #ccddef;
        border: 1px solid rgba(50,100,170,35);
        border-radius: 8px;
        gridline-color: rgba(30,60,100,25);
        font-size: 12px;
        selection-background-color: rgba(68,136,255,70);
        selection-color: white;
    }
    QTableWidget::item { padding: 6px 10px; }
    QHeaderView::section {
        background: rgba(12,22,40,230);
        color: #8899bb;
        padding: 8px 10px;
        border: none;
        border-bottom: 1px solid rgba(68,136,255,40);
        font-weight: 700;
        font-size: 11px;
        letter-spacing: 1px;
    }
    QScrollBar:vertical { background: rgba(8,14,26,150); width: 5px; border-radius: 2px; }
    QScrollBar::handle:vertical { background: rgba(70,130,200,40); border-radius: 2px; min-height: 16px; }
"""
TAB_STYLE = """
    QTabWidget::pane {
        background: transparent;
        border: 1px solid rgba(50,100,170,30);
        border-radius: 10px;
    }
    QTabBar::tab {
        background: rgba(10,18,32,200);
        color: #667788;
        padding: 10px 24px;
        border: none;
        border-bottom: 2px solid transparent;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 2px;
        min-width: 80px;
    }
    QTabBar::tab:selected {
        color: #88bbff;
        border-bottom: 2px solid #4488ff;
        background: rgba(16,28,50,230);
    }
    QTabBar::tab:hover:!selected { color: #7799bb; background: rgba(14,22,38,220); }
"""
BTN_PRIMARY = """
    QPushButton {
        background: rgba(68,136,255,35);
        color: #88bbff;
        border: 1px solid rgba(68,136,255,50);
        border-radius: 14px;
        padding: 6px 18px;
        font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(68,136,255,65); color: #aaddff; }
"""
BTN_DANGER = """
    QPushButton {
        background: rgba(220,60,60,30);
        color: #ee8888;
        border: 1px solid rgba(220,60,60,45);
        border-radius: 14px;
        padding: 6px 18px;
        font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(220,60,60,55); }
"""
INPUT_STYLE = """
    QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
        background: rgba(10,18,34,220);
        color: #aaccee;
        border: 1px solid rgba(50,110,180,40);
        border-radius: 8px;
        padding: 7px 12px;
        font-size: 12px;
    }
    QLineEdit:focus, QTextEdit:focus { border: 1px solid rgba(68,136,255,140); }
    QComboBox::drop-down { border: none; width: 20px; }
    QComboBox QAbstractItemView {
        background: rgba(10,18,34,240);
        color: #aaccee;
        selection-background-color: rgba(68,136,255,60);
        border: 1px solid rgba(50,110,180,40);
    }
"""
LABEL_STYLE = "color: #8899bb; font-size: 11px; background: transparent;"
GROUP_STYLE = """
    QGroupBox {
        color: #8899bb;
        border: 1px solid rgba(50,100,170,25);
        border-radius: 10px;
        margin-top: 10px;
        padding-top: 18px;
        font-size: 12px;
        font-weight: 600;
    }
    QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
"""


class _EntityDialog(QDialog):
    """通用实体的新增/编辑对话框 — 宇宙风格"""

    def __init__(self, title: str, fields: list, initial: dict = None, parent=None):
        """
        fields: [(key, label, widget_type, options), ...]
        widget_type: 'text' | 'num' | 'float' | 'combo' | 'area'
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self.setStyleSheet(DIALOG_BG)
        self._result = None
        self._fields_meta = fields

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 20)

        # 标题
        hl = QLabel(f"◆ {title}")
        hl.setStyleSheet("color: #88bbff; font-size: 16px; font-weight: 700; letter-spacing: 3px; background: transparent;")
        layout.addWidget(hl)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self._widgets = {}
        for key, label, wtype, opts in fields:
            lbl = QLabel(label)
            lbl.setStyleSheet(LABEL_STYLE)

            if wtype == 'combo':
                w = QComboBox()
                w.addItems(opts or [])
                w.setStyleSheet(INPUT_STYLE)
            elif wtype == 'num':
                w = QSpinBox()
                w.setRange(opts[0] if opts else 0, opts[1] if len(opts) > 1 else 99999)
                w.setStyleSheet(INPUT_STYLE)
            elif wtype == 'float':
                w = QDoubleSpinBox()
                w.setRange(0, 9999999)
                w.setDecimals(2)
                w.setStyleSheet(INPUT_STYLE)
            elif wtype == 'area':
                w = QTextEdit()
                w.setMaximumHeight(80)
                w.setStyleSheet(INPUT_STYLE)
            else:
                w = QLineEdit()
                w.setStyleSheet(INPUT_STYLE)

            if initial and key in initial:
                val = initial[key]
                if wtype == 'combo':
                    idx = w.findText(str(val))
                    if idx >= 0:
                        w.setCurrentIndex(idx)
                elif wtype == 'num':
                    w.setValue(int(val) if val else 0)
                elif wtype == 'float':
                    w.setValue(float(val) if val else 0)
                elif wtype == 'area':
                    w.setPlainText(str(val) if val else '')
                else:
                    w.setText(str(val) if val else '')

            self._widgets[key] = w
            form.addRow(lbl, w)

        layout.addLayout(form)

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = QPushButton("取消")
        cancel.setStyleSheet(BTN_DANGER)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)

        ok = QPushButton("确认")
        ok.setStyleSheet(BTN_PRIMARY)
        ok.clicked.connect(self._on_ok)
        btn_row.addWidget(ok)
        layout.addLayout(btn_row)

    def _on_ok(self):
        self._result = {}
        for key, label, wtype, _ in self._fields_meta:
            w = self._widgets[key]
            if wtype in ('combo',):
                self._result[key] = w.currentText()
            elif wtype == 'num':
                self._result[key] = w.value()
            elif wtype == 'float':
                self._result[key] = w.value()
            elif wtype == 'area':
                self._result[key] = w.toPlainText()
            else:
                self._result[key] = w.text()
        self.accept()

    def get_result(self) -> dict:
        return self._result


class BusinessWindow(QMainWindow):
    """业务管理星球 — 订单/产品/客户/财务"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("一人公司 — 业务管理 · Orbit Station")
        self.setMinimumSize(960, 640)

        init_all_dbs()

        # 背景
        self._cosmic = CosmicBackground()
        self.setCentralWidget(self._cosmic)

        self._hud = QWidget(self._cosmic)
        self._hud.setAttribute(Qt.WA_TranslucentBackground)
        self._hud.setGeometry(0, 0, 960, 640)

        self._build_ui()
        self._refresh_all()

        # 球体闪烁
        self._glow_t = 0
        self._glow = QTimer(self)
        self._glow.timeout.connect(self._tick_glow)
        self._glow.start(50)
        self._hud.paintEvent = self._paint_hud

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        self._cosmic.setGeometry(0, 0, self.width(), self.height())

    def _build_ui(self):
        layout = QVBoxLayout(self._hud)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)

        # 标题栏
        head = QHBoxLayout()
        ic = QLabel("●")
        ic.setStyleSheet("color: #4488ff; font-size: 18px; background: transparent;")
        head.addWidget(ic)
        title = QLabel("业务管理 · 轨道站")
        title.setStyleSheet("color: #ddeeff; font-size: 18px; font-weight: 700; letter-spacing: 3px; background: transparent;")
        head.addWidget(title)
        head.addStretch()

        self._status_lbl = QLabel("就绪")
        self._status_lbl.setStyleSheet("color: #556688; font-size: 10px; background: transparent; letter-spacing: 2px;")
        head.addWidget(self._status_lbl)
        layout.addLayout(head)

        # 标签页
        tabs = QTabWidget()
        tabs.setStyleSheet(TAB_STYLE)
        tabs.addTab(self._build_order_tab(), "订 单")
        tabs.addTab(self._build_product_tab(), "产 品")
        tabs.addTab(self._build_customer_tab(), "客 户")
        tabs.addTab(self._build_finance_tab(), "财 务")
        layout.addWidget(tabs, 1)

        # 底部关闭
        close_btn = QPushButton("关闭舱门")
        close_btn.setFixedWidth(120)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(16,28,50,180);
                color: #556688;
                border: 1px solid rgba(60,80,120,40);
                border-radius: 14px;
                padding: 6px 0;
                font-size: 11px;
            }
            QPushButton:hover { color: #8899bb; border: 1px solid rgba(80,100,140,70); }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

    # ════════════════ 订单 Tab ════════════════

    def _build_order_tab(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        v = QVBoxLayout(w)
        v.setSpacing(8)
        v.setContentsMargins(10, 10, 10, 10)

        tb = QHBoxLayout()
        add_btn = QPushButton("+ 新订单")
        add_btn.setStyleSheet(BTN_PRIMARY)
        add_btn.clicked.connect(self._add_order)
        tb.addWidget(add_btn)
        tb.addStretch()
        export_btn = QPushButton("导出")
        export_btn.setStyleSheet(BTN_PRIMARY.replace("4488ff", "8899bb").replace("68,136,255", "100,120,150"))
        export_btn.clicked.connect(self._export_orders)
        tb.addWidget(export_btn)
        v.addLayout(tb)

        self._order_table = QTableWidget()
        self._order_table.setColumnCount(9)
        self._order_table.setHorizontalHeaderLabels([
            "ID", "订单号", "客户", "产品", "数量", "单价", "总金额", "状态", "日期"
        ])
        self._order_table.setStyleSheet(TABLE_STYLE)
        self._order_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._order_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._order_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._order_table.doubleClicked.connect(self._edit_order)
        v.addWidget(self._order_table, 1)
        return w

    # ════════════════ 产品 Tab ════════════════

    def _build_product_tab(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        v = QVBoxLayout(w)
        v.setSpacing(8)
        v.setContentsMargins(10, 10, 10, 10)

        tb = QHBoxLayout()
        add_btn = QPushButton("+ 新产品")
        add_btn.setStyleSheet(BTN_PRIMARY)
        add_btn.clicked.connect(self._add_product)
        tb.addWidget(add_btn)
        tb.addStretch()
        del_btn = QPushButton("删除")
        del_btn.setStyleSheet(BTN_DANGER)
        del_btn.clicked.connect(self._delete_product)
        tb.addWidget(del_btn)
        v.addLayout(tb)

        self._product_table = QTableWidget()
        self._product_table.setColumnCount(9)
        self._product_table.setHorizontalHeaderLabels([
            "ID", "产品名", "分类", "售价", "成本", "库存", "单位", "状态", "备注"
        ])
        self._product_table.setStyleSheet(TABLE_STYLE)
        self._product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._product_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._product_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._product_table.doubleClicked.connect(self._edit_product)
        v.addWidget(self._product_table, 1)
        return w

    # ════════════════ 客户 Tab ════════════════

    def _build_customer_tab(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        v = QVBoxLayout(w)
        v.setSpacing(8)
        v.setContentsMargins(10, 10, 10, 10)

        tb = QHBoxLayout()
        add_btn = QPushButton("+ 新客户")
        add_btn.setStyleSheet(BTN_PRIMARY)
        add_btn.clicked.connect(self._add_customer)
        tb.addWidget(add_btn)
        tb.addStretch()
        v.addLayout(tb)

        self._customer_table = QTableWidget()
        self._customer_table.setColumnCount(8)
        self._customer_table.setHorizontalHeaderLabels([
            "ID", "姓名", "公司", "电话", "邮箱", "级别", "备注", "日期"
        ])
        self._customer_table.setStyleSheet(TABLE_STYLE)
        self._customer_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._customer_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._customer_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._customer_table.doubleClicked.connect(self._edit_customer)
        v.addWidget(self._customer_table, 1)
        return w

    # ════════════════ 财务 Tab ════════════════

    def _build_finance_tab(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        v = QVBoxLayout(w)
        v.setSpacing(8)
        v.setContentsMargins(10, 10, 10, 10)

        tb = QHBoxLayout()
        add_btn = QPushButton("+ 记一笔")
        add_btn.setStyleSheet(BTN_PRIMARY)
        add_btn.clicked.connect(self._add_finance)
        tb.addWidget(add_btn)

        self._fin_summary = QLabel("")
        self._fin_summary.setStyleSheet("color: #00cc88; font-size: 12px; background: transparent;")
        tb.addWidget(self._fin_summary)
        tb.addStretch()
        v.addLayout(tb)

        self._finance_table = QTableWidget()
        self._finance_table.setColumnCount(7)
        self._finance_table.setHorizontalHeaderLabels([
            "ID", "类型", "分类", "金额", "日期", "描述", "关联订单"
        ])
        self._finance_table.setStyleSheet(TABLE_STYLE)
        self._finance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._finance_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._finance_table.setEditTriggers(QTableWidget.NoEditTriggers)
        v.addWidget(self._finance_table, 1)
        return w

    # ════════════════ 刷新 ════════════════

    def _refresh_all(self):
        self._refresh_orders()
        self._refresh_products()
        self._refresh_customers()
        self._refresh_finance()

    def _populate_table(self, table, rows):
        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = QTableWidgetItem(str(val) if val is not None else '')
                if c == 0:
                    item.setTextAlignment(Qt.AlignCenter)
                table.setItem(r, c, item)

    def _refresh_orders(self):
        conn = sqlite3.connect(ORDER_DB)
        rows = conn.execute(
            'SELECT id, order_no, customer_name, product_name, quantity, unit_price, total_amount, status, created_at FROM orders ORDER BY id DESC'
        ).fetchall()
        conn.close()
        self._populate_table(self._order_table, rows)
        self._status_lbl.setText(f"订单 {len(rows)} 条")

    def _refresh_products(self):
        conn = sqlite3.connect(PRODUCT_DB)
        rows = conn.execute(
            'SELECT id, name, category, price, cost, stock, unit, status, description FROM product ORDER BY id DESC'
        ).fetchall()
        conn.close()
        self._populate_table(self._product_table, rows)

    def _refresh_customers(self):
        conn = sqlite3.connect(CUSTOMER_DB)
        rows = conn.execute(
            'SELECT id, name, company, phone, email, level, note, created_at FROM customer ORDER BY id DESC'
        ).fetchall()
        conn.close()
        self._populate_table(self._customer_table, rows)

    def _refresh_finance(self):
        conn = sqlite3.connect(FINANCE_DB)
        rows = conn.execute(
            'SELECT id, type, category, amount, date, description, order_no FROM finance ORDER BY id DESC'
        ).fetchall()
        conn.close()
        self._populate_table(self._finance_table, rows)

        # 汇总
        income = sum(r[3] for r in conn.execute(
            "SELECT id, type, category, amount FROM finance WHERE type='income'"
        ).fetchall()) if rows else 0
        expense = sum(r[3] for r in conn.execute(
            "SELECT id, type, category, amount FROM finance WHERE type='expense'"
        ).fetchall()) if rows else 0
        self._fin_summary.setText(f"收入 ¥{income:.0f}  |  支出 ¥{expense:.0f}  |  结余 ¥{income - expense:.0f}")

    # ════════════════ 订单 CRUD ════════════════

    def _add_order(self):
        # 先获取客户和产品列表
        conn = sqlite3.connect(CUSTOMER_DB)
        customers = [r[0] for r in conn.execute('SELECT name FROM customer').fetchall()]
        conn.close()
        conn = sqlite3.connect(PRODUCT_DB)
        products = [r[0] for r in conn.execute('SELECT name FROM product').fetchall()]
        conn.close()

        fields = [
            ('customer_name', '客户', 'combo', customers),
            ('product_name', '产品', 'combo', products),
            ('quantity', '数量', 'num', [1, 9999]),
            ('unit_price', '单价', 'float', None),
            ('note', '备注', 'area', None),
        ]
        dlg = _EntityDialog("创建订单 · 轨道站", fields, parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return
        data = dlg.get_result()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        order_no = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
        total = data['quantity'] * data['unit_price']

        conn = sqlite3.connect(ORDER_DB)
        conn.execute(
            'INSERT INTO orders (order_no, customer_name, product_name, quantity, unit_price, total_amount, status, note, created_at) VALUES (?,?,?,?,?,?,?,?,?)',
            (order_no, data['customer_name'], data['product_name'],
             data['quantity'], data['unit_price'], total, '已完成', data.get('note', ''), now)
        )
        conn.commit()
        conn.close()

        # 自动记财务收入
        if total > 0:
            conn2 = sqlite3.connect(FINANCE_DB)
            conn2.execute(
                'INSERT INTO finance (type, category, amount, date, description, order_no) VALUES (?,?,?,?,?,?)',
                ('income', '产品销售', total, now, f"{data['customer_name']}购买{data['product_name']}", order_no)
            )
            conn2.commit()
            conn2.close()

        self._refresh_all()

    def _edit_order(self, idx):
        row = idx.row()
        item_id = self._order_table.item(row, 0)
        if not item_id:
            return
        oid = item_id.text()

        conn = sqlite3.connect(ORDER_DB)
        cur = conn.execute('SELECT * FROM orders WHERE id=?', (oid,)).fetchone()
        conn.close()
        if not cur:
            return

        conn = sqlite3.connect(CUSTOMER_DB)
        customers = [r[0] for r in conn.execute('SELECT name FROM customer').fetchall()]
        conn.close()
        conn = sqlite3.connect(PRODUCT_DB)
        products = [r[0] for r in conn.execute('SELECT name FROM product').fetchall()]
        conn.close()

        initial = {
            'customer_name': cur[2], 'product_name': cur[3],
            'quantity': cur[4], 'unit_price': cur[5], 'note': cur[7] or '',
        }
        fields = [
            ('customer_name', '客户', 'combo', customers),
            ('product_name', '产品', 'combo', products),
            ('quantity', '数量', 'num', [1, 9999]),
            ('unit_price', '单价', 'float', None),
            ('note', '备注', 'area', None),
        ]
        dlg = _EntityDialog("编辑订单", fields, initial, parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return
        data = dlg.get_result()
        total = data['quantity'] * data['unit_price']

        conn = sqlite3.connect(ORDER_DB)
        conn.execute(
            'UPDATE orders SET customer_name=?, product_name=?, quantity=?, unit_price=?, total_amount=?, note=? WHERE id=?',
            (data['customer_name'], data['product_name'],
             data['quantity'], data['unit_price'], total, data.get('note', ''), oid)
        )
        conn.commit()
        conn.close()
        self._refresh_all()

    def _export_orders(self):
        """导出订单到 CSV"""
        import csv
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'orders_export.csv')
        conn = sqlite3.connect(ORDER_DB)
        rows = conn.execute('SELECT * FROM orders ORDER BY id').fetchall()
        conn.close()
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(['ID', '订单号', '客户', '产品', '数量', '单价', '总金额', '状态', '备注', '日期'])
            w.writerows(rows)
        QMessageBox.information(self, "导出成功", f"已导出 {len(rows)} 条订单到:\n{path}")

    # ════════════════ 产品 CRUD ════════════════

    def _add_product(self):
        fields = [
            ('name', '产品名', 'text', None),
            ('category', '分类', 'text', None),
            ('price', '售价', 'float', None),
            ('cost', '成本', 'float', None),
            ('stock', '库存', 'num', [0, 99999]),
            ('unit', '单位', 'text', None),
            ('description', '描述', 'area', None),
        ]
        dlg = _EntityDialog("新产品 · 轨道站", fields, parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return
        data = dlg.get_result()

        conn = sqlite3.connect(PRODUCT_DB)
        conn.execute(
            'INSERT INTO product (name, category, price, cost, stock, unit, description) VALUES (?,?,?,?,?,?,?)',
            (data['name'], data['category'], data['price'], data['cost'],
             data['stock'], data['unit'], data.get('description', ''))
        )
        conn.commit()
        conn.close()
        self._refresh_all()

    def _edit_product(self, idx):
        row = idx.row()
        pid = self._product_table.item(row, 0).text()
        conn = sqlite3.connect(PRODUCT_DB)
        cur = conn.execute('SELECT * FROM product WHERE id=?', (pid,)).fetchone()
        conn.close()
        if not cur:
            return

        initial = {f: cur[i] for i, f in enumerate(['name', 'category', 'price', 'cost', 'stock', 'unit', 'description'], 1)}
        fields = [
            ('name', '产品名', 'text', None),
            ('category', '分类', 'text', None),
            ('price', '售价', 'float', None),
            ('cost', '成本', 'float', None),
            ('stock', '库存', 'num', [0, 99999]),
            ('unit', '单位', 'text', None),
            ('description', '描述', 'area', None),
        ]
        dlg = _EntityDialog("编辑产品", fields, initial, parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return
        data = dlg.get_result()

        conn = sqlite3.connect(PRODUCT_DB)
        conn.execute(
            'UPDATE product SET name=?, category=?, price=?, cost=?, stock=?, unit=?, description=? WHERE id=?',
            (data['name'], data['category'], data['price'], data['cost'],
             data['stock'], data['unit'], data.get('description', ''), pid)
        )
        conn.commit()
        conn.close()
        self._refresh_all()

    def _delete_product(self):
        row = self._product_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中要删除的产品")
            return
        pid = self._product_table.item(row, 0).text()
        name = self._product_table.item(row, 1).text()
        reply = QMessageBox.question(self, "确认", f"确定要删除产品「{name}」吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        conn = sqlite3.connect(PRODUCT_DB)
        conn.execute('DELETE FROM product WHERE id=?', (pid,))
        conn.commit()
        conn.close()
        self._refresh_all()

    # ════════════════ 客户 CRUD ════════════════

    def _add_customer(self):
        fields = [
            ('name', '姓名', 'text', None),
            ('company', '公司', 'text', None),
            ('phone', '电话', 'text', None),
            ('email', '邮箱', 'text', None),
            ('level', '级别', 'combo', ['普通', 'VIP', '钻石']),
            ('note', '备注', 'area', None),
        ]
        dlg = _EntityDialog("新客户 · 轨道站", fields, parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return
        data = dlg.get_result()

        conn = sqlite3.connect(CUSTOMER_DB)
        conn.execute(
            'INSERT INTO customer (name, company, phone, email, level, note) VALUES (?,?,?,?,?,?)',
            (data['name'], data['company'], data['phone'], data['email'],
             data['level'], data.get('note', ''))
        )
        conn.commit()
        conn.close()
        self._refresh_all()

    def _edit_customer(self, idx):
        row = idx.row()
        cid = self._customer_table.item(row, 0).text()
        conn = sqlite3.connect(CUSTOMER_DB)
        cur = conn.execute('SELECT * FROM customer WHERE id=?', (cid,)).fetchone()
        conn.close()
        if not cur:
            return

        initial = {f: cur[i] for i, f in enumerate(['name', 'company', 'phone', 'email', 'level', 'note'], 1)}
        fields = [
            ('name', '姓名', 'text', None),
            ('company', '公司', 'text', None),
            ('phone', '电话', 'text', None),
            ('email', '邮箱', 'text', None),
            ('level', '级别', 'combo', ['普通', 'VIP', '钻石']),
            ('note', '备注', 'area', None),
        ]
        dlg = _EntityDialog("编辑客户", fields, initial, parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return
        data = dlg.get_result()

        conn = sqlite3.connect(CUSTOMER_DB)
        conn.execute(
            'UPDATE customer SET name=?, company=?, phone=?, email=?, level=?, note=? WHERE id=?',
            (data['name'], data['company'], data['phone'], data['email'],
             data['level'], data.get('note', ''), cid)
        )
        conn.commit()
        conn.close()
        self._refresh_all()

    # ════════════════ 财务 CRUD ════════════════

    def _add_finance(self):
        fields = [
            ('type', '类型', 'combo', ['income', 'expense']),
            ('category', '分类', 'text', None),
            ('amount', '金额', 'float', None),
            ('date', '日期', 'text', None),
            ('description', '描述', 'area', None),
        ]
        dlg = _EntityDialog("记账 · 轨道站", fields, initial={'date': datetime.now().strftime('%Y-%m-%d')}, parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return
        data = dlg.get_result()

        conn = sqlite3.connect(FINANCE_DB)
        conn.execute(
            'INSERT INTO finance (type, category, amount, date, description) VALUES (?,?,?,?,?)',
            (data['type'], data['category'], data['amount'], data.get('date', ''), data.get('description', ''))
        )
        conn.commit()
        conn.close()
        self._refresh_all()

    # ════════════════ 动画 ════════════════

    def _tick_glow(self):
        self._glow_t += 0.04
        self._hud.update()

    def _paint_hud(self, event):
        painter = QPainter(self._hud)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self._hud.width(), self._hud.height()

        # 右上角光球 - 业务星球
        r = 28
        cx, cy = w - 55, 42
        import math
        pulse = (math.sin(self._glow_t * 2) + 1) / 2

        for layer in range(3, 0, -1):
            lr = r + layer * 14
            alpha = int(25 * (4 - layer) * (0.7 + 0.3 * pulse))
            g = QRadialGradient(cx, cy, lr)
            g.setColorAt(0.5, QColor(0, 0, 0, 0))
            g.setColorAt(0.7, QColor(68, 136, 255, alpha))
            g.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(g)
            painter.drawEllipse(cx - lr, cy - lr, lr * 2, lr * 2)

        # 星球本体
        body = QRadialGradient(cx - r * 0.3, cy - r * 0.3, r * 1.5)
        body.setColorAt(0, QColor(120, 180, 255, 220))
        body.setColorAt(0.5, QColor(40, 100, 220, 180))
        body.setColorAt(1, QColor(10, 30, 90, 200))
        painter.setBrush(body)
        painter.setPen(QPen(QColor(68, 136, 255, 80), 1))
        painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        painter.end()

import os