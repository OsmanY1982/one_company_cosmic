"""
宇宙引擎 — 深空渲染核心
提供：星空背景、星云、粒子效果、辉光绘制
"""
import math
import random
import time
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QLinearGradient, QPainterPath, QFont
)

# ═══════════════════════════════════════════════════════
#  色彩体系
# ═══════════════════════════════════════════════════════
SPACE_VOID   = QColor(3, 5, 16)        # 深空底色
NEBULA_BLUE  = QColor(20, 30, 90, 30)  # 蓝紫星云
NEBULA_PURPLE = QColor(60, 10, 50, 25) # 紫色星云
NEBULA_TEAL  = QColor(10, 50, 60, 20)  # 青蓝星云
STAR_COLD    = QColor(180, 200, 255)    # 冷白星
STAR_WARM    = QColor(255, 220, 180)    # 暖黄星
STAR_BLUE    = QColor(150, 180, 255)    # 蓝星
HOLO_BORDER  = QColor(80, 140, 255, 60) # 全息边框
HOLO_FILL    = QColor(8, 15, 35, 200)   # 全息面板底色
ACCENT_CYAN  = QColor(0, 200, 255)
ACCENT_PURPLE = QColor(140, 80, 255)
ACCENT_GOLD  = QColor(255, 180, 50)


