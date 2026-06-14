# `core/shapes/reptilian.py`

> 路径：`core/shapes/reptilian.py` | 行数：165


---


```python
# -*- coding: utf-8 -*-
"""
蜥蜴人 — 鳞片纹理 + 竖瞳 + 缓慢眨眼 + 分叉舌伸缩
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
    head_r = radius * 0.55
    head_cx = cx
    head_cy = cy - radius * 0.15

    # ── 背景辉光 ──
    glow = QRadialGradient(cx, cy, radius * 1.05)
    glow.setColorAt(0.0, QColor(80, 160, 60, 20))
    glow.setColorAt(0.7, QColor(40, 100, 30, 8))
    glow.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(glow); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius * 1.05, radius * 1.05)

    # ── 头部（椭圆，略尖）──
    head_path = QPainterPath()
    head_path.moveTo(head_cx - head_r * 0.75, head_cy)
    head_path.cubicTo(
        head_cx - head_r * 0.78, head_cy - head_r * 0.55,
        head_cx + head_r * 0.78, head_cy - head_r * 0.55,
        head_cx + head_r * 0.75, head_cy
    )
    head_path.cubicTo(
        head_cx + head_r * 0.60, head_cy + head_r * 0.65,
        head_cx + head_r * 0.20, head_cy + head_r * 0.90,
        head_cx, head_cy + head_r * 0.85
    )
    head_path.cubicTo(
        head_cx - head_r * 0.20, head_cy + head_r * 0.90,
        head_cx - head_r * 0.60, head_cy + head_r * 0.65,
        head_cx - head_r * 0.75, head_cy
    )
    head_grad = QRadialGradient(head_cx, head_cy, head_r * 0.95)
    head_grad.setColorAt(0.0, QColor(90, 150, 55))
    head_grad.setColorAt(0.4, QColor(55, 110, 30))
    head_grad.setColorAt(0.75, QColor(35, 80, 20))
    head_grad.setColorAt(1.0, QColor(20, 55, 12))
    p.setBrush(head_grad); p.setPen(QPen(QColor(15, 40, 8), 1.5 * s))
    p.drawPath(head_path)

    # ── 鳞片纹理（小椭圆叠印）──
    scale_rng = random.Random(9876)
    p.setPen(Qt.NoPen)
    for _ in range(40):
        sx = head_cx + scale_rng.uniform(-head_r * 0.65, head_r * 0.65)
        sy = head_cy + scale_rng.uniform(-head_r * 0.55, head_r * 0.55)
        sr = scale_rng.uniform(1.0, 3.0) * s
        sa = scale_rng.randint(15, 40)
        p.setBrush(QColor(30, 70, 18, sa))
        p.drawEllipse(QPointF(sx, sy), sr, sr * 0.6)

    # ── 高光 ──
    hl = QRadialGradient(head_cx - head_r * 0.2, head_cy - head_r * 0.3, head_r * 0.25)
    hl.setColorAt(0.0, QColor(130, 190, 80, 45))
    hl.setColorAt(0.5, QColor(100, 160, 60, 10))
    hl.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(hl); p.setPen(Qt.NoPen)
    p.drawPath(head_path)

    # ── 眼睛（竖瞳，缓慢眨眼）──
    blink_phase = (anim_t * 0.45) % 5.0
    blink = 1.0
    if blink_phase < 0.15:
        blink = blink_phase / 0.15
    elif blink_phase > 4.85:
        blink = (5.0 - blink_phase) / 0.15

    for sign in (-1, 1):
        ex = head_cx + sign * head_r * 0.22
        ey = head_cy - head_r * 0.12
        # 眼白（黄绿）
        eye_grad = QRadialGradient(ex, ey, head_r * 0.15)
        eye_grad.setColorAt(0.0, QColor(220, 240, 100))
        eye_grad.setColorAt(0.7, QColor(180, 200, 60))
        eye_grad.setColorAt(1.0, QColor(100, 130, 20))
        p.setBrush(eye_grad); p.setPen(QPen(QColor(30, 70, 10), 0.8 * s))
        p.drawEllipse(QRectF(ex - head_r * 0.14, ey - head_r * 0.20 * blink,
                              head_r * 0.28, head_r * 0.40 * blink))
        # 竖瞳（窄椭圆黑色）
        if blink > 0.2:
            pupil_rx = head_r * 0.04
            pupil_ry = head_r * 0.15 * blink
            p.setBrush(QColor(5, 10, 0))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(ex, ey), pupil_rx, pupil_ry)

    # ── 鼻孔 ──
    for sign in (-1, 1):
        nx = head_cx + sign * head_r * 0.12
        ny = head_cy + head_r * 0.18
        p.setBrush(QColor(20, 45, 10))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(nx, ny), head_r * 0.05, head_r * 0.03)

    # ── 嘴巴 + 分叉舌伸缩 ──
    mouth_path = QPainterPath()
    mouth_cx = head_cx
    mouth_cy = head_cy + head_r * 0.38
    mouth_path.moveTo(mouth_cx - head_r * 0.25, mouth_cy)
    mouth_path.quadTo(mouth_cx, mouth_cy + head_r * 0.06, mouth_cx + head_r * 0.25, mouth_cy)
    p.setPen(QPen(QColor(15, 35, 8), 1.0 * s))
    p.setBrush(Qt.NoBrush)
    p.drawPath(mouth_path)

    # 分叉舌（周期性伸缩）
    tongue_phase = (anim_t * 1.2) % 6.0
    tongue_extend = 0.0
    if tongue_phase < 0.5:
        tongue_extend = tongue_phase / 0.5
    elif 2.5 < tongue_phase < 3.0:
        tongue_extend = (3.0 - tongue_phase) / 0.5
    if tongue_extend > 0:
        tongue_len = head_r * 0.45 * tongue_extend
        tongue_path = QPainterPath()
        tongue_path.moveTo(mouth_cx, mouth_cy)
        tongue_path.lineTo(mouth_cx, mouth_cy + tongue_len * 0.7)
        # 分叉
        fork_width = tongue_len * 0.3
        tongue_path.moveTo(mouth_cx, mouth_cy + tongue_len * 0.5)
        tongue_path.lineTo(mouth_cx - fork_width, mouth_cy + tongue_len)
        tongue_path.moveTo(mouth_cx, mouth_cy + tongue_len * 0.5)
        tongue_path.lineTo(mouth_cx + fork_width, mouth_cy + tongue_len)
        p.setPen(QPen(QColor(180, 60, 40), 1.8 * s))
        p.setBrush(Qt.NoBrush)
        p.drawPath(tongue_path)

    # ── 身体（肩宽下窄）──
    body_cx = head_cx
    body_cy = cy + radius * 0.40
    body_rx = head_r * 0.55
    body_ry = head_r * 0.45
    body_grad = QRadialGradient(body_cx, body_cy - body_ry * 0.1, body_rx * 1.1)
    body_grad.setColorAt(0.0, QColor(80, 140, 45))
    body_grad.setColorAt(0.6, QColor(45, 100, 25))
    body_grad.setColorAt(1.0, QColor(25, 65, 15))
    p.setBrush(body_grad); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), body_rx, body_ry)

    # ── 悬停 ──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        p.setPen(QPen(QColor(100, 200, 70, int(200 * hp)), 2.0 * s))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 2, radius + 2)

    p.restore()

```
