# `core/shapes/pluto.py`

> 路径：`core/shapes/pluto.py` | 行数：108


---


```python
# -*- coding: utf-8 -*-
"""
冥王星 — 淡棕白 + 心形区域暗示 + 稀薄大气
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

    # ── 基底（淡棕→米白渐变）──
    base = QRadialGradient(cx, cy, radius * 1.05)
    base.setColorAt(0.0, QColor(235, 210, 180))
    base.setColorAt(0.30, QColor(210, 180, 150))
    base.setColorAt(0.55, QColor(180, 150, 120))
    base.setColorAt(0.75, QColor(150, 120, 95))
    base.setColorAt(0.90, QColor(110, 85, 65))
    base.setColorAt(1.0, QColor(70, 50, 38))
    p.setBrush(base); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 地表纹理斑点（冰氮/甲烷混合暗斑）──
    tex_rng = random.Random(73)
    for _ in range(12):
        tx = cx + tex_rng.uniform(-radius * 0.80, radius * 0.80)
        ty = cy + tex_rng.uniform(-radius * 0.80, radius * 0.80)
        tr = radius * tex_rng.uniform(0.05, 0.15)
        if (tx - cx)**2 + (ty - cy)**2 > (radius * 0.88)**2:
            continue
        spot = QRadialGradient(tx, ty, tr)
        s_a = tex_rng.randint(30, 80)
        shade = tex_rng.choice([(200, 190, 175), (160, 140, 120), (120, 100, 85)])
        spot.setColorAt(0.0, QColor(shade[0], shade[1], shade[2], s_a))
        spot.setColorAt(0.7, QColor(shade[0], shade[1], shade[2], s_a // 3))
        spot.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(spot); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(tx, ty), tr, tr)

    # ── 心形区域（Tombaugh Regio：亮白色心形暗示）──
    heart_cx = cx + radius * 0.08
    heart_cy = cy - radius * 0.18
    heart_s = radius * 0.32
    heart_path = QPainterPath()
    # 左半心
    heart_path.moveTo(heart_cx, heart_cy + heart_s * 0.35)
    heart_path.cubicTo(
        heart_cx - heart_s * 1.05, heart_cy,
        heart_cx - heart_s * 0.80, heart_cy - heart_s * 0.50,
        heart_cx, heart_cy - heart_s * 0.15
    )
    # 右半心
    heart_path.cubicTo(
        heart_cx + heart_s * 0.80, heart_cy - heart_s * 0.50,
        heart_cx + heart_s * 1.05, heart_cy,
        heart_cx, heart_cy + heart_s * 0.35
    )
    heart_grad = QRadialGradient(heart_cx, heart_cy - heart_s * 0.1, heart_s * 0.9)
    heart_grad.setColorAt(0.0, QColor(250, 245, 235, 150))
    heart_grad.setColorAt(0.4, QColor(240, 230, 215, 120))
    heart_grad.setColorAt(0.7, QColor(220, 200, 180, 60))
    heart_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(heart_grad); p.setPen(Qt.NoPen)
    p.drawPath(heart_path)

    # ── 稀薄大气层（淡蓝薄辉）──
    atmo = QRadialGradient(cx, cy, radius * 1.08)
    atmo.setColorAt(0.0, QColor(255, 255, 255, 0))
    atmo.setColorAt(0.80, QColor(255, 255, 255, 0))
    atmo.setColorAt(0.90, QColor(140, 180, 220, 28))
    atmo.setColorAt(0.95, QColor(100, 140, 190, 18))
    atmo.setColorAt(0.98, QColor(70, 100, 150, 10))
    atmo.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(atmo); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius * 1.08, radius * 1.08)

    # ── 稀薄大气高光弧（顶部）──
    arc_grad = QRadialGradient(cx, cy - radius * 0.55, radius * 0.65)
    arc_grad.setColorAt(0.0, QColor(200, 220, 250, 40))
    arc_grad.setColorAt(0.5, QColor(160, 190, 230, 15))
    arc_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(arc_grad); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius * 1.04, radius * 1.04)

    # ── 球面高光 ──
    highlight = QRadialGradient(cx - radius * 0.30, cy - radius * 0.30, radius * 0.35)
    highlight.setColorAt(0.0, QColor(255, 250, 240, 50))
    highlight.setColorAt(0.5, QColor(240, 220, 200, 20))
    highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(highlight); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 悬停 ──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        p.setPen(QPen(QColor(200, 180, 160, int(200 * hp)), 2.0))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 2, radius + 2)

    p.restore()

```
