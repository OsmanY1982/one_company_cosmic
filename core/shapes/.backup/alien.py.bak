# -*- coding: utf-8 -*-
"""
小绿外星人 — 大头 + 大椭圆黑眼 + 触角弹性摆动 + 微表情眨眼 + 漂浮
"""
import math, random
from PyQt5.QtCore import Qt, QPointF, QRectF
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
    # 整体缩放，外星人在 radius 范围内
    s = radius / 50.0  # 基准半径 50px

    # ── 浮动动画 ──
    float_y = math.sin(anim_t * 2.2) * radius * 0.08
    float_x = math.cos(anim_t * 1.7) * radius * 0.04

    head_cx = cx + float_x
    head_cy = cy - radius * 0.15 + float_y
    head_r = radius * 0.65

    # ── 头部辉光 ──
    glow = QRadialGradient(head_cx, head_cy, head_r * 1.3)
    glow.setColorAt(0.0, QColor(120, 255, 100, 20))
    glow.setColorAt(0.7, QColor(60, 200, 60, 8))
    glow.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(glow); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(head_cx, head_cy), head_r * 1.3, head_r * 1.3)

    # ── 触角（两根，弹性摆动）──
    for side in (-1, 1):
        ant_base_x = head_cx + side * head_r * 0.35
        ant_base_y = head_cy - head_r * 0.75
        ant_len = radius * 0.55
        # 弹性摆动（二阶弹簧模拟：sin叠加）
        swing = math.sin(anim_t * 3.5 + side * 1.2) * radius * 0.12
        swing2 = math.cos(anim_t * 4.2 + side * 0.7) * radius * 0.06
        ant_path = QPainterPath()
        ant_path.moveTo(ant_base_x, ant_base_y)
        cp1_x = ant_base_x + side * ant_len * 0.25 + swing
        cp1_y = ant_base_y - ant_len * 0.4
        cp2_x = ant_base_x + side * ant_len * 0.5 + swing * 1.4
        cp2_y = ant_base_y - ant_len * 0.7
        tip_x = ant_base_x + side * ant_len * 0.3 + swing * 1.8 + swing2
        tip_y = ant_base_y - ant_len * 0.9
        ant_path.cubicTo(cp1_x, cp1_y, cp2_x, cp2_y, tip_x, tip_y)
        pen = QPen(QColor(80, 220, 60), 2.5 * s)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawPath(ant_path)
        # 触角末端小球
        ball_grad = QRadialGradient(tip_x, tip_y, 4 * s)
        ball_grad.setColorAt(0.0, QColor(150, 255, 100))
        ball_grad.setColorAt(0.6, QColor(80, 220, 60))
        ball_grad.setColorAt(1.0, QColor(30, 150, 20))
        p.setPen(Qt.NoPen); p.setBrush(ball_grad)
        p.drawEllipse(QPointF(tip_x, tip_y), 4 * s, 4 * s)

    # ── 头部（椭圆大头，绿渐变）──
    head = QRadialGradient(head_cx - head_r * 0.15, head_cy - head_r * 0.2, head_r * 1.05)
    head.setColorAt(0.0, QColor(140, 240, 100))
    head.setColorAt(0.4, QColor(80, 200, 60))
    head.setColorAt(0.75, QColor(40, 150, 30))
    head.setColorAt(0.92, QColor(20, 100, 15))
    head.setColorAt(1.0, QColor(10, 60, 8))
    p.setBrush(head); p.setPen(QPen(QColor(30, 120, 25), 1.5 * s))
    # 头部椭圆（宽于高）
    head_ry = head_r * 0.88
    p.drawEllipse(QPointF(head_cx, head_cy), head_r, head_ry)

    # ── 高光 ──
    head_spec = QRadialGradient(head_cx - head_r * 0.25, head_cy - head_r * 0.28, head_r * 0.38)
    head_spec.setColorAt(0.0, QColor(200, 255, 160, 70))
    head_spec.setColorAt(0.5, QColor(160, 240, 120, 20))
    head_spec.setColorAt(1.0, QColor(120, 220, 80, 0))
    p.setBrush(head_spec); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(head_cx, head_cy), head_r, head_ry)

    # ── 眼睛（大椭圆，黑色虹膜 + 白色高光点）──
    eye_spacing = head_r * 0.30
    eye_rx = head_r * 0.22
    eye_ry = head_r * 0.30

    # 眨眼动画（每 3 秒眨一次，持续 0.15 秒）
    blink_phase = (anim_t * 0.7) % 3.0
    blink = 1.0
    if blink_phase < 0.15:
        blink = blink_phase / 0.15
    elif 2.85 < blink_phase <= 3.0:
        blink = (3.0 - blink_phase) / 0.15

    for sign in (-1, 1):
        ex = head_cx + sign * eye_spacing
        ey = head_cy - head_ry * 0.1
        # 眼白
        eye_white = QRadialGradient(ex, ey, eye_rx * 1.2)
        eye_white.setColorAt(0.0, QColor(255, 255, 255))
        eye_white.setColorAt(0.7, QColor(240, 255, 240))
        eye_white.setColorAt(1.0, QColor(200, 240, 200))
        p.setBrush(eye_white); p.setPen(QPen(QColor(30, 100, 25), 1.0 * s))
        if blink < 1.0:
            p.drawEllipse(QRectF(ex - eye_rx, ey - eye_ry * blink,
                                  eye_rx * 2, eye_ry * 2 * blink))
        else:
            p.drawEllipse(QPointF(ex, ey), eye_rx, eye_ry)
        # 瞳孔（深黑大圆）
        pupil_r = eye_rx * 0.65
        p.setBrush(QColor(10, 20, 5))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, ey), pupil_r, pupil_r)
        # 高光点
        highlight_x = ex - eye_rx * 0.28
        highlight_y = ey - eye_ry * 0.32
        p.setBrush(QColor(255, 255, 255, 220))
        p.drawEllipse(QPointF(highlight_x, highlight_y), pupil_r * 0.3, pupil_r * 0.3)
        p.setBrush(QColor(255, 255, 255, 120))
        p.drawEllipse(QPointF(highlight_x + pupil_r * 0.15, highlight_y + pupil_r * 0.2),
                      pupil_r * 0.15, pupil_r * 0.15)

    # ── 微笑嘴巴 ──
    mouth_cx = head_cx
    mouth_cy = head_cy + head_ry * 0.30
    mouth = QPainterPath()
    mouth.moveTo(mouth_cx - head_r * 0.18, mouth_cy)
    mouth.cubicTo(mouth_cx - head_r * 0.10, mouth_cy + head_ry * 0.15,
                  mouth_cx + head_r * 0.10, mouth_cy + head_ry * 0.15,
                  mouth_cx + head_r * 0.18, mouth_cy)
    pen_m = QPen(QColor(20, 80, 15), 1.2 * s)
    pen_m.setCapStyle(Qt.RoundCap)
    p.setPen(pen_m); p.setBrush(Qt.NoBrush)
    p.drawPath(mouth)

    # ── 小身体（半椭圆）──
    body_rx = head_r * 0.55
    body_ry = head_r * 0.35
    body_cx = head_cx
    body_cy = head_cy + head_ry * 0.70
    body = QRadialGradient(body_cx, body_cy - body_ry * 0.1, body_rx * 1.1)
    body.setColorAt(0.0, QColor(100, 220, 70))
    body.setColorAt(0.7, QColor(50, 160, 35))
    body.setColorAt(1.0, QColor(20, 100, 15))
    p.setBrush(body); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), body_rx, body_ry)

    # ── 肩膀小闪烁粒子 ──
    part_rng = random.Random(int(anim_t * 350) % 100000 + 666)
    p.setPen(Qt.NoPen)
    for _ in range(8):
        pa2 = part_rng.uniform(0, 2 * math.pi)
        pd2 = radius * (0.70 + 0.30 * part_rng.random())
        px2 = cx + math.cos(pa2) * pd2
        py2 = cy + math.sin(pa2) * pd2
        ps2 = part_rng.uniform(0.3, 1.0)
        pg = QRadialGradient(px2, py2, ps2 * 2.0)
        pg.setColorAt(0.0, QColor(140, 255, 100, 60))
        pg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(pg)
        p.drawEllipse(QPointF(px2, py2), ps2 * 2.0, ps2 * 2.0)

    # ── 环绕粒子光环（主题色匹配）──
    aura_rng = random.Random(int(anim_t * 280) % 100000 + 43132)
    p.setPen(Qt.NoPen)
    for _ in range(22):
        a_angle = aura_rng.uniform(0, 2 * math.pi)
        a_dist = radius * (0.55 + 0.45 * aura_rng.random())
        a_offset = anim_t * (0.3 + 0.2 * aura_rng.random())
        ax = cx + math.cos(a_angle + a_offset) * a_dist
        ay = cy + math.sin(a_angle + a_offset) * a_dist * 0.7
        a_size = aura_rng.uniform(0.3, 1.8)
        a_alpha = aura_rng.randint(25, 70)
        ag = QRadialGradient(ax, ay, a_size * 2.5)
        ag.setColorAt(0.0, QColor(120, 200, 240, a_alpha))
        ag.setColorAt(0.5, QColor(120//2, 200//2, 255, a_alpha // 2))
        ag.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(ag)
        p.drawEllipse(QPointF(ax, ay), a_size * 2.5, a_size * 2.5)

# ── 悬停增强（主题色脉冲光晕 + 呼吸轮廓）──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        # 内层主题光晕
        for i in range(3):
            ir = radius + 2 + i * 5
            ig = QRadialGradient(center, ir)
            ga = int((70 - i * 18) * hp)
            ig.setColorAt(0.60, QColor(255, 255, 255, 0))
            ig.setColorAt(0.78, QColor(120, 200, 240, ga // 2))
            ig.setColorAt(0.90, QColor(120, 200, 240, ga))
            ig.setColorAt(0.97, QColor(120//2, 200//2, 255, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        # 外层扩散光晕
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(120, 200, 240, ga // 2))
            og.setColorAt(0.96, QColor(120//2, 200//2, 255, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)
        # 明亮轮廓环（呼吸感）
        br = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
        rpen = QPen(QColor(120, 200, 240, int(220 * hp * br)), 2.5 + 1.0 * br)
        p.setPen(rpen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 3, radius + 3)


    p.restore()
