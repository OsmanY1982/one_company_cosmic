# `modules/tools/orbital_sphere.py`

> 路径：`modules/tools/orbital_sphere.py` | 行数：282


---


```python
#!/usr/bin/env python3
"""
桌面悬浮球 — 透明画布全屏渲染几十个球，鼠标穿透不挡操作。
小控制条 ESC 退出、空格暂停、R 重置。
"""
import sys
import math
import random
from time import time

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QFont
)

SW, SH = None, None
MAX_SPHERES = 50
LIFETIME_MS = 20000
SPAWN_INTERVAL_MS = 300

COLORS = [
    (255, 100, 120), (100, 210, 255), (255, 210, 80),
    (140, 230, 100), (210, 130, 255), (255, 150, 200),
    (100, 255, 200), (255, 180, 100),
]


class Sphere:
    MODES = ['bezier', 'lissajous', 'brownian', 'vortex', 'bounce', 'sine_drift']

    def __init__(self):
        self.mode = random.choice(self.MODES)
        self.color = random.choice(COLORS)
        self.radius = random.randint(8, 24)
        self.x = random.uniform(self.radius, SW - self.radius)
        self.y = random.uniform(self.radius, SH - self.radius)
        self.birth = time() * 1000
        self.opacity = 1.0
        self._init_mode()

    def _init_mode(self):
        m = 80
        if self.mode == 'bezier':
            self._bp = [
                QPoint(int(self.x), int(self.y)),
                QPoint(random.randint(m, SW-m), random.randint(m, SH-m)),
                QPoint(random.randint(m, SW-m), random.randint(m, SH-m)),
                QPoint(random.randint(m, SW-m), random.randint(m, SH-m)),
            ]
            self._bt = 0.0
            self._bs = random.uniform(0.0004, 0.0015)
        elif self.mode == 'lissajous':
            self._cx, self._cy = self.x, self.y
            self._ax = random.uniform(80, 350)
            self._ay = random.uniform(80, 350)
            self._fx = random.uniform(0.3, 1.0)
            self._fy = random.uniform(0.3, 1.0)
            self._px = random.uniform(0, 6.28)
            self._py = random.uniform(0, 6.28)
            self._lt = random.uniform(0, 200)
        elif self.mode == 'brownian':
            self._angle = random.uniform(0, 6.28)
            self._speed = random.uniform(2, 8)
        elif self.mode == 'vortex':
            self._vcx = random.randint(300, SW-300)
            self._vcy = random.randint(300, SH-300)
            self._vr = random.uniform(40, 250)
            self._vs = random.uniform(0.005, 0.025)
            self._vg = random.uniform(-0.04, 0.06)
            self._vt = random.uniform(0, 200)
        elif self.mode == 'bounce':
            self._vx = random.uniform(-5, 5) or 3
            self._vy = random.uniform(-5, 5) or -3
        elif self.mode == 'sine_drift':
            self._sx, self._sy = self.x, self.y
            self._svx = random.uniform(-2, 2) or 1.5
            self._svy = random.uniform(-2, 2) or -1.5
            self._samp = random.uniform(15, 60)
            self._sfreq = random.uniform(0.02, 0.08)
            self._sphase = random.uniform(0, 6.28)

    def update(self, now_ms):
        elapsed = now_ms - self.birth
        if elapsed > LIFETIME_MS:
            return False
        if elapsed > LIFETIME_MS * 0.8:
            self.opacity = max(0, 1 - (elapsed - LIFETIME_MS*0.8) / (LIFETIME_MS*0.2))
        else:
            self.opacity = 1.0

        t = now_ms / 1000.0

        if self.mode == 'bezier':
            self._bt += self._bs
            if self._bt > 1.0:
                self._init_mode()
            else:
                mt = 1 - self._bt
                mt2, mt3 = mt*mt, mt*mt*mt
                t2, t3 = self._bt*self._bt, self._bt*self._bt*self._bt
                self.x = mt3*self._bp[0].x() + 3*mt2*self._bt*self._bp[1].x() + 3*mt*t2*self._bp[2].x() + t3*self._bp[3].x()
                self.y = mt3*self._bp[0].y() + 3*mt2*self._bt*self._bp[1].y() + 3*mt*t2*self._bp[2].y() + t3*self._bp[3].y()

        elif self.mode == 'lissajous':
            self._lt += 0.016
            self.x = self._cx + self._ax * math.sin(self._fx * self._lt + self._px)
            self.y = self._cy + self._ay * math.cos(self._fy * self._lt + self._py)

        elif self.mode == 'brownian':
            self._angle += (random.random() - 0.5) * 0.4
            self.x += math.cos(self._angle) * self._speed
            self.y += math.sin(self._angle) * self._speed

        elif self.mode == 'vortex':
            self._vt += 0.016
            r = self._vr + self._vt * self._vg
            self.x = self._vcx + r * math.cos(self._vt * self._vs)
            self.y = self._vcy + r * math.sin(self._vt * self._vs)

        elif self.mode == 'bounce':
            self.x += self._vx
            self.y += self._vy
            if self.x - self.radius < 0:    self.x = self.radius; self._vx *= -1
            if self.x + self.radius > SW:   self.x = SW - self.radius; self._vx *= -1
            if self.y - self.radius < 0:    self.y = self.radius; self._vy *= -1
            if self.y + self.radius > SH:   self.y = SH - self.radius; self._vy *= -1

        elif self.mode == 'sine_drift':
            self._sx += self._svx
            self._sy += self._svy
            self.x = self._sx + self._samp * math.sin(self._sy * self._sfreq + self._sphase)
            self.y = self._sy + self._samp * math.cos(self._sx * self._sfreq + self._sphase)
            if self._sx < 0: self._sx = 0; self._svx *= -1
            if self._sx > SW: self._sx = SW; self._svx *= -1
            if self._sy < 0: self._sy = 0; self._svy *= -1
            if self._sy > SH: self._sy = SH; self._svy *= -1

        return True


class Overlay(QWidget):
    """全屏透明画布，绘制所有球，鼠标穿透"""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
            Qt.Tool | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setGeometry(0, 0, SW, SH)
        self.spheres = []

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        for s in self.spheres:
            if s.opacity <= 0.01:
                continue
            r, g, b = s.color
            a_body = int(220 * s.opacity)
            a_glow = int(35 * s.opacity)

            # 外辉光
            glow = QRadialGradient(s.x, s.y, s.radius * 3)
            glow.setColorAt(0, QColor(r, g, b, a_glow))
            glow.setColorAt(0.6, QColor(r, g, b, 0))
            glow.setColorAt(1, QColor(r, g, b, 0))
            p.setBrush(glow)
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPoint(int(s.x), int(s.y)), int(s.radius * 3), int(s.radius * 3))

            # 主体
            body = QRadialGradient(s.x - s.radius*0.2, s.y - s.radius*0.2, s.radius*0.1,
                                   s.x, s.y, s.radius)
            body.setColorAt(0, QColor(255, 255, 255, a_body))
            body.setColorAt(0.3, QColor(r, g, b, a_body))
            body.setColorAt(0.7, QColor(int(r*0.5), int(g*0.5), int(b*0.5), a_body))
            body.setColorAt(1, QColor(int(r*0.2), int(g*0.2), int(b*0.2), int(a_body*0.3)))
            p.setBrush(body)
            p.drawEllipse(QPoint(int(s.x), int(s.y)), s.radius, s.radius)

            # 高光
            hl = QRadialGradient(s.x - s.radius*0.35, s.y - s.radius*0.35, s.radius*0.05,
                                 s.x, s.y, s.radius*0.6)
            hl.setColorAt(0, QColor(255, 255, 255, int(140 * s.opacity)))
            hl.setColorAt(1, QColor(255, 255, 255, 0))
            p.setBrush(hl)
            p.drawEllipse(QPoint(int(s.x), int(s.y)), int(s.radius*0.6), int(s.radius*0.6))


class ControlBar(QWidget):
    """小控制条，接收键盘"""
    def __init__(self, app_ref):
        super().__init__()
        self.app_ref = app_ref
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFixedSize(160, 22)
        self.setStyleSheet("background: #1a1a30; border-radius: 4px;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        for text, color in [("ESC 退出", "#666"), ("空格 暂停", "#888"), ("R 重置", "#888")]:
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {color}; font-size: 10px; font-family: 'PingFang SC';")
            layout.addWidget(lbl)

        self.move(SW // 2 - 80, 8)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.app_ref.quit()
        elif e.key() == Qt.Key_Space:
            self.app_ref.toggle_pause()
        elif e.key() == Qt.Key_R:
            self.app_ref.reset()


class App:
    def __init__(self):
        self.paused = False
        self.last_spawn = 0
        self.overlay = Overlay()
        self.control = ControlBar(self)

        self.overlay.show()
        self.control.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.setInterval(16)
        self.timer.start()

    def _tick(self):
        if self.paused:
            return
        now = time() * 1000

        # 生成新球
        if now - self.last_spawn > SPAWN_INTERVAL_MS and len(self.overlay.spheres) < MAX_SPHERES:
            s = Sphere()
            s.birth = now
            self.overlay.spheres.append(s)
            self.last_spawn = now

        # 更新 + 移除过期
        alive = []
        for s in self.overlay.spheres:
            if s.update(now):
                alive.append(s)
        self.overlay.spheres = alive

        self.overlay.update()

    def toggle_pause(self):
        self.paused = not self.paused

    def reset(self):
        self.overlay.spheres.clear()
        self.last_spawn = 0

    def quit(self):
        self.timer.stop()
        QApplication.quit()


def main():
    global SW, SH
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    screen = app.primaryScreen().geometry()
    SW, SH = screen.width(), screen.height()
    App()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

```
