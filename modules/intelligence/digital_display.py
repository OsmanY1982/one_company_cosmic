# -*- coding: utf-8 -*-
"""
数字显示大屏样式 — 所有模块面板的 HUD/指挥中心主题
星空背景 + 扫描线 + 四角括号 + 星舰轮廓 + 模块星球，统一注入到任意 QWidget
"""
import math, random as _random
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient,
    QFont, QPainterPath, QRadialGradient,
)
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton

from .starship_painter import paint_starfield

# ═══════════ 全局调色板 ═══════════
HUD_COLORS = {
    "bg_primary":     "rgba(3, 6, 18, 200)",
    "bg_secondary":   "rgba(6, 12, 28, 190)",
    "border":         "rgba(0, 200, 240, 80)",
    "border_focus":   "rgba(0, 230, 255, 150)",
    "text_primary":   "#aaddff",
    "text_secondary": "#6699bb",
    "accent":         "#00ddff",
    "accent_dim":     "#00aacc",
    "warn":           "#ff9944",
    "success":        "#55ee99",
    "error":          "#ff5577",
    "glow":           "rgba(0, 180, 255, 15)",
    "scanline":       "rgba(0, 200, 255, 4)",
}


def apply_hud_theme(widget: QWidget):
    """将数字大屏 HUD 主题应用到任意 QWidget 及其子控件"""
    widget.setStyleSheet(f"""
        {widget.__class__.__name__} {{
            background: {HUD_COLORS['bg_primary']};
            border: 1px solid {HUD_COLORS['border']};
            border-radius: 10px;
        }}
    """)
    for child in widget.findChildren(QWidget):
        _style_child(child)


