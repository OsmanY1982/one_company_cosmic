# -*- coding: utf-8 -*-
"""
星舰舰桥 3D 渲染器 — QPainter 纯 2D API 模拟立体纵深感
球形光照模型 · 透视穹顶肋骨 · 3D 凹凸控制台 · 体积光柱 · Fresnel 玻璃曲面 · 景深雾 · 4 层星场
"""
import math, random as _random
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal, QTimer
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QRadialGradient,
    QLinearGradient, QConicalGradient, QPainterPath, QFont,
    QOpenGLShaderProgram, QOpenGLShader, QOpenGLBuffer,
    QOpenGLVertexArrayObject, QOpenGLVersionProfile,
    QMatrix4x4, QVector3D, QSurfaceFormat,
)
from PyQt5.QtWidgets import QWidget, QOpenGLWidget

_SEED = 42

def _rng(seed_offset=0):
    return _random.Random(_SEED + seed_offset)

# ═══════════════════════════════════════════
#  舰桥模块星球定义（不变）
# ═══════════════════════════════════════════
BRIDGE_PLANETS = {
    "business":    {"label": "业务管理", "color": (255, 160, 60),  "ring_color": (255, 180, 100), "type": "station"},
    "intelligence": {"label": "智能中心", "color": (60, 140, 255), "ring_color": (80, 160, 255),  "type": "gas_giant"},
    "data":        {"label": "数据中心", "color": (180, 80, 255),  "ring_color": (200, 110, 255), "type": "matrix"},
    "personnel":   {"label": "人员管理", "color": (100, 240, 200), "ring_color": (140, 255, 220), "type": "crystal"},
    "system":      {"label": "系统设置", "color": (255, 100, 120), "ring_color": (255, 140, 160), "type": "lava"},
}

# ═══════════════════════════════════════════
#  布局与位置计算（不变）
# ═══════════════════════════════════════════
def get_bridge_planet_zones(rect: QRectF, role: str = "user", anim_t: float = 0.0):
    w, h = rect.width(), rect.height()
    glass_left, glass_top = rect.left() + 12, rect.top() + 10
    glass_w, glass_h = w - 24, h - 50
    planet_r = min(glass_w, glass_h) * 0.125
    hit_size = planet_r * 2.8
    zones = {}
    modules = ["business", "intelligence", "data"]
    if role == "admin":
        modules += ["personnel", "system"]
    positions = _get_dynamic_planet_positions(glass_left, glass_top, glass_w, glass_h, modules, anim_t)
    for mid, (px, py) in positions.items():
        zones[(mid, BRIDGE_PLANETS[mid]["label"])] = QRectF(px - hit_size / 2, py - hit_size / 2, hit_size, hit_size)
    return zones

# ═══════════════════════════════════════════
#  动态轨道参数（每颗星球独立椭圆轨道）
# ═══════════════════════════════════════════
_PLANET_ORBITS = {
    # 5 星共心椭圆轨道：不同尺寸/偏心率/速度让覆盖区域均匀
    "business":     {"a_ratio": 0.28, "ecc": 0.40, "speed": 0.52, "phase": 0.0},
    "intelligence": {"a_ratio": 0.35, "ecc": 0.50, "speed": 0.38, "phase": 2.094},  # 2π/3
    "data":         {"a_ratio": 0.30, "ecc": 0.36, "speed": 0.45, "phase": 4.189},  # 4π/3
    "personnel":    {"a_ratio": 0.33, "ecc": 0.46, "speed": 0.35, "phase": 1.047},  # π/3
    "system":       {"a_ratio": 0.27, "ecc": 0.55, "speed": 0.48, "phase": 5.236},  # 5π/3
}


def _get_dynamic_planet_positions(glass_left, glass_top, glass_w, glass_h, modules, anim_t):
    """根据 anim_t 计算每颗星球的椭圆轨道当前位置"""
    cx, cy = glass_left + glass_w / 2, glass_top + glass_h / 2
    positions = {}
    for mid in modules:
        orb = _PLANET_ORBITS.get(mid, {"a_ratio": 0.30, "ecc": 0.4, "speed": 0.45, "phase": 0})
        a = glass_w * orb["a_ratio"]
        b = a * (1.0 - orb["ecc"])
        angle = orb["phase"] + orb["speed"] * anim_t
        px = cx + a * math.cos(angle)
        py = cy + b * math.sin(angle)
        positions[mid] = (px, py)
    return positions


def _get_planet_positions(glass_left, glass_top, glass_w, glass_h, modules):
    """静态兜底：anim_t=0 时的初始位置（用于旧调用兼容）"""
    return _get_dynamic_planet_positions(glass_left, glass_top, glass_w, glass_h, modules, 0.0)

# ═══════════════════════════════════════════
#  图层 1：4 层视差星场
# ═══════════════════════════════════════════
def paint_starfield(p: QPainter, rect: QRectF, anim_t: float, alpha: float = 1.0,
                    drift_x: float = 0.0, drift_y: float = 0.0):
    w, h = rect.width(), rect.height()
    cx, cy = rect.center().x(), rect.center().y()
    # 背景深空渐变
    space_grad = QRadialGradient(cx, cy, max(w, h) * 0.75)
    space_grad.setColorAt(0.0, QColor(2, 4, 18, int(255 * alpha)))
    space_grad.setColorAt(0.5, QColor(1, 2, 12, int(255 * alpha)))
    space_grad.setColorAt(1.0, QColor(0, 1, 6, int(255 * alpha)))
    p.fillRect(rect, space_grad)

    # 4 层星星：(count, min_size, max_size, drift_speed, twinkle_rate, base_alpha, seed, parallax, has_mansfield)
    star_layers = [
        (120, 0.3, 0.8,  0.08, 0.3,  60,  501, 0.35, False),   # L0 最远：密小静
        (70,  0.6, 1.3,  0.18, 0.7,  130, 502, 0.6,  False),   # L1 远：有小光晕
        (35,  1.0, 2.2,  0.30, 1.2,  200, 503, 0.85, True),    # L2 中：柔和光晕
        (12,  2.5, 4.5,  0.50, 1.8,  255, 504, 1.2,  True),    # L3 近：十字星芒
    ]
    for count, mins, maxs, drift, twinkle, base_a, seed, parallax, has_mansfield in star_layers:
        rng = _rng(seed)
        scroll_x = -drift_x * w * 0.12 * parallax
        scroll_y = -drift_y * h * 0.12 * parallax
        for i in range(count):
            bx = rng.random() * w
            by = rng.random() * h
            dx = math.sin(anim_t * drift + i * 0.7) * w * 0.015 + math.cos(anim_t * 0.25 + i) * w * 0.005
            dy = math.cos(anim_t * drift + i * 1.1) * h * 0.015 + math.sin(anim_t * 0.35 + i) * h * 0.005
            sx = (bx + dx + scroll_x) % w
            sy = (by + dy + scroll_y) % h
            flicker = 0.55 + 0.45 * abs(math.sin(anim_t * twinkle + i * 3.7))
            sa = int(base_a * flicker * alpha)
            ss = mins + (maxs - mins) * rng.random()
            hue = rng.uniform(0.55, 0.72)
            p.setBrush(QColor.fromHsvF(hue, 0.3, 0.9 + rng.random() * 0.1, sa / 255))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(sx, sy), ss, ss)
            # L3: 十字星芒
            if has_mansfield and sa > 180:
                man_len = ss * 2.5
                ma = int(sa * 0.35)
                p.setPen(QPen(QColor(200, 220, 255, ma), 0.4))
                p.drawLine(QPointF(sx - man_len, sy), QPointF(sx + man_len, sy))
                p.drawLine(QPointF(sx, sy - man_len), QPointF(sx, sy + man_len))
                # 对角细芒
                d45 = man_len * 0.55
                p.setPen(QPen(QColor(180, 200, 255, int(ma * 0.6)), 0.25))
                p.drawLine(QPointF(sx - d45, sy - d45), QPointF(sx + d45, sy + d45))
                p.drawLine(QPointF(sx + d45, sy - d45), QPointF(sx - d45, sy + d45))
            # L2: 柔光晕
            elif not has_mansfield and sa > 150 and ss > 1.0:
                glow = QRadialGradient(sx, sy, ss * 3.5)
                glow.setColorAt(0.0, QColor(180, 200, 255, int(sa * 0.3)))
                glow.setColorAt(0.5, QColor(100, 140, 220, int(sa * 0.08)))
                glow.setColorAt(1.0, QColor(0, 0, 0, 0))
                p.setBrush(glow)
                p.drawEllipse(QPointF(sx, sy), ss * 3.5, ss * 3.5)
            # L1: 微光晕
            elif not has_mansfield and sa > 100 and ss > 0.7:
                glow2 = QRadialGradient(sx, sy, ss * 2.0)
                glow2.setColorAt(0.0, QColor(160, 180, 230, int(sa * 0.15)))
                glow2.setColorAt(1.0, QColor(0, 0, 0, 0))
                p.setBrush(glow2)
                p.drawEllipse(QPointF(sx, sy), ss * 2.0, ss * 2.0)

    # 高速移动时的星轨
    speed = math.sqrt(drift_x * drift_x + drift_y * drift_y)
    if speed > 0.3:
        srng = _rng(int(anim_t * 1000) % 10000 + 900)
        angle = math.atan2(drift_y, drift_x)
        for _ in range(int(speed * 20)):
            slen = srng.uniform(4, 15) * speed
            sx = srng.uniform(0, w)
            sy = srng.uniform(0, h)
            ex, ey = sx + math.cos(angle) * slen, sy + math.sin(angle) * slen
            grad = QLinearGradient(sx, sy, ex, ey)
            grad.setColorAt(0.0, QColor(255, 255, 255, 0))
            grad.setColorAt(0.3, QColor(255, 255, 255, int(80 * alpha)))
            grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setPen(QPen(grad, srng.uniform(0.5, 1.2)))
            p.drawLine(QPointF(sx, sy), QPointF(ex, ey))

