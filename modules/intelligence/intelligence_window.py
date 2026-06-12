# -*- coding: utf-8 -*-
"""
智能中心 · NEURAL NEXUS（真实星球导航模式）
宇宙主题窗口：6颗真实风格星球环绕中央能量核心，点击弹出子窗口
"""
import os, math
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QFrame,
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QFontMetrics

from core.planet_painter import (
    PLANET_STYLES, paint_planet, paint_orbit, paint_energy_line,
)

# ═══════ 6颗星球配置 ═══════
PLANETS = [
    {"id": "ai_chat",       "name": "AI对话",   "style": "neptune", "orbit": 120, "size": 51},
    {"id": "digital_emp",   "name": "数字员工", "style": "mars",    "orbit": 195, "size": 54},
    {"id": "ai_assistant",  "name": "AI助手",   "style": "jupiter", "orbit": 270, "size": 61},
    {"id": "tools",         "name": "工具箱",   "style": "saturn",  "orbit": 345, "size": 54},
    {"id": "scan",          "name": "扫码工具", "style": "mercury", "orbit": 420, "size": 51},
    {"id": "system_mgmt",   "name": "系统管理", "style": "venus",   "orbit": 495, "size": 58},
]

# ═══════ 导航 HUD 层 ═══════
class NavigationHUD(QWidget):
    """真实星球导航叠加层"""

    planet_clicked = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self._center = QPointF(0, 0)
        self._hovered_planet = None
        self._angle = 0.0
        self._anim_t = 0.0
        self._orbits = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)  # ~60fps (原 50ms)

    def _compute_orbits(self):
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return
        n = len(PLANETS)
        available_r = min(w, h) / 2 * 0.9
        max_size = max(p["size"] for p in PLANETS)
        max_orbit = available_r - max_size / 2
        if n > 3:
            base_r = max_orbit / (1 + (n - 1) * 0.4)
            self._orbits = [base_r * (1 + i * 0.4) for i in range(n)]
        else:
            self._orbits = [max_orbit * (i + 1) / n for i in range(n)]

    def _tick(self):
        self._angle = (self._angle + 0.25) % 360.0
        self._anim_t += 0.05
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._center = QPointF(self.width() / 2, self.height() / 2)
        self._compute_orbits()

    def _planet_positions(self):
        w2 = self._center
        positions = []
        n = len(PLANETS)
        for i, p in enumerate(PLANETS):
            orbit = self._orbits[i] if i < len(self._orbits) else p.get("orbit", 120)
            offset_angle = i * (360.0 / n)
            rad = math.radians(self._angle + offset_angle)
            x = w2.x() + orbit * math.cos(rad)
            y = w2.y() + orbit * math.sin(rad)
            positions.append((p, QPointF(x, y)))
        return positions

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w2 = self._center
        anim_t = self._anim_t

        # ── 轨道线 ──
        for i, planet in enumerate(PLANETS):
            orbit = self._orbits[i] if i < len(self._orbits) else planet.get("orbit", 120)
            paint_orbit(p, w2, orbit, anim_t=anim_t)

        # ── 能量连接线 ──
        for _, pos in self._planet_positions():
            paint_energy_line(p, w2, pos, anim_t=anim_t)

        # ── 行星 ──
        for planet_data, pos in self._planet_positions():
            style = PLANET_STYLES.get(planet_data["style"], PLANET_STYLES["neptune"])
            hovered = (self._hovered_planet == planet_data["id"])
            paint_planet(p, pos, planet_data["size"], style,
                         hovered=hovered, label=planet_data["name"],
                         font_size=9, anim_t=anim_t)

        # ── 中央核心地球 ──
        core_r = 82
        paint_planet(p, w2, core_r, PLANET_STYLES["earth"],
                     label="NEURAL", font_size=10, anim_t=anim_t)
        # 额外一层蓝色科技辉光（呼吸脉冲）
        pulse = 0.7 + 0.3 * abs(math.sin(anim_t * 2.2))
        tech_glow = QPen(QColor(100, 180, 255, int(50 * pulse)))
        tech_glow.setWidthF(1.5)
        p.setPen(tech_glow)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(w2, core_r + 8, core_r + 8)

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


# ═══════ 主窗口 ═══════
class IntelligenceWindow(QMainWindow):
    """智能中心 · NEURAL NEXUS — 真实星球导航"""

    def __init__(self, parent=None, role="admin", opcclaw_engine=None):
        super().__init__(parent)
        self._role = role
        self._opcclaw_engine = opcclaw_engine
        self.setWindowTitle("一人公司 — 智能中心 · NEURAL NEXUS")
        self.setMinimumSize(1200, 850)
        self._build_ui()

    def _build_ui(self):
        from core.cosmic import CosmicBackground
        bg = CosmicBackground()
        self.setCentralWidget(bg)

        self._hud = NavigationHUD(self)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        self._hud.planet_clicked = self._on_planet_clicked
        self._hud.raise_()

        header = QWidget(self)
        header.setAttribute(Qt.WA_TranslucentBackground)
        header.setFixedHeight(70)
        header.setGeometry(0, 10, self.width(), 70)

        hl = QVBoxLayout(header)
        hl.setSpacing(2)
        title = QLabel("智能中心")
        title.setStyleSheet(
            "color: #ddaaff; font-size: 24px; font-weight: 800;"
            " letter-spacing: 8px; background: transparent;"
        )
        title.setAlignment(Qt.AlignCenter)
        hl.addWidget(title)
        subtitle = QLabel("NEURAL NEXUS · 6颗真实星球")
        subtitle.setStyleSheet(
            "color: #776699; font-size: 11px; letter-spacing: 3px;"
            " background: transparent;"
        )
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

    def _on_planet_clicked(self, planet_id):
        if planet_id == "ai_chat":
            from modules.intelligence.ai_chat_window import AIChatWindow
            dlg = AIChatWindow(self, opcclaw_engine=self._opcclaw_engine)
            dlg.exec_()
        elif planet_id == "digital_emp":
            from modules.intelligence.digital_emp_window import DigitalEmpWindow
            dlg = DigitalEmpWindow(self)
            dlg.exec_()
        elif planet_id == "ai_assistant":
            from modules.intelligence.ai_assistant_window import AIAssistantWindow
            dlg = AIAssistantWindow(self, opcclaw_engine=self._opcclaw_engine)
            dlg.show()
        elif planet_id == "tools":
            from modules.intelligence.tools_window import ToolsWindow
            dlg = ToolsWindow(self)
            dlg.exec_()
        elif planet_id == "scan":
            from modules.intelligence.scan_window import ScanWindow
            dlg = ScanWindow(self)
            dlg.exec_()
        elif planet_id == "system_mgmt":
            from modules.system.system_hub_window import SystemHubWindow
            dlg = SystemHubWindow(self)
            dlg.show()
