# -*- coding: utf-8 -*-
"""
星球绘制引擎 — 程序化生成真实宇宙星球纹理
支持地球、木星、土星、海王星、火星等风格，纯 QPainter 实现
"""
import math, random
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QRadialGradient, QConicalGradient, QLinearGradient,
    QColor, QPen, QBrush, QFont, QPainterPath
)

# ═══════════════════════════════════════════
# 预设星球风格
# ═══════════════════════════════════════════

PLANET_STYLES = {
    "earth": {
        "name": "地球", "surface": [(0.0, "#1a5276"), (0.25, "#2e86c1"), (0.45, "#27ae60"),
                                     (0.55, "#f39c12"), (0.65, "#27ae60"), (0.8, "#2e86c1"), (1.0, "#1a5276")],
        "atmosphere": QColor(80, 160, 255, 40), "clouds": True,
    },
    "jupiter": {
        "name": "木星", "surface": [(0.0, "#c0392b"), (0.15, "#e8c46a"), (0.28, "#d4a056"),
                                     (0.42, "#c0392b"), (0.55, "#f5d78e"), (0.68, "#b87333"),
                                     (0.82, "#e8c46a"), (1.0, "#8b4513")],
        "atmosphere": QColor(200, 150, 80, 35), "bands": True,
    },
    "saturn": {
        "name": "土星", "surface": [(0.0, "#d4a574"), (0.2, "#f5deb3"), (0.5, "#c4a265"),
                                     (0.7, "#f5deb3"), (1.0, "#a0825a")],
        "atmosphere": QColor(220, 200, 150, 35), "has_ring": True, "bands": True,
    },
    "neptune": {
        "name": "海王星", "surface": [(0.0, "#1a237e"), (0.3, "#283593"), (0.5, "#3949ab"),
                                       (0.7, "#42a5f5"), (1.0, "#1a237e")],
        "atmosphere": QColor(80, 120, 255, 45), "clouds": True,
    },
    "mars": {
        "name": "火星", "surface": [(0.0, "#8b4513"), (0.3, "#c0392b"), (0.5, "#e67e22"),
                                     (0.7, "#d35400"), (1.0, "#6e2c00")],
        "atmosphere": QColor(255, 140, 60, 25),
    },
    "venus": {
        "name": "金星", "surface": [(0.0, "#f5c542"), (0.3, "#f9e076"), (0.5, "#f5c542"),
                                     (0.7, "#e8b730"), (1.0, "#c49520")],
        "atmosphere": QColor(255, 220, 100, 50), "clouds": True,
    },
    "mercury": {
        "name": "水星", "surface": [(0.0, "#7f8c8d"), (0.4, "#bdc3c7"), (0.6, "#95a5a6"), (1.0, "#5d6d7e")],
        "atmosphere": QColor(180, 180, 180, 15),
    },
    "uranus": {
        "name": "天王星", "surface": [(0.0, "#004d40"), (0.3, "#26a69a"), (0.5, "#80cbc4"),
                                       (0.7, "#26a69a"), (1.0, "#004d40")],
        "atmosphere": QColor(100, 220, 200, 40), "has_ring": True, "ring_vertical": True,
    },
    "pluto": {
        "name": "冥王星", "surface": [(0.0, "#5d4037"), (0.3, "#8d6e63"), (0.5, "#bcaaa4"),
                                       (0.7, "#8d6e63"), (1.0, "#4e342e")],
        "atmosphere": QColor(180, 160, 140, 20),
    },
    "sun": {
        "name": "太阳", "surface": [(0.0, "#fff176"), (0.2, "#ffb300"), (0.5, "#ff6f00"),
                                     (0.7, "#ffb300"), (1.0, "#fff176")],
        "atmosphere": QColor(255, 200, 50, 80), "glow": True,
    },
    "moon": {
        "name": "月球", "surface": [(0.0, "#9e9e9e"), (0.3, "#bdbdbd"), (0.5, "#e0e0e0"),
                                     (0.7, "#bdbdbd"), (1.0, "#757575")],
        "atmosphere": QColor(200, 200, 200, 10), "craters": True,
    },
}


# ═══════════════════════════════════════════
# 绘制入口
# ═══════════════════════════════════════════

