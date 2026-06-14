# -*- coding: utf-8 -*-
"""
白矮星 — 极亮白核 + 电子简并辉光 + 渐变蓝白外晕
"""
import math, random
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import (
    QPainter, QRadialGradient, QColor, QPen, QBrush
)


def paint(painter: QPainter, center: QPointF, radius: float,
          anim_t: float, hovered: bool, alpha: float):
    cx, cy = center.x(), center.y()
    p = painter
    p.save()
    if alpha < 1.0:
        p.setOpacity(alpha)

    # ── 外层简并辉光（蓝白→无色大范围渐晕）──
    for i in range(4):
        gr = radius * (1.1 + i * 0.45)
        glow = QRadialGradient(cx, cy, gr)
        ga = int((45 - i * 10) * (0.8 + 0.2 * abs(math.sin(anim_t * 0.8))))
        glow.setColorAt(0.0, QColor(180, 210, 255, 0))
        glow.setColorAt(0.30, QColor(140, 180, 255, ga // 2))
        glow.setColorAt(0.50, QColor(100, 140, 240, ga))
        glow.setColorAt(0.70, QColor(60, 90, 200, ga // 2))
        glow.setColorAt(0.88, QColor(30, 50, 150, ga // 4))
        glow.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(glow); p.setPen(Qt.NoPen)
        p.drawEllipse(center, gr, gr)

    # ── 炽白核心 ──
    core = QRadialGradient(cx, cy, radius * 0.55)
    core.setColorAt(0.0, QColor(255, 255, 255))
    core.setColorAt(0.05, QColor(255, 255, 255))
    core.setColorAt(0.15, QColor(245, 250, 255))
    core.setColorAt(0.30, QColor(210, 230, 255))
    core.setColorAt(0.50, QColor(150, 195, 255))
    core.setColorAt(0.70, QColor(90, 140, 235))
    core.setColorAt(0.85, QColor(40, 80, 190))
    core.setColorAt(1.0, QColor(10, 30, 100))
    p.setBrush(core); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 电子简并密度分层环（暗纹环带）──
    for i in range(3):
        ring_r = radius * (0.60 + i * 0.13)
        ring_grad = QRadialGradient(cx, cy, ring_r + radius * 0.04)
        ra = 40 - i * 10
        ring_grad.setColorAt(0.0, QColor(255, 255, 255, 0))
        ring_grad.setColorAt(0.40, QColor(255, 255, 255, 0))
        ring_grad.setColorAt(0.55, QColor(60, 100, 200, ra))
        ring_grad.setColorAt(0.65, QColor(30, 60, 160, ra // 2))
        ring_grad.setColorAt(0.80, QColor(255, 255, 255, 0))
        ring_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(ring_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(center, ring_r + radius * 0.04, ring_r + radius * 0.04)

    # ── 表面微闪斑点（量子真空涨落闪烁）──
    spark_rng = random.Random(int(anim_t * 600) % 100000 + 777)
    p.setPen(Qt.NoPen)
    for _ in range(20):
        sa2 = spark_rng.uniform(0, 2 * math.pi)
        sd2 = spark_rng.uniform(0.10, 0.90) * radius
        sx2 = cx + math.cos(sa2) * sd2
        sy2 = cy + math.sin(sa2) * sd2
        ss2 = spark_rng.uniform(0.3, 1.5)
        sa3 = int(40 + 150 * spark_rng.random())
        sg = QRadialGradient(sx2, sy2, ss2 * 2.5)
        sg.setColorAt(0.0, QColor(255, 255, 255, sa3))
        sg.setColorAt(0.5, QColor(220, 235, 255, sa3 // 3))
        sg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(sg)
        p.drawEllipse(QPointF(sx2, sy2), ss2 * 2.5, ss2 * 2.5)

    # ── 高光 ──
    spec = QRadialGradient(cx - radius * 0.28, cy - radius * 0.32, radius * 0.32)
    spec.setColorAt(0.0, QColor(255, 255, 255, 100))
    spec.setColorAt(0.3, QColor(255, 255, 255, 45))
    spec.setColorAt(0.6, QColor(240, 250, 255, 15))
    spec.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(spec); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 悬停 ──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        p.setPen(QPen(QColor(200, 230, 255, int(200 * hp)), 2.0))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 2, radius + 2)

    p.restore()
