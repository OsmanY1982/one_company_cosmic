# `core/shapes/saturn.py`

> 路径：`core/shapes/saturn.py` | 行数：138


---


```python
# -*- coding: utf-8 -*-
"""
土星 — 淡黄球体 + 标志性多层环 + 环缝
"""
import math, random
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import (
    QPainter, QRadialGradient, QLinearGradient,
    QColor, QPen, QBrush, QPainterPath
)


def paint(painter: QPainter, center: QPointF, radius: float,
          anim_t: float, hovered: bool, alpha: float):
    cx, cy = center.x(), center.y()
    p = painter
    p.save()
    if alpha < 1.0:
        p.setOpacity(alpha)

    ring_inner = radius * 1.25
    ring_outer = radius * 1.85
    ring_tilt = 0.45  # 环的倾斜比例

    # ── 光环（多层，带 Cassini 缝）──
    ring_bands = [
        (1.25, 1.33, QColor(210, 190, 150), 160),  # C环
        (1.33, 1.48, QColor(240, 220, 180), 200),  # B环
        (1.48, 1.52, QColor(255, 255, 255, 0), 0),       # Cassini缝
        (1.52, 1.63, QColor(230, 210, 170), 190),  # A环
        (1.63, 1.85, QColor(170, 150, 120), 100),  # F环
    ]
    for inner_f, outer_f, color, base_alpha in ring_bands:
        inner_r = radius * inner_f
        outer_r = radius * outer_f
        p.save()
        p.translate(cx, cy)
        p.scale(1.0, ring_tilt)
        if base_alpha == 0:
            pass  # Cassini缝不绘制
        else:
            for j in range(40):
                frac = j / 40.0
                r = inner_r + (outer_r - inner_r) * frac
                da = int(base_alpha * (0.6 + 0.4 * (1 - abs(frac - 0.5) * 2)))
                ring_color = QColor(
                    min(255, color.red() + int(20 * math.sin(frac * 12 + anim_t * 0.3))),
                    min(255, color.green() + int(15 * math.cos(frac * 10 + anim_t * 0.2))),
                    min(255, color.blue() + int(10 * math.sin(frac * 14))),
                    da
                )
                p.setBrush(ring_color); p.setPen(Qt.NoPen)
                p.drawEllipse(QPointF(0, 0), r, r * 0.015)
        p.restore()

    # ── 环粒子（光线散射）──
    ring_rng = random.Random(int(anim_t * 200) % 100000 + 777)
    p.save()
    p.translate(cx, cy)
    p.scale(1.0, ring_tilt)
    p.setPen(Qt.NoPen)
    for _ in range(40):
        ra = ring_rng.uniform(0, 2 * math.pi)
        rd = ring_rng.uniform(ring_inner, ring_outer)
        rx = math.cos(ra) * rd
        ry = math.sin(ra) * rd
        rs = ring_rng.uniform(0.4, 1.2)
        rg = QRadialGradient(rx, ry, rs * 2.0)
        ra2 = ring_rng.randint(30, 80)
        rg.setColorAt(0.0, QColor(255, 240, 200, ra2))
        rg.setColorAt(0.5, QColor(220, 200, 150, ra2 // 2))
        rg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(rg)
        p.drawEllipse(QPointF(rx, ry), rs * 2.0, rs * 2.0)
    p.restore()

    # ── 球体（淡黄渐变 + 带状条纹）──
    sphere = QRadialGradient(cx - radius * 0.1, cy - radius * 0.12, radius * 1.02)
    sphere.setColorAt(0.0, QColor(250, 240, 200))
    sphere.setColorAt(0.35, QColor(225, 210, 160))
    sphere.setColorAt(0.65, QColor(195, 175, 125))
    sphere.setColorAt(0.85, QColor(160, 140, 95))
    sphere.setColorAt(1.0, QColor(120, 100, 65))
    p.setBrush(sphere); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 水平云带 ──
    for band_i in range(10):
        band_y = cy - radius * 0.7 + radius * 1.4 * band_i / 9.0
        dx = radius * math.sqrt(max(0, 1 - ((band_y - cy) / radius) ** 2))
        if dx > 0:
            band_path = QPainterPath()
            band_path.moveTo(cx - dx, band_y)
            band_path.lineTo(cx + dx, band_y)
            band_alpha = int(30 + 25 * abs(math.sin(band_i * 1.5)))
            p.setPen(QPen(QColor(200, 180, 130, band_alpha), radius * 0.04))
            p.setBrush(Qt.NoBrush)
            p.drawPath(band_path)

    # ── 球体高光 ──
    highlight = QRadialGradient(cx - radius * 0.25, cy - radius * 0.28, radius * 0.32)
    highlight.setColorAt(0.0, QColor(255, 250, 230, 55))
    highlight.setColorAt(0.5, QColor(255, 240, 210, 18))
    highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(highlight); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 环在球体前方部分（后半环在球体后才可见，但这里简化全在后方，前面只画球体上的阴影）──
    # 环的阴影投射在球体上
    shadow_y_start = cy - radius * ring_tilt
    shadow_y_end = cy + radius * ring_tilt
    shadow_path = QPainterPath()
    shadow_path.moveTo(cx - radius, shadow_y_start)
    shadow_path.lineTo(cx + radius, shadow_y_start)
    shadow_path.lineTo(cx + radius, shadow_y_end)
    shadow_path.lineTo(cx - radius, shadow_y_end)
    shadow = QLinearGradient(cx, shadow_y_start, cx, shadow_y_end)
    shadow.setColorAt(0.0, QColor(255, 255, 255, 0))
    shadow.setColorAt(0.4, QColor(0, 0, 0, 20))
    shadow.setColorAt(0.6, QColor(0, 0, 0, 20))
    shadow.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(shadow); p.setPen(Qt.NoPen)
    # 裁剪到球体
    p.save()
    clip = QPainterPath()
    clip.addEllipse(center, radius, radius)
    p.setClipPath(clip)
    p.drawPath(shadow_path)
    p.restore()

    # ── 悬停 ──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        p.setPen(QPen(QColor(255, 220, 150, int(200 * hp)), 2.0))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 2, radius + 2)

    p.restore()

```
