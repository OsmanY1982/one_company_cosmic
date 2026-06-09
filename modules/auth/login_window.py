"""
蓝星登录窗口 — 地球注册/登录
底部蓝色地球缓慢旋转 + 上方全息登录/注册表单
"""
import math, json, os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget,
    QLineEdit, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QLinearGradient, QPainterPath, QFont, QConicalGradient, QPolygonF
)

from core.cosmic import CosmicBackground, ACCENT_CYAN, ACCENT_GOLD, HOLO_BORDER

# ── 本地用户数据文件 ──
USER_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")


def _load_users() -> dict:
    if os.path.exists(USER_DB):
        with open(USER_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"admin": "admin"}


def _save_users(users: dict):
    with open(USER_DB, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


class EarthGlobe:
    """蓝星绘制器 — 带大气光晕和大陆轮廓伪 3D"""

    EARTH_BLUE = QColor(16, 60, 140)
    OCEAN_DARK = QColor(8, 30, 80)
    CLOUD = QColor(200, 230, 255, 30)

    def __init__(self, cx: int, cy: int, radius: int):
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.angle = 0

    def draw(self, painter: QPainter):
        """绘制蓝星 + 大气光晕 + 大陆轮廓"""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        cx, cy, r = self.cx, self.cy, self.radius

        # ── 大气光晕 ──
        for layer in range(6, 0, -1):
            lr = r + layer * 16
            alpha = int(14 * (7 - layer))
            g = QRadialGradient(QPointF(cx, cy), lr)
            g.setColorAt(0.72, QColor(0, 0, 0, 0))
            g.setColorAt(0.8, QColor(80, 180, 255, alpha))
            g.setColorAt(0.92, QColor(40, 100, 200, alpha // 2))
            g.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(g))
            painter.drawEllipse(QPointF(cx, cy), lr, lr)

        # ── 球体基础（海洋深浅渐变） ──
        body = QRadialGradient(QPointF(cx - r * 0.25, cy - r * 0.25), r * 1.6)
        body.setColorAt(0.3, QColor(60, 140, 230))
        body.setColorAt(0.55, QColor(25, 80, 180))
        body.setColorAt(0.8, QColor(10, 40, 120))
        body.setColorAt(1, QColor(4, 16, 60))
        painter.setPen(QPen(QColor(30, 70, 150, 80), 1))
        painter.setBrush(QBrush(body))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # ── 大陆轮廓（随机斑点模拟） ──
        painter.setPen(Qt.NoPen)
        continents = self._continent_spots(cx, cy, r)
        for (sx, sy, sr, shade) in continents:
            color = QColor(shade, 135 + shade // 3, 60, 110)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(sx, sy), sr, sr * 0.7)

        # ── 云层（白色模糊条带） ──
        clouds = self._cloud_bands(cx, cy, r)
        painter.setPen(Qt.NoPen)
        for (bx, by, bw, bh, alpha) in clouds:
            painter.setBrush(QBrush(QColor(200, 230, 255, alpha)))
            painter.save()
            painter.translate(bx, by)
            painter.rotate(25)
            painter.drawRoundedRect(QRectF(-bw / 2, -bh / 2, bw, bh), bh / 2, bh / 2)
            painter.restore()

        # ── 高光反射（左上） ──
        highlight = QRadialGradient(QPointF(cx - r * 0.35, cy - r * 0.35), r * 0.45)
        highlight.setColorAt(0, QColor(255, 255, 255, 50))
        highlight.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(highlight))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        painter.restore()

    def _continent_spots(self, cx, cy, r):
        """固定种子的大陆斑点"""
        import random
        random.seed(42)
        spots = []
        rr = r * 0.78
        for _ in range(200):
            angle = random.random() * 2 * math.pi
            dist = random.random() * rr
            sx = cx + math.cos(angle) * dist
            sy = cy + math.sin(angle) * dist * 0.95
            sr = r * 0.03 + random.random() * r * 0.10
            shade = random.randint(20, 80)
            spots.append((sx, sy, sr, shade))
        random.seed()
        return spots

    def _cloud_bands(self, cx, cy, r):
        import random
        random.seed(99)
        bands = []
        for _ in range(18):
            angle = random.random() * math.pi * 2
            dist = r * random.uniform(0.3, 0.85)
            bx = cx + math.cos(angle) * dist
            by = cy + math.sin(angle) * dist * 0.9
            bw = r * random.uniform(0.3, 0.9)
            bh = r * random.uniform(0.04, 0.12)
            alpha = random.randint(8, 25)
            bands.append((bx, by, bw, bh, alpha))
        random.seed()
        return bands


class LoginWindow(QMainWindow):
    """蓝星登录 — 地球注册/登录"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("一人公司 — 蓝星")
        self.setMinimumSize(900, 680)

        # 星空背景
        self._cosmic = CosmicBackground()
        self.setCentralWidget(self._cosmic)

        # HUD
        self._hud = QWidget(self._cosmic)
        self._hud.setAttribute(Qt.WA_TranslucentBackground)
        self._hud.setGeometry(0, 0, 900, 680)

        # 地球
        self._earth = None  # 在 resizeEvent 中定位
        self._orbit_sats = []  # 环绕小卫星相位
        for i in range(5):
            self._orbit_sats.append(i * 2 * math.pi / 5)

        self._t = 0
        self._mode = "login"  # login / register

        self._build_ui()

        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(35)

    # ════════════════ UI 构建 ════════════════

    def _build_ui(self):
        self._hud.paintEvent = self._paint_hud

        # 堆叠：登录 / 注册
        self._stack = QStackedWidget(self._hud)
        self._stack.setStyleSheet("background: transparent;")

        self._stack.addWidget(self._build_login_panel())
        self._stack.addWidget(self._build_register_panel())
        self._stack.setCurrentIndex(0)

        self._stack.setFixedWidth(340)

    def _input_style(self) -> str:
        return """
            QLineEdit {
                background: rgba(5, 15, 40, 200);
                color: #99ccff;
                border: 1px solid rgba(60, 140, 240, 50);
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 14px;
                min-width: 260px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(0, 200, 255, 180);
                background: rgba(8, 20, 50, 230);
            }
            QLineEdit::placeholder {
                color: #334466;
            }
        """

    def _build_login_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        v = QVBoxLayout(panel)
        v.setSpacing(14)
        v.setAlignment(Qt.AlignCenter)

        title = QLabel("一 人 公 司")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #ccddf0; font-size: 26px; font-weight: 900; letter-spacing: 10px; background: transparent;")
        v.addWidget(title)

        sub = QLabel("TERRA · 蓝星基地")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #446688; font-size: 10px; letter-spacing: 5px; background: transparent;")
        v.addWidget(sub)
        v.addSpacing(10)

        self._login_user = QLineEdit()
        self._login_user.setPlaceholderText("呼叫代号")
        self._login_user.setStyleSheet(self._input_style())
        self._login_user.setAlignment(Qt.AlignCenter)
        v.addWidget(self._login_user)

        self._login_pass = QLineEdit()
        self._login_pass.setPlaceholderText("通行密钥")
        self._login_pass.setEchoMode(QLineEdit.Password)
        self._login_pass.setStyleSheet(self._input_style())
        self._login_pass.setAlignment(Qt.AlignCenter)
        self._login_pass.returnPressed.connect(self._do_login)
        v.addWidget(self._login_pass)

        v.addSpacing(6)

        btn = QPushButton("发 射")
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0066cc, stop:1 #0099ff);
                color: white; border: none; border-radius: 22px;
                padding: 10px 50px; font-size: 15px; font-weight: 700;
                letter-spacing: 10px; min-width: 200px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0088ee, stop:1 #00bbff); }
            QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0055aa, stop:1 #0077cc); }
        """)
        btn.clicked.connect(self._do_login)
        v.addWidget(btn, alignment=Qt.AlignCenter)

        switch = QLabel("没有许可？申请通行证 →")
        switch.setAlignment(Qt.AlignCenter)
        switch.setStyleSheet("color: #446688; font-size: 11px; background: transparent;")
        switch.setCursor(Qt.PointingHandCursor)
        switch.mousePressEvent = lambda e: self._switch_to_register()
        v.addWidget(switch)

        v.addStretch()
        return panel

    def _build_register_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        v = QVBoxLayout(panel)
        v.setSpacing(14)
        v.setAlignment(Qt.AlignCenter)

        title = QLabel("申请通行许可")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #ccddf0; font-size: 20px; font-weight: 800; letter-spacing: 6px; background: transparent;")
        v.addWidget(title)

        sub = QLabel("REGISTER · 新船员登记")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #446688; font-size: 10px; letter-spacing: 4px; background: transparent;")
        v.addWidget(sub)
        v.addSpacing(10)

        self._reg_user = QLineEdit()
        self._reg_user.setPlaceholderText("设定呼叫代号")
        self._reg_user.setStyleSheet(self._input_style())
        self._reg_user.setAlignment(Qt.AlignCenter)
        v.addWidget(self._reg_user)

        self._reg_pass = QLineEdit()
        self._reg_pass.setPlaceholderText("设定通行密钥")
        self._reg_pass.setEchoMode(QLineEdit.Password)
        self._reg_pass.setStyleSheet(self._input_style())
        self._reg_pass.setAlignment(Qt.AlignCenter)
        v.addWidget(self._reg_pass)

        self._reg_pass2 = QLineEdit()
        self._reg_pass2.setPlaceholderText("确认通行密钥")
        self._reg_pass2.setEchoMode(QLineEdit.Password)
        self._reg_pass2.setStyleSheet(self._input_style())
        self._reg_pass2.setAlignment(Qt.AlignCenter)
        self._reg_pass2.returnPressed.connect(self._do_register)
        v.addWidget(self._reg_pass2)

        v.addSpacing(6)

        btn = QPushButton("注 册")
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4455aa, stop:1 #6677cc);
                color: white; border: none; border-radius: 22px;
                padding: 10px 50px; font-size: 15px; font-weight: 700;
                letter-spacing: 10px; min-width: 200px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #5566cc, stop:1 #8899ee); }
        """)
        btn.clicked.connect(self._do_register)
        v.addWidget(btn, alignment=Qt.AlignCenter)

        back = QLabel("← 返回对接")
        back.setAlignment(Qt.AlignCenter)
        back.setStyleSheet("color: #446688; font-size: 11px; background: transparent;")
        back.setCursor(Qt.PointingHandCursor)
        back.mousePressEvent = lambda e: self._switch_to_login()
        v.addWidget(back)

        v.addStretch()
        return panel

    # ════════════════ 模式切换 ════════════════

    def _switch_to_register(self):
        self._stack.setCurrentIndex(1)
        self._mode = "register"
        self._reg_user.setFocus()

    def _switch_to_login(self):
        self._stack.setCurrentIndex(0)
        self._mode = "login"
        self._login_user.setFocus()

    # ════════════════ 动画 ════════════════

    def _tick(self):
        self._t += 0.018
        if self._earth:
            self._earth.angle += 0.005
        self._hud.update()

    # ════════════════ 绘制 ════════════════

    def _paint_hud(self, event):
        painter = QPainter(self._hud)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self._hud.width(), self._hud.height()

        if not self._earth:
            painter.end()
            return

        # ── 蓝星地球 ──
        self._earth.draw(painter)

        # ── 环绕卫星（小光点绕地球飞行） ──
        for i, phase in enumerate(self._orbit_sats):
            a = self._t * 0.4 + phase
            orb_r = self._earth.radius + 40 + i * 16
            sx = self._earth.cx + math.cos(a) * orb_r
            sy = self._earth.cy + math.sin(a) * orb_r * 0.85
            # 拖尾
            for trail in range(4):
                ta = a - trail * 0.08
                tx = self._earth.cx + math.cos(ta) * orb_r
                ty = self._earth.cy + math.sin(ta) * orb_r * 0.85
                alpha = int(80 - trail * 18)
                painter.setBrush(QBrush(QColor(180, 210, 255, alpha)))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(tx, ty), 2 - trail * 0.3, 2 - trail * 0.3)

        # ── 轨道线 ──
        painter.setPen(QPen(QColor(30, 70, 130, 25), 0.5))
        for i in range(3):
            orb_r = self._earth.radius + 45 + i * 20
            painter.drawEllipse(QPointF(self._earth.cx, self._earth.cy), orb_r, orb_r * 0.85)

        # ── 顶部标题 ──
        painter.setPen(QPen(QColor(80, 130, 200, 60), 1))
        painter.setFont(QFont("Menlo", 8))
        painter.drawText(QRectF(20, 10, w - 40, 18), Qt.AlignCenter, "BLUE PLANET · TERRA STATION")

        painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        self._hud.setGeometry(0, 0, w, h)
        self._cosmic.setGeometry(0, 0, w, h)
        self._earth = EarthGlobe(w // 2, h - 160, min(w, h) // 3)
        # 居中堆叠面板在地球上方
        self._stack.move(
            (w - 340) // 2,
            (h - 320) // 2 - 60
        )

    # ════════════════ 业务逻辑 ════════════════

    def _do_login(self):
        username = self._login_user.text().strip()
        password = self._login_pass.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "对接失败", "呼叫代号和通行密钥不能为空")
            return

        users = _load_users()
        if username in users and users[username] == password:
            self._open_dashboard()
        else:
            QMessageBox.warning(self, "对接失败", "呼叫代号或通行密钥错误")

    def _do_register(self):
        username = self._reg_user.text().strip()
        password = self._reg_pass.text().strip()
        password2 = self._reg_pass2.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "注册失败", "呼叫代号和通行密钥不能为空")
            return
        if len(username) < 2:
            QMessageBox.warning(self, "注册失败", "呼叫代号至少2个字符")
            return
        if len(password) < 3:
            QMessageBox.warning(self, "注册失败", "通行密钥至少3个字符")
            return
        if password != password2:
            QMessageBox.warning(self, "注册失败", "两次通行密钥不一致")
            return

        users = _load_users()
        if username in users:
            QMessageBox.warning(self, "注册失败", "该呼叫代号已被占用")
            return

        users[username] = password
        _save_users(users)
        QMessageBox.information(self, "注册成功", f"船员 {username} 已登记。请返回对接。")
        self._switch_to_login()
        self._login_user.setText(username)
        self._login_pass.setFocus()

    def _open_dashboard(self):
        from modules.auth.connect_window import ConnectWindow
        self._connect = ConnectWindow()
        self._connect.show()
        self.close()