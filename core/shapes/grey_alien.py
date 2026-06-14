# -*- coding: utf-8 -*-
"""
灰人 — 经典大头大眼灰皮 + 细长手指 + 缓慢眨眼
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

    s = radius / 50.0
    head_r = radius * 0.58
    head_cy = cy - radius * 0.18
    head_cx = cx

    # ── 背景辉光（冷灰）──
    glow = QRadialGradient(cx, cy, radius * 1.1)
    glow.setColorAt(0.0, QColor(120, 130, 140, 25))
    glow.setColorAt(0.6, QColor(80, 85, 95, 10))
    glow.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(glow); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius * 1.1, radius * 1.1)

    # ── 头部（倒梨形：上大下小）──
    head_path = QPainterPath()
    head_top = head_cy - head_r * 0.95
    head_bot = head_cy + head_r * 0.75
    head_w_top = head_r * 0.85
    head_w_mid = head_r * 0.72
    head_w_bot = head_r * 0.40
    head_path.moveTo(head_cx - head_w_mid, head_cy - head_r * 0.1)
    head_path.cubicTo(
        head_cx - head_w_top, head_cy - head_r * 0.6,
        head_cx - head_w_top, head_cy - head_r * 0.8,
        head_cx, head_top
    )
    head_path.cubicTo(
        head_cx + head_w_top, head_cy - head_r * 0.8,
        head_cx + head_w_top, head_cy - head_r * 0.6,
        head_cx + head_w_mid, head_cy - head_r * 0.1
    )
    head_path.cubicTo(
        head_cx + head_w_bot, head_cy + head_r * 0.3,
        head_cx + head_w_bot * 0.6, head_bot,
        head_cx, head_bot
    )
    head_path.cubicTo(
        head_cx - head_w_bot * 0.6, head_bot,
        head_cx - head_w_bot, head_cy + head_r * 0.3,
        head_cx - head_w_mid, head_cy - head_r * 0.1
    )
    head_grad = QRadialGradient(head_cx, head_cy - head_r * 0.2, head_r * 0.9)
    head_grad.setColorAt(0.0, QColor(185, 190, 195))
    head_grad.setColorAt(0.4, QColor(155, 160, 165))
    head_grad.setColorAt(0.75, QColor(125, 130, 138))
    head_grad.setColorAt(1.0, QColor(95, 100, 108))
    p.setBrush(head_grad); p.setPen(QPen(QColor(80, 85, 90), 1.2 * s))
    p.drawPath(head_path)

    # ── 高光 ──
    hl_grad = QRadialGradient(head_cx - head_r * 0.2, head_cy - head_r * 0.35, head_r * 0.3)
    hl_grad.setColorAt(0.0, QColor(210, 215, 220, 60))
    hl_grad.setColorAt(0.5, QColor(190, 195, 200, 15))
    hl_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(hl_grad); p.setPen(Qt.NoPen)
    p.drawPath(head_path)

    # ── 眼睛（极大，纯黑倾斜椭圆）──
    eye_spacing = head_r * 0.28
    eye_rx = head_r * 0.26
    eye_ry = head_r * 0.38
    eye_tilt = -8  # 外上角倾斜

    # 缓慢眨眼（每 4 秒眨一次）
    blink_phase = (anim_t * 0.5) % 4.0
    blink = 1.0
    if blink_phase < 0.2:
        blink = blink_phase / 0.2
    elif blink_phase > 3.8:
        blink = (4.0 - blink_phase) / 0.2

    for sign in (-1, 1):
        ex = head_cx + sign * eye_spacing
        ey = head_cy - head_r * 0.08
        p.save()
        p.translate(ex, ey)
        p.rotate(sign * eye_tilt)
        # 眼黑
        eye_grad = QRadialGradient(0, 0, eye_rx * 0.9)
        eye_grad.setColorAt(0.0, QColor(30, 30, 35))
        eye_grad.setColorAt(0.6, QColor(10, 10, 12))
        eye_grad.setColorAt(1.0, QColor(0, 0, 0))
        p.setBrush(eye_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(-eye_rx, -eye_ry * blink, eye_rx * 2, eye_ry * 2 * blink))
        # 反光高光点
        if blink > 0.3:
            pt_grad = QRadialGradient(-eye_rx * 0.35, -eye_ry * 0.35, eye_rx * 0.2)
            pt_grad.setColorAt(0.0, QColor(255, 255, 255, 160))
            pt_grad.setColorAt(0.6, QColor(200, 210, 215, 50))
            pt_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setBrush(pt_grad)
            p.drawEllipse(QPointF(-eye_rx * 0.35, -eye_ry * 0.35), eye_rx * 0.2, eye_ry * blink * 0.2)
        p.restore()

    # ── 小鼻孔 ──
    for sign in (-1, 1):
        nx = head_cx + sign * head_r * 0.10
        ny = head_cy + head_r * 0.25
        p.setBrush(QColor(75, 80, 85))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(nx, ny), head_r * 0.045, head_r * 0.03)

    # ── 细线嘴（微抿）──
    mouth_path = QPainterPath()
    mouth_path.moveTo(head_cx - head_r * 0.18, head_cy + head_r * 0.40)
    mouth_path.quadTo(head_cx, head_cy + head_r * 0.48, head_cx + head_r * 0.18, head_cy + head_r * 0.40)
    p.setPen(QPen(QColor(70, 75, 80), 0.8 * s))
    p.setBrush(Qt.NoBrush)
    p.drawPath(mouth_path)

    # ── 身体（瘦长椭圆）──
    body_cx = head_cx
    body_cy = cy + radius * 0.42
    body_rx = head_r * 0.42
    body_ry = head_r * 0.50
    body_grad = QRadialGradient(body_cx, body_cy - body_ry * 0.2, body_rx * 1.1)
    body_grad.setColorAt(0.0, QColor(160, 165, 170))
    body_grad.setColorAt(0.6, QColor(130, 135, 142))
    body_grad.setColorAt(1.0, QColor(100, 105, 112))
    p.setBrush(body_grad); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), body_rx, body_ry)

    # ── 细长胳膊 ──
    for sign in (-1, 1):
        arm_path = QPainterPath()
        shoulder_x = body_cx + sign * body_rx * 0.85
        shoulder_y = body_cy - body_ry * 0.25
        arm_path.moveTo(shoulder_x, shoulder_y)
        elbow_x = shoulder_x + sign * body_rx * 1.5
        elbow_y = body_cy + body_ry * 0.2
        arm_path.quadTo(
            shoulder_x + sign * body_rx * 0.8, shoulder_y + body_ry * 0.3,
            elbow_x, elbow_y
        )
        p.setPen(QPen(QColor(130, 135, 142), 2.5 * s))
        p.setBrush(Qt.NoBrush)
        p.drawPath(arm_path)
        # 细长手指（3根）
        for fi in range(3):
            finger_path = QPainterPath()
            f_angle = -sign * 0.4 + fi * sign * 0.4
            f_len = body_rx * 1.1
            f_tip_x = elbow_x + math.cos(f_angle + math.pi / 2) * f_len
            f_tip_y = elbow_y + math.sin(f_angle + math.pi / 2) * f_len
            finger_path.moveTo(elbow_x, elbow_y)
            finger_path.lineTo(f_tip_x, f_tip_y)
            p.setPen(QPen(QColor(120, 125, 130), 1.2 * s))
            p.drawPath(finger_path)

    # ── 悬停 ──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        p.setPen(QPen(QColor(140, 150, 160, int(200 * hp)), 2.0 * s))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 2, radius + 2)

    p.restore()