# ═══════════════════════════════════════════
#  图层 2：星云带
# ═══════════════════════════════════════════
def paint_nebula_belt(p: QPainter, rect: QRectF, anim_t: float, alpha: float = 1.0):
    w, h = rect.width(), rect.height()
    belts = [
        (0.55, 0.15, (180, 80, 255), 0.7),
        (0.30, 0.28, (60, 160, 255), 1.1),
        (0.75, 0.10, (255, 120, 60), 0.5),
        (0.12, 0.22, (100, 220, 200), 1.5),
    ]
    for rel_y, belt_h, (br, bg2, bb), drift_speed in belts:
        bx = (anim_t * drift_speed * w * 0.15) % (w * 1.5) - w * 0.25
        by = rect.top() + h * rel_y
        belt_w = w * 1.2
        belt_grad = QRadialGradient(bx + belt_w * 0.4, by, belt_w * 0.9)
        breath = 0.5 + 0.5 * abs(math.sin(anim_t * 0.8 + rel_y * 3))
        belt_grad.setColorAt(0.0, QColor(br, bg2, bb, int(14 * alpha * breath)))
        belt_grad.setColorAt(0.4, QColor(br, bg2, bb, int(8 * alpha * breath)))
        belt_grad.setColorAt(0.7, QColor(br // 3, bg2 // 3, bb // 3, int(3 * alpha)))
        belt_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(belt_grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(bx, by), belt_w * 0.8, h * belt_h * 2)

# ═══════════════════════════════════════════
#  图层 3：小行星碎片
# ═══════════════════════════════════════════
def paint_asteroids(p: QPainter, rect: QRectF, anim_t: float, alpha: float = 1.0):
    w, h = rect.width(), rect.height()
    rng = _rng(int(anim_t * 10) % 10000)
    for i in range(5):
        base_x = (anim_t * (0.4 + i * 0.25) * w * 0.12 + i * w * 0.22) % (w * 1.3) - w * 0.15
        base_y = rect.top() + h * (0.15 + i * 0.18)
        ax = base_x + math.sin(anim_t * 1.3 + i) * 8
        ay = base_y + math.cos(anim_t * 0.7 + i * 2) * 6
        ar = rng.uniform(1.8, 4.5)
        a_alpha = int(rng.uniform(30, 90) * alpha)
        path = QPainterPath()
        path.moveTo(ax - ar, ay)
        path.lineTo(ax - ar * 0.4, ay - ar * 0.8)
        path.lineTo(ax + ar * 0.6, ay - ar * 0.3)
        path.lineTo(ax + ar * 0.9, ay + ar * 0.2)
        path.lineTo(ax + ar * 0.3, ay + ar * 0.7)
        path.lineTo(ax - ar * 0.7, ay + ar * 0.4)
        path.closeSubpath()
        p.setPen(QPen(QColor(100, 110, 130, a_alpha), 0.6))
        p.setBrush(QColor(40, 42, 50, a_alpha))
        p.drawPath(path)

# ═══════════════════════════════════════════
#  图层 4：景深大气层雾
# ═══════════════════════════════════════════
def _paint_depth_atmosphere(p, rect, anim_t, alpha):
    w, h = rect.width(), rect.height()
    left, top = rect.left(), rect.top()
    glass_left, glass_top = left + 12, top + 10
    glass_w, glass_h = w - 24, h - 50
    # 纵向深度雾：上浓下淡（远处深空浓，近处淡）
    fog_grad = QLinearGradient(glass_left, glass_top, glass_left, glass_top + glass_h)
    fog_grad.setColorAt(0.0, QColor(30, 40, 90, int(38 * alpha)))
    fog_grad.setColorAt(0.25, QColor(20, 30, 70, int(28 * alpha)))
    fog_grad.setColorAt(0.55, QColor(15, 20, 55, int(12 * alpha)))
    fog_grad.setColorAt(0.80, QColor(10, 15, 40, int(5 * alpha)))
    fog_grad.setColorAt(1.0, QColor(5, 8, 25, 0))
    p.setBrush(fog_grad)
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(QRectF(glass_left, glass_top, glass_w, glass_h), 6, 6)
    # 团块状密雾区（3 个）
    fog_clusters = [
        (0.25, 0.20, 0.30, 0.18, (25, 35, 85), 32),
        (0.65, 0.12, 0.22, 0.20, (20, 30, 75), 30),
        (0.45, 0.08, 0.18, 0.14, (35, 45, 100), 25),
    ]
    for fx_rel, fy_rel, fw_rel, fh_rel, (fr, fg, fb), fa in fog_clusters:
        fx = glass_left + glass_w * fx_rel
        fy = glass_top + glass_h * fy_rel
        fw = glass_w * fw_rel
        fh = glass_h * fh_rel
        fg_grad = QRadialGradient(fx + fw * 0.5, fy + fh * 0.3, max(fw, fh) * 0.7)
        fg_grad.setColorAt(0.0, QColor(fr, fg, fb, int(fa * alpha)))
        fg_grad.setColorAt(0.5, QColor(fr // 2, fg // 2, fb // 2, int(fa * 0.5 * alpha)))
        fg_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(fg_grad)
        p.drawEllipse(QPointF(fx + fw * 0.5, fy + fh * 0.5), fw, fh)

# ═══════════════════════════════════════════
#  图层 5：侧窗框支柱（圆柱体渐变 + 铆钉投影）
# ═══════════════════════════════════════════
def _paint_side_pillars(p, rect, alpha):
    w, h = rect.width(), rect.height()
    left, top = rect.left(), rect.top()
    glass_top, glass_bot = top + 10, top + h - 38
    for side_x in [left + 2, left + w - 10]:
        pw = 8
        pillar = QRectF(side_x, glass_top, pw, glass_bot - glass_top)
        # 圆柱体渐变：中间亮，两侧暗
        pillar_grad = QLinearGradient(side_x, glass_top, side_x + pw, glass_top)
        pillar_grad.setColorAt(0.0, QColor(30, 32, 42, int(220 * alpha)))
        pillar_grad.setColorAt(0.25, QColor(50, 53, 65, int(240 * alpha)))
        pillar_grad.setColorAt(0.5, QColor(58, 60, 72, int(245 * alpha)))
        pillar_grad.setColorAt(0.75, QColor(45, 47, 58, int(235 * alpha)))
        pillar_grad.setColorAt(1.0, QColor(28, 30, 40, int(215 * alpha)))
        p.setBrush(pillar_grad)
        p.setPen(QPen(QColor(70, 80, 95, int(140 * alpha)), 0.7))
        p.drawRoundedRect(pillar, 2, 2)
        # 铆钉 + 投影
        for j in range(4):
            ry = glass_top + 8 + j * (glass_bot - glass_top - 16) / 3
            # 投影
            p.setBrush(QColor(10, 12, 18, int(80 * alpha)))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(side_x + 4.6, ry + 0.8), 1.5, 1.5)
            # 铆钉本体（圆柱凸起）
            rivet_grad = QRadialGradient(side_x + 3.5, ry - 0.5, 1.8)
            rivet_grad.setColorAt(0.0, QColor(180, 185, 200, int(200 * alpha)))
            rivet_grad.setColorAt(0.5, QColor(120, 125, 140, int(180 * alpha)))
            rivet_grad.setColorAt(1.0, QColor(60, 65, 75, int(150 * alpha)))
            p.setBrush(rivet_grad)
            p.drawEllipse(QPointF(side_x + 4, ry), 2.0, 2.0)

# ═══════════════════════════════════════════
#  图层 6：Fresnel 曲面玻璃
# ═══════════════════════════════════════════
def _paint_glass(p, rect, anim_t, alpha):
    w, h = rect.width(), rect.height()
    left, top = rect.left(), rect.top()
    glass_left, glass_top = left + 12, top + 10
    glass_w, glass_h = w - 24, h - 50
    gr = QRectF(glass_left, glass_top, glass_w, glass_h)

    # 基底：深蓝半透明
    p.setBrush(QColor(0, 15, 45, int(22 * alpha)))
    p.setPen(QPen(QColor(30, 80, 140, int(110 * alpha)), 1.5))
    p.drawRoundedRect(gr, 6, 6)

    # 大面积冷色反光（左下→中心）
    refl_cool = QLinearGradient(glass_left, glass_top + glass_h, glass_left + glass_w * 0.7, glass_top + glass_h * 0.35)
    refl_cool.setColorAt(0.0, QColor(80, 140, 220, int(22 * alpha)))
    refl_cool.setColorAt(0.35, QColor(50, 100, 180, int(15 * alpha)))
    refl_cool.setColorAt(0.7, QColor(20, 50, 120, int(5 * alpha)))
    refl_cool.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(refl_cool)
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(gr, 6, 6)

    # 暖色反光（右上角小范围）
    refl_warm = QLinearGradient(glass_left + glass_w * 0.6, glass_top, glass_left + glass_w, glass_top + glass_h * 0.4)
    refl_warm.setColorAt(0.0, QColor(255, 180, 100, int(10 * alpha)))
    refl_warm.setColorAt(0.5, QColor(200, 120, 60, int(5 * alpha)))
    refl_warm.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(refl_warm)
    p.drawRoundedRect(gr, 6, 6)

    # 边缘暗角 vignette
    vignette = QRadialGradient(glass_left + glass_w / 2, glass_top + glass_h / 2, max(glass_w, glass_h) * 0.7)
    vignette.setColorAt(0.0, QColor(0, 0, 0, 0))
    vignette.setColorAt(0.6, QColor(0, 0, 0, 0))
    vignette.setColorAt(0.85, QColor(0, 2, 10, int(30 * alpha)))
    vignette.setColorAt(1.0, QColor(0, 4, 15, int(50 * alpha)))
    p.setBrush(vignette)
    p.drawRoundedRect(gr, 6, 6)

    # 曲面镜面反射条纹（1~2 条弯曲反光）
    p.setPen(QPen(QColor(160, 210, 255, int(12 * alpha)), 1.8))
    refl_path = QPainterPath()
    refl_path.moveTo(glass_left + glass_w * 0.1, glass_top + glass_h * 0.45)
    refl_path.cubicTo(glass_left + glass_w * 0.25, glass_top + glass_h * 0.25,
                       glass_left + glass_w * 0.6, glass_top + glass_h * 0.35,
                       glass_left + glass_w * 0.85, glass_top + glass_h * 0.5)
    p.setBrush(Qt.NoBrush)
    p.drawPath(refl_path)

    p.setPen(QPen(QColor(120, 180, 240, int(8 * alpha)), 1.2))
    refl_path2 = QPainterPath()
    refl_path2.moveTo(glass_left + glass_w * 0.05, glass_top + glass_h * 0.6)
    refl_path2.cubicTo(glass_left + glass_w * 0.3, glass_top + glass_h * 0.48,
                        glass_left + glass_w * 0.55, glass_top + glass_h * 0.55,
                        glass_left + glass_w * 0.72, glass_top + glass_h * 0.65)
    p.drawPath(refl_path2)

    # 玻璃边框内发光
    inner_glow = QLinearGradient(glass_left, glass_top, glass_left, glass_top + 4)
    inner_glow.setColorAt(0.0, QColor(0, 120, 220, int(15 * alpha)))
    inner_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setPen(QPen(inner_glow, 1.0))
    # 四边内发光用简化方式：画 4 条线紧贴边框内侧
    glow_rect = QRectF(glass_left + 0.5, glass_top + 0.5, glass_w - 1, glass_h - 1)
    p.setPen(QPen(QColor(0, 140, 240, int(10 * alpha)), 0.8))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(glow_rect, 6, 6)

    # 扫描线
    p.setPen(QPen(QColor(0, 180, 240, int(4 * alpha)), 0.5))
    for y in range(int(glass_top) + 2, int(glass_top + glass_h), 4):
        p.drawLine(QPointF(glass_left + 2, y), QPointF(glass_left + glass_w - 2, y))

# ═══════════════════════════════════════════
#  图层 7：体积光柱
# ═══════════════════════════════════════════
def _paint_volumetric_light(p, rect, anim_t, alpha):
    w, h = rect.width(), rect.height()
    left, top = rect.left(), rect.top()
    glass_left, glass_top = left + 12, top + 10
    glass_w, glass_h = w - 24, h - 50
    # 2 道光柱
    pillars = [
        (glass_left + glass_w * 0.18, glass_top + 2, 0.3, 0.7),  # 左柱
        (glass_left + glass_w * 0.65, glass_top + 2, 0.5, 0.55), # 右柱
    ]
    for px, py_start, spread, mid_y_rel in pillars:
        pb = py_start
        pm = py_start + glass_h * mid_y_rel
        pe = py_start + glass_h * spread
        # 光柱渐变：近窄远宽锥形
        vol_grad = QLinearGradient(px, pb, px, pe)
        vol_grad.setColorAt(0.0, QColor(255, 240, 200, int(40 * alpha)))
        vol_grad.setColorAt(0.3, QColor(255, 225, 160, int(25 * alpha)))
        vol_grad.setColorAt(0.7, QColor(255, 200, 120, int(8 * alpha)))
        vol_grad.setColorAt(1.0, QColor(255, 180, 100, 0))
        # 光柱路径（锥形）
        top_width = glass_w * 0.012
        bot_width = glass_w * 0.08
        vpath = QPainterPath()
        vpath.moveTo(px - top_width, pb)
        vpath.lineTo(px + top_width, pb)
        vpath.lineTo(px + bot_width, pe)
        vpath.lineTo(px - bot_width, pe)
        vpath.closeSubpath()
        p.setBrush(QBrush(vol_grad))
        p.setPen(Qt.NoPen)
        p.drawPath(vpath)
        # 微尘粒子沿光柱
        rng = _rng(int(anim_t * 200) % 10000 + int(px))
        for _ in range(18):
            dp_rel = (anim_t * 0.3 + rng.random()) % 1.0
            dpx = px + (rng.random() - 0.5) * (top_width + dp_rel * (bot_width - top_width)) * 2.2
            dpy = pb + dp_rel * (pe - pb)
            ds = rng.uniform(0.6, 1.5)
            da = int(rng.uniform(40, 90) * alpha * (1 - dp_rel * 0.7))
            p.setBrush(QColor(255, 250, 230, da))
            p.drawEllipse(QPointF(dpx, dpy), ds, ds)
    # 玻璃交汇处散射光晕
    for px, py_start, spread, _ in pillars:
        halo = QRadialGradient(px, py_start, glass_w * 0.08)
        halo.setColorAt(0.0, QColor(255, 240, 210, int(18 * alpha)))
        halo.setColorAt(0.5, QColor(220, 200, 160, int(6 * alpha)))
        halo.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(halo)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(px, py_start), glass_w * 0.08, glass_h * 0.05)

# ═══════════════════════════════════════════
#  图层 8：模块星球 — 真实球体光照模型
# ═══════════════════════════════════════════
def _paint_sphere_planet(p, x, y, r, r2, g2, b2, ptype, ring_color, anim_t, alpha):
    """通用球体绘制：径向渐变 + 边缘光 + 镜面高光 + 投影"""
    breath = 0.6 + 0.4 * abs(math.sin(anim_t * 1.2 + x * 0.01))

    # ── 球体主光源（左上 135°） ──
    body_grad = QRadialGradient(x - r * 0.3, y - r * 0.25, r * 1.1)
    body_grad.setColorAt(0.0, QColor(min(r2 + 70, 255), min(g2 + 55, 255), min(b2 + 45, 255),
                                     int(175 * alpha * breath)))
    body_grad.setColorAt(0.20, QColor(min(r2 + 40, 255), min(g2 + 30, 255), min(b2 + 25, 255),
                                      int(165 * alpha * breath)))
    body_grad.setColorAt(0.45, QColor(r2, g2, b2, int(150 * alpha * breath)))
    body_grad.setColorAt(0.72, QColor(r2 * 2 // 3, g2 * 2 // 3, b2 * 2 // 3, int(130 * alpha * breath)))
    body_grad.setColorAt(0.90, QColor(r2 // 3, g2 // 3, b2 // 3, int(115 * alpha * breath)))
    body_grad.setColorAt(1.0, QColor(r2 // 4, g2 // 4, b2 // 4, int(100 * alpha * breath)))
    p.setBrush(body_grad)
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(x, y), r, r)

    # ── 次表面散射边缘光（右下冷色调） ──
    rim_grad = QRadialGradient(x + r * 0.35, y + r * 0.3, r * 1.15)
    rim_grad.setColorAt(0.0, QColor(0, 0, 0, 0))
    rim_grad.setColorAt(0.75, QColor(0, 0, 0, 0))
    rim_grad.setColorAt(0.90, QColor(70, 100, 220, int(55 * alpha * breath)))
    rim_grad.setColorAt(1.0, QColor(120, 150, 255, int(40 * alpha * breath)))
    p.setBrush(rim_grad)
    p.drawEllipse(QPointF(x, y), r, r)

    # ── 镜面高光点（左上） ──
    hl_x = x - r * 0.22
    hl_y = y - r * 0.28
    hl_rx = r * 0.10
    hl_ry = r * 0.07
    hl_grad = QRadialGradient(hl_x, hl_y, hl_rx * 1.2)
    hl_grad.setColorAt(0.0, QColor(255, 255, 255, int(170 * alpha)))
    hl_grad.setColorAt(0.4, QColor(255, 255, 250, int(100 * alpha)))
    hl_grad.setColorAt(1.0, QColor(255, 255, 240, 0))
    p.setBrush(hl_grad)
    p.drawEllipse(QPointF(hl_x, hl_y), hl_rx, hl_ry)

    # ── 球体投影（底部偏移） ──
    shadow_y = y + r * 1.02
    shadow_grad = QRadialGradient(x, shadow_y, r * 0.6)
    shadow_grad.setColorAt(0.0, QColor(0, 0, 0, int(60 * alpha)))
    shadow_grad.setColorAt(0.6, QColor(0, 0, 0, int(20 * alpha)))
    shadow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(shadow_grad)
    p.drawEllipse(QPointF(x, shadow_y), r * 0.65, r * 0.12)

    # ── 类型特化细节 ──
    _paint_planet_detail(p, x, y, r, r2, g2, b2, ptype, ring_color, anim_t, alpha, breath)

def _paint_planet_detail(p, x, y, r, r2, g2, b2, ptype, ring_color, anim_t, alpha, breath):
    if ptype == "gas_giant":
        for i in range(4):
            sy = y - r * 0.5 + i * r / 3.5
            stripe_w = r * (1.0 - abs(i - 1.5) / 3)
            stripe_a = int(40 * alpha * breath)
            p.setBrush(QColor(min(r2 + 80, 255), min(g2 + 60, 255), min(b2 + 50, 255), stripe_a))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(QRectF(x - stripe_w, sy, stripe_w * 2, r * 0.13), 2, 2)
        ring_a = int(50 * alpha * breath)
        p.setPen(QPen(QColor(*ring_color, ring_a), 0.8))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(x, y), r * 1.5, r * 0.25)

    elif ptype == "crystal":
        p.setPen(QPen(QColor(180, 255, 230, int(35 * alpha * breath)), 0.5))
        for i in range(3):
            angle = i * math.pi / 3 + anim_t * 0.3
            lx1, ly1 = x + math.cos(angle) * r * 0.4, y + math.sin(angle) * r * 0.4
            lx2, ly2 = x + math.cos(angle + math.pi) * r * 0.4, y + math.sin(angle + math.pi) * r * 0.4
            p.drawLine(QPointF(lx1, ly1), QPointF(lx2, ly2))
        sparkle = QRadialGradient(x, y - r * 0.3, r * 0.15)
        sparkle.setColorAt(0.0, QColor(255, 255, 255, int(100 * alpha)))
        sparkle.setColorAt(1.0, QColor(180, 255, 240, 0))
        p.setBrush(sparkle)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(x, y - r * 0.3), r * 0.15, r * 0.15)

    elif ptype == "station":
        path = QPainterPath()
        hex_angle = anim_t * 0.5
        for i in range(6):
            angle = hex_angle + i * math.pi / 3
            hx, hy = x + math.cos(angle) * r * 0.75, y + math.sin(angle) * r * 0.75
            (path.moveTo if i == 0 else path.lineTo)(hx, hy)
        path.closeSubpath()
        p.setPen(QPen(QColor(*ring_color, int(80 * alpha * breath)), 0.8))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)

    elif ptype == "matrix":
        grid_alpha = int(30 * alpha * breath)
        p.setPen(QPen(QColor(*ring_color, grid_alpha), 0.3))
        for gy in range(int(y - r), int(y + r), int(r * 0.3)):
            p.drawLine(QPointF(x - r, gy), QPointF(x + r, gy))
        for gx in range(int(x - r), int(x + r), int(r * 0.3)):
            p.drawLine(QPointF(gx, y - r), QPointF(gx, y + r))

    elif ptype == "lava":
        crack_angle = anim_t * 0.4
        for i in range(3):
            ca = crack_angle + i * 2.1
            lx, ly = x + math.cos(ca) * r * 0.2, y + math.sin(ca) * r * 0.2
            ex, ey = x + math.cos(ca) * r * 0.7, y + math.sin(ca) * r * 0.7
            p.setPen(QPen(QColor(255, 200, 80, int(70 * alpha)), 0.6))
            p.drawLine(QPointF(lx, ly), QPointF(ex, ey))
        glow_lava = QRadialGradient(x, y + r * 0.3, r * 0.6)
        glow_lava.setColorAt(0.0, QColor(255, 140, 30, int(30 * alpha)))
        glow_lava.setColorAt(1.0, QColor(255, 60, 10, 0))
        p.setBrush(glow_lava)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(x, y + r * 0.3), r * 0.6, r * 0.3)

def _paint_bridge_planets(p, rect, anim_t, alpha, role="user"):
    w, h = rect.width(), rect.height()
    glass_left, glass_top = rect.left() + 12, rect.top() + 10
    glass_w, glass_h = w - 24, h - 50
    planet_r = min(glass_w, glass_h) * 0.125
    cx, cy = glass_left + glass_w / 2, glass_top + glass_h / 2
    modules = ["business", "intelligence", "data"]
    if role == "admin":
        modules += ["personnel", "system"]

    # ── 计算所有星球当前动态位置 ──
    positions = _get_dynamic_planet_positions(glass_left, glass_top, glass_w, glass_h, modules, anim_t)

    # ── 按 Y 深度排序（Y 越大越靠前，绘制顺序从远到近） ──
    sorted_planets = sorted(modules, key=lambda mid: positions[mid][1])

    # ── 轨道虚线（每条轨道 40 点弧段，微弱可见） ──
    for mid in sorted_planets:
        orb = _PLANET_ORBITS.get(mid, {"a_ratio": 0.30, "ecc": 0.4, "speed": 0.45, "phase": 0})
        a = glass_w * orb["a_ratio"]
        b = a * (1.0 - orb["ecc"])
        trail_alpha = int(25 * alpha)
        for i in range(40):
            seg_angle = i * 2 * math.pi / 40
            sx = cx + a * math.cos(seg_angle)
            sy = cy + b * math.sin(seg_angle)
            if i == 0:
                p.setPen(QPen(QColor(0, 160, 220, trail_alpha), 0.3))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(QPointF(sx, sy), 0.8, 0.8)
            elif i % 8 == 0:
                p.setPen(QPen(QColor(0, 120, 180, trail_alpha), 0.2))
                p.drawEllipse(QPointF(sx, sy), 0.5, 0.5)

    # ── 从远到近绘制星球 ──
    for mid in sorted_planets:
        px, py = positions[mid]
        # 深度系数：0=最远（上方），1=最近（下方）
        depth = (py - (cy - glass_h * 0.35)) / (glass_h * 0.65)
        depth = max(0.0, min(1.0, depth))

        # 动态大小：近大远小（±12%）
        size_mod = 0.92 + depth * 0.16
        dynamic_r = planet_r * size_mod

        # 动态亮度：近处更亮
        planet_alpha = alpha * (0.85 + depth * 0.15)

        planet = BRIDGE_PLANETS[mid]
        _paint_sphere_planet(p, px, py, dynamic_r, *planet["color"],
                             planet["type"], planet["ring_color"], anim_t, planet_alpha)

        # 运动光尾（沿轨道反方向 6 段衰减光点）
        orb = _PLANET_ORBITS.get(mid, {"a_ratio": 0.30, "ecc": 0.4, "speed": 0.45, "phase": 0})
        a_trail = glass_w * orb["a_ratio"]
        b_trail = a_trail * (1.0 - orb["ecc"])
        angle_now = orb["phase"] + orb["speed"] * anim_t
        for ti in range(1, 7):
            trail_angle = angle_now - ti * 0.08
            trail_a = int(40 * alpha * (1.0 - ti / 7.0))
            tx = cx + a_trail * math.cos(trail_angle)
            ty = cy + b_trail * math.sin(trail_angle)
            trail_grad = QRadialGradient(tx, ty, dynamic_r * 0.3 * (1.0 - ti / 8.0))
            trail_grad.setColorAt(0.0, QColor(*planet["ring_color"], trail_a))
            trail_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setBrush(trail_grad)
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(tx, ty), dynamic_r * 0.25 * (1.0 - ti / 8.0),
                          dynamic_r * 0.25 * (1.0 - ti / 8.0))

        # ── 标签 ──
        font = QFont("PingFang SC", max(6, int(dynamic_r * 0.5)))
        font.setBold(True)
        p.setFont(font)
        breath = 0.6 + 0.4 * abs(math.sin(anim_t * 1.5 + px * 0.02))
        label_alpha = int(140 * alpha * breath * (0.8 + depth * 0.2))
        p.setPen(QColor(*planet["ring_color"], label_alpha))
        label_w = dynamic_r * 3.5
        p.drawText(QRectF(px - label_w / 2, py + dynamic_r * 1.15, label_w, dynamic_r * 0.8),
                   Qt.AlignCenter, planet["label"])

# ═══════════════════════════════════════════
#  图层 9：HUD 对焦括号（带投影 + 拐角发光点）
# ═══════════════════════════════════════════
def _paint_hud_brackets(p, rect, anim_t, alpha):
    left = rect.left() + 14
    top = rect.top() + 12
    right = rect.left() + rect.width() - 14
    bottom = rect.top() + rect.height() - 52
    bl, bm = 10, 3

    # 先画投影（偏移 1px 右下）
    p.setPen(QPen(QColor(0, 40, 60, int(40 * alpha)), 1.2))
    for (ax, ay, bx, by) in [
        (left, top + bm, left, top), (left, top, left + bl, top),
        (right - bm, top, right, top), (right, top, right, top + bl),
        (left, bottom - bm, left, bottom), (left, bottom, left + bl, bottom),
        (right - bm, bottom, right, bottom), (right, bottom, right, bottom - bl)]:
        p.drawLine(QPointF(ax + 1.0, ay + 1.0), QPointF(bx + 1.0, by + 1.0))

    # 主线条
    p.setPen(QPen(QColor(0, 210, 240, int(120 * alpha)), 1.2))
    p.drawLine(QPointF(left, top + bm), QPointF(left, top))
    p.drawLine(QPointF(left, top), QPointF(left + bl, top))
    p.drawLine(QPointF(right - bm, top), QPointF(right, top))
    p.drawLine(QPointF(right, top), QPointF(right, top + bl))
    p.drawLine(QPointF(left, bottom - bm), QPointF(left, bottom))
    p.drawLine(QPointF(left, bottom), QPointF(left + bl, bottom))
    p.drawLine(QPointF(right - bm, bottom), QPointF(right, bottom))
    p.drawLine(QPointF(right, bottom), QPointF(right, bottom - bl))

    # 拐角发光圆点
    for cx, cy in [(left, top), (right, top), (left, bottom), (right, bottom)]:
        dot_glow = QRadialGradient(cx, cy, 2.5)
        dot_glow.setColorAt(0.0, QColor(150, 230, 255, int(160 * alpha)))
        dot_glow.setColorAt(0.4, QColor(0, 180, 240, int(100 * alpha)))
        dot_glow.setColorAt(1.0, QColor(0, 60, 120, 0))
        p.setBrush(dot_glow)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx, cy), 2.5, 2.5)

    # 顶部状态文字
    font = QFont("Courier New", 6)
    p.setFont(font)
    p.setPen(QColor(0, 180, 220, int(80 * alpha)))
    p.drawText(QRectF(left + 2, top - 1, 60, 10), Qt.AlignLeft, "SFS-01 BRIDGE")
    p.drawText(QRectF(right - 50, top - 1, 48, 10), Qt.AlignRight, f"SYS:{anim_t * 0.5:.1f}s")
    p.setPen(QColor(0, 160, 200, int(50 * alpha)))
    p.drawText(QRectF(left + 2, bottom + 1, 40, 8), Qt.AlignLeft, "ENG:OK")
    p.drawText(QRectF(right - 40, bottom + 1, 38, 8), Qt.AlignRight, "SHD:100%")