class CosmicBackground(QWidget):
    """深空背景 — 星云 + 星场 + 流星 + 缓慢漂移"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._stars = []
        self._nebulas = []
        self._shooting_stars = []
        self._t = 0
        self._generate()

        # 动画定时器
        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(50)

    def _generate(self):
        random.seed(42)
        # 星云
        nebula_specs = [
            (0.25, 0.30, 280, NEBULA_BLUE),
            (0.70, 0.25, 320, NEBULA_PURPLE),
            (0.50, 0.65, 250, NEBULA_TEAL),
            (0.15, 0.75, 220, NEBULA_BLUE),
            (0.80, 0.70, 200, NEBULA_PURPLE),
        ]
        self._nebulas = [(cx, cy, r, c) for cx, cy, r, c in nebula_specs]

        # 小星 ~400 颗
        self._stars = []
        for _ in range(400):
            self._stars.append({
                'x': random.random(),
                'y': random.random(),
                'r': random.uniform(0.3, 1.4),
                'a': random.randint(40, 180),
                'twinkle_speed': random.uniform(0.02, 0.08),
                'twinkle_phase': random.uniform(0, math.pi * 2),
            })

        # 亮星 ~25 颗（带辉光）
        self._bright_stars = []
        bright_colors = ["#aaccff", "#ffddaa", "#ccddff", "#ffffff", "#aaddff"]
        for _ in range(25):
            self._bright_stars.append({
                'x': random.random(),
                'y': random.random(),
                'r': random.uniform(1.5, 3.0),
                'color': QColor(random.choice(bright_colors)),
                'glow_r': random.uniform(6, 14),
            })

        # 流星初始
        self._shooting_stars = []

    def _tick(self):
        self._t += 0.05
        w, h = self.width(), self.height()

        # 随机生成流星
        if random.random() < 0.03 and len(self._shooting_stars) < 2:
            sx = random.uniform(0, w)
            sy = random.uniform(0, h * 0.4)
            angle = random.uniform(-0.6, -0.2)  # 斜向下
            speed = random.uniform(3, 7)
            life = random.uniform(0.6, 1.2)
            self._shooting_stars.append({
                'x': sx, 'y': sy,
                'angle': angle, 'speed': speed,
                'life': life, 'age': 0,
                'len': random.uniform(30, 80),
            })

        # 移动 + 剔除
        survivors = []
        for s in self._shooting_stars:
            s['age'] += 0.05
            s['x'] += math.cos(s['angle']) * s['speed']
            s['y'] += math.sin(s['angle']) * s['speed']
            if s['age'] < s['life'] and 0 <= s['x'] <= w and 0 <= s['y'] <= h:
                survivors.append(s)
        self._shooting_stars = survivors

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        if w == 0 or h == 0:
            painter.end()
            return

        # 深空底色
        painter.fillRect(0, 0, w, h, SPACE_VOID)

        # 星云
        painter.setPen(Qt.NoPen)
        for cx, cy, cr, color in self._nebulas:
            px, py = cx * w, cy * h
            g = QRadialGradient(QPointF(px, py), cr)
            g.setColorAt(0, color)
            g.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(g))
            painter.drawEllipse(QPointF(px, py), cr, cr)

        # 小星
        for s in self._stars:
            px, py = s['x'] * w, s['y'] * h
            flicker = 0.5 + 0.5 * math.sin(self._t * s['twinkle_speed'] + s['twinkle_phase'])
            a = int(s['a'] * (0.6 + 0.4 * flicker))
            color = QColor(200, 210, 255, a)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(px, py), s['r'], s['r'])

        # 亮星 + 辉光
        for s in self._bright_stars:
            px, py = s['x'] * w, s['y'] * h
            # 辉光
            glow = QRadialGradient(QPointF(px, py), s['glow_r'])
            c = s['color']
            glow.setColorAt(0, QColor(c.red(), c.green(), c.blue(), 50))
            glow.setColorAt(0.4, QColor(c.red(), c.green(), c.blue(), 15))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(QPointF(px, py), s['glow_r'], s['glow_r'])
            # 核心
            painter.setBrush(QBrush(c))
            painter.drawEllipse(QPointF(px, py), s['r'], s['r'])

        # 流星
        for s in self._shooting_stars:
            progress = s['age'] / s['life']
            alpha = int(255 * (1 - progress))
            ex = s['x'] - math.cos(s['angle']) * s['len']
            ey = s['y'] - math.sin(s['angle']) * s['len']
            # 尾迹渐变
            grad = QLinearGradient(QPointF(s['x'], s['y']), QPointF(ex, ey))
            grad.setColorAt(0, QColor(255, 255, 255, alpha))
            grad.setColorAt(1, QColor(255, 255, 255, 0))
            pen = QPen(QBrush(grad), 1.5)
            painter.setPen(pen)
            painter.drawLine(QPointF(int(s['x']), int(s['y'])),
                           QPointF(int(ex), int(ey)))
            # 头部亮点
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, alpha)))
            painter.drawEllipse(QPointF(s['x'], s['y']), 2, 2)

        painter.end()


def draw_ring(painter, cx, cy, radius, width, color, progress=1.0):
    """绘制辉光环 — 用于对接环、轨道环等"""
    painter.setPen(Qt.NoPen)
    segments = 120
    for i in range(segments):
        angle = (i / segments) * math.pi * 2
        if angle / (math.pi * 2) > progress:
            break
        a = i / segments * math.pi * 2
        next_a = (i + 1) / segments * math.pi * 2
        # 线段两端点
        x1 = cx + math.cos(a) * radius
        y1 = cy + math.sin(a) * radius
        x2 = cx + math.cos(next_a) * radius
        y2 = cy + math.sin(next_a) * radius
        # 用渐变模拟辉光
        g = QLinearGradient(QPointF(x1, y1), QPointF(x2, y2))
        g.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 200))
        g.setColorAt(0.5, QColor(color.red(), color.green(), color.blue(), 80))
        g.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 200))
        painter.setPen(QPen(QBrush(g), width))


def draw_glow_ellipse(painter, cx, cy, rx, ry, color, intensity=0.4):
    """绘制辉光椭圆 — 用于按钮、卡片发光"""
    for i in range(3, 0, -1):
        alpha = int(255 * intensity * (1 - i * 0.3))
        g = QRadialGradient(QPointF(cx, cy), max(rx, ry) * (1 + i * 0.5))
        g.setColorAt(0, QColor(color.red(), color.green(), color.blue(), alpha))
        g.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(g))
        painter.drawEllipse(QPointF(cx, cy), rx * (1 + i * 0.5), ry * (1 + i * 0.5))