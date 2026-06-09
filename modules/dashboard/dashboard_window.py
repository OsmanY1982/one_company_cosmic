"""
舰桥主控面板 — AI Agent 指挥中心
对话命令 + 语音输入 + 轨道星球模块
"""
import math
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QTextEdit, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, QThread, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QLinearGradient, QPainterPath, QFont, QTextCursor, QMouseEvent
)

from core.cosmic import CosmicBackground, ACCENT_CYAN, ACCENT_GOLD, ACCENT_PURPLE
from core.agent import AgentCore
from core.llm_client import ModelConfig, LLMClient
from core.voice import VoiceListener


# ═══════════ 模块星球定义 ═══════════
ALL_PLANETS = [
    {"id": "business",     "name": "业务管理", "color": QColor(68, 136, 255),   "radius": 38, "orbit": 160},
    {"id": "personnel",    "name": "人员管理", "color": QColor(255, 102, 68),   "radius": 32, "orbit": 200},
    {"id": "intelligence", "name": "智能中心", "color": QColor(170, 68, 255),   "radius": 42, "orbit": 140},
    {"id": "data",         "name": "数据中心", "color": QColor(0, 204, 170),    "radius": 34, "orbit": 240},
    {"id": "system",       "name": "系统设置", "color": QColor(136, 153, 170),  "radius": 28, "orbit": 280},
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

    def __init__(self, config: ModelConfig = None, role: str = "admin",
                 membership_info: dict = None):
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

        self._config = config
        self._llm = LLMClient(config) if config and config.model_name else None
        self._agent = AgentCore()
        self._register_handlers()

        # 星空背景
        self._cosmic = CosmicBackground()
        self.setCentralWidget(self._cosmic)

        # HUD 层
        self._hud = QWidget(self._cosmic)
        self._hud.setAttribute(Qt.WA_TranslucentBackground)
        self._hud.setGeometry(0, 0, 1200, 760)

        # 动画状态
        self._t = 0
        self._voice_listener: VoiceListener = None
        self._hovered_planet = None
        self._modules_open = {}

        self._build_ui()

        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(45)

        # 让 HUD 接收鼠标事件以检测星球 hover/click
        self._hud.setMouseTracking(True)
        self._hud.mouseMoveEvent = self._on_hud_mouse_move
        self._hud.mousePressEvent = self._on_hud_click

        # 欢迎
        fuel = "引擎就绪" if self._llm else "离线模式"
        if self._role == "member":
            ms = self._membership_info
            level = MEMBERSHIP_LABELS.get(ms.get("membership", "trial"), "体验会员")
            self._add_message("system",
                f"舰桥就绪。Agent {fuel}。当前身份：{level}。输入命令或点击轨道星球。")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._hud.setGeometry(0, 0, self.width(), self.height())

    def _register_handlers(self):
        a = self._agent
        a.register_handler("open", self._do_open)
        a.register_handler("query", self._do_query)
        a.register_handler("create", self._do_create)
        a.register_handler("delete", self._do_delete)
        a.register_handler("analyze", self._do_analyze)
        a.register_handler("system_query", self._do_system_query)
        a.register_handler("help", self._do_help)
        a.register_handler("exit", self._do_exit)

    # ════════════════ 布局 ════════════════

    def _build_ui(self):
        self._hud.paintEvent = self._paint_hud

        # 左侧面板：对话区
        left_panel = QWidget(self._hud)
        left_panel.setStyleSheet("background: transparent;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(6)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        top_bar = QHBoxLayout()
        if self._role == "member":
            ms = self._membership_info
            level_label = MEMBERSHIP_LABELS.get(ms.get("membership", "trial"), "体验会员")
            expire_str = (ms.get("expire_at", ""))[:10] if ms.get("expire_at") else "N/A"
            title_text = f"舰桥 · 船员模式 | {level_label} | 到期: {expire_str}"
        else:
            title_text = "舰桥 · 指挥官模式"
        title = QLabel(title_text)
        title.setStyleSheet("color: #8899bb; font-size: 13px; font-weight: 700; letter-spacing: 4px; background: transparent;")
        top_bar.addWidget(title)
        top_bar.addStretch()

        self._fuel_indicator = QLabel("")
        self._fuel_indicator.setStyleSheet("color: #00cc88; font-size: 9px; background: transparent;")
        if self._config:
            self._fuel_indicator.setText(f"引擎: {self._config.model_name[:16]}")
        top_bar.addWidget(self._fuel_indicator)
        left_layout.addLayout(top_bar)

        # 对话区
        self._chat = QTextEdit()
        self._chat.setReadOnly(True)
        self._chat.setStyleSheet("""
            QTextEdit {
                background: rgba(6, 12, 26, 220);
                color: #bcc8dd;
                border: 1px solid rgba(50, 100, 170, 40);
                border-radius: 10px;
                padding: 10px;
                font-size: 12px;
                line-height: 1.6;
            }
            QScrollBar:vertical { background: rgba(8,14,26,150); width: 5px; border-radius: 2px; }
            QScrollBar::handle:vertical { background: rgba(70,130,200,50); border-radius: 2px; min-height: 16px; }
        """)
        left_layout.addWidget(self._chat, 1)

        # 输入栏
        input_row = QHBoxLayout()
        input_row.setSpacing(6)

        self._voice_btn = QPushButton("语音")
        self._voice_btn.setFixedSize(48, 38)
        self._voice_btn.setCursor(Qt.PointingHandCursor)
        self._voice_btn.clicked.connect(self._toggle_voice)
        self._update_voice_style()
        input_row.addWidget(self._voice_btn)

        self._cmd_input = QLineEdit()
        self._cmd_input.setPlaceholderText("输入命令...")
        self._cmd_input.setStyleSheet("""
            QLineEdit {
                background: rgba(8,16,30,235);
                color: #aaccee;
                border: 1px solid rgba(70,130,200,45);
                border-radius: 18px;
                padding: 8px 15px;
                font-size: 12px;
            }
            QLineEdit:focus { border: 1px solid rgba(0,200,255,160); }
            QLineEdit::placeholder { color: #334466; }
        """)
        self._cmd_input.returnPressed.connect(self._on_send)
        input_row.addWidget(self._cmd_input, 1)

        send_btn = QPushButton("发送")
        send_btn.setFixedSize(48, 38)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setStyleSheet("""
            QPushButton {
                background: rgba(20,50,100,200);
                color: #88bbee;
                border: 1px solid rgba(70,140,220,50);
                border-radius: 18px;
                font-size: 12px; font-weight: 600;
            }
            QPushButton:hover { background: rgba(30,70,140,230); }
        """)
        send_btn.clicked.connect(self._on_send)
        input_row.addWidget(send_btn)

        left_layout.addLayout(input_row)

        # 左侧面板占 30% 宽度
        left_panel.setGeometry(20, 20, 360, self.height() - 40)

    def _layout_left_panel(self):
        """响应 resize 重新布局"""
        left = self._hud.findChildren(QWidget)[0]  # 第一个子 widget 就是 left_panel
        if left:
            left.setGeometry(20, 20, 360, self._hud.height() - 40)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        self._layout_left_panel()

    # ════════════════ 对话 ════════════════

    def _add_message(self, role: str, text: str):
        colors = {
            "user": ("#ffaa44", "你"),
            "system": ("#668899", "舰桥"),
            "agent": ("#44ccff", "Agent"),
            "action": ("#00ee88", "执行"),
        }
        c, tag = colors.get(role, ("#889999", role))
        prefix = f'<span style="color:{c};font-weight:700;">{tag}</span>'
        self._chat.append(f'<p>{prefix} &nbsp;{text}</p>')
        self._chat.moveCursor(QTextCursor.End)

    def _on_send(self):
        text = self._cmd_input.text().strip()
        if not text:
            return
        self._cmd_input.clear()
        self._process_command(text)

    def _process_command(self, text: str):
        self._add_message("user", text)
        if self._llm:
            self._process_with_llm(text)
        else:
            self._process_with_rules(text)

    def _process_with_rules(self, text: str):
        intent = self._agent.parse(text)
        if intent:
            result = self._agent.execute(intent)
            self._add_message("agent", result)
            # 如果是 open，实际跳转
            if intent.action == "open" and intent.target in dict(self.MODULES_LIST):
                self._open_module(intent.target)
        else:
            self._add_message("agent", "无法理解该命令。")

    def _process_with_llm(self, text: str):
        system_prompt = """你是一人公司宇宙飞船的 AI Agent，风格像一个太空飞船 AI 助手。
你可以：打开模块（业务管理/人员管理/智能中心/数据中心/系统设置）、查询信息、分析数据、回答一般问题。
回复简洁（1-3句），带一点太空风味。"""
        try:
            response = self._llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ])
            self._add_message("agent", response)

            # 同时用规则引擎检查是否需要打开模块
            intent = self._agent.parse(text)
            if intent and intent.action == "open" and intent.target in dict(self.MODULES_LIST):
                self._open_module(intent.target)
        except Exception as e:
            self._add_message("agent", f"引擎异常: {e}")
            self._process_with_rules(text)

    # ════════════════ 处理器 ════════════════

    MODULES_LIST = [(p["id"], p["name"], "") for p in ALL_PLANETS]

    def _do_open(self, intent):
        names = {p["id"]: p["name"] for p in self._planets}
        name = names.get(intent.target, intent.target)
        return f"正在导航至「{name}」..."

    def _do_query(self, intent):
        return f"正在全舰搜索「{intent.target}」..."

    def _do_create(self, intent):
        return f"正在创建「{intent.target}」..."

    def _do_delete(self, intent):
        return f"⚠️ 确认删除「{intent.target}」？此操作不可逆。"

    def _do_analyze(self, intent):
        return f"正在分析「{intent.target or '全舰数据'}」..."

    def _do_system_query(self, intent):
        from datetime import datetime
        return f"舰桥时间 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}，一切正常。"

    def _do_help(self, intent):
        return "可用命令：打开模块、搜索信息、分析数据、创建/删除。也可直接点击轨道星球。"

    def _do_exit(self, intent):
        return "引擎降功率中..."

    def _open_module(self, module_id: str):
        """打开子模块窗口"""
        planet = next((p for p in self._planets if p["id"] == module_id), None)
        if not planet:
            return

        # 船员模式权限检查
        if self._role == "member":
            if module_id == "personnel":
                self._add_message("system", "船员权限不足：人员管理仅指挥官可访问")
                return
            if module_id == "system":
                self._add_message("system", "船员权限不足：系统设置仅指挥官可访问")
                return

        if module_id in self._modules_open:
            try:
                self._modules_open[module_id].close()
            except Exception:
                pass

        if module_id == "business":
            from modules.business.business_window import BusinessWindow
            win = BusinessWindow(self)
        elif module_id == "personnel":
            from modules.personnel.personnel_window import PersonnelWindow
            win = PersonnelWindow(self)
        elif module_id == "intelligence":
            from modules.intelligence.intelligence_window import IntelligenceWindow
            win = IntelligenceWindow(self, role=self._role)
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
        self._add_message("action", f"已打开「{planet['name']}」")

    # ════════════════ 语音 ════════════════

    def _toggle_voice(self):
        if self._voice_listener and self._voice_listener.isRunning():
            self._voice_listener.stop()
            self._voice_listener = None
            self._voice_btn.setText("语音")
            self._update_voice_style()
            self._add_message("system", "语音已关闭")
            return

        self._voice_btn.setText("...")
        self._voice_btn.setStyleSheet(self._voice_style(True))
        self._voice_listener = VoiceListener()
        self._voice_listener.result_ready.connect(self._on_voice_result)
        self._voice_listener.status_changed.connect(self._on_voice_status)
        self._voice_listener.start()

    def _on_voice_result(self, text: str):
        if text.strip():
            self._add_message("system", f"识别: {text}")
            self._process_command(text)
        else:
            self._add_message("system", "未识别到内容。")
        self._voice_btn.setText("语音")
        self._update_voice_style()
        self._voice_listener = None

    def _on_voice_status(self, status: str):
        if status == "speak_now":
            self._voice_btn.setText("正在听")
        elif status in ("fallback", "done", "idle"):
            self._voice_btn.setText("语音")
            self._update_voice_style()
            if status == "fallback":
                self._add_message("system", "语音不可用，请打字。")
            self._voice_listener = None
        elif status.startswith("error"):
            self._add_message("system", f"语音错误: {status[6:]}")
            self._voice_btn.setText("语音")
            self._update_voice_style()
            self._voice_listener = None

    def _voice_style(self, active: bool) -> str:
        if active:
            return "QPushButton{background:rgba(255,100,40,160);color:#fff;border:1px solid rgba(255,120,60,200);border-radius:18px;font-size:12px;font-weight:600;}"
        return "QPushButton{background:rgba(20,45,90,200);color:#88bbee;border:1px solid rgba(70,130,200,50);border-radius:18px;font-size:12px;font-weight:600;} QPushButton:hover{background:rgba(30,60,120,230);}"

    def _update_voice_style(self):
        active = self._voice_listener is not None and self._voice_listener.isRunning()
        self._voice_btn.setStyleSheet(self._voice_style(active))

    # ════════════════ 轨道星球交互 ════════════════

    def _get_orbit_center(self) -> QPointF:
        """右侧轨道区域的中心"""
        w = self._hud.width()
        h = self._hud.height()
        return QPointF(w * 0.72, h * 0.48)

    def _get_planet_pos(self, planet: dict) -> QPointF:
        """计算星球当前位置（基于时间和轨道参数）"""
        cx = self._get_orbit_center()
        idx = self._planets.index(planet)
        phase = idx * math.pi * 2 / len(self._planets)
        angle = phase + self._t * (0.15 + idx * 0.04)  # 不同速度
        px = cx.x() + math.cos(angle) * planet["orbit"]
        py = cx.y() + math.sin(angle) * planet["orbit"] * 0.55  # 椭圆效果
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
        painter = QPainter(self._hud)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self._hud.width(), self._hud.height()

        # ── 右侧轨道区背景遮罩 ──
        orb_rect = QRectF(w * 0.46, 10, w * 0.54, h - 20)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(3, 6, 18, 180)))
        painter.drawRoundedRect(orb_rect, 14, 14)

        # 轨道区分隔线
        line_x = w * 0.45
        lg = QLinearGradient(QPointF(line_x, 0), QPointF(line_x + 2, 0))
        lg.setColorAt(0, QColor(0, 0, 0, 0))
        lg.setColorAt(0.5, QColor(60, 120, 200, 50))
        lg.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(QPen(QBrush(lg), 2))
        painter.drawLine(QPointF(line_x, 40), QPointF(line_x, h - 40))

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
        for p in self._planets:
            r = p["orbit"]
            alpha = 15 if p == self._hovered_planet else 8
            painter.setPen(QPen(QColor(p["color"].red(), p["color"].green(),
                                       p["color"].blue(), alpha), 0.8))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(cx, r, r * 0.55)

        # ── 中心 AI 核心 ──
        core_pulse = 0.5 + 0.5 * math.sin(self._t * 1.5)
        core_r = 24 + core_pulse * 8

        # 辉光
        for layer in range(4, 0, -1):
            lr = core_r + layer * 14
            alpha = int((30 + layer * 15) * (1 - layer * 0.18))
            g = QRadialGradient(cx, lr)
            g.setColorAt(0, QColor(0, 180, 255, alpha))
            g.setColorAt(0.5, QColor(0, 100, 220, alpha // 3))
            g.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(g))
            painter.drawEllipse(cx, lr, lr)

        # 核心白点
        painter.setBrush(QBrush(QColor(220, 240, 255)))
        painter.drawEllipse(cx, core_r, core_r)

        # 核心标签
        painter.setPen(QPen(QColor(100, 180, 240, 180)))
        painter.setFont(QFont("Menlo", 8))
        painter.drawText(QRectF(cx.x() - 40, cx.y() + core_r + 14, 80, 16),
                         Qt.AlignCenter, "AI CORE")

        # ── 星球 ──
        for p in self._planets:
            pp = self._get_planet_pos(p)
            c = p["color"]
            is_hovered = p == self._hovered_planet
            r = p["radius"]

            # 辉光
            glow_r = r + (16 if is_hovered else 8)
            for layer in range(3, 0, -1):
                lr = glow_r + layer * 8
                a = int((50 - layer * 12) * (1.4 if is_hovered else 1.0))
                g = QRadialGradient(pp, lr)
                g.setColorAt(0, QColor(c.red(), c.green(), c.blue(), a))
                g.setColorAt(0.6, QColor(c.red(), c.green(), c.blue(), a // 4))
                g.setColorAt(1, QColor(0, 0, 0, 0))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(g))
                painter.drawEllipse(pp, lr, lr)

            # 星球本体
            body_g = QRadialGradient(
                QPointF(pp.x() - r * 0.25, pp.y() - r * 0.25), r * 1.2
            )
            body_g.setColorAt(0, QColor(
                min(c.red() + 60, 255),
                min(c.green() + 60, 255),
                min(c.blue() + 60, 255),
            ))
            body_g.setColorAt(0.6, c)
            body_g.setColorAt(1, QColor(
                max(c.red() - 40, 0),
                max(c.green() - 40, 0),
                max(c.blue() - 40, 0),
            ))
            painter.setBrush(QBrush(body_g))
            painter.setPen(QPen(QColor(c.red(), c.green(), c.blue(), 100), 1.5))
            painter.drawEllipse(pp, r, r)

            # 高亮环（hovered）
            if is_hovered:
                ring_r = r + 6
                ring_g = QRadialGradient(pp, ring_r + 4)
                ring_g.setColorAt(0.7, QColor(0, 0, 0, 0))
                ring_g.setColorAt(0.8, QColor(c.red(), c.green(), c.blue(), 180))
                ring_g.setColorAt(1, QColor(0, 0, 0, 0))
                painter.setPen(QPen(QBrush(ring_g), 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(pp, ring_r, ring_r)

            # 名称标签
            painter.setPen(QPen(QColor(
                min(c.red() + 80, 255),
                min(c.green() + 80, 255),
                min(c.blue() + 80, 255),
                200 if is_hovered else 120
            )))
            painter.setFont(QFont("PingFang SC", 10, QFont.Bold if is_hovered else QFont.Normal))
            painter.drawText(QRectF(pp.x() - 50, pp.y() + r + 6, 100, 20),
                             Qt.AlignCenter, p["name"])

        # ── 会员等级徽章（船员模式） ──
        if self._role == "member" and self._membership_info:
            ms = self._membership_info
            level = ms.get("membership", "trial")
            badge_color = MEMBERSHIP_BADGE_COLORS.get(level, MEMBERSHIP_BADGE_COLORS["trial"])
            level_label = MEMBERSHIP_LABELS.get(level, "体验会员")

            # 计算到期倒计时
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
                    pass

            badge_x = w * 0.6
            badge_y = 14
            badge_w = 180
            badge_h = 32

            # 徽章背景
            path = QPainterPath()
            path.addRoundedRect(QRectF(badge_x, badge_y, badge_w, badge_h), 16, 16)
            painter.setPen(QPen(QColor(badge_color.red(), badge_color.green(), badge_color.blue(), 80), 1))
            painter.setBrush(QBrush(QColor(badge_color.red(), badge_color.green(),
                                          badge_color.blue(), 25)))
            painter.drawPath(path)

            # 等级文字（居中偏左）
            painter.setPen(QPen(QColor(badge_color.red(), badge_color.green(), badge_color.blue(), 220)))
            painter.setFont(QFont("PingFang SC", 10, QFont.Bold))
            painter.drawText(QRectF(badge_x + 10, badge_y, badge_w - 20, badge_h),
                             Qt.AlignVCenter | Qt.AlignLeft, level_label)

            # 倒计时（右侧）
            if countdown_text:
                painter.setPen(QPen(QColor(badge_color.red(), badge_color.green(), badge_color.blue(), 150)))
                painter.setFont(QFont("Menlo", 9))
                painter.drawText(QRectF(badge_x + 10, badge_y, badge_w - 20, badge_h),
                                 Qt.AlignVCenter | Qt.AlignRight, countdown_text)

        # ── 右侧标签 ──
        painter.setPen(QPen(QColor(50, 80, 130, 80)))
        painter.setFont(QFont("Menlo", 9))
        painter.drawText(QRectF(w * 0.5, 24, w * 0.48, 18),
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

        bg = QWidget()
        bg.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(4,8,20,240), stop:1 rgba(8,16,36,240));
            border: 2px solid rgba({planet['color'].red()},{planet['color'].green()},{planet['color'].blue()},60);
            border-radius: 14px;
        """)
        self.setCentralWidget(bg)

        layout = QVBoxLayout(bg)
        layout.setSpacing(10)
        layout.setContentsMargins(30, 24, 30, 24)

        # 标题
        head = QHBoxLayout()
        icon = QLabel("●")
        icon.setStyleSheet(f"color: {planet['color'].name()}; font-size: 20px; background:transparent;")
        head.addWidget(icon)

        name = QLabel(planet["name"])
        name.setStyleSheet(f"color: #ddeeff; font-size: 20px; font-weight: 700; letter-spacing: 4px; background:transparent;")
        head.addWidget(name)
        head.addStretch()
        layout.addLayout(head)

        # 内容占位
        body = QLabel(f"「{planet['name']}」模块\n\n功能开发中...\n\n通过 Agent 对话或语音来操作此模块。")
        body.setAlignment(Qt.AlignCenter)
        body.setWordWrap(True)
        body.setStyleSheet("color: #667788; font-size: 14px; background: transparent; line-height: 1.8;")
        layout.addWidget(body, 1)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setFixedSize(100, 34)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba({planet['color'].red()},{planet['color'].green()},{planet['color'].blue()},30);
                color: {planet['color'].name()};
                border: 1px solid rgba({planet['color'].red()},{planet['color'].green()},{planet['color'].blue()},50);
                border-radius: 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: rgba({planet['color'].red()},{planet['color'].green()},{planet['color'].blue()},60);
            }}
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)