# ═══════════════════════════════════════════
#  图层 10：数据流飘字
# ═══════════════════════════════════════════
def _paint_data_stream(p, rect, anim_t, alpha):
    w, h = rect.width(), rect.height()
    left, top = rect.left() + 16, rect.top() + 14
    rng = _rng(int(anim_t * 300) % 10000)
    p.setFont(QFont("Courier New", 5))
    for i in range(10):
        dx = left + rng.uniform(0, w - 36)
        dy = top + rng.uniform(0, h - 68)
        flicker = 0.3 + 0.7 * abs(math.sin(anim_t * (2 + i * 0.7) + i))
        alpha_d = int(25 * alpha * flicker)
        p.setPen(QColor(0, 180, 220, alpha_d))
        p.drawText(QPointF(dx, dy), rng.choice(["0101", "1010", "FF", "A3", "7C", "◆", "█", "▓", "01", "10", "SFS", "TGT"]))

# ═══════════════════════════════════════════
#  图层 11：透视穹顶肋骨框架
# ═══════════════════════════════════════════
def _paint_canopy(p, rect, alpha):
    w, h = rect.width(), rect.height()
    left, top = rect.left(), rect.top()
    right = rect.right()
    glass_left, glass_top = left + 12, top + 10
    glass_w = w - 24
    glass_h = h - 50

    rib_count = 8
    for i in range(rib_count):
        # 深度系数：0=最前，1=最后
        depth = i / (rib_count - 1)
        # Z-attenuation：越深越细越暗
        z_alpha = 230 - depth * 160  # 230 → 70
        z_width = 3.0 - depth * 2.0   # 3.0 → 1.0
        # 曲率收敛：最前肋骨弯曲大，最后几乎平坦
        curvature = 1.0 - depth * 0.55  # 1.0 → 0.45
        # 水平分布：从顶部向下排列
        ry = glass_top + depth * glass_h * 0.72
        # 肋骨宽度随深度变化（透视）
        rib_h = 14 - depth * 7  # 14 → 7

        # 肋骨弧形路径
        path = QPainterPath()
        arc_top = ry - rib_h * curvature
        arc_bot = ry + rib_h * curvature
        # 外层弧
        path.moveTo(glass_left + 4, ry)
        path.cubicTo(glass_left + 4, arc_top, right - 4, arc_top, right - 4, ry)
        path.cubicTo(right - 4, arc_bot, glass_left + 4, arc_bot, glass_left + 4, ry)

        # 圆柱形金属渐变（中间亮两侧暗）
        rib_grad = QLinearGradient(left, ry - rib_h, left, ry + rib_h)
        dot = int(z_alpha * alpha)
        rib_grad.setColorAt(0.0, QColor(30, 32, 42, dot))
        rib_grad.setColorAt(0.3, QColor(65, 70, 85, dot))
        rib_grad.setColorAt(0.5, QColor(75, 80, 95, int(dot * 1.05)))
        rib_grad.setColorAt(0.7, QColor(60, 65, 78, dot))
        rib_grad.setColorAt(1.0, QColor(25, 28, 38, dot))
        p.setBrush(rib_grad)
        p.setPen(QPen(QColor(70, 80, 100, int(z_alpha * 0.6 * alpha)), z_width * 0.5))
        p.drawPath(path)

        # 水平横梁连接（每 3 根肋骨间拉一条横梁）
        if i > 0 and i % 3 == 0:
            prev_depth = (i - 3) / (rib_count - 1)
            prev_ry = glass_top + prev_depth * glass_h * 0.72
            beam_mid = (ry + prev_ry) / 2
            beam_grad = QLinearGradient(glass_left, beam_mid, glass_left, beam_mid + 1.5)
            bdot = int((z_alpha + (230 - prev_depth * 160)) / 2 * 0.7 * alpha)
            beam_grad.setColorAt(0.0, QColor(50, 55, 68, bdot))
            beam_grad.setColorAt(0.5, QColor(70, 75, 90, bdot))
            beam_grad.setColorAt(1.0, QColor(40, 45, 55, bdot))
            p.setBrush(beam_grad)
            p.setPen(QPen(QColor(60, 70, 85, int(bdot * 0.6)), 0.6))
            p.drawRoundedRect(QRectF(glass_left + 8, beam_mid - 1, glass_w - 16, 2.5), 1, 1)

    # 顶部主横梁
    beam_top = QRectF(glass_left + 6, glass_top - 1, glass_w - 12, 3.5)
    beam_top_grad = QLinearGradient(glass_left, glass_top, glass_left, glass_top + 3.5)
    beam_top_grad.setColorAt(0.0, QColor(70, 75, 90, int(220 * alpha)))
    beam_top_grad.setColorAt(0.5, QColor(80, 85, 100, int(230 * alpha)))
    beam_top_grad.setColorAt(1.0, QColor(50, 55, 68, int(200 * alpha)))
    p.setBrush(beam_top_grad)
    p.setPen(QPen(QColor(90, 100, 120, int(130 * alpha)), 0.6))
    p.drawRoundedRect(beam_top, 2, 2)

