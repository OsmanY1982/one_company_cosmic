# -*- coding: utf-8 -*-
"""
AI 助手导航 HUD — 12颗真实星球环绕中央 AI 核心
"""
import math
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter

from core.planet_painter import (
    PLANET_STYLES, paint_planet, paint_orbit, paint_energy_line,
)

# ═══════════════════════════════════════════
# 12颗星球配置
# ═══════════════════════════════════════════
PLANETS = [
    {"id": "super_intelligence",   "name": "超级智能",     "style": "jupiter",  "orbit": 100, "size": 51},
    {"id": "enhanced_chat",        "name": "增强对话",     "style": "neptune",  "orbit": 140, "size": 44},
    {"id": "knowledge_base",       "name": "知识库",       "style": "uranus",   "orbit": 180, "size": 48},
    {"id": "system_monitor",       "name": "系统监控",     "style": "mars",     "orbit": 220, "size": 44},
    {"id": "quick_actions",        "name": "快捷操作",     "style": "mercury",  "orbit": 260, "size": 41},
    {"id": "ai_dashboard",         "name": "AI仪表盘",     "style": "saturn",   "orbit": 300, "size": 51},
    {"id": "anomaly_detector",     "name": "异常检测",     "style": "pluto",    "orbit": 340, "size": 41},
    {"id": "recommendation_engine","name": "推荐引擎",     "style": "sun",      "orbit": 380, "size": 44},
    {"id": "data_visualization",   "name": "数据可视化",   "style": "moon",     "orbit": 420, "size": 44},
    {"id": "smart_workflow",       "name": "智能工作流",   "style": "venus",    "orbit": 460, "size": 48},
    {"id": "business_ai",          "name": "商业AI",       "style": "exoplanet",  "orbit": 500, "size": 51},
    {"id": "voice_interface",      "name": "语音接口",     "style": "crystal",  "orbit": 540, "size": 44},
]


class NavigationHUD(QWidget):
    """透明叠加层 — 13颗星球 + 轨道 + 中央 AI 核心"""

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
        self._angle = (self._angle + 0.2) % 360.0
        self._anim_t += 0.05
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._center = QPointF(self.width() / 2, self.height() / 2)
        self._compute_orbits()

    def _planet_positions(self):
        w2 = self._center
        positions = []
        for i, p in enumerate(PLANETS):
            orbit = self._orbits[i] if i < len(self._orbits) else p.get("orbit", 100)
            offset_angle = i * (360.0 / len(PLANETS))
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
            orbit = self._orbits[i] if i < len(self._orbits) else planet.get("orbit", 100)
            paint_orbit(p, w2, orbit, anim_t=anim_t)

        # ── 能量连接线 ──
        for _, pos in self._planet_positions():
            paint_energy_line(p, w2, pos, anim_t=anim_t)

        # ── 12颗行星 ──
        for planet_data, pos in self._planet_positions():
            style = PLANET_STYLES.get(planet_data["style"], PLANET_STYLES["neptune"])
            hovered = (self._hovered_planet == planet_data["id"])
            paint_planet(p, pos, planet_data["size"], style,
                         hovered=hovered, label=planet_data["name"],
                         font_size=9, anim_t=anim_t)

        # ── 中央 AI 核心 · 地球 ──
        paint_planet(p, w2, 71, PLANET_STYLES["earth"], label="CREW",
                     font_size=10, anim_t=anim_t)

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