"""
智能中心 → AI核心 · NEURAL NEXUS（小星球导航模式）
宇宙主题窗口：AI核心能量球 + 5颗环绕小星球，点击弹出独立子窗口
"""
import os, math
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QFrame, QApplication,
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QColor, QFont, QPainter, QRadialGradient, QBrush, QPen, QFontMetrics

# ═══════ 天体身份 ═══════
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

# ═══════ 5颗小星球配置 ═══════
PLANETS = [
    {"id": "ai_chat",       "name": "AI助手",   "color": QColor(100, 80, 255),   "orbit": 130, "size": 30},
    {"id": "ai_center",     "name": "智能中心", "color": QColor(170, 60, 255),   "orbit": 190, "size": 30},
    {"id": "digital_emp",   "name": "数字员工", "color": QColor(60, 200, 255),   "orbit": 250, "size": 30},
    {"id": "tools",         "name": "工具箱",   "color": QColor(120, 220, 80),   "orbit": 310, "size": 30},
    {"id": "scan",          "name": "扫码工具", "color": QColor(255, 180, 40),   "orbit": 370, "size": 30},
]


# ═══════ 导航 HUD 层（绘制能量球 + 行星 + 轨道） ═══════
class NavigationHUD(QWidget):
    """在 CosmicBackground 上方透明叠加，绘制能量球 + 行星 + 轨道"""

    planet_clicked = None  # 主窗口注入回调

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self._center = QPointF(0, 0)
        self._hovered_planet = None
        self._angle = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)

    def _tick(self):
        self._angle = (self._angle + 0.3) % 360.0
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._center = QPointF(self.width() / 2, self.height() / 2)

    def _planet_positions(self):
        w2 = self._center
        positions = []
        for i, p in enumerate(PLANETS):
            offset_angle = i * (360.0 / len(PLANETS))
            rad = math.radians(self._angle + offset_angle)
            x = w2.x() + p["orbit"] * math.cos(rad)
            y = w2.y() + p["orbit"] * math.sin(rad)
            positions.append((p, QPointF(x, y)))
        return positions

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w2 = self._center

        # ── 轨道线 ──
        for planet in PLANETS:
            orbit_r = planet["orbit"]
            pen = QPen(QColor(170, 80, 255, 15))
            pen.setWidth(1)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(w2, orbit_r, orbit_r)

        # ── 能量连接线 ──
        for planet_data, pos in self._planet_positions():
            p.setPen(QPen(QColor(170, 80, 255, 25)))
            p.drawLine(QPointF(w2.x(), w2.y()), pos)

        # ── 5颗小行星 ──
        for planet_data, pos in self._planet_positions():
            r = planet_data["size"]
            color = planet_data["color"]
            is_hovered = (self._hovered_planet == planet_data["id"])

            glow = QRadialGradient(pos, r * 2.2)
            glow.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 80))
            glow.setColorAt(0.5, QColor(color.red(), color.green(), color.blue(), 20))
            glow.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))
            p.setBrush(QBrush(glow))
            p.setPen(Qt.NoPen)
            p.drawEllipse(pos, r * 2.2, r * 2.2)

            body_grad = QRadialGradient(pos.x() - r * 0.3, pos.y() - r * 0.3, r)
            body_grad.setColorAt(0, color.lighter(180))
            body_grad.setColorAt(0.6, color)
            body_grad.setColorAt(1, color.darker(200))
            p.setBrush(QBrush(body_grad))
            pen_color = QColor(255, 255, 255, 180) if is_hovered else QColor(color.red(), color.green(), color.blue(), 60)
            p.setPen(QPen(pen_color, 2))
            p.drawEllipse(pos, r, r)

            fm = QFontMetrics(QFont("PingFang SC", 9))
            text = planet_data["name"]
            tw = fm.horizontalAdvance(text)
            tx = pos.x() - tw / 2
            ty = pos.y() + r + 14
            p.setPen(QColor(200, 170, 240))
            p.setFont(QFont("PingFang SC", 9))
            p.drawText(QPointF(tx, ty), text)

        # ── 中央 AI核心能量球 ──
        core_r = 45
        core_glow = QRadialGradient(w2, core_r * 2.5)
        core_glow.setColorAt(0, QColor(170, 60, 255, 100))
        core_glow.setColorAt(0.4, QColor(170, 60, 255, 30))
        core_glow.setColorAt(1, QColor(170, 60, 255, 0))
        p.setBrush(QBrush(core_glow))
        p.setPen(Qt.NoPen)
        p.drawEllipse(w2, core_r * 2.5, core_r * 2.5)

        body = QRadialGradient(w2.x() - 8, w2.y() - 8, core_r)
        body.setColorAt(0, QColor(220, 160, 255))
        body.setColorAt(0.3, QColor(170, 60, 255))
        body.setColorAt(0.7, QColor(100, 20, 180))
        body.setColorAt(1, QColor(50, 10, 100))
        p.setBrush(QBrush(body))
        p.setPen(QPen(QColor(200, 140, 255, 150), 2))
        p.drawEllipse(w2, core_r, core_r)

        pupil = QRadialGradient(w2, core_r * 0.6)
        pupil.setColorAt(0, QColor(255, 255, 255, 60))
        pupil.setColorAt(1, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(pupil))
        p.setPen(Qt.NoPen)
        p.drawEllipse(w2, core_r * 0.55, core_r * 0.55)

        fm2 = QFontMetrics(QFont("PingFang SC", 10, QFont.Bold))
        label = "NEURAL"
        lw = fm2.horizontalAdvance(label)
        p.setPen(QColor(210, 170, 255))
        p.setFont(QFont("PingFang SC", 10, QFont.Bold))
        p.drawText(QPointF(w2.x() - lw / 2, w2.y() - core_r - 18), label)

        p.end()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        self._hovered_planet = None
        for planet_data, pt in self._planet_positions():
            r = planet_data["size"] + 8
            dx = pos.x() - pt.x()
            dy = pos.y() - pt.y()
            if dx * dx + dy * dy <= r * r:
                self._hovered_planet = planet_data["id"]
                self.setCursor(Qt.PointingHandCursor)
                self.update()
                return
        self.setCursor(Qt.ArrowCursor)
        if self._hovered_planet is not None:
            self._hovered_planet = None
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._hovered_planet:
            if self.planet_clicked:
                self.planet_clicked(self._hovered_planet)