# ═══════════════════════════════════════════
#  图层 12：3D 凹凸控制台
# ═══════════════════════════════════════════
def _paint_console(p, rect, anim_t, alpha):
    w, h = rect.width(), rect.height()
    left, top = rect.left(), rect.top()
    console_left = left + 10
    console_w = w - 20
    console_top = top + h - 38
    console_bot = top + h
    console_h = 36

    # ── L 形截面：顶面操作面板 + 前面立面 ──
    panel_h = console_h * 0.55
    face_h = console_h - panel_h

    # 顶面（水平操作面板）— 浅灰蓝，有高光边
    panel_grad = QLinearGradient(console_left, console_top, console_left, console_top + panel_h)
    panel_grad.setColorAt(0.0, QColor(60, 65, 80, int(245 * alpha)))
    panel_grad.setColorAt(0.5, QColor(48, 52, 65, int(240 * alpha)))
    panel_grad.setColorAt(1.0, QColor(38, 42, 52, int(235 * alpha)))
    p.setBrush(panel_grad)
    p.setPen(QPen(QColor(85, 95, 115, int(160 * alpha)), 1.0))
    p.drawRoundedRect(QRectF(console_left, console_top, console_w, panel_h + 2), 3, 3)

    # 前面立面 — 深灰向下变暗
    face_grad = QLinearGradient(console_left, console_top + panel_h, console_left, console_top + console_h)
    face_grad.setColorAt(0.0, QColor(42, 46, 56, int(240 * alpha)))
    face_grad.setColorAt(0.4, QColor(35, 38, 48, int(235 * alpha)))
    face_grad.setColorAt(1.0, QColor(22, 25, 35, int(225 * alpha)))
    p.setBrush(face_grad)
    p.setPen(QPen(QColor(70, 80, 95, int(140 * alpha)), 0.8))
    p.drawRoundedRect(QRectF(console_left, console_top + panel_h, console_w, face_h), 0, 0)

    # ── 斜角扶手/边框 ──
    for side_offset in [0, console_w - 6]:
        sx = console_left + side_offset
        bevel = QRectF(sx, console_top + 2, 6, console_h - 2)
        bevel_grad = QLinearGradient(sx, console_top, sx + 6, console_top)
        bevel_grad.setColorAt(0.0, QColor(70, 75, 90, int(230 * alpha)))
        bevel_grad.setColorAt(0.5, QColor(95, 100, 120, int(240 * alpha)))
        bevel_grad.setColorAt(1.0, QColor(55, 60, 72, int(220 * alpha)))
        p.setBrush(bevel_grad)
        p.setPen(QPen(QColor(80, 90, 110, int(130 * alpha)), 0.5))
        p.drawRoundedRect(bevel, 2, 2)

    # ── 圆形仪表盘（4 个）：外凸内凹 ──
    instrument_cx = [console_left + console_w * 0.12, console_left + console_w * 0.38,
                     console_left + console_w * 0.62, console_left + console_w * 0.88]
    for i, icx in enumerate(instrument_cx):
        icy = console_top + panel_h / 2 + 1
        ir = 7.5
        # 外圈凸起 — 亮边在上，暗边在下
        bezel_grad = QLinearGradient(icx, icy - ir, icx, icy + ir)
        bezel_grad.setColorAt(0.0, QColor(100, 110, 130, int(200 * alpha)))
        bezel_grad.setColorAt(0.5, QColor(45, 50, 65, int(200 * alpha)))
        bezel_grad.setColorAt(1.0, QColor(25, 28, 40, int(190 * alpha)))
        p.setBrush(bezel_grad)
        p.setPen(QPen(QColor(80, 90, 110, int(140 * alpha)), 0.7))
        p.drawEllipse(QPointF(icx, icy), ir + 1.5, ir + 1.5)
        # 内圈凹陷 — 上暗下亮
        inner_grad = QLinearGradient(icx, icy - ir * 0.7, icx, icy + ir * 0.7)
        inner_grad.setColorAt(0.0, QColor(15, 18, 28, int(185 * alpha)))
        inner_grad.setColorAt(0.6, QColor(25, 30, 42, int(180 * alpha)))
        inner_grad.setColorAt(1.0, QColor(35, 40, 52, int(175 * alpha)))
        p.setBrush(inner_grad)
        p.setPen(QPen(QColor(50, 55, 70, int(100 * alpha)), 0.4))
        p.drawEllipse(QPointF(icx, icy), ir * 0.82, ir * 0.82)
        # 指针投影
        needle_angle = anim_t * 2.5 + i * 1.2
        needle_len = ir * 0.55
        p.setPen(QPen(QColor(0, 0, 0, int(60 * alpha)), 0.8))
        p.drawLine(QPointF(icx + 0.5, icy + 0.5),
                   QPointF(icx + math.cos(needle_angle) * needle_len + 0.5,
                           icy + math.sin(needle_angle) * needle_len + 0.5))
        # 指针主体
        p.setPen(QPen(QColor(0, 210, 255, int(185 * alpha)), 0.9))
        p.drawLine(QPointF(icx, icy),
                   QPointF(icx + math.cos(needle_angle) * needle_len,
                           icy + math.sin(needle_angle) * needle_len))
        # 中心点发光
        p.setBrush(QColor(0, 210, 255, int(120 * alpha)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(icx, icy), 1.5, 1.5)

    # ── 方形按键块（4 个，在仪表之间） ──
    for i in range(4):
        kx = console_left + console_w * (0.22 + i * 0.25) - 5
        ky = console_top + panel_h / 2 - 5
        kw, kh = 10, 10
        # 凸起块 — 顶边亮，底边暗
        key_grad = QLinearGradient(kx, ky, kx, ky + kh)
        key_grad.setColorAt(0.0, QColor(80, 85, 100, int(230 * alpha)))
        key_grad.setColorAt(0.5, QColor(50, 55, 68, int(225 * alpha)))
        key_grad.setColorAt(1.0, QColor(30, 33, 45, int(220 * alpha)))
        p.setBrush(key_grad)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(kx, ky, kw, kh), 2, 2)
        # 顶边高亮线
        p.setPen(QPen(QColor(110, 120, 140, int(120 * alpha)), 0.6))
        p.drawLine(QPointF(kx + 1, ky + 0.5), QPointF(kx + kw - 1, ky + 0.5))
        # 底边暗线
        p.setPen(QPen(QColor(15, 18, 28, int(100 * alpha)), 0.5))
        p.drawLine(QPointF(kx + 1, ky + kh - 0.5), QPointF(kx + kw - 1, ky + kh - 0.5))

    # ── 滑轨/旋钮 ──
    slider_x = console_left + console_w * 0.06
    slider_y = console_top + panel_h / 2 - 7
    slider_w, slider_h = 4, 14
    slider_grad = QLinearGradient(slider_x, slider_y, slider_x + slider_w, slider_y)
    slider_grad.setColorAt(0.0, QColor(30, 33, 45, int(210 * alpha)))
    slider_grad.setColorAt(0.5, QColor(75, 80, 95, int(220 * alpha)))
    slider_grad.setColorAt(1.0, QColor(28, 30, 42, int(205 * alpha)))
    p.setBrush(slider_grad)
    p.setPen(QPen(QColor(55, 60, 75, int(120 * alpha)), 0.4))
    p.drawRoundedRect(QRectF(slider_x, slider_y, slider_w, slider_h), 1, 1)

    # ── 底部 LED 指示灯（发光二极管效果） ──
    for li in range(5):
        lx = console_left + 12 + li * 16
        ly = console_bot - 8
        pulse = 0.5 + 0.5 * abs(math.sin(anim_t * 4 + li * 1.3))
        led_colors = [(0, 200, 100), (0, 180, 240), (255, 160, 40), (0, 200, 100), (200, 100, 255)]
        lr, lg, lb = led_colors[li]
        # 外圈暗色金属环
        p.setBrush(QColor(30, 32, 42, int(180 * alpha)))
        p.setPen(QPen(QColor(50, 55, 68, int(130 * alpha)), 0.5))
        p.drawEllipse(QPointF(lx, ly), 3.2, 3.2)
        # 内圈发光色
        led_glow = QRadialGradient(lx, ly, 2.5)
        led_glow.setColorAt(0.0, QColor(min(lr + 80, 255), min(lg + 80, 255), min(lb + 80, 255),
                                        int(200 * alpha * pulse)))
        led_glow.setColorAt(0.7, QColor(lr, lg, lb, int(150 * alpha * pulse)))
        led_glow.setColorAt(1.0, QColor(lr // 2, lg // 2, lb // 2, 0))
        p.setBrush(led_glow)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(lx, ly), 2.5, 2.5)
        # 中心白色亮点
        p.setBrush(QColor(255, 255, 255, int(160 * alpha * pulse)))
        p.drawEllipse(QPointF(lx, ly), 0.8, 0.8)

    # ── 中央小屏幕 ──
    screen_x = console_left + console_w * 0.42
    screen_w = console_w * 0.16
    screen_h = panel_h * 0.65
    screen_y = console_top + 3
    # 屏幕外框
    p.setBrush(QColor(20, 22, 32, int(200 * alpha)))
    p.setPen(QPen(QColor(60, 70, 90, int(140 * alpha)), 0.8))
    p.drawRoundedRect(QRectF(screen_x - 1, screen_y - 1, screen_w + 2, screen_h + 2), 3, 3)
    # 屏幕面板
    p.setBrush(QColor(2, 8, 20, int(210 * alpha)))
    p.setPen(QPen(QColor(0, 140, 200, int(110 * alpha)), 0.5))
    p.drawRoundedRect(QRectF(screen_x, screen_y, screen_w, screen_h), 2, 2)
    # 波形
    wave_y = screen_y + screen_h / 2
    p.setPen(QPen(QColor(0, 200, 220, int(130 * alpha)), 0.5))
    for wx in range(int(screen_x + 2), int(screen_x + screen_w - 2), 2):
        p.drawPoint(QPointF(wx, wave_y + math.sin(wx * 0.5 + anim_t * 3) * 4))

# ═══════════════════════════════════════════
#  便捷入口
# ═══════════════════════════════════════════
def paint_starship_bridge(p: QPainter, rect: QRectF, center: QPointF,
                        size: float, anim_t: float,
                        hovered: bool = False, active: bool = True,
                        alpha: float = 1.0,
                        drift_x: float = 0.0, drift_y: float = 0.0,
                        role: str = "user",
                        draw_planets: bool = True):
    """完整舰桥场景：12 层渲染管线（由远到近）"""
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.HighQualityAntialiasing)

    # L1: 星场背景（4 层深度）
    paint_starfield(p, rect, anim_t, alpha, drift_x=drift_x, drift_y=drift_y)
    # L2: 星云带
    paint_nebula_belt(p, rect, anim_t, alpha)
    # L3: 小行星碎片
    paint_asteroids(p, rect, anim_t, alpha)
    # L4: 景深大气层雾
    _paint_depth_atmosphere(p, rect, anim_t, alpha)
    # L5: 侧窗框支柱
    _paint_side_pillars(p, rect, alpha)
    # L6: 曲面玻璃（Fresnel）
    _paint_glass(p, rect, anim_t, alpha)
    # L7: 体积光柱
    _paint_volumetric_light(p, rect, anim_t, alpha)
    # L8: 模块星球（球体光照）
    if draw_planets:
        _paint_bridge_planets(p, rect, anim_t, alpha, role=role)
    # L9: HUD 对焦括号
    _paint_hud_brackets(p, rect, anim_t, alpha)
    # L10: 数据流飘字
    _paint_data_stream(p, rect, anim_t, alpha)
    # L11: 穹顶框架肋骨
    _paint_canopy(p, rect, alpha)
    # L12: 3D 凹凸控制台
    _paint_console(p, rect, anim_t, alpha)
    # L13: 数字员工屏幕（由调用方传入 employees 数据，若无数据则跳过）
    # 在 paint_starship_bridge 外部调用，见 paint_employee_screen


