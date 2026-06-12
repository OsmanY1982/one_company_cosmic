"""
数据中心 → 星云观测站 · NEBULA OBSERVATORY
小星球导航模式：2颗小星球环绕星云核心光球
"""
import traceback
import os, sqlite3, csv, math
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QDialog
)
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QLinearGradient, QFont, QMouseEvent
)
from core.cosmic import CosmicBackground
from core.planet_painter import PLANET_STYLES, paint_planet

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

# ═══════ 小星球定义（真实纹理） ═══════
NEBULA_PLANETS = [
    {"id": "report", "name": "数据报表", "style": "neptune", "orbit": 160, "radius": 48},
    {"id": "bi",     "name": "数据大屏", "style": "uranus",  "orbit": 240, "radius": 42},
]

CORE_COLOR = QColor(0, 204, 160)  # 青绿色 #00cca0


class DataWindow(QMainWindow):
    """星云观测站 · NEBULA OBSERVATORY — 小星球导航"""

    def __init__(self, parent=None, role="admin"):
        super().__init__(parent)
        self._role = role
        self.setWindowTitle("一人公司 — 星云观测站 · NEBULA OBSERVATORY")
        self.setMinimumSize(900, 620)
        self._t = 0
        self._hovered_planet = None
        self._open_windows = {}

        # 星空背景
        self._cosmic = CosmicBackground()
        self.setCentralWidget(self._cosmic)

        # HUD 层 — 必须是窗口直接子控件，不是 _cosmic 子控件
        # 否则 _cosmic 的 WA_TransparentForMouseEvents 会在 macOS 26.x 拦截所有鼠标事件
        self._hud = QWidget(self)
        self._hud.setAttribute(Qt.WA_TranslucentBackground)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        self._hud.setMouseTracking(True)
        self._hud.mouseMoveEvent = self._on_mouse_move
        self._hud.mousePressEvent = self._on_click

        self._build_ui()

        # 确保 HUD 在星空背景之上
        self._hud.raise_()

        # 动画
        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(16)  # ~60fps (原 50ms)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._hud.setGeometry(0, 0, self.width(), self.height())

    def _build_ui(self):
        self._hud.paintEvent = self._paint_hud

        # ── 顶部 Header ──
        header = QWidget(self._hud)
        header.setStyleSheet("background: transparent;")
        header.setGeometry(0, 10, self.width(), 80)
        hl = QVBoxLayout(header)
        hl.setSpacing(4)
        hl.setContentsMargins(24, 0, 24, 0)

        title = QLabel("星云观测站")
        title.setStyleSheet("color: #aaeecc; font-size: 22px; font-weight: 800; letter-spacing: 6px; background: transparent;")
        hl.addWidget(title, alignment=Qt.AlignCenter)

        subtitle = QLabel("NEBULA OBSERVATORY · 点击星球进入模块")
        subtitle.setStyleSheet("color: #558877; font-size: 10px; letter-spacing: 2px; background: transparent;")
        hl.addWidget(subtitle, alignment=Qt.AlignCenter)

        # 辉光线
        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(0,180,150,50),
                stop:0.5 rgba(0,220,180,120),
                stop:0.7 rgba(0,180,150,50), stop:1 transparent);
            border: none;
        """)
        hl.addWidget(line)

        # 底部提示
        hint = QLabel("点击轨道星球进入对应模块")
        hint.setStyleSheet("color: #335544; font-size: 10px; background: transparent;")
        hint.setAlignment(Qt.AlignCenter)
        hint.setGeometry(0, self.height() - 30, self.width(), 24)

    def _get_orbit_center(self) -> QPointF:
        w = self._hud.width()
        h = self._hud.height()
        return QPointF(w * 0.5, h * 0.55)

    def _get_planet_pos(self, planet: dict) -> QPointF:
        cx = self._get_orbit_center()
        idx = NEBULA_PLANETS.index(planet)
        phase = idx * math.pi * 0.75  # 初始相位差
        angle = phase + self._t * (0.12 + idx * 0.06)
        px = cx.x() + math.cos(angle) * planet["orbit"]
        py = cx.y() + math.sin(angle) * planet["orbit"] * 0.55
        return QPointF(px, py)

    def _planet_at_pos(self, pos: QPointF):
        for p in NEBULA_PLANETS:
            pp = self._get_planet_pos(p)
            dist = math.hypot(pos.x() - pp.x(), pos.y() - pp.y())
            if dist <= p["radius"] + 14:
                return p
        return None

    def _on_mouse_move(self, event: QMouseEvent):
        old = self._hovered_planet
        self._hovered_planet = self._planet_at_pos(event.pos())
        if old != self._hovered_planet:
            self._hud.update()
            if self._hovered_planet:
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

    def _on_click(self, event: QMouseEvent):
        planet = self._planet_at_pos(event.pos())
        if planet:
            self._open_planet(planet["id"])

    def _open_planet(self, pid: str):
        if pid in self._open_windows:
            try:
                self._open_windows[pid].close()
            except Exception:
                traceback.print_exc()

        if pid == "report":
            from modules.data_center.report_window import ReportWindow
            win = ReportWindow(self)
        elif pid == "bi":
            from modules.data_center.bi_window import BIWindow
            win = BIWindow(self)
        else:
            return

        self._open_windows[pid] = win
        win.show()

    def _tick(self):
        self._t += 0.04
        self._hud.update()

    def _paint_hud(self, event):
        QWidget.paintEvent(self._hud, event)
        painter = QPainter(self._hud)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self._hud.width(), self._hud.height()
        cx = self._get_orbit_center()

        # ── 轨道环 ──
        orbit_colors = {"neptune": QColor(0, 200, 160), "uranus": QColor(60, 200, 200)}
        for p in NEBULA_PLANETS:
            r = p["orbit"]
            alpha = 20 if p == self._hovered_planet else 10
            c = orbit_colors.get(p["style"], QColor(0, 200, 160))
            painter.setPen(QPen(QColor(c.red(), c.green(), c.blue(), alpha), 0.8))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(cx, r, r * 0.55)

        # ── 扫描弧线 ──
        scan_r = 270
        scan_a = self._t * 0.4 % (math.pi * 2)
        s_end = QPointF(cx.x() + math.cos(scan_a) * scan_r,
                        cx.y() + math.sin(scan_a) * scan_r * 0.55)
        s_start = QPointF(cx.x() + math.cos(scan_a + 0.5) * scan_r,
                          cx.y() + math.sin(scan_a + 0.5) * scan_r * 0.55)
        sg = QLinearGradient(s_start, s_end)
        sg.setColorAt(0, QColor(0, 0, 0, 0))
        sg.setColorAt(0.45, QColor(0, 200, 160, 10))
        sg.setColorAt(0.5, QColor(0, 220, 180, 35))
        sg.setColorAt(0.55, QColor(0, 200, 160, 10))
        sg.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(QPen(QBrush(sg), 1.5))
        painter.drawLine(s_start, s_end)

        # ── 中心星云核心光球（升级为真实纹理）──
        core_r = 52
        paint_planet(painter, cx, core_r, PLANET_STYLES["earth"],
                     label="NEBULA CORE", font_size=9, anim_t=self._t)

        # ── 小星球（真实纹理）──
        for p in NEBULA_PLANETS:
            pp = self._get_planet_pos(p)
            style = PLANET_STYLES.get(p["style"], PLANET_STYLES["neptune"])
            is_hovered = p == self._hovered_planet
            paint_planet(painter, pp, p["radius"], style,
                         hovered=is_hovered, label=p["name"],
                         font_size=9, anim_t=self._t)

        # ── 顶部标签 ──
        painter.setPen(QPen(QColor(30, 80, 70, 80)))
        painter.setFont(QFont("Menlo", 9))
        painter.drawText(QRectF(0, 50, w, 18), Qt.AlignCenter, "ORBIT NAVIGATION")

        painter.end()