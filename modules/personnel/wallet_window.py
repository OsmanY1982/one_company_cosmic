"""
钱包管理 · CREW
独立的 QDialog 子窗口，暖橙渐变主题
对接 personnel_window DAO 层（wallet.db）
"""
import traceback
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QComboBox,
    QDoubleSpinBox, QFrame, QLineEdit, QTextEdit, QFormLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QLinearGradient, QPen,
    QBrush, QFont, QPainterPath
)

from modules.personnel.personnel_window import (
    staff_get_all,
    wallet_get_all, wallet_create, wallet_recharge, wallet_get_by_user,
    wallet_withdraw_request, wallet_get_trans, wallet_stats,
    wallet_approve_withdraw, wallet_reject_withdraw,
    wallet_get_withdraw,
)

# ═══════ 暖橙 QSS ═══════
BTN_ORANGE = """
    QPushButton {
        background: rgba(255,140,40,40);
        color: #ffccaa;
        border: 1px solid rgba(255,140,40,40);
        border-radius: 16px; padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(255,160,60,70); }
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
BTN_GREEN = """
    QPushButton {
        background: rgba(40,160,100,40);
        color: #88ffbb;
        border: 1px solid rgba(60,180,120,60);
        border-radius: 16px; padding: 6px 18px; font-size: 11px;
    }
    QPushButton:hover { background: rgba(50,200,120,70); }
"""
TABLE_STYLE = """
    QTableWidget {
        background: rgba(15,8,5,220);
        color: #ddbbaa;
        border: 1px solid rgba(180,80,50,30);
        border-radius: 8px; gridline-color: rgba(80,40,20,25);
        font-size: 12px; selection-background-color: rgba(255,100,60,60);
    }
    QTableWidget::item { padding: 5px 10px; }
    QHeaderView::section {
        background: rgba(25,12,8,230);
        color: #bb9988; padding: 8px 10px; border: none;
        border-bottom: 1px solid rgba(255,100,60,40);
        font-weight: 700; font-size: 11px; letter-spacing: 1px;
    }
"""
DIALOG_QSS = """
    QDialog {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #1a0c04, stop:1 #2e1008);
        border: 1px solid rgba(255,140,40,40); border-radius: 12px;
    }
    QLabel { color: #ccaa99; font-size: 12px; background: transparent; }
    QComboBox {
        background: rgba(15,8,5,230); color: #ddbbaa;
        border: 1px solid rgba(255,140,40,35); border-radius: 6px;
        padding: 6px 10px; font-size: 12px;
    }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background: rgba(20,10,6,240); color: #ddbbaa;
        selection-background-color: rgba(255,140,40,60);
        border: 1px solid rgba(255,140,40,30);
    }
    QDoubleSpinBox {
        background: rgba(15,8,5,230); color: #ffccaa;
        border: 1px solid rgba(255,140,40,35); border-radius: 6px;
        padding: 6px 10px; font-size: 13px; font-weight: 600;
    }
