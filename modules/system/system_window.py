"""
系统设置 → 工程舱 · ENGINEERING DECK
宇宙主题窗口：基础信息 / 激活码 / 云端同步 / 系统日志
"""
import os, sqlite3, json
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QHeaderView, QMessageBox, QTextEdit, QLineEdit,
    QComboBox, QGroupBox, QFrame, QFormLayout, QProgressBar,
    QDialog, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from core.cosmic import CosmicBackground

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

# ═══════ 宇宙 QSS ═══════
TAB_STYLE = """
    QTabWidget::pane {
        background: transparent;
        border: 1px solid rgba(130,145,165,30);
        border-radius: 10px;
    }
    QTabBar::tab {
        background: rgba(20,22,26,220);
        color: #889999; padding: 10px 22px;
        border: none; border-bottom: 2px solid transparent;
        font-size: 12px; font-weight: 600; letter-spacing: 2px; min-width: 70px;
    }
    QTabBar::tab:selected {
        color: #aabbcc;
        border-bottom: 2px solid #8899aa;
        background: rgba(26,28,32,235);
    }
    QTabBar::tab:hover { color: #99aabb; }
"""
TABLE_STYLE = """
    QTableWidget {
        background: rgba(16,18,22,220); color: #aabbcc;
        border: 1px solid rgba(120,135,155,30); border-radius: 8px;
        gridline-color: rgba(80,90,110,25); font-size: 12px;
        selection-background-color: rgba(130,145,165,60);
    }
    QTableWidget::item { padding: 5px 10px; }
    QHeaderView::section {
        background: rgba(22,24,28,230); color: #889999; padding: 8px 10px;
        border: none; border-bottom: 1px solid rgba(130,145,165,40);
        font-weight: 700; font-size: 11px; letter-spacing: 1px;
    }
"""
INPUT_STYLE = """
    QLineEdit, QComboBox, QTextEdit {
        background: rgba(16,18,22,230); color: #aabbcc;
        border: 1px solid rgba(130,145,165,35); border-radius: 6px;
        padding: 6px 10px; font-size: 12px;
    }
    QLineEdit:focus { border: 1px solid rgba(160,175,195,180); }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background: #141618; color: #aabbcc; selection-background-color: rgba(130,145,165,80);
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
BTN_DANGER = """
    QPushButton {
        background: rgba(180,60,40,40); color: #ffaaaa;
        border: 1px solid rgba(180,80,50,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px;
    }
    QPushButton:hover { background: rgba(200,80,50,70); }
"""
BTN_GREEN = """
    QPushButton {
        background: rgba(40,150,100,40); color: #88ffbb;
        border: 1px solid rgba(60,170,120,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px;
    }
    QPushButton:hover { background: rgba(50,190,120,70); }
"""


# ═══════ DB 初始化 ═══════
def _init_dbs():
    # 激活码
    db = os.path.join(DATA_DIR, "activation.db")
    conn = sqlite3.connect(db)
    conn.execute('''CREATE TABLE IF NOT EXISTS activation (
        id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL,
        code_type TEXT DEFAULT '试用', duration_days INTEGER DEFAULT 0,
        is_used INTEGER DEFAULT 0, used_by TEXT, used_at TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    conn.commit(); conn.close()

    # 系统日志
    db = os.path.join(DATA_DIR, "system_logs.db")
    conn = sqlite3.connect(db)
    conn.execute('''CREATE TABLE IF NOT EXISTS op_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, module TEXT, action TEXT,
        detail TEXT, created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sync_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, sync_type TEXT,
        status TEXT, detail TEXT, created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS error_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, module TEXT, error TEXT,
        detail TEXT, created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    conn.commit(); conn.close()

_init_dbs()


# ═══════════════ 主窗口 ═══════════════
class SystemWindow(QMainWindow):
    """工程舱 · ENGINEERING DECK"""

    def __init__(self, parent=None, role="admin"):
        super().__init__(parent)
        self._role = role
        self.setWindowTitle("一人公司 — 工程舱 · ENGINEERING DECK")
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

        title = QLabel("工程舱")
        title.setStyleSheet("color: #aabbcc; font-size: 24px; font-weight: 800; letter-spacing: 8px; background: transparent;")
        hl.addWidget(title, alignment=Qt.AlignCenter)

        subtitle = QLabel("ENGINEERING DECK · 系统维护中枢")
        subtitle.setStyleSheet("color: #667788; font-size: 11px; letter-spacing: 3px; background: transparent;")
        hl.addWidget(subtitle, alignment=Qt.AlignCenter)

        line = QFrame(); line.setFixedHeight(2)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(130,145,165,50),
                stop:0.5 rgba(160,175,195,120),
                stop:0.7 rgba(130,145,165,50), stop:1 transparent);
            border: none;
        """)
        hl.addWidget(line)
        layout.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)
        layout.addWidget(self.tabs)

        self._build_base_info_tab()
        self._build_activation_tab()
        self._build_cloud_tab()
        self._build_logs_tab()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_hud'):
            self._hud.setGeometry(0, 0, self.width(), self.height())

    # ═══════ Tab 1: 基础信息 ═══════════
    def _build_base_info_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setSpacing(10); l.setContentsMargins(16, 12, 16, 12)

        # 公司信息
        grp = QGroupBox("公司信息"); grp.setStyleSheet("""
            QGroupBox { color: #889999; font-weight: 700; font-size: 13px;
                border: 1px solid rgba(130,145,165,35); border-radius: 10px;
                margin-top: 12px; padding-top: 18px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; }
            QLabel { color: #889999; font-size: 12px; background: transparent; }
        """)
        fl = QFormLayout(grp); fl.setSpacing(10)
        fl.setContentsMargins(20, 16, 20, 16)

        self.edit_company = QLineEdit(); self.edit_company.setPlaceholderText("公司名称")
        self.edit_contact = QLineEdit(); self.edit_contact.setPlaceholderText("联系人")
        self.edit_phone = QLineEdit(); self.edit_phone.setPlaceholderText("联系电话")
        self.edit_email = QLineEdit(); self.edit_email.setPlaceholderText("邮箱")
        self.edit_address = QLineEdit(); self.edit_address.setPlaceholderText("地址")
        self.edit_tax_id = QLineEdit(); self.edit_tax_id.setPlaceholderText("税号")
        self.edit_bank = QLineEdit(); self.edit_bank.setPlaceholderText("开户行")
        self.edit_bank_acc = QLineEdit(); self.edit_bank_acc.setPlaceholderText("银行账号")

        for w in [self.edit_company, self.edit_contact, self.edit_phone,
                   self.edit_email, self.edit_address, self.edit_tax_id, self.edit_bank, self.edit_bank_acc]:
            w.setStyleSheet(INPUT_STYLE)

        fl.addRow("公司名称:", self.edit_company)
        fl.addRow("联系人:", self.edit_contact)
        fl.addRow("联系电话:", self.edit_phone)
        fl.addRow("邮箱:", self.edit_email)
        fl.addRow("地址:", self.edit_address)
        fl.addRow("税号:", self.edit_tax_id)
        fl.addRow("开户行:", self.edit_bank)
        fl.addRow("银行账号:", self.edit_bank_acc)
        l.addWidget(grp)

        # 按钮
        ar = QHBoxLayout()
        save = QPushButton("保存"); save.setStyleSheet(BTN_PRIMARY); save.clicked.connect(self._save_base_info)
        ar.addStretch(); ar.addWidget(save)
        l.addLayout(ar)
        l.addStretch()

        self.tabs.addTab(tab, "基础信息")

    def _save_base_info(self):
        info_file = os.path.join(DATA_DIR, "company_info.json")
        data = {
            "company_name": self.edit_company.text().strip(),
            "contact": self.edit_contact.text().strip(),
            "phone": self.edit_phone.text().strip(),
            "email": self.edit_email.text().strip(),
            "address": self.edit_address.text().strip(),
            "tax_id": self.edit_tax_id.text().strip(),
            "bank": self.edit_bank.text().strip(),
            "bank_account": self.edit_bank_acc.text().strip(),
        }
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._log_op("基础信息", "保存", "公司信息已更新")
        QMessageBox.information(self, "提示", "基础信息已保存")

    def _load_base_info(self):
        info_file = os.path.join(DATA_DIR, "company_info.json")
        if os.path.exists(info_file):
            with open(info_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.edit_company.setText(data.get("company_name", ""))
            self.edit_contact.setText(data.get("contact", ""))
            self.edit_phone.setText(data.get("phone", ""))
            self.edit_email.setText(data.get("email", ""))
            self.edit_address.setText(data.get("address", ""))
            self.edit_tax_id.setText(data.get("tax_id", ""))
            self.edit_bank.setText(data.get("bank", ""))
            self.edit_bank_acc.setText(data.get("bank_account", ""))

    # ═══════ Tab 2: 激活码 ═══════════
    def _build_activation_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setSpacing(10); l.setContentsMargins(16, 12, 16, 12)

        # 生成
        gen = QGroupBox("生成激活码"); gen.setStyleSheet("""
            QGroupBox { color: #889999; font-weight: 700; font-size: 13px;
                border: 1px solid rgba(130,145,165,35); border-radius: 10px;
                margin-top: 12px; padding-top: 18px;
            }
            QGroupBox::title { left: 14px; padding: 0 6px; }
            QLabel { color: #889999; background: transparent; }
        """)
        gl = QHBoxLayout(gen); gl.setSpacing(12)
        gl.addWidget(QLabel("类型:"))
        self.act_type = QComboBox(); self.act_type.addItems(["试用","月卡","季卡","年卡","永久"]); self.act_type.setStyleSheet(INPUT_STYLE)
        gl.addWidget(self.act_type)
        gl.addWidget(QLabel("天数:"))
        self.act_days = QComboBox(); self.act_days.addItems(["7","15","30","90","365","9999"]); self.act_days.setStyleSheet(INPUT_STYLE)
        gl.addWidget(self.act_days)
        gl.addWidget(QLabel("数量:"))
        self.act_count = QComboBox(); self.act_count.addItems(["1","5","10","20","50"]); self.act_count.setStyleSheet(INPUT_STYLE)
        gl.addWidget(self.act_count)
        gen_btn = QPushButton("生成"); gen_btn.setStyleSheet(BTN_PRIMARY); gen_btn.clicked.connect(self._gen_activation)
        gl.addWidget(gen_btn); gl.addStretch()
        l.addWidget(gen)

        # 统计
        sc = QHBoxLayout()
        self.act_total_lbl = QLabel("总数: —"); sc.addWidget(self._mini_card("总数", self.act_total_lbl))
        self.act_used_lbl = QLabel("已用: —"); sc.addWidget(self._mini_card("已用", self.act_used_lbl))
        self.act_avail_lbl = QLabel("可用: —"); sc.addWidget(self._mini_card("可用", self.act_avail_lbl))
        sc.addStretch()
        l.addLayout(sc)

        # 搜索
        sr = QHBoxLayout()
        sr.addWidget(QLabel("搜索:"))
        self.act_search = QLineEdit(); self.act_search.setPlaceholderText("激活码或用户"); self.act_search.setMaximumWidth(200)
        self.act_search.setStyleSheet(INPUT_STYLE); self.act_search.textChanged.connect(self._load_activation)
        sr.addWidget(self.act_search); sr.addStretch()

        batch = QPushButton("批量操作"); batch.setStyleSheet(BTN_GREEN)
        sr.addWidget(batch)
        l.addLayout(sr)

        self.act_table = QTableWidget()
        self.act_table.setColumnCount(6)
        self.act_table.setHorizontalHeaderLabels(["ID","激活码","类型","天数","状态","使用者"])
        self.act_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.act_table.setStyleSheet(TABLE_STYLE)
        self.act_table.setEditTriggers(QTableWidget.NoEditTriggers)
        l.addWidget(self.act_table)

        self.tabs.addTab(tab, "激活码")

    def _mini_card(self, label, val_label):
        card = QFrame()
        card.setStyleSheet("background: rgba(18,20,24,230); border: 1px solid rgba(130,145,165,30); border-radius: 8px; padding: 8px 16px;")
        cl = QVBoxLayout(card); cl.setContentsMargins(0,0,0,0)
        lb = QLabel(label); lb.setStyleSheet("color: #667788; font-size: 10px; background:transparent;")
        cl.addWidget(lb); cl.addWidget(val_label)
        return card

    def _gen_activation(self):
        import random, string
        code_type = self.act_type.currentText()
        days = int(self.act_days.currentText())
        count = int(self.act_count.currentText())
        db = os.path.join(DATA_DIR, "activation.db")
        conn = sqlite3.connect(db)
        codes = []
        for _ in range(count):
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
            conn.execute("INSERT INTO activation(code, code_type, duration_days) VALUES(?,?,?)", (code, code_type, days))
            codes.append(code)
        conn.commit(); conn.close()
        self._log_op("激活码", "生成", f"生成 {count} 个 {code_type} 激活码({days}天)")
        QMessageBox.information(self, "生成成功", f"已生成 {count} 个激活码\n示例: {codes[0]}")
        self._load_activation()

    def _load_activation(self):
        search = self.act_search.text().strip() if hasattr(self, 'act_search') else ""
        db = os.path.join(DATA_DIR, "activation.db")
        conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
        if search:
            rows = conn.execute("SELECT * FROM activation WHERE code LIKE ? OR used_by LIKE ? ORDER BY id DESC",
                                (f"%{search}%", f"%{search}%")).fetchall()
        else:
            rows = conn.execute("SELECT * FROM activation ORDER BY id DESC LIMIT 100").fetchall()
        total = conn.execute("SELECT COUNT(*) as c FROM activation").fetchone()['c']
        used = conn.execute("SELECT COUNT(*) as c FROM activation WHERE is_used=1").fetchone()['c']
        conn.close()

        self.act_total_lbl.setText(str(total))
        self.act_used_lbl.setText(str(used))
        self.act_avail_lbl.setText(str(total - used))

        self.act_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.act_table.setItem(i, 0, QTableWidgetItem(str(r['id'])))
            self.act_table.setItem(i, 1, QTableWidgetItem(r['code']))
            self.act_table.setItem(i, 2, QTableWidgetItem(r['code_type']))
            self.act_table.setItem(i, 3, QTableWidgetItem(str(r['duration_days'])))
            status_text = "已使用" if r['is_used'] else "未使用"
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QColor("#ffaa44") if r['is_used'] else QColor("#44cc88"))
            self.act_table.setItem(i, 4, status_item)
            self.act_table.setItem(i, 5, QTableWidgetItem(r['used_by'] or "-"))

    # ═══════ Tab 3: 云端同步 ═══════════
    def _build_cloud_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setSpacing(10); l.setContentsMargins(16, 12, 16, 12)

        # 连接状态
        status_card = QFrame()
        status_card.setStyleSheet("background: rgba(16,18,22,230); border: 1px solid rgba(130,145,165,35); border-radius: 10px; padding: 14px;")
        sl = QHBoxLayout(status_card)
        self.cloud_status = QLabel("未连接"); self.cloud_status.setStyleSheet("color: #888888; font-size: 14px; font-weight: 700; background:transparent;")
        sl.addWidget(self.cloud_status)
        sl.addStretch()
        conn_btn = QPushButton("连接 Supabase"); conn_btn.setStyleSheet(BTN_PRIMARY)
        sl.addWidget(conn_btn)
        l.addWidget(status_card)

        # 同步控制
        sync_panel = QGroupBox("数据同步"); sync_panel.setStyleSheet("""
            QGroupBox { color: #889999; font-weight: 700; font-size: 13px;
                border: 1px solid rgba(130,145,165,35); border-radius: 10px;
                margin-top: 12px; padding-top: 18px;
            }
            QGroupBox::title { left: 14px; padding: 0 6px; }
            QLabel { color: #889999; background: transparent; }
        """)
        sl2 = QHBoxLayout(sync_panel); sl2.setSpacing(12)
        sl2.addWidget(QLabel("同步表:"))
        self.sync_tables = QComboBox(); self.sync_tables.addItems(["全部","订单","产品","客户","会员","财务","激活码","日志"])
        self.sync_tables.setStyleSheet(INPUT_STYLE)
        sl2.addWidget(self.sync_tables)

        pull = QPushButton("拉取"); pull.setStyleSheet(BTN_PRIMARY)
        push = QPushButton("推送"); push.setStyleSheet(BTN_GREEN)
        sl2.addWidget(pull); sl2.addWidget(push)
        sl2.addStretch()
        l.addWidget(sync_panel)

        # 同步日志
        log_label = QLabel("同步日志:"); log_label.setStyleSheet("color: #667788; font-size: 11px; background:transparent;")
        l.addWidget(log_label)
        self.cloud_log = QTextEdit(); self.cloud_log.setReadOnly(True)
        self.cloud_log.setStyleSheet(INPUT_STYLE)
        l.addWidget(self.cloud_log)

        self.tabs.addTab(tab, "云端同步")

    # ═══════ Tab 4: 系统日志 ═══════════
    def _build_logs_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setSpacing(10); l.setContentsMargins(16, 12, 16, 12)

        # 筛选
        sr = QHBoxLayout()
        sr.addWidget(QLabel("日志类型:"))
        self.log_type = QComboBox(); self.log_type.addItems(["操作日志","同步状态","错误日志"]); self.log_type.setStyleSheet(INPUT_STYLE)
        self.log_type.currentTextChanged.connect(self._load_logs)
        sr.addWidget(self.log_type); sr.addStretch()

        clear_btn = QPushButton("清除30天前"); clear_btn.setStyleSheet(BTN_DANGER); clear_btn.clicked.connect(self._clear_old_logs)
        sr.addWidget(clear_btn)
        l.addLayout(sr)

        self.log_table = QTableWidget()
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.log_table.setStyleSheet(TABLE_STYLE)
        self.log_table.setEditTriggers(QTableWidget.NoEditTriggers)
        l.addWidget(self.log_table)

        self.tabs.addTab(tab, "系统日志")

    def _load_logs(self):
        log_type = self.log_type.currentText()
        if log_type == "操作日志":
            table, headers = "op_logs", ["ID","模块","操作","详情","时间"]
            cols = ['id','module','action','detail','created_at']
        elif log_type == "同步状态":
            table, headers = "sync_logs", ["ID","同步类型","状态","详情","时间"]
            cols = ['id','sync_type','status','detail','created_at']
        else:
            table, headers = "error_logs", ["ID","模块","错误","详情","时间"]
            cols = ['id','module','error','detail','created_at']

        db = os.path.join(DATA_DIR, "system_logs.db")
        conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
        rows = conn.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 200").fetchall(); conn.close()

        self.log_table.clear()
        self.log_table.setColumnCount(len(headers))
        self.log_table.setHorizontalHeaderLabels(headers)
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.log_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, k in enumerate(cols):
                self.log_table.setItem(i, j, QTableWidgetItem(str(r[k]) if r[k] is not None else ""))

    def _clear_old_logs(self):
        cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        db = os.path.join(DATA_DIR, "system_logs.db")
        conn = sqlite3.connect(db)
        for tbl in ["op_logs", "sync_logs", "error_logs"]:
            conn.execute(f"DELETE FROM {tbl} WHERE created_at < ?", (cutoff,))
        conn.commit(); conn.close()
        self._log_op("系统日志", "清理", "清除30天前日志")
        self._load_logs()
        QMessageBox.information(self, "提示", f"已清理 {cutoff} 之前的日志")

    def _log_op(self, module, action, detail):
        try:
            db = os.path.join(DATA_DIR, "system_logs.db")
            conn = sqlite3.connect(db)
            conn.execute("INSERT INTO op_logs(module, action, detail) VALUES(?,?,?)", (module, action, detail))
            conn.commit(); conn.close()
        except: pass

    def _load_all(self):
        try: self._load_base_info()
        except: pass
        try: self._load_activation()
        except: pass
        try: self._load_logs()
        except: pass