def _style_child(w: QWidget):
    cls = w.__class__.__name__
    if cls in ("QLabel",):
        w.setStyleSheet(f"""
            color: {HUD_COLORS['text_primary']};
            background: transparent;
            font-size: 12px;
        """)
    elif cls in ("QPushButton",):
        w.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 140, 220, 30);
                color: {HUD_COLORS['text_primary']};
                border: 1px solid {HUD_COLORS['border']};
                border-radius: 6px;
                padding: 6px 18px;
                font-size: 12px; font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(0, 180, 255, 55);
                border: 1px solid {HUD_COLORS['border_focus']};
                color: #eef4ff;
            }}
            QPushButton:pressed {{ background: rgba(0, 220, 255, 40); }}
        """)
    elif cls in ("QLineEdit", "QTextEdit", "QPlainTextEdit"):
        w.setStyleSheet(f"""
            {cls} {{
                background: {HUD_COLORS['bg_secondary']};
                color: {HUD_COLORS['text_primary']};
                border: 1px solid {HUD_COLORS['border']};
                border-radius: 6px; padding: 6px 10px; font-size: 12px;
                selection-background-color: rgba(0, 200, 240, 50);
            }}
            {cls}:focus {{ border: 1px solid {HUD_COLORS['border_focus']}; }}
        """)
    elif cls in ("QComboBox",):
        w.setStyleSheet(f"""
            QComboBox {{
                background: {HUD_COLORS['bg_secondary']};
                color: {HUD_COLORS['text_primary']};
                border: 1px solid {HUD_COLORS['border']};
                border-radius: 6px; padding: 4px 8px; font-size: 11px;
            }}
            QComboBox:hover {{ border: 1px solid {HUD_COLORS['border_focus']}; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{
                background: rgba(3, 6, 18, 245);
                color: #99ccee;
                border: 1px solid rgba(0, 180, 220, 60);
                selection-background-color: rgba(0, 160, 230, 45);
            }}
        """)
    elif cls in ("QTabWidget", "QTabBar"):
        w.setStyleSheet(f"""
            QTabWidget::pane {{
                background: transparent; border: none;
            }}
            QTabBar::tab {{
                background: rgba(0, 100, 180, 20);
                color: {HUD_COLORS['text_primary']};
                border: 1px solid {HUD_COLORS['border']};
                border-radius: 6px 6px 0 0;
                padding: 6px 16px; font-size: 11px;
            }}
            QTabBar::tab:selected {{
                background: rgba(0, 160, 240, 55);
                color: #eef8ff;
                border: 1px solid {HUD_COLORS['border_focus']};
            }}
        """)


# ═══════════ 模块星球定义 ═══════════
# 每个功能模块 = 一颗悬浮在星空中的星球 / 天体

PLANET_DEFS = {
    "ai_assistant": {
        "label": "AI ASSISTANT",
        "color": (60, 140, 255),        # 蓝色气态巨星
        "ring_color": (80, 160, 255),
        "radius_ratio": 0.08,            # 相对窗口宽度的比例
        "orbit_radius": 0.32,
        "orbit_speed": 0.35,
        "moons": 3,
        "type": "gas_giant",            # 气态巨星 — 带状条纹
    },
    "knowledge_base": {
        "label": "KNOWLEDGE",
        "color": (100, 240, 200),       # 水晶矿星 — 蓝绿色
        "ring_color": (140, 255, 220),
        "radius_ratio": 0.06,
        "orbit_radius": 0.28,
        "orbit_speed": 0.45,
        "moons": 1,
        "type": "crystal",              # 水晶矿星 — 几何晶面
    },
    "digital_worker": {
        "label": "WORKERS",
        "color": (255, 160, 60),        # 空间站 — 暖橙色
        "ring_color": (255, 180, 100),
        "radius_ratio": 0.07,
        "orbit_radius": 0.36,
        "orbit_speed": 0.50,
        "moons": 2,
        "type": "station",              # 空间站 — 六边形框架
    },
    "data_center": {
        "label": "DATA",
        "color": (180, 80, 255),        # 数据矩阵星 — 紫色
        "ring_color": (200, 110, 255),
        "radius_ratio": 0.055,
        "orbit_radius": 0.30,
        "orbit_speed": 0.40,
        "moons": 0,
        "type": "matrix",               # 矩阵星 — 网格纹理
    },
}


# ═══════════ 大屏装饰绘制 ═══════════

_SEED = 777


def _rng(offset=0):
    return _random.Random(_SEED + offset)


def paint_module_planets(p: QPainter, rect: QRectF, anim_t: float, alpha: float = 1.0):
    """在星空背景之上绘制四颗悬浮模块星球（带公转轨道）"""
    w, h = rect.width(), rect.height()
    cx, cy = rect.center().x(), rect.center().y()

    # 四颗星球分布在四角区域
    positions = [
        (cx - w * 0.22, cy - h * 0.20, "ai_assistant"),
        (cx + w * 0.18, cy - h * 0.18, "knowledge_base"),
        (cx - w * 0.15, cy + h * 0.18, "digital_worker"),
        (cx + w * 0.20, cy + h * 0.20, "data_center"),
    ]

    for px, py, planet_key in positions:
        planet = PLANET_DEFS[planet_key]
        orbit_r = planet["orbit_radius"] * min(w, h)
        radius = planet["radius_ratio"] * min(w, h)

        orbital_x = px + math.cos(anim_t * planet["orbit_speed"]) * orbit_r * 0.15
        orbital_y = py + math.sin(anim_t * planet["orbit_speed"] * 1.3) * orbit_r * 0.12

        # 轨道虚线环
        orbit_alpha = int(18 * alpha)
        p.setPen(QPen(QColor(*planet["ring_color"], orbit_alpha), 0.4))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(px, py), orbit_r, orbit_r * 0.7)
        # 轨道交叉标记
        p.setPen(QPen(QColor(*planet["ring_color"], int(8 * alpha)), 0.3))
        p.drawLine(QPointF(px - orbit_r, py), QPointF(px + orbit_r, py))
        p.drawLine(QPointF(px, py - orbit_r * 0.7), QPointF(px, py + orbit_r * 0.7))

        # 绘制星球类型
        planet_type = planet["type"]
        breath = 0.6 + 0.4 * abs(math.sin(anim_t * 1.2 + hash(planet_key) % 100 * 0.1))

        if planet_type == "gas_giant":
            _paint_gas_giant(p, orbital_x, orbital_y, radius, planet, anim_t, alpha, breath)
        elif planet_type == "crystal":
            _paint_crystal_planet(p, orbital_x, orbital_y, radius, planet, anim_t, alpha, breath)
        elif planet_type == "station":
            _paint_station(p, orbital_x, orbital_y, radius, planet, anim_t, alpha, breath)
        elif planet_type == "matrix":
            _paint_matrix_planet(p, orbital_x, orbital_y, radius, planet, anim_t, alpha, breath)

        # 标签
        font = QFont("Courier New", max(6, int(radius * 0.45)))
        font.setBold(True)
        p.setFont(font)
        label_alpha = int(90 * alpha * breath)
        p.setPen(QColor(*planet["ring_color"], label_alpha))
        p.drawText(QRectF(orbital_x - radius * 2, orbital_y + radius * 1.1,
                           radius * 4, radius * 1.2),
                   Qt.AlignCenter, planet["label"])


def _paint_gas_giant(p, x, y, r, planet, anim_t, alpha, breath):
    """蓝色气态巨星：带状条纹 + 光环"""
    r2, g2, b2 = planet["color"]
    # 主体渐变
    body_grad = QRadialGradient(x - r * 0.25, y - r * 0.2, r * 1.1)
    body_grad.setColorAt(0.0, QColor(min(r2 + 60, 255), min(g2 + 40, 255), min(b2 + 30, 255),
                                     int(160 * alpha * breath)))
    body_grad.setColorAt(0.5, QColor(r2, g2, b2, int(140 * alpha * breath)))
    body_grad.setColorAt(1.0, QColor(r2 // 3, g2 // 3, b2 // 3, int(120 * alpha * breath)))
    p.setBrush(body_grad)
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(x, y), r, r)

    # 气态条纹
    stripe_count = 5
    p.setPen(Qt.NoPen)
    for i in range(stripe_count):
        sy = y - r * 0.6 + i * r * 1.2 / stripe_count
        stripe_w = r * (1.2 - abs((i - stripe_count / 2) / stripe_count) * 1.4)
        stripe_a = int(50 * alpha * breath * (0.5 + 0.5 * abs(math.sin(anim_t + i))))
        p.setBrush(QColor(min(r2 + 80, 255), min(g2 + 60, 255), min(b2 + 50, 255), stripe_a))
        stripe_rect = QRectF(x - stripe_w, sy, stripe_w * 2, r * 0.12)
        path = QPainterPath()
        path.addRoundedRect(stripe_rect, 3, 3)
        p.drawPath(path)

    # 行星光环（倾斜椭圆）
    ring_a = int(60 * alpha * breath)
    p.setPen(QPen(QColor(*planet["ring_color"], ring_a), 1.0))
    p.setBrush(Qt.NoBrush)
    ring_rx = r * 1.6
    ring_ry = r * 0.3
    p.drawEllipse(QPointF(x, y), ring_rx, ring_ry)

    # 卫星
    for m in range(planet["moons"]):
        m_angle = anim_t * 2.0 + m * 2.1
        m_orbit = r * 2.2 + m * r * 0.6
        mx = x + math.cos(m_angle) * m_orbit
        my = y + math.sin(m_angle) * m_orbit * 0.4
        m_alpha = int(100 * alpha)
        p.setBrush(QColor(200, 210, 220, m_alpha))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(mx, my), 2, 2)


def _paint_crystal_planet(p, x, y, r, planet, anim_t, alpha, breath):
    """水晶矿星：几何晶面 + 棱角辉光"""
    r2, g2, b2 = planet["color"]
    # 中心亮核
    core_grad = QRadialGradient(x, y, r)
    core_grad.setColorAt(0.0, QColor(220, 255, 240, int(180 * alpha * breath)))
    core_grad.setColorAt(0.3, QColor(r2, g2, b2, int(150 * alpha * breath)))
    core_grad.setColorAt(0.7, QColor(r2 // 2, g2 // 2, b2 // 2, int(100 * alpha * breath)))
    core_grad.setColorAt(1.0, QColor(r2 // 4, g2 // 4, b2 // 4, int(40 * alpha * breath)))
    p.setBrush(core_grad)
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(x, y), r, r)

    # 晶面几何线条（六边形网格感）
    p.setPen(QPen(QColor(180, 255, 230, int(40 * alpha * breath)), 0.5))
    for i in range(3):
        angle = i * math.pi / 3 + anim_t * 0.3
        lx1 = x + math.cos(angle) * r * 0.5
        ly1 = y + math.sin(angle) * r * 0.5
        lx2 = x + math.cos(angle + math.pi) * r * 0.5
        ly2 = y + math.sin(angle + math.pi) * r * 0.5
        p.drawLine(QPointF(lx1, ly1), QPointF(lx2, ly2))

    # 晶面反光点
    sparkle_phase = anim_t * 3
    for i in range(2):
        sx = x + math.cos(sparkle_phase + i * 2.5) * r * 0.5
        sy = y + math.sin(sparkle_phase * 0.7 + i * 2.5) * r * 0.5
        sparkle = QRadialGradient(sx, sy, r * 0.18)
        sparkle.setColorAt(0.0, QColor(255, 255, 255, int(140 * alpha)))
        sparkle.setColorAt(1.0, QColor(180, 255, 240, 0))
        p.setBrush(sparkle)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(sx, sy), r * 0.18, r * 0.18)


def _paint_station(p, x, y, r, planet, anim_t, alpha, breath):
    """空间站：六边形框架 + 旋转组件"""
    r2, g2, b2 = planet["color"]
    # 中心 Hub
    hub_grad = QRadialGradient(x, y, r * 0.5)
    hub_grad.setColorAt(0.0, QColor(255, 220, 180, int(180 * alpha * breath)))
    hub_grad.setColorAt(0.6, QColor(r2, g2, b2, int(120 * alpha * breath)))
    hub_grad.setColorAt(1.0, QColor(r2 // 2, g2 // 2, b2 // 2, int(60 * alpha * breath)))
    p.setBrush(hub_grad)
    p.setPen(QPen(QColor(*planet["ring_color"], int(100 * alpha)), 0.8))
    p.drawEllipse(QPointF(x, y), r * 0.45, r * 0.45)

    # 六边形框架
    hex_angle = anim_t * 0.5
    path = QPainterPath()
    for i in range(6):
        angle = hex_angle + i * math.pi / 3
        hx = x + math.cos(angle) * r * 0.85
        hy = y + math.sin(angle) * r * 0.85
        if i == 0:
            path.moveTo(hx, hy)
        else:
            path.lineTo(hx, hy)
    path.closeSubpath()
    p.setPen(QPen(QColor(*planet["ring_color"], int(90 * alpha * breath)), 1.2))
    p.setBrush(Qt.NoBrush)
    p.drawPath(path)

    # 连接辐条
    for i in range(6):
        angle = hex_angle + i * math.pi / 3
        hx = x + math.cos(angle) * r * 0.85
        hy = y + math.sin(angle) * r * 0.85
        p.setPen(QPen(QColor(*planet["ring_color"], int(40 * alpha * breath)), 0.4))
        p.drawLine(QPointF(x, y), QPointF(hx, hy))

    # 对接卫星
    for m in range(planet["moons"]):
        m_angle = anim_t * 1.5 + m * math.pi
        m_orbit = r * 1.3
        mx = x + math.cos(m_angle) * m_orbit
        my = y + math.sin(m_angle) * m_orbit
        p.setBrush(QColor(255, 200, 140, int(120 * alpha)))
        p.setPen(QPen(QColor(*planet["ring_color"], int(80 * alpha)), 0.5))
        p.drawRect(QRectF(mx - 3, my - 3, 6, 6))


def _paint_matrix_planet(p, x, y, r, planet, anim_t, alpha, breath):
    """数据矩阵星：网格纹理 + 数据流脉冲"""
    r2, g2, b2 = planet["color"]
    # 主体
    body_grad = QRadialGradient(x - r * 0.2, y - r * 0.15, r)
    body_grad.setColorAt(0.0, QColor(min(r2 + 50, 255), min(g2 + 30, 255), min(b2 + 30, 255),
                                     int(150 * alpha * breath)))
    body_grad.setColorAt(1.0, QColor(r2 // 2, g2 // 2, b2 // 2, int(100 * alpha * breath)))
    p.setBrush(body_grad)
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(x, y), r, r)

    # 矩阵网格线
    grid_step = r * 0.25
    grid_alpha = int(35 * alpha * breath)
    p.setPen(QPen(QColor(*planet["ring_color"], grid_alpha), 0.4))
    for gy in range(int(y - r), int(y + r), int(grid_step)):
        p.drawLine(QPointF(x - r, gy), QPointF(x + r, gy))
    for gx in range(int(x - r), int(x + r), int(grid_step)):
        p.drawLine(QPointF(gx, y - r), QPointF(gx, y + r))

    # 数据流脉冲（沿网格线移动的亮点）
    pulse_phase = anim_t * 4.0
    for i in range(3):
        px = x - r + ((pulse_phase + i * 2.5) % (r * 2))
        pres = px > x - r and px < x + r
        if pres:
            py = y + math.sin(px * 0.3 + anim_t * 2) * r * 0.6
            pulse_grad = QRadialGradient(px, py, r * 0.15)
            pulse_grad.setColorAt(0.0, QColor(255, 200, 255, int(120 * alpha)))
            pulse_grad.setColorAt(1.0, QColor(180, 100, 255, 0))
            p.setBrush(pulse_grad)
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(px, py), r * 0.15, r * 0.15)


def paint_hud_overlay(p: QPainter, rect: QRectF, anim_t: float, title: str = "",
                       show_scanlines: bool = True, show_corners: bool = True,
                       alpha: float = 1.0):
    """在对话框上绘制 HUD 装饰元素。需先画好星空背景 + 模块星球再调用。"""

    # ── 扫描线 ──
    if show_scanlines:
        p.setPen(QPen(QColor(0, 200, 255, int(6 * alpha)), 1))
        for y in range(int(rect.top()) + 1, int(rect.bottom()), 3):
            p.drawLine(QPointF(rect.left() + 1, y), QPointF(rect.right() - 1, y))

    # ── 四角括号 ──
    if show_corners:
        cl, cg = 22, 8
        p.setPen(QPen(QColor(0, 210, 240, int(130 * alpha)), 2))

        def corner(lx, ly, hx, hy, vx, vy):
            p.drawLine(int(lx), int(ly), int(hx), int(hy))
            p.drawLine(int(lx), int(ly), int(vx), int(vy))

        corner(rect.left() + cg, rect.top() + cg,
               rect.left() + cg + cl, rect.top() + cg,
               rect.left() + cg, rect.top() + cg + cl)
        corner(rect.right() - cg, rect.top() + cg,
               rect.right() - cg - cl, rect.top() + cg,
               rect.right() - cg, rect.top() + cg + cl)
        corner(rect.left() + cg, rect.bottom() - cg,
               rect.left() + cg + cl, rect.bottom() - cg,
               rect.left() + cg, rect.bottom() - cg - cl)
        corner(rect.right() - cg, rect.bottom() - cg,
               rect.right() - cg - cl, rect.bottom() - cg,
               rect.right() - cg, rect.bottom() - cg - cl)

    # ── 标题 ──
    if title:
        title_y = rect.top() + 4
        p.setPen(QPen(QColor(0, 200, 240, int(90 * alpha)), 0.5))
        p.drawLine(int(rect.left() + 14), int(title_y + 20), int(rect.right() - 14), int(title_y + 20))
        font = QFont("Courier New", 10)
        font.setBold(True)
        p.setFont(font)
        p.setPen(QColor(0, 220, 255, int(170 * alpha)))
        p.drawText(QRectF(rect.left() + 16, title_y, rect.width() - 32, 22),
                   Qt.AlignLeft | Qt.AlignVCenter, f"◆ {title}")

    # ── 底部状态栏 ──
    status_y = rect.bottom() - 14
    p.setPen(QPen(QColor(0, 180, 220, int(40 * alpha)), 0.5))
    p.drawLine(int(rect.left() + 12), int(status_y), int(rect.right() - 12), int(status_y))
    font_s = QFont("Courier New", 7)
    p.setFont(font_s)
    p.setPen(QColor(0, 180, 220, int(50 * alpha)))
    p.drawText(QRectF(rect.left() + 14, status_y + 1, 100, 12),
               Qt.AlignLeft, "SYS:OK")
    pulse = 0.5 + 0.5 * abs(math.sin(anim_t * 2.3))
    p.setPen(QColor(0, int(180 * pulse), int(240 * pulse), int(70 * alpha)))
    p.drawText(QRectF(rect.right() - 80, status_y + 1, 66, 12),
               Qt.AlignRight, "◆ ONLINE")

    # ── 数据流飘字 ──
    rng = _rng(int(anim_t * 300) % 10000)
    p.setFont(QFont("Courier New", 6))
    for _ in range(8):
        dx = rect.left() + rng.uniform(20, rect.width() - 20)
        dy = rect.top() + rng.uniform(30, rect.height() * 0.85)
        flicker = 0.3 + 0.7 * abs(math.sin(anim_t * (2 + _ * 0.7) + _))
        alpha_d = int(35 * alpha * flicker)
        p.setPen(QColor(0, 180, 220, alpha_d))
        chars = ["0101", "1010", "FF", "A3", "7C", "◆", "█", "▓", "01", "10"]
        p.drawText(QPointF(dx, dy), rng.choice(chars))

    # ── 底部星舰迷你轮廓 ──
    _paint_mini_starship(p, rect, anim_t, alpha)


def _paint_mini_starship(p: QPainter, rect: QRectF, anim_t: float, alpha: float):
    """在大屏底部绘制微型星舰轮廓线"""
    bw = rect.width() * 0.6
    bh = rect.height() * 0.06
    bx = rect.center().x() - bw / 2
    by = rect.bottom() - bh - 6

    path = QPainterPath()
    na = 0.33
    path.moveTo(bx + bw * na, by)
    path.lineTo(bx + bw / 2, by - bh * 0.5)
    path.lineTo(bx + bw * (1 - na), by)
    path.lineTo(bx + bw * 0.95, by + bh)
    path.lineTo(bx + bw * 0.05, by + bh)
    path.closeSubpath()

    breath = 0.3 + 0.7 * abs(math.sin(anim_t * 1.5))
    p.setPen(QPen(QColor(0, 180, 240, int(30 * alpha * breath)), 0.8))
    p.setBrush(QColor(0, 120, 200, int(10 * alpha * breath)))
    p.drawPath(path)

    for sx in [bx + bw * 0.25, bx + bw * 0.75]:
        p.setBrush(QColor(0, 200, 255, int(60 * alpha * (0.5 + 0.5 * abs(math.sin(anim_t * 6))))))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(sx, by + bh), 3, 3)


# ═══════════ HUD 窗口基类 ═══════════

class HudDialog:
    """Mixin：赋予任意 QDialog HUD 主题 + 自动绘制装饰 + 星空背景 + 模块星球
    使用静态方法 + 显式 instance 参数，不依赖继承，避免 AttributeError。
    """

    @staticmethod
    def init_hud(instance, title: str = ""):
        instance._hud_title = title
        instance._hud_anim_t = 0.0

        def hud_tick():
            instance._hud_anim_t += 0.05
            instance.update()

        instance._hud_timer = QTimer(instance)
        instance._hud_timer.timeout.connect(hud_tick)
        instance._hud_timer.start(50)

    @staticmethod
    def paint_hud(instance, event):
        """画星空 → 模块星球 → HUD 装饰覆盖层"""
        full_rect = QRectF(instance.rect())
        rect = full_rect.adjusted(1, 1, -1, -1)

        # ── 第一层：星空背景 ──
        p_bg = QPainter(instance)
        p_bg.setRenderHint(QPainter.Antialiasing)
        paint_starfield(p_bg, full_rect, instance._hud_anim_t, alpha=0.85)
        p_bg.end()

        # ── 第二层：模块星球 ──
        p_planets = QPainter(instance)
        p_planets.setRenderHint(QPainter.Antialiasing)
        paint_module_planets(p_planets, full_rect, instance._hud_anim_t, alpha=1.0)
        p_planets.end()

        # ── 第三层：HUD 装饰 ──
        p_hud = QPainter(instance)
        p_hud.setRenderHint(QPainter.Antialiasing)
        paint_hud_overlay(p_hud, rect, instance._hud_anim_t, title=instance._hud_title)
        p_hud.end()

    @staticmethod
    def stop_hud(instance):
        if instance._hud_timer:
            instance._hud_timer.stop()


# ═══════════ 装饰器 ═══════════

def make_hud_dialog(dialog_cls):
    """装饰器：将 QDialog / QMainWindow 子类升级为 HUD 数字大屏（星空 + 星球 + 扫描线 + 星舰轮廓）"""
    orig_init = dialog_cls.__init__

    def new_init(self, *args, **kwargs):
        # 必须在 orig_init 之前预置 HUD 属性默认值：
        # orig_init → super().__init__ → setCentralWidget/resize 可能
        # 在事件循环中触发 paintEvent，new_paint 会访问 _hud_anim_t
        self._hud_anim_t = 0.0
        self._hud_title = ""
        self._hud_timer = None
        orig_init(self, *args, **kwargs)
        apply_hud_theme(self)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        HudDialog.init_hud(self, getattr(self, 'windowTitle', lambda: '')())

    dialog_cls.__init__ = new_init

    orig_paint = getattr(dialog_cls, 'paintEvent', None)

    def new_paint(self, event):
        if orig_paint:
            orig_paint(self, event)
        HudDialog.paint_hud(self, event)

    dialog_cls.paintEvent = new_paint

    orig_close = getattr(dialog_cls, 'closeEvent', None)

    def new_close(self, event):
        HudDialog.stop_hud(self)
        if orig_close:
            orig_close(self, event)
        event.accept()

    dialog_cls.closeEvent = new_close
    return dialog_cls
