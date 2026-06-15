# `core/shapes/fighter.py`

> 路径：`core/shapes/fighter.py` | 行数：222


---


```python
# -*- coding: utf-8 -*-
"""
星际战机形态 — 悬浮球变形
锐利三角机身 + 两侧短翼 + 引擎尾焰，灵活动感
适配悬浮球 ~40px 半径绘制区
"""
import math
import random
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QRadialGradient,
    QLinearGradient, QPainterPath,
)


def paint(p: QPainter, center: QPointF, radius: float, anim_t: float,
          hovered: bool = False, alpha: float = 1.0):
    """绘制星际战机形态"""
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.HighQualityAntialiasing)

    size = radius * 0.95
    w, h = size * 1.8, size * 1.3
    left = center.x() - w / 2
    top = center.y() - h / 2

    # 多层外辉光
    for glow_layer in range(4):
        glow_scale = 1.06 + glow_layer * 0.22
        glow_r = radius * glow_scale
        glow = QRadialGradient(center.x(), center.y(), glow_r)
        ga = max(1, 35 - glow_layer * 8)
        glow.setColorAt(0.0, QColor(255, 255, 255, 0))
        glow.setColorAt(0.25, QColor(200, 200, 255, ga // 2))
        glow.setColorAt(0.55, QColor(120, 140, 255, ga))
        glow.setColorAt(0.80, QColor(60, 80, 200, ga // 2))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(glow); p.setPen(Qt.NoPen)
        p.drawEllipse(center, glow_r, glow_r)

    _paint_body(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_wings(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_cockpit(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_engine(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_nav_lights(p, center, size, anim_t, alpha)

    if hovered:
        _paint_hover_glow(p, center, size, anim_t, alpha)


def _paint_body(p, left, top, w, h, size, center, anim_t, alpha):
    """三角机身"""
    cx = left + w / 2
    nose_y = top + h * 0.02
    body_bot_y = top + h * 0.78
    body_top_w = w * 0.22
    body_bot_w = w * 0.08

    path = QPainterPath()
    path.moveTo(cx, nose_y)
    path.lineTo(cx - body_top_w, top + h * 0.25)
    path.lineTo(cx - body_bot_w, body_bot_y)
    path.lineTo(cx + body_bot_w, body_bot_y)
    path.lineTo(cx + body_top_w, top + h * 0.25)
    path.closeSubpath()

    body_grad = QLinearGradient(cx, nose_y, cx, body_bot_y)
    body_grad.setColorAt(0.0, QColor(60, 65, 80, int(235 * alpha)))
    body_grad.setColorAt(0.2, QColor(45, 50, 65, int(245 * alpha)))
    body_grad.setColorAt(0.5, QColor(32, 36, 50, int(240 * alpha)))
    body_grad.setColorAt(1.0, QColor(22, 26, 38, int(230 * alpha)))
    p.setBrush(body_grad)
    p.setPen(QPen(QColor(90, 100, 120, int(150 * alpha)), 0.9))
    p.drawPath(path)

    # 机身装甲线
    line_y = top + h * 0.38
    p.setPen(QPen(QColor(140, 160, 190, int(60 * alpha)), 0.4))
    p.drawLine(QPointF(cx - body_top_w * 0.8, line_y), QPointF(cx + body_top_w * 0.8, line_y))


def _paint_wings(p, left, top, w, h, size, center, anim_t, alpha):
    """两侧短翼"""
    cx = left + w / 2
    wing_root_y = top + h * 0.42
    wing_y = top + h * 0.68
    wing_span = w * 0.38

    for sign in [-1, 1]:
        path = QPainterPath()
        path.moveTo(cx + sign * w * 0.08, wing_root_y)
        path.lineTo(cx + sign * wing_span, wing_y - h * 0.08)
        path.lineTo(cx + sign * wing_span, wing_y)
        path.lineTo(cx + sign * w * 0.06, wing_y + h * 0.04)
        path.closeSubpath()

        wing_grad = QLinearGradient(cx, wing_root_y, cx + sign * wing_span, wing_y)
        wing_grad.setColorAt(0.0, QColor(50, 55, 70, int(220 * alpha)))
        wing_grad.setColorAt(0.5, QColor(38, 42, 58, int(225 * alpha)))
        wing_grad.setColorAt(1.0, QColor(28, 32, 46, int(210 * alpha)))
        p.setBrush(wing_grad)
        p.setPen(QPen(QColor(80, 90, 110, int(130 * alpha)), 0.7))
        p.drawPath(path)

        # 翼尖武器挂载点
        tip_x = cx + sign * wing_span
        tip_y = wing_y - h * 0.04
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(200, 60, 30, int(140 * alpha)))
        p.drawEllipse(QPointF(tip_x, tip_y), size * 0.04, size * 0.04)
        p.setBrush(QColor(255, 120, 40, int(200 * alpha)))
        p.drawEllipse(QPointF(tip_x, tip_y), size * 0.02, size * 0.02)


def _paint_cockpit(p, left, top, w, h, size, center, anim_t, alpha):
    """驾驶舱"""
    cx = left + w / 2
    cp_w = w * 0.10
    cp_h = h * 0.14
    cp_x = cx - cp_w / 2
    cp_y = top + h * 0.12

    cockpit_grad = QRadialGradient(cx, cp_y + cp_h * 0.6, cp_w * 1.2)
    glow = 0.6 + 0.4 * abs(math.sin(anim_t * 2.2))
    cockpit_grad.setColorAt(0.0, QColor(180, 230, 255, int(200 * glow * alpha)))
    cockpit_grad.setColorAt(0.4, QColor(60, 160, 240, int(180 * glow * alpha)))
    cockpit_grad.setColorAt(0.8, QColor(20, 80, 160, int(100 * glow * alpha)))
    cockpit_grad.setColorAt(1.0, QColor(10, 30, 60, int(40 * alpha)))
    p.setBrush(cockpit_grad)
    p.setPen(QPen(QColor(120, 180, 220, int(140 * alpha)), 0.6))
    p.drawRoundedRect(QRectF(cp_x, cp_y, cp_w, cp_h), 3.0, 3.0)


def _paint_engine(p, left, top, w, h, size, center, anim_t, alpha):
    """引擎尾焰"""
    cx = center.x()
    engine_y = top + h * 0.80
    pulse = 0.55 + 0.45 * abs(math.sin(anim_t * 8.0))

    # 引擎光晕
    for i in range(2):
        eg_r = size * (0.08 + i * 0.06)
        eg = QRadialGradient(cx, engine_y, eg_r * 1.5)
        ea = int((80 - i * 25) * pulse * alpha)
        eg.setColorAt(0.0, QColor(100, 180, 255, ea))
        eg.setColorAt(0.5, QColor(40, 100, 220, ea // 2))
        eg.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen); p.setBrush(eg)
        p.drawEllipse(QPointF(cx, engine_y), eg_r * 1.5, eg_r * 2.0)

    # 主尾焰
    flame_h = size * 0.35 * pulse
    flame_w = size * 0.04
    flame_grad = QLinearGradient(cx, engine_y - flame_h, cx, engine_y + flame_h * 0.2)
    flame_grad.setColorAt(0.00, QColor(255, 255, 240, int(240 * alpha)))
    flame_grad.setColorAt(0.06, QColor(200, 230, 255, int(220 * alpha)))
    flame_grad.setColorAt(0.25, QColor(80, 170, 255, int(180 * alpha)))
    flame_grad.setColorAt(0.55, QColor(30, 90, 220, int(90 * alpha)))
    flame_grad.setColorAt(0.85, QColor(10, 40, 130, int(25 * alpha)))
    flame_grad.setColorAt(1.00, QColor(0, 5, 30, 0))
    p.setBrush(flame_grad); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(cx, engine_y), flame_w, flame_h)

    # 双引擎粒子
    for offset in [-1, 1]:
        ex = cx + offset * w * 0.04
        ey = engine_y
        for _ in range(4):
            px = ex + random.uniform(-flame_w * 0.9, flame_w * 0.9)
            py = ey + random.uniform(0, flame_h * 1.8)
            ps = random.uniform(0.3, 1.6)
            pa = int(random.uniform(30, 140) * alpha * pulse)
            p.setBrush(QColor(120, 200, 255, pa))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(px, py), ps, ps)


def _paint_nav_lights(p, center, size, anim_t, alpha):
    """红绿导航灯"""
    cx, cy = center.x(), center.y()
    for sign, base_color in [(-1, QColor(255, 30, 15)), (1, QColor(15, 255, 35))]:
        nx = cx + sign * size * 0.55
        ny = cy - size * 0.05
        flicker = 0.3 + 0.7 * abs(math.sin(anim_t * 5.0 + sign * 1.5))
        nav_g = QRadialGradient(nx, ny, size * 0.08)
        nav_g.setColorAt(0.0, QColor(base_color.red(), base_color.green(), base_color.blue(), int(200 * flicker * alpha)))
        nav_g.setColorAt(0.4, QColor(base_color.red(), base_color.green(), base_color.blue(), int(100 * flicker * alpha)))
        nav_g.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen); p.setBrush(nav_g)
        p.drawEllipse(QPointF(nx, ny), size * 0.08, size * 0.08)
        p.setBrush(QColor(255, 255, 255, int(180 * flicker * alpha)))
        p.drawEllipse(QPointF(nx, ny), size * 0.025, size * 0.025)


def _paint_hover_glow(p, center, size, anim_t, alpha):
    """Hover 增强光晕"""
    pulse = 0.7 + 0.3 * abs(math.sin(anim_t * 3.0))
    for i in range(3):
        ir = size * (0.88 + i * 0.10)
        iglow = QRadialGradient(center, ir)
        ga = int((65 - i * 18) * pulse)
        iglow.setColorAt(0.55, QColor(255, 255, 255, 0))
        iglow.setColorAt(0.76, QColor(80, 190, 255, ga // 2))
        iglow.setColorAt(0.90, QColor(0, 140, 255, ga))
        iglow.setColorAt(0.98, QColor(0, 70, 180, ga // 3))
        iglow.setColorAt(1.00, QColor(0, 0, 0, 0))
        p.setBrush(iglow); p.setPen(Qt.NoPen)
        p.drawEllipse(center, ir, ir)
    for i in range(3):
        outer_r = size * (1.0 + i * 0.26)
        glow = QRadialGradient(center, outer_r)
        ga = int((48 - i * 14) * pulse)
        glow.setColorAt(0.70, QColor(255, 255, 255, 0))
        glow.setColorAt(0.85, QColor(80, 190, 255, ga // 2))
        glow.setColorAt(0.94, QColor(0, 140, 255, ga))
        glow.setColorAt(1.00, QColor(0, 0, 0, 0))
        p.setBrush(glow); p.setPen(Qt.NoPen)
        p.drawEllipse(center, outer_r, outer_r)
    br = 0.55 + 0.45 * abs(math.sin(anim_t * 4.5))
    rpen = QPen(QColor(80, 190, 255, int(210 * pulse * alpha * br)), 2.2 + 1.2 * br)
    p.setPen(rpen); p.setBrush(Qt.NoBrush)
    p.drawEllipse(center, size * 0.95, size * 0.95)

```
