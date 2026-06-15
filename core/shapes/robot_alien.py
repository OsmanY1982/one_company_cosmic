# -*- coding: utf-8 -*-
"""
机器外星人 — 方形金属头部 + LED点阵眼 + 天线脉冲 + 机械装甲身体 + 扫描线
"""
import math, random, time
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


    # ── 多层外辉光（增强质感）──
    for glow_layer in range(4):
        glow_scale = 1.06 + glow_layer * 0.20
        glow_r = radius * glow_scale
        glow = QRadialGradient(cx, cy, glow_r)
        ga = max(1, 35 - glow_layer * 8)
        glow.setColorAt(0.0, QColor(255, 255, 255, 0))
        glow.setColorAt(0.25, QColor(200, 200, 255, ga // 2))
        glow.setColorAt(0.55, QColor(120, 140, 255, ga))
        glow.setColorAt(0.80, QColor(60, 80, 200, ga // 2))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(glow); p.setPen(Qt.NoPen)
        p.drawEllipse(center, glow_r, glow_r)
    s = radius / 48.0

    # ── 银灰色金属色调 ──
    metal_base = QColor(140, 150, 165)
    metal_dark = QColor(80, 90, 105)
    metal_light = QColor(200, 210, 225)
    blue_glow = QColor(60, 180, 255)
    blue_bright = QColor(120, 220, 255)

    # ── 头部：方形/多边形（带圆角金属感）──
    head_w = radius * 1.0
    head_h = radius * 0.9
    head_top = cy - radius * 0.55
    head_left = cx - head_w / 2

    head_path = QPainterPath()
    corner_r = radius * 0.12
    head_path.addRoundedRect(head_left, head_top, head_w, head_h, corner_r, corner_r)

    # 金属渐变头部
    head_grad = QLinearGradient(head_left, head_top, head_left + head_w, head_top + head_h)
    head_grad.setColorAt(0.0, QColor(160, 170, 190))
    head_grad.setColorAt(0.3, QColor(190, 200, 220))
    head_grad.setColorAt(0.6, QColor(120, 130, 150))
    head_grad.setColorAt(1.0, QColor(90, 100, 120))
    p.setBrush(head_grad)
    p.setPen(QPen(QColor(60, 70, 90), s * 1.5))
    p.drawPath(head_path)

    # ── 头部装甲线 ──
    p.setPen(QPen(QColor(60, 70, 90, 120), s * 0.8))
    p.drawLine(QPointF(head_left + corner_r, head_top + head_h * 0.35),
               QPointF(head_left + head_w - corner_r, head_top + head_h * 0.35))
    p.drawLine(QPointF(head_left + corner_r, head_top + head_h * 0.65),
               QPointF(head_left + head_w - corner_r, head_top + head_h * 0.65))

    # ── 天线 ──
    ant_base_l = cx - radius * 0.18
    ant_base_r = cx + radius * 0.18
    ant_top_y = head_top - radius * 0.22
    ant_len = radius * 0.25

    for ant_x in (ant_base_l, ant_base_r):
        p.setPen(QPen(QColor(120, 130, 150), s * 1.8))
        p.drawLine(QPointF(ant_x, head_top), QPointF(ant_x, ant_top_y - ant_len))
        # 天线顶端脉冲光球
        pulse = 0.5 + 0.5 * math.sin(anim_t * 6.0 + (ant_x - cx) * 0.3)
        glow_r = s * 3.5 * (0.8 + 0.4 * pulse)
        ant_glow = QRadialGradient(ant_x, ant_top_y - ant_len, glow_r)
        ant_glow.setColorAt(0.0, QColor(120, 220, 255, int(200 * pulse)))
        ant_glow.setColorAt(0.5, QColor(60, 180, 255, int(100 * pulse)))
        ant_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(ant_glow)
        p.drawEllipse(QPointF(ant_x, ant_top_y - ant_len), glow_r, glow_r)

    # ── 眼睛：LED 点阵 2×3 ──
    led_cols, led_rows = 3, 2
    led_w = head_w * 0.30
    led_h = head_h * 0.26
    led_spacing_x = led_w / (led_cols - 1 + 1.5)
    led_spacing_y = led_h / (led_rows - 1 + 1.5)
    led_off_x = cx - led_w / 2
    led_off_y = head_top + head_h * 0.22

    # 底板暗色
    p.setBrush(QColor(20, 25, 35))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(int(led_off_x - s * 2), int(led_off_y - s * 2),
                      int(led_w + s * 4), int(led_h + s * 4), s * 2, s * 2)

    led_r = s * 2.0
    for row in range(led_rows):
        for col in range(led_cols):
            lx = led_off_x + col * led_spacing_x
            ly = led_off_y + row * led_spacing_y
            # LED 闪烁
            flicker = 0.75 + 0.25 * math.sin(anim_t * 8.0 + row * 1.7 + col * 0.9)
            led_alpha = int(200 * flicker)
            p.setBrush(QColor(60, 180, 255, led_alpha))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(int(lx), int(ly), int(s * 3.5), int(s * 3.5), s * 0.8, s * 0.8)
            # 光晕
            led_glow = QRadialGradient(lx + s * 1.75, ly + s * 1.75, s * 5)
            led_glow.setColorAt(0.0, QColor(120, 220, 255, int(80 * flicker)))
            led_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setBrush(led_glow)
            p.drawEllipse(QPointF(lx + s * 1.75, ly + s * 1.75), s * 5, s * 5)

    # ── 扫描线 ──
    scan_phase = (anim_t * 3.0) % 1.0
    scan_y = led_off_y + led_h * 0.5 + math.sin(scan_phase * math.pi * 2) * led_h * 0.55
    scan_alpha = int(180 * (0.3 + 0.7 * abs(math.sin(scan_phase * math.pi))))
    p.setPen(QPen(QColor(60, 200, 255, scan_alpha), s * 0.6))
    p.drawLine(QPointF(head_left + head_w * 0.15, scan_y),
               QPointF(head_left + head_w * 0.85, scan_y))

    # ── 身体：梯形装甲 ──
    body_top = cy + radius * 0.05
    body_h = radius * 0.55
    body_w_top = radius * 0.8
    body_w_bottom = radius * 1.15
    body_left_top = cx - body_w_top / 2
    body_left_bot = cx - body_w_bottom / 2

    body_path = QPainterPath()
    body_path.moveTo(body_left_top, body_top)
    body_path.lineTo(body_left_top + body_w_top, body_top)
    body_path.lineTo(body_left_bot + body_w_bottom, body_top + body_h)
    body_path.lineTo(body_left_bot, body_top + body_h)
    body_path.closeSubpath()

    body_grad = QLinearGradient(cx, body_top, cx, body_top + body_h)
    body_grad.setColorAt(0.0, QColor(150, 160, 180))
    body_grad.setColorAt(0.5, QColor(180, 190, 210))
    body_grad.setColorAt(1.0, QColor(100, 110, 130))
    p.setBrush(body_grad)
    p.setPen(QPen(QColor(60, 70, 90), s * 1.5))
    p.drawPath(body_path)

    # 身体装甲板分割线
    p.setPen(QPen(QColor(60, 70, 90, 120), s * 0.8))
    p.drawLine(QPointF(body_left_top + s * 3, body_top + body_h * 0.45),
               QPointF(body_left_top + body_w_top - s * 3, body_top + body_h * 0.45))

    # ── 胸口蓝色核心 ──
    core_r = radius * 0.13
    core_y = body_top + body_h * 0.55
    core_pulse = 0.6 + 0.4 * math.sin(anim_t * 3.5)
    core_glow = QRadialGradient(cx, core_y, core_r * 2.5)
    core_glow.setColorAt(0.0, QColor(80, 200, 255, int(180 * core_pulse)))
    core_glow.setColorAt(0.3, QColor(40, 140, 255, int(100 * core_pulse)))
    core_glow.setColorAt(0.6, QColor(20, 80, 200, int(40 * core_pulse)))
    core_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setPen(Qt.NoPen)
    p.setBrush(core_glow)
    p.drawEllipse(QPointF(cx, core_y), core_r * 2.5, core_r * 2.5)
    # 核心白色亮点
    p.setBrush(QColor(180, 240, 255, int(230 * core_pulse)))
    p.drawEllipse(QPointF(cx, core_y), core_r, core_r)

    # 悬停增强（主题色脉冲光晕 + 呼吸轮廓）──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        # 内层主题光晕
        for i in range(3):
            ir = radius + 2 + i * 5
            ig = QRadialGradient(center, ir)
            ga = int((70 - i * 18) * hp)
            ig.setColorAt(0.60, QColor(255, 255, 255, 0))
            ig.setColorAt(0.78, QColor(80, 180, 255, ga // 2))
            ig.setColorAt(0.90, QColor(80, 180, 255, ga))
            ig.setColorAt(0.97, QColor(40, 90, 175, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        # 外层扩散光晕（带扫描线风格）
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(80, 180, 255, ga // 2))
            og.setColorAt(0.96, QColor(40, 90, 175, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)
        # 明亮轮廓环（呼吸感）
        br = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
        rpen = QPen(QColor(80, 180, 255, int(220 * hp * br)), 2.5 + 1.0 * br)
        p.setPen(rpen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 3, radius + 3)

    # ── 环绕粒子光环（科技蓝）──
    aura_rng = random.Random(int(anim_t * 280) % 100000 + 7733)
    p.setPen(Qt.NoPen)
    for _ in range(20):
        a_angle = aura_rng.uniform(0, 2 * math.pi)
        a_dist = radius * (0.55 + 0.45 * aura_rng.random())
        a_offset = anim_t * (0.3 + 0.2 * aura_rng.random())
        ax = cx + math.cos(a_angle + a_offset) * a_dist
        ay = cy + math.sin(a_angle + a_offset) * a_dist * 0.7
        a_size = aura_rng.uniform(0.3, 1.8)
        a_alpha = aura_rng.randint(25, 70)
        ag = QRadialGradient(ax, ay, a_size * 2.5)
        ag.setColorAt(0.0, QColor(80, 180, 255, a_alpha))
        ag.setColorAt(0.5, QColor(40, 90, 175, a_alpha // 2))
        ag.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(ag)
        p.drawEllipse(QPointF(ax, ay), a_size * 2.5, a_size * 2.5)

    p.restore()
