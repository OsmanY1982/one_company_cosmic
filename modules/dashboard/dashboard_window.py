"""
舰桥主控面板 — AI Agent 指挥中心
轨道星球导航
"""
import traceback
import math
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel
)
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QLinearGradient, QPainterPath, QFont, QMouseEvent
)

from core.cosmic import CosmicBackground, ACCENT_CYAN, ACCENT_GOLD, ACCENT_PURPLE
from core.planet_painter import PLANET_STYLES, paint_planet, paint_orbit, paint_energy_line


# ═══════════ 模块星球定义（真实纹理） ═══════════
ALL_PLANETS = [
    {"id": "business",     "name": "业务管理", "style": "venus",   "radius": 65, "orbit": 160},
    {"id": "personnel",    "name": "人员管理", "style": "mars",    "radius": 54, "orbit": 205},
    {"id": "intelligence", "name": "智能中心", "style": "jupiter", "radius": 71, "orbit": 142},
    {"id": "data",         "name": "数据中心", "style": "neptune", "radius": 58, "orbit": 248},
    {"id": "system",       "name": "系统设置", "style": "moon",    "radius": 48, "orbit": 288},
]

# 会员可见模块（业务管理 + 智能中心）
MEMBER_PLANET_IDS = {"business", "intelligence"}

# ── 会员等级徽章配色 ──
MEMBERSHIP_BADGE_COLORS = {
    "trial":     QColor(0, 200, 255),     # 青色
    "vip":       QColor(255, 180, 50),    # 金色
    "permanent": QColor(140, 80, 255),    # 紫色
}

MEMBERSHIP_LABELS = {
    "trial": "体验会员", "vip": "VIP会员", "permanent": "永久会员",
}


