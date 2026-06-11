# -*- coding: utf-8 -*-
"""
opcclaw 悬浮星球 — 桌面常驻 AI 助理
可拖拽、语音对话（Apple Speech 引擎）、右键菜单导航、双击对话
"""
import sys, os, traceback, math
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QMenu, QAction, QApplication, QDialog,
    QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel,
    QMessageBox, QSystemTrayIcon,
)
from PyQt5.QtCore import (
    Qt, QTimer, QPoint, QRect, QSize, QPointF,
    QPropertyAnimation, QEasingCurve, pyqtProperty,
)
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QRadialGradient,
    QLinearGradient, QPainterPath, QRegion, QMouseEvent,
    QFont, QPixmap, QIcon,
)

# 确保项目根目录在 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.planet_painter import PLANET_STYLES, paint_planet
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
    SLEEP_SIZE = 56
    ACTIVE_SIZE = 78

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

        # ── 语音接口 ──
        self._voice = VoiceInterface()
        self._voice.recognition_result.connect(self._on_voice_result)
        self._voice.recognition_status.connect(self._on_voice_status)
        self._voice.error_occurred.connect(self._on_voice_error)
        self._last_voice_text = ""
        self._voice_enabled = True  # 可动态禁用
        self._voice_handlers_active = True  # 信号连接状态

        # 星球样式 —— 用地球纹理
        self._style = PLANET_STYLES.get("earth", PLANET_STYLES["neptune"])

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
        self._timer.start(30)

        # 提示标签（休眠态悬浮显示）
        self._tooltip = QLabel("opcclaw", self)
        self._tooltip.setAlignment(Qt.AlignCenter)
        self._tooltip.setStyleSheet(
            "color: rgba(255,255,255,180); font-size: 10px; background: transparent;"
        )
        self._tooltip.setGeometry(0, self.ACTIVE_SIZE // 2 - 10, self.ACTIVE_SIZE, 20)
        self._tooltip.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._tooltip.hide()

    # ── 圆形遮罩 ──

    def _apply_circular_mask(self):
        """应用圆形裁剪区域"""
        r = self.ACTIVE_SIZE // 2
        region = QRegion(0, 0, self.ACTIVE_SIZE, self.ACTIVE_SIZE, QRegion.Ellipse)
        self.setMask(region)

    # ── 动画 ──

    def _tick(self):
        """每帧更新 —— 尺寸过渡 + 动画参数"""
        # 尺寸平滑过渡
        diff = self._target_size - self._current_size
        if abs(diff) > 0.5:
            self._current_size += diff * 0.15
            self._center_on_current_pos()
        else:
            self._current_size = self._target_size

        # 动画相位
        self._anim_t += 0.025
        self.update()

    def _center_on_current_pos(self):
        """保持窗口中心不变的情况下调整尺寸"""
        old_center = self.geometry().center()
        s = int(self._current_size)
        new_rect = QRect(0, 0, s, s)
        new_rect.moveCenter(old_center)
        self.setGeometry(new_rect)

        # 圆形遮罩按最大尺寸裁剪，小尺寸时自然显示
        max_s = max(s, self.ACTIVE_SIZE)
        region = QRegion(0, 0, max_s, max_s, QRegion.Ellipse)
        self.setMask(region)

    # ── 状态切换 ──

    def wake(self):
        """唤醒 —— 放大 + 亮度提升"""
        if self._state == self.ACTIVE:
            return
        self._state = self.WAKING
        self._target_size = self.ACTIVE_SIZE
        self._tooltip.hide()
        QTimer.singleShot(300, self._on_wake_complete)

    def _on_wake_complete(self):
        if self._state == self.WAKING:
            self._state = self.ACTIVE

    def sleep(self):
        """休眠 —— 缩小 + 变暗"""
        self._state = self.SLEEP
        self._target_size = self.SLEEP_SIZE
        self._tooltip.show()

    def toggle(self):
        """切换唤醒/休眠"""
        if self._state == self.SLEEP:
            self.wake()
        else:
            self.sleep()

    # ── 拖拽 ──

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_start = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.RightButton:
            self._show_context_menu(event.globalPos())
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and event.buttons() & Qt.LeftButton:
            # 移动距离足够才开始拖动（防止误触）
            delta = event.globalPos() - (self.frameGeometry().topLeft() + self._drag_start)
            if delta.manhattanLength() > 5 or self._state == self.ACTIVE:
                self.move(event.globalPos() - self._drag_start)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._dragging:
            total_delta = event.globalPos() - (self.frameGeometry().topLeft() + self._drag_start)
            self._dragging = False
            # 没有明显移动 = 单击
            if total_delta.manhattanLength() < 5:
                self.toggle()
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """双击打开 AI 对话"""
        self._open_chat()
        event.accept()

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
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

        chat_action = menu.addAction("AI 对话")
        chat_action.triggered.connect(self._open_chat)

        menu.addSeparator()

        # 打开各模块
        modules_menu = menu.addMenu("打开模块")
        modules_menu.setStyleSheet(menu.styleSheet())
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

        menu.addSeparator()

        voice_action = menu.addAction("语音对话")
        voice_action.triggered.connect(self._start_voice_chat)

        menu.addSeparator()

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

    # ── AI 对话 ──

    def _open_chat(self):
        """打开 AI 对话窗口"""
        self.wake()
        try:
            dlg = _ChatDialog(self._engine, self, voice=self._voice)
            dlg.exec_()
        except Exception as e:
            print(f"[FloatingPlanet] Failed to open chat: {e}")
            traceback.print_exc()

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
            self.close()

    # ── 语音对话 ──

    def _disable_voice_handlers(self):
        """临时断开悬浮球的语音信号（供对话框使用）"""
        if not self._voice_handlers_active:
            return
        try:
            self._voice.recognition_result.disconnect(self._on_voice_result)
        except TypeError:
            pass
        try:
            self._voice.recognition_status.disconnect(self._on_voice_status)
        except TypeError:
            pass
        try:
            self._voice.error_occurred.disconnect(self._on_voice_error)
        except TypeError:
            pass
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
        self._last_voice_text = status
        self.update()

    def _on_voice_result(self, text: str):
        """语音识别结果"""
        self._last_voice_text = text
        self.update()

        # 收到最终结果 → 发送给 AI
        if text and len(text) > 1:
            self._query_ai(text)

    def _query_ai(self, text: str):
        """将语音文本发送给 AI 引擎"""
        if not self._engine:
            self._state = self.ACTIVE
            self._voice.speak("引擎未初始化，请先配置模型。")
            return

        self._state = self.THINKING
        self.update()

        try:
            # AgentBridge → ChatEngine 自动管理对话历史 + 工具调用
            voice_text = f"{text}\n\n[语音模式：口语化回复，控制在150字以内]"
            reply = self._engine.chat(voice_text)
        except Exception as e:
            traceback.print_exc()
            reply = f"出错了: {e}"

        # TTS 朗读回复
        self._state = self.SPEAKING
        self._last_voice_text = reply
        self.update()

        self._voice.speak(reply)
        self._voice.synthesis_done.connect(self._on_speak_done)

    def _on_speak_done(self):
        """朗读完成，恢复状态"""
        self._state = self.ACTIVE
        try:
            self._voice.synthesis_done.disconnect(self._on_speak_done)
        except TypeError:
            pass

    def _on_voice_error(self, error: str):
        """语音错误处理"""
        self._last_voice_text = error
        self._state = self.ACTIVE
        self.update()

    # ── 绘制 ──

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        center = QPointF(self.width() / 2.0, self.height() / 2.0)
        r = self._current_size / 2

        # ── 语音状态光效 ──
        if self._state == self.LISTENING:
            # 脉冲录音光晕（红色波纹）
            pulse_r = r + 6 + int(10 * abs(math.sin(self._anim_t * 5)))
            pulse_grad = QRadialGradient(center, pulse_r)
            pulse_grad.setColorAt(0, QColor(255, 80, 80, 0))
            pulse_grad.setColorAt(0.5, QColor(255, 100, 80, 30))
            pulse_grad.setColorAt(1.0, QColor(255, 80, 80, 0))
            p.setBrush(pulse_grad)
            p.setPen(Qt.NoPen)
            p.drawEllipse(center, pulse_r, pulse_r)
        elif self._state == self.THINKING:
            # 思考旋转光晕（蓝色）
            think_r = r + 6 + int(6 * abs(math.sin(self._anim_t * 4)))
            think_grad = QRadialGradient(center, think_r)
            think_grad.setColorAt(0, QColor(80, 160, 255, 0))
            think_grad.setColorAt(0.5, QColor(80, 160, 255, 40))
            think_grad.setColorAt(1.0, QColor(80, 160, 255, 0))
            p.setBrush(think_grad)
            p.setPen(Qt.NoPen)
            p.drawEllipse(center, think_r, think_r)
        elif self._state == self.SPEAKING:
            # 朗读波纹（绿色）
            speak_r = r + 6 + int(8 * abs(math.sin(self._anim_t * 6)))
            speak_grad = QRadialGradient(center, speak_r)
            speak_grad.setColorAt(0, QColor(80, 255, 120, 0))
            speak_grad.setColorAt(0.5, QColor(80, 255, 120, 30))
            speak_grad.setColorAt(1.0, QColor(80, 255, 120, 0))
            p.setBrush(speak_grad)
            p.setPen(Qt.NoPen)
            p.drawEllipse(center, speak_r, speak_r)
        elif self._state in (self.WAKING, self.ACTIVE):
            # 外层光晕
            wave_r = r + 4 + int(6 * abs(math.sin(self._anim_t * 3)))
            wave_grad = QRadialGradient(center, wave_r)
            wave_grad.setColorAt(0, QColor(80, 160, 255, 0))
            wave_grad.setColorAt(0.7, QColor(80, 160, 255, 10))
            wave_grad.setColorAt(1.0, QColor(80, 160, 255, 0))
            p.setBrush(wave_grad)
            p.setPen(Qt.NoPen)
            p.drawEllipse(center, wave_r, wave_r)

        # 使用 planet_painter 绘制星球
        paint_planet(p, center, int(r), self._style, hovered=self._hover)

        # 休眠态覆盖半透明暗层
        if self._state == self.SLEEP:
            overlay = QColor(0, 0, 0, 100)
            p.setBrush(overlay)
            p.setPen(Qt.NoPen)
            p.drawEllipse(center, int(r), int(r))

        p.end()


# ═══════════ AI 对话弹窗（内嵌） ═══════════

class _ChatDialog(QDialog):
    """悬浮球 AI 对话弹窗"""

    def __init__(self, engine, parent=None, voice: VoiceInterface = None):
        super().__init__(parent)
        self._engine = engine
        self._voice = voice
        self.setWindowTitle("opcclaw · AI 对话")
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint
        )
        self.setMinimumSize(420, 480)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 对话历史
        self._history_widget = QTextEdit()
        self._history_widget.setReadOnly(True)
        self._history_widget.setStyleSheet("""
            QTextEdit {
                background: rgba(10, 10, 30, 230);
                color: #c0d0ff;
                border: 1px solid rgba(80, 140, 255, 40);
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
            }
        """)
        layout.addWidget(self._history_widget)

        # 输入区
        input_layout = QHBoxLayout()
        self._input = QTextEdit()
        self._input.setPlaceholderText("输入问题，Ctrl+Enter 发送...")
        self._input.setMaximumHeight(80)
        self._input.setStyleSheet("""
            QTextEdit {
                background: rgba(10, 10, 30, 230);
                color: #e0e0ff;
                border: 1px solid rgba(80, 140, 255, 40);
                border-radius: 8px;
                padding: 6px;
                font-size: 12px;
            }
        """)
        self._input.installEventFilter(self)
        input_layout.addWidget(self._input)

        # 语音按钮
        if self._voice:
            self._mic_btn = QPushButton("🎤")
            self._mic_btn.setToolTip("语音输入")
            self._mic_btn.setFixedSize(36, 36)
            self._mic_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 100, 80, 160);
                    color: white;
                    border: none;
                    border-radius: 18px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background: rgba(255, 130, 100, 200);
                }
            """)
            self._mic_btn.clicked.connect(self._toggle_voice_input)
            input_layout.addWidget(self._mic_btn)

        self._send_btn = QPushButton("发送")
        self._send_btn.setStyleSheet("""
            QPushButton {
                background: rgba(60, 120, 255, 180);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(80, 150, 255, 220);
            }
        """)
        self._send_btn.clicked.connect(self._send)
        input_layout.addWidget(self._send_btn)

        layout.addLayout(input_layout)

    def eventFilter(self, obj, event):
        """Ctrl+Enter 发送"""
        from PyQt5.QtCore import QEvent
        if obj == self._input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
                self._send()
                return True
        return super().eventFilter(obj, event)

    def _toggle_voice_input(self):
        """切换语音输入"""
        if not self._voice:
            return
        if self._voice.is_listening():
            self._voice.stop_listening()
            self._mic_btn.setText("🎤")
            parent = self.parent()
            if hasattr(parent, '_enable_voice_handlers'):
                parent._enable_voice_handlers()
        else:
            parent = self.parent()
            if hasattr(parent, '_disable_voice_handlers'):
                parent._disable_voice_handlers()
            self._voice.recognition_result.connect(self._on_voice_result)
            self._voice.start_listening(timeout=6.0)
            self._mic_btn.setText("⏹️")
            self._mic_btn.setStyleSheet(self._mic_btn.styleSheet().replace("rgba(255, 100, 80, 160)", "rgba(255, 80, 80, 220)"))

    def _on_voice_result(self, text: str):
        """语音识别结果（用于对话框）"""
        if not self._voice:
            return
        try:
            self._voice.recognition_result.disconnect(self._on_voice_result)
        except TypeError:
            pass
        self._input.setText(text)
        self._mic_btn.setText("🎤")
        parent = self.parent()
        if hasattr(parent, '_enable_voice_handlers'):
            parent._enable_voice_handlers()

    def closeEvent(self, event):
        """关闭对话框时恢复悬浮球语音连接"""
        parent = self.parent()
        if hasattr(parent, '_enable_voice_handlers'):
            parent._enable_voice_handlers()
        super().closeEvent(event)

    def _send(self):
        text = self._input.toPlainText().strip()
        if not text:
            return

        self._history_widget.append(f'<p style="color:#80b0ff;"><b>你:</b> {text}</p>')
        self._input.clear()
        self._input.setEnabled(False)
        self._send_btn.setEnabled(False)

        now = datetime.now().strftime("%H:%M")

        # 尝试流式输出（打字机效果）
        if self._engine and hasattr(self._engine, 'chat_stream'):
            # 插入流式占位
            placeholder = (
                f'<p style="color:#c0ffc0;"><b>[{now}] opcclaw:</b> '
                f'<span id="stream_cursor" style="color:#44ff88;">_</span></p>'
            )
            self._history_widget.append(placeholder)
            self._stream_accumulated = ""
            self._stream_now = now

            try:
                self._engine.chat_stream(
                    text,
                    self._on_floating_chunk,
                    self._on_floating_done,
                    self._on_floating_tool,
                )
                return
            except Exception as e:
                # 回退到同步模式
                self._input.setEnabled(True)
                self._send_btn.setEnabled(True)

    # ═══ 流式回调（实例方法 — 确保 QueuedConnection 派发到主线程） ═══

    def _on_floating_chunk(self, chunk: str):
        self._stream_accumulated += chunk
        cursor = self._history_widget.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.BlockUnderCursor)
        cursor.removeSelectedText()
        display = self._stream_accumulated[-500:]
        self._history_widget.append(
            f'<p style="color:#c0ffc0;"><b>[{self._stream_now}] opcclaw:</b> {display}'
            f'<span style="color:#44ff88;">_</span></p>'
        )
        sb = self._history_widget.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_floating_done(self, full_text: str):
        cursor = self._history_widget.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.BlockUnderCursor)
        cursor.removeSelectedText()
        final = full_text.replace('\n', '<br>') if full_text else ''
        if not final:
            self._history_widget.append(
                f'<p style="color:#c0ffc0;"><b>[{self._stream_now}] opcclaw:</b> '
                f'<span style="color:#ff8888;">[响应为空，请重试]</span></p>'
            )
        else:
            self._history_widget.append(
                f'<p style="color:#c0ffc0;"><b>[{self._stream_now}] opcclaw:</b> {final}</p>'
            )
        self._input.setEnabled(True)
        self._send_btn.setEnabled(True)
        self._input.setFocus()
        if self._voice and len(full_text) < 300:
            self._voice.speak(full_text)

    def _on_floating_tool(self, name: str, status: str):
        icon = "OK" if status == "OK" else "FAIL" if status == "Failed" else "..."
        cursor = self._history_widget.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.BlockUnderCursor)
        cursor.removeSelectedText()
        display = self._stream_accumulated[-400:] if self._stream_accumulated else ""
        self._history_widget.append(
            f'<p style="color:#c0ffc0;"><b>[{self._stream_now}] opcclaw:</b> {display}'
            f'<span style="color:#888888;">[{name}: {icon}]</span> '
            f'<span style="color:#44ff88;">_</span></p>'
        )

        # 同步模式（回退）
        if self._engine:
            try:
                reply = self._engine.chat(text)
            except Exception as e:
                traceback.print_exc()
                reply = f"调用失败: {e}"
        else:
            reply = "引擎未初始化，请先在模型配置中选择模型。"

        self._history_widget.append(
            f'<p style="color:#c0ffc0;"><b>opcclaw:</b> {reply}</p>'
        )
        self._input.setEnabled(True)
        self._send_btn.setEnabled(True)

        if self._voice and len(reply) < 300:
            self._voice.speak(reply)
