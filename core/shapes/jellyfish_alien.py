# -*- coding: utf-8 -*-
"""
水母外星人 — 半透明伞状头部 + 辐射纹理 + 6-8 条贝塞尔触手弹性摆动 + 生物荧光脉冲
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
    s = radius / 50.0  # 缩放基准

    # ── 浮动动画 ──
    float_y = math.sin(anim_t * 1.8) * radius * 0.06
    float_x = math.cos(anim_t * 1.4) * radius * 0.03
    jcx = cx + float_x
    jcy = cy - radius * 0.12 + float_y

    # ── 伞状头部尺寸 ──
    umbrella_rx = radius * 0.58
    umbrella_ry = radius * 0.48
    umbrella_top = jcy - umbrella_ry
    umbrella_bottom = jcy

    # ── bioluminescence pulse at apex ──
    bio_pulse = 0.5 + 0.5 * abs(math.sin(anim_t * 2.7 + 1.1))
    apex_y = umbrella_top
    for layer in range(3):
        lr = umbrella_rx * (0.22 + layer * 0.18)
        la = int((50 - layer * 14) * bio_pulse)
        glow = QRadialGradient(jcx, apex_y, lr)
        glow.setColorAt(0.0, QColor(80, 255, 200, la))
        glow.setColorAt(0.45, QColor(40, 220, 180, int(la * 0.6)))
        glow.setColorAt(0.78, QColor(20, 160, 140, int(la * 0.25)))
        glow.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(glow); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(jcx, apex_y), lr, lr * 0.8)

    # ── 伞体半透明渐变 ──
    umbrella_path = QPainterPath()
    umbrella_path.arcTo(QRectF(jcx - umbrella_rx, umbrella_top,
                               umbrella_rx * 2, umbrella_ry * 2), 0, 180)
    umbrella_path.closeSubpath()
    # 伞体填充
    body_grad = QRadialGradient(jcx, umbrella_top + umbrella_ry * 0.35, umbrella_rx * 1.1)
    body_grad.setColorAt(0.0, QColor(100, 220, 200, 140))
    body_grad.setColorAt(0.35, QColor(60, 180, 170, 120))
    body_grad.setColorAt(0.65, QColor(30, 140, 140, 90))
    body_grad.setColorAt(0.88, QColor(15, 90, 100, 50))
    body_grad.setColorAt(1.0, QColor(5, 50, 60, 20))
    p.setBrush(body_grad)
    p.setPen(QPen(QColor(40, 160, 150, 80), 1.2 * s))
    p.drawPath(umbrella_path)

    # ── 辐射状纹理（伞面内部放射线）──
    radial_count = 14
    rng_radial = random.Random(int(anim_t * 137) % 10000 + 777)
    for i in range(radial_count):
        angle = (i / radial_count) * math.pi
        inner_r = umbrella_rx * 0.18
        outer_r = umbrella_rx * (0.82 + rng_radial.uniform(-0.06, 0.06))
        x1 = jcx + math.cos(angle) * inner_r
        y1 = umbrella_top + umbrella_ry - math.sin(angle) * inner_r
        x2 = jcx + math.cos(angle) * outer_r
        y2 = umbrella_top + umbrella_ry - math.sin(angle) * outer_r
        path = QPainterPath()
        path.moveTo(x1, y1)
        path.lineTo(x2, y2)
        pen = QPen(QColor(80, 220, 200, 45), 0.8 * s)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawPath(path)

    # ── 伞缘高光 ──
    rim_glow = QRadialGradient(jcx, umbrella_bottom - umbrella_ry * 0.1, umbrella_rx * 1.05)
    rim_glow.setColorAt(0.0, QColor(255, 255, 255, 0))
    rim_glow.setColorAt(0.5, QColor(120, 240, 220, 18))
    rim_glow.setColorAt(0.8, QColor(60, 200, 180, 28))
    rim_glow.setColorAt(0.92, QColor(40, 160, 150, 45))
    rim_glow.setColorAt(1.0, QColor(80, 220, 200, 35))
    p.setBrush(rim_glow); p.setPen(Qt.NoPen)
    p.drawEllipse(QRectF(jcx - umbrella_rx, umbrella_top,
                         umbrella_rx * 2, umbrella_ry * 2))

    # ── 触手 ──
    tentacle_count = 7
    rng_tent = random.Random(int(anim_t * 241) % 100000 + 333)
    for i in range(tentacle_count):
        # 触手在伞缘的起始位置
        base_angle = (i / tentacle_count) * math.pi
        base_x = jcx + math.cos(base_angle) * umbrella_rx * 0.92
        base_y = umbrella_bottom - math.sin(base_angle) * umbrella_ry * 0.15

        tent_len = radius * (0.45 + 0.35 * rng_tent.random())
        # 正弦波弹性摆动
        swing_phase = anim_t * (2.8 + i * 0.6) + i * 1.2
        swing_amp = radius * 0.08 * rng_tent.uniform(0.6, 1.2)

        # 贝塞尔曲线控制点
        cp1_x = base_x + swing_amp * math.sin(swing_phase)
        cp1_y = base_y + tent_len * 0.33
        cp2_x = base_x + swing_amp * 1.8 * math.sin(swing_phase + 0.7)
        cp2_y = base_y + tent_len * 0.66
        tip_x = base_x + swing_amp * 2.2 * math.sin(swing_phase + 1.4)
        tip_y = base_y + tent_len

        path = QPainterPath()
        path.moveTo(base_x, base_y)
        path.cubicTo(cp1_x, cp1_y, cp2_x, cp2_y, tip_x, tip_y)

        # 触手粗细渐变：根部粗、尖端细
        grad = QLinearGradient(base_x, base_y, tip_x, tip_y)
        grad.setColorAt(0.0, QColor(50, 180, 160, 90))
        grad.setColorAt(0.35, QColor(40, 160, 150, 75))
        grad.setColorAt(0.7, QColor(30, 130, 130, 50))
        grad.setColorAt(1.0, QColor(15, 80, 90, 20))
        pen = QPen(grad, 2.8 * s)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawPath(path)

        # 内层亮线（半透明细线，增加层次感）
        inner_pen = QPen(QColor(100, 230, 210, 40), 0.8 * s)
        inner_pen.setCapStyle(Qt.RoundCap)
        p.setPen(inner_pen)
        p.drawPath(path)

        # 触手上发光点/吸盘（沿触手随机分布）
        suckers = 5 + rng_tent.randint(0, 3)
        for j in range(suckers):
            t = 0.18 + (j / (suckers - 1)) * 0.62 if suckers > 1 else 0.4
            # 贝塞尔曲线插值
            t1 = 1.0 - t
            sx = t1*t1*t1 * base_x + 3*t1*t1*t * cp1_x + 3*t1*t*t * cp2_x + t*t*t * tip_x
            sy = t1*t1*t1 * base_y + 3*t1*t1*t * cp1_y + 3*t1*t*t * cp2_y + t*t*t * tip_y
            sucker_r = 1.8 * s * rng_tent.uniform(0.5, 1.2)
            sucker_alpha = int(80 + rng_tent.randint(-20, 40))
            sg = QRadialGradient(sx, sy, sucker_r * 1.5)
            sg.setColorAt(0.0, QColor(120, 255, 220, sucker_alpha))
            sg.setColorAt(0.5, QColor(60, 200, 180, int(sucker_alpha * 0.6)))
            sg.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setBrush(sg); p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(sx, sy), sucker_r, sucker_r)

    # ── 伞顶内部生物荧光点 ──
    glow_count = 10
    rng_glow = random.Random(int(anim_t * 97) % 100000 + 888)
    for _ in range(glow_count):
        gangle = rng_glow.uniform(0.1, math.pi - 0.1)
        gdist = rng_glow.uniform(umbrella_rx * 0.15, umbrella_rx * 0.78)
        gx = jcx + math.cos(gangle) * gdist
        gy = umbrella_top + umbrella_ry - math.sin(gangle) * gdist * (umbrella_ry / umbrella_rx)
        gs = s * rng_glow.uniform(0.6, 1.8)
        ga = int(30 + rng_glow.randint(0, 50))
        pg = QRadialGradient(gx, gy, gs * 2)
        pg.setColorAt(0.0, QColor(140, 255, 220, ga))
        pg.setColorAt(0.6, QColor(80, 220, 190, int(ga * 0.4)))
        pg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(pg); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(gx, gy), gs, gs)

    # ── 环绕粒子光环（主题色匹配）──
    aura_rng = random.Random(int(anim_t * 280) % 100000 + 22250)
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
        ag.setColorAt(0.0, QColor(80, 240, 200, a_alpha))
        ag.setColorAt(0.5, QColor(80//2, 240//2, 230, a_alpha // 2))
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
            ig.setColorAt(0.78, QColor(80, 240, 200, ga // 2))
            ig.setColorAt(0.90, QColor(80, 240, 200, ga))
            ig.setColorAt(0.97, QColor(80//2, 240//2, 230, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        # 外层扩散光晕
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(80, 240, 200, ga // 2))
            og.setColorAt(0.96, QColor(80//2, 240//2, 240, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)
        # 明亮轮廓环（呼吸感）
        br = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
        rpen = QPen(QColor(80, 240, 200, int(220 * hp * br)), 2.5 + 1.0 * br)
        p.setPen(rpen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 3, radius + 3)


    p.restore()
