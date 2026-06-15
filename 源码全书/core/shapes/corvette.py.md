# `core/shapes/corvette.py`

> 路径：`core/shapes/corvette.py` | 行数：239


---


```python
# -*- coding: utf-8 -*-
"""
轻型护卫舰形态 — 悬浮球变形
流线梭形船体 + 顶部小型舰桥 + 双引擎
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
    """绘制轻型护卫舰形态"""
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.HighQualityAntialiasing)

    size = radius * 0.95
    w, h = size * 2.2, size * 1.2
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

    _paint_hull(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_bridge(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_armor_lines(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_engines(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_nav_lights(p, center, size, anim_t, alpha)

    if hovered:
        _paint_hover_glow(p, center, size, anim_t, alpha)


def _paint_hull(p, left, top, w, h, size, center, anim_t, alpha):
    """梭形船体"""
    cx = left + w / 2
    hull_top = top + h * 0.15
    hull_bot = top + h * 0.90
    nose_w = w * 0.04
    mid_w = w * 0.16
    tail_w = w * 0.06

    path = QPainterPath()
    path.moveTo(cx, hull_top)
    # 右侧曲线
    path.cubicTo(cx + nose_w * 1.5, hull_top + h * 0.05,
                 cx + mid_w, hull_top + h * 0.40,
                 cx + mid_w * 0.90, hull_bot - h * 0.22)
    path.cubicTo(cx + mid_w * 0.50, hull_bot - h * 0.08,
                 cx + tail_w, hull_bot - h * 0.02,
                 cx + tail_w * 0.80, hull_bot)
    # 底部
    path.lineTo(cx - tail_w * 0.80, hull_bot)
    # 左侧曲线
    path.cubicTo(cx - tail_w, hull_bot - h * 0.02,
                 cx - mid_w * 0.50, hull_bot - h * 0.08,
                 cx - mid_w * 0.90, hull_bot - h * 0.22)
    path.cubicTo(cx - mid_w, hull_top + h * 0.40,
                 cx - nose_w * 1.5, hull_top + h * 0.05,
                 cx, hull_top)

    hull_grad = QLinearGradient(cx, hull_top, cx, hull_bot)
    hull_grad.setColorAt(0.0, QColor(45, 50, 65, int(240 * alpha)))
    hull_grad.setColorAt(0.3, QColor(35, 38, 52, int(245 * alpha)))
    hull_grad.setColorAt(0.6, QColor(28, 32, 46, int(240 * alpha)))
    hull_grad.setColorAt(1.0, QColor(20, 24, 36, int(235 * alpha)))
    p.setBrush(hull_grad)
    p.setPen(QPen(QColor(85, 95, 115, int(145 * alpha)), 0.8))
    p.drawPath(path)


def _paint_bridge(p, left, top, w, h, size, center, anim_t, alpha):
    """小型舰桥"""
    cx = left + w / 2
    bw = w * 0.10
    bh = h * 0.20
    bx = cx - bw / 2
    by = top + h * 0.06

    bridge_grad = QLinearGradient(bx, by, bx + bw, by)
    bridge_grad.setColorAt(0.0, QColor(55, 60, 75, int(220 * alpha)))
    bridge_grad.setColorAt(0.5, QColor(75, 80, 95, int(225 * alpha)))
    bridge_grad.setColorAt(1.0, QColor(50, 55, 70, int(210 * alpha)))
    p.setBrush(bridge_grad)
    p.setPen(QPen(QColor(100, 110, 130, int(135 * alpha)), 0.7))
    p.drawRoundedRect(QRectF(bx, by, bw, bh), 3.0, 3.0)

    # 舰桥舷窗
    for col in range(3):
        wx = bx + bw * 0.12 + col * bw * 0.28
        wy = by + bh * 0.30
        glow = 0.5 + 0.5 * abs(math.sin(anim_t * 2.8 + col * 0.7))
        p.setBrush(QColor(100, 200, 255, int(170 * alpha * glow)))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(wx, wy, bw * 0.16, bh * 0.30), 1.5, 1.5)

    # 传感器阵列
    sx = bx + bw * 0.3
    sy = by - h * 0.06
    p.setPen(QPen(QColor(60, 180, 240, int(100 * alpha)), 0.5))
    p.drawLine(QPointF(sx, sy), QPointF(sx, by))
    for j in range(3):
        slab_x = sx - size * 0.06 + j * size * 0.06
        p.setBrush(QColor(60, 200, 255, int(130 * alpha)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(slab_x, sy), size * 0.022, size * 0.022)


def _paint_armor_lines(p, left, top, w, h, size, center, anim_t, alpha):
    """船体装甲线"""
    cx = left + w / 2
    mid_y = top + h * 0.55
    for offset_y in [h * 0.08, h * 0.16, h * 0.24]:
        ly = mid_y + offset_y
        lw = w * 0.06 + offset_y * 1.8
        p.setPen(QPen(QColor(140, 160, 190, int(55 * alpha)), 0.4))
        p.drawLine(QPointF(cx - lw, ly), QPointF(cx + lw, ly))


def _paint_engines(p, left, top, w, h, size, center, anim_t, alpha):
    """双引擎尾焰"""
    engine_y = top + h * 0.92
    pulse = 0.6 + 0.4 * abs(math.sin(anim_t * 6.5))

    for offset in [w * 0.08, -w * 0.08]:
        ex = center.x() + offset
        # 引擎本体
        engine_grad = QRadialGradient(ex, engine_y, size * 0.08)
        engine_grad.setColorAt(0.0, QColor(60, 70, 90, int(200 * alpha)))
        engine_grad.setColorAt(1.0, QColor(20, 25, 40, 0))
        p.setPen(Qt.NoPen); p.setBrush(engine_grad)
        p.drawEllipse(QPointF(ex, engine_y), size * 0.08, size * 0.05)

        # 尾焰光晕
        for fl in range(3):
            fl_r = size * (0.05 + fl * 0.06)
            fl_grad = QRadialGradient(ex, engine_y + size * 0.18, fl_r * 1.4)
            fa = int((70 - fl * 20) * pulse * alpha)
            fl_grad.setColorAt(0.0, QColor(255, 200, 50, fa))
            fl_grad.setColorAt(0.5, QColor(255, 100, 20, fa // 2))
            fl_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setBrush(fl_grad); p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(ex, engine_y + size * 0.18), fl_r * 1.4, fl_r * 2.2)

        # 尾焰主体
        flame_h = size * 0.28 * pulse
        flame_w = size * 0.035
        fgrad = QLinearGradient(ex, engine_y - flame_h, ex, engine_y + flame_h * 0.2)
        fgrad.setColorAt(0.00, QColor(255, 255, 240, int(240 * alpha)))
        fgrad.setColorAt(0.06, QColor(200, 230, 255, int(220 * alpha)))
        fgrad.setColorAt(0.25, QColor(80, 170, 255, int(180 * alpha)))
        fgrad.setColorAt(0.55, QColor(30, 90, 220, int(90 * alpha)))
        fgrad.setColorAt(0.85, QColor(10, 40, 130, int(25 * alpha)))
        fgrad.setColorAt(1.00, QColor(0, 5, 30, 0))
        p.setBrush(fgrad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, engine_y), flame_w, flame_h)

        for _ in range(5):
            px = ex + random.uniform(-flame_w * 1.2, flame_w * 1.2)
            py = engine_y + random.uniform(0, flame_h * 2.0)
            ps = random.uniform(0.3, 1.8)
            pa = int(random.uniform(30, 150) * alpha * pulse)
            p.setBrush(QColor(120, 200, 255, pa))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(px, py), ps, ps)


def _paint_nav_lights(p, center, size, anim_t, alpha):
    """红绿导航灯"""
    cx, cy = center.x(), center.y()
    for sign, base_color in [(-1, QColor(255, 30, 15)), (1, QColor(15, 255, 35))]:
        nx = cx + sign * size * 0.65
        ny = cy - size * 0.10
        flicker = 0.3 + 0.7 * abs(math.sin(anim_t * 4.5 + sign * 1.3))
        nav_g = QRadialGradient(nx, ny, size * 0.09)
        nav_g.setColorAt(0.0, QColor(base_color.red(), base_color.green(), base_color.blue(), int(200 * flicker * alpha)))
        nav_g.setColorAt(0.4, QColor(base_color.red(), base_color.green(), base_color.blue(), int(100 * flicker * alpha)))
        nav_g.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen); p.setBrush(nav_g)
        p.drawEllipse(QPointF(nx, ny), size * 0.09, size * 0.09)
        p.setBrush(QColor(255, 255, 255, int(180 * flicker * alpha)))
        p.drawEllipse(QPointF(nx, ny), size * 0.025, size * 0.025)

    # 尾部白色频闪灯
    strobe_y = cy + size * 0.55
    strobe_flicker = abs(math.sin(anim_t * 6.0))
    for sx in [cx - size * 0.25, cx + size * 0.25]:
        sg = QRadialGradient(sx, strobe_y, size * 0.07)
        sg.setColorAt(0.0, QColor(255, 255, 255, int(200 * strobe_flicker * alpha)))
        sg.setColorAt(0.5, QColor(200, 220, 255, int(100 * strobe_flicker * alpha)))
        sg.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen); p.setBrush(sg)
        p.drawEllipse(QPointF(sx, strobe_y), size * 0.07, size * 0.07)


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
