# `modules/intelligence/backup_p02/intelligence_window.py`

> 路径：`modules/intelligence/backup_p02/intelligence_window.py` | 行数：204


---


```python
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
    {"id": "ai_chat",       "name": "AI对话",   "style": "neptune", "orbit": 120, "size": 52},
    {"id": "digital_emp",   "name": "数字员工", "style": "mars",    "orbit": 195, "size": 54},
    {"id": "ai_assistant",  "name": "AI助手",   "style": "jupiter", "orbit": 270, "size": 60},
    {"id": "tools",         "name": "工具箱",   "style": "saturn",  "orbit": 345, "size": 54},
    {"id": "scan",          "name": "扫码工具", "style": "mercury", "orbit": 420, "size": 52},
    {"id": "system_mgmt",   "name": "系统管理", "style": "earth",   "orbit": 495, "size": 56},
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
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)

    def _tick(self):
        self._angle = (self._angle + 0.25) % 360.0
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._center = QPointF(self.width() / 2, self.height() / 2)

    def _planet_positions(self):
        w2 = self._center
        positions = []
        n = len(PLANETS)
        for i, p in enumerate(PLANETS):
            offset_angle = i * (360.0 / n)
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
            paint_orbit(p, w2, planet["orbit"])

        # ── 能量连接线 ──
        for _, pos in self._planet_positions():
            paint_energy_line(p, w2, pos)

        # ── 行星 ──
        for planet_data, pos in self._planet_positions():
            style = PLANET_STYLES.get(planet_data["style"], PLANET_STYLES["neptune"])
            hovered = (self._hovered_planet == planet_data["id"])
            paint_planet(p, pos, planet_data["size"], style,
                         hovered=hovered, label=planet_data["name"], font_size=10)

        # ── 中央核心地球 ──
        core_r = 68
        paint_planet(p, w2, core_r, PLANET_STYLES["earth"],
                     label="NEURAL", font_size=12)
        # 额外一层蓝色科技辉光
        tech_glow = QPen(QColor(100, 180, 255, 30))
        tech_glow.setWidth(1)
        p.setPen(tech_glow)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(w2, core_r + 12, core_r + 12)

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
            dlg.show()
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

```
