# `modules/auth/upgrade_window.py`

> 路径：`modules/auth/upgrade_window.py` | 行数：353


---


```python
"""
升级会员 · COSMIC
QDialog：套餐展示 + 二维码占位 + 激活码自助激活
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QFrame, QMessageBox, QButtonGroup, QRadioButton
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath

from modules.auth.auth_service import AuthService

# ═══════════ 主题配色 ═══════════
GOLD = QColor(255, 180, 50)
PURPLE = QColor(140, 80, 255)
DARK_BG = "#080e1a"
DARK_BG2 = "#101a2e"
TEXT_DIM = "#667788"
TEXT_LIGHT = "#aabccc"

QSS_DIALOG = """
    QDialog {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #080e1a, stop:1 #101a2e);
        border: 2px solid rgba(80,120,200,50);
        border-radius: 14px;
    }
    QLabel { background: transparent; }
"""

QSS_INPUT = """
    QLineEdit {
        background: rgba(10,18,32,235);
        color: #aaccee;
        border: 1px solid rgba(70,130,200,40);
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 13px;
    }
    QLineEdit:focus { border: 1px solid rgba(100,180,255,160); }
    QLineEdit::placeholder { color: #334466; }
"""

QSS_BTN_PRIMARY = """
    QPushButton {
        background: rgba(30,80,180,200);
        color: #cceeff;
        border: 1px solid rgba(70,140,240,60);
        border-radius: 18px;
        padding: 8px 28px;
        font-size: 13px; font-weight: 700;
    }
    QPushButton:hover { background: rgba(40,100,210,240); }
    QPushButton:disabled { background: rgba(20,30,50,150); color: #445566; border: 1px solid rgba(40,50,70,40); }
"""


class QRPlaceholder(QFrame):
    """模拟二维码占位图（QPainter 绘制）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 140)
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        margin = 6

        # 白色背景
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 245)))
        painter.drawRoundedRect(QRectF(margin, margin, w - 2 * margin, h - 2 * margin), 8, 8)

        # 绘制模拟二维码方块
        cell = 8
        offset = 16
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(20, 20, 20)))

        # 定位图案（三个角）
        for cx, cy in [(offset, offset), (w - offset - 3 * cell, offset), (offset, w - offset - 3 * cell)]:
            for dx in range(3):
                for dy in range(3):
                    if dx == 1 and dy == 1:
                        continue
                    painter.drawRect(int(cx + dx * cell), int(cy + dy * cell), cell, cell)

        # 随机数据方块
        import random
        rng = random.Random(42)
        for x in range(offset, w - offset, cell):
            for y in range(offset, h - offset, cell):
                if rng.random() > 0.55:
                    painter.drawRect(x, y, cell - 1, cell - 1)

        painter.end()


class PlanCard(QFrame):
    """套餐卡片"""

    def __init__(self, title, price, desc, border_color, parent=None):
        super().__init__(parent)
        self._border_color = border_color
        self._title = title
        self._price = price
        self._desc = desc
        self.setFixedSize(230, 130)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        bc = self._border_color

        # 卡片背景
        path = QPainterPath()
        path.addRoundedRect(QRectF(2, 2, w - 4, h - 4), 12, 12)
        painter.setPen(QPen(QColor(bc.red(), bc.green(), bc.blue(), 80), 2))
        painter.setBrush(QBrush(QColor(bc.red(), bc.green(), bc.blue(), 12)))
        painter.drawPath(path)

        # 标题
        painter.setPen(QPen(QColor(bc.red(), bc.green(), bc.blue(), 230)))
        painter.setFont(QFont("PingFang SC", 14, QFont.Bold))
        painter.drawText(QRectF(16, 14, w - 32, 28), Qt.AlignLeft, self._title)

        # 价格
        painter.setPen(QPen(QColor(200, 210, 230)))
        painter.setFont(QFont("PingFang SC", 22, QFont.Bold))
        painter.drawText(QRectF(16, 42, w - 32, 36), Qt.AlignLeft, self._price)

        # 描述
        painter.setPen(QPen(QColor(100, 120, 150)))
        painter.setFont(QFont("PingFang SC", 10))
        painter.drawText(QRectF(16, 80, w - 32, 36), Qt.AlignLeft, self._desc)

        painter.end()


class UpgradeWindow(QDialog):
    """升级会员窗口"""

    def __init__(self, username, role, membership, expire_at, parent=None):
        super().__init__(parent)
        self._username = username
        self._role = role
        self._membership = membership
        self._expire_at = expire_at
        self._auth = AuthService()

        self.setWindowTitle("升级会员 · COSMIC")
        self.setFixedSize(550, 500)
        self.setStyleSheet(QSS_DIALOG)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 18, 24, 18)

        # ── 标题 ──
        title = QLabel("升级会员 · COSMIC")
        title.setStyleSheet("color: #cceeff; font-size: 16px; font-weight: 800; letter-spacing: 3px;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        # ── 当前会员状态卡片 ──
        info = self._auth.get_membership_info(self._username)
        days_left = info.get("days_left", 0)
        label = info.get("label", "体验会员")

        status_frame = QFrame()
        status_frame.setStyleSheet("""
            background: rgba(12,20,36,230);
            border: 1px solid rgba(70,120,180,35);
            border-radius: 10px;
            padding: 10px;
        """)
        sl = QHBoxLayout(status_frame)
        sl.setContentsMargins(14, 8, 14, 8)

        # 徽章
        badge = QLabel("●")
        level_colors = {"trial": "#00ccff", "vip": "#ffb432", "permanent": "#8c50ff"}
        badge.setStyleSheet(
            f"color: {level_colors.get(self._membership, '#00ccff')}; font-size: 22px; font-weight: bold;"
        )
        sl.addWidget(badge)

        status_text = f"当前：{label}"
        if days_left == -1:
            status_text += " | 永久有效"
        else:
            status_text += f" | 剩余 {days_left} 天"
            if self._expire_at:
                status_text += f" | 到期：{self._expire_at[:10]}"

        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {TEXT_LIGHT}; font-size: 12px;")
        sl.addWidget(status_label, 1)
        layout.addWidget(status_frame)

        # ── 套餐区 ──
        plan_label = QLabel("选择套餐")
        plan_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; font-weight: 600; letter-spacing: 1px;")
        layout.addWidget(plan_label)

        plans_layout = QHBoxLayout()
        plans_layout.setSpacing(14)

        self._vip_card = PlanCard("VIP 会员", "49 元/年", "解锁全部模块", GOLD)
        self._perm_card = PlanCard("永久会员", "99 元", "终身使用+优先支持", PURPLE)

        # RadioButton 隐藏，仅用于逻辑
        self._plan_group = QButtonGroup(self)
        self._radio_vip = QRadioButton()
        self._radio_perm = QRadioButton()
        self._radio_vip.setVisible(False)
        self._radio_perm.setVisible(False)
        self._plan_group.addButton(self._radio_vip)
        self._plan_group.addButton(self._radio_perm)

        self._vip_card.mousePressEvent = lambda e: self._select_plan("vip")
        self._perm_card.mousePressEvent = lambda e: self._select_plan("permanent")

        plans_layout.addWidget(self._vip_card)
        plans_layout.addWidget(self._perm_card)
        plans_layout.addStretch()
        layout.addLayout(plans_layout)

        # ── 选中后显示区 ──
        self._activate_area = QFrame()
        self._activate_area.setVisible(False)
        self._activate_area.setStyleSheet(f"""
            background: rgba(12,20,36,200);
            border: 1px solid rgba(70,120,180,30);
            border-radius: 10px;
            padding: 10px;
        """)
        al = QVBoxLayout(self._activate_area)
        al.setSpacing(8)
        al.setContentsMargins(14, 10, 14, 10)

        # 提示
        hint = QLabel("联系管理员获取激活码后，在下方输入并激活")
        hint.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        hint.setAlignment(Qt.AlignCenter)
        al.addWidget(hint)

        # 二维码 + 输入区
        mid_row = QHBoxLayout()
        mid_row.setSpacing(16)

        qr_container = QVBoxLayout()
        self._qr = QRPlaceholder()
        qr_container.addWidget(self._qr, alignment=Qt.AlignCenter)

        qr_label = QLabel("扫码联系管理员")
        qr_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px;")
        qr_label.setAlignment(Qt.AlignCenter)
        qr_container.addWidget(qr_label)
        mid_row.addLayout(qr_container)

        # 输入区
        input_col = QVBoxLayout()
        input_col.setSpacing(8)

        code_label = QLabel("激活码")
        code_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; font-weight: 600;")
        input_col.addWidget(code_label)

        self._code_input = QLineEdit()
        self._code_input.setPlaceholderText("请输入16位激活码")
        self._code_input.setMaxLength(20)
        self._code_input.setStyleSheet(QSS_INPUT)
        input_col.addWidget(self._code_input)

        self._activate_btn = QPushButton("立即激活")
        self._activate_btn.setStyleSheet(QSS_BTN_PRIMARY)
        self._activate_btn.clicked.connect(self._do_activate)
        self._activate_btn.setEnabled(False)
        input_col.addWidget(self._activate_btn)

        self._activate_status = QLabel("")
        self._activate_status.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        self._activate_status.setAlignment(Qt.AlignCenter)
        self._activate_status.setWordWrap(True)
        input_col.addWidget(self._activate_status)

        input_col.addStretch()
        mid_row.addLayout(input_col, 1)
        al.addLayout(mid_row)

        layout.addWidget(self._activate_area)
        layout.addStretch()

    def _select_plan(self, plan):
        if plan == "vip":
            self._radio_vip.setChecked(True)
            self._vip_card.setStyleSheet(
                f"border: 2px solid rgba({GOLD.red()},{GOLD.green()},{GOLD.blue()},120); border-radius: 14px;"
            )
            self._perm_card.setStyleSheet("border: 2px solid transparent; border-radius: 14px;")
            self._activate_area.setStyleSheet(f"""
                background: rgba(12,20,36,200);
                border: 2px solid rgba({GOLD.red()},{GOLD.green()},{GOLD.blue()},60);
                border-radius: 10px;
                padding: 10px;
            """)
        else:
            self._radio_perm.setChecked(True)
            self._perm_card.setStyleSheet(
                f"border: 2px solid rgba({PURPLE.red()},{PURPLE.green()},{PURPLE.blue()},120); border-radius: 14px;"
            )
            self._vip_card.setStyleSheet("border: 2px solid transparent; border-radius: 14px;")
            self._activate_area.setStyleSheet(f"""
                background: rgba(12,20,36,200);
                border: 2px solid rgba({PURPLE.red()},{PURPLE.green()},{PURPLE.blue()},60);
                border-radius: 10px;
                padding: 10px;
            """)

        self._activate_area.setVisible(True)
        self._code_input.textChanged.connect(self._on_code_changed)

    def _on_code_changed(self):
        code = self._code_input.text().strip()
        self._activate_btn.setEnabled(len(code) >= 8)
        self._activate_status.setText("")

    def _do_activate(self):
        code = self._code_input.text().strip()
        if not code:
            return

        ok, msg = self._auth.activate_member(self._username, code)
        if ok:
            self._activate_status.setStyleSheet("color: #44cc88; font-size: 12px; font-weight: 600;")
            self._activate_status.setText("激活成功！请重新登录以生效。")
            self._activate_btn.setEnabled(False)
            self._code_input.setEnabled(False)
            QMessageBox.information(self, "激活成功", f"会员升级成功！\n{msg}\n\n请重新登录以生效。")
            self.accept()
        else:
            self._activate_status.setStyleSheet("color: #ff6644; font-size: 12px; font-weight: 600;")
            self._activate_status.setText(msg)

```