# ═══════════════════════════════════════════
#  L13: 数字员工状态屏 — 2×3 卡片网格
# ═══════════════════════════════════════════

# 员工核心颜色映射（与 digital_employee.py 一致）
_EMP_SHAPE_PATHS = {
    "hexagon":  None,  # 六边形由外部绘制
    "circle":   None,
    "square":   None,
    "triangle": None,
    "diamond":  None,
    "pentagon": None,
}

# 状态色
_STATUS_COLORS = {
    "idle":      QColor(60, 80, 100),
    "thinking":  QColor(0, 180, 255),
    "working":   QColor(80, 220, 140),
    "reporting": QColor(255, 180, 60),
}


def _paint_shape_icon(p: QPainter, cx: float, cy: float, r: float, shape: str,
                      color: QColor, alpha: float):
    """在 (cx, cy) 中心绘制员工形状图标"""
    p.setBrush(QColor(color.red(), color.green(), color.blue(), int(60 * alpha)))
    p.setPen(QPen(QColor(color.red(), color.green(), color.blue(), int(180 * alpha)), 0.8))

    if shape == "hexagon":
        pts = []
        for i in range(6):
            a = math.pi / 6 + i * math.pi / 3
            pts.append(QPointF(cx + r * math.cos(a), cy + r * math.sin(a)))
        path = QPainterPath()
        path.moveTo(pts[0])
        for pt in pts[1:]:
            path.lineTo(pt)
        path.closeSubpath()
        p.drawPath(path)
    elif shape == "diamond":
        path = QPainterPath()
        path.moveTo(cx, cy - r)
        path.lineTo(cx + r, cy)
        path.lineTo(cx, cy + r)
        path.lineTo(cx - r, cy)
        path.closeSubpath()
        p.drawPath(path)
    elif shape == "triangle":
        path = QPainterPath()
        path.moveTo(cx, cy - r)
        path.lineTo(cx + r, cy + r * 0.6)
        path.lineTo(cx - r, cy + r * 0.6)
        path.closeSubpath()
        p.drawPath(path)
    elif shape == "pentagon":
        pts = []
        for i in range(5):
            a = -math.pi / 2 + i * 2 * math.pi / 5
            pts.append(QPointF(cx + r * math.cos(a), cy + r * math.sin(a)))
        path = QPainterPath()
        path.moveTo(pts[0])
        for pt in pts[1:]:
            path.lineTo(pt)
        path.closeSubpath()
        p.drawPath(path)
    elif shape == "square":
        p.drawRoundedRect(QRectF(cx - r, cy - r, r * 2, r * 2), 1.5, 1.5)
    else:  # circle / default
        p.drawEllipse(QPointF(cx, cy), r, r)


def paint_employee_screen(p: QPainter, rect: QRectF, anim_t: float,
                          alpha: float,
                          employees: list = None):
    """L13: 数字员工状态屏幕 — 在舰桥中部渲染 2×3 员工卡片"""
    if not employees or alpha < 0.2:
        return

    w, h = rect.width(), rect.height()
    left, top = rect.left(), rect.top()

    # ── 面板区域：居中偏下，控制台上方 ──
    panel_margin_x = 14
    panel_w = w - panel_margin_x * 2
    panel_h = 62
    panel_x = left + panel_margin_x
    panel_y = top + h - 108  # 控制台 (38px) 上方留 gap

    # 面板背景 — 半透明深色
    p.setBrush(QColor(4, 8, 20, int(185 * alpha)))
    p.setPen(QPen(QColor(0, 180, 255, int(50 * alpha)), 0.6))
    p.drawRoundedRect(QRectF(panel_x, panel_y, panel_w, panel_h), 5, 5)

    # ── 标题 ──
    font = p.font()
    font.setPointSizeF(5.5)
    p.setFont(font)
    p.setPen(QColor(100, 160, 200, int(160 * alpha)))
    p.drawText(QRectF(panel_x + 6, panel_y - 1, panel_w - 12, 10),
               Qt.AlignLeft | Qt.AlignVCenter, "舰队状态")

    # ── 2×3 网格 ──
    cols = 3
    rows = 2
    card_w = (panel_w - 16) / cols
    card_h = (panel_h - 16) / rows
    grid_x = panel_x + 8
    grid_y = panel_y + 10

    for idx, emp in enumerate(employees[:6]):
        col = idx % cols
        row = idx // cols
        cx_card = grid_x + col * card_w
        cy_card = grid_y + row * card_h

        # 卡片背景
        p.setBrush(QColor(8, 14, 30, int(140 * alpha)))
        p.setPen(QPen(QColor(30, 50, 70, int(60 * alpha)), 0.4))
        p.drawRoundedRect(QRectF(cx_card + 1, cy_card + 1, card_w - 2, card_h - 2), 3, 3)

        # 状态指示色
        status_color = _STATUS_COLORS.get(
            emp.status.value if hasattr(emp.status, 'value') else str(emp.status),
            QColor(60, 80, 100))

        # 形状图标（左侧）
        shape_r = min(card_h * 0.32, 7)
        shape_cx = cx_card + shape_r + 5
        shape_cy = cy_card + card_h / 2
        role_color = QColor(*_parse_hex_color(emp.role_color)) if hasattr(emp, 'role_color') else QColor(100, 100, 100)
        _paint_shape_icon(p, shape_cx, shape_cy, shape_r, emp.shape, role_color, alpha)

        # 状态脉冲点
        pulse_r = 2.2
        pulse_cx = shape_cx
        pulse_cy = shape_cy + shape_r + 2
        pulse_alpha = 140 + int(115 * (0.5 + 0.5 * math.sin(anim_t * 5 + idx * 1.3)))
        p.setBrush(QColor(status_color.red(), status_color.green(), status_color.blue(),
                          int(pulse_alpha * alpha)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(pulse_cx, pulse_cy), pulse_r, pulse_r)

        # 名字
        font.setPointSizeF(5.5)
        p.setFont(font)
        p.setPen(QColor(160, 200, 230, int(200 * alpha)))
        name_x = cx_card + shape_r * 2 + 11
        p.drawText(QRectF(name_x, cy_card + 2, card_w - name_x + cx_card - 4, 11),
                   Qt.AlignLeft | Qt.AlignVCenter, emp.name)

        # 角色
        font.setPointSizeF(4.2)
        p.setFont(font)
        p.setPen(QColor(100, 140, 180, int(140 * alpha)))
        role_str = getattr(emp, 'role', '')
        p.drawText(QRectF(name_x, cy_card + 13, card_w - name_x + cx_card - 4, 9),
                   Qt.AlignLeft | Qt.AlignVCenter, role_str)

        # 状态文字
        status_text = {
            "idle": "待命", "thinking": "思考", "working": "执行", "reporting": "汇报"
        }.get(emp.status.value if hasattr(emp.status, 'value') else str(emp.status), "待命")
        font.setPointSizeF(4.0)
        p.setFont(font)
        p.setPen(QColor(status_color.red(), status_color.green(), status_color.blue(),
                        int(170 * alpha)))
        p.drawText(QRectF(cx_card + 1, cy_card + card_h - 10, card_w - 2, 8),
                   Qt.AlignCenter, status_text)

        # 进度条（工作中）
        if hasattr(emp, 'status') and hasattr(emp.status, 'value') and emp.status.value == "working":
            bar_x = cx_card + 2
            bar_y = cy_card + card_h - 3
            bar_w = card_w - 4
            bar_h = 1.2
            prog = min(getattr(emp, 'progress', 0) / 100.0, 1.0)
            p.setBrush(QColor(20, 30, 40, int(100 * alpha)))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 0.5, 0.5)
            p.setBrush(QColor(status_color.red(), status_color.green(), status_color.blue(),
                              int(170 * alpha)))
            p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w * prog, bar_h), 0.5, 0.5)


def _parse_hex_color(hex_str: str) -> tuple:
    """解析 #rrggbb 格式颜色字符串为 (r, g, b)"""
    h = hex_str.lstrip('#')
    if len(h) == 6:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    return (100, 100, 100)


def paint_starship_scene(p: QPainter, rect: QRectF, center: QPointF,
                        size: float, anim_t: float,
                        hovered: bool = False, active: bool = True,
                        alpha: float = 1.0,
                        drift_x: float = 0.0, drift_y: float = 0.0):
    """旧接口兼容，转发到 bridge 场景"""
    paint_starship_bridge(p, rect, center, size, anim_t,
                        hovered=hovered, active=active, alpha=alpha,
                        drift_x=drift_x, drift_y=drift_y)




