# `modules/intelligence/ai_assistant_window.py`

> 路径：`modules/intelligence/ai_assistant_window.py` | 行数：211


---


```python
# -*- coding: utf-8 -*-
"""
AI 助手模块 v3 — 支持本地模型管理
- 标签1: 💬 AI 对话 (opcclaw ChatWindow)
- 标签2: ⚡ 快捷工具 (模板、本地模型、系统状态)
- 标签3~6: 增强功能（智能对话、快捷操作、系统监控、高级功能）

改进:
- 添加 Ollama 本地模型管理（检测、启动、下载、切换）
- 添加多尺寸模型（超小/中等/大模型）
- 增强本地模型使用体验
- 优化界面布局
- 优化导入路径管理，提升模块加载稳定性
"""

import sys
import os
import subprocess
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

# ── 路径管理 ──────────────────────────────────────────────────────────────────
# 确保项目根目录（one_company_desktop）在 sys.path 中，
# 使「from opcclaw.xxx import ...」和「from modules.intelligence.xxx import ...」
# 在所有调用场景下均可正常工作。
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
# ─────────────────────────────────────────────────────────────────────────────

from PyQt5.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QGridLayout, QMessageBox,
    QGroupBox, QComboBox, QDialog, QFormLayout, QCheckBox,
    QProgressBar, QTextEdit, QPlainTextEdit, QApplication,
    QScrollArea, QFrame, QSizePolicy,
)
from PyQt5.QtCore import Qt, QObject, QTimer, QThread, pyqtSignal, QUrl, QPropertyAnimation, QEasingCurve, pyqtProperty, QRect, QParallelAnimationGroup
from PyQt5.QtGui import QFont, QPalette

from modules.intelligence._stubs import app_state

from ._ai_shared import SUPER_INTELLIGENCE_AVAILABLE
from ._navigation_hud import NavigationHUD
from ._shell_dialogs import (
    SystemMonitorDialog, AIDashboardDialog,
    SmartWorkflowDialog, BusinessAIDialog,
)
from ._ai_widgets import (
    SuperIntelligenceWidget, AnomalyDetectorWidget,
    RecommendationEngineWidget, DataVisualizationWidget,
)



# ═══════════════════════════════════════════
# AI 助手主窗口 — 星球导航模式
# ═══════════════════════════════════════════

class AIAssistantWindow(QMainWindow):
    """AI 助手 · CREW — 13颗星球导航模式"""

    def __init__(self, parent=None, opcclaw_engine=None):
        super().__init__(parent)
        self._opcclaw = opcclaw_engine
        self._role = "admin"
        self.setWindowTitle("AI 助手 · CREW")
        self.setMinimumSize(1200, 900)
        self._build_ui()

    def _build_ui(self):
        from core.cosmic import CosmicBackground
        bg = CosmicBackground()
        self.setCentralWidget(bg)

        self._hud = NavigationHUD(self)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        self._hud.planet_clicked = self._on_planet_clicked
        self._hud.raise_()

        header = QWidget(self)
        header.setAttribute(Qt.WA_TranslucentBackground)
        header.setFixedHeight(70)
        header.setGeometry(0, 10, self.width(), 70)

        hl = QVBoxLayout(header)
        hl.setSpacing(2)
        title = QLabel("AI 助手")
        title.setStyleSheet(
            "color: #ddaaff; font-size: 24px; font-weight: 800;"
            "letter-spacing: 8px; background: transparent;"
        )
        title.setAlignment(Qt.AlignCenter)
        hl.addWidget(title)
        subtitle = QLabel("CREW · 12颗智能星球")
        subtitle.setStyleSheet(
            "color: #776699; font-size: 11px; letter-spacing: 3px;"
            "background: transparent;"
        )
        subtitle.setAlignment(Qt.AlignCenter)
        hl.addWidget(subtitle)

        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(170,80,255,50),
                stop:0.5 rgba(200,120,255,120),
                stop:0.7 rgba(170,80,255,50), stop:1 transparent);
            border: none;
        """)
        hl.addWidget(line)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_hud'):
            self._hud.setGeometry(0, 0, self.width(), self.height())

    # ═══════ 行星点击路由 ═══════
    def _on_planet_clicked(self, planet_id):
        if planet_id == "opcclaw_chat":
            dlg = OPCclawChatDialog(self, opcclaw_engine=self._opcclaw)
            dlg.show()
        elif planet_id == "super_intelligence":
            if SUPER_INTELLIGENCE_AVAILABLE:
                dlg = QDialog(self)
                dlg.setWindowTitle("超级智能")
                dlg.setMinimumSize(750, 550)
                layout = QVBoxLayout(dlg)
                layout.addWidget(SuperIntelligenceWidget(dlg))
                dlg.show()
            else:
                QMessageBox.information(self, "提示", "超级智能模块未安装，请检查依赖")
        elif planet_id == "enhanced_chat":
            try:
                from modules.intelligence.enhanced_chat import EnhancedChatWidget
                dlg = EnhancedChatWidget(self)
                dlg.show()
            except ImportError as e:
                QMessageBox.warning(self, "错误", f"增强对话模块加载失败: {e}")
        elif planet_id == "knowledge_base":
            try:
                from modules.intelligence.knowledge_base import KnowledgeBase
                dlg = QDialog(self)
                dlg.setWindowTitle("知识库")
                dlg.setMinimumSize(600, 450)
                kb = KnowledgeBase()
                layout = QVBoxLayout(dlg)
                layout.addWidget(QLabel("知识库管理", dlg))
                dlg.exec_()
            except ImportError as e:
                QMessageBox.warning(self, "错误", f"知识库模块加载失败: {e}")
        elif planet_id == "system_monitor":
            dlg = SystemMonitorDialog(self)
            dlg.show()
        elif planet_id == "quick_actions":
            try:
                from modules.intelligence.quick_actions import QuickActionsWidget
                dlg = QuickActionsWidget(self)
                dlg.show()
            except ImportError as e:
                QMessageBox.warning(self, "错误", f"快捷操作模块加载失败: {e}")
        elif planet_id == "ai_dashboard":
            dlg = AIDashboardDialog(self)
            dlg.show()
        elif planet_id == "anomaly_detector":
            dlg = QDialog(self)
            dlg.setWindowTitle("异常检测")
            dlg.setMinimumSize(650, 500)
            layout = QVBoxLayout(dlg)
            layout.addWidget(AnomalyDetectorWidget(dlg))
            dlg.show()
        elif planet_id == "recommendation_engine":
            dlg = QDialog(self)
            dlg.setWindowTitle("推荐引擎")
            dlg.setMinimumSize(650, 500)
            layout = QVBoxLayout(dlg)
            layout.addWidget(RecommendationEngineWidget(dlg))
            dlg.show()
        elif planet_id == "data_visualization":
            dlg = QDialog(self)
            dlg.setWindowTitle("数据可视化")
            dlg.setMinimumSize(650, 500)
            layout = QVBoxLayout(dlg)
            layout.addWidget(DataVisualizationWidget(dlg))
            dlg.show()
        elif planet_id == "smart_workflow":
            dlg = SmartWorkflowDialog(self)
            dlg.show()
        elif planet_id == "business_ai":
            dlg = BusinessAIDialog(self)
            dlg.show()
        elif planet_id == "voice_interface":
            try:
                from modules.intelligence.voice_interface import VoiceWidget
                dlg = VoiceWidget(self)
                dlg.exec_()
            except ImportError as e:
                QMessageBox.warning(self, "错误", f"语音接口模块加载失败: {e}")

    def closeEvent(self, event):
        try:
            app_state.current_module = "dashboard"
        except Exception as e:
            print(f"[ai_assistant_window] closeEvent 状态切换失败: {e}")
        super().closeEvent(event)




```