class DashboardWindow(QMainWindow):
    """舰桥 — AI Agent 驾驶舱"""

    def __init__(self, config=None, role: str = "admin",
                 membership_info: dict = None,
                 opcclaw_engine=None):
        super().__init__()
        self._role = role
        self._membership_info = membership_info or {}

        # 根据角色确定可见星球
        if role == "member":
            self._planets = [p for p in ALL_PLANETS if p["id"] in MEMBER_PLANET_IDS]
            mode_title = "舰桥 · 船员模式"
            if membership_info:
                ms = membership_info
                level = ms.get("membership", "trial")
                expire = ms.get("expire_at", "")
                mode_title += f" | 会员等级: {MEMBERSHIP_LABELS.get(level, level)} | 到期: {expire[:10]}"
            self.setWindowTitle(f"一人公司 — {mode_title}")
        else:
            self._planets = list(ALL_PLANETS)
            self.setWindowTitle("一人公司 — 舰桥 · 指挥官模式")

        self.setMinimumSize(1200, 760)

        # opcclaw 引擎（优先级最高）
        self._opcclaw = opcclaw_engine

        # 星空背景
        self._cosmic = CosmicBackground()
        self.setCentralWidget(self._cosmic)

        # HUD 层 — 必须是窗口直接子控件，不是 _cosmic 子控件
        # 否则 _cosmic 的 WA_TransparentForMouseEvents 会在 macOS 26.x 拦截所有鼠标事件
        self._hud = QWidget(self)
        self._hud.setAttribute(Qt.WA_TranslucentBackground)
        self._hud.setGeometry(0, 0, 1200, 760)

        # 动画状态
        self._t = 0
        self._hovered_planet = None
        self._modules_open = {}
        self._orbits = []  # dynamic orbit radii

        self._build_ui()

        # 确保 HUD 在星空背景之上
        self._hud.raise_()

        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(16)  # ~60fps (原 45ms)

        # 让 HUD 接收鼠标事件以检测星球 hover/click
        self._hud.setMouseTracking(True)
        self._hud.mouseMoveEvent = self._on_hud_mouse_move
        self._hud.mousePressEvent = self._on_hud_click

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        self._compute_orbits()

    # ════════════════ 布局 ════════════════

    def _build_ui(self):
        self._hud.paintEvent = self._paint_hud

        # 顶部标题（浮在 HUD 上）
        if self._role == "member":
            ms = self._membership_info
            level_label = MEMBERSHIP_LABELS.get(ms.get("membership", "trial"), "体验会员")
            expire_str = (ms.get("expire_at", ""))[:10] if ms.get("expire_at") else "N/A"
            title_text = f"舰桥 · 船员模式 | {level_label} | 到期: {expire_str}"
        else:
            title_text = "舰桥 · 指挥官模式"

        self._title_label = QLabel(title_text, self._hud)
        self._title_label.setStyleSheet(
            "color: #8899bb; font-size: 13px; font-weight: 700; "
            "letter-spacing: 4px; background: transparent;"
        )
        self._title_label.move(24, 18)
        self._title_label.adjustSize()

        # 引擎指示
        self._fuel_indicator = QLabel("", self._hud)
        self._fuel_indicator.setStyleSheet(
            "color: #00cc88; font-size: 9px; background: transparent;"
        )
        if self._opcclaw:
            self._fuel_indicator.setText("引擎: opcclaw")
        self._fuel_indicator.adjustSize()

        # 船员升级按钮
        if self._role == "member":
            self._upgrade_btn = QPushButton("升级会员", self._hud)
            self._upgrade_btn.setCursor(Qt.PointingHandCursor)
            self._upgrade_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255,180,45,35);
                    color: #ffdd88;
                    border: 1px solid rgba(255,200,60,55);
                    border-radius: 14px;
                    padding: 4px 14px;
                    font-size: 11px; font-weight: 600;
                }
                QPushButton:hover { background: rgba(255,190,50,60); }
            """)
            self._upgrade_btn.clicked.connect(self._open_upgrade)
            self._upgrade_btn.adjustSize()
        else:
            self._upgrade_btn = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        # 重新摆放顶部控件
        self._title_label.move(24, 18)
        self._title_label.adjustSize()
        if self._upgrade_btn:
            tw = self._title_label.width()
            self._upgrade_btn.move(32 + tw, 14)
            self._upgrade_btn.adjustSize()
            self._fuel_indicator.move(48 + tw + self._upgrade_btn.width(), 20)
        else:
            self._fuel_indicator.move(32 + self._title_label.width(), 20)
        self._fuel_indicator.adjustSize()

    # ════════════════ 模块导航 ════════════════

    def _open_module(self, module_id: str):
        """打开子模块窗口"""
        planet = next((p for p in self._planets if p["id"] == module_id), None)
        if not planet:
            return

        # 船员模式权限检查
        if self._role == "member":
            if module_id in ("personnel", "system"):
                return

        if module_id in self._modules_open:
            try:
                self._modules_open[module_id].close()
            except Exception:
                traceback.print_exc()

        if module_id == "business":
            from modules.business.business_window import BusinessWindow
            win = BusinessWindow(self)
        elif module_id == "personnel":
            from modules.personnel.personnel_window import PersonnelWindow
            win = PersonnelWindow(self)
        elif module_id == "intelligence":
            from modules.intelligence.intelligence_window import IntelligenceWindow
            win = IntelligenceWindow(self, role=self._role, opcclaw_engine=self._opcclaw)
        elif module_id == "data":
            from modules.data_center.data_window import DataWindow
            win = DataWindow(self)
        elif module_id == "system":
            from modules.system.system_window import SystemWindow
            win = SystemWindow(self)
        else:
            win = _ModuleWindow(planet, self)

        self._modules_open[module_id] = win
        win.show()

    def _open_upgrade(self):
        """船员点击升级会员按钮"""
        from modules.auth.upgrade_window import UpgradeWindow
        ms = self._membership_info
        dlg = UpgradeWindow(
            username=self._membership_info.get("username", ""),
            role=self._role,
            membership=ms.get("membership", "trial"),
            expire_at=ms.get("expire_at"),
            parent=self,
        )
        dlg.exec_()

    def _get_orbit_center(self) -> QPointF:
        """轨道中心 — 窗口正中央"""
        w = self._hud.width()
        h = self._hud.height()
        return QPointF(w * 0.5, h * 0.52)

    def _compute_orbits(self):
        w = self._hud.width()
        h = self._hud.height()
        if w <= 0 or h <= 0 or not self._planets:
            return
        n = len(self._planets)
        available_r = min(w, h) / 2 * 0.9
        max_radius = max(p["radius"] for p in self._planets)
        max_orbit = available_r - max_radius / 2
        if n > 3:
            base_r = max_orbit / (1 + (n - 1) * 0.4)
            self._orbits = [base_r * (1 + i * 0.4) for i in range(n)]
        else:
            self._orbits = [max_orbit * (i + 1) / n for i in range(n)]

    def _get_planet_pos(self, planet: dict) -> QPointF:
        """计算星球当前位置（基于时间和轨道参数）"""
        cx = self._get_orbit_center()
        idx = self._planets.index(planet)
        orbit = self._orbits[idx] if idx < len(self._orbits) else planet.get("orbit", 160)
        phase = idx * math.pi * 2 / len(self._planets)
        angle = phase + self._t * (0.15 + idx * 0.04)  # 不同速度
        px = cx.x() + math.cos(angle) * orbit
        py = cx.y() + math.sin(angle) * orbit * 0.55  # 椭圆效果
        return QPointF(px, py)

    def _planet_at_pos(self, pos: QPointF) -> dict:
        """返回 pos 处的星球，无则 None"""
        for p in self._planets:
            pp = self._get_planet_pos(p)
            dist = math.hypot(pos.x() - pp.x(), pos.y() - pp.y())
            if dist <= p["radius"] + 12:  # 容忍点击区域
                return p
        return None

    def _on_hud_mouse_move(self, event: QMouseEvent):
        old = self._hovered_planet
        self._hovered_planet = self._planet_at_pos(event.pos())
        if old != self._hovered_planet:
            self._hud.update()

    def _on_hud_click(self, event: QMouseEvent):
        planet = self._planet_at_pos(event.pos())
        if planet:
            self._open_module(planet["id"])

    # ════════════════ 动画 + 绘制 ════════════════

    def _tick(self):
        self._t += 0.04
        self._hud.update()

    def _paint_hud(self, event):
        QWidget.paintEvent(self._hud, event)
        painter = QPainter(self._hud)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self._hud.width(), self._hud.height()

        # ── 轨道环 ──
        cx = self._get_orbit_center()

        # 扫描线
        scan_r = 310
        scan_a = self._t * 0.5 % (math.pi * 2)
        sx = cx.x() + math.cos(scan_a) * scan_r
        sy = cx.y() + math.sin(scan_a) * scan_r * 0.55
        ex = cx.x() + math.cos(scan_a + math.pi) * scan_r
        ey = cx.y() + math.sin(scan_a + math.pi) * scan_r * 0.55
        sg = QLinearGradient(QPointF(ex, ey), QPointF(sx, sy))
        sg.setColorAt(0, QColor(0, 0, 0, 0))
        sg.setColorAt(0.45, QColor(0, 180, 255, 8))
        sg.setColorAt(0.5, QColor(0, 180, 255, 20))
        sg.setColorAt(0.55, QColor(0, 180, 255, 8))
        sg.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(QPen(QBrush(sg), 1.5))
        painter.drawLine(QPointF(ex, ey), QPointF(sx, sy))

        # 轨道线
        for i, p in enumerate(self._planets):
            orbit = self._orbits[i] if i < len(self._orbits) else p.get("orbit", 160)
            paint_orbit(painter, cx, orbit, anim_t=self._t)

        # ── 中央 AI 核心 · 地球 ──
        core_pulse = 0.5 + 0.5 * math.sin(self._t * 1.5)
        core_r = 48 + core_pulse * 10
        paint_planet(painter, cx, core_r, PLANET_STYLES["earth"],
                     label="AI CORE", font_size=8, anim_t=self._t)

        # ── 星球 ──
        for p in self._planets:
            pp = self._get_planet_pos(p)
            style = PLANET_STYLES.get(p["style"], PLANET_STYLES["neptune"])
            is_hovered = p == self._hovered_planet
            paint_planet(painter, pp, p["radius"], style,
                         hovered=is_hovered, label=p["name"], font_size=10,
                         anim_t=self._t)

        # ── 会员等级徽章（船员模式） ──
        if self._role == "member" and self._membership_info:
            ms = self._membership_info
            level = ms.get("membership", "trial")
            badge_color = MEMBERSHIP_BADGE_COLORS.get(level, MEMBERSHIP_BADGE_COLORS["trial"])
            level_label = MEMBERSHIP_LABELS.get(level, "体验会员")

            expire_str = ms.get("expire_at", "")
            countdown_text = ""
            if expire_str:
                try:
                    from datetime import datetime
                    expire_dt = datetime.strptime(expire_str, "%Y-%m-%d %H:%M:%S")
                    now = datetime.now()
                    remain = (expire_dt - now).days
                    if remain > 0:
                        countdown_text = f"剩余 {remain} 天"
                    elif remain == 0:
                        countdown_text = "今日到期"
                    else:
                        countdown_text = "已过期"
                except Exception:
                    traceback.print_exc()

            badge_x = w - 200
            badge_y = 14
            badge_w = 180
            badge_h = 32

            path = QPainterPath()
            path.addRoundedRect(QRectF(badge_x, badge_y, badge_w, badge_h), 16, 16)
            painter.setPen(QPen(QColor(badge_color.red(), badge_color.green(), badge_color.blue(), 80), 1))
            painter.setBrush(QBrush(QColor(badge_color.red(), badge_color.green(),
                                          badge_color.blue(), 25)))
            painter.drawPath(path)

            painter.setPen(QPen(QColor(badge_color.red(), badge_color.green(), badge_color.blue(), 220)))
            painter.setFont(QFont("PingFang SC", 10, QFont.Bold))
            painter.drawText(QRectF(badge_x + 10, badge_y, badge_w - 20, badge_h),
                             Qt.AlignVCenter | Qt.AlignLeft, level_label)

            if countdown_text:
                painter.setPen(QPen(QColor(badge_color.red(), badge_color.green(), badge_color.blue(), 150)))
                painter.setFont(QFont("Menlo", 9))
                painter.drawText(QRectF(badge_x + 10, badge_y, badge_w - 20, badge_h),
                                 Qt.AlignVCenter | Qt.AlignRight, countdown_text)

        # ── 底部标签 ──
        painter.setPen(QPen(QColor(50, 80, 130, 60)))
        painter.setFont(QFont("Menlo", 9))
        painter.drawText(QRectF(0, h - 36, w, 18),
                         Qt.AlignCenter, "ORBIT CONTROL")

        painter.end()


# ════════════════ 子模块窗口 ════════════════

class _ModuleWindow(QMainWindow):
    """模块弹窗 — 近景星球视图"""

    def __init__(self, planet: dict, parent=None):
        super().__init__(parent)
        self._planet = planet
        self.setWindowTitle(f"一人公司 — {planet['name']}")
        self.setMinimumSize(600, 440)

        # 从 style 推导主题色
        style = PLANET_STYLES.get(planet.get("style", "neptune"), PLANET_STYLES["neptune"])
        surface = style.get("surface", [("0.5", "#4488ff")])
        main_color = surface[len(surface)//2][1]
        c = QColor(main_color)
        color_name = c.name()

        bg = QWidget()
        bg.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(4,8,20,240), stop:1 rgba(8,16,36,240));
            border: 2px solid rgba({c.red()},{c.green()},{c.blue()},60);
            border-radius: 14px;
        """)
        self.setCentralWidget(bg)

        layout = QVBoxLayout(bg)
        layout.setSpacing(10)
        layout.setContentsMargins(30, 24, 30, 24)

        head = QHBoxLayout()
        icon = QLabel("●")
        icon.setStyleSheet(f"color: {color_name}; font-size: 20px; background:transparent;")
        head.addWidget(icon)

        name = QLabel(planet["name"])
        name.setStyleSheet(f"color: #ddeeff; font-size: 20px; font-weight: 700; letter-spacing: 4px; background:transparent;")
        head.addWidget(name)
        head.addStretch()
        layout.addLayout(head)

        body = QLabel(f"「{planet['name']}」模块\n\n功能开发中...\n\n通过 Agent 对话或语音来操作此模块。")
        body.setAlignment(Qt.AlignCenter)
        body.setWordWrap(True)
        body.setStyleSheet("color: #667788; font-size: 14px; background: transparent; line-height: 1.8;")
        layout.addWidget(body, 1)

        close_btn = QPushButton("关闭")
        close_btn.setFixedSize(100, 34)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba({c.red()},{c.green()},{c.blue()},30);
                color: {color_name};
                border: 1px solid rgba({c.red()},{c.green()},{c.blue()},50);
                border-radius: 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: rgba({c.red()},{c.green()},{c.blue()},60);
            }}
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)