# ═══════ 小星球导航主窗口 ═══════
class IntelligenceWindow(QMainWindow):
    """AI核心 · NEURAL NEXUS — 小星球导航模式"""

    def __init__(self, parent=None, role="admin"):
        super().__init__(parent)
        self._role = role
        self.setWindowTitle("一人公司 — AI核心 · NEURAL NEXUS")
        self.setMinimumSize(900, 680)
        self._build_ui()

    def _build_ui(self):
        from core.cosmic import CosmicBackground
        bg = CosmicBackground()
        self.setCentralWidget(bg)

        self._hud = NavigationHUD(bg)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        self._hud.planet_clicked = self._on_planet_clicked

        header = QWidget(bg)
        header.setAttribute(Qt.WA_TranslucentBackground)
        header.setFixedHeight(70)
        header.setGeometry(0, 10, self.width(), 70)

        hl = QVBoxLayout(header)
        hl.setSpacing(2)
        title = QLabel("AI核心")
        title.setStyleSheet("color: #ddaaff; font-size: 24px; font-weight: 800; letter-spacing: 8px; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        hl.addWidget(title)
        subtitle = QLabel("NEURAL NEXUS · 智能中枢")
        subtitle.setStyleSheet("color: #776699; font-size: 11px; letter-spacing: 3px; background: transparent;")
        subtitle.setAlignment(Qt.AlignCenter)
        hl.addWidget(subtitle)

        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(170,80,255,50),
                stop:0.5 rgba(200,120,255,120),
                stop:0.7 rgba(170,80,255,50), stop:1 transparent);
            border: none;
        """)
        hl.addWidget(line)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_hud'):
            self._hud.setGeometry(0, 0, self.width(), self.height())

    # ═══════ 行星点击路由 ═══════
    def _on_planet_clicked(self, planet_id):
        if planet_id == "ai_chat":
            from modules.intelligence.ai_chat_window import AiChatWindow
            dlg = AiChatWindow(self)
            dlg.exec_()
        elif planet_id == "ai_center":
            from modules.intelligence.ai_center_window import AiCenterWindow
            dlg = AiCenterWindow(self)
            dlg.exec_()
        elif planet_id == "digital_emp":
            from modules.intelligence.digital_emp_window import DigitalEmpWindow
            dlg = DigitalEmpWindow(self)
            dlg.exec_()
        elif planet_id == "tools":
            from modules.intelligence.tools_window import ToolsWindow
            dlg = ToolsWindow(self)
            dlg.exec_()
        elif planet_id == "scan":
            from modules.intelligence.scan_window import ScanWindow
            dlg = ScanWindow(self)
            dlg.exec_()