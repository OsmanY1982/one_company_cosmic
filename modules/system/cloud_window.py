"""
云端同步 · ENGINEERING DECK
QDialog：同步状态 + 手动同步 + 日志，蓝色点缀金属灰主题
"""
import os, sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox,
    QGroupBox, QTextEdit, QFrame
)
from PyQt5.QtCore import Qt

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

QSS = """
    QDialog {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(14,16,20,245), stop:1 rgba(20,23,28,245));
        border: 2px solid rgba(100,160,220,50);
        border-radius: 14px;
    }
"""
INPUT_STYLE = """
    QLineEdit, QComboBox, QTextEdit {
        background: rgba(16,18,22,230); color: #aabbcc;
        border: 1px solid rgba(130,145,165,35); border-radius: 6px;
        padding: 6px 10px; font-size: 12px;
    }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background: #141618; color: #aabbcc;
        selection-background-color: rgba(130,145,165,80);
    }
"""
BTN_PRIMARY = """
    QPushButton {
        background: rgba(130,145,165,40); color: #ccddee;
        border: 1px solid rgba(150,165,185,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(150,165,185,70); }
"""
BTN_BLUE = """
    QPushButton {
        background: rgba(100,160,220,40); color: #aaddff;
        border: 1px solid rgba(120,180,240,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(120,180,240,70); }
"""
GROUP_STYLE = """
    QGroupBox {
        color: #889999; font-weight: 700; font-size: 12px;
        border: 1px solid rgba(130,145,165,35); border-radius: 10px;
        margin-top: 12px; padding-top: 16px;
    }
    QGroupBox::title { left: 14px; padding: 0 6px; }
    QLabel { color: #889999; background: transparent; }
"""


class CloudWindow(QDialog):
    """云端同步管理"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("云端同步 · ENGINEERING DECK")
        self.setMinimumSize(600, 500)
        self.setStyleSheet(QSS)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(22, 18, 22, 18)

        title = QLabel("云端同步 · ENGINEERING DECK")
        title.setStyleSheet("color: #aabbcc; font-size: 16px; font-weight: 800; letter-spacing: 3px; background: transparent;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        # ── 连接状态 ──
        status_card = QFrame()
        status_card.setStyleSheet("background: rgba(16,18,22,230); border: 1px solid rgba(130,145,165,35); border-radius: 10px; padding: 14px;")
        sl = QHBoxLayout(status_card)
        self.status_lbl = QLabel("未连接")
        self.status_lbl.setStyleSheet("color: #888888; font-size: 14px; font-weight: 700; background:transparent;")
        sl.addWidget(self.status_lbl)
        sl.addStretch()

        conn_btn = QPushButton("连接 Supabase")
        conn_btn.setStyleSheet(BTN_BLUE)
        conn_btn.clicked.connect(self._toggle_connect)
        self._conn_btn = conn_btn
        sl.addWidget(conn_btn)
        layout.addWidget(status_card)

        # ── 同步控制 ──
        sync_panel = QGroupBox("数据同步")
        sync_panel.setStyleSheet(GROUP_STYLE)
        sl2 = QHBoxLayout(sync_panel); sl2.setSpacing(12)
        sl2.addWidget(QLabel("同步表:"))
        self.sync_tables = QComboBox()
        self.sync_tables.addItems(["全部", "订单", "产品", "客户", "会员", "财务", "激活码", "日志"])
        self.sync_tables.setStyleSheet(INPUT_STYLE)
        sl2.addWidget(self.sync_tables)

        pull = QPushButton("拉取")
        pull.setStyleSheet(BTN_PRIMARY)
        pull.clicked.connect(lambda: self._sync("拉取"))
        push = QPushButton("推送")
        push.setStyleSheet(BTN_BLUE)
        push.clicked.connect(lambda: self._sync("推送"))
        sl2.addWidget(pull); sl2.addWidget(push)
        sl2.addStretch()
        layout.addWidget(sync_panel)

        # ── 同步日志 ──
        log_label = QLabel("同步日志:")
        log_label.setStyleSheet("color: #667788; font-size: 11px; background:transparent;")
        layout.addWidget(log_label)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet(INPUT_STYLE)
        layout.addWidget(self.log_view)

    def _toggle_connect(self):
        if self._conn_btn.text() == "连接 Supabase":
            self.status_lbl.setText("连接中...")
            self.status_lbl.setStyleSheet("color: #ffcc44; font-size: 14px; font-weight: 700; background:transparent;")
            self._conn_btn.setText("断开")
            self._add_log("正在连接 Supabase 服务...")
            # 模拟连接成功
            self.status_lbl.setText("已连接")
            self.status_lbl.setStyleSheet("color: #44cc88; font-size: 14px; font-weight: 700; background:transparent;")
            self._add_log("Supabase 连接成功")
            self._log_sync("连接", "成功", "Supabase 连接建立")
        else:
            self.status_lbl.setText("未连接")
            self.status_lbl.setStyleSheet("color: #888888; font-size: 14px; font-weight: 700; background:transparent;")
            self._conn_btn.setText("连接 Supabase")
            self._add_log("已断开 Supabase 连接")
            self._log_sync("断开", "成功", "Supabase 连接已断开")

    def _sync(self, direction):
        table = self.sync_tables.currentText()
        self._add_log(f"[{datetime.now().strftime('%H:%M:%S')}] {direction} {table} 数据...")
        self._log_sync(direction, "进行中", f"{direction} {table}")
        # 模拟同步
        self._add_log(f"[{datetime.now().strftime('%H:%M:%S')}] {direction} {table} 完成")
        self._log_sync(direction, "成功", f"{direction} {table} 完成")

    def _add_log(self, msg):
        self.log_view.append(msg)

    def _log_sync(self, sync_type, status, detail):
        try:
            db = os.path.join(DATA_DIR, "system_logs.db")
            conn = sqlite3.connect(db)
            conn.execute("INSERT INTO sync_logs(sync_type, status, detail) VALUES(?,?,?)",
                         (sync_type, status, detail))
            conn.commit(); conn.close()
        except Exception:
            pass