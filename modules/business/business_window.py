"""
业务管理模块 — 小星球导航模式
订单 / 产品 / 客户 / 财务 四大板块，以环绕星球的宇宙导航呈现
"""
import sqlite3
import math
import random
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QHeaderView, QMessageBox, QDialog, QFormLayout, QLineEdit,
    QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, QPropertyAnimation, pyqtProperty, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QLinearGradient, QFont, QPainterPath, QConicalGradient
)

from core.cosmic import CosmicBackground, ACCENT_CYAN, draw_ring, draw_glow_ellipse
from core.data import init_all_dbs, ORDER_DB, PRODUCT_DB, CUSTOMER_DB, FINANCE_DB

ACCENT_BLUE = QColor(68, 136, 255)
ACCENT_GREEN = QColor(0, 204, 170)

# ── 宇宙样式常量 ──
DIALOG_BG = """
    QDialog {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #080e1a, stop:1 #101a2e);
        border: 1px solid rgba(68,136,255,40);
        border-radius: 12px;
    }
"""
TABLE_STYLE = """
    QTableWidget {
        background: rgba(8,14,26,220);
        color: #ccddef;
        border: 1px solid rgba(50,100,170,35);
        border-radius: 8px;
        gridline-color: rgba(40,80,140,30);
        selection-background-color: rgba(68,136,255,60);
    }
    QTableWidget::item {
        padding: 4px 8px;
    }
    QHeaderView::section {
        background: rgba(20,40,80,180);
        color: #88aadd;
        border: 1px solid rgba(50,100,170,30);
        padding: 6px;
        font-weight: bold;
    }
"""
BTN_PRIMARY = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(68,136,255,200), stop:1 rgba(100,160,255,200));
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 20px;
        font-weight: bold;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(80,150,255,230), stop:1 rgba(120,180,255,230));
    }
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(40,100,220,220), stop:1 rgba(60,120,240,220));
    }
"""


# ═══════════════════════════════════════════════════════
#  DAO 函数 — 订单 / 产品 / 客户 / 财务
# ═══════════════════════════════════════════════════════

def _get_conn(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ── 订单 DAO ──
def order_create(customer_name, product_name, quantity, unit_price, total_amount,
                 status="已完成", note="", payment_method=""):
    conn = _get_conn(ORDER_DB)
    c = conn.cursor()
    order_no = "OR" + datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100, 999))
    c.execute("""INSERT INTO orders (order_no, customer_name, product_name, quantity,
        unit_price, total_amount, status, note, payment_method)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (order_no, customer_name, product_name, quantity, unit_price, total_amount,
         status, note, payment_method))
    conn.commit()
    row_id = c.lastrowid
    conn.close()
    return order_no, row_id


def order_update(oid, customer_name, product_name, quantity, unit_price, total_amount,
                 status, note):
    conn = _get_conn(ORDER_DB)
    c = conn.cursor()
    c.execute("""UPDATE orders SET customer_name=?, product_name=?, quantity=?,
        unit_price=?, total_amount=?, status=?, note=? WHERE id=?""",
        (customer_name, product_name, quantity, unit_price, total_amount, status, note, oid))
    conn.commit()
    conn.close()


def order_delete(oid):
    conn = _get_conn(ORDER_DB)
    c = conn.cursor()
    c.execute("DELETE FROM orders WHERE id=?", (oid,))
    conn.commit()
    conn.close()


