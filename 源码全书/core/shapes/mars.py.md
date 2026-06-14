# `core/shapes/mars.py`

> 路径：`core/shapes/mars.py` | 行数：109


---


```python
# -*- coding: utf-8 -*-
"""
火星 — 红色氧化铁地表 + 极冠白色 + 沙尘暴粒子
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

    # ── 基底（火星红棕渐变）──
    base = QRadialGradient(cx - radius * 0.15, cy - radius * 0.15, radius * 1.1)
    base.setColorAt(0.0, QColor(235, 140, 80))
    base.setColorAt(0.35, QColor(200, 95, 45))
    base.setColorAt(0.65, QColor(165, 65, 30))
    base.setColorAt(0.85, QColor(130, 45, 20))
    base.setColorAt(1.0, QColor(90, 25, 10))
    p.setBrush(base); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 地表纹理（暗斑模拟陨石坑/高地）──
    tex_rng = random.Random(42)
    for _ in range(8):
        tx = cx + tex_rng.uniform(-radius * 0.72, radius * 0.72)
        ty = cy + tex_rng.uniform(-radius * 0.72, radius * 0.72)
        tr = radius * tex_rng.uniform(0.06, 0.18)
        if (tx - cx)**2 + (ty - cy)**2 < (radius * 0.8)**2:
            spot = QRadialGradient(tx, ty, tr)
            spot.setColorAt(0.0, QColor(150, 55, 20, 80))
            spot.setColorAt(0.6, QColor(160, 60, 25, 40))
            spot.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setBrush(spot); p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(tx, ty), tr, tr)

    # ── 陨石坑（小环）──
    for _ in range(6):
        crx = cx + tex_rng.uniform(-radius * 0.55, radius * 0.55)
        cry = cy + tex_rng.uniform(-radius * 0.55, radius * 0.55)
        crr = radius * tex_rng.uniform(0.04, 0.12)
        if (crx - cx)**2 + (cry - cy)**2 < (radius * 0.7)**2:
            p.setBrush(QColor(170, 70, 30, 50))
            p.setPen(QPen(QColor(120, 40, 15, 60), 1.0))
            p.drawEllipse(QPointF(crx, cry), crr, crr)

    # ── 极冠（顶部白色冰盖）──
    cap_path = QPainterPath()
    cap_path.moveTo(cx - radius * 0.45, cy - radius * 0.45)
    cap_path.quadTo(cx, cy - radius * 1.05, cx + radius * 0.45, cy - radius * 0.45)
    cap_path.quadTo(cx + radius * 0.15, cy - radius * 0.75, cx, cy - radius * 0.50)
    cap_path.quadTo(cx - radius * 0.15, cy - radius * 0.75, cx - radius * 0.45, cy - radius * 0.45)
    cap_grad = QRadialGradient(cx, cy - radius * 0.82, radius * 0.55)
    cap_grad.setColorAt(0.0, QColor(255, 255, 255, 200))
    cap_grad.setColorAt(0.5, QColor(240, 245, 250, 120))
    cap_grad.setColorAt(1.0, QColor(220, 230, 240, 0))
    p.setBrush(cap_grad); p.setPen(Qt.NoPen)
    p.drawPath(cap_path)

    # ── 大气薄层 ──
    atmo = QRadialGradient(cx, cy, radius * 1.05)
    atmo.setColorAt(0.0, QColor(255, 255, 255, 0))
    atmo.setColorAt(0.82, QColor(255, 255, 255, 0))
    atmo.setColorAt(0.92, QColor(255, 180, 140, 30))
    atmo.setColorAt(0.97, QColor(255, 150, 100, 15))
    atmo.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(atmo); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius * 1.05, radius * 1.05)

    # ── 沙尘暴粒子 ──
    storm_rng = random.Random(int(anim_t * 180) % 100000 + 1234)
    for _ in range(30):
        sa = storm_rng.uniform(0, 2 * math.pi)
        sd = radius * (0.3 + 0.7 * storm_rng.random())
        storm_angle = anim_t * 0.4 + storm_rng.uniform(0, 0.8)
        sx = cx + math.cos(sa + storm_angle) * sd
        sy = cy + math.sin(sa + storm_angle) * sd * 0.55
        ss = storm_rng.uniform(0.6, 2.2)
        sg = QRadialGradient(sx, sy, ss * 2.5)
        sa2 = storm_rng.randint(25, 80)
        sg.setColorAt(0.0, QColor(220, 160, 110, sa2))
        sg.setColorAt(0.5, QColor(200, 120, 80, sa2 // 2))
        sg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(sg); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(sx, sy), ss * 2.5, ss * 2.5)

    # ── 球面高光 ──
    highlight = QRadialGradient(cx - radius * 0.28, cy - radius * 0.30, radius * 0.35)
    highlight.setColorAt(0.0, QColor(255, 210, 170, 50))
    highlight.setColorAt(0.5, QColor(255, 180, 140, 15))
    highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(highlight); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 悬停 ──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        p.setPen(QPen(QColor(255, 140, 80, int(200 * hp)), 2.0))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 2, radius + 2)

    p.restore()

```
