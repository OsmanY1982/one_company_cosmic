import logging

logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
"""
iqra 悬浮星球 — 桌面常驻 AI 助理
可拖拽、语音对话（Apple Speech 引擎）、右键菜单导航、双击对话
"""
import sys, os, traceback, math, random
import subprocess
import threading
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QApplication, QMessageBox, QDialog, QVBoxLayout,
    QHBoxLayout, QPushButton, QLineEdit, QTextEdit, QListWidget,
    QFileDialog, QLabel,
)
from PyQt5.QtCore import (
    Qt, QTimer, QPoint, QRect, QSize, QPointF, QRectF,
    QPropertyAnimation, QEasingCurve, pyqtProperty,
)
from PyQt5.QtGui import (
    QPainter, QColor, QMouseEvent, QFont, QRegion,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.planet_painter import PLANET_STYLES
from core.shapes import SHAPE_PLANETS, SHAPE_ALIENS, SHAPE_STARSHIPS, SHAPE_MODES
from .floating_planet_anim_mixin import FloatingPlanetAnimMixin
from .floating_planet_draw_mixin import FloatingPlanetDrawMixin
from .floating_planet_menu_mixin import FloatingPlanetMenuMixin


class FloatingPlanet(FloatingPlanetAnimMixin, FloatingPlanetDrawMixin,
                     FloatingPlanetMenuMixin, QWidget):
    """桌面悬浮星球 — frameless + 圆形遮罩"""

    SLEEP = "sleep"
    WAKING = "waking"
    ACTIVE = "active"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    CONVERSING = "conversing"

    SLEEP_SIZE = 85
    ACTIVE_SIZE = 117

    # ── pyqtProperty ──
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

    def __init__(self, iqra_engine=None,
                 role: str = "admin",
                 membership_info: dict = None,
                 config: dict = None):
        super().__init__()
        self._engine = iqra_engine
        self._role = role or "admin"
        self._membership_info = membership_info or {}
        self._config = config or {}

        self._state = self.SLEEP
        self._current_size = self.SLEEP_SIZE
        self._target_size = self.SLEEP_SIZE
        self._standalone_chat = None
        self._open_windows: dict = {}  # 保持非模态窗口引用防止被 GC 回收
        self._tooltip_text = "经典星球"
        self.TOOLTIP_H = 26
        self._dragging = False
        self._drag_start = QPoint()
        self._anim_t = 0.0
        self._hover = False

        self._hover_scale = 1.0
        self._hover_anim = QPropertyAnimation(self, b"hoverScale")
        self._hover_anim.setDuration(200)
        self._hover_anim.setEasingCurve(QEasingCurve.OutCubic)

        self._click_pulse = 0.0
        self._pulse_anim = QPropertyAnimation(self, b"clickPulse")
        self._pulse_anim.setDuration(350)
        self._pulse_anim.setEasingCurve(QEasingCurve.OutCubic)

        self._scale_multiplier = 1.0

        self._auto_move = True
        self._vx = 0.0
        self._vy = 0.0
        self._gravity = 0.0
        self._bounce_factor = 0.3
        self._drag_pause = False
        self._drag_trail = []
        self._drag_trail_max = 5
        self._wander_timer = 0
        self._next_wander = 120

        self._style = PLANET_STYLES.get("earth", PLANET_STYLES["neptune"])
        self._shape_mode = None
        self._planet_keys = SHAPE_PLANETS.copy()
        self._alien_keys = SHAPE_ALIENS.copy()
        self._starship_keys = SHAPE_STARSHIPS.copy()
        self._current_category = "planet"
        self._current_planet_idx = 0
        self._current_alien_idx = 0
        self._current_starship_idx = 0

        self._aliens = self._spawn_aliens()
        self._mouse_x = 0
        self._mouse_y = 0

        self._all_shape_keys = self._planet_keys + self._alien_keys + self._starship_keys
        self._auto_switch_idx = 0
        self._auto_switch_timer = QTimer(self)
        self._auto_switch_timer.timeout.connect(self._auto_cycle_shape)
        self._auto_switch_timer.start(7000)

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        # self._keep_on_top_timer 已移除：改为 enterEvent 中调用 _smart_raise()
        # 避免持续 raise 导致悬浮球压在其它窗口上面
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._active_popup = None

        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = geom.right() - self.ACTIVE_SIZE - 80
            y = geom.center().y() - self.ACTIVE_SIZE // 2
        else:
            x, y = 1300, 400

        self.setGeometry(x, y, self.ACTIVE_SIZE, self.ACTIVE_SIZE + self.TOOLTIP_H)
        self._apply_circular_mask()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

        self._daemon_cleanup = None
        self._cleanup_done = False

    def _scaled_widget_size(self):
        return max(16, int(self.ACTIVE_SIZE * self._scale_multiplier))

    def _apply_circular_mask(self):
        s = self._scaled_widget_size()
        region = QRegion(0, 0, s, s, QRegion.Ellipse)
        region = region.united(QRegion(0, s, s, self.TOOLTIP_H))
        self.setMask(region)

    # ── 状态切换 ──

    def wake(self):
        if self._state == self.ACTIVE:
            return
        self._state = self.WAKING
        self._target_size = self.ACTIVE_SIZE
        QTimer.singleShot(300, self._on_wake_complete)

    def _on_wake_complete(self):
        if self._state == self.WAKING:
            self._state = self.ACTIVE

    def sleep(self):
        self._state = self.SLEEP
        self._target_size = self.SLEEP_SIZE

    def toggle(self):
        if self._state == self.SLEEP:
            self.wake()
        else:
            self.sleep()
        self._trigger_click_pulse()

    def _trigger_click_pulse(self):
        self._pulse_anim.stop()
        self._click_pulse = 1.0
        self._pulse_anim.setStartValue(1.0)
        self._pulse_anim.setEndValue(0.0)
        self._pulse_anim.start()
        self.update()

    # ── 生命周期 ──

    def showEvent(self, event):
        super().showEvent(event)
        from core.ad_launcher import check_and_prompt_ad
        check_and_prompt_ad(self)

    # ── 鼠标事件 ──

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            s = self._scaled_widget_size()
            cx, cy = s / 2, s / 2
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
            self._dragging = False
            global_pos = event.globalPos()
            QTimer.singleShot(10, lambda gp=global_pos: self._show_context_menu(gp))
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        self._mouse_x = event.pos().x()
        self._mouse_y = event.pos().y()
        if self._dragging and event.buttons() & Qt.LeftButton:
            delta = event.globalPos() - (self.frameGeometry().topLeft() + self._drag_start)
            if delta.manhattanLength() > 5 or self._state == self.ACTIVE:
                self.move(event.globalPos() - self._drag_start)
                now = datetime.now()
                self._drag_trail.append((event.globalPos(), now))
                if len(self._drag_trail) > self._drag_trail_max:
                    self._drag_trail = self._drag_trail[-self._drag_trail_max:]
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._dragging:
            total_delta = event.globalPos() - (self.frameGeometry().topLeft() + self._drag_start)
            self._dragging = False
            self._drag_pause = False
            if self._auto_move and len(self._drag_trail) >= 2:
                p0, t0 = self._drag_trail[0]
                p1, t1 = self._drag_trail[-1]
                dt = (t1 - t0).total_seconds()
                if dt > 0.005:
                    dx = p1.x() - p0.x()
                    dy = p1.y() - p0.y()
                    self._vx = (dx / dt) / 60.0
                    self._vy = (dy / dt) / 60.0
                    max_speed = 18.0
                    speed = math.sqrt(self._vx**2 + self._vy**2)
                    if speed > max_speed:
                        self._vx = self._vx / speed * max_speed
                        self._vy = self._vy / speed * max_speed
            self._drag_trail = []
            if total_delta.manhattanLength() < 5:
                self.toggle()
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self._open_chat()
        event.accept()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self._cycle_shape(1 if delta > 0 else -1)
        event.accept()

    def enterEvent(self, event):
        self._hover = True
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_scale)
        self._hover_anim.setEndValue(1.08)
        self._hover_anim.start()
        self._smart_raise()

    def leaveEvent(self, event):
        self._hover = False
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_scale)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()

    # ── 模块打开 ──

    # ── 第三层子模块 → 第二层大类回退映射 ──
    _SUB_TO_CATEGORY = {
        # 工具箱 → calculator 回退到 ToolsWindow；其余有独立窗口
        "calculator": "tools",
        # 系统管理子模块 → SystemHubWindow
        "system_settings": "system",
        "activation": "system",
        "cloud_sync": "system",
        "cloud_server": "system",
        "system_logs": "system",
        "admin": "system",
        # 数据中心子模块 → DataWindow
        "dashboard": "data",
        "report": "data",
        "bi": "data",
        "chart": "data",
        # 账号与安全 → backup/update 回退到 AccountWindow
        "backup": "account",
        "update": "account",
    }

    def _open_module(self, module_id: str):
        try:
            # ── 第三层子模块：优先精确路由 ──
            if module_id == "upgrade":
                self._open_upgrade()
                return
            elif module_id == "password":
                self._open_change_password()
                return
            elif module_id == "editor":
                from modules.intelligence.editor_window import EditorWindow
                win = EditorWindow()
            elif module_id == "vault":
                from modules.intelligence.vault_window import VaultWindow
                win = VaultWindow()
            elif module_id == "scanner":
                from modules.intelligence.scan_window import ScanWindow
                win = ScanWindow()
            elif module_id == "astronomy_hub":
                from modules.astronomy.hub import AstronomyHubWindow
                win = AstronomyHubWindow()
            elif module_id == "solar_system":
                from modules.astronomy.solar_system.window import SolarSystemWindow
                win = SolarSystemWindow()
            elif module_id == "solar_explorer":
                from modules.astronomy.star_catalog.catalog import StarCatalogWindow
                win = StarCatalogWindow()
            elif module_id == "order":
                from modules.business.order_window import OrderWindow
                win = OrderWindow()
            elif module_id == "product":
                from modules.business.product_window import ProductWindow
                win = ProductWindow()
            elif module_id == "customer":
                from modules.business.customer_window import CustomerWindow
                win = CustomerWindow()
            elif module_id == "finance":
                from modules.business.finance_window import FinanceWindow
                win = FinanceWindow()
            elif module_id == "distribution":
                from modules.personnel.distribution_window import DistributionWindow
                win = DistributionWindow()
            elif module_id == "staff":
                from modules.personnel.staff_window import StaffWindow
                win = StaffWindow()
            elif module_id == "member":
                from modules.personnel.member_window import MemberWindow
                win = MemberWindow()
            elif module_id == "wallet":
                from modules.personnel.wallet_window import WalletWindow
                win = WalletWindow()

            # ── AI 助手子模块精确路由 ──
            elif module_id == "iqra_chat":
                self._open_chat()
                return
            elif module_id == "super_intelligence":
                from ._ai_shared import SUPER_INTELLIGENCE_AVAILABLE
                if SUPER_INTELLIGENCE_AVAILABLE:
                    from ._ai_widgets import SuperIntelligenceWidget
                    dlg = QDialog()
                    dlg.setWindowTitle("超级智能")
                    dlg.setMinimumSize(750, 550)
                    layout = QVBoxLayout(dlg)
                    layout.addWidget(SuperIntelligenceWidget(dlg))
                    self._open_windows[module_id] = dlg
                    dlg.destroyed.connect(lambda mid=module_id: self._open_windows.pop(mid, None))
                    dlg.show()
                else:
                    QMessageBox.information(self, "提示", "超级智能模块未安装，请检查依赖")
                return
            elif module_id == "enhanced_chat":
                try:
                    from modules.intelligence.enhanced_chat import EnhancedChatWidget
                    dlg = QDialog()
                    dlg.setWindowTitle("增强对话")
                    dlg.setMinimumSize(800, 600)
                    layout = QVBoxLayout(dlg)
                    layout.addWidget(EnhancedChatWidget(dlg))
                    self._open_windows[module_id] = dlg
                    dlg.destroyed.connect(lambda mid=module_id: self._open_windows.pop(mid, None))
                    dlg.show()
                except ImportError as e:
                    QMessageBox.warning(self, "错误", f"增强对话模块加载失败: {e}")
                return
            elif module_id == "knowledge_base":
                try:
                    from modules.intelligence.knowledge_base import KnowledgeBase
                    kb = KnowledgeBase()
                    dlg = QDialog()
                    dlg.setWindowTitle("知识库")
                    dlg.setMinimumSize(700, 500)
                    dl = QVBoxLayout(dlg)

                    search_layout = QHBoxLayout()
                    search_input = QLineEdit()
                    search_input.setPlaceholderText("输入查询关键词...")
                    search_btn = QPushButton("搜索")
                    search_layout.addWidget(search_input)
                    search_layout.addWidget(search_btn)
                    dl.addLayout(search_layout)

                    result_area = QTextEdit()
                    result_area.setReadOnly(True)
                    result_area.setStyleSheet("font-family: monospace; font-size: 11px;")
                    dl.addWidget(result_area)

                    dl.addWidget(QLabel("已导入文档:"))
                    doc_list = QListWidget()
                    dl.addWidget(doc_list)

                    btn_layout = QHBoxLayout()
                    import_btn = QPushButton("导入文档")
                    import_text_btn = QPushButton("导入文本")
                    refresh_btn = QPushButton("刷新列表")
                    btn_layout.addWidget(import_btn)
                    btn_layout.addWidget(import_text_btn)
                    btn_layout.addWidget(refresh_btn)
                    btn_layout.addStretch()
                    dl.addLayout(btn_layout)

                    def refresh_docs():
                        doc_list.clear()
                        docs = kb.list_documents()
                        for d in docs:
                            title = d.get("title", d.get("id", "?"))
                            doc_list.addItem(title)

                    def do_search():
                        q = search_input.text().strip()
                        if not q:
                            return
                        res = kb.query(q, top_k=10)
                        result_area.clear()
                        if not res.get("success"):
                            result_area.append(f"查询失败: {res.get('error', '未知错误')}")
                            return
                        sources = res.get("sources", [])
                        if not sources:
                            result_area.append("无匹配结果。")
                            return
                        result_area.append(f"答案: {res.get('answer', 'N/A')}\n{'-'*50}")
                        for s in sources:
                            result_area.append(
                                f"【{s.get('title', '?')}】"
                                f"(相似度: {s.get('score', 0):.2f})\n"
                                f"{s.get('chunk', '')}\n{'-'*50}"
                            )

                    def import_doc():
                        from PyQt5.QtWidgets import QFileDialog as QFD
                        fp, _ = QFD.getOpenFileName(dlg, "选择文档", "", "文本文件 (*.txt *.md *.json *.csv)")
                        if fp:
                            outcome = kb.import_document(fp, title="")
                            result_area.append(f"导入: {outcome}")
                            refresh_docs()

                    def import_txt():
                        from PyQt5.QtWidgets import QFileDialog as QFD
                        fp, _ = QFD.getOpenFileName(dlg, "选择文件", "", "所有文件 (*)")
                        if fp:
                            try:
                                with open(fp, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                outcome = kb.import_text(content, title=os.path.basename(fp))
                                result_area.append(f"导入文本: {outcome}")
                                refresh_docs()
                            except Exception as ex:
                                result_area.append(f"导入失败: {ex}")

                    search_btn.clicked.connect(do_search)
                    import_btn.clicked.connect(import_doc)
                    import_text_btn.clicked.connect(import_txt)
                    refresh_btn.clicked.connect(refresh_docs)
                    refresh_docs()

                    self._open_windows[module_id] = dlg
                    dlg.destroyed.connect(lambda mid=module_id: self._open_windows.pop(mid, None))
                    dlg.show()
                except ImportError as e:
                    QMessageBox.warning(self, "错误", f"知识库模块加载失败: {e}")
                return
            elif module_id == "system_monitor":
                from ._shell_dialogs import SystemMonitorDialog
                dlg = SystemMonitorDialog()
                self._open_windows[module_id] = dlg
                dlg.destroyed.connect(lambda mid=module_id: self._open_windows.pop(mid, None))
                dlg.show()
                return
            elif module_id == "quick_actions":
                try:
                    from modules.intelligence.quick_actions import QuickActionsWidget
                    dlg = QDialog()
                    dlg.setWindowTitle("快捷操作")
                    dlg.setMinimumSize(700, 550)
                    layout = QVBoxLayout(dlg)
                    layout.addWidget(QuickActionsWidget(dlg))
                    self._open_windows[module_id] = dlg
                    dlg.destroyed.connect(lambda mid=module_id: self._open_windows.pop(mid, None))
                    dlg.show()
                except ImportError as e:
                    QMessageBox.warning(self, "错误", f"快捷操作模块加载失败: {e}")
                return
            elif module_id == "anomaly_detector":
                from ._ai_widgets import AnomalyDetectorWidget
                dlg = QDialog()
                dlg.setWindowTitle("异常检测")
                dlg.setMinimumSize(650, 500)
                layout = QVBoxLayout(dlg)
                layout.addWidget(AnomalyDetectorWidget(dlg))
                self._open_windows[module_id] = dlg
                dlg.destroyed.connect(lambda mid=module_id: self._open_windows.pop(mid, None))
                dlg.show()
                return
            elif module_id == "recommendation_engine":
                from ._ai_widgets import RecommendationEngineWidget
                dlg = QDialog()
                dlg.setWindowTitle("推荐引擎")
                dlg.setMinimumSize(650, 500)
                layout = QVBoxLayout(dlg)
                layout.addWidget(RecommendationEngineWidget(dlg))
                self._open_windows[module_id] = dlg
                dlg.destroyed.connect(lambda mid=module_id: self._open_windows.pop(mid, None))
                dlg.show()
                return
            elif module_id == "data_visualization":
                from ._ai_widgets import DataVisualizationWidget
                dlg = QDialog()
                dlg.setWindowTitle("数据可视化")
                dlg.setMinimumSize(650, 500)
                layout = QVBoxLayout(dlg)
                layout.addWidget(DataVisualizationWidget(dlg))
                self._open_windows[module_id] = dlg
                dlg.destroyed.connect(lambda mid=module_id: self._open_windows.pop(mid, None))
                dlg.show()
                return
            elif module_id == "smart_workflow":
                from ._shell_dialogs import SmartWorkflowDialog
                dlg = SmartWorkflowDialog()
                self._open_windows[module_id] = dlg
                dlg.destroyed.connect(lambda mid=module_id: self._open_windows.pop(mid, None))
                dlg.show()
                return
            elif module_id == "business_ai":
                from ._shell_dialogs import BusinessAIDialog
                dlg = BusinessAIDialog()
                self._open_windows[module_id] = dlg
                dlg.destroyed.connect(lambda mid=module_id: self._open_windows.pop(mid, None))
                dlg.show()
                return
            elif module_id == "voice_interface":
                try:
                    from modules.intelligence.voice_interface import VoiceWidget
                    dlg = VoiceWidget()
                    self._open_windows[module_id] = dlg
                    dlg.destroyed.connect(lambda mid=module_id: self._open_windows.pop(mid, None))
                    dlg.show()
                except ImportError as e:
                    QMessageBox.warning(self, "错误", f"语音接口模块加载失败: {e}")
                return

            # ── 工具箱 计算器 ──
            elif module_id == "calculator":
                from modules.intelligence.tools_window import CalcDialog
                dlg = CalcDialog()
                dlg.exec_()
                return

            # ── 数据中心子模块 ──
            elif module_id == "dashboard":
                from modules.dashboard.dashboard_window import DashboardWindow
                win = DashboardWindow()
            elif module_id == "report":
                from modules.data_center.report_window import ReportWindow
                win = ReportWindow()
            elif module_id == "bi":
                from modules.data_center.bi_window import BIWindow
                win = BIWindow()
            elif module_id == "chart":
                from modules.data_center.chart_window import ChartWindow
                win = ChartWindow()

            # ── 系统管理子模块 ──
            elif module_id == "system_settings":
                from modules.system.base_info_window import BaseInfoWindow
                dlg = BaseInfoWindow()
                dlg.exec_()
                return
            elif module_id == "activation":
                from modules.account.account_activation import AccountActivationWindow
                dlg = AccountActivationWindow()
                dlg.exec_()
                return
            elif module_id == "cloud_sync":
                from modules.system.cloud_window import CloudWindow
                dlg = CloudWindow()
                dlg.exec_()
                return
            elif module_id == "cloud_server":
                from modules.system.cloud_server_window import CloudServerWindow
                win = CloudServerWindow()
            elif module_id == "system_logs":
                from modules.system.logs_window import LogsWindow
                dlg = LogsWindow()
                dlg.exec_()
                return
            elif module_id == "admin":
                from modules.admin.admin_window import AdminWindow
                win = AdminWindow()

            # ── 账号与安全子模块 ──
            elif module_id == "backup":
                self._do_backup()
                return
            elif module_id == "update":
                from modules.account.account_update import AccountUpdateDialog
                dlg = AccountUpdateDialog()
                dlg.exec_()
                return

            # ── 回退：子模块 → 大类窗口 ──
            elif module_id in self._SUB_TO_CATEGORY:
                return self._open_module(self._SUB_TO_CATEGORY[module_id])

            # ── 第二层大类 / 第一层独立项 ──
            elif module_id == "business":
                from modules.business.business_window import BusinessWindow
                win = BusinessWindow()
            elif module_id == "personnel":
                from modules.personnel.personnel_window import PersonnelWindow
                win = PersonnelWindow()
            elif module_id == "intelligence":
                from modules.intelligence.intelligence_window import IntelligenceWindow
                win = IntelligenceWindow(role=self._role, iqra_engine=self._engine)
            elif module_id == "data":
                from modules.data_center.data_window import DataWindow
                win = DataWindow()
            elif module_id == "system":
                from modules.system.system_hub_window import SystemHubWindow
                win = SystemHubWindow(role=self._role)
            elif module_id == "account":
                from modules.intelligence.account_window import AccountWindow
                win = AccountWindow(role=self._role, iqra_engine=self._engine)
            elif module_id == "ai_assistant":
                from modules.intelligence.ai_assistant_window import AIAssistantWindow
                win = AIAssistantWindow(iqra_engine=self._engine)
            elif module_id == "tools":
                from modules.intelligence.tools_window import ToolsWindow
                win = ToolsWindow()
            elif module_id == "login":
                from modules.auth.login_window import LoginWindow
                win = LoginWindow()
            elif module_id == "model_settings":
                from modules.auth.model_setup_window import ModelSetupWindow
                dlg = ModelSetupWindow(
                    username=self._membership_info.get("username", ""),
                    role=self._role,
                    membership_info=self._membership_info,
                )
                self._open_windows["model_settings"] = dlg
                dlg.destroyed.connect(lambda: self._open_windows.pop("model_settings", None))
                dlg.show()
                return
            else:
                return
            self._open_windows[module_id] = win
            win.destroyed.connect(lambda mid=module_id: self._open_windows.pop(mid, None))
            win.show()
        except Exception as e:
            print(f"[FloatingPlanet] Failed to open module {module_id}: {e}")
            traceback.print_exc()

    def _open_upgrade(self):
        """升级会员"""
        from modules.auth.upgrade_window import UpgradeWindow
        dlg = UpgradeWindow(
            username=self._membership_info.get("username", ""),
            role=self._role,
            membership=self._membership_info.get("membership", "trial"),
            expire_at=self._membership_info.get("expire_at"),
            parent=None,
        )
        dlg.exec_()

    def _open_change_password(self):
        """修改密码"""
        from modules.auth.change_password_dialog import ChangePasswordWindow
        dlg = ChangePasswordWindow(
            username=self._membership_info.get("username", "admin"),
            parent=None,
        )
        dlg.exec_()

    def _do_backup(self):
        """数据备份 — 从悬浮球直接触发"""
        import io, zipfile, struct, hashlib
        from PyQt5.QtWidgets import QInputDialog, QLineEdit
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        username = self._membership_info.get("username", "admin")

        # ── 验证 / 设置备份密码 ──
        config_dir = os.path.join(root, "config")
        config_file = os.path.join(config_dir, f"backup_{username}.json")
        stored_hash = ""
        if os.path.exists(config_file):
            try:
                import json
                with open(config_file, "r") as f:
                    stored_hash = json.load(f).get("password_hash", "")
            except Exception:
                logger.exception("异常详情")

        pwd = None
        if not stored_hash:
            pwd, ok = QInputDialog.getText(
                self, "设置备份密码", "首次使用，请设置备份主密码（至少4位）：",
                QLineEdit.Password)
            if not ok or len(pwd) < 4:
                if ok:
                    QMessageBox.warning(self, "错误", "密码至少4位")
                return
            confirm, ok = QInputDialog.getText(
                self, "确认", "请再次输入备份密码确认：",
                QLineEdit.Password)
            if not ok or pwd != confirm:
                if ok:
                    QMessageBox.warning(self, "错误", "两次密码不一致")
                return
            os.makedirs(config_dir, exist_ok=True)
            import json
            with open(config_file, "w") as f:
                json.dump({
                    "password_hash": hashlib.sha256(pwd.encode()).hexdigest(),
                    "created_at": datetime.now().isoformat()
                }, f)
        else:
            for _ in range(3):
                pwd, ok = QInputDialog.getText(
                    self, "验证备份密码", "请输入备份主密码：",
                    QLineEdit.Password)
                if not ok:
                    return
                if hashlib.sha256(pwd.encode()).hexdigest() == stored_hash:
                    break
                QMessageBox.warning(self, "错误", "备份密码错误！")
            else:
                return

        # ── 选择保存路径 ──
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

        # ── 打包加密 ──
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

    def _switch_to_shape(self, category: str, key: str):
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
        self._tooltip_text = name
        try:
            print(f"[FloatingPlanet] 切换到形态: {name} ({key})")
        except OSError:
            logger.exception("异常详情")

    # ── AI 对话 ──

    def _open_chat(self):
        self.wake()
        try:
            from modules.intelligence.ai_chat_window import AIChatWindow
            from .session_context import session_ctx
            session_ctx.set_agent_bridge(self._engine)
            if self._standalone_chat is not None:
                try:
                    self._standalone_chat.close()
                except RuntimeError:
                    logger.exception("异常详情")
                self._standalone_chat = None
            self._standalone_chat = AIChatWindow(
                iqra_engine=self._engine,
                embedded=False,
                session_id=session_ctx.current_session_id,
            )
            self._standalone_chat.setAttribute(Qt.WA_DeleteOnClose)
            self._standalone_chat.show()
        except Exception as e:
            print(f"[FloatingPlanet] Failed to open chat: {e}")
            traceback.print_exc()

    # ── 退出 ──

    def _on_exit(self):
        reply = QMessageBox.question(
            self, "退出悬浮球",
            "确定要退出悬浮球吗？\n可从智能中心重新启动。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._do_cleanup()
            self.close()

    def _do_cleanup(self):
        if self._cleanup_done:
            return
        self._cleanup_done = True
        if self._daemon_cleanup:
            self._daemon_cleanup()

    def closeEvent(self, event):
        if hasattr(self, '_keep_on_top_timer') and self._keep_on_top_timer.isActive():
            self._keep_on_top_timer.stop()
        if not event.spontaneous():
            self._do_cleanup()
        else:
            event.ignore()
            return
        super().closeEvent(event)

    def _toggle_auto_move(self):
        self._auto_move = not self._auto_move
        if self._auto_move:
            angle = random.uniform(0, math.pi * 2)
            kick = random.uniform(3.0, 6.0)
            self._vx = math.cos(angle) * kick
            self._vy = math.sin(angle) * kick

    def _set_scale_multiplier(self, value: float):
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            max_by_width = geom.width() * 0.9 / self.ACTIVE_SIZE
            max_by_height = geom.height() * 0.9 / self.ACTIVE_SIZE
            max_scale = min(3.0, max_by_width, max_by_height)
        else:
            max_scale = 3.0
        value = max(0.5, min(value, max_scale))
        if abs(self._scale_multiplier - value) < 0.01:
            return
        old_s = self._scaled_widget_size()
        self._scale_multiplier = value
        s = self._scaled_widget_size()
        circle_cx = self.x() + old_s // 2
        circle_cy = self.y() + old_s // 2
        self.setFixedSize(s, s + self.TOOLTIP_H)
        new_rect = QRect(
            circle_cx - s // 2,
            circle_cy - s // 2,
            s, s + self.TOOLTIP_H
        )
        self.setGeometry(new_rect)
        self._apply_circular_mask()
        self.update()
