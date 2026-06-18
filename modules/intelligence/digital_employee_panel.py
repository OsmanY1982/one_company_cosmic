
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
舰队指挥监控面板 · CEO 球球（向舰长汇报）
PyQt5 QDialog — 舰长指挥模式
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QProgressBar, QTextEdit, QLineEdit,
    QPushButton, QFrame,
)
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QPixmap

from modules.intelligence.opcclaw_employee import (
    BallCEOEngine, OpcclawEmployee, EmployeeStatus, ChatType, ChatLog,
)

import math


# ── 几何头像渲染 ─────────────────────────────────

def make_avatar_pixmap(shape: str, color: str, size: int = 48) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    c = QColor(color)
    pen = QPen(c.lighter(130), 2)
    brush = QBrush(c.darker(110))
    painter.setPen(pen)
    painter.setBrush(brush)

    margin = 4
    r = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)
    cx, cy = size / 2, size / 2
    radius = (size - 2 * margin) / 2

    if shape == "circle":
        painter.drawEllipse(r)
    elif shape == "square":
        painter.drawRoundedRect(r, 6, 6)
    elif shape == "triangle":
        pts = [QPointF(cx, margin), QPointF(size - margin, size - margin), QPointF(margin, size - margin)]
        painter.drawPolygon(QPolygonF(pts))
    elif shape == "hexagon":
        pts = [QPointF(cx + radius * math.cos(math.pi/6 + i*math.pi/3),
                       cy - radius * math.sin(math.pi/6 + i*math.pi/3)) for i in range(6)]
        painter.drawPolygon(QPolygonF(pts))
    elif shape == "diamond":
        pts = [QPointF(cx, margin), QPointF(size - margin, cy), QPointF(cx, size - margin), QPointF(margin, cy)]
        painter.drawPolygon(QPolygonF(pts))
    elif shape == "pentagon":
        pts = [QPointF(cx + radius * math.cos(-math.pi/2 + i*2*math.pi/5),
                       cy + radius * math.sin(-math.pi/2 + i*2*math.pi/5)) for i in range(5)]
        painter.drawPolygon(QPolygonF(pts))
    else:
        painter.drawEllipse(r)

    painter.end()
    return pixmap


# ── 员工卡片组件 ─────────────────────────────────