# ═══════════════════════════════════════════
#  Starship4DWidget — 四维星舰 QOpenGLWidget 渲染器
#  （3D空间 + 时间维度动画）
# ═══════════════════════════════════════════

_VS = """#version 330 core
layout(location=0)in vec3 aPos;layout(location=1)in vec3 aNormal;
layout(location=2)in vec3 aColor;layout(location=3)in float aEnergy;
uniform mat4 uModel,uView,uProjection;uniform float uTime,uEnergyPulse;
out vec3 vPos,vNormal,vColor;out float vEnergy,vFresnel;
void main(){
vec4 wp=uModel*vec4(aPos,1.0);
gl_Position=uProjection*uView*wp;
vPos=wp.xyz;vNormal=normalize(mat3(uModel)*aNormal);
vColor=aColor;vEnergy=aEnergy;
vFresnel=1.0-abs(dot(vNormal,normalize(-wp.xyz)));
}"""

_FS = """#version 330 core
in vec3 vPos,vNormal,vColor;in float vEnergy,vFresnel;
uniform vec3 uLightDir,uLightColor,uAmbient,uViewPos;
uniform float uTime,uEnergyPulse;out vec4 FragColor;
void main(){
vec3 N=normalize(vNormal),L=normalize(uLightDir),V=normalize(uViewPos-vPos);
float diff=max(dot(N,L),0.0);
vec3 H=normalize(L+V);
float spec=pow(max(dot(N,H),0.0),128.0);
vec3 bc=vColor;
if(vEnergy>0.5){float w=sin(uTime*4.0+vPos.x*12.0+vPos.y*8.0)*0.5+0.5;
float pulse=0.6+0.4*w*uEnergyPulse;
bc=mix(vColor,vec3(0.2,0.55,1.0),pulse);}
vec3 amb=uAmbient*bc;
vec3 diffC=uLightColor*bc*diff*1.0;
vec3 specC=uLightColor*spec*0.6;
vec3 fg=vec3(0.15,0.35,0.7)*vFresnel*vFresnel*0.7;
FragColor=vec4(amb+diffC+specC+fg,1.0);}"""

_PVS = """#version 330 core
layout(location=0)in vec3 aPos;layout(location=1)in vec3 aColor;
layout(location=2)in float aAlpha;layout(location=3)in float aSize;
uniform mat4 uView,uProjection;out vec3 vColor;out float vAlpha;
void main(){gl_Position=uProjection*uView*vec4(aPos,1.0);
gl_PointSize=aSize*(200.0/-gl_Position.w);vColor=aColor;vAlpha=aAlpha;}"""

_PFS = """#version 330 core
in vec3 vColor;in float vAlpha;out vec4 FragColor;
void main(){float d=length(gl_PointCoord-0.5)*2.0;
float a=(1.0-d)*(1.0-d)*vAlpha;FragColor=vec4(vColor,a);}"""


