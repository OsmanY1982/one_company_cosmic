import logging

logger = logging.getLogger(__name__)

"""
舰桥主控面板 — AI Agent 指挥中心
轨道星球导航
"""
import traceback
import math
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QDialog, QMessageBox
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
    {"id": "business",     "name": "业务管理", "style": "earth",   "radius": 56, "orbit": 160},
    {"id": "personnel",    "name": "人员管理", "style": "mars",    "radius": 48, "orbit": 205},
    {"id": "intelligence", "name": "智能中心", "style": "jupiter", "radius": 60, "orbit": 142},
    {"id": "data",         "name": "数据中心", "style": "neptune", "radius": 50, "orbit": 248},
    {"id": "system",       "name": "系统设置", "style": "moon",    "radius": 44, "orbit": 288},
    {"id": "account",      "name": "账号与安全", "style": "saturn",  "radius": 48, "orbit": 330},
    {"id": "admin",        "name": "管理后台", "style": "sun",     "radius": 52, "orbit": 370},
]

# 会员可见模块（业务管理 + 智能中心）
MEMBER_PLANET_IDS = {"business", "intelligence", "account"}

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
                 iqra_engine=None):
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

        # iqra 引擎（优先级最高）
        self._iqra = iqra_engine

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

        self._build_ui()

        # 确保 HUD 在星空背景之上
        self._hud.raise_()

        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(45)

        # 让 HUD 接收鼠标事件以检测星球 hover/click
        self._hud.setMouseTracking(True)
        self._hud.mouseMoveEvent = self._on_hud_mouse_move
        self._hud.mousePressEvent = self._on_hud_click

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._hud.setGeometry(0, 0, self.width(), self.height())

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
        if self._iqra:
            self._fuel_indicator.setText("引擎: iqra")
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
            win = IntelligenceWindow(self, role=self._role, iqra_engine=self._iqra)
        elif module_id == "data":
            from modules.data_center.data_window import DataWindow
            win = DataWindow(self)
        elif module_id == "system":
            from modules.system.system_hub_window import SystemHubWindow
            win = SystemHubWindow(self, role=self._role)
        elif module_id == "account":
            self._show_account_tools()
            return
        elif module_id == "admin":
            from modules.admin.admin_window import AdminWindow
            win = AdminWindow(self)
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

    def _open_activation(self):
        """激活许可证"""
        from modules.account.account_activation import AccountActivationWindow
        dlg = AccountActivationWindow(self)
        dlg.exec_()

    def _open_update_check(self):
        """检查更新"""
        from modules.account.account_update import AccountUpdateDialog
        dlg = AccountUpdateDialog(self)
        dlg.exec_()

    # ════════════════ 账号与安全 ════════════════

    def _show_account_tools(self):
        """弹出账号与安全工具面板"""
        import os
        dlg = QDialog(self)
        dlg.setWindowTitle("账号与安全")
        dlg.setMinimumWidth(420)
        dlg.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #080e1a, stop:1 #0c1424);
            }
        """)

        layout = QVBoxLayout(dlg)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("账号与安全")
        title.setStyleSheet("color: #ddeeff; font-size: 18px; font-weight: 700; letter-spacing: 3px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        _btn_style = """
            QPushButton {{
                background: {bg};
                color: #e0e0f0;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background: {hover}; }}
            QPushButton:pressed {{ background: {pressed}; }}
        """

        # 1. 激活许可证
        btn1 = QPushButton("激活许可证")
        btn1.setStyleSheet(_btn_style.format(bg="#d69e2e", hover="#c59a2e", pressed="#b8860b"))
        btn1.clicked.connect(lambda: (dlg.close(), self._open_activation()))
        layout.addWidget(btn1)

        # 2. 升级会员
        btn2 = QPushButton("升级会员")
        btn2.setStyleSheet(_btn_style.format(bg="#7c3aed", hover="#6d28d9", pressed="#5b21b6"))
        btn2.clicked.connect(lambda: (dlg.close(), self._open_upgrade()))
        layout.addWidget(btn2)

        # 3. 检查更新
        btn3 = QPushButton("检查更新")
        btn3.setStyleSheet(_btn_style.format(bg="#2563eb", hover="#1d4ed8", pressed="#1e40af"))
        btn3.clicked.connect(lambda: (dlg.close(), self._open_update_check()))
        layout.addWidget(btn3)

        # 4. 数据备份
        btn4 = QPushButton("数据备份")
        btn4.setStyleSheet(_btn_style.format(bg="#059669", hover="#047857", pressed="#065f46"))
        btn4.clicked.connect(lambda: self._user_backup(dlg))
        layout.addWidget(btn4)

        dlg.exec_()

    def _get_project_root(self):
        """获取宇宙版项目根目录"""
        import os
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def _get_backup_config(self):
        import os, json
        root = self._get_project_root()
        config_dir = os.path.join(root, "config")
        username = self._membership_info.get("username", "admin")
        config_file = os.path.join(config_dir, f"backup_{username}.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                logger.exception("异常详情")
        return {}

    def _save_backup_config(self, config: dict):
        import os, json
        root = self._get_project_root()
        config_dir = os.path.join(root, "config")
        username = self._membership_info.get("username", "admin")
        config_file = os.path.join(config_dir, f"backup_{username}.json")
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def _verify_backup_password(self, parent=None):
        """验证或首次设置备份密码，返回密码字符串或 None"""
        from PyQt5.QtWidgets import QInputDialog, QLineEdit
        import hashlib
        from datetime import datetime

        config = self._get_backup_config()
        stored_hash = config.get("password_hash", "")

        if not stored_hash:
            pwd, ok = QInputDialog.getText(
                parent or self, "设置备份密码", "首次使用，请设置备份主密码（至少4位）：",
                QLineEdit.Password)
            if not ok or len(pwd) < 4:
                if ok:
                    QMessageBox.warning(parent or self, "错误", "密码至少4位")
                return None
            confirm, ok = QInputDialog.getText(
                parent or self, "确认", "请再次输入备份密码确认：",
                QLineEdit.Password)
            if not ok or pwd != confirm:
                if ok:
                    QMessageBox.warning(parent or self, "错误", "两次密码不一致")
                return None
            self._save_backup_config({
                "password_hash": hashlib.sha256(pwd.encode()).hexdigest(),
                "created_at": datetime.now().isoformat()
            })
            return pwd
        else:
            for _ in range(3):
                pwd, ok = QInputDialog.getText(
                    parent or self, "验证备份密码", "请输入备份主密码：",
                    QLineEdit.Password)
                if not ok:
                    return None
                if hashlib.sha256(pwd.encode()).hexdigest() == stored_hash:
                    return pwd
                QMessageBox.warning(parent or self, "错误", "备份密码错误！")
            return None

    def _user_backup(self, parent=None):
        """加密备份用户数据"""
        import os, zipfile, io, struct, hashlib
        from datetime import datetime
        from PyQt5.QtWidgets import QFileDialog

        root = self._get_project_root()
        username = self._membership_info.get("username", "admin")

        pwd = self._verify_backup_password(parent)
        if not pwd:
            return

        default_dir = os.path.join(root, "backup")
        os.makedirs(default_dir, exist_ok=True)
        default_name = f"user_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.usrbak"
        path, _ = QFileDialog.getSaveFileName(
            parent or self, "备份数据",
            os.path.join(default_dir, default_name),
            "加密备份 (*.usrbak)"
        )
        if not path:
            return

        try:
            user_data_files = [
                "data/member.db", "data/customer.db",
                "data/order.db", "data/product.db",
                "data/finance.db", "data/wallet.db",
                "data/distribution.db", "data/vault.enc",
                "data/notes/",
            ]

            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in user_data_files:
                    full_path = os.path.join(root, f)
                    if os.path.isfile(full_path):
                        zf.write(full_path, f)
                    elif os.path.isdir(full_path):
                        for dr, _, files in os.walk(full_path):
                            for file in files:
                                fp = os.path.join(dr, file)
                                arcname = os.path.relpath(fp, root)
                                zf.write(fp, arcname)
            zip_data = buf.getvalue()

            MAGIC = b"USRBAK_V1\x00"
            salt = os.urandom(16)
            key = hashlib.pbkdf2_hmac("sha256", pwd.encode(), salt, 100000)
            enc = bytes([b ^ key[i % len(key)] for i, b in enumerate(zip_data)])
            data_len = struct.pack(">I", len(enc))

            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(MAGIC + salt + data_len + enc)

            QMessageBox.information(parent or self, "备份成功", f"数据已加密备份至：\n{path}")
        except Exception as e:
            QMessageBox.critical(parent or self, "备份失败", f"备份出错：{e}")

    # ════════════════
        """轨道中心 — 窗口正中央"""
        w = self._hud.width()
        h = self._hud.height()
        return QPointF(w * 0.5, h * 0.52)

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
        for p in self._planets:
            paint_orbit(painter, cx, p["orbit"])

        # ── 星球 ──
        for p in self._planets:
            pp = self._get_planet_pos(p)
            style = PLANET_STYLES.get(p["style"], PLANET_STYLES["neptune"])
            is_hovered = p == self._hovered_planet
            paint_planet(painter, pp, p["radius"], style,
                         hovered=is_hovered, label=p["name"], font_size=11)

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