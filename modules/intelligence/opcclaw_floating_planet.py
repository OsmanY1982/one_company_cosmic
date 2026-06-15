# -*- coding: utf-8 -*-
"""
opcclaw 悬浮星球 — 桌面常驻 AI 助理
可拖拽、语音对话（Apple Speech 引擎）、右键菜单导航、双击对话
"""
import sys, os, traceback, math, random
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QMenu, QAction, QApplication, QDialog,
    QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel,
    QMessageBox, QSystemTrayIcon,
)
from PyQt5.QtCore import (
    Qt, QTimer, QPoint, QRect, QSize, QPointF,
    QPropertyAnimation, QEasingCurve, pyqtProperty,
    QThread, QObject, pyqtSignal,
)
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QRadialGradient,
    QLinearGradient, QPainterPath, QRegion, QMouseEvent,
    QFont, QPixmap, QIcon,
)

# 确保项目根目录在 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.planet_painter import PLANET_STYLES, paint_planet
from core.shapes import alien, robot_alien, ghost_alien, jellyfish_alien
from core.shapes import SHAPE_PAINTERS, SHAPE_MODE_LIST, SHAPE_MODES, SHAPE_PLANETS, SHAPE_ALIENS, SHAPE_STARSHIPS
from .voice_interface import VoiceInterface


# ═══════════ 悬浮星球主窗口 ═══════════

