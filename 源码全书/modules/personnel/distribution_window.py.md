# `modules/personnel/distribution_window.py`

> 路径：`modules/personnel/distribution_window.py` | 行数：813


---


```python
"""
Distribution Management · CREW
完整的 QMainWindow 分销管理窗口，金色渐变主题
一比一复刻桌面版 modules/distribution/distribution_window.py 全部功能
对接 modules.personnel.distribution_service
"""
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QMessageBox, QHeaderView, QDialog, QFormLayout,
    QDoubleSpinBox, QTabWidget, QComboBox, QFrame, QGroupBox
)
from PyQt5.QtCore import Qt, QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import (
    QPainter, QColor, QLinearGradient, QPen, QBrush, QFont, QPainterPath,
    QRadialGradient
)

from modules.personnel.distribution_service import (
    add_commission, get_all_links, get_all_commissions, get_all_team_members,
    get_distribution_stats, create_link, increment_click, increment_register,
    add_team_member, update_commission_status, update_link_status,
    delete_link, remove_team_member, search_commissions,
    export_commissions_csv, export_team_csv,
)

from core.paths import DATA_DIR

DB_FILE = os.path.join(DATA_DIR, "distribution.db")

# ═══════ 宇宙金色 QSS ═══════
WINDOW_QSS = """
    QMainWindow {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #0d0904, stop:1 #1a1008);
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

BTN_GOLD = """
    QPushButton {
        background: rgba(210,160,40,40);
        color: #ffddaa;
        border: 1px solid rgba(210,160,40,40);
        border-radius: 16px; padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(230,180,50,70); }
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
BTN_DANGER = """
    QPushButton {
        background: rgba(200,60,40,40);
        color: #ffaaaa;
        border: 1px solid rgba(200,80,50,60);
        border-radius: 16px; padding: 6px 18px; font-size: 11px;
    }
    QPushButton:hover { background: rgba(220,80,50,70); }
"""
BTN_BLUE = """
    QPushButton {
        background: rgba(60,120,220,40);
        color: #aaccff;
        border: 1px solid rgba(80,140,240,60);
        border-radius: 16px; padding: 6px 18px; font-size: 11px;
    }
    QPushButton:hover { background: rgba(80,160,240,70); }
"""
BTN_ORANGE = """
    QPushButton {
        background: rgba(253,126,20,50);
        color: #ffcc88;
        border: 1px solid rgba(253,126,20,60);
        border-radius: 16px; padding: 6px 18px; font-size: 11px;
    }
    QPushButton:hover { background: rgba(253,140,40,80); }
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
TAB_QSS = """
    QTabWidget::pane {
        background: transparent; border: none;
    }
    QTabBar::tab {
        background: rgba(20,14,6,180);
        color: #998866;
        border: 1px solid rgba(210,160,40,20);
        border-radius: 8px; padding: 8px 24px;
        font-size: 12px; font-weight: 600;
        margin-right: 4px;
    }
    QTabBar::tab:selected {
        background: rgba(210,160,40,40);
        color: #ffddaa;
        border: 1px solid rgba(210,160,40,60);
    }
    QTabBar::tab:hover { background: rgba(210,160,40,25); }
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


# ═══════════ 金色统计卡片 ═══════════
class GoldStatCard(QFrame):
    def __init__(self, title, color_start, color_end, parent=None):
        super().__init__(parent)
        self._title = title
        self._value_str = "0"
        self._color_start = QColor(*color_start)
        self._color_end = QColor(*color_end)
        self.setFixedSize(180, 80)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def set_value(self, v):
        self._value_str = str(v)
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
        painter.setFont(QFont("sans-serif", 22, QFont.Bold))
        painter.drawText(14, 56, self._value_str)
        painter.end()


# ═══════════════ DistributionWindow ═══════════════
class DistributionWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("分销管理 · CREW")
        self.setMinimumSize(1200, 750)
        self.setStyleSheet(WINDOW_QSS)
        self._init_ui()
        self._load_all()

    # ── UI 构建 ──
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # ── 标题栏 ──
        top_row = QHBoxLayout()
        title = QLabel("分销管理")
        title.setStyleSheet(
            "color: #ffddaa; font-size: 20px; font-weight: 800; "
            "letter-spacing: 8px; background: transparent;"
        )
        top_row.addWidget(title)
        top_row.addStretch()

        # 统计标签
        self.stats_label = QLabel("加载中...")
        self.stats_label.setStyleSheet(
            "color: #998866; font-size: 13px; background: transparent;"
        )
        top_row.addWidget(self.stats_label)
        top_row.addSpacing(16)

        btn_back = QPushButton("返回")
        btn_back.setStyleSheet(BTN_GOLD)
        btn_back.clicked.connect(self._go_back)
        btn_back.setFixedWidth(80)
        top_row.addWidget(btn_back)
        main_layout.addLayout(top_row)

        # ── 分隔线 ──
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            "stop:0 transparent, stop:0.3 rgba(210,160,40,40), "
            "stop:0.5 rgba(210,160,40,80), "
            "stop:0.7 rgba(210,160,40,40), stop:1 transparent); "
            "border: none;"
        )
        main_layout.addWidget(sep)

        # ── Tab 切换 ──
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_QSS)
        main_layout.addWidget(self.tabs)

        # ===== Tab 1: 分销链接 =====
        tab_links = QWidget()
        ll = QVBoxLayout(tab_links)
        ll.setContentsMargins(10, 10, 10, 10)
        ll.setSpacing(8)

        r1 = QHBoxLayout()
        r1.addWidget(QLabel("搜索用户:"))
        self.link_search = QLineEdit()
        self.link_search.setPlaceholderText("输入用户ID或邀请码")
        self.link_search.textChanged.connect(self._search_links)
        r1.addWidget(self.link_search)
        r1.addStretch()
        btn_create_link = QPushButton("创建链接")
        btn_create_link.setStyleSheet(BTN_GREEN)
        btn_create_link.clicked.connect(self._show_create_link_dialog)
        r1.addWidget(btn_create_link)
        ll.addLayout(r1)

        self.link_table = QTableWidget()
        self.link_table.setColumnCount(7)
        self.link_table.setHorizontalHeaderLabels(
            ["ID", "用户ID", "推广码", "链接", "点击", "注册", "状态"])
        self.link_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.link_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.link_table.setStyleSheet(TABLE_STYLE)
        self.link_table.verticalHeader().setVisible(False)
        ll.addWidget(self.link_table)

        r2 = QHBoxLayout()
        btn_sim_click = QPushButton("模拟点击")
        btn_sim_click.setStyleSheet(BTN_BLUE)
        btn_sim_click.clicked.connect(self._simulate_click)
        r2.addWidget(btn_sim_click)
        btn_sim_reg = QPushButton("模拟注册")
        btn_sim_reg.setStyleSheet(BTN_BLUE)
        btn_sim_reg.clicked.connect(self._simulate_register)
        r2.addWidget(btn_sim_reg)
        r2.addStretch()
        btn_toggle = QPushButton("停用/启用")
        btn_toggle.setStyleSheet(BTN_ORANGE)
        btn_toggle.clicked.connect(self._toggle_link_status)
        r2.addWidget(btn_toggle)
        btn_del_link = QPushButton("删除链接")
        btn_del_link.setStyleSheet(BTN_DANGER)
        btn_del_link.clicked.connect(self._delete_selected_link)
        r2.addWidget(btn_del_link)
        btn_export_links = QPushButton("导出 CSV")
        btn_export_links.setStyleSheet(BTN_GOLD)
        btn_export_links.clicked.connect(self._export_links)
        r2.addWidget(btn_export_links)
        ll.addLayout(r2)
        self.tabs.addTab(tab_links, "分销链接")

        # ===== Tab 2: 佣金记录 =====
        tab_comm = QWidget()
        cl = QVBoxLayout(tab_comm)
        cl.setContentsMargins(10, 10, 10, 10)
        cl.setSpacing(8)

        sr = QHBoxLayout()
        sr.addWidget(QLabel("用户ID:"))
        self.comm_user_search = QLineEdit()
        self.comm_user_search.setPlaceholderText("按用户ID搜索")
        self.comm_user_search.setMaximumWidth(120)
        self.comm_user_search.returnPressed.connect(self._search_commissions)
        sr.addWidget(self.comm_user_search)
        sr.addWidget(QLabel("从:"))
        self.comm_date_from = QLineEdit()
        self.comm_date_from.setPlaceholderText("2024-01-01")
        self.comm_date_from.setMaximumWidth(100)
        sr.addWidget(self.comm_date_from)
        sr.addWidget(QLabel("到:"))
        self.comm_date_to = QLineEdit()
        self.comm_date_to.setPlaceholderText("2024-12-31")
        self.comm_date_to.setMaximumWidth(100)
        sr.addWidget(self.comm_date_to)
        sr.addWidget(QLabel("状态:"))
        self.comm_filter = QComboBox()
        self.comm_filter.addItems(["全部", "pending", "approved", "rejected", "paid"])
        self.comm_filter.setMaximumWidth(100)
        self.comm_filter.currentTextChanged.connect(self._search_commissions)
        sr.addWidget(self.comm_filter)
        btn_search_comm = QPushButton("搜索")
        btn_search_comm.setStyleSheet(BTN_GOLD)
        btn_search_comm.clicked.connect(self._search_commissions)
        sr.addWidget(btn_search_comm)
        btn_clear_comm = QPushButton("清除")
        btn_clear_comm.setStyleSheet(BTN_DANGER)
        btn_clear_comm.clicked.connect(self._clear_comm_search)
        sr.addWidget(btn_clear_comm)
        sr.addStretch()
        btn_add_comm = QPushButton("发放佣金")
        btn_add_comm.setStyleSheet(BTN_ORANGE)
        btn_add_comm.clicked.connect(self._show_add_commission_dialog)
        sr.addWidget(btn_add_comm)
        btn_export_comm = QPushButton("导出 CSV")
        btn_export_comm.setStyleSheet(BTN_GOLD)
        btn_export_comm.clicked.connect(self._export_commissions)
        sr.addWidget(btn_export_comm)
        cl.addLayout(sr)

        self.comm_table = QTableWidget()
        self.comm_table.setColumnCount(7)
        self.comm_table.setHorizontalHeaderLabels(
            ["ID", "用户ID", "来源用户", "金额", "类型", "状态", "时间"])
        self.comm_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.comm_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.comm_table.setStyleSheet(TABLE_STYLE)
        self.comm_table.verticalHeader().setVisible(False)
        cl.addWidget(self.comm_table)

        ar = QHBoxLayout()
        btn_approve = QPushButton("审批通过")
        btn_approve.setStyleSheet(BTN_GREEN)
        btn_approve.clicked.connect(lambda: self._update_comm_status("approved"))
        ar.addWidget(btn_approve)
        btn_reject = QPushButton("拒绝")
        btn_reject.setStyleSheet(BTN_DANGER)
        btn_reject.clicked.connect(lambda: self._update_comm_status("rejected"))
        ar.addWidget(btn_reject)
        btn_pending = QPushButton("改回待审")
        btn_pending.setStyleSheet(BTN_ORANGE)
        btn_pending.clicked.connect(lambda: self._update_comm_status("pending"))
        ar.addWidget(btn_pending)
        btn_paid = QPushButton("标记已付")
        btn_paid.setStyleSheet(BTN_BLUE)
        btn_paid.clicked.connect(lambda: self._update_comm_status("paid"))
        ar.addWidget(btn_paid)
        ar.addStretch()
        btn_del_comm = QPushButton("删除记录")
        btn_del_comm.setStyleSheet(BTN_DANGER)
        btn_del_comm.clicked.connect(self._delete_commission)
        ar.addWidget(btn_del_comm)
        cl.addLayout(ar)
        self.tabs.addTab(tab_comm, "佣金记录")

        # ===== Tab 3: 团队管理 =====
        tab_team = QWidget()
        tl = QVBoxLayout(tab_team)
        tl.setContentsMargins(10, 10, 10, 10)
        tl.setSpacing(8)

        tr = QHBoxLayout()
        tr.addWidget(QLabel("搜索用户:"))
        self.team_search = QLineEdit()
        self.team_search.setPlaceholderText("输入用户ID或上级ID")
        self.team_search.textChanged.connect(self._search_team)
        tr.addWidget(self.team_search)
        tr.addStretch()
        btn_add_team = QPushButton("添加成员")
        btn_add_team.setStyleSheet(BTN_GREEN)
        btn_add_team.clicked.connect(self._show_add_team_dialog)
        tr.addWidget(btn_add_team)
        btn_rem_team = QPushButton("移除成员")
        btn_rem_team.setStyleSheet(BTN_DANGER)
        btn_rem_team.clicked.connect(self._remove_selected_member)
        tr.addWidget(btn_rem_team)
        btn_export_team = QPushButton("导出 CSV")
        btn_export_team.setStyleSheet(BTN_GOLD)
        btn_export_team.clicked.connect(self._export_team)
        tr.addWidget(btn_export_team)
        tl.addLayout(tr)

        self.team_table = QTableWidget()
        self.team_table.setColumnCount(5)
        self.team_table.setHorizontalHeaderLabels(
            ["ID", "用户ID", "上级ID", "层级", "加入时间"])
        self.team_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.team_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.team_table.setStyleSheet(TABLE_STYLE)
        self.team_table.verticalHeader().setVisible(False)
        tl.addWidget(self.team_table)
        self.tabs.addTab(tab_team, "团队管理")

    # ═══════ 数据加载 ═══════
    def _load_all(self):
        self._load_links()
        self._search_commissions()
        self._load_team()

    def _load_links(self):
        rows = get_all_links()
        self.link_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.link_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.link_table.setItem(i, 1, QTableWidgetItem(str(r["user_name"])))
            self.link_table.setItem(i, 2, QTableWidgetItem(str(r["code"])))
            self.link_table.setItem(i, 3, QTableWidgetItem(str(r.get("url") or "")))
            self.link_table.setItem(i, 4, QTableWidgetItem(str(r["click_count"])))
            self.link_table.setItem(i, 5, QTableWidgetItem(str(r["register_count"])))
            status_item = QTableWidgetItem(str(r["status"]))
            if r["status"] == "active":
                status_item.setForeground(QColor(136, 255, 187))
            elif r["status"] == "inactive":
                status_item.setForeground(QColor(255, 170, 170))
            self.link_table.setItem(i, 6, status_item)
        self._update_stats()

    def _search_links(self):
        text = self.link_search.text().strip()
        if not text:
            self._load_links()
            return
        rows = [r for r in get_all_links()
                if text.lower() in str(r.get("user_name", "")).lower()
                or text.lower() in str(r.get("code", "")).lower()]
        self.link_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.link_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.link_table.setItem(i, 1, QTableWidgetItem(str(r["user_name"])))
            self.link_table.setItem(i, 2, QTableWidgetItem(str(r["code"])))
            self.link_table.setItem(i, 3, QTableWidgetItem(str(r.get("url") or "")))
            self.link_table.setItem(i, 4, QTableWidgetItem(str(r["click_count"])))
            self.link_table.setItem(i, 5, QTableWidgetItem(str(r["register_count"])))
            self.link_table.setItem(i, 6, QTableWidgetItem(str(r["status"])))

    def _search_commissions(self, _=None):
        user_text = self.comm_user_search.text().strip()
        uid = int(user_text) if user_text else None
        date_from = self.comm_date_from.text().strip() or None
        date_to = self.comm_date_to.text().strip() or None
        status = self.comm_filter.currentText()
        status_filter = None if (not status or status == "全部") else status
        rows = search_commissions(
            user_id=uid, date_from=date_from, date_to=date_to,
            status=status_filter
        )
        self.comm_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.comm_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.comm_table.setItem(i, 1, QTableWidgetItem(str(r["user_name"])))
            self.comm_table.setItem(i, 2, QTableWidgetItem(str(r.get("from_user_name") or "")))
            self.comm_table.setItem(i, 3, QTableWidgetItem(f"{r['amount']:.2f}"))
            self.comm_table.setItem(i, 4, QTableWidgetItem(str(r["type"])))
            status_item = QTableWidgetItem(str(r["status"]))
            if r["status"] == "approved":
                status_item.setForeground(QColor(136, 255, 187))
            elif r["status"] == "rejected":
                status_item.setForeground(QColor(255, 170, 170))
            elif r["status"] == "paid":
                status_item.setForeground(QColor(170, 200, 255))
            self.comm_table.setItem(i, 5, status_item)
            self.comm_table.setItem(i, 6, QTableWidgetItem(str(r.get("created_at") or "")))
        self._update_stats()

    def _clear_comm_search(self):
        self.comm_user_search.clear()
        self.comm_date_from.clear()
        self.comm_date_to.clear()
        self.comm_filter.setCurrentText("全部")
        self._search_commissions()

    def _load_team(self):
        rows = get_all_team_members()
        self.team_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.team_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.team_table.setItem(i, 1, QTableWidgetItem(str(r["user_name"])))
            self.team_table.setItem(i, 2, QTableWidgetItem(str(r["parent_name"])))
            self.team_table.setItem(i, 3, QTableWidgetItem(str(r["level"])))
            self.team_table.setItem(i, 4, QTableWidgetItem(str(r.get("created_at") or "")))
        self._update_stats()

    def _search_team(self):
        text = self.team_search.text().strip()
        if not text:
            self._load_team()
            return
        rows = [r for r in get_all_team_members()
                if text.lower() in str(r.get("user_name", "")).lower()
                or text.lower() in str(r.get("parent_name", "")).lower()]
        self.team_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.team_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.team_table.setItem(i, 1, QTableWidgetItem(str(r["user_name"])))
            self.team_table.setItem(i, 2, QTableWidgetItem(str(r["parent_name"])))
            self.team_table.setItem(i, 3, QTableWidgetItem(str(r["level"])))
            self.team_table.setItem(i, 4, QTableWidgetItem(str(r.get("created_at") or "")))

    def _update_stats(self):
        s = get_distribution_stats()
        self.stats_label.setText(
            f"链接: {s['links']} | 总点击: {s['clicks']} | "
            f"佣金: {s['commissions_count']}笔 ¥{s['commissions_amount']:.2f} | "
            f"团队: {s['team_size']}人"
        )

    # ═══════ 操作 - 链接 ═══════
    def _show_create_link_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("创建分销链接")
        dlg.setMinimumWidth(420)
        dlg.setStyleSheet(DIALOG_QSS)
        layout = QFormLayout(dlg)
        layout.setSpacing(12)
        user_input = QLineEdit()
        user_input.setPlaceholderText("输入用户ID")
        layout.addRow("用户ID:", user_input)
        code_input = QLineEdit()
        code_input.setPlaceholderText("留空自动生成")
        layout.addRow("推广码:", code_input)
        url_input = QLineEdit()
        url_input.setPlaceholderText("https://example.com/ref/...")
        layout.addRow("链接URL:", url_input)
        btn = QPushButton("创建")
        btn.setStyleSheet(BTN_GREEN)
        def do_create():
            uid = user_input.text().strip()
            if not uid:
                QMessageBox.warning(dlg, "提示", "用户ID不能为空")
                return
            try:
                uid_int = int(uid)
            except ValueError:
                QMessageBox.warning(dlg, "格式错误", "用户ID必须是整数")
                return
            code = code_input.text().strip()
            url = url_input.text().strip()
            result = create_link(user_id=uid_int, code=code or None, url=url or None)
            if result["ok"]:
                QMessageBox.information(dlg, "成功",
                    f"链接已创建\n推广码: {result.get('code', code)}")
                self._load_links()
                dlg.accept()
            else:
                err = result.get("error", "未知错误")
                if "UNIQUE constraint" in err or "已存在" in err:
                    QMessageBox.warning(dlg, "错误", "推广码已存在")
                else:
                    QMessageBox.warning(dlg, "错误", f"创建失败: {err}")
        btn.clicked.connect(do_create)
        layout.addRow(btn)
        dlg.exec_()

    def _toggle_link_status(self):
        row = self.link_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个链接")
            return
        link_id = int(self.link_table.item(row, 0).text())
        current_status = self.link_table.item(row, 6).text()
        new_status = "inactive" if current_status == "active" else "active"
        result = update_link_status(link_id, new_status)
        if result["ok"]:
            self._load_links()
            QMessageBox.information(self, "成功", f"链接状态已更新为: {new_status}")

    def _delete_selected_link(self):
        row = self.link_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个链接")
            return
        link_id = int(self.link_table.item(row, 0).text())
        if QMessageBox.question(self, "确认", f"确定删除链接 #{link_id}？",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        result = delete_link(link_id)
        if result["ok"]:
            self._load_links()

    def _simulate_click(self):
        row = self.link_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个链接")
            return
        code = self.link_table.item(row, 2).text()
        result = increment_click(code)
        if result["ok"]:
            self._load_links()
            QMessageBox.information(self, "完成", "点击数 +1")
        else:
            QMessageBox.warning(self, "错误", result.get("error", "操作失败"))

    def _simulate_register(self):
        row = self.link_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个链接")
            return
        code = self.link_table.item(row, 2).text()
        result = increment_register(code)
        if result["ok"]:
            self._load_links()
            QMessageBox.information(self, "完成", "注册数 +1")
        else:
            QMessageBox.warning(self, "错误", result.get("error", "操作失败"))

    def _export_links(self):
        import csv
        filepath = os.path.join(DATA_DIR,
            f"links_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        rows = get_all_links()
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(["ID", "用户ID", "推广码", "链接", "点击", "注册", "状态"])
            for r in rows:
                w.writerow([r["id"], r["user_name"], r["code"], r.get("url", ""),
                            r["click_count"], r["register_count"], r.get("status", "")])
        QMessageBox.information(self, "导出成功", f"已导出 {len(rows)} 条链接到:\n{filepath}")

    # ═══════ 操作 - 佣金 ═══════
    def _show_add_commission_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("发放佣金")
        dlg.setMinimumWidth(420)
        dlg.setStyleSheet(DIALOG_QSS)
        layout = QFormLayout(dlg)
        layout.setSpacing(12)
        user_input = QLineEdit()
        user_input.setPlaceholderText("受益用户ID")
        layout.addRow("用户ID:", user_input)
        from_input = QLineEdit()
        from_input.setPlaceholderText("来源用户ID（可选）")
        layout.addRow("来源用户:", from_input)
        amt = QDoubleSpinBox()
        amt.setRange(0.01, 999999)
        amt.setValue(10)
        amt.setDecimals(2)
        layout.addRow("金额:", amt)
        type_combo = QComboBox()
        type_combo.addItems(["direct", "indirect", "team", "referral"])
        layout.addRow("类型:", type_combo)
        desc = QLineEdit()
        desc.setText("后台发放")
        layout.addRow("备注:", desc)
        btn = QPushButton("确认发放")
        btn.setStyleSheet(BTN_ORANGE)
        def do_add():
            uid = user_input.text().strip()
            if not uid:
                QMessageBox.warning(dlg, "提示", "用户ID不能为空")
                return
            try:
                uid_int = int(uid)
            except ValueError:
                QMessageBox.warning(dlg, "格式错误", "用户ID必须是整数")
                return
            from_uid = from_input.text().strip()
            from_uid_int = int(from_uid) if from_uid else None
            result = add_commission(
                user_id=uid_int,
                amount=amt.value(),
                from_user_id=from_uid_int,
                comm_type=type_combo.currentText(),
                description=desc.text()
            )
            if result["ok"]:
                warn = ""
                if result.get("wallet_error"):
                    warn = f"\n⚠️ 钱包同步失败: {result['wallet_error']}"
                QMessageBox.information(dlg, "成功",
                    f"佣金 {amt.value():.2f} 已发放给 {uid}{warn}")
                self._search_commissions()
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "失败", f"发放失败: {result.get('error', '未知错误')}")
        btn.clicked.connect(do_add)
        layout.addRow(btn)
        dlg.exec_()

    def _update_comm_status(self, status):
        row = self.comm_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一条佣金记录")
            return
        comm_id = int(self.comm_table.item(row, 0).text())
        result = update_commission_status(comm_id, status)
        if result["ok"]:
            self._search_commissions()
            QMessageBox.information(self, "成功", f"佣金状态已更新为: {status}")
        else:
            QMessageBox.warning(self, "失败", result.get("error", "操作失败"))

    def _delete_commission(self):
        row = self.comm_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一条佣金记录")
            return
        comm_id = int(self.comm_table.item(row, 0).text())
        if QMessageBox.question(self, "确认", f"确定删除佣金记录 #{comm_id}？",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        from modules.personnel import distribution_service
        result = distribution_service.delete_commission(comm_id)
        if result["ok"]:
            self._search_commissions()

    def _export_commissions(self):
        result = export_commissions_csv()
        if result["ok"]:
            QMessageBox.information(self, "导出成功",
                f"已导出 {result['count']} 条记录到:\n{result['filepath']}")

    # ═══════ 操作 - 团队 ═══════
    def _show_add_team_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("添加团队成员")
        dlg.setMinimumWidth(380)
        dlg.setStyleSheet(DIALOG_QSS)
        layout = QFormLayout(dlg)
        layout.setSpacing(12)
        user_input = QLineEdit()
        user_input.setPlaceholderText("成员用户ID")
        layout.addRow("成员ID:", user_input)
        parent_input = QLineEdit()
        parent_input.setPlaceholderText("上级用户ID")
        layout.addRow("上级ID:", parent_input)
        btn = QPushButton("添加")
        btn.setStyleSheet(BTN_GREEN)
        def do_add():
            uid = user_input.text().strip()
            pid = parent_input.text().strip()
            if not uid or not pid:
                QMessageBox.warning(dlg, "提示", "成员ID和上级ID都不能为空")
                return
            try:
                uid_int = int(uid)
                pid_int = int(pid)
            except ValueError:
                QMessageBox.warning(dlg, "格式错误", "ID必须是整数")
                return
            result = add_team_member(user_id=uid_int, parent_id=pid_int)
            if result["ok"]:
                QMessageBox.information(dlg, "成功",
                    f"成员 {uid} 已添加到 {pid} 团队")
                self._load_team()
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "失败", f"添加失败: {result.get('error', '未知错误')}")
        btn.clicked.connect(do_add)
        layout.addRow(btn)
        dlg.exec_()

    def _remove_selected_member(self):
        row = self.team_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个成员")
            return
        member_id = int(self.team_table.item(row, 0).text())
        if QMessageBox.question(self, "确认", f"确定移除成员 #{member_id}？",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        result = remove_team_member(member_id)
        if result["ok"]:
            self._load_team()

    def _export_team(self):
        result = export_team_csv()
        if result["ok"]:
            QMessageBox.information(self, "导出成功",
                f"已导出 {result['count']} 条记录到:\n{result['filepath']}")

    # ═══════ 导航 ═══════
    def _go_back(self):
        self.close()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = DistributionWindow()
    w.show()
    sys.exit(app.exec_())

```
