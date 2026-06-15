# -*- coding: utf-8 -*-
"""
无畏舰形态 — 悬浮球变形
矩形厚重装甲 + 多层甲板 + 大量炮塔阵列 + 巨大引擎
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
    """绘制无畏舰形态"""
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.HighQualityAntialiasing)

    size = radius * 0.95
    w, h = size * 3.0, size * 1.8
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
    _paint_decks(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_turrets(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_bridge(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_engines(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_nav_lights(p, center, size, anim_t, alpha)

    if hovered:
        _paint_hover_glow(p, center, size, anim_t, alpha)


def _paint_hull(p, left, top, w, h, size, center, anim_t, alpha):
    """矩形厚重装甲船体"""
    cx = left + w / 2
    hull_left = left + w * 0.06
    hull_right = left + w * 0.94
    hull_top = top + h * 0.02
    hull_bot = top + h * 0.88

    path = QPainterPath()
    path.moveTo(left + w * 0.12, hull_top)
    path.lineTo(left + w * 0.88, hull_top)
    path.lineTo(left + w * 0.84, hull_bot)
    path.lineTo(left + w * 0.16, hull_bot)
    path.closeSubpath()

    hull_grad = QLinearGradient(cx, hull_top, cx, hull_bot)
    hull_grad.setColorAt(0.0, QColor(48, 52, 66, int(245 * alpha)))
    hull_grad.setColorAt(0.2, QColor(38, 42, 56, int(248 * alpha)))
    hull_grad.setColorAt(0.5, QColor(30, 34, 48, int(245 * alpha)))
    hull_grad.setColorAt(0.8, QColor(24, 28, 42, int(240 * alpha)))
    hull_grad.setColorAt(1.0, QColor(18, 22, 34, int(235 * alpha)))
    p.setBrush(hull_grad)
    p.setPen(QPen(QColor(85, 95, 120, int(160 * alpha)), 1.2))
    p.drawPath(path)

    # 船体装甲板线
    for i in range(6):
        ly = hull_top + h * 0.12 + i * h * 0.12
        lw = w * 0.36 - i * w * 0.015
        p.setPen(QPen(QColor(140, 160, 190, int(55 * alpha)), 0.4))
        p.drawLine(QPointF(cx - lw, ly), QPointF(cx + lw, ly))

    # 侧面厚重装甲带
    for side in [-1, 1]:
        belt_x = cx + side * w * 0.34
        belt_rect = QRectF(belt_x - w * 0.03, hull_top + h * 0.10, w * 0.06, h * 0.65)
        belt_grad = QLinearGradient(belt_x - w * 0.03, 0, belt_x + w * 0.03, 0)
        belt_grad.setColorAt(0.0, QColor(60, 65, 80, int(200 * alpha)))
        belt_grad.setColorAt(0.5, QColor(45, 50, 65, int(210 * alpha)))
        belt_grad.setColorAt(1.0, QColor(60, 65, 80, int(200 * alpha)))
        p.setBrush(belt_grad)
        p.setPen(Qt.NoPen)
        p.drawRect(belt_rect)


def _paint_decks(p, left, top, w, h, size, center, anim_t, alpha):
    """多层甲板结构"""
    cx = left + w / 2
    deck_gap = h * 0.16
    for layer in range(4):
        dy = top + h * 0.06 + layer * deck_gap
        dw = w * 0.34 - layer * w * 0.015
        deck_grad = QLinearGradient(cx, dy, cx, dy + h * 0.08)
        da = int(180 * alpha * (0.8 - layer * 0.12))
        deck_grad.setColorAt(0.0, QColor(60, 65, 80, da))
        deck_grad.setColorAt(0.5, QColor(50, 55, 70, da))
        deck_grad.setColorAt(1.0, QColor(35, 40, 55, da))
        p.setBrush(deck_grad)
        p.setPen(QPen(QColor(100, 110, 135, int(80 * alpha)), 0.3))
        p.drawRect(QRectF(cx - dw, dy, dw * 2, h * 0.08))


def _paint_turrets(p, left, top, w, h, size, center, anim_t, alpha):
    """炮塔阵列"""
    cx = left + w / 2
    turret_positions = [
        (-1, 0.22), (1, 0.22),
        (-1, 0.40), (1, 0.40),
        (0, 0.55),
        (-0.6, 0.68), (0.6, 0.68),
    ]

    for j, (side_factor, y_factor) in enumerate(turret_positions):
        tx = cx + side_factor * w * 0.15
        ty = top + h * y_factor
        tr = size * 0.055

        # 炮塔基座
        turret_grad = QRadialGradient(tx, ty, tr)
        turret_grad.setColorAt(0.0, QColor(70, 75, 90, int(220 * alpha)))
        turret_grad.setColorAt(0.6, QColor(50, 55, 70, int(200 * alpha)))
        turret_grad.setColorAt(1.0, QColor(30, 35, 50, int(150 * alpha)))
        p.setBrush(turret_grad)
        p.setPen(QPen(QColor(100, 110, 135, int(120 * alpha)), 0.5))
        p.drawEllipse(QPointF(tx, ty), tr, tr * 0.7)

        # 炮管
        barrel_angle = -0.3 + j * 0.08
        barrel_len = tr * 1.5
        barrel_end_x = tx + math.sin(barrel_angle) * barrel_len * 0.3
        barrel_end_y = ty - barrel_len * 0.8
        p.setPen(QPen(QColor(85, 95, 115, int(160 * alpha)), tr * 0.25))
        p.drawLine(QPointF(tx, ty), QPointF(barrel_end_x, barrel_end_y))

        # 炮口光点（部分炮塔）
        if (j % 2 == 0):
            charge_pulse = 0.3 + 0.7 * abs(math.sin(anim_t * 5.5 + j))
            p.setBrush(QColor(255, 140, 20, int(160 * charge_pulse * alpha)))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(barrel_end_x, barrel_end_y), tr * 0.25, tr * 0.25)


def _paint_bridge(p, left, top, w, h, size, center, anim_t, alpha):
    """指挥舰桥"""
    cx = left + w / 2
    bw = w * 0.12
    bh = h * 0.20
    bx = cx - bw / 2
    by = top + h * 0.00

    # 舰桥主体
    bridge_grad = QLinearGradient(bx, by, bx + bw, by)
    bridge_grad.setColorAt(0.0, QColor(45, 50, 65, int(220 * alpha)))
    bridge_grad.setColorAt(0.5, QColor(85, 90, 105, int(225 * alpha)))
    bridge_grad.setColorAt(1.0, QColor(40, 45, 60, int(210 * alpha)))
    p.setBrush(bridge_grad)
    p.setPen(QPen(QColor(105, 115, 135, int(140 * alpha)), 0.8))
    p.drawRoundedRect(QRectF(bx, by, bw, bh), 4, 4)

    # 舷窗
    for col in range(3):
        for row in range(2):
            wx = bx + bw * 0.12 + col * bw * 0.32
            wy = by + bh * 0.18 + row * bh * 0.36
            glow = 0.4 + 0.6 * abs(math.sin(anim_t * 2.4 + col * 0.6 + row))
            p.setBrush(QColor(90, 200, 255, int(170 * alpha * glow)))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(QRectF(wx, wy, bw * 0.18, bh * 0.22), 1.5, 1.5)

    # 天线塔
    mast_x = cx
    mast_y = by - h * 0.04
    p.setPen(QPen(QColor(100, 110, 130, int(120 * alpha)), 0.8))
    p.drawLine(QPointF(cx, by), QPointF(mast_x, mast_y))

    # 雷达旋转
    radar_angle = anim_t * 2.5
    radar_r = size * 0.08
    p.setPen(QPen(QColor(0, 200, 255, int(140 * alpha)), 0.6))
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(QPointF(mast_x, mast_y), radar_r, radar_r * 0.25)
    p.drawLine(QPointF(mast_x, mast_y),
               QPointF(mast_x + math.cos(radar_angle) * radar_r,
                       mast_y + math.sin(radar_angle) * radar_r * 0.25))


def _paint_engines(p, left, top, w, h, size, center, anim_t, alpha):
    """巨大引擎阵列（6联装）"""
    engine_y = top + h * 0.91
    pulse = 0.55 + 0.45 * abs(math.sin(anim_t * 5.0))
    positions = [center.x() + d * w * 0.11 for d in range(-2, 3)]

    for i, ex in enumerate(positions):
        # 引擎外壳
        eng_grad = QRadialGradient(ex, engine_y, size * 0.08)
        eng_grad.setColorAt(0.0, QColor(55, 60, 75, int(210 * alpha)))
        eng_grad.setColorAt(1.0, QColor(20, 25, 40, 0))
        p.setPen(Qt.NoPen); p.setBrush(eng_grad)
        p.drawEllipse(QPointF(ex, engine_y), size * 0.08, size * 0.05)

        # 尾焰光晕
        for fl in range(3):
            fl_r = size * (0.06 + fl * 0.07)
            fl_grad = QRadialGradient(ex, engine_y + size * 0.22, fl_r * 1.4)
            fa = int((80 - fl * 22) * pulse * alpha)
            fl_grad.setColorAt(0.0, QColor(255, 200, 50, fa))
            fl_grad.setColorAt(0.5, QColor(255, 100, 20, fa // 2))
            fl_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(fl_grad)
            p.drawEllipse(QPointF(ex, engine_y + size * 0.22), fl_r * 1.4, fl_r * 2.3)

        # 尾焰主体
        flame_h = size * 0.30 * pulse * (0.85 + i * 0.08)
        flame_w = size * 0.04
        fgrad = QLinearGradient(ex, engine_y - flame_h, ex, engine_y + flame_h * 0.2)
        fgrad.setColorAt(0.00, QColor(255, 255, 240, int(245 * alpha)))
        fgrad.setColorAt(0.06, QColor(200, 230, 255, int(220 * alpha)))
        fgrad.setColorAt(0.25, QColor(80, 170, 255, int(180 * alpha)))
        fgrad.setColorAt(0.55, QColor(30, 90, 220, int(90 * alpha)))
        fgrad.setColorAt(0.85, QColor(10, 40, 130, int(25 * alpha)))
        fgrad.setColorAt(1.00, QColor(0, 5, 30, 0))
        p.setBrush(fgrad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, engine_y), flame_w, flame_h)

        # 粒子喷射
        for _ in range(5):
            px = ex + random.uniform(-flame_w * 1.4, flame_w * 1.4)
            py = engine_y + random.uniform(0, flame_h * 2.2)
            ps = random.uniform(0.3, 1.8)
            pa = int(random.uniform(30, 150) * alpha * pulse)
            p.setBrush(QColor(100, 190, 255, pa))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(px, py), ps, ps)


def _paint_nav_lights(p, center, size, anim_t, alpha):
    """红绿导航灯 + 尾灯"""
    cx, cy = center.x(), center.y()
    for sign, base_color in [(-1, QColor(255, 30, 15)), (1, QColor(15, 255, 35))]:
        nx = cx + sign * size * 0.90
        ny = cy - size * 0.10
        flicker = 0.3 + 0.7 * abs(math.sin(anim_t * 4.0 + sign * 1.4))
        nav_g = QRadialGradient(nx, ny, size * 0.08)
        nav_g.setColorAt(0.0, QColor(base_color.red(), base_color.green(), base_color.blue(), int(200 * flicker * alpha)))
        nav_g.setColorAt(0.4, QColor(base_color.red(), base_color.green(), base_color.blue(), int(100 * flicker * alpha)))
        nav_g.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen); p.setBrush(nav_g)
        p.drawEllipse(QPointF(nx, ny), size * 0.08, size * 0.08)
        p.setBrush(QColor(255, 255, 255, int(180 * flicker * alpha)))
        p.drawEllipse(QPointF(nx, ny), size * 0.022, size * 0.022)
    strobe_y = cy + size * 0.50
    strobe_flicker = abs(math.sin(anim_t * 5.5))
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
