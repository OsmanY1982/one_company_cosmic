# `core/shapes/destroyer.py`

> 路径：`core/shapes/destroyer.py` | 行数：277


---


```python
# -*- coding: utf-8 -*-
"""
重型驱逐舰形态 — 悬浮球变形
楔形船体前宽后窄 + 中央巨型炮塔 + 两侧副炮 + 引擎阵列
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
    """绘制重型驱逐舰形态"""
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.HighQualityAntialiasing)

    size = radius * 0.95
    w, h = size * 2.8, size * 1.5
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
    _paint_main_turret(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_secondary_guns(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_bridge(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_engines(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_nav_lights(p, center, size, anim_t, alpha)

    if hovered:
        _paint_hover_glow(p, center, size, anim_t, alpha)


def _paint_hull(p, left, top, w, h, size, center, anim_t, alpha):
    """楔形船体"""
    cx = left + w / 2
    bow_w = w * 0.26
    stern_w = w * 0.06
    hull_top = top + h * 0.08
    hull_bot = top + h * 0.88

    path = QPainterPath()
    path.moveTo(cx - bow_w, hull_top)
    path.lineTo(cx + bow_w, hull_top)
    path.lineTo(cx + stern_w, hull_bot)
    path.lineTo(cx - stern_w, hull_bot)
    path.closeSubpath()

    hull_grad = QLinearGradient(cx, hull_top, cx, hull_bot)
    hull_grad.setColorAt(0.0, QColor(55, 60, 75, int(240 * alpha)))
    hull_grad.setColorAt(0.3, QColor(38, 42, 58, int(245 * alpha)))
    hull_grad.setColorAt(0.6, QColor(28, 32, 48, int(240 * alpha)))
    hull_grad.setColorAt(1.0, QColor(18, 22, 34, int(235 * alpha)))
    p.setBrush(hull_grad)
    p.setPen(QPen(QColor(90, 100, 125, int(150 * alpha)), 1.0))
    p.drawPath(path)

    # 装甲带
    belt_y1 = hull_top + h * 0.50
    belt_y2 = hull_top + h * 0.60
    belt_grad = QLinearGradient(cx, belt_y1, cx, belt_y2)
    belt_grad.setColorAt(0.0, QColor(70, 75, 90, int(180 * alpha)))
    belt_grad.setColorAt(1.0, QColor(40, 45, 60, int(180 * alpha)))
    p.setBrush(belt_grad)
    p.setPen(Qt.NoPen)
    p.drawRect(QRectF(cx - w * 0.22, belt_y1, w * 0.44, belt_y2 - belt_y1))

    # 船体装甲线
    for i in range(4):
        ly = hull_top + h * 0.20 + i * h * 0.16
        lw_at_y = bow_w - (bow_w - stern_w) * ((ly - hull_top) / (hull_bot - hull_top))
        p.setPen(QPen(QColor(140, 160, 190, int(50 * alpha)), 0.35))
        p.drawLine(QPointF(cx - lw_at_y * 0.85, ly), QPointF(cx + lw_at_y * 0.85, ly))


def _paint_main_turret(p, left, top, w, h, size, center, anim_t, alpha):
    """中央巨型炮塔"""
    cx = left + w / 2
    turret_cx = cx
    turret_cy = top + h * 0.18
    turret_r = size * 0.15

    # 炮塔基座
    base_grad = QRadialGradient(turret_cx, turret_cy, turret_r)
    base_grad.setColorAt(0.0, QColor(65, 70, 85, int(230 * alpha)))
    base_grad.setColorAt(0.6, QColor(45, 50, 65, int(220 * alpha)))
    base_grad.setColorAt(1.0, QColor(30, 35, 50, int(180 * alpha)))
    p.setBrush(base_grad)
    p.setPen(QPen(QColor(100, 110, 135, int(140 * alpha)), 0.8))
    p.drawEllipse(QPointF(turret_cx, turret_cy), turret_r, turret_r * 0.8)

    # 主炮管（双联装）
    barrel_angle = anim_t * 0.15
    for offset in [-1, 1]:
        bx = turret_cx + offset * turret_r * 0.35
        by = turret_cy - turret_r * 0.5
        b_len = turret_r * 1.8
        b_end_x = bx + math.sin(barrel_angle + offset * 0.05) * b_len * 0.15
        b_end_y = by - b_len
        p.setPen(QPen(QColor(80, 90, 110, int(180 * alpha)), turret_r * 0.18))
        p.drawLine(QPointF(bx, by), QPointF(b_end_x, b_end_y))

        # 炮口能量蓄积
        charge_pulse = 0.4 + 0.6 * abs(math.sin(anim_t * 4.5 + offset))
        charge_grad = QRadialGradient(b_end_x, b_end_y, turret_r * 0.2)
        charge_grad.setColorAt(0.0, QColor(255, 100, 20, int(200 * charge_pulse * alpha)))
        charge_grad.setColorAt(0.5, QColor(255, 200, 50, int(80 * charge_pulse * alpha)))
        charge_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen); p.setBrush(charge_grad)
        p.drawEllipse(QPointF(b_end_x, b_end_y), turret_r * 0.20, turret_r * 0.20)


def _paint_secondary_guns(p, left, top, w, h, size, center, anim_t, alpha):
    """两侧副炮"""
    cx = left + w / 2
    for side in [-1, 1]:
        for j in range(2):
            gx = cx + side * w * 0.18 * (1 + j * 0.6)
            gy = top + h * 0.42 + j * h * 0.15
            # 炮台
            gun_grad = QRadialGradient(gx, gy, size * 0.06)
            gun_grad.setColorAt(0.0, QColor(75, 80, 95, int(210 * alpha)))
            gun_grad.setColorAt(1.0, QColor(35, 40, 55, int(150 * alpha)))
            p.setBrush(gun_grad)
            p.setPen(QPen(QColor(100, 110, 130, int(120 * alpha)), 0.5))
            p.drawEllipse(QPointF(gx, gy), size * 0.06, size * 0.06)

            # 炮管
            gun_angle = -0.2 + j * 0.1
            barrel_len = size * 0.12
            barrel_end_x = gx + side * barrel_len * 0.7
            barrel_end_y = gy - barrel_len * 0.6 * (1 - j * 0.3)
            p.setPen(QPen(QColor(90, 100, 120, int(160 * alpha)), size * 0.025))
            p.drawLine(QPointF(gx, gy), QPointF(barrel_end_x, barrel_end_y))

            # 炮口光点
            p.setBrush(QColor(255, 150, 30, int(140 * alpha)))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(barrel_end_x, barrel_end_y), size * 0.02, size * 0.02)


def _paint_bridge(p, left, top, w, h, size, center, anim_t, alpha):
    """舰桥塔"""
    cx = left + w / 2
    bw = w * 0.10
    bh = h * 0.22
    bx = cx - bw / 2
    by = top + h * 0.02

    bridge_grad = QLinearGradient(bx, by, bx + bw, by)
    bridge_grad.setColorAt(0.0, QColor(50, 55, 70, int(210 * alpha)))
    bridge_grad.setColorAt(0.5, QColor(80, 85, 100, int(215 * alpha)))
    bridge_grad.setColorAt(1.0, QColor(45, 50, 65, int(200 * alpha)))
    p.setBrush(bridge_grad)
    p.setPen(QPen(QColor(100, 110, 130, int(130 * alpha)), 0.7))
    p.drawRoundedRect(QRectF(bx, by, bw, bh), 3, 3)

    # 舰桥舷窗
    for col in range(2):
        for row in range(2):
            wx = bx + bw * 0.12 + col * bw * 0.42
            wy = by + bh * 0.15 + row * bh * 0.36
            glow = 0.5 + 0.5 * abs(math.sin(anim_t * 2.6 + col + row * 0.8))
            p.setBrush(QColor(100, 200, 255, int(160 * alpha * glow)))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(QRectF(wx, wy, bw * 0.30, bh * 0.22), 1.5, 1.5)


def _paint_engines(p, left, top, w, h, size, center, anim_t, alpha):
    """引擎阵列（四引擎）"""
    engine_y = top + h * 0.91
    pulse = 0.6 + 0.4 * abs(math.sin(anim_t * 5.5))
    positions = [center.x() + d * w * 0.13 for d in [-1.5, -0.5, 0.5, 1.5]]

    for i, ex in enumerate(positions):
        # 引擎本体
        eng_grad = QRadialGradient(ex, engine_y, size * 0.07)
        eng_grad.setColorAt(0.0, QColor(50, 55, 70, int(200 * alpha)))
        eng_grad.setColorAt(1.0, QColor(15, 20, 35, 0))
        p.setPen(Qt.NoPen); p.setBrush(eng_grad)
        p.drawEllipse(QPointF(ex, engine_y), size * 0.07, size * 0.04)

        # 尾焰
        flame_h = size * 0.25 * pulse * (0.8 + i * 0.12)
        flame_w = size * 0.03
        fgrad = QLinearGradient(ex, engine_y - flame_h, ex, engine_y + flame_h * 0.2)
        fgrad.setColorAt(0.00, QColor(255, 255, 240, int(240 * alpha)))
        fgrad.setColorAt(0.06, QColor(200, 230, 255, int(220 * alpha)))
        fgrad.setColorAt(0.25, QColor(80, 170, 255, int(180 * alpha)))
        fgrad.setColorAt(0.55, QColor(30, 90, 220, int(90 * alpha)))
        fgrad.setColorAt(0.85, QColor(10, 40, 130, int(25 * alpha)))
        fgrad.setColorAt(1.00, QColor(0, 5, 30, 0))
        p.setBrush(fgrad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, engine_y), flame_w, flame_h)

        # 粒子
        for _ in range(3):
            px = ex + random.uniform(-flame_w * 1.2, flame_w * 1.2)
            py = engine_y + random.uniform(0, flame_h * 2.0)
            ps = random.uniform(0.3, 1.5)
            pa = int(random.uniform(30, 140) * alpha * pulse)
            p.setBrush(QColor(100, 190, 255, pa))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(px, py), ps, ps)


def _paint_nav_lights(p, center, size, anim_t, alpha):
    """红绿导航灯 + 尾灯"""
    cx, cy = center.x(), center.y()
    for sign, base_color in [(-1, QColor(255, 30, 15)), (1, QColor(15, 255, 35))]:
        nx = cx + sign * size * 0.82
        ny = cy - size * 0.12
        flicker = 0.3 + 0.7 * abs(math.sin(anim_t * 4.5 + sign * 1.3))
        nav_g = QRadialGradient(nx, ny, size * 0.08)
        nav_g.setColorAt(0.0, QColor(base_color.red(), base_color.green(), base_color.blue(), int(200 * flicker * alpha)))
        nav_g.setColorAt(0.4, QColor(base_color.red(), base_color.green(), base_color.blue(), int(100 * flicker * alpha)))
        nav_g.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen); p.setBrush(nav_g)
        p.drawEllipse(QPointF(nx, ny), size * 0.08, size * 0.08)
        p.setBrush(QColor(255, 255, 255, int(180 * flicker * alpha)))
        p.drawEllipse(QPointF(nx, ny), size * 0.022, size * 0.022)
    strobe_y = cy + size * 0.50
    strobe_flicker = abs(math.sin(anim_t * 6.0))
    for sx in [cx - size * 0.30, cx + size * 0.30]:
        sg = QRadialGradient(sx, strobe_y, size * 0.06)
        sg.setColorAt(0.0, QColor(255, 255, 255, int(200 * strobe_flicker * alpha)))
        sg.setColorAt(0.5, QColor(200, 220, 255, int(100 * strobe_flicker * alpha)))
        sg.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen); p.setBrush(sg)
        p.drawEllipse(QPointF(sx, strobe_y), size * 0.06, size * 0.06)


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
