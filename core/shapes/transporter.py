# -*- coding: utf-8 -*-
"""
运输舰形态 — 悬浮球变形
货柜箱体结构 + 驾驶舱在前 + 多引擎
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
    """绘制运输舰形态"""
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.HighQualityAntialiasing)

    size = radius * 0.95
    w, h = size * 2.8, size * 1.6
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

    _paint_cab(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_cargo_bays(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_frame(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_engines(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_nav_lights(p, center, size, anim_t, alpha)

    if hovered:
        _paint_hover_glow(p, center, size, anim_t, alpha)


def _paint_cab(p, left, top, w, h, size, center, anim_t, alpha):
    """驾驶舱（前部）"""
    cx = left + w / 2
    cab_w = w * 0.16
    cab_h = h * 0.28
    cab_x = cx - cab_w / 2
    cab_y = top + h * 0.06

    # 驾驶舱主体
    cab_grad = QLinearGradient(cab_x, cab_y, cab_x + cab_w, cab_y)
    cab_grad.setColorAt(0.0, QColor(55, 60, 78, int(225 * alpha)))
    cab_grad.setColorAt(0.5, QColor(85, 90, 108, int(230 * alpha)))
    cab_grad.setColorAt(1.0, QColor(50, 55, 72, int(215 * alpha)))
    p.setBrush(cab_grad)
    p.setPen(QPen(QColor(100, 110, 135, int(145 * alpha)), 0.9))
    p.drawRoundedRect(QRectF(cab_x, cab_y, cab_w, cab_h), 4, 4)

    # 驾驶舱舷窗（大面积）
    win_w = cab_w * 0.55
    win_h = cab_h * 0.40
    win_x = cab_x + (cab_w - win_w) / 2
    win_y = cab_y + cab_h * 0.08
    win_glow = 0.5 + 0.5 * abs(math.sin(anim_t * 2.2))
    win_grad = QRadialGradient(cx, win_y + win_h * 0.5, win_w * 1.5)
    win_grad.setColorAt(0.0, QColor(180, 230, 255, int(220 * win_glow * alpha)))
    win_grad.setColorAt(0.4, QColor(80, 180, 240, int(200 * win_glow * alpha)))
    win_grad.setColorAt(0.8, QColor(20, 80, 160, int(100 * alpha)))
    win_grad.setColorAt(1.0, QColor(10, 30, 60, 0))
    p.setBrush(win_grad)
    p.setPen(QPen(QColor(120, 180, 220, int(130 * alpha)), 0.4))
    p.drawRoundedRect(QRectF(win_x, win_y, win_w, win_h), 2, 2)

    # 通讯天线
    antenna_x = cab_x + cab_w * 0.6
    antenna_y = cab_y - h * 0.06
    p.setPen(QPen(QColor(100, 120, 150, int(110 * alpha)), 0.6))
    p.drawLine(QPointF(antenna_x, cab_y), QPointF(antenna_x, antenna_y))
    p.setBrush(QColor(100, 200, 255, int(150 * alpha)))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(antenna_x, antenna_y), size * 0.025, size * 0.025)


def _paint_cargo_bays(p, left, top, w, h, size, center, anim_t, alpha):
    """货柜箱体结构"""
    cx = left + w / 2
    # 箱体定位在驾驶舱后方
    bay_start_x = cx - w * 0.08
    bay_y = top + h * 0.40
    bay_w = w * 0.16
    bay_h = h * 0.50

    for i in range(3):
        bx = bay_start_x + i * (bay_w + w * 0.02)
        by = bay_y

        # 货柜主体
        container_grad = QLinearGradient(bx, by, bx + bay_w, by)
        hue_offset = i * 15
        container_grad.setColorAt(0.0, QColor(55 + hue_offset, 60 + hue_offset, 80, int(230 * alpha)))
        container_grad.setColorAt(0.5, QColor(75 + hue_offset, 80 + hue_offset, 100, int(235 * alpha)))
        container_grad.setColorAt(1.0, QColor(50 + hue_offset, 55 + hue_offset, 72, int(220 * alpha)))
        p.setBrush(container_grad)
        p.setPen(QPen(QColor(95, 105, 130, int(140 * alpha)), 0.7))
        p.drawRoundedRect(QRectF(bx, by, bay_w, bay_h), 3, 3)

        # 货柜内部线条（箱体棱线）
        for lj in range(2):
            ly = by + bay_h * 0.33 + lj * bay_h * 0.33
            p.setPen(QPen(QColor(130, 150, 180, int(45 * alpha)), 0.3))
            p.drawLine(QPointF(bx + bay_w * 0.10, ly), QPointF(bx + bay_w * 0.90, ly))

        # 货柜垂直棱线
        for lj in range(1):
            lx = bx + bay_w * (0.35 + lj * 0.30)
            p.setPen(QPen(QColor(130, 150, 180, int(40 * alpha)), 0.3))
            p.drawLine(QPointF(lx, by + bay_h * 0.08), QPointF(lx, by + bay_h * 0.92))

        # 货柜指示灯
        cargo_light = 0.4 + 0.6 * abs(math.sin(anim_t * 3.0 + i * 0.9))
        for side in [-1, 1]:
            clx = bx + bay_w * 0.5 + side * bay_w * 0.35
            cly = by + bay_h * 0.1
            cl_grad = QRadialGradient(clx, cly, size * 0.025)
            cl_grad.setColorAt(0.0, QColor(255, 200, 50, int(150 * cargo_light * alpha)))
            cl_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(cl_grad)
            p.drawEllipse(QPointF(clx, cly), size * 0.025, size * 0.025)


def _paint_frame(p, left, top, w, h, size, center, anim_t, alpha):
    """船体框架连接结构"""
    cx = left + w / 2
    # 顶部连接梁
    frame_y1 = top + h * 0.08
    frame_y2 = top + h * 0.92
    frame_w = w * 0.55

    # 上框架
    upper_grad = QLinearGradient(cx - frame_w / 2, frame_y1, cx + frame_w / 2, frame_y1)
    upper_grad.setColorAt(0.0, QColor(50, 55, 70, 0))
    upper_grad.setColorAt(0.2, QColor(60, 65, 85, int(180 * alpha)))
    upper_grad.setColorAt(0.8, QColor(60, 65, 85, int(180 * alpha)))
    upper_grad.setColorAt(1.0, QColor(50, 55, 70, 0))
    p.setBrush(upper_grad)
    p.setPen(Qt.NoPen)
    p.drawRect(QRectF(cx - frame_w / 2, frame_y1, frame_w, h * 0.04))

    # 下框架
    lower_grad = QLinearGradient(cx - frame_w / 2, frame_y2, cx + frame_w / 2, frame_y2)
    lower_grad.setColorAt(0.0, QColor(40, 45, 60, 0))
    lower_grad.setColorAt(0.2, QColor(55, 60, 78, int(175 * alpha)))
    lower_grad.setColorAt(0.8, QColor(55, 60, 78, int(175 * alpha)))
    lower_grad.setColorAt(1.0, QColor(40, 45, 60, 0))
    p.setBrush(lower_grad)
    p.setPen(Qt.NoPen)
    p.drawRect(QRectF(cx - frame_w / 2, frame_y2, frame_w, h * 0.04))


def _paint_engines(p, left, top, w, h, size, center, anim_t, alpha):
    """多引擎（4个）"""
    engine_y = top + h * 0.94
    pulse = 0.6 + 0.4 * abs(math.sin(anim_t * 5.0))
    positions = [center.x() + d * w * 0.13 for d in [-1.5, -0.5, 0.5, 1.5]]

    for i, ex in enumerate(positions):
        # 引擎外壳
        eng_grad = QRadialGradient(ex, engine_y, size * 0.07)
        eng_grad.setColorAt(0.0, QColor(55, 60, 78, int(200 * alpha)))
        eng_grad.setColorAt(1.0, QColor(20, 25, 40, 0))
        p.setPen(Qt.NoPen); p.setBrush(eng_grad)
        p.drawEllipse(QPointF(ex, engine_y), size * 0.07, size * 0.045)

        # 尾焰光晕
        for fl in range(3):
            fl_r = size * (0.05 + fl * 0.06)
            fl_grad = QRadialGradient(ex, engine_y + size * 0.18, fl_r * 1.4)
            fa = int((70 - fl * 20) * pulse * alpha)
            fl_grad.setColorAt(0.0, QColor(255, 200, 50, fa))
            fl_grad.setColorAt(0.5, QColor(255, 100, 20, fa // 2))
            fl_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(fl_grad)
            p.drawEllipse(QPointF(ex, engine_y + size * 0.18), fl_r * 1.4, fl_r * 2.2)

        # 尾焰主体
        flame_h = size * 0.28 * pulse * (0.8 + i * 0.12)
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

        # 粒子
        for _ in range(4):
            px = ex + random.uniform(-flame_w * 1.2, flame_w * 1.2)
            py = engine_y + random.uniform(0, flame_h * 2.0)
            ps = random.uniform(0.3, 1.6)
            pa = int(random.uniform(30, 140) * alpha * pulse)
            p.setBrush(QColor(120, 200, 255, pa))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(px, py), ps, ps)


def _paint_nav_lights(p, center, size, anim_t, alpha):
    """红绿导航灯 + 尾灯"""
    cx, cy = center.x(), center.y()
    for sign, base_color in [(-1, QColor(255, 30, 15)), (1, QColor(15, 255, 35))]:
        nx = cx + sign * size * 0.85
        ny = cy - size * 0.10
        flicker = 0.3 + 0.7 * abs(math.sin(anim_t * 4.0 + sign * 1.3))
        nav_g = QRadialGradient(nx, ny, size * 0.08)
        nav_g.setColorAt(0.0, QColor(base_color.red(), base_color.green(), base_color.blue(), int(200 * flicker * alpha)))
        nav_g.setColorAt(0.4, QColor(base_color.red(), base_color.green(), base_color.blue(), int(100 * flicker * alpha)))
        nav_g.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen); p.setBrush(nav_g)
        p.drawEllipse(QPointF(nx, ny), size * 0.08, size * 0.08)
        p.setBrush(QColor(255, 255, 255, int(180 * flicker * alpha)))
        p.drawEllipse(QPointF(nx, ny), size * 0.022, size * 0.022)
    strobe_y = cy + size * 0.45
    strobe_flicker = abs(math.sin(anim_t * 5.5))
    for sx in [cx - size * 0.28, cx + size * 0.28]:
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
