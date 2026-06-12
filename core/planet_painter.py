# -*- coding: utf-8 -*-
"""
星球绘制引擎 — 程序化生成真实宇宙星球纹理
支持地球、木星、土星、海王星、火星等风格，纯 QPainter 实现
v2: 增强色彩渐变、光晕极光、表面纹理、漂浮粒子、动画细节
"""
import math, random
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QRadialGradient, QConicalGradient, QLinearGradient,
    QColor, QPen, QBrush, QFont, QPainterPath
)

# ═══════════════════════════════════════════
# 预设星球风格 (v2 — 丰富色带 + 极光参数)
# ═══════════════════════════════════════════

PLANET_STYLES = {
    "earth": {
        "name": "地球",
        "surface": [
            (0.00, "#0a3d62"), (0.12, "#1a5f8a"), (0.22, "#2e86c1"),
            (0.36, "#16a085"), (0.44, "#27ae60"), (0.50, "#f0c040"),
            (0.58, "#27ae60"), (0.66, "#16a085"), (0.78, "#2e86c1"),
            (0.90, "#1a5f8a"), (1.00, "#0a3d62"),
        ],
        "atmosphere": QColor(80, 160, 255, 50),
        "aurora": QColor(40, 220, 160, 30),
        "clouds": True,
    },
    "jupiter": {
        "name": "木星",
        "surface": [
            (0.00, "#8b2500"), (0.08, "#c0392b"), (0.18, "#e6b84c"),
            (0.30, "#d4983c"), (0.40, "#a04020"), (0.50, "#f0d070"),
            (0.58, "#c87830"), (0.70, "#e6b84c"), (0.82, "#c0392b"),
            (0.92, "#d4983c"), (1.00, "#6e1a00"),
        ],
        "atmosphere": QColor(200, 150, 80, 40),
        "aurora": QColor(255, 180, 50, 25),
        "bands": True,
        "storm": True,
        "storm_color": QColor(210, 100, 50, 120),
    },
    "saturn": {
        "name": "土星",
        "surface": [
            (0.00, "#8b7355"), (0.15, "#d4b896"), (0.30, "#e8d5a8"),
            (0.48, "#c4a46c"), (0.62, "#e8d5a8"), (0.78, "#d4b896"),
            (0.90, "#b08d5c"), (1.00, "#7a6040"),
        ],
        "atmosphere": QColor(220, 200, 150, 40),
        "aurora": QColor(180, 220, 140, 20),
        "has_ring": True,
        "bands": True,
    },
    "neptune": {
        "name": "海王星",
        "surface": [
            (0.00, "#0d1b5e"), (0.20, "#1a3a8a"), (0.40, "#2c5ec9"),
            (0.58, "#4890e8"), (0.72, "#6cb4f5"), (0.88, "#4890e8"),
            (1.00, "#0d1b5e"),
        ],
        "atmosphere": QColor(80, 120, 255, 55),
        "aurora": QColor(60, 200, 255, 40),
        "clouds": True,
        "storm": True,
        "storm_color": QColor(100, 160, 240, 80),
    },
    "mars": {
        "name": "火星",
        "surface": [
            (0.00, "#5c1a00"), (0.18, "#8b3a15"), (0.36, "#c0502a"),
            (0.52, "#e87838"), (0.68, "#d06028"), (0.84, "#a04020"),
            (1.00, "#4a1200"),
        ],
        "atmosphere": QColor(255, 140, 60, 30),
        "aurora": QColor(255, 100, 30, 15),
        "craters": True,
    },
    "venus": {
        "name": "金星",
        "surface": [
            (0.00, "#c89820"), (0.18, "#e8c848"), (0.38, "#f8e888"),
            (0.56, "#e8c848"), (0.74, "#d4b030"), (0.90, "#c89820"),
            (1.00, "#a07810"),
        ],
        "atmosphere": QColor(255, 220, 100, 55),
        "aurora": QColor(255, 200, 80, 35),
        "clouds": True,
    },
    "mercury": {
        "name": "水星",
        "surface": [
            (0.00, "#4a4d52"), (0.25, "#8c9098"), (0.48, "#b0b5bd"),
            (0.68, "#8c9098"), (0.88, "#6a6e75"), (1.00, "#3a3d42"),
        ],
        "atmosphere": QColor(180, 180, 180, 18),
        "craters": True,
    },
    "uranus": {
        "name": "天王星",
        "surface": [
            (0.00, "#00332a"), (0.18, "#0d7377"), (0.40, "#26a69a"),
            (0.58, "#80cbc4"), (0.76, "#26a69a"), (0.92, "#0d7377"),
            (1.00, "#00332a"),
        ],
        "atmosphere": QColor(100, 220, 200, 48),
        "aurora": QColor(80, 240, 220, 30),
        "has_ring": True,
        "ring_vertical": True,
    },
    "pluto": {
        "name": "冥王星",
        "surface": [
            (0.00, "#3e2723"), (0.22, "#6d4c41"), (0.46, "#a1887f"),
            (0.66, "#6d4c41"), (0.88, "#4e342e"), (1.00, "#2d1b16"),
        ],
        "atmosphere": QColor(180, 160, 140, 22),
        "craters": True,
    },
    "sun": {
        "name": "太阳",
        "surface": [
            (0.00, "#fff9c4"), (0.12, "#ffe082"), (0.30, "#ffb300"),
            (0.50, "#ff8f00"), (0.68, "#ffb300"), (0.86, "#ffe082"),
            (1.00, "#fff9c4"),
        ],
        "atmosphere": QColor(255, 200, 50, 90),
        "aurora": QColor(255, 140, 20, 60),
        "glow": True,
    },
    "moon": {
        "name": "月球",
        "surface": [
            (0.00, "#757575"), (0.22, "#a0a0a0"), (0.46, "#d0d0d0"),
            (0.68, "#a0a0a0"), (0.88, "#808080"), (1.00, "#555555"),
        ],
        "atmosphere": QColor(200, 200, 200, 12),
        "craters": True,
    },
    # ── 新增风格 ──
    "exoplanet": {
        "name": "异星",
        "surface": [
            (0.00, "#1a0033"), (0.15, "#4a0e6e"), (0.32, "#8e2de2"),
            (0.50, "#c850c0"), (0.66, "#8e2de2"), (0.84, "#4a0e6e"),
            (1.00, "#1a0033"),
        ],
        "atmosphere": QColor(180, 80, 255, 48),
        "aurora": QColor(200, 120, 255, 35),
        "clouds": True,
        "has_ring": True,
    },
    "crystal": {
        "name": "水晶",
        "surface": [
            (0.00, "#0a2a3a"), (0.18, "#1a6a8a"), (0.38, "#40c0d0"),
            (0.56, "#80e8f0"), (0.74, "#40c0d0"), (0.90, "#1a6a8a"),
            (1.00, "#0a2a3a"),
        ],
        "atmosphere": QColor(80, 220, 255, 50),
        "aurora": QColor(100, 240, 255, 40),
        "clouds": True,
    },
}


