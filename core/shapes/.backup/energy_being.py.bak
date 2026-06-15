# -*- coding: utf-8 -*-
"""
能量体 — 半透明人形轮廓 + 脉冲光晕 + 色彩循环变幻
"""
import math, random
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import (
    QPainter, QRadialGradient, QColor, QPen, QBrush, QPainterPath
)


def _hsla(h, s, l, a):
    """简单 HSL→RGB 转换，返回 QColor"""
    import colorsys
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l / 100.0, s / 100.0)
    return QColor(int(r * 255), int(g * 255), int(b * 255), a)


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
    s = radius / 50.0
    head_r = radius * 0.45

    # ── 色彩循环（慢速旋转色相）──
    hue = (anim_t * 15.0) % 360.0
    hue2 = (hue + 120) % 360.0
    hue3 = (hue + 240) % 360.0

    # ── 外层脉冲光晕 ──
    for i in range(3):
        pulse_r = radius * (0.8 + i * 0.35)
        pulse_phase = anim_t * (2.0 + i * 0.6)
        pulse_strength = 0.5 + 0.5 * abs(math.sin(pulse_phase))
        hi = (hue + i * 40) % 360.0
        glow = QRadialGradient(cx, cy, pulse_r)
        glow.setColorAt(0.0, _hsla(hi, 90, 30, int(15 * pulse_strength)))
        glow.setColorAt(0.5, _hsla(hi, 80, 20, int(8 * pulse_strength)))
        glow.setColorAt(0.8, _hsla(hi, 60, 12, int(3 * pulse_strength)))
        glow.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(glow); p.setPen(Qt.NoPen)
        p.drawEllipse(center, pulse_r, pulse_r)

    # ── 粒子带（环绕身体的粒子）──
    part_rng = random.Random(int(anim_t * 200) % 100000 + 3333)
    p.setPen(Qt.NoPen)
    for _ in range(30):
        pa = part_rng.uniform(0, 2 * math.pi) + anim_t * 1.5
        pd = radius * part_rng.uniform(0.5, 1.1)
        px = cx + math.cos(pa) * pd
        py = cy + math.sin(pa) * pd
        ps = part_rng.uniform(0.5, 1.5)
        ph = (hue + part_rng.uniform(-30, 30)) % 360.0
        pg = QRadialGradient(px, py, ps * 2.5)
        pg.setColorAt(0.0, _hsla(ph, 100, 60, 100))
        pg.setColorAt(0.4, _hsla(ph, 80, 40, 50))
        pg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(pg)
        p.drawEllipse(QPointF(px, py), ps * 2.5, ps * 2.5)

    # ── 人形轮廓（半透明）──
    head_cx = cx
    head_cy = cy - radius * 0.35

    # 头部椭圆
    body_alpha = 60 + int(20 * abs(math.sin(anim_t * 1.3)))
    head_grad = QRadialGradient(head_cx, head_cy - head_r * 0.1, head_r * 0.7)
    head_grad.setColorAt(0.0, _hsla(hue, 80, 50, body_alpha + 15))
    head_grad.setColorAt(0.5, _hsla(hue2, 60, 35, body_alpha))
    head_grad.setColorAt(1.0, _hsla(hue3, 40, 20, body_alpha // 2))
    p.setBrush(head_grad); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(head_cx, head_cy), head_r * 0.7, head_r * 0.75)

    # 身体（椭圆）
    body_cx = cx
    body_cy = cy + radius * 0.05
    body_rx = head_r * 0.55
    body_ry = head_r * 0.70
    body_grad = QRadialGradient(body_cx, body_cy - body_ry * 0.15, body_rx * 1.2)
    body_grad.setColorAt(0.0, _hsla(hue2, 70, 45, body_alpha + 10))
    body_grad.setColorAt(0.5, _hsla(hue, 55, 30, body_alpha))
    body_grad.setColorAt(1.0, _hsla(hue3, 35, 18, body_alpha // 2))
    p.setBrush(body_grad); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), body_rx, body_ry)

    # 肩膀连接
    for sign in (-1, 1):
        shx = body_cx + sign * body_rx * 0.9
        shy = body_cy - body_ry * 0.55
        sh_grad = QRadialGradient(shx, shy, head_r * 0.25)
        sh_grad.setColorAt(0.0, _hsla(hue, 60, 40, body_alpha))
        sh_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(sh_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(shx, shy), head_r * 0.25, head_r * 0.25)

    # ── 光眼（两个亮点）──
    eye_y = head_cy - head_r * 0.05
    for sign in (-1, 1):
        ex = head_cx + sign * head_r * 0.25
        ee_grad = QRadialGradient(ex, eye_y, head_r * 0.22)
        ee_grad.setColorAt(0.0, QColor(255, 255, 255, 200))
        ee_grad.setColorAt(0.2, _hsla(hue, 30, 80, 160))
        ee_grad.setColorAt(0.5, _hsla(hue, 40, 50, 80))
        ee_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(ee_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, eye_y), head_r * 0.22, head_r * 0.20)

    # ── 中心核心光点 ──
    core_pulse = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
    core = QRadialGradient(body_cx, body_cy - body_ry * 0.1, head_r * 0.2)
    core.setColorAt(0.0, QColor(255, 255, 255, int(200 * core_pulse)))
    core.setColorAt(0.3, _hsla(hue, 50, 80, int(140 * core_pulse)))
    core.setColorAt(0.6, _hsla(hue2, 40, 50, int(60 * core_pulse)))
    core.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(core); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy - body_ry * 0.1), head_r * 0.2, head_r * 0.2)

    # ── 环绕粒子光环（主题色匹配）──
    aura_rng = random.Random(int(anim_t * 280) % 100000 + 6325)
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
        ag.setColorAt(0.0, QColor(180, 140, 255, a_alpha))
        ag.setColorAt(0.5, QColor(180//2, 140//2, 255, a_alpha // 2))
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
            ig.setColorAt(0.78, QColor(180, 140, 255, ga // 2))
            ig.setColorAt(0.90, QColor(180, 140, 255, ga))
            ig.setColorAt(0.97, QColor(180//2, 140//2, 255, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        # 外层扩散光晕
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(180, 140, 255, ga // 2))
            og.setColorAt(0.96, QColor(180//2, 140//2, 255, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)
        # 明亮轮廓环（呼吸感）
        br = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
        rpen = QPen(QColor(180, 140, 255, int(220 * hp * br)), 2.5 + 1.0 * br)
        p.setPen(rpen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 3, radius + 3)


    p.restore()