class Starship4DWidget(QOpenGLWidget):
    """3D OpenGL 碟形星舰渲染器。

    经典碟形星舰外观：宽碟主体 + 工程舱 + 双曲速引擎舱 + 舰桥
    四维：3D 空间（可旋转立体模型）+ 时间维度（持续动画）
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(260, 260)
        self.resize(400, 400)
        self._gl = None
        self._cam_theta = 0.0
        self._cam_phi = 0.45
        self._cam_dist = 4.0
        self._last_mouse = None
        self._mouse_down = False
        self._anim_t = 0.0
        self._particles = []
        self._max_parts = 280
        self._pseed = 0
        self._prog = None
        self._pprog = None
        # 碟形主舰体 VAO
        self._h_vao = self._h_vbo = self._h_ebo = None
        self._h_ic = 0
        # 工程舱 VAO
        self._s_vao = self._s_vbo = self._s_ebo = None
        self._s_ic = 0
        # 曲速引擎舱 + 支架 VAO
        self._n_vao = self._n_vbo = self._n_ebo = None
        self._n_ic = 0
        # 偏导仪发光碟 VAO
        self._d_vao = self._d_vbo = self._d_ebo = None
        self._d_ic = 0
        # 舰桥 VAO
        self._b_vao = self._b_vbo = self._b_ebo = None
        self._b_ic = 0
        # 碟缘能量环 VAO
        self._r_vao = self._r_vbo = self._r_ebo = None
        self._r_ic = 0
        self._pvbo = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)
        fmt = QSurfaceFormat()
        fmt.setSamples(4)
        fmt.setDepthBufferSize(24)
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        self.setFormat(fmt)

    def _tick(self):
        dt = 0.016
        self._anim_t += dt
        if not self._mouse_down:
            self._cam_theta += dt * 0.314
        self._upd_parts(dt)
        self.update()

    def _upd_parts(self, dt):
        # 双曲速引擎舱尾喷口位置（z=-0.65 向后喷射约 0.4 单位）
        eps = [(-0.36, 0.24, -0.65), (0.36, 0.24, -0.65)]
        for _ in range(6):
            if len(self._particles) >= self._max_parts:
                break
            self._pseed += 1
            s = self._pseed * 0.382
            ep = eps[self._pseed % 2]
            vx = math.sin(s * 7.3) * 0.04
            vy = math.sin(s * 5.1) * 0.03
            vz = -0.28 - abs(math.sin(s * 3.7)) * 0.22
            life = 1.0 + abs(math.sin(s * 2.3)) * 1.5
            # 蓝色引擎尾焰为主，偶有橙红火花
            r, g, b = (0.2, 0.5, 0.95)
            if self._pseed % 7 == 0:
                r, g, b = (0.85, 0.35, 0.15)
            self._particles.append([ep[0], ep[1], ep[2], vx, vy, vz, life, r, g, b])
        for p in self._particles:
            p[0] += p[3] * dt
            p[1] += p[4] * dt
            p[2] += p[5] * dt
            p[6] -= dt
        self._particles = [p for p in self._particles if p[6] > 0]

    def initializeGL(self):
        self._gl = self.context().versionFunctions()
        if self._gl is None:
            raise RuntimeError("无法获取OpenGL函数——需要OpenGL 3.3+环境")
        self._gl.initializeOpenGLFunctions()
        gl = self._gl
        gl.glClearColor(0.06, 0.06, 0.16, 1.0)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        self._prog = self._mkprog(_VS, _FS)
        self._pprog = self._mkprog(_PVS, _PFS)
        self._build_hull()
        self._build_secondary()
        self._build_nacelles()
        self._build_deflector()
        self._build_bridge()
        self._build_ring()

    def _mkprog(self, vs, fs):
        p = QOpenGLShaderProgram(self)
        if not p.addShaderFromSourceCode(QOpenGLShader.Vertex, vs):
            raise RuntimeError(f"VS: {p.log()}")
        if not p.addShaderFromSourceCode(QOpenGLShader.Fragment, fs):
            raise RuntimeError(f"FS: {p.log()}")
        if not p.link():
            raise RuntimeError(f"Link: {p.log()}")
        return p

    def resizeGL(self, w, h):
        self._gl.glViewport(0, 0, w, h)

    def paintGL(self):
        gl = self._gl
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        w, h = self.width(), self.height()
        aspect = w / max(h, 1)
        proj = QMatrix4x4()
        proj.perspective(45.0, aspect, 0.1, 20.0)
        view = QMatrix4x4()
        ex = self._cam_dist * math.cos(self._cam_phi) * math.sin(self._cam_theta)
        ey = self._cam_dist * math.sin(self._cam_phi)
        ez = self._cam_dist * math.cos(self._cam_phi) * math.cos(self._cam_theta)
        view.lookAt(QVector3D(ex, ey, ez), QVector3D(0, 0.05, 0), QVector3D(0, 1, 0))
        model = QMatrix4x4()
        model.rotate(self._anim_t * 360.0 / 20.0, 0, 1, 0)
        ld = QVector3D(0.6, 1.2, 0.8).normalized()
        ep = 0.5 + 0.5 * math.sin(self._anim_t * 2.5)

        prog = self._prog
        prog.bind()
        prog.setUniformValue("uModel", model)
        prog.setUniformValue("uView", view)
        prog.setUniformValue("uProjection", proj)
        prog.setUniformValue("uTime", self._anim_t)
        prog.setUniformValue("uEnergyPulse", ep)
        prog.setUniformValue("uLightDir", ld)
        prog.setUniformValue("uLightColor", QVector3D(1.0, 1.0, 1.0))
        prog.setUniformValue("uAmbient", QVector3D(0.32, 0.35, 0.45))
        prog.setUniformValue("uViewPos", QVector3D(ex, ey, ez))

        # 1. 工程舰体（secondary hull）——在碟盘后方，先画
        self._s_vao.bind()
        gl.glDrawElements(gl.GL_TRIANGLES, self._s_ic, gl.GL_UNSIGNED_INT, None)
        self._s_vao.release()

        # 2. 偏导仪发光碟
        self._d_vao.bind()
        gl.glDrawElements(gl.GL_TRIANGLES, self._d_ic, gl.GL_UNSIGNED_INT, None)
        self._d_vao.release()

        # 3. 碟缘能量环（脉动）
        self._r_vao.bind()
        gl.glDrawElements(gl.GL_TRIANGLES, self._r_ic, gl.GL_UNSIGNED_INT, None)
        self._r_vao.release()

        # 4. 碟形主舰体
        self._h_vao.bind()
        gl.glDrawElements(gl.GL_TRIANGLES, self._h_ic, gl.GL_UNSIGNED_INT, None)
        self._h_vao.release()

        # 5. 舰桥穹顶
        self._b_vao.bind()
        gl.glDrawElements(gl.GL_TRIANGLES, self._b_ic, gl.GL_UNSIGNED_INT, None)
        self._b_vao.release()

        # 6. 曲速引擎支架
        self._n_vao.bind()
        gl.glDrawElements(gl.GL_TRIANGLES, self._n_ic, gl.GL_UNSIGNED_INT, None)
        self._n_vao.release()

        prog.release()

        # 7. 引擎粒子尾焰（从引擎舱后端向后喷射）
        self._draw_parts(gl, view, proj)

    def _draw_parts(self, gl, view, proj):
        if not self._particles:
            return
        import ctypes
        verts = []
        for p in self._particles:
            px, py, pz, _, _, _, life, cr, cg, cb = p
            a = life / 1.5
            sz = 3.0 + (1.0 - life / 2.0) * 6.0
            verts.extend([px, py, pz, cr, cg, cb, min(a, 1.0), sz])
        cnt = len(verts) // 8
        if cnt == 0:
            return
        data = (ctypes.c_float * len(verts))(*verts)
        if self._pvbo is None:
            self._pvbo = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
            self._pvbo.create()
        self._pvbo.bind()
        self._pvbo.allocate(data, len(verts) * 4)
        stride = 8 * 4
        pp = self._pprog
        pp.bind()
        pp.setUniformValue("uView", view)
        pp.setUniformValue("uProjection", proj)
        pp.enableAttributeArray(0)
        pp.setAttributeBuffer(0, gl.GL_FLOAT, 0, 3, stride)
        pp.enableAttributeArray(1)
        pp.setAttributeBuffer(1, gl.GL_FLOAT, 3 * 4, 3, stride)
        pp.enableAttributeArray(2)
        pp.setAttributeBuffer(2, gl.GL_FLOAT, 6 * 4, 1, stride)
        pp.enableAttributeArray(3)
        pp.setAttributeBuffer(3, gl.GL_FLOAT, 7 * 4, 1, stride)
        gl.glDrawArrays(gl.GL_POINTS, 0, cnt)
        self._pvbo.release()
        pp.release()

    # ═══════════════════════════════════════════

    # ═══════════════════════════════════════════
    #  VAO 设置辅助方法
    # ═══════════════════════════════════════════

    def _setup_vao(self, verts, idxs, vao_attr, vbo_attr, ebo_attr, ic_attr):
        """通用 VAO 设置：上传顶点/索引数据、绑定着色器属性。"""
        import ctypes
        gl = self._gl
        vdata = (ctypes.c_float * len(verts))(*verts)
        idata = (ctypes.c_uint * len(idxs))(*idxs)
        vao = QOpenGLVertexArrayObject(self)
        vao.create()
        vao.bind()
        vbo = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
        vbo.create()
        vbo.bind()
        vbo.allocate(vdata, len(verts) * 4)
        ebo = QOpenGLBuffer(QOpenGLBuffer.IndexBuffer)
        ebo.create()
        ebo.bind()
        ebo.allocate(idata, len(idxs) * 4)
        stride = 10 * 4
        self._prog.bind()
        self._prog.enableAttributeArray(0)
        self._prog.setAttributeBuffer(0, gl.GL_FLOAT, 0, 3, stride)
        self._prog.enableAttributeArray(1)
        self._prog.setAttributeBuffer(1, gl.GL_FLOAT, 3 * 4, 3, stride)
        self._prog.enableAttributeArray(2)
        self._prog.setAttributeBuffer(2, gl.GL_FLOAT, 6 * 4, 3, stride)
        self._prog.enableAttributeArray(3)
        self._prog.setAttributeBuffer(3, gl.GL_FLOAT, 9 * 4, 1, stride)
        self._prog.release()
        setattr(self, vao_attr, vao)
        setattr(self, vbo_attr, vbo)
        setattr(self, ebo_attr, ebo)
        setattr(self, ic_attr, len(idxs))
        vao.release()

    # ═══════════════════════════════════════════
    #  碟形主舰体几何（进取号风格扁碟盘）
    # ═══════════════════════════════════════════

    def _build_hull(self):
        """进取号风格极扁椭球碟盘：半径0.6，中心厚度约0.08，前缘略上翘。"""
        import ctypes
        gl = self._gl
        rx, ry, rz = 0.6, 0.04, 0.6          # 极扁椭球
        cx, cy, cz = 0.0, 0.0, 0.1            # 中心
        tilt = 0.07                            # 前缘上翘攻角 ~4°
        r_seg = 36                             # 径向段数
        top_bands = 5                          # 上半球段数
        bot_bands = 5                          # 下半球段数（使总纵段=5×2=10，中线+上下各5）
        hc = (0.76, 0.80, 0.84)               # 亮银灰金属
        ec = (0.19, 0.38, 0.63)               # 能量蓝 #3060A0
        stripe_every = 6                       # 每6段一条能量蓝纹

        verts = []
        idxs = []

        def rotate_x(x, y, z, ang):
            ca, sa = math.cos(ang), math.sin(ang)
            ny = y * ca - z * sa
            nz = y * sa + z * ca
            return x, ny, nz

        def av(x, y, z, nx, ny, nz, r, g, b, e):
            verts.extend([x, y, z, nx, ny, nz, r, g, b, e])

        def ellipsoid_vert(theta, phi):
            """返回椭球面上的点坐标和法线（局部坐标，不含倾斜）。"""
            sr = math.sin(phi)
            cr_phi = math.cos(phi)
            x = rx * sr * math.cos(theta)
            y = ry * cr_phi
            z = rz * sr * math.sin(theta)
            if sr < 1e-6:
                nx, ny, nz = 0.0, 1.0, 0.0
            else:
                nx = math.cos(theta) / rx
                ny = cr_phi / ry
                nz = math.sin(theta) / rz
                nl = math.sqrt(nx * nx + ny * ny + nz * nz)
                nx, ny, nz = nx / nl, ny / nl, nz / nl
            return x, y, z, nx, ny, nz

        # ── 上半球：φ 从 0（极顶）到 π/2（赤道），共 top_bands+1 圈 ──
        top_ring_count = top_bands + 1
        for ri in range(top_ring_count):
            phi = ri / top_bands * (math.pi / 2)
            for ti in range(r_seg):
                theta = ti / r_seg * math.pi * 2
                lx, ly, lz, lnx, lny, lnz = ellipsoid_vert(theta, phi)
                rx_, ry_, rz_ = rotate_x(lx, ly, lz, tilt)
                rnx, rny, rnz = rotate_x(lnx, lny, lnz, tilt)
                is_stripe = (ti % stripe_every == 0)
                cr, cg, cb = ec if is_stripe else hc
                ee = 0.8 if is_stripe else 0.0
                av(cx + rx_, cy + ry_, cz + rz_, rnx, rny, rnz, cr, cg, cb, ee)

        # 上半球环间三角带
        for ri in range(top_bands):
            r0 = ri * r_seg
            r1 = (ri + 1) * r_seg
            for ti in range(r_seg):
                tn = (ti + 1) % r_seg
                a0, a1 = r0 + ti, r0 + tn
                b0, b1 = r1 + ti, r1 + tn
                idxs.extend([a0, b0, a1, a1, b0, b1])

        top_first_ring = 0                     # ri=0 即极点圈
        top_last_ring = top_bands * r_seg      # ri=top_bands 即赤道圈
        # 极点扇面：ri=0 所有顶点重合，用第一个顶点作为极顶
        for ti in range(r_seg):
            tn = (ti + 1) % r_seg
            idxs.extend([top_first_ring + ti, top_last_ring + ti, top_last_ring + tn])

        # ── 下半球：φ 从 π/2（赤道）到 π（底极），共 bot_bands+1 圈 ──
        bot_start = top_ring_count * r_seg     # 顶点起始索引
        bot_ring_count = bot_bands + 1
        for ri in range(bot_ring_count):
            phi = math.pi / 2 + ri / bot_bands * (math.pi / 2)
            for ti in range(r_seg):
                theta = ti / r_seg * math.pi * 2
                lx, ly, lz, lnx, lny, lnz = ellipsoid_vert(theta, phi)
                rx_, ry_, rz_ = rotate_x(lx, ly, lz, tilt)
                rnx, rny, rnz = rotate_x(lnx, lny, lnz, tilt)
                is_stripe = (ti % stripe_every == 0)
                cr, cg, cb = ec if is_stripe else hc
                ee = 0.8 if is_stripe else 0.0
                av(cx + rx_, cy + ry_, cz + rz_, rnx, rny, rnz, cr, cg, cb, ee)

        # 下半球环间三角带
        for ri in range(bot_bands):
            r0 = bot_start + ri * r_seg
            r1 = bot_start + (ri + 1) * r_seg
            for ti in range(r_seg):
                tn = (ti + 1) % r_seg
                a0, a1 = r0 + ti, r0 + tn
                b0, b1 = r1 + ti, r1 + tn
                idxs.extend([a0, b0, a1, a1, b0, b1])

        bot_first_ring = bot_start               # ri=0 即赤道圈
        bot_last_ring = bot_start + bot_bands * r_seg  # ri=bot_bands 即底极圈
        # 底极扇面：ri=bot_bands 所有顶点重合于底极
        for ti in range(r_seg):
            tn = (ti + 1) % r_seg
            idxs.extend([bot_last_ring + ti, bot_first_ring + ti, bot_first_ring + tn])

        self._setup_vao(verts, idxs, '_h_vao', '_h_vbo', '_h_ebo', '_h_ic')

    # ═══════════════════════════════════════════
    #  碟缘能量环几何（进取号风格脉动环带）
    # ═══════════════════════════════════════════

    def _build_ring(self):
        """碟盘外缘发光环带：沿碟盘最宽截面，能量蓝色，随时间脉动。"""
        r_seg = 36
        rr = 0.62                            # 略突出于碟盘外缘
        y_top = 0.006
        y_bot = -0.006
        cz = 0.1                             # 碟盘中心 z 坐标
        ec = (0.15, 0.40, 0.75)

        verts = []
        idxs = []

        def rv(x, y, z, nx, ny, nz, r, g, b, e):
            verts.extend([x, y, z, nx, ny, nz, r, g, b, e])

        for i in range(r_seg + 1):
            ang = i / r_seg * math.pi * 2
            cx = rr * math.cos(ang)
            sz = rr * math.sin(ang)
            nx = math.cos(ang)
            nz = math.sin(ang)
            rv(cx, y_top, cz + sz, nx, 0.0, nz, *ec, 1.0)
            rv(cx, y_bot, cz + sz, nx, 0.0, nz, *ec, 1.0)

        for i in range(r_seg):
            a0 = i * 2
            a1 = (i + 1) * 2
            idxs.extend([a0, a1, a0 + 1, a0 + 1, a1, a1 + 1])

        self._setup_vao(verts, idxs, '_r_vao', '_r_vbo', '_r_ebo', '_r_ic')

    # ═══════════════════════════════════════════
    #  舰桥几何（进取号风格扁半球穹顶）
    # ═══════════════════════════════════════════

    def _build_bridge(self):
        """舰桥穹顶：碟盘顶部偏后的扁半球形凸起。"""
        bc = (0.42, 0.44, 0.50)              # 浅银灰
        bx, by, bz = 0.0, 0.04, 0.05         # 中心（碟盘上方偏后）
        br, bh = 0.08, 0.025                  # 半径、高度
        r_seg = 16
        rings = 3                             # 纬度圈数

        verts = []
        idxs = []

        def av(x, y, z, nx, ny, nz, r, g, b, e):
            verts.extend([x, y, z, nx, ny, nz, r, g, b, e])

        # 顶点
        av(bx, by + bh, bz, 0, 1, 0, *bc, 0.3)
        top_idx = 0

        # 纬度圈
        for ri in range(rings):
            phi = (ri + 1) / (rings + 1) * math.pi / 2
            r = br * math.cos(phi)
            y_off = bh * math.sin(phi)
            for i in range(r_seg):
                ang = i / r_seg * math.pi * 2
                nx = math.cos(phi) * math.cos(ang)
                ny = math.sin(phi)
                nz = math.cos(phi) * math.sin(ang)
                x = r * math.cos(ang)
                z = r * math.sin(ang)
                av(bx + x, by + y_off, bz + z, nx, ny, nz, *bc, 0.1)

        # 顶部扇面
        for i in range(r_seg):
            nxt = (i + 1) % r_seg
            idxs.extend([top_idx, 1 + i, 1 + nxt])

        # 环间三角带
        for ri in range(rings - 1):
            r0 = 1 + ri * r_seg
            r1 = 1 + (ri + 1) * r_seg
            for i in range(r_seg):
                nxt = (i + 1) % r_seg
                a0, a1 = r0 + i, r0 + nxt
                b0, b1 = r1 + i, r1 + nxt
                idxs.extend([a0, b0, a1, a1, b0, b1])

        # 底部环（贴合碟盘顶面）
        base_ring = 1 + (rings - 1) * r_seg
        bb = by
        bbr = br
        av(bx, bb, bz, 0, -1, 0, *bc, 0)
        base_c = len(verts) // 10 - 1
        for i in range(r_seg):
            ang = i / r_seg * math.pi * 2
            av(bx + bbr * math.cos(ang), bb, bz + bbr * math.sin(ang), 0, -1, 0, *bc, 0)
        base_start = len(verts) // 10 - r_seg
        for i in range(r_seg):
            nxt = (i + 1) % r_seg
            a0, a1 = base_ring + i, base_ring + nxt
            b0, b1 = base_start + i, base_start + nxt
            idxs.extend([a0, b0, a1, a1, b0, b1])
        for i in range(r_seg):
            nxt = (i + 1) % r_seg
            idxs.extend([base_c, base_start + nxt, base_start + i])

        self._setup_vao(verts, idxs, '_b_vao', '_b_vbo', '_b_ebo', '_b_ic')

    # ═══════════════════════════════════════════
    #  工程舰体几何（进取号风格独立圆柱体）
    # ═══════════════════════════════════════════

    def _build_secondary(self):
        """独立圆柱形工程舰体：从碟盘下方中部延伸到后方，前端带偏导仪碟。"""
        sc = (0.76, 0.80, 0.84)              # 亮银灰金属
        dc = (0.20, 0.24, 0.30)              # 暗纹
        yc = -0.12                            # 中心 y
        z_start, z_end = -0.12, -0.78
        r_seg = 16
        z_steps = 10

        verts = []
        idxs = []

        def av(x, y, z, nx, ny, nz, r, g, b, e):
            verts.extend([x, y, z, nx, ny, nz, r, g, b, e])

        for zi in range(z_steps + 1):
            t = zi / z_steps
            z = z_start + t * (z_end - z_start)
            rad = 0.16 - t * 0.03            # 0.16 → 0.13 前粗后细
            for i in range(r_seg + 1):
                ang = i / r_seg * math.pi * 2
                x = rad * math.cos(ang)
                y = yc + rad * math.sin(ang)
                nx = math.cos(ang)
                ny = math.sin(ang)
                # 每45°一条暗纹（8条纵向纹路，r_seg=16 → 每2个segment一条）
                is_dark = (i % 2 == 0)
                cr, cg, cb = dc if is_dark else sc
                ee = 0.2 if is_dark else 0.0
                av(x, y, z, nx, ny, 0.0, cr, cg, cb, ee)

        vps = r_seg + 1
        for zi in range(z_steps):
            ba = zi * vps
            bb = (zi + 1) * vps
            for i in range(r_seg):
                a0, a1 = ba + i, ba + i + 1
                b0, b1 = bb + i, bb + i + 1
                idxs.extend([a0, b0, a1, a1, b0, b1])

        # 后端封口
        lb = z_steps
        last_rad = 0.13
        cap_yc = yc
        cap_z = z_end
        back_base = lb * vps
        av(0.0, cap_yc, cap_z, 0, 0, -1, *sc, 0)
        cap_c = len(verts) // 10 - 1
        for i in range(r_seg + 1):
            ang = i / r_seg * math.pi * 2
            av(last_rad * math.cos(ang), cap_yc + last_rad * math.sin(ang), cap_z, 0, 0, -1, *sc, 0)
        cap_start = len(verts) // 10 - (r_seg + 1)
        for i in range(r_seg):
            idxs.extend([cap_c, cap_start + i, cap_start + i + 1])

        self._setup_vao(verts, idxs, '_s_vao', '_s_vbo', '_s_ebo', '_s_ic')

    # ═══════════════════════════════════════════
    #  偏导仪发光碟几何（进取号风格）
    # ═══════════════════════════════════════════

    def _build_deflector(self):
        """偏导仪发光碟：工程舰体前端的蓝色发光小圆盘。"""
        dc = (0.15, 0.40, 0.75)              # 能量蓝
        ek = (0.10, 0.25, 0.50)              # 背部暗蓝
        disk_y = -0.12
        disk_z = -0.12
        disk_r = 0.12
        r_seg = 20

        verts = []
        idxs = []

        def av(x, y, z, nx, ny, nz, r, g, b, e):
            verts.extend([x, y, z, nx, ny, nz, r, g, b, e])

        # 中心顶点（向前凸出一点形成微锥）
        av(0.0, disk_y, disk_z - 0.04, 0, 0, -1, *dc, 1.0)
        center_idx = 0

        # 外圈（正面）
        for i in range(r_seg + 1):
            ang = i / r_seg * math.pi * 2
            x = disk_r * math.cos(ang)
            y = disk_y + disk_r * math.sin(ang)
            av(x, y, disk_z, 0, 0, -1, *dc, 0.95)

        for i in range(r_seg):
            nxt = (i + 1) % r_seg
            idxs.extend([center_idx, 1 + i, 1 + nxt])

        # 背面（向后凸出小锥体）
        back_c = len(verts) // 10
        av(0.0, disk_y, disk_z + 0.03, 0, 0, 1, *ek, 0.6)
        back_ci = back_c
        small_r = disk_r * 0.45
        for i in range(r_seg + 1):
            ang = i / r_seg * math.pi * 2
            av(small_r * math.cos(ang), disk_y + small_r * math.sin(ang), disk_z, 0, 0, 1, *ek, 0.5)
        back_start = back_ci + 1
        for i in range(r_seg):
            nxt = (i + 1) % r_seg
            idxs.extend([back_ci, back_start + nxt, back_start + i])

        self._setup_vao(verts, idxs, '_d_vao', '_d_vbo', '_d_ebo', '_d_ic')

    # ═══════════════════════════════════════════
    #  曲速引擎舱 + 支架几何（进取号风格）
    # ═══════════════════════════════════════════

    def _build_nacelles(self):
        """双曲速引擎舱：上翘支架 + 长圆柱引擎舱 + 前端橙红发光帽 + 后端蓝色喷口。"""
        nc = (0.28, 0.30, 0.38)              # 引擎舱中灰金属
        nst = (0.32, 0.36, 0.42)             # 略浅条纹
        pc = (0.22, 0.24, 0.30)              # 支架中灰
        r_seg = 12
        z_steps = 10

        verts = []
        idxs = []

        def av(x, y, z, nx, ny, nz, r, g, b, e):
            verts.extend([x, y, z, nx, ny, nz, r, g, b, e])

        for side in [-1, 1]:
            sx = side * 0.36
            nac_y = 0.24
            nac_z0, nac_z1 = -0.10, -0.65
            nac_r = 0.07

            # ── 引擎舱圆柱体 ──
            nac_start = len(verts) // 10
            for zi in range(z_steps + 1):
                t = zi / z_steps
                z = nac_z0 + t * (nac_z1 - nac_z0)
                for i in range(r_seg + 1):
                    ang = i / r_seg * math.pi * 2
                    x = nac_r * math.cos(ang)
                    y = nac_r * math.sin(ang)
                    nx = math.cos(ang)
                    ny = math.sin(ang)
                    # 中间凹槽分割线（在引擎舱 ~40% 处）
                    is_groove = (abs(t - 0.4) < 0.025)
                    ist = (i % 4 == 0 and not is_groove)
                    if is_groove:
                        cr, cg, cb = (0.14, 0.15, 0.22)
                        ee = 0.0
                    elif ist:
                        cr, cg, cb = nst
                        ee = 0.3
                    else:
                        cr, cg, cb = nc
                        ee = 0.0
                    av(sx + x, nac_y + y, z, nx, ny, 0.0, cr, cg, cb, ee)

            vps = r_seg + 1
            sec_base = nac_start
            for zi in range(z_steps):
                ba = sec_base + zi * vps
                bb = sec_base + (zi + 1) * vps
                for i in range(r_seg):
                    a0, a1 = ba + i, ba + i + 1
                    b0, b1 = bb + i, bb + i + 1
                    idxs.extend([a0, b0, a1, a1, b0, b1])

            # ── 前端橙红发光半球帽 ──
            fcap_r = 0.075
            fc = (0.85, 0.30, 0.10)          # 橙红发光
            frings = 3
            fcap_base = len(verts) // 10
            # 顶点
            av(sx, nac_y, nac_z0 - 0.07, 0, 0, -1, *fc, 1.0)
            fcap_top = fcap_base
            # 纬度圈
            for ri in range(frings):
                phi = (ri + 1) / (frings + 1) * math.pi / 2
                r = fcap_r * math.cos(phi)
                ofs = -fcap_r * math.sin(phi)
                for i in range(r_seg):
                    ang = i / r_seg * math.pi * 2
                    nx = math.cos(phi) * math.cos(ang)
                    ny = math.cos(phi) * math.sin(ang)
                    nz = -math.sin(phi)
                    av(sx + r * math.cos(ang), nac_y + r * math.sin(ang), nac_z0 + ofs, nx, ny, nz, *fc, 0.85)
            for i in range(r_seg):
                nxt = (i + 1) % r_seg
                idxs.extend([fcap_top, fcap_base + 1 + i, fcap_base + 1 + nxt])
            for ri in range(frings - 1):
                r0 = fcap_base + 1 + ri * r_seg
                r1 = fcap_base + 1 + (ri + 1) * r_seg
                for i in range(r_seg):
                    nxt = (i + 1) % r_seg
                    idxs.extend([r0 + i, r1 + i, r0 + nxt, r0 + nxt, r1 + i, r1 + nxt])

            # ── 后端蓝色发光喷口圈 ──
            erec = (0.15, 0.42, 0.78)         # 蓝色发光
            ering_start = len(verts) // 10
            er_r_outer = nac_r * 1.10
            er_r_inner = nac_r * 0.70
            er_len = 0.04
            for i in range(r_seg + 1):
                ang = i / r_seg * math.pi * 2
                nx = math.cos(ang)
                ny = math.sin(ang)
                av(sx + er_r_outer * math.cos(ang), nac_y + er_r_outer * math.sin(ang), nac_z1,
                   nx, ny, 0.0, *erec, 1.0)
                av(sx + er_r_outer * math.cos(ang), nac_y + er_r_outer * math.sin(ang), nac_z1 + er_len,
                   nx, ny, 0.0, *erec, 1.0)
            for i in range(r_seg):
                a0 = ering_start + i * 2
                a1 = ering_start + (i + 1) * 2
                idxs.extend([a0, a1, a0 + 1, a0 + 1, a1, a1 + 1])

            # 内环
            ein_start = len(verts) // 10
            for i in range(r_seg + 1):
                ang = i / r_seg * math.pi * 2
                nx = math.cos(ang)
                ny = math.sin(ang)
                av(sx + er_r_inner * math.cos(ang), nac_y + er_r_inner * math.sin(ang), nac_z1 + er_len,
                   -nx, -ny, 0.0, *erec, 1.0)
                av(sx + er_r_inner * math.cos(ang), nac_y + er_r_inner * math.sin(ang), nac_z1,
                   -nx, -ny, 0.0, *erec, 1.0)
            for i in range(r_seg):
                a0 = ein_start + i * 2
                a1 = ein_start + (i + 1) * 2
                idxs.extend([a0, a1, a0 + 1, a0 + 1, a1, a1 + 1])

            # ── 引擎舱前端圆盘（引擎罩与发光帽交接面）──
            fdisk_start = len(verts) // 10
            av(sx, nac_y, nac_z0, 0, 0, -1, *nc, 0.0)
            fdisk_c = fdisk_start
            for i in range(r_seg + 1):
                ang = i / r_seg * math.pi * 2
                av(sx + nac_r * math.cos(ang), nac_y + nac_r * math.sin(ang), nac_z0, 0, 0, -1, *nc, 0.0)
            fdisk_s = fdisk_c + 1
            for i in range(r_seg):
                idxs.extend([fdisk_c, fdisk_s + i, fdisk_s + i + 1])

            # ── 后端封口圆盘 ──
            edisk_start = len(verts) // 10
            av(sx, nac_y, nac_z1 + er_len, 0, 0, 1, *nc, 0.0)
            edisk_c = edisk_start
            for i in range(r_seg + 1):
                ang = i / r_seg * math.pi * 2
                av(sx + er_r_inner * math.cos(ang), nac_y + er_r_inner * math.sin(ang), nac_z1 + er_len, 0, 0, 1, *nc, 0.0)
            edisk_s = edisk_c + 1
            for i in range(r_seg):
                idxs.extend([edisk_c, edisk_s + i + 1, edisk_s + i])

            # ── 上翘支架（Pylon）──
            # 锚点在工程舰体中后部 → 引擎舱底部
            px0, py0, pz0 = side * 0.11, -0.10, -0.35
            px1, py1, pz1 = side * 0.33, 0.20, -0.35
            pw = 0.03                            # 半宽
            ph = 0.04                            # 半高

            # 支架方向
            dx = px1 - px0
            dy = py1 - py0
            dl = math.sqrt(dx * dx + dy * dy) + 0.001
            dx, dy = dx / dl, dy / dl
            snx = -dy
            sny = dx

            # 八边形截面（圆角矩形近似）
            oct_n = 8
            p_front = len(verts) // 10
            for k in range(oct_n):
                a = k / oct_n * math.pi * 2
                olx = snx * pw * math.cos(a)
                oly = sny * pw * math.cos(a)
                olz = ph * math.sin(a)
                onx = snx * math.cos(a)
                ony = sny * math.cos(a)
                onz = math.sin(a)
                onl = math.sqrt(onx * onx + ony * ony + onz * onz) + 0.001
                onx, ony, onz = onx / onl, ony / onl, onz / onl
                av(px0 + olx, py0 + oly, pz0 + olz, onx, ony, onz, *pc, 0.0)
                av(px1 + olx, py1 + oly, pz1 + olz, onx, ony, onz, *pc, 0.0)

            for k in range(oct_n):
                nk = (k + 1) % oct_n
                a0 = p_front + k
                a1 = p_front + nk
                b0 = p_front + oct_n + k
                b1 = p_front + oct_n + nk
                idxs.extend([a0, b0, a1, a1, b0, b1])

            # 前端封口
            fcap_p = len(verts) // 10
            av(px0, py0, pz0, -dx, -dy, 0.0, *pc, 0.0)
            for k in range(oct_n):
                a = k / oct_n * math.pi * 2
                olx = snx * pw * math.cos(a)
                oly = sny * pw * math.cos(a)
                olz = ph * math.sin(a)
                av(px0 + olx, py0 + oly, pz0 + olz, -dx, -dy, 0.0, *pc, 0.0)
            for k in range(oct_n):
                nk = (k + 1) % oct_n
                idxs.extend([fcap_p, fcap_p + 1 + k, fcap_p + 1 + nk])

            # 后端封口
            bcap_p = len(verts) // 10
            av(px1, py1, pz1, dx, dy, 0.0, *pc, 0.0)
            for k in range(oct_n):
                a = k / oct_n * math.pi * 2
                olx = snx * pw * math.cos(a)
                oly = sny * pw * math.cos(a)
                olz = ph * math.sin(a)
                av(px1 + olx, py1 + oly, pz1 + olz, dx, dy, 0.0, *pc, 0.0)
            for k in range(oct_n):
                nk = (k + 1) % oct_n
                idxs.extend([bcap_p, bcap_p + 1 + nk, bcap_p + 1 + k])

        self._setup_vao(verts, idxs, '_n_vao', '_n_vbo', '_n_ebo', '_n_ic')
    # ── 鼠标交互 ──

    def mousePressEvent(self, event):
        self._mouse_down = True
        self._last_mouse = (event.x(), event.y())

    def mouseMoveEvent(self, event):
        if not self._mouse_down or self._last_mouse is None:
            return
        dx = event.x() - self._last_mouse[0]
        dy = event.y() - self._last_mouse[1]
        self._last_mouse = (event.x(), event.y())
        self._cam_theta -= dx * 0.008
        self._cam_phi -= dy * 0.008
        self._cam_phi = max(-1.4, min(1.4, self._cam_phi))

    def mouseReleaseEvent(self, event):
        self._mouse_down = False
        self._last_mouse = None

    def wheelEvent(self, event):
        delta = event.angleDelta().y() / 120.0
        self._cam_dist -= delta * 0.3
        self._cam_dist = max(1.5, min(10.0, self._cam_dist))
