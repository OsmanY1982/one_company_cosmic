# `core/shapes/interceptor.py`

> 路径：`core/shapes/interceptor.py` | 行数：256


---


```python
# -*- coding: utf-8 -*-
"""
截击机形态 — 悬浮球变形
细长矛状机身 + 超大引擎占比 + 两侧稳定翼，极速风格
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
    """绘制截击机形态"""
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.HighQualityAntialiasing)

    size = radius * 0.95
    w, h = size * 1.4, size * 1.8
    left = center.x() - w / 2
    top = center.y() - h / 2

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
    _paint_stabilizers(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_cockpit(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_mega_engine(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_nav_lights(p, center, size, anim_t, alpha)

    if hovered:
        _paint_hover_glow(p, center, size, anim_t, alpha)


def _paint_body(p, left, top, w, h, size, center, anim_t, alpha):
    """矛状机身"""
    cx = left + w / 2
    nose_y = top + h * 0.02
    body_end_y = top + h * 0.62
    max_w = w * 0.12
    tail_w = w * 0.07

    path = QPainterPath()
    # 尖头
    path.moveTo(cx, nose_y)
    # 右侧膨胀
    path.cubicTo(cx + w * 0.04, nose_y + h * 0.03,
                 cx + max_w, nose_y + h * 0.20,
                 cx + max_w, body_end_y - h * 0.18)
    path.cubicTo(cx + max_w * 0.90, body_end_y - h * 0.06,
                 cx + tail_w, body_end_y - h * 0.02,
                 cx + tail_w * 0.70, body_end_y)
    # 底部
    path.lineTo(cx - tail_w * 0.70, body_end_y)
    # 左侧
    path.cubicTo(cx - tail_w, body_end_y - h * 0.02,
                 cx - max_w * 0.90, body_end_y - h * 0.06,
                 cx - max_w, body_end_y - h * 0.18)
    path.cubicTo(cx - max_w, nose_y + h * 0.20,
                 cx - w * 0.04, nose_y + h * 0.03,
                 cx, nose_y)

    body_grad = QLinearGradient(cx, nose_y, cx, body_end_y)
    body_grad.setColorAt(0.0, QColor(70, 75, 90, int(240 * alpha)))
    body_grad.setColorAt(0.2, QColor(50, 55, 72, int(245 * alpha)))
    body_grad.setColorAt(0.5, QColor(36, 40, 56, int(242 * alpha)))
    body_grad.setColorAt(1.0, QColor(24, 28, 42, int(235 * alpha)))
    p.setBrush(body_grad)
    p.setPen(QPen(QColor(90, 100, 125, int(150 * alpha)), 0.8))
    p.drawPath(path)

    # 速度线
    for i in range(5):
        ly = nose_y + h * 0.10 + i * h * 0.10
        lw = w * 0.03 + i * w * 0.008
        p.setPen(QPen(QColor(140, 180, 220, int(45 * alpha)), 0.3))
        p.drawLine(QPointF(cx - lw, ly), QPointF(cx + lw, ly))


def _paint_stabilizers(p, left, top, w, h, size, center, anim_t, alpha):
    """两侧稳定翼"""
    cx = left + w / 2
    wing_root_y = top + h * 0.35
    wing_tip_y = top + h * 0.52
    wing_span = w * 0.32

    for sign in [-1, 1]:
        path = QPainterPath()
        path.moveTo(cx + sign * w * 0.04, wing_root_y)
        path.lineTo(cx + sign * wing_span, wing_tip_y - h * 0.03)
        path.lineTo(cx + sign * wing_span, wing_tip_y)
        path.lineTo(cx + sign * w * 0.03, wing_tip_y + h * 0.02)
        path.closeSubpath()

        wing_grad = QLinearGradient(cx, wing_root_y, cx + sign * wing_span, wing_tip_y)
        wing_grad.setColorAt(0.0, QColor(55, 60, 78, int(220 * alpha)))
        wing_grad.setColorAt(0.5, QColor(40, 45, 62, int(225 * alpha)))
        wing_grad.setColorAt(1.0, QColor(30, 34, 50, int(210 * alpha)))
        p.setBrush(wing_grad)
        p.setPen(QPen(QColor(80, 90, 115, int(130 * alpha)), 0.6))
        p.drawPath(path)

        # 翼尖能量指示灯
        tip_x = cx + sign * wing_span
        tip_y = wing_tip_y - h * 0.015
        glow_pulse = 0.4 + 0.6 * abs(math.sin(anim_t * 7.0 + sign))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(80, 200, 255, int(180 * glow_pulse * alpha)))
        p.drawEllipse(QPointF(tip_x, tip_y), size * 0.04, size * 0.04)
        p.setBrush(QColor(255, 255, 255, int(220 * glow_pulse * alpha)))
        p.drawEllipse(QPointF(tip_x, tip_y), size * 0.018, size * 0.018)


def _paint_cockpit(p, left, top, w, h, size, center, anim_t, alpha):
    """驾驶舱"""
    cx = left + w / 2
    cp_w = w * 0.10
    cp_h = h * 0.11
    cp_x = cx - cp_w / 2
    cp_y = top + h * 0.04

    cockpit_grad = QRadialGradient(cx, cp_y + cp_h * 0.5, cp_w)
    glow = 0.5 + 0.5 * abs(math.sin(anim_t * 2.5))
    cockpit_grad.setColorAt(0.0, QColor(160, 220, 255, int(210 * glow * alpha)))
    cockpit_grad.setColorAt(0.3, QColor(60, 150, 240, int(190 * glow * alpha)))
    cockpit_grad.setColorAt(0.7, QColor(20, 80, 160, int(120 * alpha)))
    cockpit_grad.setColorAt(1.0, QColor(10, 25, 55, int(40 * alpha)))
    p.setBrush(cockpit_grad)
    p.setPen(QPen(QColor(100, 170, 220, int(140 * alpha)), 0.5))
    p.drawRoundedRect(QRectF(cp_x, cp_y, cp_w, cp_h), 2.5, 2.5)


def _paint_mega_engine(p, left, top, w, h, size, center, anim_t, alpha):
    """超大引擎"""
    cx = center.x()
    engine_y = top + h * 0.65
    pulse = 0.5 + 0.5 * abs(math.sin(anim_t * 9.0))

    # 引擎主体（超大）
    engine_rim_r = size * 0.14
    eng_grad = QRadialGradient(cx, engine_y, engine_rim_r)
    eng_grad.setColorAt(0.0, QColor(50, 55, 72, int(220 * alpha)))
    eng_grad.setColorAt(0.5, QColor(35, 40, 58, int(210 * alpha)))
    eng_grad.setColorAt(1.0, QColor(18, 22, 38, int(150 * alpha)))
    p.setBrush(eng_grad)
    p.setPen(QPen(QColor(100, 110, 140, int(140 * alpha)), 1.0))
    p.drawEllipse(QPointF(cx, engine_y), engine_rim_r, engine_rim_r * 0.75)

    # 引擎核心
    core_r = size * 0.06
    core_grad = QRadialGradient(cx, engine_y, core_r)
    core_pulse = 0.7 + 0.3 * abs(math.sin(anim_t * 10.0))
    core_grad.setColorAt(0.0, QColor(255, 255, 255, int(240 * core_pulse * alpha)))
    core_grad.setColorAt(0.3, QColor(180, 220, 255, int(200 * alpha)))
    core_grad.setColorAt(0.7, QColor(40, 120, 240, int(100 * alpha)))
    core_grad.setColorAt(1.0, QColor(0, 20, 80, 0))
    p.setBrush(core_grad); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(cx, engine_y), core_r, core_r * 0.6)

    # 巨型尾焰光晕
    for fl in range(4):
        fl_r = size * (0.08 + fl * 0.10)
        fl_grad = QRadialGradient(cx, engine_y + size * 0.30, fl_r * 1.5)
        fa = int((90 - fl * 20) * pulse * alpha)
        fl_grad.setColorAt(0.0, QColor(255, 200, 50, fa))
        fl_grad.setColorAt(0.4, QColor(255, 100, 20, fa // 2))
        fl_grad.setColorAt(0.7, QColor(30, 80, 200, fa // 3))
        fl_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen); p.setBrush(fl_grad)
        p.drawEllipse(QPointF(cx, engine_y + size * 0.30), fl_r * 1.5, fl_r * 2.5)

    # 主尾焰
    flame_h = size * 0.55 * pulse
    flame_w = size * 0.06
    fgrad = QLinearGradient(cx, engine_y - flame_h, cx, engine_y + flame_h * 0.2)
    fgrad.setColorAt(0.00, QColor(255, 255, 240, int(255 * alpha)))
    fgrad.setColorAt(0.04, QColor(210, 240, 255, int(230 * alpha)))
    fgrad.setColorAt(0.15, QColor(100, 190, 255, int(200 * alpha)))
    fgrad.setColorAt(0.35, QColor(40, 110, 240, int(140 * alpha)))
    fgrad.setColorAt(0.60, QColor(15, 50, 180, int(60 * alpha)))
    fgrad.setColorAt(0.85, QColor(5, 20, 100, int(20 * alpha)))
    fgrad.setColorAt(1.00, QColor(0, 5, 30, 0))
    p.setBrush(fgrad); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(cx, engine_y), flame_w, flame_h)

    # 大量粒子喷射
    for _ in range(12):
        px = cx + random.uniform(-flame_w * 2.0, flame_w * 2.0)
        py = engine_y + random.uniform(0, flame_h * 2.5)
        ps = random.uniform(0.3, 2.2)
        pa = int(random.uniform(25, 160) * alpha * pulse)
        p.setBrush(QColor(140, 210, 255, pa))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(px, py), ps, ps)


def _paint_nav_lights(p, center, size, anim_t, alpha):
    """红绿导航灯"""
    cx, cy = center.x(), center.y()
    for sign, base_color in [(-1, QColor(255, 30, 15)), (1, QColor(15, 255, 35))]:
        nx = cx + sign * size * 0.35
        ny = cy - size * 0.10
        flicker = 0.3 + 0.7 * abs(math.sin(anim_t * 5.5 + sign * 1.2))
        nav_g = QRadialGradient(nx, ny, size * 0.07)
        nav_g.setColorAt(0.0, QColor(base_color.red(), base_color.green(), base_color.blue(), int(200 * flicker * alpha)))
        nav_g.setColorAt(0.4, QColor(base_color.red(), base_color.green(), base_color.blue(), int(100 * flicker * alpha)))
        nav_g.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen); p.setBrush(nav_g)
        p.drawEllipse(QPointF(nx, ny), size * 0.07, size * 0.07)
        p.setBrush(QColor(255, 255, 255, int(180 * flicker * alpha)))
        p.drawEllipse(QPointF(nx, ny), size * 0.02, size * 0.02)


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
