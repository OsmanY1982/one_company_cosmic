# `modules/intelligence/digital_emp_window.py`

> 路径：`modules/intelligence/digital_emp_window.py` | 行数：593


---


```python
"""
数字员工 · NEURAL — 自动化任务执行引擎
SQLite 持久化 + 真实业务执行 + 日志追踪
"""
import os, sqlite3, traceback
from datetime import datetime
from typing import Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QTextEdit, QWidget, QMessageBox,
    QFormLayout, QLineEdit, QComboBox, QCheckBox, QDialogButtonBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
DB_PATH = os.path.join(DATA_DIR, "digital_emp.db")

INPUT_STYLE = """
    QLineEdit, QComboBox, QTextEdit {
        background: rgba(12,6,22,230); color: #ccbbdd;
        border: 1px solid rgba(170,80,255,35); border-radius: 6px;
        padding: 6px 10px; font-size: 12px;
    }
    QLineEdit:focus { border: 1px solid rgba(180,100,255,180); }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background: #150a20; color: #ccbbdd; selection-background-color: rgba(150,60,220,80);
    }
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
BTN_PRIMARY = """
    QPushButton {
        background: rgba(150,60,220,40); color: #ddaaff;
        border: 1px solid rgba(170,80,240,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(170,80,240,70); }
"""
BTN_EXEC_ALL = """
    QPushButton {
        background: rgba(60,200,120,45); color: #aaffcc;
        border: 1px solid rgba(80,220,140,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(80,220,140,70); }
"""

# ═══════ 数据库初始化 ═══════
def _init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            schedule TEXT DEFAULT '',
            description TEXT DEFAULT '',
            enabled INTEGER DEFAULT 1,
            last_run TEXT DEFAULT '—',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            task_name TEXT,
            status TEXT,
            message TEXT,
            executed_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    # 首次插入预置任务
    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count == 0:
        presets = [
            ("数据采集员", "数据采集", "每日 8:00", "每日自动采集各平台数据"),
            ("报表生成员", "报表生成", "周一 9:00", "每周一自动生成周报"),
            ("客户关怀员", "客户运营", "每日 10:00", "定期发送客户问候"),
            ("库存监控员", "库存监控", "实时", "监控库存告警"),
            ("对账小助手", "财务管理", "每月 1 日", "月末自动对账"),
        ]
        for name, role, schedule, desc in presets:
            conn.execute("INSERT INTO tasks(name,role,schedule,description) VALUES(?,?,?,?)",
                         (name, role, schedule, desc))
    conn.commit()
    conn.close()


# ═══════ 任务执行器：真实数据库操作 ═══════
class TaskRunner:
    """任务执行引擎 — 真实查询各业务数据库"""

    @staticmethod
    def execute(task_name: str, role: str) -> str:
        handler_map = {
            "数据采集": TaskRunner._run_data_collection,
            "报表生成": TaskRunner._run_report_generation,
            "客户运营": TaskRunner._run_customer_ops,
            "库存监控": TaskRunner._run_inventory_monitor,
            "财务管理": TaskRunner._run_finance_check,
            "内容发布": TaskRunner._run_content_publish,
            "日志清理": TaskRunner._run_log_cleanup,
        }
        handler = handler_map.get(role)
        if handler:
            return handler()
        return f"未知角色 '{role}'，无可执行操作"

    @staticmethod
    def _run_data_collection() -> str:
        """数据采集：汇总各库统计"""
        lines = ["[数据采集] 各库统计汇总："]
        dbs = {
            "order.db": ("orders", "订单", "SELECT COUNT(*) FROM orders"),
            "product.db": ("product", "产品", "SELECT COUNT(*) FROM product"),
            "customer.db": ("customer", "客户", "SELECT COUNT(*) FROM customer"),
            "member.db": ("member", "会员", "SELECT COUNT(*) FROM member"),
        }
        for db_name, (table, label, sql) in dbs.items():
            path = os.path.join(DATA_DIR, db_name)
            if os.path.exists(path):
                try:
                    conn = sqlite3.connect(path)
                    count = conn.execute(sql).fetchone()[0]
                    conn.close()
                    lines.append(f"  {label}: {count}")
                except Exception as e:
                    lines.append(f"  {label}: 读取失败 ({e})")
            else:
                lines.append(f"  {label}: 数据库不存在")
        return "\n".join(lines)

    @staticmethod
    def _run_report_generation() -> str:
        """报表生成：生成经营摘要"""
        order_db = os.path.join(DATA_DIR, "order.db")
        finance_db = os.path.join(DATA_DIR, "finance.db")
        if not os.path.exists(order_db):
            return "[报表生成] 无订单数据，无法生成报表"

        conn = sqlite3.connect(order_db)
        conn.row_factory = sqlite3.Row
        total = conn.execute("SELECT COUNT(*) as c, COALESCE(SUM(total_amount),0) as s FROM orders").fetchone()
        conn.close()

        finance_in = finance_out = 0.0
        if os.path.exists(finance_db):
            conn2 = sqlite3.connect(finance_db)
            r_in = conn2.execute("SELECT COALESCE(SUM(amount),0) FROM finance WHERE type='收入'").fetchone()[0]
            r_out = conn2.execute("SELECT COALESCE(SUM(amount),0) FROM finance WHERE type='支出'").fetchone()[0]
            finance_in = r_in or 0; finance_out = r_out or 0
            conn2.close()

        profit = finance_in - finance_out
        return (
            f"[报表生成] 经营摘要 {datetime.now().strftime('%Y-%m-%d')}：\n"
            f"  总订单: {total['c']} 单 | 总营收: ¥{total['s'] or 0:,.2f}\n"
            f"  财务: 收 ¥{finance_in:,.2f} / 支 ¥{finance_out:,.2f} / 利 ¥{profit:,.2f}"
        )

    @staticmethod
    def _run_customer_ops() -> str:
        """客户运营：识别高价值客户和流失风险"""
        order_db = os.path.join(DATA_DIR, "order.db")
        customer_db = os.path.join(DATA_DIR, "customer.db")
        lines = ["[客户运营] 客户分析："]
        total = 0

        if os.path.exists(customer_db):
            conn = sqlite3.connect(customer_db)
            total = conn.execute("SELECT COUNT(*) FROM customer").fetchone()[0]
            conn.close()
        lines.append(f"  客户总数: {total}")

        if os.path.exists(order_db):
            conn = sqlite3.connect(order_db)
            conn.row_factory = sqlite3.Row
            top = conn.execute(
                "SELECT customer_name, COUNT(*) as cnt, COALESCE(SUM(total_amount),0) as amt "
                "FROM orders GROUP BY customer_name ORDER BY amt DESC LIMIT 3"
            ).fetchall()
            conn.close()
            if top:
                lines.append("  高价值客户 TOP3:")
                for t in top:
                    lines.append(f"    - {t['customer_name']}: {t['cnt']}单 / ¥{t['amt']:,.2f}")
        return "\n".join(lines)

    @staticmethod
    def _run_inventory_monitor() -> str:
        """库存监控：检查低库存产品"""
        product_db = os.path.join(DATA_DIR, "product.db")
        if not os.path.exists(product_db):
            return "[库存监控] 无产品数据"
        conn = sqlite3.connect(product_db)
        conn.row_factory = sqlite3.Row
        low = conn.execute(
            "SELECT name, stock, price FROM product WHERE stock < 10 AND status='在售' ORDER BY stock ASC"
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM product").fetchone()[0]
        conn.close()

        lines = [f"[库存监控] 产品总数: {total}"]
        if low:
            lines.append(f"  ⚠ 低库存产品 ({len(low)} 款):")
            for item in low:
                lines.append(f"    - {item['name']}: 库存 {item['stock']}, 售价 ¥{item['price']:.0f}")
        else:
            lines.append("  库存状态: 全部正常")
        return "\n".join(lines)

    @staticmethod
    def _run_finance_check() -> str:
        """财务管理：对账与利润核算"""
        finance_db = os.path.join(DATA_DIR, "finance.db")
        if not os.path.exists(finance_db):
            return "[财务管理] 无财务数据"
        conn = sqlite3.connect(finance_db)
        conn.row_factory = sqlite3.Row
        income = conn.execute("SELECT COALESCE(SUM(amount),0) as t FROM finance WHERE type='收入'").fetchone()['t'] or 0
        expense = conn.execute("SELECT COALESCE(SUM(amount),0) as t FROM finance WHERE type='支出'").fetchone()['t'] or 0
        cats = conn.execute(
            "SELECT category, COALESCE(SUM(amount),0) as amt FROM finance WHERE type='支出' "
            "GROUP BY category ORDER BY amt DESC LIMIT 5"
        ).fetchall()
        conn.close()

        profit = income - expense
        margin = (profit / income * 100) if income > 0 else 0
        lines = [
            f"[财务管理] 对账报告 {datetime.now().strftime('%Y-%m-%d')}：",
            f"  收入: ¥{income:,.2f} | 支出: ¥{expense:,.2f}",
            f"  利润: ¥{profit:,.2f} (利润率 {margin:.1f}%)",
        ]
        if cats:
            lines.append("  支出分类 TOP5:")
            for c in cats:
                lines.append(f"    - {c['category']}: ¥{c['amt']:,.2f}")
        return "\n".join(lines)

    @staticmethod
    def _run_content_publish() -> str:
        return "[内容发布] 暂无待发布内容（需接入发布平台 API）"

    @staticmethod
    def _run_log_cleanup() -> str:
        db_path = os.path.join(DATA_DIR, "digital_emp.db")
        if not os.path.exists(db_path):
            return "[日志清理] 无可清理日志"
        conn = sqlite3.connect(db_path)
        old_count = conn.execute("SELECT COUNT(*) FROM execution_logs").fetchone()[0]
        conn.execute("DELETE FROM execution_logs WHERE executed_at < datetime('now','-30 days')")
        conn.commit()
        new_count = conn.execute("SELECT COUNT(*) FROM execution_logs").fetchone()[0]
        conn.close()
        return f"[日志清理] 已清理 {old_count - new_count} 条 30 天前的旧日志，当前剩余 {new_count} 条"


# ═══════ 任务编辑对话框 ═══════
class EmployeeTaskDialog(QDialog):
    """数字员工 — 新增/编辑任务"""

    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.setWindowTitle("编辑任务" if task else "新增任务")
        self.setFixedSize(420, 350)
        self.setStyleSheet("background: rgba(16,8,28,235);")
        l = QFormLayout(self)
        l.setSpacing(10)

        self._name = QLineEdit(task["name"] if task else "")
        self._name.setStyleSheet(INPUT_STYLE)
        self._name.setPlaceholderText("如: 数据采集员")
        l.addRow("任务名称:", self._name)

        self._role = QComboBox()
        self._role.addItems(["数据采集", "报表生成", "客户运营", "库存监控", "财务管理", "内容发布", "日志清理"])
        self._role.setStyleSheet(INPUT_STYLE)
        if task:
            idx = self._role.findText(task.get("role", ""))
            if idx >= 0:
                self._role.setCurrentIndex(idx)
        l.addRow("角色:", self._role)

        self._schedule = QLineEdit(task.get("schedule", "每日 8:00") if task else "每日 8:00")
        self._schedule.setStyleSheet(INPUT_STYLE)
        self._schedule.setPlaceholderText("如: 每日 8:00 / 周一 9:00 / 实时")
        l.addRow("调度:", self._schedule)

        self._desc = QLineEdit(task.get("description", task.get("desc", "")) if task else "")
        self._desc.setStyleSheet(INPUT_STYLE)
        self._desc.setPlaceholderText("任务描述...")
        l.addRow("描述:", self._desc)

        self._enabled = QCheckBox("启用")
        self._enabled.setStyleSheet("color: #ccbbdd;")
        if task:
            val = task.get("enabled", task.get("status", True))
            self._enabled.setChecked(bool(val))
        else:
            self._enabled.setChecked(True)
        l.addRow("", self._enabled)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._validate_and_accept)
        btn_box.rejected.connect(self.reject)
        btn_box.setStyleSheet(
            "QPushButton { background: rgba(150,60,220,40); color: #ddaaff; border-radius: 12px; padding: 5px 18px; }"
        )
        l.addRow(btn_box)

    def _validate_and_accept(self):
        if not self._name.text().strip():
            QMessageBox.warning(self, "缺少参数", "请输入任务名称")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self._name.text().strip(),
            "role": self._role.currentText(),
            "schedule": self._schedule.text().strip(),
            "description": self._desc.text().strip(),
            "enabled": self._enabled.isChecked(),
        }


# ═══════ 数字员工窗口 ═══════
class DigitalEmpWindow(QDialog):
    """数字员工 · NEURAL — SQLite 持久化 + 真实执行"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数字员工 · NEURAL")
        self.setMinimumSize(820, 540)
        self.setStyleSheet("background: rgba(10,5,20,240);")
        _init_db()
        self._build_ui()
        self._emp_refresh()

    # ─── DB 操作 ───
    def _get_conn(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_tasks(self):
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _add_task(self, data: dict):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO tasks(name,role,schedule,description,enabled) VALUES(?,?,?,?,?)",
            (data["name"], data["role"], data["schedule"], data["description"], int(data["enabled"]))
        )
        conn.commit()
        tid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return tid

    def _update_task(self, tid: int, data: dict):
        conn = self._get_conn()
        conn.execute(
            "UPDATE tasks SET name=?,role=?,schedule=?,description=?,enabled=? WHERE id=?",
            (data["name"], data["role"], data["schedule"], data["description"], int(data["enabled"]), tid)
        )
        conn.commit()
        conn.close()

    def _toggle_task(self, tid: int, enabled: bool):
        conn = self._get_conn()
        conn.execute("UPDATE tasks SET enabled=?, last_run=? WHERE id=?", (int(enabled), "—" if enabled else "已停用", tid))
        conn.commit()
        conn.close()

    def _delete_task(self, tid: int):
        conn = self._get_conn()
        conn.execute("DELETE FROM tasks WHERE id=?", (tid,))
        conn.execute("DELETE FROM execution_logs WHERE task_id=?", (tid,))
        conn.commit()
        conn.close()

    def _log_execution(self, tid: int, task_name: str, status: str, message: str):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO execution_logs(task_id,task_name,status,message) VALUES(?,?,?,?)",
            (tid, task_name, status, message)
        )
        if status == "成功":
            conn.execute("UPDATE tasks SET last_run=? WHERE id=?", (datetime.now().strftime("%Y-%m-%d %H:%M"), tid))
        conn.commit()
        conn.close()

    # ─── 任务执行 ───
    def _execute_task(self, tid: int):
        tasks = self._load_tasks()
        task = next((t for t in tasks if t["id"] == tid), None)
        if not task:
            return
        now = datetime.now().strftime("%H:%M:%S")
        self.emp_log.append(f'<p style="color:#aaa;">[{now}] 开始执行: {task["name"]}</p>')
        try:
            result = TaskRunner.execute(task["name"], task["role"])
            self._log_execution(tid, task["name"], "成功", result)
            self.emp_log.append(f'<p style="color:#44cc88;">[{now}] ✓ {task["name"]} 执行成功</p>')
            self.emp_log.append(f'<p style="color:#88aacc; font-size:11px; padding-left:16px;">{result[:300]}</p>')
        except Exception as e:
            err_msg = traceback.format_exc()
            self._log_execution(tid, task["name"], "失败", str(e))
            self.emp_log.append(f'<p style="color:#ff6666;">[{now}] ✗ {task["name"]} 执行失败: {e}</p>')
        self._emp_refresh()

    def _execute_all(self):
        tasks = self._load_tasks()
        enabled = [t for t in tasks if t["enabled"]]
        if not enabled:
            self.emp_log.append('<p style="color:#ffaa44;">没有已启用的任务</p>')
            return
        now = datetime.now().strftime("%H:%M:%S")
        self.emp_log.append(f'<p style="color:#ffaa44;font-weight:700;">[{now}] === 批量执行 {len(enabled)} 个任务 ===</p>')
        for task in enabled:
            self._execute_task(task["id"])

    # ─── UI ───
    def _build_ui(self):
        l = QVBoxLayout(self)
        l.setSpacing(10)
        l.setContentsMargins(16, 12, 16, 12)

        info = QLabel("数字员工 — 自动化任务执行 / 监控（SQLite 持久化）")
        info.setStyleSheet("color: #776699; font-size: 12px; background: transparent;")
        l.addWidget(info)

        stats_row = QHBoxLayout()
        self.emp_stats_label = QLabel("任务: 0 | 运行中: 0")
        self.emp_stats_label.setStyleSheet(
            "color: #9988bb; font-size: 11px; background: rgba(16,8,28,150); border-radius: 8px; padding: 6px 12px;"
        )
        stats_row.addWidget(self.emp_stats_label)
        stats_row.addStretch()
        btn_all = QPushButton("▶ 全部执行")
        btn_all.setStyleSheet(BTN_EXEC_ALL)
        btn_all.clicked.connect(self._execute_all)
        stats_row.addWidget(btn_all)
        btn_add = QPushButton("+ 新增任务")
        btn_add.setStyleSheet(BTN_PRIMARY)
        btn_add.clicked.connect(self._emp_add_task)
        stats_row.addWidget(btn_add)
        btn_refresh = QPushButton("刷新")
        btn_refresh.setStyleSheet(BTN_PRIMARY)
        btn_refresh.clicked.connect(self._emp_refresh)
        stats_row.addWidget(btn_refresh)
        l.addLayout(stats_row)

        self.emp_table = QTableWidget()
        self.emp_table.setColumnCount(7)
        self.emp_table.setHorizontalHeaderLabels(["任务名称", "角色", "调度", "状态", "上次执行", "操作", "执行"])
        self.emp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.emp_table.setStyleSheet(TABLE_STYLE)
        self.emp_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.emp_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.emp_table.doubleClicked.connect(self._emp_edit_task)
        l.addWidget(self.emp_table, 1)

        log_label = QLabel("执行日志:")
        log_label.setStyleSheet("color: #776699; font-size: 11px; background:transparent;")
        l.addWidget(log_label)
        self.emp_log = QTextEdit()
        self.emp_log.setReadOnly(True)
        self.emp_log.setMaximumHeight(160)
        self.emp_log.setStyleSheet(INPUT_STYLE)
        l.addWidget(self.emp_log)

    def _emp_refresh(self):
        tasks = self._load_tasks()
        self.emp_table.setRowCount(len(tasks))
        running = sum(1 for t in tasks if t["enabled"])
        self.emp_stats_label.setText(f"任务: {len(tasks)} | 运行中: {running} | 已停用: {len(tasks) - running}")
        for i, task in enumerate(tasks):
            self.emp_table.setItem(i, 0, QTableWidgetItem(task["name"]))
            self.emp_table.setItem(i, 1, QTableWidgetItem(task["role"]))
            self.emp_table.setItem(i, 2, QTableWidgetItem(task["schedule"]))
            status_item = QTableWidgetItem("运行中" if task["enabled"] else "已停用")
            status_item.setForeground(QColor("#44cc88" if task["enabled"] else "#ff6666"))
            self.emp_table.setItem(i, 3, status_item)
            self.emp_table.setItem(i, 4, QTableWidgetItem(task["last_run"] or "—"))

            # 操作按钮
            op_widget = QWidget()
            op_layout = QHBoxLayout(op_widget)
            op_layout.setContentsMargins(2, 2, 2, 2)
            op_layout.setSpacing(3)
            toggle_btn = QPushButton("停用" if task["enabled"] else "启用")
            toggle_btn.setFixedSize(44, 22)
            toggle_btn.setStyleSheet(
                f"font-size:10px; border-radius:8px; padding:1px 4px; "
                f"{'background:rgba(200,60,40,40);color:#ffaaaa;' if task['enabled'] else 'background:rgba(60,200,80,40);color:#aaffaa;'} "
                f"border:1px solid rgba(120,60,180,40);"
            )
            toggle_btn.clicked.connect(lambda _, tid=task["id"]: self._emp_toggle(tid))
            op_layout.addWidget(toggle_btn)
            edit_btn = QPushButton("编辑")
            edit_btn.setFixedSize(40, 22)
            edit_btn.setStyleSheet(
                "font-size:10px; border-radius:8px; padding:1px 4px; background:rgba(150,60,220,30); "
                "color:#ddaaff; border:1px solid rgba(170,80,240,40);"
            )
            edit_btn.clicked.connect(lambda _, tid=task["id"]: self._emp_edit_dialog(tid))
            op_layout.addWidget(edit_btn)
            del_btn = QPushButton("删除")
            del_btn.setFixedSize(40, 22)
            del_btn.setStyleSheet(
                "font-size:10px; border-radius:8px; padding:1px 4px; background:rgba(200,60,40,30); "
                "color:#ffaaaa; border:1px solid rgba(200,80,50,40);"
            )
            del_btn.clicked.connect(lambda _, tid=task["id"]: self._emp_delete(tid))
            op_layout.addWidget(del_btn)
            self.emp_table.setCellWidget(i, 5, op_widget)

            # 执行按钮
            exec_btn = QPushButton("执行")
            exec_btn.setFixedSize(44, 22)
            exec_btn.setStyleSheet(
                "font-size:10px; border-radius:8px; padding:1px 6px; "
                "background:rgba(100,180,255,40); color:#aaddff; border:1px solid rgba(100,180,255,55);"
            )
            exec_btn.clicked.connect(lambda _, tid=task["id"]: self._execute_task(tid))
            self.emp_table.setCellWidget(i, 6, exec_btn)

    def _emp_toggle(self, tid: int):
        tasks = self._load_tasks()
        task = next((t for t in tasks if t["id"] == tid), None)
        if task:
            new_state = not task["enabled"]
            self._toggle_task(tid, new_state)
            status_text = "启动" if new_state else "停用"
            self.emp_log.append(f'<p style="color:#aaa;">[{datetime.now().strftime("%H:%M:%S")}] {status_text}: {task["name"]}</p>')
            self._emp_refresh()

    def _emp_add_task(self):
        dlg = EmployeeTaskDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            self._add_task(data)
            self.emp_log.append(f'<p style="color:#aaa;">[{datetime.now().strftime("%H:%M:%S")}] 新增任务: {data["name"]}</p>')
            self._emp_refresh()

    def _emp_edit_task(self):
        row = self.emp_table.currentRow()
        if row >= 0:
            tasks = self._load_tasks()
            if row < len(tasks):
                self._emp_edit_dialog(tasks[row]["id"])

    def _emp_edit_dialog(self, tid: int):
        tasks = self._load_tasks()
        task = next((t for t in tasks if t["id"] == tid), None)
        if not task:
            return
        dlg = EmployeeTaskDialog(self, task)
        if dlg.exec_() == QDialog.Accepted:
            self._update_task(tid, dlg.get_data())
            self.emp_log.append(f'<p style="color:#aaa;">[{datetime.now().strftime("%H:%M:%S")}] 编辑任务: {task["name"]}</p>')
            self._emp_refresh()

    def _emp_delete(self, tid: int):
        tasks = self._load_tasks()
        task = next((t for t in tasks if t["id"] == tid), None)
        if not task:
            return
        if QMessageBox.question(self, "确认删除", f"确定删除任务「{task['name']}」？") == QMessageBox.Yes:
            self._delete_task(tid)
            self.emp_log.append(f'<p style="color:#aaa;">[{datetime.now().strftime("%H:%M:%S")}] 删除任务: {task["name"]}</p>')
            self._emp_refresh()

```
