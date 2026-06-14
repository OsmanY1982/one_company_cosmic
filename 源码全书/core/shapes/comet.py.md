# `core/shapes/comet.py`

> 路径：`core/shapes/comet.py` | 行数：162


---


```python
# -*- coding: utf-8 -*-
"""
彗星 — 冰蓝彗核 + 多段拖尾粒子 + 尾部摆动
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

    # 彗星方向（向右上飞掠），尾巴在左下方
    comet_angle = math.radians(-40)  # 飞行方向
    tail_angle = comet_angle + math.pi  # 尾巴方向（反方向）

    # ── 彗发辉光（球体周围的冰蓝光晕）──
    coma_radius = radius * 1.1
    for i in range(4):
        cr = coma_radius * (0.9 + i * 0.30)
        coma = QRadialGradient(cx, cy, cr)
        ca = max(0, 55 - i * 12)
        coma.setColorAt(0.0, QColor(180, 220, 255, 0))
        coma.setColorAt(0.3, QColor(140, 200, 255, ca))
        coma.setColorAt(0.6, QColor(80, 160, 240, ca // 2))
        coma.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(coma); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx, cy), cr, cr)

    # ── 彗核（冰蓝白渐变球体）──
    core_r = radius * 0.55
    core = QRadialGradient(cx - core_r * 0.2, cy - core_r * 0.25, core_r * 1.05)
    core.setColorAt(0.0, QColor(220, 240, 255))
    core.setColorAt(0.25, QColor(160, 210, 255))
    core.setColorAt(0.55, QColor(80, 160, 240))
    core.setColorAt(0.80, QColor(30, 80, 180))
    core.setColorAt(1.0, QColor(5, 20, 80))
    p.setBrush(core); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(cx, cy), core_r, core_r)

    # 核内亮斑
    core_spec = QRadialGradient(cx - core_r * 0.28, cy - core_r * 0.30, core_r * 0.30)
    core_spec.setColorAt(0.0, QColor(255, 255, 255, 140))
    core_spec.setColorAt(0.5, QColor(255, 255, 255, 40))
    core_spec.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(core_spec)
    p.drawEllipse(QPointF(cx, cy), core_r, core_r)

    # ── 离子尾（长直蓝色尾，轻微摆动）──
    ion_len = radius * 3.5
    ion_width = radius * 0.14
    tail_pivot_x = cx + math.cos(tail_angle) * core_r * 0.8
    tail_pivot_y = cy + math.sin(tail_angle) * core_r * 0.8
    swing = math.sin(anim_t * 1.5) * radius * 0.12
    swing2 = math.cos(anim_t * 2.0) * radius * 0.06

    # 离子尾路径（贝塞尔曲线）
    ion_path = QPainterPath()
    ion_start_x = tail_pivot_x
    ion_start_y = tail_pivot_y
    ion_path.moveTo(ion_start_x, ion_start_y)
    # 控制点
    cp1_x = tail_pivot_x + math.cos(tail_angle) * ion_len * 0.3
    cp1_y = tail_pivot_y + math.sin(tail_angle) * ion_len * 0.3 + swing * 0.5
    cp2_x = tail_pivot_x + math.cos(tail_angle) * ion_len * 0.6
    cp2_y = tail_pivot_y + math.sin(tail_angle) * ion_len * 0.6 + swing * 1.5 + swing2
    ion_end_x = tail_pivot_x + math.cos(tail_angle) * ion_len
    ion_end_y = tail_pivot_y + math.sin(tail_angle) * ion_len + swing * 2.5 + swing2 * 1.5
    ion_path.cubicTo(cp1_x, cp1_y, cp2_x, cp2_y, ion_end_x, ion_end_y)

    # 离子尾渐变描边（宽→窄，亮→暗）
    pen = QPen(QColor(100, 160, 255, 60), ion_width * 2)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen); p.setBrush(Qt.NoBrush)
    p.drawPath(ion_path)
    pen2 = QPen(QColor(140, 200, 255, 120), ion_width)
    pen2.setCapStyle(Qt.RoundCap)
    p.setPen(pen2)
    p.drawPath(ion_path)
    pen3 = QPen(QColor(200, 230, 255, 200), ion_width * 0.35)
    pen3.setCapStyle(Qt.RoundCap)
    p.setPen(pen3)
    p.drawPath(ion_path)

    # ── 尘埃尾（宽阔弯曲的白色/暖色尾巴）──
    dust_len = radius * 2.2
    dust_width = radius * 0.40
    dust_path = QPainterPath()
    dust_path.moveTo(tail_pivot_x, tail_pivot_y)
    dust_angle = tail_angle - math.radians(22)  # 尘埃尾稍微弯曲
    d_cp1_x = tail_pivot_x + math.cos(dust_angle) * dust_len * 0.35
    d_cp1_y = tail_pivot_y + math.sin(dust_angle) * dust_len * 0.35 + swing * 0.3
    d_cp2_x = tail_pivot_x + math.cos(dust_angle - 0.3) * dust_len * 0.7
    d_cp2_y = tail_pivot_y + math.sin(dust_angle - 0.3) * dust_len * 0.7 + swing * 0.8
    d_end_x = tail_pivot_x + math.cos(dust_angle - 0.5) * dust_len
    d_end_y = tail_pivot_y + math.sin(dust_angle - 0.5) * dust_len + swing * 1.2
    dust_path.cubicTo(d_cp1_x, d_cp1_y, d_cp2_x, d_cp2_y, d_end_x, d_end_y)
    d_pen = QPen(QColor(255, 240, 210, 35), dust_width)
    d_pen.setCapStyle(Qt.RoundCap)
    p.setPen(d_pen); p.setBrush(Qt.NoBrush)
    p.drawPath(dust_path)
    d_pen2 = QPen(QColor(255, 250, 235, 65), dust_width * 0.5)
    d_pen2.setCapStyle(Qt.RoundCap)
    p.setPen(d_pen2)
    p.drawPath(dust_path)

    # ── 彗尾粒子（沿尾巴方向散布）──
    tail_rng = random.Random(int(anim_t * 400) % 100000 + 111)
    p.setPen(Qt.NoPen)
    for _ in range(60):
        t = tail_rng.uniform(0.05, 1.0)
        # 沿尾巴曲线分布（近似线性插值在贝塞尔上）
        px_t = tail_pivot_x + math.cos(tail_angle) * ion_len * t
        py_t = tail_pivot_y + math.sin(tail_angle) * ion_len * t + swing * (t * 2.5)
        # 散布偏移
        perp = tail_angle + math.pi / 2
        lateral = tail_rng.uniform(-1, 1) * ion_width * (1.5 + t * 3)
        px_t += math.cos(perp) * lateral
        py_t += math.sin(perp) * lateral
        # 内侧更亮
        ts = tail_rng.uniform(0.3, 2.0) * (1.2 - t * 0.6)
        ta = int((20 + 80 * (1 - t)) * tail_rng.random())
        if t < 0.15:
            ta = min(200, ta + 60)
        tg = QRadialGradient(px_t, py_t, ts * 2.0)
        tg.setColorAt(0.0, QColor(200, 230, 255, ta))
        tg.setColorAt(0.5, QColor(140, 200, 255, ta // 3))
        tg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(tg)
        p.drawEllipse(QPointF(px_t, py_t), ts * 2.0, ts * 2.0)

    # ── 彗核附近粒子 ──
    near_rng = random.Random(int(anim_t * 500) % 100000 + 222)
    for _ in range(15):
        na = near_rng.uniform(0, 2 * math.pi)
        nd = radius * (0.6 + 0.45 * near_rng.random())
        nx = cx + math.cos(na) * nd
        ny = cy + math.sin(na) * nd
        ns = near_rng.uniform(0.3, 1.2)
        na2 = near_rng.randint(30, 90)
        ng = QRadialGradient(nx, ny, ns * 2.0)
        ng.setColorAt(0.0, QColor(180, 220, 255, na2))
        ng.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(ng)
        p.drawEllipse(QPointF(nx, ny), ns * 2.0, ns * 2.0)

    # ── 悬停 ──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 4.0 + 0.3))
        pen = QPen(QColor(180, 220, 255, int(200 * hp)), 1.8)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 2, radius + 2)

    p.restore()

```
