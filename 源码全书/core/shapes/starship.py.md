# `core/shapes/starship.py`

> 路径：`core/shapes/starship.py` | 行数：304


---


```python
# -*- coding: utf-8 -*-
"""
星舰形态 — 悬浮球第 73 变
微型航空母舰：甲板 + 舰岛 + 引擎尾焰 + 跑道 + 雷达脉冲
适配悬浮球 ~40px 半径绘制区
"""
import math
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QRadialGradient,
    QLinearGradient, QPainterPath, QFont,
)


def paint(p: QPainter, center: QPointF, radius: float, anim_t: float,
          hovered: bool = False, alpha: float = 1.0):
    """绘制星舰变形形态"""
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.HighQualityAntialiasing)

    size = radius * 0.95
    w, h = size * 2.6, size * 1.55
    left = center.x() - w / 2
    top = center.y() - h / 2

    # ── 多层外辉光（增强质感）──
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

    _paint_engine_glow(p, left, top, w, h, size, anim_t, alpha)
    _paint_hull(p, left, top, w, h, size, anim_t, alpha)
    _paint_deck(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_island(p, left, top, w, h, size, anim_t, alpha)
    _paint_runway(p, left, top, w, h, size, anim_t, alpha)
    _paint_radar(p, left, top, w, h, size, anim_t, alpha)
    _paint_engine_flames(p, left, top, w, h, size, center, anim_t, alpha)
    _paint_nav_lights(p, center, size, anim_t, alpha)

    if hovered:
        _paint_hover_glow(p, center, size, anim_t, alpha)


def _paint_engine_glow(p, left, top, w, h, size, anim_t, alpha):
    """引擎底部光晕"""
    deck_cx = left + w / 2
    deck_cy = top + h + size * 0.05
    breath = 0.65 + 0.35 * abs(math.sin(anim_t * 1.8))
    ag = QRadialGradient(deck_cx, deck_cy, size * 0.9)
    ag.setColorAt(0.00, QColor(20, 60, 140, int(8 * breath * alpha)))
    ag.setColorAt(0.50, QColor(25, 70, 160, int(6 * breath * alpha)))
    ag.setColorAt(1.00, QColor(5, 10, 30, 0))
    p.setBrush(ag)
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(deck_cx, deck_cy), size * 0.9, size * 0.45)


def _paint_hull(p, left, top, w, h, size, anim_t, alpha):
    """梯形船体"""
    hull_top = top + h * 0.08
    hull_bot = top + h + size * 0.05
    hull_left = left + w * 0.08
    hull_right = left + w * 0.92

    path = QPainterPath()
    path.moveTo(hull_left - w * 0.02, hull_top)
    path.lineTo(hull_left + w * 0.04, hull_bot)
    path.lineTo(hull_right - w * 0.04, hull_bot)
    path.lineTo(hull_right + w * 0.02, hull_top)
    path.closeSubpath()

    hull_grad = QLinearGradient(left, hull_top, left, hull_bot)
    hull_grad.setColorAt(0.0, QColor(30, 34, 44, int(230 * alpha)))
    hull_grad.setColorAt(0.3, QColor(24, 28, 38, int(240 * alpha)))
    hull_grad.setColorAt(0.7, QColor(20, 22, 32, int(235 * alpha)))
    hull_grad.setColorAt(1.0, QColor(14, 16, 24, int(220 * alpha)))
    p.setBrush(hull_grad)
    p.setPen(QPen(QColor(70, 80, 100, int(140 * alpha)), 0.8))
    p.drawPath(path)


def _paint_deck(p, left, top, w, h, size, center, anim_t, alpha):
    """飞行甲板（五边形）"""
    path = QPainterPath()
    nose_angle, stern_angle = 0.33, 0.12
    d_top = top
    d_bot = top + h * 0.92
    path.moveTo(left + w * nose_angle, d_top)
    path.lineTo(left + w / 2, d_top - h * 0.05)
    path.lineTo(left + w * (1 - nose_angle), d_top)
    path.lineTo(left + w * (1 - stern_angle), d_bot)
    path.lineTo(left + w * stern_angle, d_bot)
    path.closeSubpath()

    deck_grad = QLinearGradient(left, d_top, left, d_bot)
    deck_grad.setColorAt(0.0, QColor(48, 52, 62, int(240 * alpha)))
    deck_grad.setColorAt(0.4, QColor(40, 44, 54, int(245 * alpha)))
    deck_grad.setColorAt(1.0, QColor(34, 38, 48, int(240 * alpha)))
    p.setBrush(deck_grad)
    p.setPen(QPen(QColor(100, 110, 130, int(170 * alpha)), 1.0))
    p.drawPath(path)

    # 甲板虚线边框
    edge_p = QPen(QColor(140, 160, 190, int(75 * alpha)), 0.5)
    edge_p.setStyle(Qt.DashLine)
    p.setPen(edge_p)
    p.setBrush(Qt.NoBrush)
    p.drawPath(path)


def _paint_island(p, left, top, w, h, size, anim_t, alpha):
    """舰岛（右舷指挥塔）"""
    iw = w * 0.13
    ih = h * 0.35
    ix = left + w * 0.82
    iy = top + h * 0.08

    path = QPainterPath()
    path.addRoundedRect(QRectF(ix, iy, iw, ih), 4, 4)
    island_grad = QLinearGradient(ix, iy, ix + iw, iy)
    island_grad.setColorAt(0.0, QColor(52, 57, 67, int(230 * alpha)))
    island_grad.setColorAt(0.6, QColor(68, 73, 83, int(230 * alpha)))
    island_grad.setColorAt(1.0, QColor(47, 50, 62, int(220 * alpha)))
    p.setBrush(island_grad)
    p.setPen(QPen(QColor(110, 120, 140, int(140 * alpha)), 0.8))
    p.drawPath(path)

    # 舰岛舷窗
    for row in range(3):
        for col in range(2):
            wx = ix + 4 + col * (iw * 0.36)
            wy = iy + 5 + row * (ih * 0.26)
            glow = 0.5 + 0.5 * abs(math.sin(anim_t * 2.5 + row * 0.8 + col))
            win_a = int(180 * alpha * glow)
            p.setBrush(QColor(100, 200, 255, win_a))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(QRectF(wx, wy, iw * 0.26, ih * 0.12), 1.5, 1.5)


def _paint_runway(p, left, top, w, h, size, anim_t, alpha):
    """跑道中线 + 弹射轨道"""
    cx = left + w / 2
    y1 = top + h * 0.02
    y2 = top + h * 0.85
    dash = size * 0.07
    gap = size * 0.05
    y = y1
    while y < y2:
        ye = min(y + dash, y2)
        glow_a = int(80 * alpha * (0.6 + 0.4 * abs(math.sin(anim_t * 4 + y * 0.02))))
        p.setPen(QPen(QColor(180, 210, 255, glow_a), 1.0))
        p.drawLine(QPointF(cx, y), QPointF(cx, ye))
        y = ye + gap

    # 弹射器边线
    for side in [-1, 1]:
        lx = cx + side * w * 0.20
        p.setPen(QPen(QColor(150, 170, 200, int(50 * alpha)), 0.5))
        p.drawLine(QPointF(lx, y1 + h * 0.02), QPointF(lx, y2 - h * 0.05))


def _paint_radar(p, left, top, w, h, size, anim_t, alpha):
    """舰岛雷达脉冲"""
    mast_x = left + w * 0.82 + w * 0.13 / 2
    mast_y = top + h * 0.08 - h * 0.35 * 0.2

    # 雷达天线杆
    p.setPen(QPen(QColor(100, 110, 130, int(120 * alpha)), 1.0))
    p.drawLine(QPointF(mast_x, top + h * 0.08), QPointF(mast_x, mast_y))

    # 旋转雷达
    radar_angle = anim_t * 3.0
    radar_r = size * 0.12
    p.setPen(QPen(QColor(0, 200, 255, int(160 * alpha)), 0.8))
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(QPointF(mast_x, mast_y), radar_r, radar_r * 0.3)
    p.drawLine(QPointF(mast_x, mast_y),
               QPointF(mast_x + math.cos(radar_angle) * radar_r,
                       mast_y + math.sin(radar_angle) * radar_r * 0.3))

    # 雷达信号脉冲环
    cycle = anim_t % 2.5
    for i in range(2):
        t = (cycle + i * 2.5 / 2) % 2.5
        progress = t / 2.5
        pr = 3 + progress * size * 0.40
        pa = int(90 * alpha * (1.0 - progress))
        if pa > 0:
            p.setPen(QPen(QColor(0, 200, 255, pa), 0.8 - progress * 0.5))
            p.drawEllipse(QPointF(mast_x, mast_y), pr, pr * 0.6)


def _paint_engine_flames(p, left, top, w, h, size, center, anim_t, alpha):
    """双引擎尾焰（增强版：外层光晕 + 火焰核心 + 粒子喷射）"""
    engine_y = top + h + size * 0.06
    for i, side in enumerate([-1, 1]):
        ex = center.x() + side * w * 0.12
        ey = engine_y
        pulse = 0.6 + 0.4 * abs(math.sin(anim_t * 7 + i * 2.5))
        flame_h = size * 0.30 * pulse
        flame_w = size * 0.05
        # ── 外层火焰光晕（径向渐变脉冲）──
        for fl in range(3):
            fl_r = size * (0.06 + fl * 0.07)
            fl_grad = QRadialGradient(ex, ey + flame_h * 0.4, fl_r * 1.6)
            fl_a = int((70 - fl * 20) * pulse * alpha)
            fl_grad.setColorAt(0.0, QColor(255, 200, 50, fl_a))
            fl_grad.setColorAt(0.5, QColor(255, 100, 20, fl_a // 2))
            fl_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(fl_grad)
            p.drawEllipse(QPointF(ex, ey + flame_h * 0.4), fl_r * 1.6, fl_r * 2.5)
        # ── 线性尾焰主体 ──
        flame_grad = QLinearGradient(ex, ey - flame_h, ex, ey + flame_h * 0.2)
        flame_grad.setColorAt(0.00, QColor(255, 255, 240, int(240 * alpha)))
        flame_grad.setColorAt(0.06, QColor(200, 230, 255, int(220 * alpha)))
        flame_grad.setColorAt(0.25, QColor(80, 170, 255, int(180 * alpha)))
        flame_grad.setColorAt(0.55, QColor(30, 90, 220, int(90 * alpha)))
        flame_grad.setColorAt(0.85, QColor(10, 40, 130, int(25 * alpha)))
        flame_grad.setColorAt(1.00, QColor(0, 5, 30, 0))
        p.setBrush(flame_grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, ey), flame_w, flame_h)
        # ── 尾焰粒子喷射 ──
        import random
        for _ in range(6):
            px = ex + random.uniform(-flame_w * 1.3, flame_w * 1.3)
            py = ey + random.uniform(0, flame_h * 2.2)
            ps = random.uniform(0.4, 2.0)
            pa = int(random.uniform(30, 160) * alpha * pulse)
            p.setBrush(QColor(120, 200, 255, pa))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(px, py), ps, ps)


def _paint_nav_lights(p, center, size, anim_t, alpha):
    """航行灯闪烁（红绿翼尖灯 + 白色频闪尾灯）"""
    cx, cy = center.x(), center.y()
    for sign, nav_base in [(-1, QColor(255, 30, 15)), (1, QColor(15, 255, 35))]:
        nx = cx + sign * size * 0.75
        ny = cy - size * 0.15
        flicker = 0.3 + 0.7 * abs(math.sin(anim_t * 4.5 + sign * 1.3))
        nav_g = QRadialGradient(nx, ny, size * 0.10)
        nav_g.setColorAt(0.0, QColor(nav_base.red(), nav_base.green(), nav_base.blue(), int(200 * flicker * alpha)))
        nav_g.setColorAt(0.4, QColor(nav_base.red(), nav_base.green(), nav_base.blue(), int(100 * flicker * alpha)))
        nav_g.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen); p.setBrush(nav_g)
        p.drawEllipse(QPointF(nx, ny), size * 0.10, size * 0.10)
        p.setBrush(QColor(255, 255, 255, int(200 * flicker * alpha)))
        p.drawEllipse(QPointF(nx, ny), size * 0.03, size * 0.03)
    strobe_y = cy + size * 0.55
    strobe_flicker = abs(math.sin(anim_t * 6.0))
    for sx in [cx - size * 0.30, cx + size * 0.30]:
        sg = QRadialGradient(sx, strobe_y, size * 0.08)
        sg.setColorAt(0.0, QColor(255, 255, 255, int(200 * strobe_flicker * alpha)))
        sg.setColorAt(0.5, QColor(200, 220, 255, int(100 * strobe_flicker * alpha)))
        sg.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen); p.setBrush(sg)
        p.drawEllipse(QPointF(sx, strobe_y), size * 0.08, size * 0.08)


def _paint_hover_glow(p, center, size, anim_t, alpha):
    """hover 增强光晕（多层扩散环 + 引擎光晕联动）"""
    pulse = 0.7 + 0.3 * abs(math.sin(anim_t * 3.0))
    # 内层主题密集光晕
    for i in range(3):
        ir = size * (0.88 + i * 0.10)
        iglow = QRadialGradient(center, ir)
        ga = int((65 - i * 18) * pulse)
        iglow.setColorAt(0.55, QColor(255, 255, 255, 0))
        iglow.setColorAt(0.76, QColor(80, 190, 255, ga // 2))
        iglow.setColorAt(0.90, QColor(0, 140, 255, ga))
        iglow.setColorAt(0.98, QColor(0, 70, 180, ga // 3))
        iglow.setColorAt(1.00, QColor(0, 0, 0, 0))
        p.setBrush(iglow)
        p.setPen(Qt.NoPen)
        p.drawEllipse(center, ir, ir)
    # 外层扩散光晕
    for i in range(3):
        outer_r = size * (1.0 + i * 0.26)
        glow = QRadialGradient(center, outer_r)
        ga = int((48 - i * 14) * pulse)
        glow.setColorAt(0.70, QColor(255, 255, 255, 0))
        glow.setColorAt(0.85, QColor(80, 190, 255, ga // 2))
        glow.setColorAt(0.94, QColor(0, 140, 255, ga))
        glow.setColorAt(1.00, QColor(0, 0, 0, 0))
        p.setBrush(glow)
        p.setPen(Qt.NoPen)
        p.drawEllipse(center, outer_r, outer_r)
    # 明亮轮廓环（呼吸感）
    br = 0.55 + 0.45 * abs(math.sin(anim_t * 4.5))
    rpen = QPen(QColor(80, 190, 255, int(210 * pulse * alpha * br)), 2.2 + 1.2 * br)
    p.setPen(rpen)
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(center, size * 0.95, size * 0.95)


```
