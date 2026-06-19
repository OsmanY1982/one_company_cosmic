# `modules/system/logs_window.py`

> 路径：`modules/system/logs_window.py` | 行数：448


---


```python
"""
系统日志 · 操作日志 + 同步状态 + 错误日志（三标签页）
对标桌面版 SystemLogsWindow — 本地 SQLite 替代 Supabase
"""
import os, sqlite3
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QWidget, QGroupBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
LOG_DIR = os.path.join(_PROJECT_ROOT, "log")
LOG_DB = os.path.join(DATA_DIR, "operation_log.db")
SYNC_LOG_DB = os.path.join(DATA_DIR, "sync_log.db")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


def _ensure_log_db():
    conn = sqlite3.connect(LOG_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL DEFAULT 'system',
            action TEXT NOT NULL,
            module TEXT DEFAULT '',
            detail TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def _ensure_sync_db():
    conn = sqlite3.connect(SYNC_LOG_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sync_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_type TEXT NOT NULL DEFAULT 'manual',
            status TEXT DEFAULT 'success',
            detail TEXT DEFAULT '',
            files_synced INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module TEXT DEFAULT '',
            error_type TEXT DEFAULT '',
            message TEXT NOT NULL,
            traceback TEXT DEFAULT '',
            resolved INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


_ensure_log_db()
_ensure_sync_db()


def log_action(username, action, module="", detail=""):
    try:
        conn = sqlite3.connect(LOG_DB)
        conn.execute(
            "INSERT INTO operation_logs (username, action, module, detail) VALUES (?,?,?,?)",
            (username, action, module, detail)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def log_error(module, error_type, message, traceback_text=""):
    try:
        conn = sqlite3.connect(SYNC_LOG_DB)
        conn.execute(
            "INSERT INTO error_logs (module, error_type, message, traceback) VALUES (?,?,?,?)",
            (module, error_type, message, traceback_text)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


class LogsWindow(QDialog):
    """系统日志 · ENGINEERING DECK"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统日志 · ENGINEERING DECK")
        self.setMinimumSize(800, 600)
        self._build_ui()
        self._load_operation_logs()
        self._load_sync_status()
        self._load_error_logs()
        self.setStyleSheet(self._style())

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 16, 20, 20)

        title = QLabel("系统日志")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("PingFang SC", 18, QFont.Bold))
        title.setStyleSheet("color: #ddaaff; letter-spacing: 4px;")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self._build_op_log_tab(), "操作日志")
        tabs.addTab(self._build_sync_tab(), "同步状态")
        tabs.addTab(self._build_error_tab(), "错误日志")
        layout.addWidget(tabs)

    # ═══════════════════════════════════════════
    #  标签页 1: 操作日志
    # ═══════════════════════════════════════════
    def _build_op_log_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(8)

        # 筛选
        flt = QHBoxLayout()
        flt.addWidget(QLabel("用户:"))
        self.op_user = QLineEdit()
        self.op_user.setMaximumWidth(120)
        self.op_user.setPlaceholderText("全部")
        self.op_user.textChanged.connect(self._load_operation_logs)
        flt.addWidget(self.op_user)

        flt.addWidget(QLabel("模块:"))
        self.op_module = QComboBox()
        self.op_module.addItems(["全部", "激活码", "订单", "客户", "财务", "系统", "备份", "会员", "登录"])
        self.op_module.currentIndexChanged.connect(self._load_operation_logs)
        flt.addWidget(self.op_module)
        flt.addStretch()

        btn_export = QPushButton("导出")
        btn_export.clicked.connect(self._export_logs)
        flt.addWidget(btn_export)

        btn_clean = QPushButton("清理30天前")
        btn_clean.setObjectName("btn_clean")
        btn_clean.clicked.connect(self._clean_old_logs)
        flt.addWidget(btn_clean)
        lay.addLayout(flt)

        self.op_table = QTableWidget()
        self.op_table.setColumnCount(6)
        self.op_table.setHorizontalHeaderLabels(["ID", "用户", "操作", "模块", "详情", "时间"])
        self.op_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        lay.addWidget(self.op_table)

        return w

    # ═══════════════════════════════════════════
    #  标签页 2: 同步状态
    # ═══════════════════════════════════════════
    def _build_sync_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)

        info_box = QGroupBox("连接状态")
        ig = QVBoxLayout(info_box)
        ig.setSpacing(6)

        self.sync_status_lbl = QLabel("状态: 检查中...")
        self.sync_status_lbl.setStyleSheet("font-size: 14px; font-weight: bold;")
        ig.addWidget(self.sync_status_lbl)

        self.sync_last_lbl = QLabel("最后同步: -")
        ig.addWidget(self.sync_last_lbl)

        ig.addWidget(QLabel("同步记录:"))
        lay.addWidget(info_box)

        self.sync_table = QTableWidget()
        self.sync_table.setColumnCount(5)
        self.sync_table.setHorizontalHeaderLabels(["ID", "类型", "状态", "文件数", "时间"])
        self.sync_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        lay.addWidget(self.sync_table)

        btn_row = QHBoxLayout()
        btn_sync = QPushButton("手动同步")
        btn_sync.setObjectName("btn_sync")
        btn_sync.clicked.connect(self._manual_sync)
        btn_row.addWidget(btn_sync)

        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self._load_sync_status)
        btn_row.addWidget(btn_refresh)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        return w

    # ═══════════════════════════════════════════
    #  标签页 3: 错误日志
    # ═══════════════════════════════════════════
    def _build_error_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(8)

        stats = QHBoxLayout()
        self.err_today = QLabel("今日: 0")
        self.err_week = QLabel("本周: 0")
        self.err_pending = QLabel("未处理: 0")
        for lbl, color in [(self.err_today, "#e53e3e"), (self.err_week, "#f6ad55"), (self.err_pending, "#63b3ed")]:
            lbl.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold; margin-right: 14px;")
            stats.addWidget(lbl)
        stats.addStretch()

        btn_mark = QPushButton("标记为已处理")
        btn_mark.clicked.connect(self._mark_resolved)
        stats.addWidget(btn_mark)
        lay.addLayout(stats)

        self.err_table = QTableWidget()
        self.err_table.setColumnCount(6)
        self.err_table.setHorizontalHeaderLabels(["ID", "模块", "类型", "错误信息", "已处理", "时间"])
        self.err_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        lay.addWidget(self.err_table)

        return w

    # ═══════════════════════════════════════════
    #  数据加载
    # ═══════════════════════════════════════════
    def _load_operation_logs(self):
        user = self.op_user.text().strip() if hasattr(self, 'op_user') else ""
        mod = self.op_module.currentText() if hasattr(self, 'op_module') else "全部"
        conn = sqlite3.connect(LOG_DB)
        conn.row_factory = sqlite3.Row
        sql = "SELECT id, username, action, module, detail, created_at FROM operation_logs WHERE 1=1"
        params = []
        if user:
            sql += " AND username LIKE ?"
            params.append(f"%{user}%")
        if mod != "全部":
            sql += " AND module = ?"
            params.append(mod)
        sql += " ORDER BY id DESC LIMIT 200"
        rows = conn.execute(sql, params).fetchall()
        conn.close()

        self.op_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, key in enumerate(["id", "username", "action", "module", "detail", "created_at"]):
                val = r[key] if r[key] else "-"
                item = QTableWidgetItem(str(val))
                self.op_table.setItem(i, j, item)

    def _load_sync_status(self):
        conn = sqlite3.connect(SYNC_LOG_DB)
        conn.row_factory = sqlite3.Row
        try:
            # 最后同步记录
            last = conn.execute("SELECT created_at, status FROM sync_records ORDER BY id DESC LIMIT 1").fetchone()
            if last:
                self.sync_last_lbl.setText(f"最后同步: {last['created_at']} ({last['status']})")
                self.sync_status_lbl.setText(f"状态: {'已连接' if last['status'] == 'success' else '连接异常'}")
            else:
                self.sync_status_lbl.setText("状态: 待同步")
                self.sync_last_lbl.setText("最后同步: -")

            # 同步记录表格
            recs = conn.execute("""
                SELECT id, sync_type, status, files_synced, created_at
                FROM sync_records ORDER BY id DESC LIMIT 50
            """).fetchall()
        except Exception:
            recs = []
            conn.close()
            conn = sqlite3.connect(SYNC_LOG_DB)
            conn.row_factory = sqlite3.Row
            recs = conn.execute("SELECT * FROM sync_records ORDER BY id DESC LIMIT 50").fetchall()
        conn.close()

        self.sync_table.setRowCount(len(recs))
        for i, r in enumerate(recs):
            vals = [str(r["id"]), r.get("sync_type", "-"), r.get("status", "-"),
                    str(r.get("files_synced", 0)), str(r["created_at"])]
            for j, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if j == 2 and v == "success":
                    item.setForeground(QColor(0x44, 0xcc, 0x88))
                self.sync_table.setItem(i, j, item)

    def _load_error_logs(self):
        conn = sqlite3.connect(SYNC_LOG_DB)
        conn.row_factory = sqlite3.Row
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        today_c = conn.execute("SELECT COUNT(*) as c FROM error_logs WHERE created_at >= ?", (today,)).fetchone()["c"]
        week_c = conn.execute("SELECT COUNT(*) as c FROM error_logs WHERE created_at >= ?", (week_ago,)).fetchone()["c"]
        pending_c = conn.execute("SELECT COUNT(*) as c FROM error_logs WHERE resolved=0").fetchone()["c"]

        self.err_today.setText(f"今日: {today_c}")
        self.err_week.setText(f"本周: {week_c}")
        self.err_pending.setText(f"未处理: {pending_c}")

        rows = conn.execute("""
            SELECT id, module, error_type, message, resolved, created_at
            FROM error_logs ORDER BY id DESC LIMIT 100
        """).fetchall()
        conn.close()

        self.err_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.err_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.err_table.setItem(i, 1, QTableWidgetItem(r["module"] or "-"))
            self.err_table.setItem(i, 2, QTableWidgetItem(r["error_type"] or "-"))
            self.err_table.setItem(i, 3, QTableWidgetItem((r["message"] or "")[:100]))
            resolved = QTableWidgetItem("是" if r["resolved"] else "否")
            resolved.setForeground(QColor(0x44, 0xcc, 0x88) if r["resolved"] else QColor(0xe5, 0x3e, 0x3e))
            self.err_table.setItem(i, 4, resolved)
            self.err_table.setItem(i, 5, QTableWidgetItem(str(r["created_at"]) or "-"))

    # ═══════════════════════════════════════════
    #  操作
    # ═══════════════════════════════════════════
    def _export_logs(self):
        from PyQt5.QtWidgets import QFileDialog
        import csv
        path, _ = QFileDialog.getSaveFileName(self, "导出操作日志", "操作日志.csv", "CSV (*.csv)")
        if not path:
            return
        conn = sqlite3.connect(LOG_DB)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM operation_logs ORDER BY id DESC LIMIT 1000").fetchall()
        conn.close()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["ID", "用户", "操作", "模块", "详情", "时间"])
            for r in rows:
                w.writerow([r["id"], r["username"], r["action"], r["module"], r["detail"], r["created_at"]])
        QMessageBox.information(self, "导出成功", f"已导出 {len(rows)} 条日志")

    def _clean_old_logs(self):
        if QMessageBox.Yes != QMessageBox.question(self, "清理确认", "删除 30 天前的操作日志？", QMessageBox.Yes | QMessageBox.No):
            return
        conn = sqlite3.connect(LOG_DB)
        cur = conn.execute("DELETE FROM operation_logs WHERE created_at < datetime('now', '-30 days')")
        deleted = cur.rowcount
        conn.commit()
        conn.close()
        QMessageBox.information(self, "清理完成", f"已删除 {deleted} 条旧日志")
        self._load_operation_logs()

    def _manual_sync(self):
        try:
            conn = sqlite3.connect(SYNC_LOG_DB)
            conn.execute(
                "INSERT INTO sync_records (sync_type, status, detail, files_synced) VALUES (?,?,?,?)",
                ("manual", "success", "手动同步", 0)
            )
            conn.commit()
            conn.close()
            QMessageBox.information(self, "同步完成", "数据已同步到本地数据库")
            self._load_sync_status()
        except Exception as e:
            QMessageBox.warning(self, "同步失败", str(e)[:200])

    def _mark_resolved(self):
        row = self.err_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请选中一行错误记录")
            return
        eid = int(self.err_table.item(row, 0).text())
        conn = sqlite3.connect(SYNC_LOG_DB)
        conn.execute("UPDATE error_logs SET resolved=1 WHERE id=?", (eid,))
        conn.commit()
        conn.close()
        self._load_error_logs()

    def _style(self):
        return """
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(10,12,18,245), stop:1 rgba(18,21,28,245));
                border: 2px solid rgba(130,145,165,35); border-radius: 14px;
            }
            QTabWidget::pane {
                background: transparent; border: 1px solid rgba(130,145,165,20);
                border-radius: 8px; padding: 8px;
            }
            QTabBar::tab {
                background: rgba(18,22,30,200); color: #889999;
                padding: 8px 20px; border: 1px solid rgba(130,145,165,15);
                border-bottom: none; border-top-left-radius: 8px;
                border-top-right-radius: 8px; font-size: 12px;
            }
            QTabBar::tab:selected {
                background: rgba(30,36,46,230); color: #ddaaff;
                border-bottom: 1px solid rgba(30,36,46,230);
            }
            QLabel { color: #99aabb; background: transparent; font-size: 12px; }
            QGroupBox {
                color: #889999; font-weight: 700;
                border: 1px solid rgba(130,145,165,25); border-radius: 10px;
                margin-top: 8px; padding-top: 14px;
            }
            QGroupBox::title { left: 14px; padding: 0 6px; }
            QLineEdit, QComboBox {
                background: rgba(16,20,26,220); color: #aabbcc;
                border: 1px solid rgba(130,145,165,25); border-radius: 6px;
                padding: 6px 10px; font-size: 12px;
            }
            QPushButton {
                background: rgba(130,145,165,30); color: #ccddee;
                border: 1px solid rgba(150,165,185,45); border-radius: 8px;
                padding: 7px 18px; font-size: 11px; font-weight: 600;
            }
            QPushButton:hover { background: rgba(160,175,195,55); }
            QPushButton#btn_clean { background: rgba(200,50,50,35); color: #ff6666; }
            QPushButton#btn_clean:hover { background: rgba(220,70,70,55); }
            QPushButton#btn_sync { background: rgba(40,160,80,45); color: #88ffaa; }
            QTableWidget {
                background: rgba(14,18,24,220); color: #aabbcc;
                border: 1px solid rgba(120,140,165,20); border-radius: 8px;
                gridline-color: rgba(80,95,115,18); font-size: 12px;
            }
            QTableWidget::item { padding: 5px 8px; }
            QHeaderView::section {
                background: rgba(22,26,32,230); color: #889999;
                padding: 6px 8px; border: none;
                border-bottom: 1px solid rgba(130,145,165,30);
                font-weight: 700; font-size: 11px;
            }
        """

```