# ═══════════════════════════════════════════
# 公共绘制入口
# ═══════════════════════════════════════════

def paint_planet(painter: QPainter, center: QPointF, radius: float, style: dict,
                 hovered: bool = False, label: str = "", font_size: int = 9,
                 anim_t: float = 0.0):
    """
    绘制一颗真实风格星球 (v2)。

    参数:
        painter: QPainter 实例（需已开启 Antialiasing）
        center: 球心坐标
        radius: 球半径
        style: 星球风格字典（来自 PLANET_STYLES）
        hovered: 是否鼠标悬停
        label: 星球名称
        font_size: 标签字号
        anim_t: 动画时间（秒），用于动态效果
    """
    cx, cy = center.x(), center.y()

    # ── 0. 漂浮粒子（星球外围）──
    _paint_particles(painter, center, radius, style, anim_t)

    # ── 1. 外层大气光晕（含极光呼吸脉冲）──
    _paint_atmosphere(painter, center, radius, style, anim_t)

    # ── 2. 光环（土星/天王星/异星）──
    has_ring = style.get("has_ring", False)
    ring_vertical = style.get("ring_vertical", False)
    if has_ring:
        _paint_ring(painter, center, radius, style, ring_vertical, anim_t)

    # ── 3. 极光带 ──
    _paint_aurora_band(painter, center, radius, style, anim_t)

    # ── 4. 球体表面 ──
    _paint_surface(painter, center, radius, style, anim_t)

    # ── 5. 云层/条纹/环形山/风暴 ──
    if style.get("clouds"):
        _paint_clouds(painter, center, radius, anim_t)
    if style.get("bands"):
        _paint_bands(painter, center, radius, style, anim_t)
    if style.get("craters"):
        _paint_craters(painter, center, radius)
    if style.get("storm"):
        _paint_storm_swirls(painter, center, radius, style, anim_t)

    # ── 6. 球体高光 ──
    _paint_specular(painter, center, radius, anim_t)

    # ── 7. 悬停边框 ──
    if hovered:
        # 呼吸脉冲边框
        pulse = 0.7 + 0.3 * abs(math.sin(anim_t * 4.0 + 1.0))
        pen = QPen(QColor(255, 255, 255, int(200 * pulse)))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center, radius + 1, radius + 1)

        # 外发光环
        outer_glow = QRadialGradient(center, radius + 12)
        outer_glow.setColorAt(0.80, QColor(0, 0, 0, 0))
        outer_glow.setColorAt(0.90, QColor(120, 180, 255, int(50 * pulse)))
        outer_glow.setColorAt(1.00, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(outer_glow)
        painter.drawEllipse(center, radius + 12, radius + 12)

    # ── 8. 文字标签 ──
    if label:
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(label)
        tx = cx - tw / 2
        ty = cy + radius + 14
        # 标签发光
        label_color = QColor(200, 180, 240)
        painter.setPen(label_color)
        painter.setFont(QFont("PingFang SC", font_size))
        painter.drawText(QPointF(tx + 0.5, ty + 0.5), label)
        painter.setPen(QColor(255, 255, 255, 180))
        painter.drawText(QPointF(tx, ty), label)


# ═══════════════════════════════════════════
# 内部绘制函数 (v2 全面升级)
# ═══════════════════════════════════════════

def _paint_atmosphere(p: QPainter, c: QPointF, r: float, style: dict, anim_t: float):
    """多层大气辉光 + 呼吸脉冲 + 极光外层"""
    atmos = style.get("atmosphere", QColor(100, 100, 255, 30))
    aurora = style.get("aurora")
    breath = 1.0 + 0.05 * math.sin(anim_t * 2.0)

    # ── 三层基础辉光 ──
    for i in range(4):
        scale = (1.10 + i * 0.14) * breath
        alpha = int(atmos.alpha() * (0.7 ** i))
        grad = QRadialGradient(c, r * scale)
        ac = QColor(atmos.red(), atmos.green(), atmos.blue(), max(0, alpha))
        grad.setColorAt(0, QColor(ac.red(), ac.green(), ac.blue(), alpha // 3))
        grad.setColorAt(0.3, ac)
        grad.setColorAt(0.65, QColor(ac.red(), ac.green(), ac.blue(), alpha // 2))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(c, r * scale, r * scale)

    # ── 极光外层（若配置了 aurora 颜色）──
    if aurora and aurora.alpha() > 0:
        for i in range(3):
            scale = (1.30 + i * 0.22) * breath
            alpha = int(aurora.alpha() * (0.55 ** i))
            grad = QRadialGradient(c, r * scale)
            ac = QColor(aurora.red(), aurora.green(), aurora.blue(), alpha)
            grad.setColorAt(0, QColor(0, 0, 0, 0))
            grad.setColorAt(0.4, QColor(ac.red(), ac.green(), ac.blue(), alpha // 2))
            grad.setColorAt(0.65, ac)
            grad.setColorAt(0.85, QColor(ac.red(), ac.green(), ac.blue(), alpha // 3))
            grad.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(grad)
            p.setPen(Qt.NoPen)
            p.drawEllipse(c, r * scale, r * scale)

    # ── 太阳额外烈焰辉光 ──
    if style.get("glow"):
        for i in range(3):
            scale = (1.25 + i * 0.30) * breath
            alpha = max(0, 60 - i * 18)
            glow = QRadialGradient(c, r * scale)
            glow.setColorAt(0, QColor(255, 200, 50, alpha))
            glow.setColorAt(0.4, QColor(255, 140, 20, alpha // 2))
            glow.setColorAt(0.7, QColor(255, 100, 10, alpha // 4))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(glow)
            p.setPen(Qt.NoPen)
            p.drawEllipse(c, r * scale, r * scale)


def _paint_surface(p: QPainter, c: QPointF, r: float, style: dict, anim_t: float):
    """球体表面 —— 径向渐变 + 圆锥渐变混合，产生更丰富的色带层次"""
    cx, cy = c.x(), c.y()
    surface = style.get("surface", [])
    if not surface:
        return

    # ── 主径向渐变（球体 3D 光照）──
    grad = QRadialGradient(cx - r * 0.28, cy - r * 0.34, r * 1.05)
    for pos, color in surface:
        grad.setColorAt(pos, QColor(color))
    p.setBrush(grad)
    p.setPen(Qt.NoPen)
    p.drawEllipse(c, r, r)

    # ── 圆锥渐变叠加（色带纹理）──
    # 仅对 gas giant（有 bands / storm 标记）添加圆锥渐变
    if style.get("bands") or style.get("storm"):
        conical = QConicalGradient(cx, cy, anim_t * 15.0)
        for i in range(len(surface)):
            pos = i / len(surface)
            color = QColor(surface[i][1])
            color.setAlpha(18)
            conical.setColorAt(pos, color)
        p.setBrush(conical)
        p.drawEllipse(c, r, r)

    # ── 暗面叠加（右侧+底部阴影）──
    shadow_grad = QRadialGradient(cx, cy, r * 1.55)
    shadow_grad.setColorAt(0, QColor(0, 0, 0, 0))
    shadow_grad.setColorAt(0.40, QColor(0, 0, 0, 8))
    shadow_grad.setColorAt(0.55, QColor(0, 0, 0, 25))
    shadow_grad.setColorAt(0.72, QColor(0, 0, 0, 70))
    shadow_grad.setColorAt(0.88, QColor(0, 0, 0, 130))
    shadow_grad.setColorAt(1.00, QColor(0, 0, 0, 180))
    p.setBrush(shadow_grad)
    p.drawEllipse(c, r, r)


def _paint_specular(p: QPainter, c: QPointF, r: float, anim_t: float):
    """镜面高光（v2: 微微移动增强动感）"""
    cx, cy = c.x(), c.y()
    shift_x = math.sin(anim_t * 0.6) * r * 0.04
    shift_y = math.cos(anim_t * 0.6) * r * 0.04
    spec = QRadialGradient(cx - r * 0.35 + shift_x, cy - r * 0.40 + shift_y, r * 0.50)
    spec.setColorAt(0, QColor(255, 255, 255, 55))
    spec.setColorAt(0.25, QColor(255, 255, 255, 25))
    spec.setColorAt(0.50, QColor(255, 255, 255, 8))
    spec.setColorAt(0.75, QColor(255, 255, 255, 2))
    spec.setColorAt(1.00, QColor(255, 255, 255, 0))
    p.setBrush(spec)
    p.setPen(Qt.NoPen)
    p.drawEllipse(c, r, r)


def _paint_clouds(p: QPainter, c: QPointF, r: float, anim_t: float):
    """云层纹理（v2: 贝塞尔曲线云带 + 缓慢漂移）"""
    cx, cy = c.x(), c.y()

    # ── 旋转漂移 ──
    p.save()
    p.setClipRect(QRectF(cx - r, cy - r, r * 2, r * 2))

    drift = anim_t * 0.03
    p.setPen(Qt.NoPen)

    # 云团簇（使用确定性哈希而非 random.seed 避免每帧重建 PRNG 状态）
    import hashlib
    frame_seed = int(abs(hashlib.md5(f"clouds_{anim_t:.6f}".encode()).digest()[0]) * 16807) % 2147483647
    rng = random.Random(frame_seed)

    for _ in range(12):
        angle = rng.uniform(0, 2 * math.pi) + drift
        dist = rng.uniform(0.10, 0.78) * r
        cloud_cx = cx + math.cos(angle) * dist
        cloud_cy = cy + math.sin(angle) * dist
        cloud_rx = rng.uniform(0.12, 0.28) * r
        cloud_ry = rng.uniform(0.05, 0.14) * r

        cloud_grad = QRadialGradient(cloud_cx, cloud_cy, max(cloud_rx, cloud_ry))
        cloud_grad.setColorAt(0, QColor(255, 255, 255, rng.randint(35, 75)))
        cloud_grad.setColorAt(0.45, QColor(255, 255, 255, rng.randint(15, 35)))
        cloud_grad.setColorAt(0.75, QColor(255, 255, 255, rng.randint(5, 15)))
        cloud_grad.setColorAt(1, QColor(255, 255, 255, 0))
        p.setBrush(cloud_grad)
        p.drawEllipse(QPointF(cloud_cx, cloud_cy), cloud_rx, cloud_ry)

    # 云带（弯曲的贝塞尔路径）
    for _ in range(4):
        base_y = cy + rng.uniform(-0.35, 0.35) * r
        if abs(base_y - cy) > r:
            continue
        half_w = math.sqrt(max(0, r * r - (base_y - cy) ** 2))
        path = QPainterPath()
        start_x = cx - half_w
        path.moveTo(start_x, base_y)
        cp1_x = cx - half_w * 0.5
        cp1_y = base_y + rng.uniform(-6, 6) + math.sin(anim_t * 0.7 + _) * 4
        cp2_x = cx + half_w * 0.5
        cp2_y = base_y + rng.uniform(-6, 6) + math.cos(anim_t * 0.7 + _) * 4
        end_x = cx + half_w
        path.cubicTo(cp1_x, cp1_y, cp2_x, cp2_y, end_x, base_y)
        pen = QPen(QColor(255, 255, 255, rng.randint(15, 45)))
        pen.setWidthF(rng.uniform(1.5, 4.0))
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)

    p.restore()


def _paint_bands(p: QPainter, c: QPointF, r: float, style: dict, anim_t: float):
    """气体行星水平条纹（v2: 波浪边缘 + 渐变 alpha）"""
    cx, cy = c.x(), c.y()
    surface = style.get("surface", [])
    if not surface:
        return

    p.setPen(Qt.NoPen)
    num_bands = 14
    band_height = (r * 2) / num_bands

    for i in range(num_bands):
        y = cy - r + i * band_height
        dy = y - cy
        if abs(dy) >= r:
            continue
        half_width = math.sqrt(r * r - dy * dy)

        # 波浪偏移
        wave_offset = math.sin(i * 0.9 + anim_t * 0.6) * r * 0.06

        idx = int(i / num_bands * len(surface))
        color = QColor(surface[min(idx, len(surface) - 1)][1])
        base_alpha = 35 if i % 3 == 0 else 14
        alpha = base_alpha + int(10 * abs(math.sin(i * 0.5 + anim_t * 0.4)))

        band_color = QColor(color.red(), color.green(), color.blue(), alpha)
        p.setBrush(band_color)

        # 画稍倾斜的矩形条带
        bx = cx - half_width + wave_offset
        bw = half_width * 2
        p.drawRect(QRectF(bx, y, bw, band_height + 1.0))


def _paint_storm_swirls(p: QPainter, c: QPointF, r: float, style: dict, anim_t: float):
    """风暴漩涡（木星大红斑 / 海王星暗斑风格）"""
    cx, cy = c.x(), c.y()
    storm_color = style.get("storm_color", QColor(200, 80, 40, 90))

    # ── 主涡旋（椭圆风暴）──
    storm_cx = cx + r * 0.18 * math.cos(anim_t * 0.15)
    storm_cy = cy + r * 0.22
    storm_rx = r * 0.28
    storm_ry = r * 0.16

    # 风暴主体渐变
    for i in range(3):
        sr = storm_rx * (0.45 + i * 0.28)
        alpha = storm_color.alpha() - i * 28
        grad = QRadialGradient(storm_cx, storm_cy, sr)
        sc = QColor(storm_color.red(), storm_color.green(),
                     storm_color.blue(), max(0, alpha))
        grad.setColorAt(0, sc)
        grad.setColorAt(0.5, QColor(sc.red(), sc.green(), sc.blue(), max(0, alpha // 2)))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(storm_cx, storm_cy), storm_rx * (0.45 + i * 0.28),
                      storm_ry * (0.45 + i * 0.28))

    # 旋臂曲线
    p.save()
    p.setClipRect(QRectF(storm_cx - storm_rx, storm_cy - storm_ry,
                          storm_rx * 2, storm_ry * 2))
    for j in range(3):
        path = QPainterPath()
        angle = j * 2.1 + anim_t * 0.3
        path.moveTo(storm_cx, storm_cy)
        cp1_x = storm_cx + math.cos(angle) * storm_rx * 0.6
        cp1_y = storm_cy + math.sin(angle) * storm_ry * 0.6
        cp2_x = storm_cx + math.cos(angle + 1.2) * storm_rx * 0.9
        cp2_y = storm_cy + math.sin(angle + 1.2) * storm_ry * 0.9
        end_x = storm_cx + math.cos(angle + 2.0) * storm_rx * 0.5
        end_y = storm_cy + math.sin(angle + 2.0) * storm_ry * 0.5
        path.cubicTo(cp1_x, cp1_y, cp2_x, cp2_y, end_x, end_y)
        pen = QPen(QColor(storm_color.red(), storm_color.green(),
                          storm_color.blue(), max(0, storm_color.alpha() - 40)))
        pen.setWidthF(1.5)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)
    p.restore()


def _paint_ring(p: QPainter, c: QPointF, r: float, style: dict,
                vertical: bool = False, anim_t: float = 0.0):
    """行星光环（v2: 多层纹理 + 粒子感 + 透明度渐变）"""
    cx, cy = c.x(), c.y()
    ring_inner = r * 1.22
    ring_outer = r * 1.78

    # 光环颜色取自 surface 暖色调或默认
    surface = style.get("surface", [])
    ring_base = QColor(210, 180, 140, 120)
    if surface:
        mid_color = QColor(surface[len(surface) // 2][1])
        ring_base = QColor(mid_color.red(), mid_color.green(),
                           mid_color.blue(), 100)

    p.save()

    # ── 多层光环 ──
    ring_layers = [
        (ring_inner, ring_outer, 90),
        (ring_inner * 1.06, ring_outer * 0.94, 55),
        (ring_inner * 1.12, ring_outer * 0.88, 30),
    ]

    if vertical:
        # 天王星垂直环
        for inner, outer, alpha in ring_layers:
            for pos in [0.0, 0.25, 0.5, 0.75, 1.0]:
                r_current = inner + (outer - inner) * pos
                color = QColor(ring_base.red(), ring_base.green(),
                               ring_base.blue(), alpha)
                p.setBrush(color)
                p.setPen(Qt.NoPen)
                p.drawEllipse(QPointF(cx, cy), r_current, r_current * 0.12)
    else:
        # 土星水平环
        for inner, outer, alpha in ring_layers:
            for pos in [0.0, 0.25, 0.5, 0.75, 1.0]:
                r_current = inner + (outer - inner) * pos
                color = QColor(ring_base.red(), ring_base.green(),
                               ring_base.blue(), alpha)
                p.setBrush(color)
                p.setPen(Qt.NoPen)
                p.drawEllipse(QPointF(cx, cy), r_current, r_current * 0.07)

    # ── 光环粒子点缀 ──
    ring_rng = random.Random(int(anim_t * 100) % 10000)
    p.setPen(Qt.NoPen)
    for _ in range(30):
        angle = ring_rng.uniform(0, 2 * math.pi)
        dist = ring_rng.uniform(ring_inner, ring_outer)
        px = cx + math.cos(angle) * dist
        if vertical:
            py = cy + math.sin(angle) * dist * 0.12
        else:
            py = cy + math.sin(angle) * dist * 0.07
        particle_r = ring_rng.uniform(0.5, 1.8)
        alpha = ring_rng.randint(30, 100)
        p.setBrush(QColor(ring_base.red(), ring_base.green(),
                          ring_base.blue(), alpha))
        p.drawEllipse(QPointF(px, py), particle_r, particle_r)

    p.restore()


def _paint_aurora_band(p: QPainter, c: QPointF, r: float, style: dict, anim_t: float):
    """极光带（v2 新增：星球顶部柔和光带）"""
    aurora = style.get("aurora")
    if not aurora or aurora.alpha() <= 0:
        return

    cx, cy = c.x(), c.y()
    wave = math.sin(anim_t * 1.2) * 0.15

    p.save()
    # 裁剪到球体上半部分
    clip_path = QPainterPath()
    clip_path.addEllipse(c, r * 1.05, r * 1.05)
    p.setClipPath(clip_path)

    # 极光渐变带（顶部弧形）
    for i in range(3):
        aurora_y = cy - r * (0.5 + i * 0.25)
        aurora_rx = r * (0.75 + i * 0.15)
        aurora_ry = r * (0.12 + i * 0.05)

        offset_x = math.sin(anim_t * 0.5 + i * 1.5) * r * (0.10 + wave)
        grad = QRadialGradient(cx + offset_x, aurora_y, aurora_rx)
        alpha = int(aurora.alpha() * (0.35 - i * 0.10))
        ac = QColor(aurora.red(), aurora.green(), aurora.blue(), max(0, alpha))
        grad.setColorAt(0, QColor(0, 0, 0, 0))
        grad.setColorAt(0.4, ac)
        grad.setColorAt(0.6, QColor(ac.red(), ac.green(), ac.blue(), alpha // 2))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx + offset_x, aurora_y), aurora_rx, aurora_ry)

    p.restore()


def _paint_craters(p: QPainter, c: QPointF, r: float):
    """月球/水星陨石坑（v2: 亮边 + 阴影）"""
    cx, cy = c.x(), c.y()
    random.seed(123)
    p.setPen(Qt.NoPen)
    for _ in range(20):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0.08, 0.88) * r
        crater_cx = cx + math.cos(angle) * dist
        crater_cy = cy + math.sin(angle) * dist
        crater_r = random.uniform(0.02, 0.11) * r

        # 亮边（左上方）
        rim_grad = QRadialGradient(crater_cx - crater_r * 0.3,
                                    crater_cy - crater_r * 0.3, crater_r * 1.05)
        rim_grad.setColorAt(0, QColor(200, 200, 200, 50))
        rim_grad.setColorAt(0.4, QColor(140, 140, 140, 30))
        rim_grad.setColorAt(0.7, QColor(60, 60, 60, 80))
        rim_grad.setColorAt(1, QColor(100, 100, 100, 15))
        p.setBrush(rim_grad)
        p.drawEllipse(QPointF(crater_cx, crater_cy), crater_r, crater_r * 0.75)


def _paint_particles(p: QPainter, c: QPointF, r: float, style: dict, anim_t: float):
    """漂浮微光粒子（v2 新增：星球周围的星尘粒子）"""
    cx, cy = c.x(), c.y()
    atmos = style.get("atmosphere", QColor(100, 100, 255, 30))
    aurora = style.get("aurora")

    # 粒子伪随机基于动画时间，使用局部 Random 实例避免全局种子污染
    seed = int(anim_t * 1000) % 100000
    rng = random.Random(42 + seed * 31)

    p.setPen(Qt.NoPen)
    num_particles = 18

    for i in range(num_particles):
        # 粒子轨道参数
        base_angle = (i / num_particles) * 2 * math.pi
        angle = base_angle + anim_t * (0.3 + 0.15 * math.sin(i * 2.7))
        dist = r * (1.15 + 0.35 * abs(math.sin(i * 1.8 + anim_t * 0.5)))

        px = cx + math.cos(angle) * dist
        py = cy + math.sin(angle) * dist

        # 粒子大小
        size = 1.2 + 1.5 * abs(math.sin(i * 3.1 + anim_t * 1.8))

        # 颜色取自大气或极光色，带透明度脉冲
        pulse = 0.5 + 0.5 * abs(math.sin(i * 2.3 + anim_t * 2.5))
        if aurora and aurora.alpha() > 0:
            alpha = int(aurora.alpha() * 0.6 * pulse)
            particle_color = QColor(aurora.red(), aurora.green(), aurora.blue(), alpha)
        else:
            alpha = int(atmos.alpha() * 0.5 * pulse)
            particle_color = QColor(atmos.red(), atmos.green(), atmos.blue(), alpha)

        # 外层光晕
        glow_r = size * 2.5
        glow = QRadialGradient(px, py, glow_r)
        glow.setColorAt(0, QColor(particle_color.red(), particle_color.green(),
                                   particle_color.blue(), particle_color.alpha()))
        glow.setColorAt(0.5, QColor(particle_color.red(), particle_color.green(),
                                     particle_color.blue(), particle_color.alpha() // 3))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(glow)
        p.drawEllipse(QPointF(px, py), glow_r, glow_r)

        # 亮点核心
        p.setBrush(QColor(255, 255, 255, int(alpha * 1.2)))
        p.drawEllipse(QPointF(px, py), size * 0.6, size * 0.6)


# ═══════════════════════════════════════════
# 轨道线 + 能量连接线
# ═══════════════════════════════════════════

def paint_orbit(p: QPainter, center: QPointF, radius: float, anim_t: float = 0.0):
    """半透明轨道圆环（v2: 带微光脉冲）"""
    pulse = 0.8 + 0.2 * abs(math.sin(anim_t * 0.4))
    alpha = int(12 * pulse)
    pen = QPen(QColor(170, 80, 255, alpha))
    pen.setWidth(1)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(center, radius, radius)


def paint_energy_line(p: QPainter, from_pos: QPointF, to_pos: QPointF,
                      alpha: int = 20, anim_t: float = 0.0):
    """能量连接线（v2: 闪烁效果）"""
    pulse = 0.7 + 0.3 * abs(math.sin(anim_t * 2.0))
    a = int(alpha * pulse)
    p.setPen(QPen(QColor(170, 80, 255, a)))
    p.drawLine(from_pos, to_pos)


# ═══════════════════════════════════════════
# 便捷函数：带角度偏移的星球绘制
# ═══════════════════════════════════════════

def paint_planet_at_angle(p: QPainter, orbit_center: QPointF, orbit_r: float,
                          angle: float, planet_r: float, style: dict,
                          hovered: bool = False, label: str = "",
                          font_size: int = 9, anim_t: float = 0.0):
    """在指定轨道的某个角度位置绘制星球。"""
    cx = orbit_center.x() + math.cos(angle) * orbit_r
    cy = orbit_center.y() + math.sin(angle) * orbit_r
    paint_planet(p, QPointF(cx, cy), planet_r, style,
                 hovered=hovered, label=label, font_size=font_size, anim_t=anim_t)
