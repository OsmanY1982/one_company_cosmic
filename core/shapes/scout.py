# -*- coding: utf-8 -*-
"""
侦察舰形态 — 悬浮球变形
圆盘形主体 + 多条天线/传感器阵列 + 微弱引擎
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
    """绘制侦察舰形态"""
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.HighQualityAntialiasing)

    size = radius * 0.95
    w, h = size * 1.6, size * 1.6
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

    _paint_disk(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_sensors(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_core(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_engine(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_nav_lights(p, center, size, anim_t, alpha)

    if hovered:
        _paint_hover_glow(p, center, size, anim_t, alpha)


def _paint_disk(p, left, top, w, h, size, center, anim_t, alpha):
    """圆盘形主体"""
    cx = center.x()
    cy = center.y()
    disk_rx = w * 0.38
    disk_ry = h * 0.30

    # 圆盘主体
    disk_grad = QRadialGradient(cx, cy - disk_ry * 0.1, disk_rx)
    disk_grad.setColorAt(0.0, QColor(80, 90, 110, int(230 * alpha)))
    disk_grad.setColorAt(0.4, QColor(55, 62, 80, int(240 * alpha)))
    disk_grad.setColorAt(0.75, QColor(38, 45, 62, int(235 * alpha)))
    disk_grad.setColorAt(1.0, QColor(25, 32, 48, int(220 * alpha)))
    p.setBrush(disk_grad)
    p.setPen(QPen(QColor(100, 115, 140, int(160 * alpha)), 1.0))
    p.drawEllipse(QPointF(cx, cy - disk_ry * 0.1), disk_rx, disk_ry)

    # 圆盘边框（科技感环）
    ring_grad = QRadialGradient(cx, cy - disk_ry * 0.1, disk_rx * 1.05)
    ring_grad.setColorAt(0.82, QColor(255, 255, 255, 0))
    ring_grad.setColorAt(0.88, QColor(100, 180, 240, int(90 * alpha)))
    ring_grad.setColorAt(0.94, QColor(40, 120, 200, int(60 * alpha)))
    ring_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(ring_grad)
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(cx, cy - disk_ry * 0.1), disk_rx * 1.05, disk_ry * 1.08)

    # 圆盘分割线
    for i in range(6):
        angle = i * math.pi / 3 + anim_t * 0.3
        r1 = disk_rx * 0.25
        r2 = disk_rx * 0.90
        x1 = cx + math.cos(angle) * r1
        y1 = cy - disk_ry * 0.1 + math.sin(angle) * r1 * (disk_ry / disk_rx)
        x2 = cx + math.cos(angle) * r2
        y2 = cy - disk_ry * 0.1 + math.sin(angle) * r2 * (disk_ry / disk_rx)
        p.setPen(QPen(QColor(150, 180, 210, int(45 * alpha)), 0.3))
        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    # 内环
    p.setPen(QPen(QColor(130, 170, 210, int(70 * alpha)), 0.4))
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(QPointF(cx, cy - disk_ry * 0.1), disk_rx * 0.28, disk_ry * 0.25)


def _paint_sensors(p, left, top, w, h, size, center, anim_t, alpha):
    """天线/传感器阵列"""
    cx = center.x()
    cy = center.y()

    antennas = [
        (0, -1, 0.42),       # 上方
        (0.35, -0.85, 0.36), # 右上方
        (-0.35, -0.85, 0.36),# 左上方
        (0.7, -0.5, 0.28),   # 右侧
        (-0.7, -0.5, 0.28),  # 左侧
    ]

    for dx, dy, length_f in antennas:
        ax = cx + dx * size * 0.55
        ay = cy + dy * size * 0.45
        antenna_len = size * length_f
        antenna_end_x = ax + dx * antenna_len * 0.5
        antenna_end_y = ay - antenna_len

        # 天线杆
        p.setPen(QPen(QColor(120, 140, 170, int(100 * alpha)), 0.6))
        p.drawLine(QPointF(ax, ay), QPointF(antenna_end_x, antenna_end_y))

        # 传感器头
        sensor_pulse = 0.4 + 0.6 * abs(math.sin(anim_t * 3.5 + dx * 2.0 + dy))
        sensor_grad = QRadialGradient(antenna_end_x, antenna_end_y, size * 0.04)
        sensor_grad.setColorAt(0.0, QColor(100, 200, 255, int(200 * sensor_pulse * alpha)))
        sensor_grad.setColorAt(0.5, QColor(40, 140, 220, int(120 * sensor_pulse * alpha)))
        sensor_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen); p.setBrush(sensor_grad)
        p.drawEllipse(QPointF(antenna_end_x, antenna_end_y), size * 0.04, size * 0.04)
        p.setBrush(QColor(255, 255, 255, int(200 * sensor_pulse * alpha)))
        p.drawEllipse(QPointF(antenna_end_x, antenna_end_y), size * 0.015, size * 0.015)

    # 信号脉冲环（从中心扩散）
    cycle = anim_t % 3.0
    for i in range(2):
        t = (cycle + i * 1.5) % 3.0
        progress = t / 3.0
        pr = size * 0.15 + progress * size * 0.55
        pa = int(60 * alpha * (1.0 - progress))
        if pa > 0:
            p.setPen(QPen(QColor(80, 200, 255, pa), 0.5 - progress * 0.3))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(cx, cy), pr, pr * 0.7)


def _paint_core(p, left, top, w, h, size, center, anim_t, alpha):
    """核心处理器"""
    cx = center.x()
    cy = center.y()
    core_r = size * 0.08

    core_pulse = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
    core_grad = QRadialGradient(cx, cy - size * 0.06, core_r)
    core_grad.setColorAt(0.0, QColor(180, 230, 255, int(220 * core_pulse * alpha)))
    core_grad.setColorAt(0.3, QColor(80, 180, 240, int(200 * alpha)))
    core_grad.setColorAt(0.7, QColor(30, 100, 180, int(120 * alpha)))
    core_grad.setColorAt(1.0, QColor(10, 30, 60, 0))
    p.setBrush(core_grad)
    p.setPen(QPen(QColor(100, 180, 230, int(150 * alpha)), 0.5))
    p.drawEllipse(QPointF(cx, cy - size * 0.06), core_r, core_r * 0.75)


def _paint_engine(p, left, top, w, h, size, center, anim_t, alpha):
    """微弱引擎（3个小型）"""
    cx = center.x()
    engine_y = center.y() + size * 0.28
    pulse = 0.5 + 0.5 * abs(math.sin(anim_t * 4.5))

    for offset in [-1, 0, 1]:
        ex = cx + offset * size * 0.10
        ey = engine_y

        # 引擎光晕（微弱）
        eg_r = size * 0.06
        eg = QRadialGradient(ex, ey + size * 0.06, eg_r)
        ea = int(35 * pulse * alpha)
        eg.setColorAt(0.0, QColor(80, 160, 240, ea))
        eg.setColorAt(0.5, QColor(30, 80, 180, ea // 2))
        eg.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen); p.setBrush(eg)
        p.drawEllipse(QPointF(ex, ey + size * 0.06), eg_r, eg_r * 1.5)

        # 小尾焰
        flame_h = size * 0.12 * pulse
        flame_w = size * 0.025
        fgrad = QLinearGradient(ex, ey - flame_h, ex, ey + flame_h * 0.2)
        fgrad.setColorAt(0.00, QColor(220, 240, 255, int(180 * alpha)))
        fgrad.setColorAt(0.15, QColor(120, 200, 255, int(140 * alpha)))
        fgrad.setColorAt(0.50, QColor(30, 100, 220, int(60 * alpha)))
        fgrad.setColorAt(0.85, QColor(5, 30, 100, int(15 * alpha)))
        fgrad.setColorAt(1.00, QColor(0, 5, 30, 0))
        p.setBrush(fgrad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, ey), flame_w, flame_h)


def _paint_nav_lights(p, center, size, anim_t, alpha):
    """红绿导航灯"""
    cx, cy = center.x(), center.y()
    for sign, base_color in [(-1, QColor(255, 30, 15)), (1, QColor(15, 255, 35))]:
        nx = cx + sign * size * 0.45
        ny = cy - size * 0.05
        flicker = 0.3 + 0.7 * abs(math.sin(anim_t * 4.0 + sign * 1.2))
        nav_g = QRadialGradient(nx, ny, size * 0.07)
        nav_g.setColorAt(0.0, QColor(base_color.red(), base_color.green(), base_color.blue(), int(190 * flicker * alpha)))
        nav_g.setColorAt(0.4, QColor(base_color.red(), base_color.green(), base_color.blue(), int(90 * flicker * alpha)))
        nav_g.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen); p.setBrush(nav_g)
        p.drawEllipse(QPointF(nx, ny), size * 0.07, size * 0.07)
        p.setBrush(QColor(255, 255, 255, int(170 * flicker * alpha)))
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
