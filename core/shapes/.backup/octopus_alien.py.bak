# -*- coding: utf-8 -*-
"""
章鱼星人 — 圆头 + 8条触手腕足弹性摆动 + 吸盘闪烁
"""
import math, random
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
    s = radius / 48.0  # 基准

    # ── 整体漂浮 ──
    float_y = math.sin(anim_t * 1.6) * radius * 0.06
    float_x = math.cos(anim_t * 1.3) * radius * 0.03
    body_cx = cx + float_x
    body_cy = cy + float_y

    head_r = radius * 0.50  # 头部半径
    head_cy = body_cy - radius * 0.10

    # ── 背景辉光（海洋紫）──
    glow = QRadialGradient(body_cx, body_cy, radius * 1.1)
    glow.setColorAt(0.0, QColor(140, 80, 200, 18))
    glow.setColorAt(0.5, QColor(100, 50, 180, 8))
    glow.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(glow); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), radius * 1.1, radius * 1.1)

    # ── 8条触手（从头部下方辐射，弹性正弦摆动）──
    tentacle_rng = random.Random(31)
    tentacles_data = []
    for i in range(8):
        base_angle = -math.pi / 2 + (i - 3.5) * math.pi / 10  # 扇开在下方
        length = radius * tentacle_rng.uniform(0.58, 0.85)
        thickness = radius * tentacle_rng.uniform(0.07, 0.14)
        swing_phase = tentacle_rng.uniform(0, 2 * math.pi)
        swing_freq = tentacle_rng.uniform(2.0, 3.5)
        tentacles_data.append((base_angle, length, thickness, swing_phase, swing_freq))

    # 先画远处的触手（背面），再画近的（正面）
    for i, (base_angle, length, thickness, swing_phase, swing_freq) in enumerate(tentacles_data):
        # 弹性摆动：每个触手沿路径的多段正弦偏移
        swing = math.sin(anim_t * swing_freq + swing_phase) * radius * 0.13
        swing2 = math.cos(anim_t * swing_freq * 1.4 + swing_phase + 1) * radius * 0.07
        segs = 7
        tent_path = QPainterPath()
        # 触手根点在头部下缘
        start_x = body_cx + math.cos(base_angle) * head_r * 0.95
        start_y = head_cy + head_r * 0.55
        tent_path.moveTo(start_x, start_y)

        prev_x, prev_y = start_x, start_y
        for seg in range(1, segs + 1):
            t = seg / segs
            seg_swing = swing * t + swing2 * (1 - t) * 0.5
            perp = base_angle + math.pi / 2
            nx = start_x + math.cos(base_angle) * length * t + math.cos(perp) * seg_swing
            ny = start_y + math.sin(base_angle) * length * t + math.sin(perp) * seg_swing * 0.5 + length * t * 0.2

            # 每段用二次贝塞尔平滑
            cx1 = (prev_x + nx) / 2 + math.cos(perp) * seg_swing * 0.15
            cy1 = (prev_y + ny) / 2 + math.sin(perp) * seg_swing * 0.15 * 0.5
            tent_path.quadTo(cx1, cy1, nx, ny)
            prev_x, prev_y = nx, ny
            # 吸盘（沿触手内侧闪烁）
            if seg % 2 == 0:
                sucker_alpha = int(80 + 60 * abs(math.sin(anim_t * 4.0 + i * 0.8 + seg)))
                sucker_grad = QRadialGradient(nx, ny, thickness * 0.55)
                hue = (i * 45 + seg * 20) % 360
                sucker_grad.setColorAt(0.0, QColor.fromHsv(hue, 150, 220, sucker_alpha))
                sucker_grad.setColorAt(0.6, QColor.fromHsv(hue, 180, 160, sucker_alpha // 2))
                sucker_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
                p.setBrush(sucker_grad); p.setPen(Qt.NoPen)
                p.drawEllipse(QPointF(nx, ny), thickness * 0.55, thickness * 0.55)

        # 触手填充（深紫→青渐变）
        tent_grad = QLinearGradient(start_x, start_y, prev_x, prev_y)
        hue_t = (i * 40 + 270) % 360
        tent_grad.setColorAt(0.0, QColor.fromHsv(hue_t, 180, 140, 220))
        tent_grad.setColorAt(0.5, QColor.fromHsv(hue_t, 200, 120, 200))
        tent_grad.setColorAt(1.0, QColor.fromHsv(hue_t, 220, 90, 170))
        pen = QPen(QBrush(tent_grad), thickness)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawPath(tent_path)

        # 触手末端球（吸盘簇）
        tip_grad = QRadialGradient(prev_x, prev_y, thickness * 0.7)
        tip_grad.setColorAt(0.0, QColor.fromHsv(hue_t, 100, 230, 200))
        tip_grad.setColorAt(0.6, QColor.fromHsv(hue_t, 180, 150, 160))
        tip_grad.setColorAt(1.0, QColor.fromHsv(hue_t, 200, 80, 50))
        p.setPen(Qt.NoPen); p.setBrush(tip_grad)
        p.drawEllipse(QPointF(prev_x, prev_y), thickness * 0.7, thickness * 0.7)

    # ── 头部（圆球形，紫罗兰色调）──
    head = QRadialGradient(body_cx - head_r * 0.12, head_cy - head_r * 0.15, head_r * 1.05)
    head.setColorAt(0.0, QColor(210, 170, 240))
    head.setColorAt(0.25, QColor(170, 120, 210))
    head.setColorAt(0.55, QColor(120, 75, 170))
    head.setColorAt(0.80, QColor(70, 35, 120))
    head.setColorAt(0.95, QColor(35, 15, 70))
    head.setColorAt(1.0, QColor(15, 5, 35))
    p.setBrush(head); p.setPen(QPen(QColor(80, 40, 140), 1.2 * s))
    p.drawEllipse(QPointF(body_cx, head_cy), head_r, head_r)

    # ── 头部高光 ──
    head_spec = QRadialGradient(body_cx - head_r * 0.22, head_cy - head_r * 0.25, head_r * 0.35)
    head_spec.setColorAt(0.0, QColor(240, 220, 255, 60))
    head_spec.setColorAt(0.5, QColor(200, 170, 240, 20))
    head_spec.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(head_spec); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, head_cy), head_r, head_r)

    # ── 眼睛（两枚大椭圆，荧光绿瞳）──
    eye_spacing = head_r * 0.28
    eye_rx = head_r * 0.20
    eye_ry = head_r * 0.26
    for sign in (-1, 1):
        ex = body_cx + sign * eye_spacing
        ey = head_cy - head_r * 0.08
        # 眼白
        eye_white = QRadialGradient(ex, ey, eye_rx * 1.15)
        eye_white.setColorAt(0.0, QColor(255, 255, 255))
        eye_white.setColorAt(0.6, QColor(230, 250, 240))
        eye_white.setColorAt(1.0, QColor(180, 220, 200))
        p.setBrush(eye_white); p.setPen(QPen(QColor(60, 30, 100), 1.0 * s))
        p.drawEllipse(QPointF(ex, ey), eye_rx, eye_ry)

        # 荧光绿瞳孔（横椭圆，山羊瞳样式）
        pupil_rx = eye_rx * 0.55
        pupil_ry = eye_ry * 0.35
        pupil_grad = QRadialGradient(ex, ey, pupil_rx * 1.1)
        pupil_grad.setColorAt(0.0, QColor(80, 255, 80))
        pupil_grad.setColorAt(0.4, QColor(30, 200, 30))
        pupil_grad.setColorAt(0.8, QColor(5, 100, 10))
        pupil_grad.setColorAt(1.0, QColor(0, 40, 5))
        p.setBrush(pupil_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, ey), pupil_rx, pupil_ry)

        # 瞳孔高光点
        p.setBrush(QColor(255, 255, 255, 200))
        p.drawEllipse(QPointF(ex - pupil_rx * 0.3, ey - pupil_ry * 0.4), pupil_rx * 0.22, pupil_ry * 0.28)

    # ── 嘴巴（小弧线）──
    mouth_cx = body_cx
    mouth_cy = head_cy + head_r * 0.28
    mouth = QPainterPath()
    mouth.moveTo(mouth_cx - head_r * 0.12, mouth_cy)
    mouth.cubicTo(mouth_cx - head_r * 0.06, mouth_cy + head_r * 0.10,
                  mouth_cx + head_r * 0.06, mouth_cy + head_r * 0.10,
                  mouth_cx + head_r * 0.12, mouth_cy)
    pen_m = QPen(QColor(40, 15, 80), 1.0 * s)
    pen_m.setCapStyle(Qt.RoundCap)
    p.setPen(pen_m); p.setBrush(Qt.NoBrush)
    p.drawPath(mouth)

    # ── 触手间粒子（生物荧光微尘）──
    part_rng = random.Random(int(anim_t * 280) % 100000 + 889)
    p.setPen(Qt.NoPen)
    for _ in range(12):
        pa = part_rng.uniform(0, 2 * math.pi)
        pd = radius * (0.50 + 0.50 * part_rng.random())
        px = body_cx + math.cos(pa) * pd
        py = body_cy + math.sin(pa) * pd
        ps = part_rng.uniform(0.4, 1.4)
        pg = QRadialGradient(px, py, ps * 2)
        ph = part_rng.randint(0, 359)
        pg.setColorAt(0.0, QColor.fromHsv(ph, 150, 255, 55))
        pg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(pg)
        p.drawEllipse(QPointF(px, py), ps * 2, ps * 2)

    # ── 环绕粒子光环（主题色匹配）──
    aura_rng = random.Random(int(anim_t * 280) % 100000 + 88330)
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
        ag.setColorAt(0.0, QColor(160, 100, 220, a_alpha))
        ag.setColorAt(0.5, QColor(160//2, 100//2, 250, a_alpha // 2))
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
            ig.setColorAt(0.78, QColor(160, 100, 220, ga // 2))
            ig.setColorAt(0.90, QColor(160, 100, 220, ga))
            ig.setColorAt(0.97, QColor(160//2, 100//2, 250, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        # 外层扩散光晕
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(160, 100, 220, ga // 2))
            og.setColorAt(0.96, QColor(160//2, 100//2, 255, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)
        # 明亮轮廓环（呼吸感）
        br = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
        rpen = QPen(QColor(160, 100, 220, int(220 * hp * br)), 2.5 + 1.0 * br)
        p.setPen(rpen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 3, radius + 3)


    p.restore()
