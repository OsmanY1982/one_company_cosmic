# `modules/system/system_hub_window.py`

> 路径：`modules/system/system_hub_window.py` | 行数：178


---


```python
# -*- coding: utf-8 -*-
"""
系统管理中心 · 子星球导航
环绕太阳核心的5颗子星球，点击分别路由到系统模块窗口
"""
import math
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QFrame,
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QFontMetrics

from core.planet_painter import (
    PLANET_STYLES, paint_planet, paint_orbit, paint_energy_line,
)

# ═══════ 5颗子星球配置 ═══════
PLANETS = [
    {"id": "system_settings", "name": "系统设置", "style": "uranus",  "orbit": 140, "size": 30},
    {"id": "activation",      "name": "激活码",   "style": "sun",     "orbit": 210, "size": 30},
    {"id": "cloud_sync",      "name": "云端同步", "style": "neptune", "orbit": 280, "size": 30},
    {"id": "system_logs",     "name": "系统日志", "style": "pluto",   "orbit": 350, "size": 30},
    {"id": "update_check",    "name": "更新检测", "style": "moon",    "orbit": 420, "size": 30},
]


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

        for planet in PLANETS:
            paint_orbit(p, w2, planet["orbit"], alpha=10)

        for planet_data, pos in self._planet_positions():
            paint_energy_line(p, w2, pos, alpha=15)

        for planet_data, pos in self._planet_positions():
            style = PLANET_STYLES.get(planet_data.get("style"), PLANET_STYLES["neptune"])
            is_hovered = (self._hovered_planet == planet_data["id"])
            paint_planet(p, pos, planet_data["size"], style,
                         hovered=is_hovered, label=planet_data["name"], font_size=9)

        # 中央核心 · 太阳
        paint_planet(p, w2, 38, PLANET_STYLES["sun"], label="SYS", font_size=10)

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


class SystemHubWindow(QMainWindow):
    """系统管理中心 · 子星球导航主窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("一人公司 — 系统管理中心 · SOLAR HUB")
        self.setMinimumSize(800, 650)
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
        title = QLabel("系统管理")
        title.setStyleSheet("color: #ddaaff; font-size: 24px; font-weight: 800; letter-spacing: 8px; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        hl.addWidget(title)
        subtitle = QLabel("SOLAR HUB · 5颗子星球")
        subtitle.setStyleSheet("color: #776699; font-size: 11px; letter-spacing: 3px; background: transparent;")
        subtitle.setAlignment(Qt.AlignCenter)
        hl.addWidget(subtitle)

        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(255,180,40,50),
                stop:0.5 rgba(255,200,60,120),
                stop:0.7 rgba(255,180,40,50), stop:1 transparent);
            border: none;
        """)
        hl.addWidget(line)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_hud'):
            self._hud.setGeometry(0, 0, self.width(), self.height())

    def _on_planet_clicked(self, planet_id):
        if planet_id == "system_settings":
            from modules.system.system_window import SystemWindow
            dlg = SystemWindow(self)
            dlg.show()
        elif planet_id == "activation":
            from modules.system.activation_window import ActivationWindow
            dlg = ActivationWindow(self)
            dlg.exec_()
        elif planet_id == "cloud_sync":
            from modules.system.cloud_window import CloudWindow
            dlg = CloudWindow(self)
            dlg.exec_()
        elif planet_id == "system_logs":
            from modules.system.logs_window import LogsWindow
            dlg = LogsWindow(self)
            dlg.show()
        elif planet_id == "update_check":
            from modules.system.update_dialog import UpdateDialog
            dlg = UpdateDialog(self)
            dlg.exec_()

```