def paint_planet(painter: QPainter, center: QPointF, radius: float, style: dict,
                  hovered: bool = False, label: str = "", font_size: int = 9,
                  anim_t: float = 0.0):
    """
    绘制一颗真实风格星球。
    
    参数:
        painter: QPainter 实例（需已开启 Antialiasing）
        center: 球心坐标
        radius: 球半径
        style: 星球风格字典（来自 PLANET_STYLES）
        hovered: 是否鼠标悬停
        label: 星球名称
        font_size: 标签字号
    """
    cx, cy = center.x(), center.y()
    
    # ── 1. 外层大气光晕 ──
    _paint_atmosphere(painter, center, radius, style)
    
    # ── 2. 光环（土星/天王星）──
    has_ring = style.get("has_ring", False)
    ring_vertical = style.get("ring_vertical", False)
    if has_ring:
        _paint_ring(painter, center, radius, style, ring_vertical)
    
    # ── 3. 球体表面 ──
    _paint_surface(painter, center, radius, style)
    
    # ── 4. 云层/条纹 ──
    if style.get("clouds"):
        _paint_clouds(painter, center, radius)
    if style.get("bands"):
        _paint_bands(painter, center, radius, style)
    if style.get("craters"):
        _paint_craters(painter, center, radius)
    
    # ── 5. 球体高光 ──
    _paint_specular(painter, center, radius)
    
    # ── 6. 悬停边框 ──
    if hovered:
        pen = QPen(QColor(255, 255, 255, 200))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center, radius + 1, radius + 1)
    
    # ── 7. 文字标签 ──
    if label:
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(label)
        tx = cx - tw / 2
        ty = cy + radius + 14
        painter.setPen(QColor(200, 180, 220))
        painter.setFont(QFont("PingFang SC", font_size))
        painter.drawText(QPointF(tx, ty), label)


# ═══════════════════════════════════════════
# 内部绘制函数
# ═══════════════════════════════════════════