"""


# ═══════ 余额卡片自绘 ═══════
class BalanceCard(QFrame):
    def __init__(self, title, color_start, color_end, parent=None):
        super().__init__(parent)
        self._title = title
        self._value = 0.0
        self._color_start = QColor(*color_start)
        self._color_end = QColor(*color_end)
        self.setFixedSize(170, 80)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def set_value(self, v):
        self._value = v
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
        painter.setPen(QPen(QColor(255, 140, 40, 60), 1))
        painter.drawPath(path)

        painter.setPen(QColor(255, 200, 160, 180))
        painter.setFont(QFont("sans-serif", 10))
        painter.drawText(14, 24, self._title)

        painter.setPen(QColor(255, 230, 200))
        painter.setFont(QFont("sans-serif", 20, QFont.Bold))
        painter.drawText(14, 54, f"¥{self._value:,.2f}")

        painter.end()


# ═══════════════ 提现审核弹窗 ═══════════════
class WithdrawAuditDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("提现审核")
        self.setMinimumSize(600, 450)
        self.setStyleSheet(DIALOG_QSS)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 16, 20, 16)

        title = QLabel("提现待审核")
        title.setStyleSheet(
            "color: #ffccaa; font-size: 16px; font-weight: 800; "
            "letter-spacing: 4px; background: transparent;"
        )
        layout.addWidget(title, alignment=Qt.AlignCenter)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(["ID", "用户", "金额", "方式", "时间", "备注"])
        self._table.setStyleSheet(TABLE_STYLE)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self._table)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        approve_btn = QPushButton("通过")
        approve_btn.setStyleSheet(BTN_GREEN)
        approve_btn.clicked.connect(self._on_approve)
        reject_btn = QPushButton("驳回")
        reject_btn.setStyleSheet(BTN_DANGER)
        reject_btn.clicked.connect(self._on_reject)
        btn_row.addWidget(approve_btn)
        btn_row.addWidget(reject_btn)
        layout.addLayout(btn_row)

    def _load(self):
        rows = wallet_get_withdraw("pending")
        self._table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self._table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self._table.setItem(i, 1, QTableWidgetItem(r["user_id"] or ""))
            self._table.setItem(i, 2, QTableWidgetItem(f"¥{float(r['amount']):,.2f}"))
            self._table.setItem(i, 3, QTableWidgetItem(r["method"] or ""))
            self._table.setItem(i, 4, QTableWidgetItem(r["created_at"] or ""))
            self._table.setItem(i, 5, QTableWidgetItem(r["note"] or ""))

    def _get_selected(self):
        row = self._table.currentRow()
        if row < 0:
            return None
        return int(self._table.item(row, 0).text())

    def _on_approve(self):
        wid = self._get_selected()
        if wid is None:
            QMessageBox.warning(self, "提示", "请先选择一条提现记录")
            return
        r = wallet_approve_withdraw(wid, operator="admin")
        if r["ok"]:
            QMessageBox.information(self, "成功", f"已通过提现 ¥{r.get('amount',0):,.2f}")
        else:
            QMessageBox.warning(self, "失败", r["error"])
        self._load()

    def _on_reject(self):
        wid = self._get_selected()
        if wid is None:
            QMessageBox.warning(self, "提示", "请先选择一条提现记录")
            return
        r = wallet_reject_withdraw(wid, operator="admin", note="驳回")
        if r["ok"]:
            QMessageBox.information(self, "成功", "已驳回提现申请")
        else:
            QMessageBox.warning(self, "失败", r["error"])
        self._load()


# ═══════════════ 钱包管理窗口 ═══════════════
class WalletWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("钱包管理 · CREW")
        self.setMinimumSize(650, 600)
        self.setStyleSheet(DIALOG_QSS)
        self._staff_map = {}  # id → name
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(10)
        main.setContentsMargins(20, 16, 20, 16)

        # ── 标题 ──
        title = QLabel("钱包管理")
        title.setStyleSheet(
            "color: #ffccaa; font-size: 18px; font-weight: 800; "
            "letter-spacing: 6px; background: transparent;"
        )
        main.addWidget(title, alignment=Qt.AlignCenter)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(255,140,40,40),
                stop:0.5 rgba(255,140,40,80),
                stop:0.7 rgba(255,140,40,40), stop:1 transparent);
            border: none;
        """)
        main.addWidget(line)

        # ── 3 个余额卡片 ──
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)
        self._card_balance = BalanceCard("总余额", (255, 100, 40), (200, 60, 20))
        self._card_income = BalanceCard("累计收入", (255, 140, 60), (200, 80, 30))
        self._card_withdraw = BalanceCard("累计提现", (255, 120, 50), (180, 50, 15))
        cards_layout.addWidget(self._card_balance)
        cards_layout.addWidget(self._card_income)
        cards_layout.addWidget(self._card_withdraw)
        main.addLayout(cards_layout)

        line2 = QFrame()
        line2.setFixedHeight(1)
        line2.setStyleSheet("background: rgba(255,140,40,20); border: none;")
        main.addWidget(line2)

        # ── 员工选择 + 钱包操作 ──
        staff_layout = QHBoxLayout()
        staff_layout.setSpacing(12)

        staff_label = QLabel("员工/用户")
        staff_label.setStyleSheet("color: #ccaa99; font-size: 12px; background: transparent;")
        staff_layout.addWidget(staff_label)

        self._user_combo = QComboBox()
        self._user_combo.setMinimumWidth(160)
        self._user_combo.setEditable(True)
        self._user_combo.setInsertPolicy(QComboBox.NoInsert)
        self._user_combo.currentTextChanged.connect(self._on_user_changed)
        staff_layout.addWidget(self._user_combo)

        staff_layout.addStretch()

        self._balance_label = QLabel("余额: ¥0.00")
        self._balance_label.setStyleSheet(
            "color: #ffcc88; font-size: 16px; font-weight: 700; background: transparent;"
        )
        staff_layout.addWidget(self._balance_label)
        main.addLayout(staff_layout)

        # ── 操作区 ──
        op_layout = QHBoxLayout()
        op_layout.setSpacing(10)

        recharge_label = QLabel("充值")
        recharge_label.setStyleSheet("color: #ccaa99; font-size: 11px; background: transparent;")
        op_layout.addWidget(recharge_label)

        self._recharge_spin = QDoubleSpinBox()
        self._recharge_spin.setRange(0, 999999)
        self._recharge_spin.setPrefix("¥ ")
        self._recharge_spin.setValue(100)
        self._recharge_spin.setFixedWidth(120)
        op_layout.addWidget(self._recharge_spin)

        self._recharge_btn = QPushButton("充值")
        self._recharge_btn.setStyleSheet(BTN_ORANGE)
        self._recharge_btn.clicked.connect(self._do_recharge)
        op_layout.addWidget(self._recharge_btn)

        op_layout.addSpacing(20)

        withdraw_label = QLabel("提现申请")
        withdraw_label.setStyleSheet("color: #ccaa99; font-size: 11px; background: transparent;")
        op_layout.addWidget(withdraw_label)

        self._withdraw_spin = QDoubleSpinBox()
        self._withdraw_spin.setRange(0, 999999)
        self._withdraw_spin.setPrefix("¥ ")
        self._withdraw_spin.setValue(50)
        self._withdraw_spin.setFixedWidth(120)
        op_layout.addWidget(self._withdraw_spin)

        self._withdraw_btn = QPushButton("提现")
        self._withdraw_btn.setStyleSheet(BTN_DANGER)
        self._withdraw_btn.clicked.connect(self._do_withdraw)
        op_layout.addWidget(self._withdraw_btn)

        op_layout.addStretch()

        self._audit_btn = QPushButton("审核")
        self._audit_btn.setStyleSheet(BTN_GREEN)
        self._audit_btn.clicked.connect(self._open_audit)
        op_layout.addWidget(self._audit_btn)
        main.addLayout(op_layout)

        # ── 交易记录表格 ──
        table_label = QLabel("交易记录")
        table_label.setStyleSheet(
            "color: #bb9988; font-size: 13px; font-weight: 700; "
            "letter-spacing: 2px; background: transparent;"
        )
        main.addWidget(table_label)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["用户", "类型", "金额", "备注", "时间"])
        self._table.setStyleSheet(TABLE_STYLE)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        main.addWidget(self._table)

    def _load_data(self):
        # 加载员工列表作为钱包用户候选
        self._staff_map = {}
        self._user_combo.blockSignals(True)
        self._user_combo.clear()
        try:
            staff_rows = staff_get_all()
            for row in staff_rows:
                sid = str(row["id"])
                name = row["name"] or f"员工#{sid}"
                self._staff_map[sid] = name
                self._user_combo.addItem(f"{name} (ID:{sid})", sid)
        except Exception:
            traceback.print_exc()
        self._user_combo.blockSignals(False)

        self._refresh_stats()
        self._load_transactions()

    def _refresh_stats(self):
        try:
            s = wallet_stats()
            self._card_balance.set_value(s.get("balance", 0))
            self._card_income.set_value(s.get("income", 0))
            self._card_withdraw.set_value(s.get("expense", 0))
            pending = s.get("pending", 0)
            self._audit_btn.setText(f"审核({pending})" if pending else "审核")
        except Exception:
            traceback.print_exc()

    def _load_transactions(self):
        try:
            rows = wallet_get_trans()
            self._table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                self._table.setItem(i, 0, QTableWidgetItem(r["user_id"] or ""))
                ttype = r["trans_type"] or ""
                type_item = QTableWidgetItem(ttype)
                if "收入" in ttype or "充值" in ttype or "佣金" in ttype:
                    type_item.setForeground(QColor(136, 255, 187))
                elif "支出" in ttype or "提现" in ttype or "转账" in ttype:
                    type_item.setForeground(QColor(255, 170, 170))
                self._table.setItem(i, 1, type_item)
                amt = float(r["amount"]) if r.get("amount") else 0
                self._table.setItem(i, 2, QTableWidgetItem(f"¥{amt:,.2f}"))
                self._table.setItem(i, 3, QTableWidgetItem(r["note"] or ""))
                self._table.setItem(i, 4, QTableWidgetItem(r["created_at"] or ""))
        except Exception:
            traceback.print_exc()

    def _get_current_user(self):
        sid = self._user_combo.currentData()
        if sid:
            return sid, self._staff_map.get(sid, "")
        # 如果编辑了自定义文本
        text = self._user_combo.currentText().strip()
        if text:
            return text, text
        return None, ""

    def _on_user_changed(self):
        uid, _ = self._get_current_user()
        if not uid:
            self._balance_label.setText("余额: ¥0.00")
            return
        try:
            w = wallet_get_by_user(uid)
            if w:
                self._balance_label.setText(f"余额: ¥{float(w['balance']):,.2f}")
            else:
                self._balance_label.setText("余额: ¥0.00 (未开通)")
        except Exception:
            self._balance_label.setText("余额: —")

    def _ensure_wallet(self, uid, name):
        w = wallet_get_by_user(uid)
        if not w:
            wallet_create(uid, name)
            return wallet_get_by_user(uid)
        return w

    def _do_recharge(self):
        uid, name = self._get_current_user()
        if not uid:
            QMessageBox.warning(self, "提示", "请选择员工/用户或输入用户ID")
            return
        amount = self._recharge_spin.value()
        if amount <= 0:
            QMessageBox.warning(self, "提示", "请输入有效充值金额")
            return
        self._ensure_wallet(uid, name)
        r = wallet_recharge(uid, amount, f"管理员充值 ¥{amount}")
        if r["ok"]:
            self._balance_label.setText(f"余额: ¥{r['balance']:,.2f}")
        else:
            QMessageBox.warning(self, "充值失败", r["error"])
        self._refresh_stats()
        self._load_transactions()
        self._recharge_spin.setValue(100)

    def _do_withdraw(self):
        uid, name = self._get_current_user()
        if not uid:
            QMessageBox.warning(self, "提示", "请选择员工/用户或输入用户ID")
            return
        amount = self._withdraw_spin.value()
        if amount <= 0:
            QMessageBox.warning(self, "提示", "请输入有效提现金额")
            return
        self._ensure_wallet(uid, name)
        r = wallet_withdraw_request(uid, amount, method="手动", note=f"提现申请 ¥{amount}")
        if r["ok"]:
            QMessageBox.information(self, "成功", r["message"])
            self._on_user_changed()
        else:
            QMessageBox.warning(self, "提现失败", r["error"])
        self._refresh_stats()
        self._load_transactions()

    def _open_audit(self):
        dlg = WithdrawAuditDialog(self)
        dlg.exec_()
        self._refresh_stats()
        self._load_transactions()