class FloatingPlanet(QWidget):
    """桌面悬浮星球 — frameless + always-on-top + 圆形遮罩"""

    # 状态
    SLEEP = "sleep"
    WAKING = "waking"
    ACTIVE = "active"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"

    # 尺寸参数
    SLEEP_SIZE = 85
    ACTIVE_SIZE = 117

    # ── 动画属性（pyqtProperty）──
    def _get_hover_scale(self):
        return self._hover_scale
    def _set_hover_scale(self, val):
        self._hover_scale = val
        self.update()
    hoverScale = pyqtProperty(float, _get_hover_scale, _set_hover_scale)

    def _get_click_pulse(self):
        return self._click_pulse
    def _set_click_pulse(self, val):
        self._click_pulse = val
        self.update()
    clickPulse = pyqtProperty(float, _get_click_pulse, _set_click_pulse)

    def __init__(self, opcclaw_engine=None,
                 role: str = "admin",
                 membership_info: dict = None,
                 config: dict = None):
        """
        Args:
            opcclaw_engine: opcclaw AI 引擎实例
            role: 用户角色
            membership_info: 会员信息
            config: 模型配置
        """
        super().__init__()
        self._engine = opcclaw_engine
        self._role = role or "admin"
        self._membership_info = membership_info or {}
        self._config = config or {}

        # 状态
        self._state = self.SLEEP
        self._current_size = self.SLEEP_SIZE
        self._target_size = self.SLEEP_SIZE

        # 拖拽
        self._dragging = False
        self._drag_start = QPoint()

        # 动画
        self._anim_t = 0.0
        self._hover = False

        # ── 悬停缩放动画 ──
        self._hover_scale = 1.0           # 悬停缩放因子 (1.0=正常, 1.08=放大)
        self._hover_anim = QPropertyAnimation(self, b"hoverScale")
        self._hover_anim.setDuration(200)  # 200ms 平滑过渡
        self._hover_anim.setEasingCurve(QEasingCurve.OutCubic)

        # ── 点击脉冲动画 ──
        self._click_pulse = 0.0           # 脉冲强度 (0.0=无, 1.0=最强)
        self._pulse_anim = QPropertyAnimation(self, b"clickPulse")
        self._pulse_anim.setDuration(350)
        self._pulse_anim.setEasingCurve(QEasingCurve.OutCubic)

        # ── 缩放倍数 ──
        self._scale_multiplier = 1.0     # 缩放倍数 (0.5x ~ 3.0x)

        # ── 物理漫游 ──
        self._auto_move = True           # 是否启用自动漫游
        self._vx = 0.0                   # 水平速度 (px/frame)
        self._vy = 0.0                   # 垂直速度
        self._gravity = 0.015            # 重力加速度（降低，更柔和）
        self._bounce_factor = 0.3        # 碰撞能量保留率（降低，快速停稳）
        self._drag_pause = False         # 拖拽时暂停物理
        self._drag_trail = []            # 拖拽轨迹点 (用于 fling)
        self._drag_trail_max = 5         # 保留最近 N 个轨迹点
        self._wander_timer = 0           # 漫游计时器（帧计数）
        self._next_wander = 120          # 下次随机扰动的帧间隔（初始值，后续按 10-25s 随机）

        # ── 语音接口 ──
        self._voice = VoiceInterface(stt_engine="whisper")
        print(f"[FloatingPlanet] VoiceInterface stt={self._voice.stt_engine}, tts={self._voice.tts_engine}")
        self._voice.recognition_result.connect(self._on_voice_result)
        self._voice.recognition_status.connect(self._on_voice_status)
        self._voice.error_occurred.connect(self._on_voice_error)
        self._last_voice_text = ""
        self._voice_enabled = True  # 可动态禁用
        self._voice_handlers_active = True  # 信号连接状态

        # ── 语音唤醒 ──
        self._wake_word_mode = True        # 默认启用持续监听唤醒
        self._wake_words = ["球球", "星仔", "球球在吗", "小助手", "助理"]
        self._wake_pending = False           # 已检测到唤醒词，等待命令
        self._exit_words = ["退出", "关闭", "再见", "拜拜", "睡觉", "休息", "退下"]
        self._whisper_wake_recognizer = None  # Whisper 唤醒模式专用识别器

        # 星球样式（默认地球）
        self._style = PLANET_STYLES.get("earth", PLANET_STYLES["neptune"])

        # shapes 形态系统 —— 28 种形态（新 shapes 模块渲染）
        self._shape_mode = None  # None=使用旧 planet_painter；"classic"/etc=使用 shapes
        self._planet_keys = SHAPE_PLANETS.copy()     # 星球形态
        self._alien_keys = SHAPE_ALIENS.copy()       # 外星人形态
        self._starship_keys = SHAPE_STARSHIPS.copy() # 太空星舰形态
        self._current_category = "planet"            # 当前分类："planet" / "alien" / "starship"
        self._current_planet_idx = 0                 # 星球索引
        self._current_alien_idx = 0                  # 外星人索引
        self._current_starship_idx = 0               # 太空星舰索引

        # ── 外星人装饰 ──
        self._aliens = self._spawn_aliens()  # [(type, x, y, vx, vy, phase, size), ...]
        self._mouse_x = 0
        self._mouse_y = 0

        # 窗口配置 — 无边框置顶独立窗口
        self.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 初始位置：右下角
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = geom.right() - self.ACTIVE_SIZE - 30
            y = geom.bottom() - self.ACTIVE_SIZE - 30
        else:
            x, y = 1300, 700

        self.setGeometry(x, y, self.ACTIVE_SIZE, self.ACTIVE_SIZE)
        self._apply_circular_mask()

        # 动画定时器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)  # ~60fps (原 30ms → 16ms)

        # 提示标签（休眠态悬浮显示）
        self._tooltip = QLabel("opcclaw", self)
        self._tooltip.setAlignment(Qt.AlignCenter)
        self._tooltip.setStyleSheet(
            "color: rgba(255,255,255,180); font-size: 10px; background: transparent;"
        )
        s = self._scaled_widget_size()
        self._tooltip.setGeometry(0, s // 2 - 10, s, 20)
        self._tooltip.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._tooltip.hide()

        # 内嵌 AI 对话
        from modules.intelligence.ai_chat_window import AIChatWindow
        self._chat_widget = AIChatWindow(self, opcclaw_engine=self._engine, embedded=True)
        self._chat_widget.hide()
        self._pre_chat_geometry = None

        # 默认启用语音唤醒
        if self._wake_word_mode:
            self._wake_pending = False
            self._enable_voice_handlers()
            QTimer.singleShot(1000, self._start_wake_on_init)

        # 守护进程清理回调（由 planet_daemon.py 注入）
        self._daemon_cleanup = None
        self._cleanup_done = False

    def _start_wake_on_init(self):
        """初始化时启动语音唤醒"""
        stt = self._voice.stt_engine
        print(f"[Wake] _start_wake_on_init: stt={stt}")
        if stt == "whisper":
            # 先用Apple Speech立即启动唤醒，后台加载Whisper
            print("[Wake] 先用 Apple Speech 启动唤醒，后台加载 Whisper...")
            self._start_wake_listen()
            # 后台加载 Whisper
            QTimer.singleShot(500, self._start_whisper_wake)
        else:
            self._start_wake_listen()

    # ── 圆形遮罩 ──

    def _scaled_widget_size(self):
        """返回缩放后的窗口固定尺寸"""
        return max(16, int(self.ACTIVE_SIZE * self._scale_multiplier))

    def _apply_circular_mask(self):
        """应用圆形裁剪区域"""
        s = self._scaled_widget_size()
        region = QRegion(0, 0, s, s, QRegion.Ellipse)
        self.setMask(region)

    # ── 动画 ──

    def _tick(self):
        """每帧更新 —— 物理漫游 + 尺寸过渡 + 动画参数"""
        # ── 物理漫游 ──
        if self._auto_move and not self._drag_pause and not self._dragging:
            # 重力
            self._vy += self._gravity

            # 空气阻力（加大，帮助快速停稳）
            self._vx *= 0.9970
            self._vy *= 0.9970

            # ── 不规则扰动：每隔 ~10-25 秒轻轻推一下 ──
            self._wander_timer += 1
            if self._wander_timer >= self._next_wander:
                self._wander_timer = 0
                self._next_wander = random.randint(600, 1500)  # 10-25 秒
                # 极轻微的随机扰动，只是让球不"死"
                kick_vx = random.uniform(-0.6, 0.6)
                kick_vy = random.uniform(-0.8, 0.4)  # 偏向上方
                self._vx += kick_vx
                self._vy += kick_vy

            # 更新位置
            new_x = self.x() + int(self._vx)
            new_y = self.y() + int(self._vy)

            # 屏幕边界检测 + 带随机扰动的反弹
            screen = QApplication.primaryScreen()
            if screen:
                geom = screen.availableGeometry()
                s = self._scaled_widget_size()
                left, top = geom.left(), geom.top()
                right, bottom = geom.right() - s, geom.bottom() - s

                if new_x < left:
                    new_x = left
                    self._vx = abs(self._vx) * self._bounce_factor
                    self._vy += random.uniform(-1.5, 1.5)  # 水平撞墙扰动垂直
                elif new_x > right:
                    new_x = right
                    self._vx = -abs(self._vx) * self._bounce_factor
                    self._vy += random.uniform(-1.5, 1.5)

                if new_y < top:
                    new_y = top
                    self._vy = abs(self._vy) * self._bounce_factor
                    self._vx += random.uniform(-2.0, 2.0)  # 撞天花板扰动水平
                elif new_y > bottom:
                    new_y = bottom
                    self._vy = -abs(self._vy) * self._bounce_factor
                    self._vx += random.uniform(-2.0, 2.0)  # 撞地板扰动水平
                    if abs(self._vy) < 1.0:
                        self._vy = 0
                        new_y = bottom

            # 超低速时给一个极轻微的随机速度（防止完全静止）
            if abs(self._vx) < 0.3 and abs(self._vy) < 0.3:
                self._vx = random.uniform(-0.5, 0.5)
                self._vy = random.uniform(-1.5, -0.3)  # 轻微向上

            self.move(new_x, new_y)

        # 尺寸平滑过渡（16ms帧率校准）
        diff = self._target_size - self._current_size
        if abs(diff) > 0.5:
            self._current_size += diff * 0.08
            self._center_on_current_pos()
        else:
            self._current_size = self._target_size

        # 动画相位（16ms帧率校准）
        self._anim_t += 0.0133

        # ── 外星人漂移动画 ──
        self._tick_aliens()

        self.update()

    def _center_on_current_pos(self):
        """保持窗口中心不变的情况下调整尺寸（含缩放倍数）"""
        old_center = self.geometry().center()
        base_s = max(int(self._current_size), self.ACTIVE_SIZE)
        s = max(base_s, self._scaled_widget_size())
        new_rect = QRect(0, 0, s, s)
        new_rect.moveCenter(old_center)
        self.setFixedSize(s, s)
        self.setGeometry(new_rect)

        region = QRegion(0, 0, s, s, QRegion.Ellipse)
        self.setMask(region)

    # ── 状态切换 ──

    def wake(self):
        """唤醒 —— 放大 + 亮度提升"""
        if self._state == self.ACTIVE:
            return
        self._state = self.WAKING
        self._target_size = self.ACTIVE_SIZE
        QTimer.singleShot(300, self._on_wake_complete)

    def _on_wake_complete(self):
        if self._state == self.WAKING:
            self._state = self.ACTIVE

    def sleep(self):
        """休眠 —— 缩小 + 变暗"""
        self._state = self.SLEEP
        self._target_size = self.SLEEP_SIZE

    def toggle(self):
        """切换唤醒/休眠"""
        if self._state == self.SLEEP:
            self.wake()
        else:
            self.sleep()
        # 点击脉冲反馈
        self._trigger_click_pulse()

    def _trigger_click_pulse(self):
        """触发点击脉冲动画（ripple 反馈）"""
        self._pulse_anim.stop()
        self._click_pulse = 1.0
        self._pulse_anim.setStartValue(1.0)
        self._pulse_anim.setEndValue(0.0)
        self._pulse_anim.start()
        self.update()

    # ── 拖拽 ──

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            # 优先检测外星人点击
            pos = event.pos()
            cx, cy = self.width() / 2, self.height() / 2
            radius = self._current_size / 2
            hit_alien = self._check_alien_click(cx, cy, radius, pos.x(), pos.y())
            if hit_alien is not None:
                self._alien_click_animation(hit_alien)
                event.accept()
                return
            self._dragging = True
            self._drag_start = event.globalPos() - self.frameGeometry().topLeft()
            self._drag_trail = [(event.globalPos(), datetime.now())]
            self._drag_pause = True
            event.accept()
        elif event.button() == Qt.RightButton:
            self._show_context_menu(event.globalPos())
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        # 追踪鼠标窗口内坐标（外星人 hover 检测用）
        self._mouse_x = event.pos().x()
        self._mouse_y = event.pos().y()
        if self._dragging and event.buttons() & Qt.LeftButton:
            # 移动距离足够才开始拖动（防止误触）
            delta = event.globalPos() - (self.frameGeometry().topLeft() + self._drag_start)
            if delta.manhattanLength() > 5 or self._state == self.ACTIVE:
                self.move(event.globalPos() - self._drag_start)
                # 记录拖拽轨迹 (时间戳 + 位置)
                now = datetime.now()
                self._drag_trail.append((event.globalPos(), now))
                # 只保留最近 N 个点
                if len(self._drag_trail) > self._drag_trail_max:
                    self._drag_trail = self._drag_trail[-self._drag_trail_max:]
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._dragging:
            total_delta = event.globalPos() - (self.frameGeometry().topLeft() + self._drag_start)
            self._dragging = False
            self._drag_pause = False

            # 抛出速度检测 (fling)
            if self._auto_move and len(self._drag_trail) >= 2:
                p0, t0 = self._drag_trail[0]
                p1, t1 = self._drag_trail[-1]
                dt = (t1 - t0).total_seconds()
                if dt > 0.005:
                    dx = p1.x() - p0.x()
                    dy = p1.y() - p0.y()
                    # 帧率约 60fps，转换为每帧速度
                    self._vx = (dx / dt) / 60.0
                    self._vy = (dy / dt) / 60.0
                    # 限制最大初速度
                    max_speed = 18.0
                    speed = math.sqrt(self._vx**2 + self._vy**2)
                    if speed > max_speed:
                        self._vx = self._vx / speed * max_speed
                        self._vy = self._vy / speed * max_speed

            self._drag_trail = []

            # 没有明显移动 = 单击
            if total_delta.manhattanLength() < 5:
                self.toggle()
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """双击打开 AI 对话"""
        self._open_chat()
        event.accept()

    def wheelEvent(self, event):
        """滚轮切换形态"""
        delta = event.angleDelta().y()
        self._cycle_shape(1 if delta > 0 else -1)
        event.accept()

    def enterEvent(self, event):
        self._hover = True
        # 平滑缩放过渡
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_scale)
        self._hover_anim.setEndValue(1.08)
        self._hover_anim.start()
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        # 平滑缩回过渡
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_scale)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()
        self.update()

    # ── 右键菜单 ──

    def _show_context_menu(self, global_pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: rgba(20, 20, 40, 240);
                color: #e0e0ff;
                border: 1px solid rgba(100, 160, 255, 80);
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 6px 28px 6px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: rgba(80, 140, 255, 60);
            }
        """)

        shape_icons = {
            k: v.get("name", k) for k, v in SHAPE_MODES.items()
        }

        # ═══════════ 悬浮球子菜单 ═══════════
        floating_menu = menu.addMenu("悬浮球")
        floating_menu.setStyleSheet(menu.styleSheet())

        planet_menu = floating_menu.addMenu("星球形态")
        planet_menu.setStyleSheet(floating_menu.styleSheet())
        for key in self._planet_keys:
            label = shape_icons.get(key, key)
            action = planet_menu.addAction(label)
            action.triggered.connect(
                lambda checked, cat="planet", k=key: self._switch_to_shape(cat, k)
            )

        alien_menu = floating_menu.addMenu("外星人形态")
        alien_menu.setStyleSheet(floating_menu.styleSheet())
        for key in self._alien_keys:
            label = shape_icons.get(key, key)
            action = alien_menu.addAction(label)
            action.triggered.connect(
                lambda checked, cat="alien", k=key: self._switch_to_shape(cat, k)
            )

        starship_menu = floating_menu.addMenu("太空星舰")
        starship_menu.setStyleSheet(floating_menu.styleSheet())
        for key in self._starship_keys:
            label = shape_icons.get(key, key)
            action = starship_menu.addAction(label)
            action.triggered.connect(
                lambda checked, cat="starship", k=key: self._switch_to_shape(cat, k)
            )

        # ═══════════ AI对话子菜单 ═══════════
        ai_menu = menu.addMenu("AI对话")
        ai_menu.setStyleSheet(menu.styleSheet())

        chat_action = ai_menu.addAction("AI 对话")
        chat_action.triggered.connect(self._open_chat)

        ai_menu.addSeparator()

        model_action = ai_menu.addAction("模型设置")
        model_action.triggered.connect(self._open_model_config)

        ai_menu.addSeparator()

        # 打开各模块
        modules_menu = ai_menu.addMenu("打开模块")
        modules_menu.setStyleSheet(ai_menu.styleSheet())
        modules = [
            ("business", "业务管理"),
            ("intelligence", "智能中心"),
            ("data", "数据中心"),
        ]
        if self._role == "admin":
            modules += [
                ("personnel", "人员管理"),
                ("system", "系统设置"),
            ]

        for mid, mname in modules:
            action = modules_menu.addAction(mname)
            action.setData(mid)
            action.triggered.connect(
                lambda checked, m=mid: self._open_module(m)
            )

        # ═══════════ 语音对话子菜单 ═══════════
        voice_menu = menu.addMenu("语音对话")
        voice_menu.setStyleSheet(menu.styleSheet())

        voice_action = voice_menu.addAction("语音对话")
        voice_action.triggered.connect(self._start_voice_chat)

        voice_menu.addSeparator()

        wake_action = voice_menu.addAction("语音唤醒 (开)" if self._wake_word_mode else "语音唤醒 (关)")
        wake_action.triggered.connect(self._toggle_wake_word)

        # ═══════════ 缩放倍数子菜单 ═══════════
        scale_menu = menu.addMenu("缩放倍数")
        scale_menu.setStyleSheet(menu.styleSheet())
        scale_options = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
        for val in scale_options:
            label = f"{val:.2f}x" if val != int(val) else f"{val:.1f}x"
            if abs(self._scale_multiplier - val) < 0.01:
                label = f"✓ {label}"
            action = scale_menu.addAction(label)
            action.triggered.connect(
                lambda checked, v=val: self._set_scale_multiplier(v)
            )

        menu.addSeparator()

        # ═══════════ 第一层独立项 ═══════════
        move_action = menu.addAction("自动漫游 (开)" if self._auto_move else "自动漫游 (关)")
        move_action.triggered.connect(self._toggle_auto_move)

        exit_action = menu.addAction("退出悬浮球")
        exit_action.triggered.connect(self._on_exit)

        menu.exec_(global_pos)

    # ── 打开模块 ──

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
            print(f"[FloatingPlanet] Failed to open module {module_id}: {e}")
            traceback.print_exc()

    # ── shapes 形态切换 ──

    def _switch_to_shape(self, category: str, key: str):
        """切换到指定分类中的指定形态"""
        if category == "planet":
            if key in self._planet_keys:
                self._current_planet_idx = self._planet_keys.index(key)
                self._shape_mode = key
                self._current_category = "planet"
        elif category == "alien":
            if key in self._alien_keys:
                self._current_alien_idx = self._alien_keys.index(key)
                self._shape_mode = key
                self._current_category = "alien"
        elif category == "starship":
            if key in self._starship_keys:
                self._current_starship_idx = self._starship_keys.index(key)
                self._shape_mode = key
                self._current_category = "starship"
        else:
            return
        name = SHAPE_MODES.get(key, {}).get("name", key)
        self._tooltip.setText(f"opcclaw · {name}")
        print(f"[FloatingPlanet] 切换到形态: {name} ({key})")

    def _cycle_shape(self, direction: int):
        """在当前分类内循环切换形态（+1 下一个, -1 上一个）"""
        if self._current_category == "planet":
            keys = self._planet_keys
            idx = (self._current_planet_idx + direction) % len(keys)
            self._current_planet_idx = idx
        elif self._current_category == "starship":
            keys = self._starship_keys
            idx = (self._current_starship_idx + direction) % len(keys)
            self._current_starship_idx = idx
        else:
            keys = self._alien_keys
            idx = (self._current_alien_idx + direction) % len(keys)
            self._current_alien_idx = idx
        key = keys[idx]
        self._switch_to_shape(self._current_category, key)

    # ── 外星人装饰 ──

    def _spawn_aliens(self):
        """生成 2-3 个随机外星人，初始分布在星球周围"""
        import random
        alien_types = [alien, robot_alien, ghost_alien, jellyfish_alien]
        count = random.randint(2, 3)
        aliens = []
        for i in range(count):
            angle = i * (2 * math.pi / count) + random.uniform(-0.3, 0.3)
            dist = random.uniform(1.4, 2.2)  # 初始距离（以星球半径为单位）
            aliens.append([
                random.choice(alien_types),   # type
                math.cos(angle) * dist,        # x (相对于中心的归一化坐标)
                math.sin(angle) * dist,        # y
                random.uniform(-0.3, 0.3),     # vx
                random.uniform(-0.3, 0.3),     # vy
                random.uniform(0, 2 * math.pi),# phase
                random.uniform(12, 18),        # size (px)
            ])
        return aliens

    def _tick_aliens(self):
        """更新外星人位置（柔和漂浮环绕）"""
        import random
        rng = random.Random(int(self._anim_t * 1000) % 100000 + 42)
        for a in self._aliens:
            # 缓动朝向环绕轨道
            x, y = a[1], a[2]
            dist = math.hypot(x, y)
            angle = math.atan2(y, x)
            # 目标轨道距离 1.5-2.5
            target_dist = 1.6 + a[6] * 0.03
            # 径向弹簧力
            radial_force = (target_dist - dist) * 0.003
            # 切向旋转力
            orbital_speed = 0.15 + a[6] * 0.004
            # 施加力
            a[3] += math.cos(angle) * radial_force - math.sin(angle) * orbital_speed
            a[4] += math.sin(angle) * radial_force + math.cos(angle) * orbital_speed
            # 随机微扰
            a[3] += rng.uniform(-0.02, 0.02)
            a[4] += rng.uniform(-0.02, 0.02)
            # 阻尼
            a[3] *= 0.99
            a[4] *= 0.99
            # 速度限制
            speed = math.hypot(a[3], a[4])
            max_speed = 0.8
            if speed > max_speed:
                a[3] *= max_speed / speed
                a[4] *= max_speed / speed
            # 更新位置
            a[1] += a[3]
            a[2] += a[4]
            # 相位
            a[5] += 0.033

    def _draw_aliens(self, painter, cx, cy, radius):
        """绘制所有外星人"""
        planet_r = radius * 0.82  # 星球可见半径（留边距给光环）
        for a in self._aliens:
            atype = a[0]
            # 归一化坐标转像素坐标，限制在星球外环一定范围
            ax = cx + a[1] * planet_r
            ay = cy + a[2] * planet_r
            asize = a[6]
            # 外星人半径限制在星球外围 1.2-3.0 倍半径
            draw_center = QPointF(ax, ay)
            # 探测 hover：鼠标与外星人中心距离
            dist_to_mouse = math.hypot(
                self._mouse_x - ax, self._mouse_y - ay
            )
            hovered = dist_to_mouse < asize * 1.5
            try:
                atype.paint(painter, draw_center, asize,
                           a[5], hovered, 0.85)
            except Exception:
                pass  # 外星人绘制失败不阻断整体渲染

    def _check_alien_click(self, cx, cy, radius, click_x, click_y):
        """检测点击是否命中外星人，返回命中类型或 None"""
        planet_r = radius * 0.82
        for a in self._aliens:
            ax = cx + a[1] * planet_r
            ay = cy + a[2] * planet_r
            dist = math.hypot(click_x - ax, click_y - ay)
            if dist < a[6] * 1.5:
                return a[0]
        return None

    def _alien_click_animation(self, alien_type):
        """点击外星人后触发简短动画/对话"""
        # 获取外星人类型名用于提示
        type_names = {
            alien: "小绿外星人",
            robot_alien: "机器外星人",
            ghost_alien: "幽灵外星人",
            jellyfish_alien: "水母外星人",
        }
        name = type_names.get(alien_type, "外星来客")
        # 触发脉冲动画视觉反馈
        self._trigger_click_pulse()
        # 可选的语音提示
        if self._voice:
            try:
                self._voice.speak(f"你好，我是{name}")
            except Exception:
                pass

    # ── 模型设置入口 ──

    def _open_model_config(self):
        """打开模型配置面板（登录后同款界面）"""
        try:
            from modules.auth.model_setup_window import ModelSetupWindow
            self._model_setup_window = ModelSetupWindow(
                username="",
                role=self._role,
                membership_info=self._membership_info,
            )
            self._model_setup_window.show()
        except Exception as e:
            print(f"[FloatingPlanet] Failed to open model config: {e}")
            traceback.print_exc()

    # ── AI 对话 ──

    def _open_chat(self):
        """将悬浮球展开为内嵌 AI 对话窗口（不改变窗口标志，避免重建原生句柄）"""
        self.wake()

        # 保存当前几何状态
        self._pre_chat_geometry = self.geometry()

        # 移除圆形遮罩
        self.clearMask()

        # 暂停星球动画，避免重绘干扰
        self._timer.stop()

        # 展开尺寸并居中到屏幕（保持 FramelessWindowHint | WindowStaysOnTopHint 不变）
        self.setFixedSize(780, 580)
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = geom.center().x() - 390
            y = geom.center().y() - 290
            self.move(x, y)

        # 隐藏星球提示，显示聊天组件
        self._tooltip.hide()
        self._chat_widget.setGeometry(0, 0, 780, 580)
        self._chat_widget.raise_()
        self._chat_widget.show()

        # 连接关闭信号
        self._chat_widget.chat_close_requested.connect(self._close_embedded_chat)

    def _close_embedded_chat(self):
        """从内嵌对话恢复到星球模式（不改变窗口标志）"""
        self._chat_widget.chat_close_requested.disconnect(self._close_embedded_chat)
        self._chat_widget.hide()

        # 恢复之前的位置和尺寸
        if self._pre_chat_geometry:
            self.setGeometry(self._pre_chat_geometry)

        # 恢复圆形遮罩和动画
        self._apply_circular_mask()
        self._timer.start(16)

        self.sleep()

    # ── 退出 ──

    def _on_exit(self):
        """退出悬浮球"""
        reply = QMessageBox.question(
            self, "退出悬浮球",
            "确定要退出悬浮球吗？\n可从主控面板重新启动。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._voice.stop_listening()
            self._do_cleanup()
            self.close()

    def _do_cleanup(self):
        """执行守护进程清理（仅一次，删 plist + bootout）"""
        if self._cleanup_done:
            return
        self._cleanup_done = True
        if self._daemon_cleanup:
            self._daemon_cleanup()

    def closeEvent(self, event):
        """拦截窗口关闭（含 Cmd+Q），执行守护进程清理"""
        self._do_cleanup()
        super().closeEvent(event)

    def _toggle_auto_move(self):
        """切换自动漫游开关"""
        self._auto_move = not self._auto_move
        if self._auto_move:
            # 重新激活时给随机初始推力
            angle = random.uniform(0, math.pi * 2)
            kick = random.uniform(3.0, 6.0)
            self._vx = math.cos(angle) * kick
            self._vy = math.sin(angle) * kick

    def _set_scale_multiplier(self, value: float):
        """设置缩放倍数（带屏幕约束）"""
        # 计算屏幕允许的最大倍数
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            max_by_width = geom.width() * 0.9 / self.ACTIVE_SIZE
            max_by_height = geom.height() * 0.9 / self.ACTIVE_SIZE
            max_scale = min(3.0, max_by_width, max_by_height)
        else:
            max_scale = 3.0
        # 修正到允许范围 [0.5, max_scale]
        value = max(0.5, min(value, max_scale))
        if abs(self._scale_multiplier - value) < 0.01:
            return  # 没变，不操作
        self._scale_multiplier = value
        # 重新设置窗口大小
        old_center = self.geometry().center()
        s = self._scaled_widget_size()
        self.setFixedSize(s, s)
        new_rect = QRect(0, 0, s, s)
        new_rect.moveCenter(old_center)
        self.setGeometry(new_rect)
        self._apply_circular_mask()
        self.update()

    # ── 语音对话 ──

    def _disable_voice_handlers(self):
        """临时断开悬浮球的语音信号（供对话框使用）"""
        if not self._voice_handlers_active:
            return
        try:
            self._voice.recognition_result.disconnect(self._on_voice_result)
        except TypeError:
            import traceback; traceback.print_exc()
        try:
            self._voice.recognition_status.disconnect(self._on_voice_status)
        except TypeError:
            import traceback; traceback.print_exc()
        try:
            self._voice.error_occurred.disconnect(self._on_voice_error)
        except TypeError:
            import traceback; traceback.print_exc()
        self._voice_handlers_active = False

    def _enable_voice_handlers(self):
        """重新连接悬浮球的语音信号"""
        if self._voice_handlers_active:
            return
        self._voice.recognition_result.connect(self._on_voice_result)
        self._voice.recognition_status.connect(self._on_voice_status)
        self._voice.error_occurred.connect(self._on_voice_error)
        self._voice_handlers_active = True

    def _start_voice_chat(self):
        """启动一轮语音对话"""
        if not self._voice_enabled:
            return
        self._enable_voice_handlers()
        self.wake()
        self._state = self.LISTENING
        self._last_voice_text = ""
        self._voice.start_listening(timeout=8.0)

    def _on_voice_status(self, status: str):
        """语音状态更新"""
        print(f"[Voice Status] {status}")
        self._last_voice_text = status
        self.update()

    def _on_voice_result(self, text: str):
        """语音识别结果"""
        text = text.strip()
        print(f"[Voice] result: '{text}' wake_mode={self._wake_word_mode} wake_pending={self._wake_pending}")
        if not text or len(text) < 1:
            return

        # 唤醒模式：先检测唤醒词
        if self._wake_word_mode:
            # 若 Whisper 已接管，忽略 Apple Speech 结果
            if self._whisper_wake_recognizer and self._whisper_wake_recognizer.isRunning():
                return
            if not self._wake_pending:
                for ww in self._wake_words:
                    if ww in text:
                        self._wake_pending = True
                        self._state = self.WAKING
                        self._last_voice_text = "在呢"
                        self.update()
                        if self._voice.is_listening():
                            self._voice.stop_listening()
                        self._voice.speak("在呢")
                        self._voice.synthesis_done.connect(self._on_wake_ack_done)
                        return

                # 未检测到唤醒词，静默重启监听
                self._last_voice_text = ""
                self.update()
                if self._voice.is_listening():
                    self._voice.stop_listening()
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(500, self._start_wake_listen)
                return
            else:
                # 已唤醒，这是命令
                self._wake_pending = False
                if self._check_exit(text):
                    return
                self._last_voice_text = text
                self.update()
                self._query_ai(text)
                return

        # 普通语音对话模式
        self._last_voice_text = text
        self.update()
        if len(text) > 1:
            if self._check_exit(text):
                return
            self._query_ai(text)

    def _query_ai(self, text: str):
        """将语音文本发送给 AI 引擎（任务型输入走 AgentLoop，对话型走 ChatEngine）"""
        if not self._engine:
            self._state = self.ACTIVE
            self._voice.speak("引擎未初始化，请先配置模型。")
            return

        self._state = self.THINKING
        self.update()

        try:
            # AgentBridge.chat() 内置智能路由：检测到任务动词自动走 AgentLoop，
            # 普通对话走 ChatEngine，均返回自然语言回复
            # 语音模式下追加口语化提示
            if self._voice and not self._is_task_intent(text):
                prompt = f"{text}\n\n[语音模式：口语化回复，控制在150字以内]"
            else:
                prompt = text
            reply = self._engine.chat(prompt)
        except Exception as e:
            traceback.print_exc()
            reply = f"出错了: {e}"

        # TTS 朗读回复
        self._state = self.SPEAKING
        self._last_voice_text = reply
        self.update()

        self._voice.speak(reply)
        self._voice.synthesis_done.connect(self._on_speak_done)

    def _is_task_intent(self, text: str) -> bool:
        """判断用户输入是否为任务型意图（需要 AgentLoop 自主执行）"""
        task_keywords = [
            "帮我", "创建", "删除", "修改", "打开", "关闭", "启动", "停止",
            "搜索", "查找", "找出", "整理", "移动", "复制", "保存", "截图",
            "锁屏", "静音", "音量", "写一个", "新建", "生成", "配置",
            "安装", "运行", "执行", "启动应用", "截屏",
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in task_keywords)

    def _on_speak_done(self):
        """朗读完成，恢复状态"""
        self._state = self.ACTIVE
        try:
            self._voice.synthesis_done.disconnect(self._on_speak_done)
        except TypeError:
            import traceback; traceback.print_exc()

        # 唤醒模式下，朗读结束后重新开始监听
        if self._wake_word_mode:
            from PyQt5.QtCore import QTimer
            # Whisper 持续唤醒：AI回复完毕后恢复唤醒监听
            if self._whisper_wake_recognizer and self._whisper_wake_recognizer.isRunning():
                self._whisper_wake_recognizer.resume_wake()
                return
            # Apple Speech 轮询模式（Whisper 未就绪时使用）
            if not self._whisper_wake_recognizer:
                QTimer.singleShot(600, self._start_wake_listen)

    def _check_exit(self, text: str) -> bool:
        """检测退出词，返回 True 表示已拦截并执行退出"""
        for ew in self._exit_words:
            if ew in text:
                self._last_voice_text = "好的，再见！"
                self._state = self.SPEAKING
                self.update()
                self._voice.speak("好的，再见！")
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(1800, self.close)
                return True
        return False

    # ── 语音唤醒 ──

    def _toggle_wake_word(self):
        """切换语音唤醒模式"""
        self._wake_word_mode = not self._wake_word_mode
        print(f"[Wake] toggled: wake_word_mode={self._wake_word_mode}, stt={self._voice.stt_engine}, tts={self._voice.tts_engine}")

        if self._wake_word_mode:
            self._wake_pending = False
            self._enable_voice_handlers()

            # 检测引擎：Whisper 走持续唤醒流，Apple 走轮询监听流
            if self._voice.stt_engine == "whisper":
                self._start_whisper_wake()
            else:
                self._start_wake_listen()
            self.setToolTip("opcclaw · 唤醒已开启")
        else:
            self._wake_pending = False
            self._state = self.ACTIVE
            self.update()
            # 停止 Whisper 唤醒
            if self._whisper_wake_recognizer:
                self._whisper_wake_recognizer.stop()
                self._whisper_wake_recognizer = None
            self.setToolTip("opcclaw · 语音助手")

    def _start_wake_listen(self):
        """开始一轮唤醒监听（Apple Speech 轮询模式）"""
        if not self._wake_word_mode:
            return
        if self._voice.is_listening():
            self._voice.stop_listening()

        self._state = self.SLEEP
        self.update()
        # 强制使用 Apple Speech（不创建 Whisper 实例）
        self._voice.start_apple_listening(timeout=6.0)

    def _start_whisper_wake(self):
        """启动 Whisper 持续唤醒模式（模型常驻，不轮询）"""
        from modules.intelligence.whisper_recognizer import WhisperRecognizer

        if self._whisper_wake_recognizer:
            self._whisper_wake_recognizer.stop()
            self._whisper_wake_recognizer.wait(2000)

        self._whisper_wake_recognizer = WhisperRecognizer(model_size="large-v3")
        self._whisper_wake_recognizer.set_wake_mode(True)

        self._whisper_wake_recognizer.status_changed.connect(self._on_whisper_status)
        self._whisper_wake_recognizer.wake_detected.connect(self._on_whisper_wake)
        self._whisper_wake_recognizer.text_ready.connect(self._on_whisper_command)
        self._whisper_wake_recognizer.error_occurred.connect(self._on_whisper_wake_error)
        self._whisper_wake_recognizer.start()

    def _on_whisper_wake(self):
        """Whisper 检测到唤醒词"""
        self._state = self.WAKING
        self._last_voice_text = "在呢"
        self.update()
        self._voice.speak("在呢")
        # 播放完毕后进入命令录制
        self._voice.synthesis_done.connect(self._on_whisper_ack_done)

    def _on_whisper_ack_done(self):
        """唤醒应答播放完毕 → 开始录制语音命令"""
        try:
            self._voice.synthesis_done.disconnect(self._on_whisper_ack_done)
        except TypeError:
            pass

        if not self._wake_word_mode or not self._whisper_wake_recognizer:
            return

        self._state = self.LISTENING
        self.update()
        self._whisper_wake_recognizer.listen_for_command()

    def _on_whisper_command(self, text: str):
        """Whisper 唤醒后识别到的命令"""
        text = text.strip()
        if not text:
            return
        if self._check_exit(text):
            return
        self._last_voice_text = text
        self.update()
        self._query_ai(text)

    def _on_whisper_status(self, status: str):
        """Whisper 状态更新 — 模型就绪后切换到 Whisper 唤醒"""
        try:
            print(f"[Whisper Status] {status}")
        except OSError:
            pass
        self._last_voice_text = status
        self.update()
        # Whisper 唤醒循环就绪：停止 Apple Speech 轮询，让 Whisper 接管
        if status == "唤醒监听中...":
            try:
                print("[Wake] Whisper 就绪，切换到 Whisper 唤醒")
            except OSError:
                pass
            if self._voice.is_listening():
                self._voice.stop_listening()

    def _on_whisper_wake_error(self, error: str):
        """Whisper 唤醒模式错误 → 降级到 Apple Speech 轮询"""
        self._whisper_wake_recognizer = None
        self._last_voice_text = error
        self.update()
        if self._wake_word_mode:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1000, self._start_wake_listen)

    def _on_wake_ack_done(self):
        """唤醒应答播放完毕 → 开始监听命令"""
        try:
            self._voice.synthesis_done.disconnect(self._on_wake_ack_done)
        except TypeError:
            pass

        if not self._wake_word_mode:
            self._wake_pending = False
            self._state = self.ACTIVE
            self.update()
            return

        self._state = self.LISTENING
        self.update()
        if self._voice.is_listening():
            self._voice.stop_listening()
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(300, lambda: self._voice.start_listening(timeout=6.0))

    def _on_voice_error(self, error: str):
        """语音错误处理"""
        print(f"[Voice Error] {error}")
        self._last_voice_text = error
        self._state = self.ACTIVE
        self.update()

        # 唤醒模式下超时/无语音 → 静默重启监听（仅当 Whisper 未接管时）
        if self._wake_word_mode and not self._whisper_wake_recognizer:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(500, self._start_wake_listen)

    # ── 绘制 ──

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        center = QPointF(self.width() / 2.0, self.height() / 2.0)
        r = self._current_size * self._scale_multiplier / 2

        # ── 悬停缩放 ──
        scaled_r = int(r * self._hover_scale)

        # ── 语音状态光效（增强版）──
        if self._state == self.LISTENING:
            # 多层录音脉冲（红色波纹 + 粒子感）
            for layer in range(3):
                wave_phase = self._anim_t * (5 + layer * 2)
                pulse_r = scaled_r + 8 + int((10 + layer * 6) * abs(math.sin(wave_phase)))
                pulse_grad = QRadialGradient(center, pulse_r)
                pulse_grad.setColorAt(0, QColor(255, 80, 80, 0))
                pulse_grad.setColorAt(0.35, QColor(255, 100, 80, 30 - layer * 8))
                pulse_grad.setColorAt(0.7, QColor(255, 60, 60, 15 - layer * 5))
                pulse_grad.setColorAt(1.0, QColor(255, 80, 80, 0))
                p.setBrush(pulse_grad)
                p.setPen(Qt.NoPen)
                p.drawEllipse(center, pulse_r, pulse_r)
        elif self._state == self.THINKING:
            # 思考旋转光晕（蓝紫多层 + 粒子环）
            for layer in range(3):
                wave_phase = self._anim_t * (4 + layer * 1.5)
                think_r = scaled_r + 6 + int((6 + layer * 4) * abs(math.sin(wave_phase)))
                think_grad = QRadialGradient(center, think_r)
                think_grad.setColorAt(0, QColor(80, 160, 255, 0))
                think_grad.setColorAt(0.3, QColor(100, 180, 255, 35 - layer * 10))
                think_grad.setColorAt(0.6, QColor(140, 100, 255, 20 - layer * 6))
                think_grad.setColorAt(1.0, QColor(80, 160, 255, 0))
                p.setBrush(think_grad)
                p.setPen(Qt.NoPen)
                p.drawEllipse(center, think_r, think_r)
        elif self._state == self.SPEAKING:
            # 朗读波纹（绿色多层）
            for layer in range(3):
                wave_phase = self._anim_t * (6 + layer * 2)
                speak_r = scaled_r + 6 + int((8 + layer * 5) * abs(math.sin(wave_phase)))
                speak_grad = QRadialGradient(center, speak_r)
                speak_grad.setColorAt(0, QColor(80, 255, 120, 0))
                speak_grad.setColorAt(0.3, QColor(80, 255, 140, 35 - layer * 10))
                speak_grad.setColorAt(0.6, QColor(60, 220, 100, 20 - layer * 6))
                speak_grad.setColorAt(1.0, QColor(80, 255, 120, 0))
                p.setBrush(speak_grad)
                p.setPen(Qt.NoPen)
                p.drawEllipse(center, speak_r, speak_r)
        elif self._state in (self.WAKING, self.ACTIVE):
            # 外层多层光晕
            for layer in range(2):
                wave_phase = self._anim_t * (3 + layer * 1.8)
                wave_r = scaled_r + 4 + int((6 + layer * 4) * abs(math.sin(wave_phase)))
                wave_grad = QRadialGradient(center, wave_r)
                wave_grad.setColorAt(0, QColor(80, 160, 255, 0))
                wave_grad.setColorAt(0.4, QColor(80, 160, 255, 12 - layer * 4))
                wave_grad.setColorAt(0.75, QColor(120, 100, 255, 8 - layer * 3))
                wave_grad.setColorAt(1.0, QColor(80, 160, 255, 0))
                p.setBrush(wave_grad)
                p.setPen(Qt.NoPen)
                p.drawEllipse(center, wave_r, wave_r)

        # ── 点击脉冲波纹 ──
        if self._click_pulse > 0.01:
            pulse_alpha = int(80 * self._click_pulse)
            pulse_ring_r = scaled_r + 4 + int(20 * (1.0 - self._click_pulse))
            pulse_grad = QRadialGradient(center, pulse_ring_r)
            pulse_grad.setColorAt(0, QColor(255, 255, 255, 0))
            pulse_grad.setColorAt(0.5, QColor(255, 255, 255, pulse_alpha // 3))
            pulse_grad.setColorAt(0.85, QColor(100, 200, 255, pulse_alpha))
            pulse_grad.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(pulse_grad)
            p.setPen(Qt.NoPen)
            p.drawEllipse(center, pulse_ring_r, pulse_ring_r)

        # 渲染形态：优先 shapes 系统，否则回退 planet_painter
        if self._shape_mode and self._shape_mode in SHAPE_PAINTERS:
            painter_fn = SHAPE_PAINTERS[self._shape_mode]
            if self._shape_mode == "classic":
                mode_name = SHAPE_MODES.get(self._shape_mode, {}).get("name", self._shape_mode)
                painter_fn(p, center, scaled_r, self._anim_t, self._hover, 1.0,
                           style=self._style, label=mode_name)
            else:
                painter_fn(p, center, scaled_r, self._anim_t, self._hover, 1.0)
        else:
            paint_planet(p, center, scaled_r, self._style, hovered=self._hover,
                         anim_t=self._anim_t)

        # 休眠态覆盖半透明暗层
        if self._state == self.SLEEP:
            overlay = QColor(0, 0, 0, 100)
            p.setBrush(overlay)
            p.setPen(Qt.NoPen)
            p.drawEllipse(center, int(r), int(r))

        # ── 外星人装饰 ──
        self._draw_aliens(p, center.x(), center.y(), scaled_r)

        p.end()


# ═══════════ AI 对话弹窗（内嵌） ═══════════