def order_list(search=""):
    conn = _get_conn(ORDER_DB)
    c = conn.cursor()
    if search:
        c.execute("""SELECT * FROM orders WHERE customer_name LIKE ? OR product_name LIKE ?
            OR order_no LIKE ? ORDER BY created_at DESC""",
            (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        c.execute("SELECT * FROM orders ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return rows


# ── 产品 DAO ──
def product_create(name, category, price, cost, stock, description="", unit="个"):
    conn = _get_conn(PRODUCT_DB)
    c = conn.cursor()
    c.execute("""INSERT INTO product (name, category, price, cost, stock, unit, description)
        VALUES (?,?,?,?,?,?,?)""",
        (name, category, price, cost, stock, unit, description))
    conn.commit()
    conn.close()


def product_update(pid, name, category, price, cost, stock, description):
    conn = _get_conn(PRODUCT_DB)
    c = conn.cursor()
    c.execute("""UPDATE product SET name=?, category=?, price=?, cost=?, stock=?,
        description=? WHERE id=?""",
        (name, category, price, cost, stock, description, pid))
    conn.commit()
    conn.close()


def product_delete(pid):
    conn = _get_conn(PRODUCT_DB)
    c = conn.cursor()
    c.execute("DELETE FROM product WHERE id=?", (pid,))
    conn.commit()
    conn.close()


def product_list(search=""):
    conn = _get_conn(PRODUCT_DB)
    c = conn.cursor()
    if search:
        c.execute("""SELECT * FROM product WHERE name LIKE ? OR category LIKE ?
            ORDER BY id DESC""", (f"%{search}%", f"%{search}%"))
    else:
        c.execute("SELECT * FROM product ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows


# ── 客户 DAO ──
def customer_create(name, company="", phone="", email="", address="", level="普通", note=""):
    conn = _get_conn(CUSTOMER_DB)
    c = conn.cursor()
    c.execute("""INSERT INTO customer (name, company, phone, email, address, level, note)
        VALUES (?,?,?,?,?,?,?)""", (name, company, phone, email, address, level, note))
    conn.commit()
    conn.close()


def customer_update(cid, name, company, phone, email, address, level, note):
    conn = _get_conn(CUSTOMER_DB)
    c = conn.cursor()
    c.execute("""UPDATE customer SET name=?, company=?, phone=?, email=?, address=?,
        level=?, note=? WHERE id=?""",
        (name, company, phone, email, address, level, note, cid))
    conn.commit()
    conn.close()


def customer_delete(cid):
    conn = _get_conn(CUSTOMER_DB)
    c = conn.cursor()
    c.execute("DELETE FROM customer WHERE id=?", (cid,))
    conn.commit()
    conn.close()


def customer_list(search=""):
    conn = _get_conn(CUSTOMER_DB)
    c = conn.cursor()
    if search:
        c.execute("""SELECT * FROM customer WHERE name LIKE ? OR company LIKE ?
            OR phone LIKE ? ORDER BY id DESC""",
            (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        c.execute("SELECT * FROM customer ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows


# ── 财务 DAO ──
def finance_add(ftype, amount, date, description="", order_no="", category=""):
    conn = _get_conn(FINANCE_DB)
    c = conn.cursor()
    c.execute("""INSERT INTO finance (type, amount, date, description, order_no, category)
        VALUES (?,?,?,?,?,?)""", (ftype, amount, date, description, order_no, category))
    conn.commit()
    conn.close()


def finance_list(search="", start_date="", end_date=""):
    conn = _get_conn(FINANCE_DB)
    c = conn.cursor()
    sql = "SELECT * FROM finance WHERE 1=1"
    params = []
    if search:
        sql += " AND (description LIKE ? OR order_no LIKE ? OR category LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if start_date:
        sql += " AND date >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND date <= ?"
        params.append(end_date)
    sql += " ORDER BY date DESC"
    c.execute(sql, params)
    rows = c.fetchall()
    conn.close()
    return rows


# ═══════════════════════════════════════════════════════
#  小星球导航 HUD 层
# ═══════════════════════════════════════════════════════

PLANET_DATA = {
    "order":    {"label": "订单", "color": QColor(0xD2, 0xA0, 0x28), "orbit": 130, "speed": 1.2, "icon": "O"},
    "product":  {"label": "产品", "color": QColor(0x38, 0xA0, 0x50), "orbit": 200, "speed": 0.9, "icon": "P"},
    "customer": {"label": "客户", "color": QColor(0xDC, 0x64, 0x1E), "orbit": 270, "speed": 0.7, "icon": "C"},
    "finance":  {"label": "财务", "color": QColor(0x80, 0x50, 0xD2), "orbit": 340, "speed": 0.6, "icon": "F"},
}

CORE_COLOR = QColor(0x44, 0x88, 0xFF)


class PlanetNavHUD(QWidget):
    """HUD 层 — 绘制核心光球 + 轨道环 + 4颗小星球，带公转动画"""

    planetClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self._planet_angles = {key: 0.0 for key in PLANET_DATA}
        self._hovered = None
        self._planet_positions = {}  # key -> (px, py)

        self.setMouseTracking(True)

        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(40)

    def _tick(self):
        for key, data in PLANET_DATA.items():
            self._planet_angles[key] += 0.008 * data["speed"]
        self.update()

    def _planet_angle(self, planet_key):
        """每个星球按其固定轨道起始角 + 独立公转角度"""
        base_orbit = PLANET_DATA[planet_key]["orbit"]
        return math.radians(base_orbit) + self._planet_angles[planet_key]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        # ── 核心光球 ──
        core_radius = 48
        # 外层辉光（3层）
        for i in range(4, 0, -1):
            alpha = int(40 * (1 - i * 0.22))
            r = core_radius * (1 + i * 0.6)
            g = QRadialGradient(QPointF(cx, cy), r)
            g.setColorAt(0, QColor(CORE_COLOR.red(), CORE_COLOR.green(),
                                   CORE_COLOR.blue(), alpha))
            g.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(g))
            painter.drawEllipse(QPointF(cx, cy), r, r)

        # 核心球体（渐变）
        core_g = QRadialGradient(QPointF(cx - 8, cy - 12), core_radius * 1.3)
        core_g.setColorAt(0, QColor(160, 200, 255))
        core_g.setColorAt(0.35, CORE_COLOR)
        core_g.setColorAt(0.7, QColor(20, 50, 140))
        core_g.setColorAt(1, QColor(5, 15, 50))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(core_g))
        painter.drawEllipse(QPointF(cx, cy), core_radius, core_radius)

        # 核心光环
        ring_g = QRadialGradient(QPointF(cx, cy), core_radius + 6)
        ring_g.setColorAt(0.85, QColor(0, 0, 0, 0))
        ring_g.setColorAt(0.92, QColor(CORE_COLOR.red(), CORE_COLOR.green(),
                                        CORE_COLOR.blue(), 120))
        ring_g.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(ring_g))
        painter.drawEllipse(QPointF(cx, cy), core_radius + 6, core_radius + 6)

        # ── 轨道环 ──
        painter.setPen(Qt.NoPen)
        for key, data in PLANET_DATA.items():
            orbit_r = data["orbit"]
            orbit_color = data["color"]
            # 轨道虚线（用扇形渐变模拟）
            pen = QPen(QColor(orbit_color.red(), orbit_color.green(),
                              orbit_color.blue(), 30), 1, Qt.DotLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), orbit_r, orbit_r)

        # ── 星球 ──
        self._planet_positions.clear()
        font = QFont("Arial", 10, QFont.Bold)
        label_font = QFont("Arial", 9)

        for key, data in PLANET_DATA.items():
            orbit_r = data["orbit"]
            planet_color = data["color"]
            icon_text = data["icon"]
            angle = self._planet_angle(key)
            px = cx + math.cos(angle) * orbit_r
            py = cy + math.sin(angle) * orbit_r
            planet_r = 18

            self._planet_positions[key] = (px, py)

            # 星球辉光
            glow_r = planet_r + 10
            glow = QRadialGradient(QPointF(px, py), glow_r)
            glow.setColorAt(0, QColor(planet_color.red(), planet_color.green(),
                                       planet_color.blue(), 70))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(QPointF(px, py), glow_r, glow_r)

            # 星球球体
            planet_g = QRadialGradient(QPointF(px - 3, py - 5), planet_r * 1.2)
            planet_g.setColorAt(0, QColor(
                min(255, planet_color.red() + 80),
                min(255, planet_color.green() + 80),
                min(255, planet_color.blue() + 80)))
            planet_g.setColorAt(0.5, planet_color)
            planet_g.setColorAt(1, QColor(
                max(0, planet_color.red() - 60),
                max(0, planet_color.green() - 60),
                max(0, planet_color.blue() - 60)))
            painter.setBrush(QBrush(planet_g))
            painter.drawEllipse(QPointF(px, py), planet_r, planet_r)

            # 高亮（hover 时增强辉光）
            if self._hovered == key:
                hover_glow = QRadialGradient(QPointF(px, py), planet_r + 16)
                hover_glow.setColorAt(0, QColor(255, 255, 255, 60))
                hover_glow.setColorAt(1, QColor(0, 0, 0, 0))
                painter.setBrush(QBrush(hover_glow))
                painter.drawEllipse(QPointF(px, py), planet_r + 16, planet_r + 16)

            # 图标文字
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(font)
            painter.drawText(QRectF(px - planet_r, py - planet_r, planet_r * 2, planet_r * 2),
                             Qt.AlignCenter, icon_text)

            # 标签
            label_y = py + planet_r + 14
            painter.setPen(QColor(planet_color.red(), planet_color.green(),
                                  planet_color.blue(), 180))
            painter.setFont(label_font)
            painter.drawText(QRectF(px - 30, label_y, 60, 18),
                             Qt.AlignHCenter | Qt.AlignTop, data["label"])

        painter.end()

    def mouseMoveEvent(self, event):
        mx, my = event.x(), event.y()
        old_hover = self._hovered
        self._hovered = None
        for key, (px, py) in self._planet_positions.items():
            dist = math.hypot(mx - px, my - py)
            if dist <= 30:
                self._hovered = key
                break
        if old_hover != self._hovered:
            self.update()
            if self._hovered:
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        if self._hovered:
            self.planetClicked.emit(self._hovered)
            self._hovered = None
            self.update()


# ═══════════════════════════════════════════════════════
#  BusinessWindow
# ═══════════════════════════════════════════════════════

class BusinessWindow(QMainWindow):
    """业务管理 — 小星球导航模式"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("业务管理 · COSMIC")
        self.resize(900, 680)

        init_all_dbs()

        # 深空背景
        self._bg = CosmicBackground(self)
        self._bg.setGeometry(self.rect())

        # HUD 层
        self._hud = PlanetNavHUD(self)
        self._hud.setGeometry(self.rect())
        self._hud.planetClicked.connect(self._on_planet_clicked)

        # 顶部标题
        title_label = QLabel("业务管理中心", self)
        title_label.setStyleSheet("""
            QLabel {
                color: #aaccff;
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setGeometry(0, 18, self.width(), 36)

        subtitle = QLabel("点击环绕星球进入对应模块", self)
        subtitle.setStyleSheet("""
            QLabel {
                color: rgba(136,170,221,120);
                font-size: 12px;
                background: transparent;
            }
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setGeometry(0, 52, self.width(), 24)

        # 版本号
        version = QLabel("v2.0 · ORBIT MODE", self)
        version.setStyleSheet("""
            QLabel {
                color: rgba(100,140,200,80);
                font-size: 10px;
                background: transparent;
            }
        """)
        version.setAlignment(Qt.AlignRight)
        version.setGeometry(self.width() - 180, self.height() - 30, 170, 20)

        # 子窗口引用
        self._order_win = None
        self._product_win = None
        self._customer_win = None
        self._finance_win = None

    def _on_planet_clicked(self, key):
        if key == "order":
            from modules.business.order_window import OrderWindow
            self._order_win = OrderWindow(self)
            self._order_win.show()
        elif key == "product":
            from modules.business.product_window import ProductWindow
            self._product_win = ProductWindow(self)
            self._product_win.show()
        elif key == "customer":
            from modules.business.customer_window import CustomerWindow
            self._customer_win = CustomerWindow(self)
            self._customer_win.show()
        elif key == "finance":
            from modules.business.finance_window import FinanceWindow
            self._finance_win = FinanceWindow(self)
            self._finance_win.show()
        else:
            label = PLANET_DATA[key]["label"]
            QMessageBox.information(self, "施工中", f"「{label}」模块施工中，小行星正在紧急建造中")

    def resizeEvent(self, event):
        self._bg.setGeometry(self.rect())
        self._hud.setGeometry(self.rect())
        super().resizeEvent(event)