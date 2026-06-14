# `core/shapes/venus.py`

> 路径：`core/shapes/venus.py` | 行数：110


---


```python
# -*- coding: utf-8 -*-
"""
金星 — 淡黄浓密大气 + 云层漩涡 + 温室光晕
"""
import math, random
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import (
    QPainter, QRadialGradient, QColor, QPen, QBrush, QPainterPath
)


def paint(painter: QPainter, center: QPointF, radius: float,
          anim_t: float, hovered: bool, alpha: float):
    cx, cy = center.x(), center.y()
    p = painter
    p.save()
    if alpha < 1.0:
        p.setOpacity(alpha)

    # ── 基底（浓密淡黄大气）──
    base = QRadialGradient(cx, cy, radius * 1.02)
    base.setColorAt(0.0, QColor(250, 240, 180))
    base.setColorAt(0.3, QColor(235, 220, 150))
    base.setColorAt(0.6, QColor(210, 190, 120))
    base.setColorAt(0.85, QColor(180, 155, 90))
    base.setColorAt(1.0, QColor(140, 110, 55))
    p.setBrush(base); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 云层漩涡（多层螺旋叠加）──
    for layer in range(4):
        swirl_paths = []
        swirl_rng = random.Random(77 + layer * 13)
        swirl_offset = anim_t * (0.06 + layer * 0.015)
        for i in range(5):
            sw_path = QPainterPath()
            sw_start_angle = swirl_rng.uniform(0, 2 * math.pi)
            sw_center_dx = swirl_rng.uniform(-radius * 0.35, radius * 0.35)
            sw_center_dy = swirl_rng.uniform(-radius * 0.35, radius * 0.35)
            swx = cx + sw_center_dx
            swy = cy + sw_center_dy
            sw_len = radius * swirl_rng.uniform(0.4, 0.85)
            sw_width = radius * swirl_rng.uniform(0.04, 0.12)
            sw_start_x = swx + math.cos(sw_start_angle + swirl_offset) * sw_len * 0.3
            sw_start_y = swy + math.sin(sw_start_angle + swirl_offset) * sw_len * 0.3
            sw_path.moveTo(sw_start_x, sw_start_y)
            for j in range(6):
                frac = j / 5.0
                a = sw_start_angle + swirl_offset + frac * math.pi * 0.9
                r = sw_len * (0.3 + 0.7 * frac)
                x = swx + math.cos(a) * r
                y = swy + math.sin(a) * r
                sw_path.lineTo(x, y)
            swirl_paths.append(sw_path)

        for sw_path in swirl_paths:
            sw_pen = QPen(QColor(220, 205, 150, 55 - layer * 10), sw_width * 2.5)
            sw_pen.setCapStyle(Qt.RoundCap)
            p.setPen(sw_pen); p.setBrush(Qt.NoBrush)
            p.drawPath(sw_path)

    # ── 云层粒子光点 ──
    cloud_rng = random.Random(int(anim_t * 120) % 100000 + 4321)
    p.setPen(Qt.NoPen)
    for _ in range(20):
        ca = cloud_rng.uniform(0, 2 * math.pi)
        cd = radius * cloud_rng.uniform(0.15, 0.88)
        cx2 = cx + math.cos(ca) * cd
        cy2 = cy + math.sin(ca) * cd
        cs = cloud_rng.uniform(0.5, 2.0)
        cg = QRadialGradient(cx2, cy2, cs * 2.0)
        ca2 = cloud_rng.randint(20, 60)
        cg.setColorAt(0.0, QColor(255, 250, 220, ca2))
        cg.setColorAt(0.6, QColor(240, 230, 180, ca2 // 2))
        cg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(cg)
        p.drawEllipse(QPointF(cx2, cy2), cs * 2.0, cs * 2.0)

    # ── 厚大气层光晕（温室效应）──
    for i in range(3):
        halo_r = radius * (0.92 + i * 0.05)
        halo = QRadialGradient(cx, cy, halo_r)
        ha = int((25 - i * 7) * (0.8 + 0.2 * abs(math.sin(anim_t * 1.1))))
        halo.setColorAt(0.0, QColor(255, 255, 255, 0))
        halo.setColorAt(0.7, QColor(255, 255, 255, 0))
        halo.setColorAt(0.85, QColor(255, 230, 150, ha // 2))
        halo.setColorAt(0.93, QColor(255, 200, 100, ha))
        halo.setColorAt(0.97, QColor(200, 150, 60, ha // 2))
        halo.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(halo); p.setPen(Qt.NoPen)
        p.drawEllipse(center, halo_r, halo_r)

    # ── 外圈热辐射辉光 ──
    outer_glow = QRadialGradient(cx, cy, radius * 1.25)
    outer_glow.setColorAt(0.0, QColor(255, 255, 255, 0))
    outer_glow.setColorAt(0.6, QColor(255, 255, 255, 0))
    outer_glow.setColorAt(0.85, QColor(255, 180, 100, 12))
    outer_glow.setColorAt(0.95, QColor(200, 120, 50, 6))
    outer_glow.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(outer_glow); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius * 1.25, radius * 1.25)

    # ── 悬停 ──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        p.setPen(QPen(QColor(255, 220, 140, int(200 * hp)), 2.0))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 2, radius + 2)

    p.restore()

```
