# `core/shapes/crystal_alien.py`

> 路径：`core/shapes/crystal_alien.py` | 行数：164


---


```python
# -*- coding: utf-8 -*-
"""
水晶生命体 — 多面体晶体折射 + 彩虹闪光 + 晶格缓慢生长
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

    s = radius / 55.0  # 基准

    # ── 浮动 ──
    float_y = math.sin(anim_t * 1.4) * radius * 0.05
    float_x = math.cos(anim_t * 1.1) * radius * 0.03
    body_cx = cx + float_x
    body_cy = cy + float_y

    # ── 背景辉光（冰蓝紫）──
    glow = QRadialGradient(body_cx, body_cy, radius * 1.05)
    glow.setColorAt(0.0, QColor(160, 200, 255, 25))
    glow.setColorAt(0.5, QColor(100, 130, 220, 10))
    glow.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(glow); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), radius * 1.05, radius * 1.05)

    # ── 核心晶体簇（6个主晶面 + 中心核）──
    # 晶格缓慢生长（半径微幅膨胀收缩）
    grow = 1.0 + 0.04 * math.sin(anim_t * 0.35) + 0.02 * math.sin(anim_t * 0.65)
    main_r = radius * 0.52 * grow

    # 中心晶核（亮白内芯）
    core = QRadialGradient(body_cx, body_cy, main_r * 0.30)
    core.setColorAt(0.0, QColor(255, 255, 255, 230))
    core.setColorAt(0.30, QColor(230, 240, 255, 200))
    core.setColorAt(0.60, QColor(160, 200, 255, 140))
    core.setColorAt(1.0, QColor(80, 140, 240, 40))
    p.setBrush(core); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), main_r * 0.30, main_r * 0.30)

    # 6个外延晶面（六边形排列）
    crystal_rng = random.Random(42)
    for i in range(6):
        angle = i * math.pi / 3 + anim_t * 0.06  # 极缓慢自转
        facet_cx = body_cx + math.cos(angle) * main_r * 0.55
        facet_cy = body_cy + math.sin(angle) * main_r * 0.55
        facet_w = main_r * crystal_rng.uniform(0.30, 0.45)
        facet_h = main_r * crystal_rng.uniform(0.38, 0.55)
        face_angle = angle + crystal_rng.uniform(-0.3, 0.3)

        p.save()
        p.translate(facet_cx, facet_cy)
        p.rotate(face_angle * 180 / math.pi)

        # 晶面主体（棱形）
        facet_path = QPainterPath()
        facet_path.moveTo(0, -facet_h)
        facet_path.lineTo(facet_w, 0)
        facet_path.lineTo(0, facet_h)
        facet_path.lineTo(-facet_w, 0)
        facet_path.closeSubpath()

        # 水晶折射渐变（蓝→紫→透明）
        hue_shift = i * 60
        facet_grad = QLinearGradient(-facet_w * 0.5, -facet_h * 0.5,
                                      facet_w * 0.5, facet_h * 0.5)
        facet_grad.setColorAt(0.0, QColor(180, 200 + hue_shift % 55, 255, 160))
        facet_grad.setColorAt(0.35, QColor(140, 180 + hue_shift % 75, 255, 120))
        facet_grad.setColorAt(0.65, QColor(100, 120 + hue_shift % 80, 240, 90))
        facet_grad.setColorAt(1.0, QColor(60, 80 + hue_shift % 60, 200, 30))
        p.setBrush(facet_grad)
        p.setPen(QPen(QColor(200, 220, 255, 100), 1.0 * s))
        p.drawPath(facet_path)

        # 晶面内部微棱（折射分裂线）
        for j in range(2):
            split_grad = QLinearGradient(-facet_w * 0.3, 0, facet_w * 0.3, 0)
            split_grad.setColorAt(0.0, QColor(255, 255, 255, 0))
            split_grad.setColorAt(0.5, QColor(255, 255, 255, 40))
            split_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setPen(QPen(QBrush(split_grad), 0.6 * s))
            p.drawLine(QPointF(-facet_w * 0.35, (j - 0.5) * facet_h * 0.35),
                       QPointF(facet_w * 0.35, (j - 0.5) * facet_h * 0.35))

        p.restore()

    # ── 小型副晶（散落在主体周围）──
    sub_rng = random.Random(73)
    for _ in range(8):
        sa = sub_rng.uniform(0, 2 * math.pi)
        sd = main_r * sub_rng.uniform(0.70, 1.15)
        sx = body_cx + math.cos(sa) * sd
        sy = body_cy + math.sin(sa) * sd
        ss = main_r * sub_rng.uniform(0.06, 0.16)
        sub_grad = QRadialGradient(sx - ss * 0.2, sy - ss * 0.2, ss)
        sh = sub_rng.randint(0, 5) * 60
        sub_grad.setColorAt(0.0, QColor(200, 200 + sh % 55, 255, 180))
        sub_grad.setColorAt(0.5, QColor(140, 160 + sh % 75, 240, 100))
        sub_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(sub_grad); p.setPen(QPen(QColor(180, 200, 255, 60), 0.5 * s))
        p.drawEllipse(QPointF(sx, sy), ss, ss)

    # ── 彩虹闪光（周期性四射，模拟晶体内部色散）──
    rainbow_phase = (anim_t * 0.6) % 8.0
    if rainbow_phase < 0.8:
        flash_alpha = int(200 * (1.0 - rainbow_phase / 0.8))
        for ray_i in range(4):
            ray_angle = ray_i * math.pi / 2 + anim_t * 0.15
            ray_len = main_r * (1.8 + ray_i * 0.12)
            ray_path = QPainterPath()
            ray_path.moveTo(body_cx, body_cy)
            perp = ray_angle + math.pi / 2
            bw = main_r * 0.08
            ray_path.lineTo(body_cx + math.cos(ray_angle) * ray_len + math.cos(perp) * bw,
                           body_cy + math.sin(ray_angle) * ray_len + math.sin(perp) * bw)
            ray_path.lineTo(body_cx + math.cos(ray_angle) * ray_len - math.cos(perp) * bw,
                           body_cy + math.sin(ray_angle) * ray_len - math.sin(perp) * bw)
            ray_path.closeSubpath()
            hue = (ray_i * 90 + int(anim_t * 30)) % 360
            flash_grad = QRadialGradient(body_cx, body_cy, ray_len)
            flash_grad.setColorAt(0.0, QColor.fromHsv(hue, 80, 255, flash_alpha))
            flash_grad.setColorAt(0.4, QColor.fromHsv(hue, 100, 240, flash_alpha // 2))
            flash_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setBrush(flash_grad); p.setPen(Qt.NoPen)
            p.drawPath(ray_path)

    # ── 外层晶格结构光环 ──
    ring_r = radius * 0.85
    ring_pulse = 0.6 + 0.4 * abs(math.sin(anim_t * 0.5))
    ring_grad = QRadialGradient(body_cx, body_cy, ring_r + radius * 0.05)
    ring_grad.setColorAt(0.0, QColor(255, 255, 255, 0))
    ring_grad.setColorAt(0.75, QColor(255, 255, 255, 0))
    ring_grad.setColorAt(0.85, QColor(140, 200, 255, int(60 * ring_pulse)))
    ring_grad.setColorAt(0.92, QColor(100, 160, 240, int(35 * ring_pulse)))
    ring_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(ring_grad); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), ring_r + radius * 0.05, ring_r + radius * 0.05)

    # ── 高光 ──
    spec = QRadialGradient(body_cx - main_r * 0.25, body_cy - main_r * 0.28, main_r * 0.30)
    spec.setColorAt(0.0, QColor(255, 255, 255, 70))
    spec.setColorAt(0.5, QColor(220, 240, 255, 25))
    spec.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(spec); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), main_r, main_r)

    # ── 悬停 ──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        p.setPen(QPen(QColor(180, 220, 255, int(200 * hp)), 2.0 * s))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 2, radius + 2)

    p.restore()

```
