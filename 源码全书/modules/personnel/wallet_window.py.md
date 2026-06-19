# `modules/personnel/wallet_window.py`

> 路径：`modules/personnel/wallet_window.py` | 行数：1574


---


```python
# -*- coding: utf-8 -*-
"""
钱包管理界面（宇宙版）
所有数据库操作委托给 wallet_service，UI 只负责展示和交互。
一比一完整复刻桌面版 4Tab QMainWindow。
"""
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QMessageBox, QHeaderView, QDialog, QGroupBox,
    QDoubleSpinBox, QComboBox, QTabWidget, QAbstractItemView,
    QTextEdit, QGridLayout, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

import subprocess

from core.dark_theme import (
    apply_dark_theme,
    BG_MAIN, BG_CARD, BG_INPUT,
    BTN_NORMAL, BTN_HOVER, BTN_PRESSED,
    TEXT_WHITE, TEXT_LIGHT, TEXT_MUTED,
    ACCENT, SUCCESS, WARNING, DANGER, PURPLE,
    BORDER, BORDER_LIGHT
)
from modules.personnel.wallet_service import (
    init_db,
    init_address_book_db,
    add_address,
    get_addresses,
    update_address,
    delete_address,
    get_all_wallets,
    get_wallet,
    get_or_create_wallet,
    recharge,
    withdraw,
    transfer,
    add_commission,
    get_transactions,
    get_wallet_stats,
    update_wallet_status,
    get_income_expense_report,
    get_balance_trend,
    get_pending_withdrawals,
    get_all_withdrawal_requests,
    submit_withdrawal_request,
    approve_withdrawal,
    reject_withdrawal,
    cancel_withdrawal_request,
    delete_withdrawal_request,
    clear_withdrawal_queue,
    delete_wallet,
    delete_transaction,
    get_top_wallets,
    export_transactions_to_csv,
)


# ──────────────────────────────────────────
#  Stat Card Widget
# ──────────────────────────────────────────
class StatCard(QFrame):
    def __init__(self, title: str, value: str, color: str = ACCENT, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"background-color: {BG_CARD}; border-left: 4px solid {color}; "
            "border-radius: 4px; padding: 12px;"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        layout.addWidget(lbl_title)
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold;")
        self.lbl_value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.lbl_value)
        self.setMinimumWidth(180)

    def set_value(self, value: str):
        self.lbl_value.setText(value)


# ──────────────────────────────────────────
#  钱包主窗口
# ──────────────────────────────────────────
class WalletWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        apply_dark_theme(self)
        self.setWindowTitle("钱包管理")
        self.setMinimumSize(1200, 800)
        init_db()
        self.init_ui()
        self.load_dashboard()
        self.load_wallets()
        self.load_transactions()

    # ──────────────────────────────────────
    #  UI 初始化
    # ──────────────────────────────────────
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)

        # 标题栏
        top_layout = QHBoxLayout()
        title = QLabel("💰 钱包管理")
        title.setFont(QFont("PingFang SC", 18, QFont.Bold))
        top_layout.addWidget(title)
        top_layout.addStretch()
        btn_export = QPushButton("📥 导出 CSV")
        btn_export.setStyleSheet(self._btn_style(SUCCESS))
        btn_export.clicked.connect(self._do_export_csv)
        top_layout.addWidget(btn_export)
        btn_back = QPushButton("返回主控")
        btn_back.setStyleSheet(self._btn_style(TEXT_MUTED))
        btn_back.clicked.connect(self._go_back)
        top_layout.addWidget(btn_back)
        layout.addLayout(top_layout)

        # Tab 控件
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # ── Tab 0: 📊 看板 ──
        self._build_dashboard_tab()

        # ── Tab 1: 💼 钱包列表 ──
        self._build_wallets_tab()

        # ── Tab 2: 📋 交易记录 ──
        self._build_transactions_tab()

        # ── Tab 3: ⏳ 提现审批 ──
        self._build_withdrawal_queue_tab()

    # ──────────────────────────────────────
    #  Tab 0: 看板
    # ──────────────────────────────────────
    def _build_dashboard_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(16)

        hdr = QLabel("📊 钱包总览")
        hdr.setFont(QFont("PingFang SC", 16, QFont.Bold))
        l.addWidget(hdr)

        # Stat Cards 行
        card_layout = QHBoxLayout()
        card_layout.setSpacing(16)
        self.card_balance = StatCard("💰 总余额", "—", ACCENT)
        self.card_frozen = StatCard("❄️ 总冻结", "—", TEXT_MUTED)
        self.card_income = StatCard("📈 总收入", "—", SUCCESS)
        self.card_withdraw = StatCard("📤 总提现", "—", WARNING)
        self.card_pending = StatCard("⏳ 待审批", "—", DANGER)
        for c in [self.card_balance, self.card_frozen,
                  self.card_income, self.card_withdraw, self.card_pending]:
            card_layout.addWidget(c)
        card_layout.addStretch()
        l.addLayout(card_layout)

        # 收支报表行
        report_layout = QHBoxLayout()
        report_layout.setSpacing(16)

        # 最近30天收支
        fr_report = QFrame()
        rl = QVBoxLayout(fr_report)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.addWidget(QLabel("📅 近30天收支"))
        self.lbl_income = QLabel("收入: —")
        self.lbl_expense = QLabel("支出: —")
        self.lbl_net = QLabel("净额: —")
        for w in [self.lbl_income, self.lbl_expense, self.lbl_net]:
            w.setStyleSheet("font-size: 14px; padding: 4px;")
        rl.addWidget(self.lbl_income)
        rl.addWidget(self.lbl_expense)
        rl.addWidget(self.lbl_net)

        # Top 5 钱包
        fr_top = QFrame()
        tl2 = QVBoxLayout(fr_top)
        tl2.setContentsMargins(0, 0, 0, 0)
        tl2.addWidget(QLabel("🏆 Top 5 钱包"))
        self.top_table = QTableWidget()
        self.top_table.setColumnCount(4)
        self.top_table.setHorizontalHeaderLabels(["用户", "余额", "冻结", "可用"])
        self.top_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.top_table.setMaximumHeight(160)
        self.top_table.setEditTriggers(QTableWidget.NoEditTriggers)
        tl2.addWidget(self.top_table)

        report_layout.addWidget(fr_report, 1)
        report_layout.addWidget(fr_top, 2)
        l.addLayout(report_layout)

        # 余额趋势图（文字版）
        fr_trend = QFrame()
        trend_layout = QVBoxLayout(fr_trend)
        trend_layout.setContentsMargins(0, 0, 0, 0)
        trend_layout.addWidget(QLabel("📈 近7天余额趋势"))
        self.trend_text = QTextEdit()
        self.trend_text.setMaximumHeight(160)
        self.trend_text.setReadOnly(True)
        self.trend_text.setStyleSheet(
            f"QTextEdit {{ font-family: Menlo, 'Courier New', monospace; "
            f"font-size: 12px; background: {BG_INPUT}; border: 1px solid {BORDER_LIGHT}; "
            f"border-radius: 4px; padding: 8px; }}"
        )
        trend_layout.addWidget(self.trend_text)
        l.addWidget(fr_trend, 0)

        # 最近交易
        fr_recent = QFrame()
        rrl = QVBoxLayout(fr_recent)
        rrl.setContentsMargins(0, 0, 0, 0)
        rrl.addWidget(QLabel("🕐 最近交易（全局）"))
        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(5)
        self.recent_table.setHorizontalHeaderLabels(["ID", "用户", "类型", "金额", "时间"])
        self.recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.recent_table.setEditTriggers(QTableWidget.NoEditTriggers)
        rrl.addWidget(self.recent_table)

        l.addWidget(fr_recent, 1)
        l.addStretch()

        self.tabs.addTab(tab, "📊 看板")

    # ──────────────────────────────────────
    #  Tab 1: 钱包列表
    # ──────────────────────────────────────
    def _build_wallets_tab(self):
        tab = QWidget()
        wl = QVBoxLayout(tab)
        wl.setContentsMargins(10, 10, 10, 10)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 搜索用户:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入用户ID搜索")
        self.search_input.textChanged.connect(self.load_wallets)
        search_layout.addWidget(self.search_input)
        search_layout.addStretch()
        btn_create = QPushButton("➕ 创建钱包")
        btn_create.setStyleSheet(self._btn_style(SUCCESS))
        btn_create.clicked.connect(self._show_create_dialog)
        search_layout.addWidget(btn_create)
        wl.addLayout(search_layout)

        self.wallet_table = QTableWidget()
        self.wallet_table.setColumnCount(8)
        self.wallet_table.setHorizontalHeaderLabels(
            ["ID", "用户ID", "余额", "冻结", "可用", "总收入", "总提现", "状态"]
        )
        self.wallet_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.wallet_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.wallet_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.wallet_table.itemSelectionChanged.connect(self._on_wallet_selected)
        wl.addWidget(self.wallet_table)

        # 操作按钮行
        btn_layout = QHBoxLayout()
        for label, color, handler in [
            ("💰 充值",      ACCENT,  self._show_recharge_dialog),
            ("📥 提现申请",  WARNING, self._show_withdrawal_request_dialog),
            ("🔄 转账",      PURPLE,  self._show_transfer_dialog),
            ("🎁 发放佣金",  SUCCESS, self._show_commission_dialog),
            ("🚫 封禁/激活", DANGER,  self._toggle_status),
            ("🗑 删除钱包",  TEXT_MUTED, self._do_delete_wallet),
        ]:
            btn = QPushButton(label)
            btn.setStyleSheet(self._btn_style(color))
            btn.clicked.connect(handler)
            btn_layout.addWidget(btn)
        btn_layout.addStretch()
        wl.addLayout(btn_layout)
        self.tabs.addTab(tab, "💼 钱包列表")

    # ──────────────────────────────────────
    #  Tab 2: 交易记录
    # ──────────────────────────────────────
    def _build_transactions_tab(self):
        tab = QWidget()
        tl = QVBoxLayout(tab)
        tl.setContentsMargins(10, 10, 10, 10)

        # 第1行：基本筛选
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("筛选:"))
        self.filter_type = QComboBox()
        self.filter_type.addItems(
            ["全部", "recharge", "withdraw", "transfer_in", "transfer_out",
             "commission", "freeze", "unfreeze"]
        )
        filter_layout.addWidget(self.filter_type)
        filter_layout.addWidget(QLabel(" 关键词:"))
        self.filter_desc = QLineEdit()
        self.filter_desc.setPlaceholderText("描述关键词...")
        self.filter_desc.setMaximumWidth(150)
        filter_layout.addWidget(self.filter_desc)
        filter_layout.addWidget(QLabel(" 金额区间:"))
        self.filter_min_amt = QLineEdit()
        self.filter_min_amt.setPlaceholderText("最小")
        self.filter_min_amt.setMaximumWidth(80)
        filter_layout.addWidget(self.filter_min_amt)
        filter_layout.addWidget(QLabel("~"))
        self.filter_max_amt = QLineEdit()
        self.filter_max_amt.setPlaceholderText("最大")
        self.filter_max_amt.setMaximumWidth(80)
        filter_layout.addWidget(self.filter_max_amt)
        filter_layout.addStretch()
        btn_search = QPushButton("🔍 搜索")
        btn_search.setStyleSheet(self._btn_style(ACCENT))
        btn_search.clicked.connect(self.load_transactions)
        filter_layout.addWidget(btn_search)
        btn_refresh = QPushButton("🔄 刷新")
        btn_refresh.setStyleSheet(self._btn_style(TEXT_MUTED))
        btn_refresh.clicked.connect(self.load_transactions)
        filter_layout.addWidget(btn_refresh)
        btn_del_txn = QPushButton("🗑 删除")
        btn_del_txn.setStyleSheet(self._btn_style(DANGER))
        btn_del_txn.clicked.connect(self._do_delete_transaction)
        filter_layout.addWidget(btn_del_txn)
        tl.addLayout(filter_layout)

        # 第2行：日期范围
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("📅 日期范围:"))
        self.filter_start_date = QLineEdit()
        self.filter_start_date.setPlaceholderText("开始日期，如 2025-01-01")
        self.filter_start_date.setMaximumWidth(160)
        date_layout.addWidget(self.filter_start_date)
        date_layout.addWidget(QLabel(" 至 "))
        self.filter_end_date = QLineEdit()
        self.filter_end_date.setPlaceholderText("结束日期，如 2025-12-31")
        self.filter_end_date.setMaximumWidth(160)
        date_layout.addWidget(self.filter_end_date)
        date_layout.addStretch()
        btn_clear = QPushButton("🧹 清空条件")
        btn_clear.setStyleSheet(self._btn_style(TEXT_MUTED))
        btn_clear.clicked.connect(self._clear_txn_filters)
        date_layout.addWidget(btn_clear)
        tl.addLayout(date_layout)

        self.txn_table = QTableWidget()
        self.txn_table.setColumnCount(7)
        self.txn_table.setHorizontalHeaderLabels(
            ["", "ID", "钱包ID", "类型", "金额", "余额后", "描述", "时间"]
        )
        self.txn_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.txn_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.txn_table.setSelectionBehavior(QTableWidget.SelectRows)
        tl.addWidget(self.txn_table)
        self.tabs.addTab(tab, "📋 交易记录")

    # ──────────────────────────────────────
    #  Tab 3: 提现审批
    # ──────────────────────────────────────
    def _build_withdrawal_queue_tab(self):
        tab = QWidget()
        vl = QVBoxLayout(tab)
        vl.setContentsMargins(10, 10, 10, 10)

        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("⏳ 提现审批队列"))
        hdr.addStretch()
        self.queue_filter = QComboBox()
        self.queue_filter.addItems(["全部", "pending", "approved", "rejected", "cancelled"])
        self.queue_filter.currentTextChanged.connect(self.load_withdrawal_queue)
        hdr.addWidget(QLabel("状态:"))
        hdr.addWidget(self.queue_filter)
        btn_reload = QPushButton("🔄 刷新")
        btn_reload.setStyleSheet(self._btn_style(TEXT_MUTED))
        btn_reload.clicked.connect(self.load_withdrawal_queue)
        hdr.addWidget(btn_reload)
        vl.addLayout(hdr)

        self.withdraw_table = QTableWidget()
        self.withdraw_table.setColumnCount(8)
        self.withdraw_table.setHorizontalHeaderLabels(
            ["ID", "用户ID", "金额", "申请时间", "状态", "审批人", "审批时间", "操作"]
        )
        self.withdraw_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.withdraw_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.withdraw_table.itemSelectionChanged.connect(self._on_withdrawal_selected)
        vl.addWidget(self.withdraw_table)

        # 批量操作
        btn_ops = QHBoxLayout()
        self.btn_approve = QPushButton("✅ 审批通过")
        self.btn_approve.setStyleSheet(self._btn_style(SUCCESS))
        self.btn_approve.clicked.connect(self._do_approve_withdrawal)
        self.btn_reject = QPushButton("❌ 审批拒绝")
        self.btn_reject.setStyleSheet(self._btn_style(DANGER))
        self.btn_reject.clicked.connect(self._do_reject_withdrawal)
        self.btn_cancel_req = QPushButton("❎ 取消申请")
        self.btn_cancel_req.setStyleSheet(self._btn_style(WARNING))
        self.btn_cancel_req.clicked.connect(self._do_cancel_withdrawal)
        self.btn_del_req = QPushButton("🗑 删除记录")
        self.btn_del_req.setStyleSheet(self._btn_style(TEXT_MUTED))
        self.btn_del_req.clicked.connect(self._do_delete_withdrawal_request)
        self.btn_clear_all = QPushButton("🧹 全部清理")
        self.btn_clear_all.setStyleSheet(self._btn_style(TEXT_MUTED))
        self.btn_clear_all.clicked.connect(self._do_clear_withdrawal_queue)
        self.lbl_selected_req = QLabel("请选择一条待审批记录")
        self.lbl_selected_req.setStyleSheet(f"color: {TEXT_MUTED};")
        btn_ops.addWidget(self.btn_approve)
        btn_ops.addWidget(self.btn_reject)
        btn_ops.addWidget(self.btn_cancel_req)
        btn_ops.addWidget(self.btn_del_req)
        btn_ops.addWidget(self.btn_clear_all)
        btn_ops.addWidget(self.lbl_selected_req)
        btn_ops.addStretch()
        vl.addLayout(btn_ops)

        self.tabs.addTab(tab, "⏳ 提现审批")

        # ═══════════════════════════════════════════════
        #  批量操作 Tab
        # ═══════════════════════════════════════════════
        tab_batch = QWidget()
        self.tabs.addTab(tab_batch, "批量操作")
        self._init_batch_tab(tab_batch)

        # === 地址簿 ===
        tab_addr = QWidget()
        tal = QVBoxLayout(tab_addr)
        tal.setContentsMargins(10, 10, 10, 10)
        addr_h = QHBoxLayout()
        addr_h.addWidget(QLabel("地址簿"))
        addr_h.addStretch()
        self.addr_owner_input = QLineEdit()
        self.addr_owner_input.setPlaceholderText("所属用户")
        self.addr_owner_input.setMaximumWidth(150)
        self.addr_owner_input.textChanged.connect(self._load_address_book)
        addr_h.addWidget(self.addr_owner_input)
        btn_add_addr = QPushButton("添加地址")
        btn_add_addr.setStyleSheet(self._btn_style(SUCCESS))
        btn_add_addr.clicked.connect(self._show_add_address_dialog)
        addr_h.addWidget(btn_add_addr)
        btn_edit_addr = QPushButton("编辑地址")
        btn_edit_addr.setStyleSheet(self._btn_style(ACCENT))
        btn_edit_addr.clicked.connect(self._edit_address)
        addr_h.addWidget(btn_edit_addr)
        tal.addLayout(addr_h)
        self.addr_table = QTableWidget()
        self.addr_table.setColumnCount(5)
        self.addr_table.setHorizontalHeaderLabels(["ID", "标签", "地址", "类型", "备注"])
        self.addr_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.addr_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.addr_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tal.addWidget(self.addr_table)
        addr_btn_h = QHBoxLayout()
        btn_del_addr = QPushButton("删除选中")
        btn_del_addr.setStyleSheet(self._btn_style(DANGER))
        btn_del_addr.clicked.connect(self._delete_address)
        addr_btn_h.addWidget(btn_del_addr)
        addr_btn_h.addStretch()
        tal.addLayout(addr_btn_h)
        self.tabs.addTab(tab_addr, "地址簿")

    def _init_batch_tab(self, tab: QWidget):
        vl = QVBoxLayout(tab)
        vl.setContentsMargins(15, 15, 15, 15)
        vl.addWidget(QLabel("<b>📦 批量操作</b> — 可一次性向多个用户充值/转账/发佣金"))
        vl.addSpacing(5)

        # ── 批量充值 ──────────────────────────────────
        group_rech = QGroupBox("💰 批量充值")
        rech_layout = QVBoxLayout()

        rech_table_layout = QHBoxLayout()
        self.batch_rech_table = QTableWidget(0, 3)
        self.batch_rech_table.setHorizontalHeaderLabels(["用户ID", "金额", "备注"])
        self.batch_rech_table.setMinimumHeight(120)
        self.batch_rech_table.horizontalHeader().setStretchLastSection(True)
        rech_table_layout.addWidget(self.batch_rech_table)

        rech_btn_col = QVBoxLayout()
        btn_add_rech = QPushButton("➕ 添加行")
        btn_add_rech.clicked.connect(
            lambda: self._add_batch_row(self.batch_rech_table))
        btn_del_rech = QPushButton("🗑 删除选中")
        btn_del_rech.clicked.connect(
            lambda: self._del_batch_row(self.batch_rech_table))
        rech_btn_col.addWidget(btn_add_rech)
        rech_btn_col.addWidget(btn_del_rech)
        rech_btn_col.addStretch()
        rech_table_layout.addLayout(rech_btn_col)
        rech_layout.addLayout(rech_table_layout)

        rech_footer = QHBoxLayout()
        rech_footer.addStretch()
        btn_rech_all = QPushButton("🚀 执行批量充值")
        btn_rech_all.setStyleSheet(self._btn_style(SUCCESS))
        btn_rech_all.clicked.connect(self._do_batch_recharge)
        rech_footer.addWidget(btn_rech_all)
        rech_layout.addLayout(rech_footer)
        group_rech.setLayout(rech_layout)
        vl.addWidget(group_rech)

        # ── 批量转账 ──────────────────────────────────
        group_trans = QGroupBox("🔄 批量转账（单账户→多人）")
        trans_layout = QVBoxLayout()

        from_layout = QHBoxLayout()
        from_layout.addWidget(QLabel("转出用户ID:"))
        self.batch_trans_from = QLineEdit()
        self.batch_trans_from.setPlaceholderText("输入转出方用户ID")
        from_layout.addWidget(self.batch_trans_from)
        from_layout.addWidget(QLabel("说明:"))
        self.batch_trans_desc = QLineEdit()
        self.batch_trans_desc.setPlaceholderText("统一备注（可选）")
        from_layout.addWidget(self.batch_trans_desc)
        trans_layout.addLayout(from_layout)

        trans_table_layout = QHBoxLayout()
        self.batch_trans_table = QTableWidget(0, 2)
        self.batch_trans_table.setHorizontalHeaderLabels(["收款用户ID", "金额"])
        self.batch_trans_table.setMinimumHeight(120)
        trans_table_layout.addWidget(self.batch_trans_table)

        trans_btn_col = QVBoxLayout()
        btn_add_trans = QPushButton("➕ 添加行")
        btn_add_trans.clicked.connect(
            lambda: self._add_batch_row(self.batch_trans_table, cols=2))
        btn_del_trans = QPushButton("🗑 删除选中")
        btn_del_trans.clicked.connect(
            lambda: self._del_batch_row(self.batch_trans_table))
        trans_btn_col.addWidget(btn_add_trans)
        trans_btn_col.addWidget(btn_del_trans)
        trans_btn_col.addStretch()
        trans_table_layout.addLayout(trans_btn_col)
        trans_layout.addLayout(trans_table_layout)

        trans_footer = QHBoxLayout()
        lbl_trans_hint = QLabel("💡 提示：总金额不能超过转出用户可用余额")
        lbl_trans_hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        trans_footer.addWidget(lbl_trans_hint)
        trans_footer.addStretch()
        btn_trans_all = QPushButton("🚀 执行批量转账")
        btn_trans_all.setStyleSheet(self._btn_style(PURPLE))
        btn_trans_all.clicked.connect(self._do_batch_transfer)
        trans_footer.addWidget(btn_trans_all)
        trans_layout.addLayout(trans_footer)
        group_trans.setLayout(trans_layout)
        vl.addWidget(group_trans)

        # ── 批量佣金 ──────────────────────────────────
        group_comm = QGroupBox("🎯 批量发放佣金")
        comm_layout = QVBoxLayout()

        comm_table_layout = QHBoxLayout()
        self.batch_comm_table = QTableWidget(0, 3)
        self.batch_comm_table.setHorizontalHeaderLabels(["用户ID", "佣金金额", "说明"])
        self.batch_comm_table.setMinimumHeight(120)
        comm_table_layout.addWidget(self.batch_comm_table)

        comm_btn_col = QVBoxLayout()
        btn_add_comm = QPushButton("➕ 添加行")
        btn_add_comm.clicked.connect(
            lambda: self._add_batch_row(self.batch_comm_table))
        btn_del_comm = QPushButton("🗑 删除选中")
        btn_del_comm.clicked.connect(
            lambda: self._del_batch_row(self.batch_comm_table))
        comm_btn_col.addWidget(btn_add_comm)
        comm_btn_col.addWidget(btn_del_comm)
        comm_btn_col.addStretch()
        comm_table_layout.addLayout(comm_btn_col)
        comm_layout.addLayout(comm_table_layout)

        comm_footer = QHBoxLayout()
        comm_footer.addStretch()
        btn_comm_all = QPushButton("🚀 执行批量佣金")
        btn_comm_all.setStyleSheet(self._btn_style(PURPLE))
        btn_comm_all.clicked.connect(self._do_batch_commission)
        comm_footer.addWidget(btn_comm_all)
        comm_layout.addLayout(comm_footer)
        group_comm.setLayout(comm_layout)
        vl.addWidget(group_comm)

        vl.addStretch()

    # ──────────────────────────────────────
    #  批量操作辅助方法
    # ──────────────────────────────────────
    def _add_batch_row(self, table: 'QTableWidget', cols: int = None):
        if cols is None:
            cols = table.columnCount()
        table.insertRow(table.rowCount())
        for col in range(cols):
            table.setCellWidget(table.rowCount() - 1, col, QLineEdit())

    def _del_batch_row(self, table: 'QTableWidget'):
        row = table.currentRow()
        if row >= 0:
            table.removeRow(row)

    def _table_to_dicts(self, table: 'QTableWidget',
                        col_keys: list[str]) -> list[dict]:
        items = []
        for row in range(table.rowCount()):
            row_data = {}
            for col, key in enumerate(col_keys):
                w = table.cellWidget(row, col)
                if isinstance(w, QLineEdit):
                    val = w.text().strip()
                else:
                    val = ""
                row_data[key] = val
            if any(v for v in row_data.values()):
                items.append(row_data)
        return items

    def _do_batch_recharge(self):
        items = self._table_to_dicts(
            self.batch_rech_table, ["user_id", "amount", "description"])
        if not items:
            QMessageBox.information(self, "提示", "请先添加充值记录（至少填一行）")
            return
        results = []
        for it in items:
            try:
                amount = float(it["amount"])
                desc = it["description"] or "批量充值"
                r = recharge(it["user_id"], amount, desc)
                results.append({"user_id": it["user_id"], "ok": r["ok"],
                                "error": r.get("error", "")})
            except ValueError:
                results.append({"user_id": it["user_id"], "ok": False,
                                "error": "金额格式错误"})
            except Exception as e:
                results.append({"user_id": it["user_id"], "ok": False,
                                "error": str(e)})
        self._show_batch_result("充值", results)
        self.load_wallets()
        self.load_dashboard()

    def _do_batch_transfer(self):
        from_user = self.batch_trans_from.text().strip()
        if not from_user:
            QMessageBox.information(self, "提示", "请填写转出用户ID")
            return
        desc = self.batch_trans_desc.text().strip()
        items = self._table_to_dicts(
            self.batch_trans_table, ["user_id", "amount"])
        if not items:
            QMessageBox.information(self, "提示", "请先添加转账记录")
            return
        results = []
        for it in items:
            try:
                amount = float(it["amount"])
                r = transfer(from_user, it["user_id"], amount, desc)
                results.append({"user_id": it["user_id"], "ok": r["ok"],
                                "error": r.get("error", "")})
            except ValueError:
                results.append({"user_id": it["user_id"], "ok": False,
                                "error": "金额格式错误"})
            except Exception as e:
                results.append({"user_id": it["user_id"], "ok": False,
                                "error": str(e)})
        self._show_batch_result("批量转账", results)
        self.load_wallets()
        self.load_dashboard()

    def _do_batch_commission(self):
        items = self._table_to_dicts(
            self.batch_comm_table, ["user_id", "amount", "description"])
        if not items:
            QMessageBox.information(self, "提示", "请先添加佣金记录")
            return
        results = []
        for it in items:
            try:
                amount = float(it["amount"])
                desc = it["description"] or "批量佣金"
                r = add_commission(it["user_id"], amount, desc)
                results.append({"user_id": it["user_id"], "ok": r["ok"],
                                "error": r.get("error", "")})
            except ValueError:
                results.append({"user_id": it["user_id"], "ok": False,
                                "error": "金额格式错误"})
            except Exception as e:
                results.append({"user_id": it["user_id"], "ok": False,
                                "error": str(e)})
        self._show_batch_result("佣金发放", results)
        self.load_wallets()
        self.load_dashboard()

    def _show_batch_result(self, operation: str, results: list):
        succeeded = sum(1 for r in results if r.get("ok"))
        failed = len(results) - succeeded
        lines = [f"✅ 成功: {succeeded} 条 | ❌ 失败: {failed} 条\n"]
        for r in results:
            status = "✅" if r.get("ok") else f"❌ {r.get('error', '')}"
            lines.append(f"  {r.get('user_id', '?')} → {status}")
        QMessageBox.information(self, f"{operation}结果", "\n".join(lines))

    # ──────────────────────────────────────
    #  地址簿管理
    # ──────────────────────────────────────
    def _load_address_book(self):
        owner = self.addr_owner_input.text().strip() or None
        rows = get_addresses(owner) if owner else get_addresses()
        self.addr_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.addr_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.addr_table.setItem(i, 1, QTableWidgetItem(str(r.get("label", ""))))
            self.addr_table.setItem(i, 2, QTableWidgetItem(str(r.get("address", ""))))
            self.addr_table.setItem(i, 3, QTableWidgetItem(str(r.get("address_type", ""))))
            self.addr_table.setItem(i, 4, QTableWidgetItem(str(r.get("note", ""))))

    def _show_add_address_dialog(self):
        sel = self._get_selected_wallet()
        default_owner = sel[1] if sel else ""
        dlg = QDialog(self)
        dlg.setWindowTitle("添加地址")
        dlg.setMinimumWidth(400)
        apply_dark_theme(dlg)
        layout = QFormLayout(dlg)
        owner_e = QLineEdit(default_owner)
        owner_e.setPlaceholderText("所属用户ID")
        layout.addRow("所属用户:", owner_e)
        label_e = QLineEdit()
        label_e.setPlaceholderText("如：我的银行卡")
        layout.addRow("标签:", label_e)
        addr_e = QLineEdit()
        addr_e.setPlaceholderText("账户地址/ID")
        layout.addRow("地址:", addr_e)
        type_e = QComboBox()
        type_e.addItems(["user", "bank", "alipay", "wechat", "other"])
        layout.addRow("类型:", type_e)
        note_e = QLineEdit()
        layout.addRow("备注:", note_e)
        btn = QPushButton("保存")
        btn.setStyleSheet(self._btn_style(SUCCESS))

        def do_save():
            owner = owner_e.text().strip()
            label = label_e.text().strip()
            addr = addr_e.text().strip()
            if not owner or not label or not addr:
                QMessageBox.warning(dlg, "提示", "所属用户、标签、地址都不能为空")
                return
            result = add_address(owner, label, addr, type_e.currentText(), note_e.text().strip())
            if result["ok"]:
                QMessageBox.information(dlg, "成功", "地址已添加")
                self._load_address_book()
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "失败", "添加失败: " + result.get("error", "未知错误"))

        btn.clicked.connect(do_save)
        layout.addRow(btn)
        dlg.exec_()

    def _delete_address(self):
        row = self.addr_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择要删除的地址")
            return
        addr_id = int(self.addr_table.item(row, 0).text())
        confirm = QMessageBox.question(self, "确认删除", "确定要删除这条地址吗？",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            result = delete_address(addr_id)
            if result["ok"]:
                self._load_address_book()
                QMessageBox.information(self, "成功", "地址已删除")
            else:
                QMessageBox.warning(self, "失败", "删除失败: " + result.get("error", "未知错误"))

    def _edit_address(self):
        row = self.addr_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择要编辑的地址")
            return
        addr_id = int(self.addr_table.item(row, 0).text())
        old_label = self.addr_table.item(row, 1).text()
        old_addr = self.addr_table.item(row, 2).text()
        old_type = self.addr_table.item(row, 3).text()
        old_note = self.addr_table.item(row, 4).text()
        dlg = QDialog(self)
        dlg.setWindowTitle("编辑地址")
        dlg.setMinimumWidth(400)
        apply_dark_theme(dlg)
        layout = QFormLayout(dlg)
        label_e = QLineEdit(old_label)
        layout.addRow("标签:", label_e)
        addr_e = QLineEdit(old_addr)
        layout.addRow("地址:", addr_e)
        type_e = QComboBox()
        type_e.addItems(["user", "bank", "alipay", "wechat", "other"])
        type_e.setCurrentText(old_type)
        layout.addRow("类型:", type_e)
        note_e = QLineEdit(old_note)
        layout.addRow("备注:", note_e)
        btn = QPushButton("保存修改")
        btn.setStyleSheet(self._btn_style(ACCENT))

        def do_save():
            label = label_e.text().strip()
            addr = addr_e.text().strip()
            if not label or not addr:
                QMessageBox.warning(dlg, "提示", "标签和地址都不能为空")
                return
            result = update_address(addr_id, label=label, address=addr, note=note_e.text().strip())
            if result["ok"]:
                QMessageBox.information(dlg, "成功", "地址已更新")
                self._load_address_book()
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "失败", "更新失败: " + result.get("error", "未知错误"))

        btn.clicked.connect(do_save)
        layout.addRow(btn)
        dlg.exec_()

    @staticmethod
    def _btn_style(color: str) -> str:
        return (
            f"background-color: {color}; color: white; padding: 8px 20px; "
            "border: none; border-radius: 4px; font-size: 14px;"
        )

    # ──────────────────────────────────────
    #  数据加载
    # ──────────────────────────────────────
    def load_dashboard(self):
        stats = get_wallet_stats()
        self.card_balance.set_value(f"¥ {stats['total_balance']:.2f}")
        self.card_frozen.set_value(f"¥ {stats['total_frozen']:.2f}")
        self.card_income.set_value(f"¥ {stats['total_income']:.2f}")
        self.card_withdraw.set_value(f"¥ {stats['total_withdraw']:.2f}")

        pending = get_pending_withdrawals()
        self.card_pending.set_value(str(len(pending)))

        # 收支报表
        report = get_income_expense_report(days=30)
        self.lbl_income.setText(f"📈 收入: ¥{report['income']:.2f}")
        self.lbl_expense.setText(f"📉 支出: ¥{report['expense']:.2f}")
        self.lbl_net.setText(
            f"{'⬆️' if report['net'] >= 0 else '⬇️'} 净额: ¥{report['net']:.2f}"
        )
        self.lbl_income.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {SUCCESS}; padding: 4px;")
        self.lbl_expense.setStyleSheet(f"font-size: 14px; color: {DANGER}; padding: 4px;")
        self.lbl_net.setStyleSheet(
            f"font-size: 14px; font-weight: bold; "
            f"color: {'#28a745' if report['net'] >= 0 else '#dc3545'}; padding: 4px;"
        )

        # Top 5 钱包
        tops = get_top_wallets(limit=5)
        self.top_table.setRowCount(len(tops))
        for i, t in enumerate(tops):
            available = t.get("balance", 0) - t.get("frozen_amount", 0)
            self.top_table.setItem(i, 0, QTableWidgetItem(str(t["user_id"])))
            self.top_table.setItem(i, 1, QTableWidgetItem(f"{t.get('balance', 0):.2f}"))
            self.top_table.setItem(i, 2, QTableWidgetItem(f"{t.get('frozen_amount', 0):.2f}"))
            item_avail = QTableWidgetItem(f"{available:.2f}")
            if available < 0:
                item_avail.setForeground(Qt.red)
            self.top_table.setItem(i, 3, item_avail)

        # 最近全局交易
        init_db()
        from core.database import get_conn
        conn = get_conn("wallet.db")
        rows = conn.execute(
            "SELECT t.*, w.user_id FROM wallet_transactions t "
            "JOIN wallet w ON t.wallet_id=w.id ORDER BY t.id DESC LIMIT 20"
        ).fetchall()

        type_labels = {
            "recharge": "充值", "withdraw": "提现",
            "transfer_in": "转入", "transfer_out": "转出",
            "commission": "佣金", "freeze": "冻结", "unfreeze": "解冻",
        }
        self.recent_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            amt_item = QTableWidgetItem(f"{r['amount']:.2f}")
            if r["amount"] > 0:
                amt_item.setForeground(Qt.darkGreen)
            elif r["amount"] < 0:
                amt_item.setForeground(Qt.red)
            self.recent_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.recent_table.setItem(i, 1, QTableWidgetItem(str(r["user_id"])))
            self.recent_table.setItem(i, 2, QTableWidgetItem(type_labels.get(r["type"], r["type"])))
            self.recent_table.setItem(i, 3, amt_item)
            self.recent_table.setItem(i, 4, QTableWidgetItem(str(r["created_at"])))

        # 余额趋势图
        self._load_trend_chart()

    def _load_trend_chart(self, days: int = 7):
        try:
            trend_data = get_balance_trend(days=days)
        except Exception as e:
            self.trend_text.setHtml(f"<i>趋势数据加载失败: {e}</i>")
            return

        if not trend_data:
            self.trend_text.setHtml("<i>暂无趋势数据</i>")
            return

        lines = []
        lines.append(f"{'日期':<12} {'余额':>12}  趋势")
        lines.append("─" * 60)

        max_balance = max(t["balance"] for t in trend_data) if trend_data else 1
        min_balance = min(t["balance"] for t in trend_data) if trend_data else 0
        chart_width = 20

        for t in trend_data:
            date_str = t["date"][:10] if t["date"] else ""
            bal = t["balance"]
            if max_balance > min_balance:
                ratio = (bal - min_balance) / (max_balance - min_balance)
            else:
                ratio = 0.5
            bar_len = max(1, int(ratio * chart_width))
            bar = "█" * bar_len
            trend_icon = "📈" if t.get("income", 0) > t.get("expense", 0) else "📉"
            income_lbl = f'+{t.get("income", 0):.0f}'
            exp_lbl = f'-{t.get("expense", 0):.0f}'
            lines.append(
                f"{date_str:<12} {bal:>12,.2f}  {bar} {trend_icon}  "
                f"收入:{income_lbl} 支出:{exp_lbl}"
            )

        lines.append("─" * 60)
        lines.append(f"最高: {max_balance:,.2f}   最低: {min_balance:,.2f}   "
                     f"当前: {trend_data[-1]['balance'] if trend_data else 0:,.2f}")

        self.trend_text.setPlainText("\n".join(lines))

    def load_wallets(self):
        search = self.search_input.text().strip()
        wallets = get_all_wallets(search=search if search else "")
        self.wallet_table.setRowCount(len(wallets))
        for i, w in enumerate(wallets):
            frozen = w.get("frozen_amount", 0)
            available = w.get("balance", 0) - frozen
            status_text = "✅ 正常" if w.get("status") == "active" else f"❌ {w.get('status', '')}"
            for col, val in enumerate([
                str(w["id"]), str(w["user_id"]),
                f"{w.get('balance', 0):.2f}", f"{frozen:.2f}",
                f"{available:.2f}",
                f"{w.get('total_income', 0):.2f}",
                f"{w.get('total_withdraw', 0):.2f}",
                status_text,
            ]):
                item = QTableWidgetItem(val)
                if col == 4 and available < 0:
                    item.setForeground(Qt.red)
                self.wallet_table.setItem(i, col, item)

    def load_transactions(self, _=None):
        selected_row = self.wallet_table.currentRow()
        wallet_id = None
        if selected_row >= 0:
            wallet_id = int(self.wallet_table.item(selected_row, 0).text())

        txn_type = self.filter_type.currentText()
        txn_type = "" if txn_type == "全部" else txn_type
        keyword = self.filter_desc.text().strip()
        start_date = self.filter_start_date.text().strip()
        end_date = self.filter_end_date.text().strip()

        min_amt, max_amt = None, None
        try:
            if self.filter_min_amt.text().strip():
                min_amt = float(self.filter_min_amt.text())
        except ValueError:
            QMessageBox.warning(self, "格式错误", "最小金额格式错误")
            return
        try:
            if self.filter_max_amt.text().strip():
                max_amt = float(self.filter_max_amt.text())
        except ValueError:
            QMessageBox.warning(self, "格式错误", "最大金额格式错误")
            return

        txns = get_transactions(
            wallet_id=wallet_id,
            txn_type=txn_type,
            start_date=start_date,
            end_date=end_date,
            min_amount=min_amt,
            max_amount=max_amt,
            keyword=keyword,
            limit=500,
        )

        self.txn_table.setRowCount(len(txns))
        type_labels = {
            "recharge": "充值", "withdraw": "提现",
            "transfer_in": "转入", "transfer_out": "转出",
            "commission": "佣金", "freeze": "冻结", "unfreeze": "解冻",
        }
        for i, t in enumerate(txns):
            label = type_labels.get(t["type"], t["type"])
            amt_item = QTableWidgetItem(f"{t['amount']:.2f}")
            if t["amount"] > 0:
                amt_item.setForeground(Qt.darkGreen)
            elif t["amount"] < 0:
                amt_item.setForeground(Qt.red)
            self.txn_table.setItem(i, 0, QTableWidgetItem(str(t["id"])))
            self.txn_table.setItem(i, 1, QTableWidgetItem(str(t["wallet_id"])))
            self.txn_table.setItem(i, 2, QTableWidgetItem(label))
            self.txn_table.setItem(i, 3, amt_item)
            self.txn_table.setItem(i, 4, QTableWidgetItem(f"{t['balance_after']:.2f}"))
            self.txn_table.setItem(i, 5, QTableWidgetItem(t.get("description") or ""))
            self.txn_table.setItem(i, 6, QTableWidgetItem(str(t["created_at"])))

    def _clear_txn_filters(self):
        self.filter_type.setCurrentIndex(0)
        self.filter_desc.clear()
        self.filter_min_amt.clear()
        self.filter_max_amt.clear()
        self.filter_start_date.clear()
        self.filter_end_date.clear()
        self.load_transactions()

    def load_withdrawal_queue(self, _=None):
        status = self.queue_filter.currentText()
        status = "" if status == "全部" else status
        requests = get_all_withdrawal_requests(status=status)
        self.withdraw_table.setRowCount(len(requests))
        for i, req in enumerate(requests):
            status_item = QTableWidgetItem(req["status"])
            status_item.setForeground(Qt.red if req["status"] == "pending" else Qt.darkGreen)
            self.withdraw_table.setItem(i, 0, QTableWidgetItem(str(req["id"])))
            self.withdraw_table.setItem(i, 1, QTableWidgetItem(str(req["user_id"])))
            self.withdraw_table.setItem(i, 2, QTableWidgetItem(f"{req['amount']:.2f}"))
            self.withdraw_table.setItem(i, 3, QTableWidgetItem(str(req["created_at"])))
            self.withdraw_table.setItem(i, 4, status_item)
            self.withdraw_table.setItem(i, 5, QTableWidgetItem(req.get("reviewed_by") or "—"))
            self.withdraw_table.setItem(i, 6, QTableWidgetItem(req.get("reviewed_at") or "—"))
            self.withdraw_table.setItem(i, 7, QTableWidgetItem(req.get("note") or "—"))

    def _on_wallet_selected(self):
        pass

    def _on_withdrawal_selected(self):
        row = self.withdraw_table.currentRow()
        if row < 0:
            self.lbl_selected_req.setText("请选择一条待审批记录")
            return
        req_id = self.withdraw_table.item(row, 0).text()
        user_id = self.withdraw_table.item(row, 1).text()
        amount = self.withdraw_table.item(row, 2).text()
        status = self.withdraw_table.item(row, 4).text()
        if status == "pending":
            self.lbl_selected_req.setText(
                f"已选: #{req_id} | {user_id} | ¥{amount}"
            )
        else:
            self.lbl_selected_req.setText(f"#{req_id} - {status}")

    # ──────────────────────────────────────
    #  操作对话框
    # ──────────────────────────────────────
    def _get_selected_wallet(self):
        row = self.wallet_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先在表格中选择一个钱包")
            return None
        return (
            int(self.wallet_table.item(row, 0).text()),
            self.wallet_table.item(row, 1).text(),
        )

    def _show_create_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("创建钱包")
        dlg.setMinimumWidth(350)
        apply_dark_theme(dlg)
        layout = QFormLayout(dlg)
        user_input = QLineEdit()
        user_input.setPlaceholderText("输入用户ID")
        layout.addRow("用户ID:", user_input)
        btn = QPushButton("创建")
        btn.setStyleSheet(self._btn_style(SUCCESS))

        def do_create():
            uid = user_input.text().strip()
            if not uid:
                QMessageBox.warning(dlg, "提示", "用户ID不能为空")
                return
            result = get_or_create_wallet(uid)
            if result.get("id"):
                QMessageBox.information(dlg, "成功", f"钱包已创建: {uid}（ID: {result['id']}）")
                self.load_wallets()
                self.load_dashboard()
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "错误", "创建失败")

        btn.clicked.connect(do_create)
        layout.addRow(btn)
        dlg.exec_()

    def _show_recharge_dialog(self):
        sel = self._get_selected_wallet()
        if not sel:
            return
        wallet_id, user_id = sel
        dlg = QDialog(self)
        dlg.setWindowTitle(f"💰 充值 - {user_id}")
        dlg.setMinimumWidth(350)
        apply_dark_theme(dlg)
        layout = QFormLayout(dlg)
        amt = QDoubleSpinBox()
        amt.setRange(0.01, 999999)
        amt.setValue(100)
        amt.setDecimals(2)
        layout.addRow("金额:", amt)
        desc = QLineEdit()
        desc.setText("后台充值")
        layout.addRow("备注:", desc)
        btn = QPushButton("确认充值")
        btn.setStyleSheet(self._btn_style(ACCENT))

        def do():
            result = recharge(user_id, amt.value(), desc.text())
            if result["ok"]:
                QMessageBox.information(dlg, "成功",
                    f"充值 {amt.value():.2f} 成功\n新余额: {result['balance']:.2f}")
                self.load_wallets()
                self.load_transactions()
                self.load_dashboard()
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "错误", result.get("error", "充值失败"))

        btn.clicked.connect(do)
        layout.addRow(btn)
        dlg.exec_()

    def _show_withdrawal_request_dialog(self):
        sel = self._get_selected_wallet()
        if not sel:
            return
        wallet_id, user_id = sel
        w = get_wallet(user_id)
        available = w.get("balance", 0) - w.get("frozen_amount", 0)

        dlg = QDialog(self)
        dlg.setWindowTitle(f"📥 提现申请 - {user_id}")
        dlg.setMinimumWidth(380)
        apply_dark_theme(dlg)
        layout = QFormLayout(dlg)
        info = QLabel(f"当前可用余额: ¥{available:.2f}（冻结中金额不会影响可用余额）")
        info.setStyleSheet(f"color: {TEXT_MUTED}; padding: 4px;")
        layout.addRow(info)
        amt = QDoubleSpinBox()
        amt.setRange(0.01, available if available > 0 else 0.01)
        amt.setDecimals(2)
        layout.addRow("提现金额:", amt)
        desc = QLineEdit()
        desc.setPlaceholderText("可选备注（如银行账号）")
        layout.addRow("备注:", desc)
        note_lbl = QLabel(
            "💡 提交后将冻结金额，等待审批通过后正式扣款\n"
            "审批拒绝后金额自动解冻"
        )
        note_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; padding: 4px;")
        layout.addRow(note_lbl)
        btn = QPushButton("提交申请")
        btn.setStyleSheet(self._btn_style(WARNING))

        def do():
            if amt.value() <= 0:
                QMessageBox.warning(dlg, "提示", "金额必须大于 0")
                return
            result = submit_withdrawal_request(user_id, amt.value(), desc.text())
            if result["ok"]:
                QMessageBox.information(dlg, "成功", result.get("message", "申请已提交"))
                self.load_wallets()
                self.load_withdrawal_queue()
                self.load_dashboard()
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "错误", result.get("error", "提交失败"))

        btn.clicked.connect(do)
        layout.addRow(btn)
        dlg.exec_()

    def _show_transfer_dialog(self):
        sel = self._get_selected_wallet()
        if not sel:
            return
        _, from_user = sel
        w = get_wallet(from_user)
        available = w.get("balance", 0) - w.get("frozen_amount", 0)

        dlg = QDialog(self)
        dlg.setWindowTitle(f"🔄 转账 - {from_user}")
        dlg.setMinimumWidth(380)
        apply_dark_theme(dlg)
        layout = QFormLayout(dlg)
        layout.addRow(QLabel(f"可用余额: ¥{available:.2f}"))
        to_input = QLineEdit()
        to_input.setPlaceholderText("目标用户ID")
        layout.addRow("转入用户:", to_input)
        amt = QDoubleSpinBox()
        amt.setRange(0.01, available)
        amt.setDecimals(2)
        layout.addRow("金额:", amt)
        desc = QLineEdit()
        desc.setPlaceholderText("可选备注")
        layout.addRow("备注:", desc)
        btn = QPushButton("确认转账")
        btn.setStyleSheet(self._btn_style(PURPLE))

        def do():
            to_user = to_input.text().strip()
            if not to_user:
                QMessageBox.warning(dlg, "提示", "目标用户ID不能为空")
                return
            result = transfer(from_user, to_user, amt.value(), desc.text())
            if result["ok"]:
                QMessageBox.information(dlg, "成功",
                    f"转账 {amt.value():.2f} 给 {to_user} 成功\n"
                    f"你的新余额: {result['from_balance']:.2f}")
                self.load_wallets()
                self.load_transactions()
                self.load_dashboard()
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "错误", result.get("error", "转账失败"))

        btn.clicked.connect(do)
        layout.addRow(btn)
        dlg.exec_()

    def _show_commission_dialog(self):
        sel = self._get_selected_wallet()
        if not sel:
            return
        wallet_id, user_id = sel
        dlg = QDialog(self)
        dlg.setWindowTitle(f"🎁 发放佣金 - {user_id}")
        dlg.setMinimumWidth(350)
        apply_dark_theme(dlg)
        layout = QFormLayout(dlg)
        amt = QDoubleSpinBox()
        amt.setRange(0.01, 999999)
        amt.setDecimals(2)
        layout.addRow("佣金金额:", amt)
        desc = QLineEdit()
        desc.setText("佣金收入")
        layout.addRow("描述:", desc)
        btn = QPushButton("确认发放")
        btn.setStyleSheet(self._btn_style(SUCCESS))

        def do():
            result = add_commission(user_id, amt.value(), desc.text())
            if result["ok"]:
                QMessageBox.information(dlg, "成功",
                    f"佣金 {amt.value():.2f} 发放成功\n新余额: {result['balance']:.2f}")
                self.load_wallets()
                self.load_transactions()
                self.load_dashboard()
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "错误", result.get("error", "发放失败"))

        btn.clicked.connect(do)
        layout.addRow(btn)
        dlg.exec_()

    def _toggle_status(self):
        sel = self._get_selected_wallet()
        if not sel:
            return
        wallet_id, user_id = sel
        w = get_wallet(user_id)
        current = w.get("status", "active")
        new_status = "banned" if current == "active" else "active"
        msg = f"确认要将用户 {user_id} 的钱包" + ("封禁" if new_status == "banned" else "激活") + "？"
        reply = QMessageBox.question(self, "确认", msg, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            result = update_wallet_status(user_id, new_status)
            if result["ok"]:
                QMessageBox.information(self, "成功", f"钱包已{'封禁' if new_status == 'banned' else '激活'}")
                self.load_wallets()
            else:
                QMessageBox.warning(self, "错误", result.get("error", "操作失败"))

    def _do_approve_withdrawal(self):
        row = self.withdraw_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一条待审批记录")
            return
        req_id = int(self.withdraw_table.item(row, 0).text())
        status = self.withdraw_table.item(row, 4).text()
        if status != "pending":
            QMessageBox.information(self, "提示", "该记录已处理，无需重复审批")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("审批备注")
        dlg.setMinimumWidth(350)
        apply_dark_theme(dlg)
        layout = QFormLayout(dlg)
        note = QLineEdit()
        layout.addRow("审批备注:", note)
        btn = QPushButton("确认通过")
        btn.setStyleSheet(self._btn_style(SUCCESS))

        def do():
            result = approve_withdrawal(req_id, operator="admin", note=note.text())
            if result["ok"]:
                QMessageBox.information(self, "成功",
                    f"提现 ¥{result['amount']:.2f} 已通过，金额已正式扣款")
                self.load_wallets()
                self.load_withdrawal_queue()
                self.load_dashboard()
                dlg.accept()
            else:
                QMessageBox.warning(self, "错误", result.get("error", "操作失败"))

        btn.clicked.connect(do)
        layout.addRow(btn)
        dlg.exec_()

    def _do_reject_withdrawal(self):
        row = self.withdraw_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一条待审批记录")
            return
        req_id = int(self.withdraw_table.item(row, 0).text())
        status = self.withdraw_table.item(row, 4).text()
        if status != "pending":
            QMessageBox.information(self, "提示", "该记录已处理")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("拒绝原因")
        dlg.setMinimumWidth(350)
        apply_dark_theme(dlg)
        layout = QFormLayout(dlg)
        note = QLineEdit()
        note.setPlaceholderText("输入拒绝原因（可选）")
        layout.addRow("拒绝原因:", note)
        btn = QPushButton("确认拒绝")
        btn.setStyleSheet(self._btn_style(DANGER))

        def do():
            result = reject_withdrawal(req_id, operator="admin", note=note.text())
            if result["ok"]:
                QMessageBox.information(self, "成功",
                    f"已拒绝申请，¥{result['amount']:.2f} 已解冻")
                self.load_wallets()
                self.load_withdrawal_queue()
                self.load_dashboard()
                dlg.accept()
            else:
                QMessageBox.warning(self, "错误", result.get("error", "拒绝失败"))

        btn.clicked.connect(do)
        layout.addRow(btn)
        dlg.exec_()

    def _do_export_csv(self):
        filepath = export_transactions_to_csv()
        reply = QMessageBox.information(
            self, "导出成功",
            f"报表已导出至:\n{filepath}\n\n是否打开？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            subprocess.run(['open', filepath])

    def _do_delete_wallet(self):
        sel = self._get_selected_wallet()
        if not sel:
            return
        wallet_id, user_id = sel

        w = get_wallet(user_id)
        if not w:
            return
        balance = w.get("balance", 0)
        frozen = w.get("frozen_amount", 0)

        pending = get_pending_withdrawals()
        has_pending = any(p["user_id"] == user_id for p in pending)
        if has_pending:
            QMessageBox.information(
                self, "无法删除",
                f"用户 {user_id} 有待审批的提现申请，请先在「提现审批」中处理后再删除。"
            )
            return

        if frozen != 0:
            reply = QMessageBox.question(
                self, "⚠️ 有冻结金额",
                f"用户 {user_id} 的钱包有冻结金额 ¥{frozen:.2f}。\n"
                f"强制删除将清零冻结金额，确定要继续吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            result = delete_wallet(user_id, force=True)
        elif balance != 0:
            reply = QMessageBox.question(
                self, "⚠️ 有余额余额",
                f"用户 {user_id} 的钱包余额为 ¥{balance:.2f}。\n"
                f"强制删除将清零余额，确定要继续吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            result = delete_wallet(user_id, force=True)
        else:
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除用户 {user_id} 的钱包吗？\n"
                f"（此操作不可恢复）",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            result = delete_wallet(user_id, force=False)

        if result["ok"]:
            QMessageBox.information(self, "成功", f"钱包 {user_id} 已删除")
            self.load_wallets()
            self.load_dashboard()
        else:
            QMessageBox.warning(self, "删除失败", result.get("error", "未知错误"))

    def _do_cancel_withdrawal(self):
        row = self.withdraw_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先在提现审批队列中选择一条待审批记录")
            return
        req_id = int(self.withdraw_table.item(row, 0).text())
        status = self.withdraw_table.item(row, 4).text()
        if status != "pending":
            QMessageBox.information(self, "提示", "只能取消【待审批】状态的申请")
            return

        reply = QMessageBox.question(
            self, "确认取消",
            f"确定要取消提现申请 #{req_id} 吗？\n金额将自动解冻。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            result = cancel_withdrawal_request(req_id)
            if result["ok"]:
                QMessageBox.information(
                    self, "已取消",
                    f"申请 #{req_id} 已取消，¥{result['amount']:.2f} 已解冻"
                )
                self.load_wallets()
                self.load_withdrawal_queue()
                self.load_dashboard()
            else:
                QMessageBox.warning(self, "失败", result.get("error", "取消失败"))

    def _do_delete_withdrawal_request(self):
        row = self.withdraw_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先在提现审批队列中选择一条记录")
            return
        req_id = int(self.withdraw_table.item(row, 0).text())
        status = self.withdraw_table.item(row, 4).text()
        if status == "pending":
            QMessageBox.information(
                self, "提示",
                "pending 状态的申请不能直接删除，请先「取消申请」"
            )
            return

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除提现申请记录 #{req_id} 吗？\n状态：{status}\n此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            result = delete_withdrawal_request(req_id)
            if result["ok"]:
                QMessageBox.information(self, "已删除", f"记录 #{req_id} 已删除")
                self.load_withdrawal_queue()
            else:
                QMessageBox.warning(self, "删除失败", result.get("error", "删除失败"))

    def _do_clear_withdrawal_queue(self):
        reply = QMessageBox.question(
            self, "选择清理范围",
            "请选择要清理的范围：\n\n"
            "【已处理】- 删除所有已通过/已拒绝的记录（保留 pending 和 cancelled）\n"
            "【含取消】- 删除所有已处理+已取消的记录（保留 pending）\n"
            "【清空全部】- 删除所有记录（含 pending，需先解冻金额）\n\n"
            "点击 Yes = 已处理 | No = 含取消 | Cancel = 取消",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        if reply == QMessageBox.Yes:
            result = clear_withdrawal_queue(status="processed")
            scope = "已处理（通过/拒绝）"
        elif reply == QMessageBox.No:
            result = clear_withdrawal_queue(status="cancelled")
            r2 = clear_withdrawal_queue(status="processed")
            result = {"ok": True, "deleted": r2.get("deleted", 0) + result.get("deleted", 0)}
            scope = "已处理+已取消"
        else:
            return

        if result["ok"]:
            QMessageBox.information(
                self, "清理完成",
                f"已清理 {scope} 记录，共 {result['deleted']} 条"
            )
            self.load_withdrawal_queue()
        else:
            QMessageBox.warning(self, "清理失败", result.get("error", "清理失败"))

    def _do_delete_transaction(self):
        row = self.txn_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先在交易记录中选择一条记录")
            return
        txn_id = int(self.txn_table.item(row, 0).text())
        amount = self.txn_table.item(row, 3).text()
        desc = self.txn_table.item(row, 5).text() or ""

        reply = QMessageBox.question(
            self, "⚠️ 确认删除交易记录",
            f"确定要删除交易记录 #{txn_id} 吗？\n"
            f"金额: {amount} | 描述: {desc}\n\n"
            f"⚠️ 此操作会修正钱包余额，请确认！",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            result = delete_transaction(txn_id, operator="admin")
            if result["ok"]:
                QMessageBox.information(
                    self, "已删除",
                    f"交易 #{txn_id} 已删除，余额已修正"
                )
                self.load_transactions()
                self.load_wallets()
                self.load_dashboard()
            else:
                QMessageBox.warning(self, "删除失败", result.get("error", "删除失败"))

    def _go_back(self):
        self.close()
        parent = self.parent()
        if parent and hasattr(parent, 'show') and callable(parent.show):
            parent.show()


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = WalletWindow()
    w.show()
    sys.exit(app.exec_())

```
