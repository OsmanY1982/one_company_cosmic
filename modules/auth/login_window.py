"""
登录窗口 — 空间站对接场景
中心对接环 + 全息扫描光束输入 + 脉冲星登录按钮
"""
import math
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QLinearGradient, QPainterPath, QFont
)

from core.cosmic import (
    CosmicBackground, SPACE_VOID, HOLO_BORDER, HOLO_FILL,
    ACCENT_CYAN, ACCENT_PURPLE, ACCENT_GOLD
)


class LoginWindow(QMainWindow):
    """空间站对接登录"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("一人公司 — 空间站对接")
        self.setMinimumSize(800, 600)

        # 星空背景
        self._cosmic = CosmicBackground()
        self.setCentralWidget(self._cosmic)

        # HUD 覆盖层
        self._hud = QWidget(self._cosmic)
        self._hud.setAttribute(Qt.WA_TranslucentBackground)
        self._hud.setGeometry(0, 0, 800, 600)

        # 动画状态
        self._ring_angle = 0
        self._pulse = 0
        self._scan_line = 0

        # 对接环参数
        self._ring_radius = 130
        self._ring_segments = 8

        self._build_ui()

        # 动画循环
        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(40)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        self._cosmic.setGeometry(0, 0, self.width(), self.height())

    def _build_ui(self):
        # HUD 使用自定义 paintEvent
        self._hud.paintEvent = self._paint_hud

        # 输入框放在中心偏下
        form = QWidget(self._hud)
        form.setStyleSheet("background: transparent;")
        form_layout = QVBoxLayout(form)
        form_layout.setSpacing(16)
        form_layout.setAlignment(Qt.AlignCenter)

        # 标题
        title = QLabel("一 人 公 司")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: #ccddf0;
            font-size: 28px;
            font-weight: 900;
            letter-spacing: 12px;
            background: transparent;
        """)
        form_layout.addWidget(title)

        # 副标题
        sub = QLabel("SPACE STATION DOCKING")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("""
            color: #445566;
            font-size: 10px;
            letter-spacing: 6px;
            background: transparent;
        """)
        form_layout.addWidget(sub)

        form_layout.addSpacing(20)

        # 输入框 — 全息风格
        input_style = """
            QLineEdit {
                background: rgba(10, 20, 50, 200);
                color: #88ccff;
                border: 1px solid rgba(80, 160, 255, 60);
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 14px;
                min-width: 280px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(0, 200, 255, 200);
                background: rgba(15, 25, 60, 220);
            }
            QLineEdit::placeholder {
                color: #334466;
            }
        """

        self._user_input = QLineEdit()
        self._user_input.setPlaceholderText("呼叫代号")
        self._user_input.setStyleSheet(input_style)
        self._user_input.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(self._user_input)

        self._pass_input = QLineEdit()
        self._pass_input.setPlaceholderText("通行密钥")
        self._pass_input.setEchoMode(QLineEdit.Password)
        self._pass_input.setStyleSheet(input_style)
        self._pass_input.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(self._pass_input)

        form_layout.addSpacing(10)

        # 登录按钮 — 脉冲星
        btn = QPushButton("对 接")
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0066cc, stop:1 #0099ff);
                color: white;
                border: none;
                border-radius: 22px;
                padding: 10px 50px;
                font-size: 15px;
                font-weight: 700;
                letter-spacing: 8px;
                min-width: 200px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0088ee, stop:1 #00bbff);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0055aa, stop:1 #0077cc);
            }
        """)
        btn.clicked.connect(self._on_login)
        form_layout.addWidget(btn, alignment=Qt.AlignCenter)

        # 注册链接
        reg = QLabel("首次到访？申请通行许可")
        reg.setAlignment(Qt.AlignCenter)
        reg.setStyleSheet("""
            color: #445566;
            font-size: 11px;
            background: transparent;
        """)
        reg.setCursor(Qt.PointingHandCursor)
        reg.mousePressEvent = lambda e: self._on_register()
        form_layout.addWidget(reg)

        # 定位表单在窗口中部偏下
        form.move(
            (self.width() - 320) // 2,
            (self.height() - 380) // 2 + 60
        )

    def _tick(self):
        self._ring_angle += 0.02
        self._pulse = (math.sin(self._ring_angle * 2) + 1) / 2
        self._scan_line += 0.03
        self._hud.update()

    def _paint_hud(self, event):
        painter = QPainter(self._hud)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self._hud.width(), self._hud.height()

        cx, cy = w // 2, h // 2 - 40

        # ═══ 外层光晕 ═══
        for layer in range(4, 0, -1):
            r = self._ring_radius + layer * 20
            alpha = int(30 * (1 - layer * 0.2))
            g = QRadialGradient(QPointF(cx, cy), r)
            g.setColorAt(0.6, QColor(0, 150, 255, alpha))
            g.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(g))
            painter.drawEllipse(QPointF(cx, cy), r, r)

        # ═══ 对接环（多层旋转弧段） ═══
        ring_layers = [
            (self._ring_radius, ACCENT_CYAN, 1.5, 0),
            (self._ring_radius - 15, ACCENT_PURPLE, 1.0, math.pi / 4),
            (self._ring_radius + 8, QColor(100, 180, 255), 0.8, -math.pi / 6),
        ]

        for radius, color, width, phase_offset in ring_layers:
            pen = QPen()
            segments = 60
            for i in range(segments):
                a = (i / segments) * math.pi * 2 + self._ring_angle + phase_offset
                next_a = ((i + 1) / segments) * math.pi * 2 + self._ring_angle + phase_offset
                # 每段亮度波动
                bright = 0.5 + 0.5 * math.sin(i * 0.6 + self._ring_angle * 4)
                alpha = int(80 + 140 * bright)
                x1 = cx + math.cos(a) * radius
                y1 = cy + math.sin(a) * radius
                x2 = cx + math.cos(next_a) * radius
                y2 = cy + math.sin(next_a) * radius
                pen.setColor(QColor(color.red(), color.green(), color.blue(), alpha))
                pen.setWidthF(width * (0.8 + 0.4 * bright))
                painter.setPen(pen)
                painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # ═══ 中心核心 ═══
        core_r = 18 + 4 * self._pulse
        core_g = QRadialGradient(QPointF(cx, cy), core_r * 3)
        core_g.setColorAt(0, QColor(200, 240, 255, 200))
        core_g.setColorAt(0.3, QColor(0, 180, 255, 120))
        core_g.setColorAt(0.6, QColor(0, 80, 200, 30))
        core_g.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(core_g))
        painter.drawEllipse(QPointF(cx, cy), core_r * 3, core_r * 3)

        # 核心白点
        painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
        painter.drawEllipse(QPointF(cx, cy), core_r, core_r)

        # ═══ 扫描线 ═══
        scan_y = cy + math.sin(self._scan_line * math.pi) * self._ring_radius * 1.2
        scan_g = QLinearGradient(QPointF(cx - 120, scan_y), QPointF(cx + 120, scan_y))
        scan_g.setColorAt(0, QColor(0, 0, 0, 0))
        scan_g.setColorAt(0.45, QColor(0, 200, 255, 30))
        scan_g.setColorAt(0.5, QColor(0, 200, 255, 80))
        scan_g.setColorAt(0.55, QColor(0, 200, 255, 30))
        scan_g.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(scan_g))
        painter.drawRect(QRectF(cx - 120, scan_y - 1, 240, 2))

        # ═══ 装饰小卫星 ═══
        for i in range(3):
            sat_a = self._ring_angle * 0.3 + i * math.pi * 2 / 3
            sat_r = self._ring_radius + 50
            sx = cx + math.cos(sat_a) * sat_r
            sy = cy + math.sin(sat_a) * sat_r
            painter.setBrush(QBrush(QColor(180, 200, 255, 150)))
            painter.drawEllipse(QPointF(sx, sy), 2.5, 2.5)

        painter.end()

    def _on_login(self):
        username = self._user_input.text().strip()
        password = self._pass_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "对接失败", "呼叫代号和通行密钥不能为空")
            return

        # 暂时用 admin / admin 做演示
        if username == "admin" and password == "admin":
            self._open_dashboard()
        else:
            QMessageBox.warning(self, "对接失败", "呼叫代号或通行密钥错误")

    def _on_register(self):
        QMessageBox.information(self, "申请许可", "注册功能开发中...")

    def _open_dashboard(self):
        from modules.auth.connect_window import ConnectWindow
        self._connect = ConnectWindow()
        self._connect.show()
        self.close()