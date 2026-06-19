# `modules/intelligence/account_window.py`

> 路径：`modules/intelligence/account_window.py` | 行数：434


---


```python
"""
账号与安全 — 小星球导航模式
修改密码 / 升级会员 / 数据备份 / 检查更新 / 退出登录
以环绕星球的宇宙导航呈现，与 BusinessWindow 同架构
"""
import os, math, hashlib, zipfile, io, struct
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QMessageBox,
    QInputDialog, QLineEdit, QFileDialog, QDialog,
)
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QFont, QLinearGradient,
)

from core.cosmic import CosmicBackground

# ═══════ 星球配色 ═══════
PLANET_DATA = {
    "password": {"label": "修改密码",   "color": QColor(0xE5, 0x3E, 0x3E), "orbit": 130, "speed": 1.0, "icon": "P"},
    "upgrade":  {"label": "升级会员",   "color": QColor(0x7C, 0x3A, 0xED), "orbit": 200, "speed": 0.9, "icon": "U"},
    "backup":   {"label": "数据备份",   "color": QColor(0x05, 0x96, 0x69), "orbit": 270, "speed": 0.8, "icon": "B"},
    "update":   {"label": "检查更新",   "color": QColor(0x25, 0x63, 0xEB), "orbit": 340, "speed": 0.7, "icon": "C"},
}

CORE_COLOR = QColor(0xCC, 0x88, 0xFF)


# ═══════ 导航 HUD ═══════
class AccountNavHUD(QWidget):
    """账号安全模块的小星球导航覆盖层"""
    planetClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self._center = QPointF(0, 0)
        self._hovered_key = None
        self._planet_angles = {key: 0.0 for key in PLANET_DATA}
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)

    def _tick(self):
        for key, data in PLANET_DATA.items():
            self._planet_angles[key] += 0.008 * data["speed"]
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._center = QPointF(self.width() / 2, self.height() / 2)

    def _planet_positions(self):
        positions = []
        cx, cy = self._center.x(), self._center.y()
        for key, data in PLANET_DATA.items():
            orbit = data["orbit"]
            angle = math.radians(orbit) + self._planet_angles[key]
            x = cx + orbit * math.cos(angle)
            y = cy + orbit * math.sin(angle)
            positions.append((key, QPointF(x, y)))
        return positions

    # ═══ 绘制 ═══
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy = self._center.x(), self._center.y()

        # ── 核心光球 ──
        for i, r in enumerate([72, 56, 40, 28]):
            alpha = 8 + i * 6
            grad = QRadialGradient(self._center, r)
            grad.setColorAt(0, QColor(CORE_COLOR.red(), CORE_COLOR.green(),
                                       CORE_COLOR.blue(), alpha + 30))
            grad.setColorAt(1, QColor(CORE_COLOR.red(), CORE_COLOR.green(),
                                       CORE_COLOR.blue(), 0))
            p.setBrush(QBrush(grad))
            p.setPen(Qt.NoPen)
            p.drawEllipse(self._center, r, r)

        # 球体
        ball_grad = QRadialGradient(self._center, 22)
        ball_grad.setColorAt(0, QColor(240, 220, 255))
        ball_grad.setColorAt(0.5, CORE_COLOR.lighter(120))
        ball_grad.setColorAt(1, CORE_COLOR.darker(150))
        p.setBrush(QBrush(ball_grad))
        p.drawEllipse(self._center, 22, 22)

        # 光环
        ring_pen = QPen(QColor(CORE_COLOR.red(), CORE_COLOR.green(),
                                CORE_COLOR.blue(), 40))
        ring_pen.setWidth(2)
        p.setPen(ring_pen)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(self._center, 30, 30)

        # ── 轨道 ──
        for data in PLANET_DATA.values():
            orbit = data["orbit"]
            c = data["color"]
            pen = QPen(QColor(c.red(), c.green(), c.blue(), 25))
            pen.setStyle(Qt.DotLine)
            pen.setWidth(1)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(self._center, orbit, orbit)

        # ── 星球 ──
        font = QFont("SF Pro Display", 10, QFont.Bold)
        label_font = QFont("SF Pro Display", 9)
        for key, pos in self._planet_positions():
            data = PLANET_DATA[key]
            is_hover = (self._hovered_key == key)
            r = 26

            # 辉光
            glow_grad = QRadialGradient(pos, r + 10 if is_hover else r + 6)
            c = data["color"]
            glow_grad.setColorAt(0, QColor(c.red(), c.green(), c.blue(), 50 if is_hover else 25))
            glow_grad.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 0))
            p.setBrush(QBrush(glow_grad))
            p.setPen(Qt.NoPen)
            p.drawEllipse(pos, r + 10 if is_hover else r + 6, r + 10 if is_hover else r + 6)

            # hover 高亮环
            if is_hover:
                hl_pen = QPen(QColor(c.red(), c.green(), c.blue(), 160))
                hl_pen.setWidth(2)
                p.setPen(hl_pen)
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(pos, r + 4, r + 4)

            # 球体
            ball = QRadialGradient(pos, r)
            ball.setColorAt(0, c.lighter(160))
            ball.setColorAt(0.6, c)
            ball.setColorAt(1, c.darker(180))
            p.setBrush(QBrush(ball))
            p.setPen(Qt.NoPen)
            p.drawEllipse(pos, r, r)

            # 图标
            p.setFont(font)
            p.setPen(QColor(255, 255, 255, 200))
            p.drawText(QRectF(pos.x() - r, pos.y() - r, r * 2, r * 2),
                        Qt.AlignCenter, data["icon"])

            # 标签
            p.setFont(label_font)
            p.setPen(QColor(200, 200, 220, 180))
            p.drawText(QRectF(pos.x() - 40, pos.y() + r + 4, 80, 18),
                        Qt.AlignHCenter | Qt.AlignTop, data["label"])

        p.end()

    # ═══ 交互 ═══
    def mouseMoveEvent(self, event):
        pos = event.pos()
        self._hovered_key = None
        for key, pt in self._planet_positions():
            r = 30
            dx = pos.x() - pt.x()
            dy = pos.y() - pt.y()
            if dx * dx + dy * dy <= r * r:
                self._hovered_key = key
                self.setCursor(Qt.PointingHandCursor)
                self.update()
                return
        self.setCursor(Qt.ArrowCursor)
        if self._hovered_key is not None:
            self._hovered_key = None
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._hovered_key:
            self.planetClicked.emit(self._hovered_key)


# ═══════ 主窗口 ═══════
class AccountWindow(QMainWindow):
    """账号与安全 — 小星球导航"""

    def __init__(self, parent=None, role="admin", opcclaw_engine=None):
        super().__init__(parent)
        self._role = role
        self._opcclaw_engine = opcclaw_engine
        self.setWindowTitle("一人公司 — 账号与安全")
        self.setMinimumSize(1100, 780)
        self.resize(1100, 780)
        self._build_ui()

    def _build_ui(self):
        # 深空背景直接作为 central widget（不套中间层 QWidget）
        bg = CosmicBackground()
        self.setCentralWidget(bg)

        # HUD 层 — QMainWindow 直接子控件，悬浮在背景之上
        self._hud = AccountNavHUD(self)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        self._hud.planetClicked.connect(self._on_planet_clicked)
        self._hud.raise_()

        # 标题
        title = QLabel("账号与安全", self)
        title.setStyleSheet(
            "color: #ddaaff; font-size: 22px; font-weight: 800;"
            " letter-spacing: 6px; background: transparent;"
        )
        title.setAlignment(Qt.AlignCenter)
        title.setGeometry(0, 18, self.width(), 36)
        self._title = title

        subtitle = QLabel("点击环绕星球进入各功能", self)
        subtitle.setStyleSheet(
            "color: #776699; font-size: 11px; letter-spacing: 2px;"
            " background: transparent;"
        )
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setGeometry(0, 52, self.width(), 18)
        self._subtitle = subtitle

        version = QLabel("v1.0 · ACCOUNT NEXUS", self)
        version.setStyleSheet(
            "color: rgba(150,130,180,60); font-size: 10px; background: transparent;"
        )
        version.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        version.setGeometry(self.width() - 200, self.height() - 28, 190, 20)
        self._version = version

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        if hasattr(self, '_hud'):
            self._hud.setGeometry(0, 0, w, h)
        if hasattr(self, '_title'):
            self._title.setGeometry(0, 18, w, 36)
        if hasattr(self, '_subtitle'):
            self._subtitle.setGeometry(0, 52, w, 18)
        if hasattr(self, '_version'):
            self._version.setGeometry(w - 200, h - 28, 190, 20)

    # ═══ 星球路由 ═══
    def _on_planet_clicked(self, key):
        if key == "password":
            from modules.auth.change_password_dialog import ChangePasswordWindow
            dlg = ChangePasswordWindow(username=self._membership_info.get("username", "admin"), parent=self)
            dlg.exec_()
        elif key == "upgrade":
            self._open_upgrade()
        elif key == "backup":
            self._user_backup()
        elif key == "update":
            from modules.account.account_update import AccountUpdateDialog
            dlg = AccountUpdateDialog(self)
            dlg.exec_()

    # ═══ 升级会员 ═══
    def _open_upgrade(self):
        from modules.auth.upgrade_window import UpgradeWindow
        ms = self._membership_info
        dlg = UpgradeWindow(
            username=ms.get("username", ""),
            role=self._role,
            membership=ms.get("membership", "trial"),
            expire_at=ms.get("expire_at"),
            parent=self,
        )
        dlg.exec_()
        try:
            import sqlite3
            root = self._get_project_root()
            db_path = os.path.join(root, "data", "member.db")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                row = conn.execute(
                    "SELECT username, role, membership, expire_at FROM members WHERE username=?",
                    (ms.get("username", "admin"),)).fetchone()
                if row:
                    self._role = row[1] or "member"
                    self._membership_info_cache = {
                        "username": row[0], "role": row[1],
                        "membership": row[2] or "trial", "expire_at": row[3] or ""
                    }
                conn.close()
        except Exception:
            pass

    # ═══ 数据备份 ═══
    def _user_backup(self):
        root = self._get_project_root()
        username = self._membership_info.get("username", "admin")

        pwd = self._verify_backup_password()
        if not pwd:
            return

        default_dir = os.path.join(root, "backup")
        os.makedirs(default_dir, exist_ok=True)
        default_name = f"user_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.usrbak"
        path, _ = QFileDialog.getSaveFileName(
            self, "备份数据",
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

            QMessageBox.information(self, "备份成功", f"数据已加密备份至：\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "备份失败", f"备份出错：{e}")

    def _verify_backup_password(self):
        config = self._get_backup_config()
        stored_hash = config.get("password_hash", "")

        if not stored_hash:
            pwd, ok = QInputDialog.getText(
                self, "设置备份密码", "首次使用，请设置备份主密码（至少4位）：",
                QLineEdit.Password)
            if not ok or len(pwd) < 4:
                if ok:
                    QMessageBox.warning(self, "错误", "密码至少4位")
                return None
            confirm, ok = QInputDialog.getText(
                self, "确认", "请再次输入备份密码确认：",
                QLineEdit.Password)
            if not ok or pwd != confirm:
                if ok:
                    QMessageBox.warning(self, "错误", "两次密码不一致")
                return None
            self._save_backup_config({
                "password_hash": hashlib.sha256(pwd.encode()).hexdigest(),
                "created_at": datetime.now().isoformat()
            })
            return pwd
        else:
            for _ in range(3):
                pwd, ok = QInputDialog.getText(
                    self, "验证备份密码", "请输入备份主密码：",
                    QLineEdit.Password)
                if not ok:
                    return None
                if hashlib.sha256(pwd.encode()).hexdigest() == stored_hash:
                    return pwd
                QMessageBox.warning(self, "错误", "备份密码错误！")
            return None

    def _get_backup_config(self):
        import json
        root = self._get_project_root()
        config_dir = os.path.join(root, "config")
        username = self._membership_info.get("username", "admin")
        config_file = os.path.join(config_dir, f"backup_{username}.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_backup_config(self, config: dict):
        import json
        root = self._get_project_root()
        config_dir = os.path.join(root, "config")
        username = self._membership_info.get("username", "admin")
        config_file = os.path.join(config_dir, f"backup_{username}.json")
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    # ═══ 工具方法 ═══
    def _get_project_root(self):
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    @property
    def _membership_info(self):
        if hasattr(self, '_membership_info_cache'):
            return self._membership_info_cache
        info = {"username": self._role or "admin", "role": self._role or "admin",
                "membership": "trial", "expire_at": ""}
        try:
            import sqlite3
            root = self._get_project_root()
            db_path = os.path.join(root, "data", "member.db")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                row = conn.execute(
                    "SELECT username, role, membership, expire_at FROM members WHERE username=?",
                    (self._role or "admin",)).fetchone()
                if row:
                    info = {"username": row[0] or "admin", "role": row[1] or "member",
                            "membership": row[2] or "trial", "expire_at": row[3] or ""}
                conn.close()
        except Exception:
            pass
        return info

```
