# `modules/intelligence/bridge_window.py`

> 路径：`modules/intelligence/bridge_window.py` | 行数：198


---


```python
# -*- coding: utf-8 -*-
"""
星舰舰桥窗口 — 全尺寸可缩放/全屏的舰桥内景
玻璃外太空 + 5 颗可点击模块星球 + 驾驶台
"""
import math
import traceback
from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont, QMouseEvent
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel


try:
    from modules.intelligence.starship_painter import paint_starship_bridge, get_bridge_planet_zones
except ImportError:
    from starship_painter import paint_starship_bridge, get_bridge_planet_zones


class CockpitWindow(QWidget):
    """星舰舰桥：可缩放窗口，全屏支持"""

    def __init__(self, role: str = "admin", opcclaw_engine=None, parent=None):
        super().__init__(parent)
        self._role = role
        self._engine = opcclaw_engine
        self._anim_t = 0.0
        self._hovered_planet = None  # 当前悬停的星球 module_id

        # ── 窗口设置 ──
        self.setWindowTitle("一人公司·舰桥")
        self.setMinimumSize(800, 520)
        screen = self.screen()
        if screen:
            geo = screen.availableGeometry()
            w = int(geo.width() * 0.72)
            h = int(geo.height() * 0.72)
        else:
            w, h = 1200, 800
        self.resize(w, h)

        # 支持全屏
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowCloseButtonHint |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint
        )
        self.setMouseTracking(True)

        # ── 全屏切换快捷键 ──
        self._fullscreen = False

        # ── 动画定时器 ──
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(33)  # ~30 FPS
        self._anim_timer.timeout.connect(self._tick)
        self._anim_timer.start()

        # ── 样式 ──
        self.setStyleSheet("background: #050a18;")

    # ═══════════ 动画 ═══════════

    def _tick(self):
        self._anim_t += 0.033
        self.update()

    # ═══════════ 全屏切换 ═══════════

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11 or (event.key() == Qt.Key_F and event.modifiers() & Qt.ControlModifier):
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_Escape and self._fullscreen:
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)

    def toggle_fullscreen(self):
        self._fullscreen = not self._fullscreen
        if self._fullscreen:
            self.showFullScreen()
        else:
            self.showNormal()

    # ═══════════ 绘制 ═══════════

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        rect = QRectF(self.rect())
        center = rect.center()
        size = min(self.width(), self.height()) * 0.38

        paint_starship_bridge(
            p, rect, center,
            size=size, anim_t=self._anim_t,
            hovered=False, active=True, alpha=1.0,
            drift_x=0.0, drift_y=0.0,
            role=self._role,
        )

        # ── 底部操作提示 ──
        p.setPen(QColor(0, 180, 220, 100))
        font = QFont("PingFang SC", 10)
        p.setFont(font)
        hints = [
            "F11 切换全屏",
            "双击最大化",
            "点击星球进入模块",
        ]
        x = 16
        for h in hints:
            tw = p.fontMetrics().horizontalAdvance(h)
            p.drawText(x, self.height() - 12, h)
            x += tw + 24

        p.end()

    # ═══════════ 鼠标交互 ═══════════

    def mouseMoveEvent(self, event: QMouseEvent):
        """悬停检测 — 星球高亮"""
        zones = get_bridge_planet_zones(QRectF(self.rect()), role=self._role)
        hit = None
        for (mid, _label), zone in zones.items():
            if zone.contains(event.pos()):
                hit = mid
                break
        if hit != self._hovered_planet:
            self._hovered_planet = hit
            if hit:
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """双击最大化/还原"""
        if self._fullscreen:
            self.toggle_fullscreen()
        elif self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """点击星球 → 打开对应模块"""
        total_delta = (event.globalPos() - getattr(self, '_mpress_global', event.globalPos())).manhattanLength()
        if total_delta > 8:  # 拖拽，不是点击
            super().mouseReleaseEvent(event)
            return

        zones = get_bridge_planet_zones(QRectF(self.rect()), role=self._role)
        for (mid, _label), zone in zones.items():
            if zone.contains(event.pos()):
                self._open_module(mid)
                return
        super().mouseReleaseEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        self._mpress_global = event.globalPos()
        super().mousePressEvent(event)

    # ═══════════ 模块打开 ═══════════

    def _open_module(self, module_id: str):
        """打开对应模块窗口"""
        try:
            if module_id == "business":
                from modules.business.business_window import BusinessWindow
                win = BusinessWindow()
            elif module_id == "personnel":
                from modules.personnel.personnel_window import PersonnelWindow
                win = PersonnelWindow()
            elif module_id == "intelligence":
                from modules.intelligence.intelligence_window import IntelligenceWindow
                win = IntelligenceWindow(role=self._role, opcclaw_engine=self._engine)
            elif module_id == "data":
                from modules.data_center.data_window import DataWindow
                win = DataWindow()
            elif module_id == "system":
                from modules.system.system_window import SystemWindow
                win = SystemWindow()
            else:
                return
            win.show()
        except Exception as e:
            print(f"[CockpitWindow] Failed to open module {module_id}: {e}")
            traceback.print_exc()

    # ═══════════ 关闭 ═══════════

    def closeEvent(self, event):
        self._anim_timer.stop()
        super().closeEvent(event)

```