class EmployeeCard(QFrame):
    def __init__(self, employee: OpcclawEmployee, parent=None):
        super().__init__(parent)
        self.employee = employee
        self.setObjectName("employeeCard")
        self.setFixedHeight(130)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(52, 52)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self._update_avatar()
        layout.addWidget(self.avatar_label)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)

        name_layout = QHBoxLayout()
        self.name_label = QLabel(self.employee.name)
        self.name_label.setStyleSheet("font-size:14px;font-weight:bold;color:#e0e6f0;")
        name_layout.addWidget(self.name_label)

        self.role_label = QLabel(self.employee.role)
        self.role_label.setStyleSheet(
            f"font-size:10px;color:{self.employee.role_color};"
            f"background:rgba(255,255,255,0.05);border-radius:8px;padding:1px 8px;"
        )
        name_layout.addWidget(self.role_label)
        name_layout.addStretch()
        info_layout.addLayout(name_layout)

        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size:10px;color:#8899aa;")
        info_layout.addWidget(self.status_label)

        self.task_label = QLabel("待命中...")
        self.task_label.setWordWrap(True)
        self.task_label.setStyleSheet("font-size:11px;color:#aab4c0;")
        self.task_label.setMaximumHeight(28)
        info_layout.addWidget(self.task_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("empProgress")
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        info_layout.addWidget(self.progress_bar)

        layout.addLayout(info_layout, 1)

    def _update_avatar(self):
        pix = make_avatar_pixmap(self.employee.shape, self.employee.role_color, 48)
        self.avatar_label.setPixmap(pix.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def refresh(self):
        emp = self.employee
        self.task_label.setText("待命中..." if emp.status == EmployeeStatus.IDLE else emp.current_task)

        if emp.status == EmployeeStatus.IDLE:
            self.status_label.setText("●  空闲")
            self.status_label.setStyleSheet("font-size:10px;color:#556677;")
            self.progress_bar.setVisible(False)
        elif emp.status == EmployeeStatus.THINKING:
            self.status_label.setText("◉  思考中...")
            self.status_label.setStyleSheet("font-size:10px;color:#5b8def;font-weight:bold;")
            self.progress_bar.setVisible(False)
        elif emp.status == EmployeeStatus.WORKING:
            self.status_label.setText(f"▷  工作中 ({emp.progress}%)")
            self.status_label.setStyleSheet("font-size:10px;color:#3dd6d0;font-weight:bold;")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(emp.progress)
            self.progress_bar.setStyleSheet(f"""
                QProgressBar#empProgress {{ background: rgba(255,255,255,0.05); border: none; border-radius: 3px; }}
                QProgressBar#empProgress::chunk {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {emp.role_color}, stop:1 {emp.role_color}88); border-radius: 3px; }}
            """)
        elif emp.status == EmployeeStatus.REPORTING:
            self.status_label.setText("✦  汇报中...")
            self.status_label.setStyleSheet("font-size:10px;color:#f0c040;font-weight:bold;")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(100)
            self.progress_bar.setStyleSheet("""
                QProgressBar#empProgress { background: rgba(255,255,255,0.05); border: none; border-radius: 3px; }
                QProgressBar#empProgress::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #f0c040, stop:1 #f0c04088); border-radius: 3px; }
            """)

        if emp.status != EmployeeStatus.IDLE:
            self.setStyleSheet(f"""
                QFrame#employeeCard {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 rgba(255,255,255,0.06), stop:1 rgba(255,255,255,0.02));
                    border: 1px solid {emp.role_color}44; border-radius: 12px; }}
            """)
        else:
            self.setStyleSheet("""
                QFrame#employeeCard { background: rgba(255,255,255,0.03);
                    border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; }
            """)


# ── 通信日志 HTML 渲染 ───────────────────────────

def render_log_html(log: ChatLog) -> str:
    t = log.timestamp
    minutes = int(t // 60)
    seconds = int(t % 60)
    time_str = f"{minutes:02d}:{seconds:02d}"

    mt = log.msg_type

    # ── 舰长 → 球球（金色） ──
    if mt == ChatType.CAPTAIN_ORDER or log.sender == "舰长":
        color = "#d4a844"
        border = "#d4a84466"
        bg = "rgba(212,168,68,0.08)"
        header = f'<span style="color:{color};font-weight:bold;">[舰长]</span>'
        header += ' <span style="color:#b8a060;">→ [星仔]</span>'

    # ── 球球 → 舰长（金色文字 + 蓝色背景） ──
    elif mt == ChatType.CAPTAIN_REPORT and log.receiver == "舰长":
        color = "#d4a844"
        border = "#5b8def55"
        bg = "rgba(91,141,239,0.08)"
        header = f'<span style="color:#5b8def;font-weight:bold;">[星仔]</span>'
        header += f' <span style="color:{color};">→ [舰长]</span>'

    # ── 球球拆解广播 ──
    elif mt == ChatType.DISPATCH:
        color = "#8b7ce0"
        border = "#8b7ce066"
        bg = "rgba(139,124,224,0.08)"
        header = f'<span style="color:{color};font-weight:bold;">[星仔] 调度指令</span>'

    # ── 球球 → 员工 ──
    elif log.sender == "球球":
        color = "#5b8def"
        border = "#5b8def55"
        bg = "rgba(91,141,239,0.08)"
        header = f'<span style="color:{color};font-weight:bold;">[星仔]</span>'
        header += f' <span style="color:#7799bb;">→ @{log.receiver}</span>'

    # ── 员工 → 球球 ──
    else:
        color = "#3dd6d0"
        border = "#3dd6d055"
        bg = "rgba(61,214,208,0.06)"
        header = f'<span style="color:{color};font-weight:bold;">[{log.sender}]</span>'

    return f"""
    <div style="margin:4px 2px;padding:6px 10px;border-left:3px solid {border};
        background:{bg};border-radius:0 8px 8px 0;font-size:11px;line-height:1.4;">
        <div style="color:#667788;font-size:9px;margin-bottom:2px;">{time_str}</div>
        <div style="color:#ccd4e0;">{header}</div>
        <div style="color:#99aabb;margin-top:2px;">{log.content}</div>
    </div>"""


# ── 舰队指挥监控面板 ─────────────────────────────

class DigitalEmployeePanel(QDialog):
    """舰队指挥监控台 · CEO 球球（向舰长汇报）"""

    def __init__(self, parent=None, engine=None):
        super().__init__(parent)
        self.setWindowTitle("舰队指挥监控台 · CEO 球球（向舰长汇报）")
        self.setFixedSize(480, 660)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowTitleHint)
        if parent:
            pg = parent.geometry()
            self.move(pg.right() + 20, pg.center().y() - 330)

        self.engine = engine if engine is not None else BallCEOEngine()
        self._shared_engine = engine is not None  # 共享模式：由载体驱动引擎
        self.anim_t = 0.0
        self._cards: list[EmployeeCard] = []
        self._known_log_count = 0

        self._setup_ui()
        self._apply_global_style()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(100)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(6)

        # ── 顶部状态栏 ──
        top_bar = QHBoxLayout()
        self.mode_label = QLabel("舰长指挥模式")
        self.mode_label.setStyleSheet("font-size:12px;color:#d4a844;font-weight:bold;")
        top_bar.addWidget(self.mode_label)
        top_bar.addStretch()
        self.online_label = QLabel("在线: 0")
        self.online_label.setStyleSheet("font-size:12px;color:#8899aa;")
        top_bar.addWidget(self.online_label)
        main_layout.addLayout(top_bar)

        # ── 舰长指令输入栏 ──
        cmd_layout = QHBoxLayout()
        cmd_layout.setSpacing(6)
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("舰长，给球球下达指令...")
        self.cmd_input.setObjectName("captainInput")
        self.cmd_input.setStyleSheet("""
            QLineEdit#captainInput {
                background: rgba(10,14,26,0.8);
                border: 1px solid #d4a84455;
                border-radius: 10px;
                padding: 8px 12px;
                color: #d4a844;
                font-size: 12px;
                selection-background-color: #d4a84444;
            }
            QLineEdit#captainInput:focus {
                border: 1px solid #d4a844aa;
            }
            QLineEdit#captainInput::placeholder {
                color: #665533;
            }
        """)
        self.cmd_input.returnPressed.connect(self._send_captain_order)
        cmd_layout.addWidget(self.cmd_input, 1)

        self.send_btn = QPushButton("▶ 下达")
        self.send_btn.setObjectName("captainSendBtn")
        self.send_btn.setFixedSize(72, 36)
        self.send_btn.setStyleSheet("""
            QPushButton#captainSendBtn {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #d4a844, stop:1 #a08030);
                border: none;
                border-radius: 10px;
                color: #0a0e1a;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton#captainSendBtn:hover {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #e0b850, stop:1 #b09040);
            }
            QPushButton#captainSendBtn:pressed {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #a08030, stop:1 #806020);
            }
        """)
        self.send_btn.clicked.connect(self._send_captain_order)
        cmd_layout.addWidget(self.send_btn)
        main_layout.addLayout(cmd_layout)

        # ── 员工卡片区域 2列×3行 ──
        card_grid = QGridLayout()
        card_grid.setSpacing(8)
        for i, emp in enumerate(self.engine.employees):
            card = EmployeeCard(emp)
            self._cards.append(card)
            row, col = divmod(i, 2)
            card_grid.addWidget(card, row, col)
        main_layout.addLayout(card_grid)

        # ── 分隔线 ──
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:rgba(255,255,255,0.08);")
        sep.setFixedHeight(1)
        main_layout.addWidget(sep)

        # ── 通信日志 ──
        log_title = QLabel("通信日志")
        log_title.setStyleSheet("font-size:12px;color:#667788;font-weight:bold;")
        main_layout.addWidget(log_title)

        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setObjectName("logWidget")
        self.log_widget.setStyleSheet("""
            QTextEdit#logWidget {
                background: rgba(10,14,26,0.6);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 10px;
                padding: 6px;
                color: #99aabb;
                font-size: 11px;
            }
            QScrollBar:vertical { background: transparent; width: 6px; }
            QScrollBar::handle:vertical { background: rgba(255,255,255,0.1); border-radius: 3px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        main_layout.addWidget(self.log_widget, 1)

    def _apply_global_style(self):
        self.setStyleSheet("""
            QDialog { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #0a0e1a, stop:1 #0d1224); }
            QLabel { background: transparent; }
        """)

    def _send_captain_order(self):
        text = self.cmd_input.text().strip()
        if not text:
            return
        ok = self.engine.captain_assign(text)
        if ok:
            self.cmd_input.clear()
        else:
            self.cmd_input.setStyleSheet("""
                QLineEdit#captainInput {
                    background: rgba(10,14,26,0.8);
                    border: 1px solid #d44;
                    border-radius: 10px;
                    padding: 8px 12px;
                    color: #d4a844;
                    font-size: 12px;
                }
            """)
            QTimer.singleShot(800, self._restore_input_style)

    def _restore_input_style(self):
        self.cmd_input.setStyleSheet("""
            QLineEdit#captainInput {
                background: rgba(10,14,26,0.8);
                border: 1px solid #d4a84455;
                border-radius: 10px;
                padding: 8px 12px;
                color: #d4a844;
                font-size: 12px;
                selection-background-color: #d4a84444;
            }
            QLineEdit#captainInput:focus { border: 1px solid #d4a844aa; }
            QLineEdit#captainInput::placeholder { color: #665533; }
        """)

    def _tick(self):
        if not self._shared_engine:
            self.anim_t += 0.1
            self.engine.poll(self.anim_t)

        for card in self._cards:
            card.refresh()

        online = self.engine.get_online_count()
        self.online_label.setText(f"在线: {online}")

        logs = self.engine.chat_logs
        if len(logs) > self._known_log_count:
            new_logs = logs[self._known_log_count:]
            for log_entry in new_logs:
                self.log_widget.append(render_log_html(log_entry))
            self._known_log_count = len(logs)
            scrollbar = self.log_widget.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        self._timer.stop()
        event.accept()

    def showEvent(self, event):
        super().showEvent(event)
        if not self._timer.isActive():
            self._timer.start(100)
