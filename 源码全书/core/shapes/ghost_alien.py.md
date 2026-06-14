# `core/shapes/ghost_alien.py`

> 路径：`core/shapes/ghost_alien.py` | 行数：183


---


```python
# -*- coding: utf-8 -*-
"""
幽灵外星人 — 半透明飘浮 + 边缘模糊 + 正弦波时隐时现 + 磷火粒子
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

    s = radius / 48.0

    # ── 浮动 ──
    float_y = math.sin(anim_t * 1.3) * radius * 0.10
    float_x = math.cos(anim_t * 0.9) * radius * 0.06
    body_cx = cx + float_x
    body_cy = cy + float_y

    # ── 身体正弦闪烁 alpha（0.3 - 0.7）──
    ghost_alpha = 0.50 + 0.20 * math.sin(anim_t * 2.5)

    # ── 头部半径 ──
    head_r = radius * 0.42
    head_cy = body_cy - radius * 0.15

    # ── 外层模糊辉光（多层，模拟边缘柔化）──
    for i in range(3):
        glow_r = head_r * (1.2 + i * 0.30)
        glow = QRadialGradient(body_cx, head_cy, glow_r)
        ga = int(40 - i * 12)
        glow.setColorAt(0.0, QColor(160, 210, 255, ga))
        glow.setColorAt(0.3, QColor(120, 180, 240, int(ga * 0.7)))
        glow.setColorAt(0.6, QColor(80, 140, 220, int(ga * 0.4)))
        glow.setColorAt(0.85, QColor(40, 80, 180, int(ga * 0.15)))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(glow); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(body_cx, head_cy), glow_r, glow_r)

    # ── 身体（类人形斗篷：上窄下宽弧形）──
    body_path = QPainterPath()
    body_top_y = head_cy + head_r * 0.60
    body_bot_y = head_cy + head_r * 1.60
    body_top_w = head_r * 0.50
    body_bot_w = head_r * 0.85
    body_mid_y = head_cy + head_r * 0.95

    body_path.moveTo(body_cx - body_top_w, body_top_y)
    body_path.cubicTo(
        body_cx - body_top_w * 1.1, body_mid_y,
        body_cx - body_bot_w * 1.0, body_bot_y - head_r * 0.15,
        body_cx - body_bot_w * 0.5, body_bot_y
    )
    body_path.quadTo(body_cx, body_bot_y + head_r * 0.12,
                     body_cx + body_bot_w * 0.5, body_bot_y)
    body_path.cubicTo(
        body_cx + body_bot_w * 1.0, body_bot_y - head_r * 0.15,
        body_cx + body_top_w * 1.1, body_mid_y,
        body_cx + body_top_w, body_top_y
    )
    body_path.closeSubpath()

    body_grad = QLinearGradient(body_cx, body_top_y, body_cx, body_bot_y)
    body_grad.setColorAt(0.0, QColor(180, 220, 255, int(200 * ghost_alpha)))
    body_grad.setColorAt(0.4, QColor(140, 190, 240, int(160 * ghost_alpha)))
    body_grad.setColorAt(0.7, QColor(100, 150, 220, int(110 * ghost_alpha)))
    body_grad.setColorAt(1.0, QColor(40, 80, 180, int(30 * ghost_alpha)))
    p.setBrush(body_grad); p.setPen(Qt.NoPen)
    p.drawPath(body_path)

    # ── 头部（椭圆形，浅蓝白半透明）──
    head_path = QPainterPath()
    head_ry = head_r * 0.85
    head_path.addEllipse(QPointF(body_cx, head_cy), head_r, head_ry)
    head_grad = QRadialGradient(body_cx - head_r * 0.12, head_cy - head_ry * 0.12, head_r)
    head_grad.setColorAt(0.0, QColor(220, 240, 255, int(220 * ghost_alpha)))
    head_grad.setColorAt(0.35, QColor(180, 220, 250, int(180 * ghost_alpha)))
    head_grad.setColorAt(0.65, QColor(130, 180, 230, int(140 * ghost_alpha)))
    head_grad.setColorAt(0.88, QColor(70, 120, 200, int(80 * ghost_alpha)))
    head_grad.setColorAt(1.0, QColor(20, 50, 120, int(20 * ghost_alpha)))
    p.setBrush(head_grad); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, head_cy), head_r, head_ry)

    # ── 眼睛（深色空洞，无瞳孔 — 幽灵质感）──
    eye_spacing = head_r * 0.26
    eye_r = head_r * 0.10
    for sign in (-1, 1):
        ex = body_cx + sign * eye_spacing
        ey = head_cy - head_ry * 0.05
        eye_grad = QRadialGradient(ex, ey, eye_r * 1.3)
        eye_grad.setColorAt(0.0, QColor(10, 15, 40, int(200 * ghost_alpha)))
        eye_grad.setColorAt(0.5, QColor(20, 30, 60, int(140 * ghost_alpha)))
        eye_grad.setColorAt(1.0, QColor(80, 130, 200, 0))
        p.setBrush(eye_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, ey), eye_r, eye_r)

    # ── 嘴（小椭圆开口 — 惊讶状）──
    mouth_y = head_cy + head_ry * 0.28
    mouth_rx = head_r * 0.10
    mouth_ry = head_r * 0.08
    mouth_grad = QRadialGradient(body_cx, mouth_y, mouth_ry * 1.2)
    mouth_grad.setColorAt(0.0, QColor(10, 15, 40, int(180 * ghost_alpha)))
    mouth_grad.setColorAt(0.6, QColor(20, 30, 60, int(100 * ghost_alpha)))
    mouth_grad.setColorAt(1.0, QColor(80, 130, 200, 0))
    p.setBrush(mouth_grad); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, mouth_y), mouth_rx, mouth_ry)

    # ── 头部高光 ──
    head_spec = QRadialGradient(body_cx - head_r * 0.22, head_cy - head_ry * 0.22, head_r * 0.28)
    head_spec.setColorAt(0.0, QColor(255, 255, 255, int(70 * ghost_alpha)))
    head_spec.setColorAt(0.6, QColor(220, 240, 255, int(20 * ghost_alpha)))
    head_spec.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(head_spec); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, head_cy), head_r, head_ry)

    # ── 磷火粒子（2-3颗蓝绿冷光点，缓慢漂移）──
    wisp_rng = random.Random(91)
    wisp_count = 3
    for i in range(wisp_count):
        base_angle = i * 2 * math.pi / wisp_count + anim_t * 0.35
        orbit_r = radius * wisp_rng.uniform(0.65, 0.95)
        wobble = math.sin(anim_t * 1.8 + i * 2.1) * radius * 0.12
        wx = body_cx + math.cos(base_angle) * orbit_r + math.cos(anim_t * 0.7 + i) * wobble
        wy = body_cy + math.sin(base_angle) * orbit_r * 0.65 + math.sin(anim_t * 0.6 + i) * wobble

        # 磷火脉冲
        wisp_pulse = 0.5 + 0.5 * math.sin(anim_t * 3.5 + i * 2.0)
        wisp_size = radius * 0.04 * (0.8 + 0.4 * wisp_pulse)

        # 多层辉光（模拟冷焰）
        for layer in range(3):
            lr = wisp_size * (1.0 + layer * 1.2)
            la = int((60 - layer * 18) * wisp_pulse)
            wg = QRadialGradient(wx, wy, lr)
            wg.setColorAt(0.0, QColor(120, 255, 200, la))
            wg.setColorAt(0.25, QColor(80, 220, 180, int(la * 0.7)))
            wg.setColorAt(0.55, QColor(40, 160, 140, int(la * 0.35)))
            wg.setColorAt(0.80, QColor(10, 80, 80, int(la * 0.12)))
            wg.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setBrush(wg); p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(wx, wy), lr, lr)

        # 磷火核心
        core_grad = QRadialGradient(wx, wy, wisp_size * 0.6)
        core_grad.setColorAt(0.0, QColor(200, 255, 230, int(180 * wisp_pulse)))
        core_grad.setColorAt(0.5, QColor(140, 240, 200, int(100 * wisp_pulse)))
        core_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(core_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(wx, wy), wisp_size * 0.6, wisp_size * 0.6)

    # ── 幽灵尾迹（底部渐隐拖尾粒子）──
    trail_rng = random.Random(int(anim_t * 200) % 100000 + 442)
    p.setPen(Qt.NoPen)
    for _ in range(6):
        ta = trail_rng.uniform(-0.4, 0.4) + math.pi / 2
        td = radius * trail_rng.uniform(0.45, 0.95)
        tx = body_cx + math.cos(ta) * td
        ty = body_cy + math.sin(ta) * td + radius * 0.15
        ts = trail_rng.uniform(0.4, 1.5)
        tg = QRadialGradient(tx, ty, ts * 2.5)
        tg.setColorAt(0.0, QColor(140, 200, 250, int(30 * ghost_alpha)))
        tg.setColorAt(0.5, QColor(80, 150, 220, int(15 * ghost_alpha)))
        tg.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(tg)
        p.drawEllipse(QPointF(tx, ty), ts * 2.5, ts * 2.5)

    # ── 悬停 ──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        p.setPen(QPen(QColor(140, 200, 240, int(200 * hp)), 2.0 * s))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 2, radius + 2)

    p.restore()

```