def _paint_atmosphere(p: QPainter, c: QPointF, r: float, style: dict):
    """外层大气辉光"""
    atmos = style.get("atmosphere", QColor(100, 100, 255, 30))
    for i in range(3):
        scale = 1.15 + i * 0.12
        alpha = atmos.alpha() // (i + 2)
        grad = QRadialGradient(c, r * scale)
        ac = QColor(atmos.red(), atmos.green(), atmos.blue(), alpha)
        grad.setColorAt(0, ac)
        grad.setColorAt(0.6, QColor(ac.red(), ac.green(), ac.blue(), alpha // 3))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(c, r * scale, r * scale)
    
    # 太阳额外辉光
    if style.get("glow"):
        for i in range(2):
            scale = 1.3 + i * 0.25
            glow = QRadialGradient(c, r * scale)
            glow.setColorAt(0, QColor(255, 200, 50, 40 - i * 15))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(glow)
            p.setPen(Qt.NoPen)
            p.drawEllipse(c, r * scale, r * scale)


def _paint_surface(p: QPainter, c: QPointF, r: float, style: dict):
    """球体表面渐变"""
    cx, cy = c.x(), c.y()
    surface = style.get("surface", [])
    
    if not surface:
        return
    
    # 多层径向渐变模拟球体光照
    grad = QRadialGradient(cx - r * 0.25, cy - r * 0.3, r * 1.0)
    for pos, color in surface:
        grad.setColorAt(pos, QColor(color))
    
    # 暗面叠加
    shadow_grad = QRadialGradient(cx, cy, r * 1.5)
    shadow_grad.setColorAt(0, QColor(0, 0, 0, 0))
    shadow_grad.setColorAt(0.5, QColor(0, 0, 0, 20))
    shadow_grad.setColorAt(0.8, QColor(0, 0, 0, 80))
    shadow_grad.setColorAt(1, QColor(0, 0, 0, 160))
    
    p.setBrush(grad)
    p.setPen(Qt.NoPen)
    p.drawEllipse(c, r, r)
    
    p.setBrush(shadow_grad)
    p.drawEllipse(c, r, r)


def _paint_specular(p: QPainter, c: QPointF, r: float):
    """镜面高光"""
    cx, cy = c.x(), c.y()
    spec = QRadialGradient(cx - r * 0.35, cy - r * 0.4, r * 0.55)
    spec.setColorAt(0, QColor(255, 255, 255, 50))
    spec.setColorAt(0.3, QColor(255, 255, 255, 20))
    spec.setColorAt(0.6, QColor(255, 255, 255, 5))
    spec.setColorAt(1, QColor(255, 255, 255, 0))
    p.setBrush(spec)
    p.setPen(Qt.NoPen)
    p.drawEllipse(c, r, r)


def _paint_clouds(p: QPainter, c: QPointF, r: float):
    """白色云层纹理"""
    cx, cy = c.x(), c.y()
    random.seed(42)
    p.setPen(Qt.NoPen)
    for _ in range(8):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0.2, 0.75) * r
        cloud_cx = cx + math.cos(angle) * dist
        cloud_cy = cy + math.sin(angle) * dist
        cloud_r = random.uniform(0.08, 0.20) * r
        
        cloud_grad = QRadialGradient(cloud_cx, cloud_cy, cloud_r)
        cloud_grad.setColorAt(0, QColor(255, 255, 255, random.randint(30, 70)))
        cloud_grad.setColorAt(0.6, QColor(255, 255, 255, random.randint(10, 30)))
        cloud_grad.setColorAt(1, QColor(255, 255, 255, 0))
        p.setBrush(cloud_grad)
        p.drawEllipse(QPointF(cloud_cx, cloud_cy), cloud_r, cloud_r)


def _paint_bands(p: QPainter, c: QPointF, r: float, style: dict):
    """气体行星水平条纹"""
    cx, cy = c.x(), c.y()
    surface = style.get("surface", [])
    if not surface:
        return
    
    p.setPen(Qt.NoPen)
    num_bands = 12
    band_height = (r * 2) / num_bands
    for i in range(num_bands):
        y = cy - r + i * band_height
        # 计算该位置的 x 宽度（基于圆形截面）
        dy = y - cy
        if abs(dy) >= r:
            continue
        half_width = math.sqrt(r * r - dy * dy)
        
        idx = int(i / num_bands * len(surface))
        color = QColor(surface[min(idx, len(surface) - 1)][1])
        alpha = random.randint(15, 45) if i % 3 == 0 else random.randint(5, 20)
        
        p.setBrush(QColor(color.red(), color.green(), color.blue(), alpha))
        p.drawRect(QRectF(cx - half_width, y, half_width * 2, band_height + 0.5))


def _paint_ring(p: QPainter, c: QPointF, r: float, style: dict, vertical: bool = False):
    """行星光环"""
    cx, cy = c.x(), c.y()
    ring_inner = r * 1.25
    ring_outer = r * 1.7
    
    p.save()
    p.setPen(Qt.NoPen)
    
    # 土星风格光环
    ring_colors = [
        (0.0, QColor(210, 180, 140, 120)),
        (0.3, QColor(230, 210, 170, 100)),
        (0.5, QColor(180, 150, 120, 80)),
        (0.7, QColor(200, 170, 130, 60)),
        (1.0, QColor(160, 130, 100, 20)),
    ]
    
    if vertical:
        # 天王星垂直环
        for i, (pos, color) in enumerate(ring_colors):
            r_current = ring_inner + (ring_outer - ring_inner) * pos
            p.setBrush(color)
            p.drawEllipse(QPointF(cx, cy), r_current, r_current * 0.15)
    else:
        # 土星水平环
        for i, (pos, color) in enumerate(ring_colors):
            r_current = ring_inner + (ring_outer - ring_inner) * pos
            p.setBrush(color)
            p.drawEllipse(QPointF(cx, cy), r_current, r_current * 0.08)
    
    p.restore()


def _paint_craters(p: QPainter, c: QPointF, r: float):
    """月球陨石坑"""
    cx, cy = c.x(), c.y()
    random.seed(123)
    p.setPen(Qt.NoPen)
    for _ in range(15):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0.1, 0.85) * r
        crater_cx = cx + math.cos(angle) * dist
        crater_cy = cy + math.sin(angle) * dist
        crater_r = random.uniform(0.03, 0.10) * r
        
        # 暗色坑
        crater = QRadialGradient(crater_cx, crater_cy, crater_r)
        crater.setColorAt(0, QColor(40, 40, 40, 100))
        crater.setColorAt(0.7, QColor(80, 80, 80, 50))
        crater.setColorAt(1, QColor(120, 120, 120, 10))
        p.setBrush(crater)
        p.drawEllipse(QPointF(crater_cx, crater_cy), crater_r, crater_r * 0.7)


# ═══════════════════════════════════════════
# 轨道线 + 能量连接线
# ═══════════════════════════════════════════

def paint_orbit(p: QPainter, center: QPointF, radius: float):
    """半透明轨道圆环"""
    pen = QPen(QColor(170, 80, 255, 12))
    pen.setWidth(1)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(center, radius, radius)


def paint_energy_line(p: QPainter, from_pos: QPointF, to_pos: QPointF):
    """能量连接线"""
    p.setPen(QPen(QColor(170, 80, 255, 20)))
    p.drawLine(from_pos, to_pos)
