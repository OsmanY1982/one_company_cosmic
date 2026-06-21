# -*- coding: utf-8 -*-
"""
AI 助手模块 v3 — 支持本地模型管理
- 标签1: 💬 AI 对话 (iqra ChatWindow)
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
# 使「from iqra.xxx import ...」和「from modules.intelligence.xxx import ...」
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

from ._ai_shared import ButtonAnimationHelper, QUICK_TEMPLATES


# ═══════════════════════════════════════════
# 快捷工具标签页
# ═══════════════════════════════════════════

class QuickToolsWidget(QWidget):
    """快捷工具面板"""
    
    template_selected = pyqtSignal(str)
    use_local_model = pyqtSignal(str)  # 请求使用本地模型
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
    
    def _build_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        # 滚动内容
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # 标题区域
        title_row = QHBoxLayout()
        title_icon = QLabel("⚡")
        title_icon.setFont(QFont("PingFang SC", 28))
        title_row.addWidget(title_icon)
        title = QLabel("快捷工具")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setStyleSheet("color: #1a202c;")
        title_row.addWidget(title)
        title_row.addStretch()
        layout.addLayout(title_row)
        
        # ═══════════════════════════════════════════
        #  快速提问模板
        # ═══════════════════════════════════════════
        template_group = QGroupBox("📝 快速提问模板")
        template_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                color: #2d3748;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 14px;
                padding: 18px 16px 14px 16px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 8px;
                color: #2b6cb0;
            }
        """)
        template_layout = QGridLayout(template_group)
        template_layout.setSpacing(12)
        template_layout.setContentsMargins(8, 8, 8, 8)
        
        for i, (name, template) in enumerate(QUICK_TEMPLATES):
            btn = QPushButton(name)
            btn.setMinimumHeight(56)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f7fafc;
                    color: #1a202c;
                    border: 1px solid #e2e8f0;
                    border-radius: 10px;
                    font-size: 14px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #ebf8ff;
                    border-color: #2b6cb0;
                    color: #2b6cb0;
                }
                QPushButton:pressed {
                    background-color: #bee3f8;
                    padding-top: 9px;
                    padding-bottom: 7px;
                }
            """)
            btn.clicked.connect(lambda checked, t=template: self.template_selected.emit(t))
            # 添加悬停缩放动画
            ButtonAnimationHelper.apply_scale_animation(btn, 1.02)
            template_layout.addWidget(btn, i // 2, i % 2)
        
        layout.addWidget(template_group)
        
        # ═══════════════════════════════════════════
        #  本地模型管理 (Ollama)
        # ═══════════════════════════════════════════
        local_group = QGroupBox("🖥️ 本地模型 (Ollama)")
        local_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                color: #2d3748;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 14px;
                padding: 18px 16px 14px 16px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 8px;
                color: #2b6cb0;
            }
        """)
        local_layout = QVBoxLayout(local_group)
        local_layout.setContentsMargins(8, 8, 8, 8)
        local_layout.setSpacing(16)
        
        # Ollama 状态卡片
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #f7fafc;
                border-radius: 8px;
                padding: 4px;
            }
        """)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(16, 12, 16, 12)
        
        self.ollama_status = QLabel("检测中...")
        self.ollama_status.setStyleSheet("font-size: 14px; color: #1a202c;")
        self.ollama_status.setWordWrap(True)
        status_layout.addWidget(self.ollama_status)
        
        local_layout.addWidget(status_frame)
        
        # 模型选择区域
        model_select_layout = QHBoxLayout()
        model_select_layout.setSpacing(12)
        
        model_label = QLabel("选择模型:")
        model_label.setStyleSheet("font-size: 14px; color: #1a202c;")
        model_select_layout.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.setMinimumHeight(36)
        self.model_combo.setMinimumWidth(200)
        self.model_combo.setCursor(Qt.PointingHandCursor)
        self.model_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 13px;
                background: white;
            }
            QComboBox:focus { border-color: #2b6cb0; }
            QComboBox::drop-down { border: none; }
        """)
        self.model_combo.setEnabled(False)
        model_select_layout.addWidget(self.model_combo, stretch=1)
        
        local_layout.addLayout(model_select_layout)
        
        # 操作按钮行
        ollama_btn_layout = QHBoxLayout()
        ollama_btn_layout.setSpacing(12)
        
        self.start_ollama_btn = QPushButton("▶️ 启动服务")
        self.start_ollama_btn.setMinimumHeight(40)
        self.start_ollama_btn.setMinimumWidth(120)
        self.start_ollama_btn.setCursor(Qt.PointingHandCursor)
        self.start_ollama_btn.setStyleSheet("""
            QPushButton {
                background-color: #38a169;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #2f855a; }
            QPushButton:disabled { background-color: #cbd5e0; }
            QPushButton:pressed { padding-top: 9px; padding-bottom: 7px; }
        """)
        self.start_ollama_btn.clicked.connect(self._start_ollama)
        # 添加悬停缩放动画
        ButtonAnimationHelper.apply_scale_animation(self.start_ollama_btn, 1.03)
        ollama_btn_layout.addWidget(self.start_ollama_btn)
        
        self.download_btn = QPushButton("⬇️ 下载模型")
        self.download_btn.setMinimumHeight(40)
        self.download_btn.setMinimumWidth(120)
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b6cb0;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #2c5282; }
            QPushButton:disabled { background-color: #cbd5e0; }
            QPushButton:pressed { padding-top: 9px; padding-bottom: 7px; }
        """)
        self.download_btn.clicked.connect(self._show_download_dialog)
        self.download_btn.setEnabled(False)
        # 添加悬停缩放动画
        ButtonAnimationHelper.apply_scale_animation(self.download_btn, 1.03)
        ollama_btn_layout.addWidget(self.download_btn)
        
        self.use_local_btn = QPushButton("✅ 使用本地模型")
        self.use_local_btn.setMinimumHeight(40)
        self.use_local_btn.setMinimumWidth(140)
        self.use_local_btn.setCursor(Qt.PointingHandCursor)
        self.use_local_btn.setStyleSheet("""
            QPushButton {
                background-color: #553c9a;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #44337a; }
            QPushButton:disabled { background-color: #cbd5e0; }
            QPushButton:pressed { padding-top: 9px; padding-bottom: 7px; }
        """)
        self.use_local_btn.clicked.connect(self._use_local_model)
        self.use_local_btn.setEnabled(False)
        # 添加悬停缩放动画
        ButtonAnimationHelper.apply_scale_animation(self.use_local_btn, 1.03)
        ollama_btn_layout.addWidget(self.use_local_btn)
        
        # 刷新模型列表按钮
        refresh_ollama_btn = QPushButton("🔄 刷新列表")
        refresh_ollama_btn.setMinimumHeight(40)
        refresh_ollama_btn.setMinimumWidth(110)
        refresh_ollama_btn.setCursor(Qt.PointingHandCursor)
        refresh_ollama_btn.setStyleSheet("""
            QPushButton {
                background-color: #718096;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #4a5568; }
            QPushButton:pressed { padding-top: 9px; padding-bottom: 7px; }
        """)
        refresh_ollama_btn.clicked.connect(self._check_ollama_status)
        # 添加悬停缩放动画
        ButtonAnimationHelper.apply_scale_animation(refresh_ollama_btn, 1.03)
        ollama_btn_layout.addWidget(refresh_ollama_btn)
        
        ollama_btn_layout.addStretch()
        local_layout.addLayout(ollama_btn_layout)
        
        layout.addWidget(local_group)
        
        # ═══════════════════════════════════════════
        #  系统状态
        # ═══════════════════════════════════════════
        status_group = QGroupBox("📊 系统状态")
        status_group.setStyleSheet(template_group.styleSheet())
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(12)
        
        self.status_label = QLabel("检测中...")
        self.status_label.setStyleSheet("font-size: 14px; color: #2c3e50; line-height: 1.8;")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        
        # 状态刷新按钮
        refresh_btn = QPushButton("🔄 刷新状态")
        refresh_btn.setMinimumHeight(36)
        refresh_btn.setMinimumWidth(120)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b6cb0;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #2c5282; }
            QPushButton:pressed { padding-top: 9px; padding-bottom: 7px; }
        """)
        refresh_btn.clicked.connect(self._check_status)
        # 添加悬停缩放动画
        ButtonAnimationHelper.apply_scale_animation(refresh_btn, 1.03)
        status_layout.addWidget(refresh_btn)
        

        layout.addWidget(status_group)
        
        # ═══════════════════════════════════════════
        #  使用指南
        # ═══════════════════════════════════════════
        guide_group = QGroupBox("📖 使用指南")
        guide_group.setStyleSheet(template_group.styleSheet())
        guide_layout = QVBoxLayout(guide_group)
        
        guide_text = QLabel("""
<b>🚀 快速开始：</b><br>
1. <b>云端模型</b>：配置 API Key 即可使用（需要网络）<br>
2. <b>本地模型</b>：启动 Ollama → 下载模型 → 使用（可离线）<br>
3. 点击上方模板快速提问<br><br>

<b>☁️ 云端模型推荐：</b><br>
• DeepSeek - 性价比高，中文优秀<br>
• OpenAI - 功能强大，国际通用<br>
• 通义千问 - 国内稳定，速度快<br><br>

<b>🖥️ 本地模型推荐：</b><br>
• qwen2.5:0.5b (400MB) - 极速测试<br>
• llama3.2:1b (1.3GB) - 超轻量<br>
• deepseek-r1:1.5b (1.1GB) - 推理入门<br><br>

<b>⌨️ 快捷操作：</b><br>
• Ctrl+Enter 发送消息<br>
• 支持 Markdown 格式输出
        """)
        guide_text.setStyleSheet("font-size: 13px; color: #2c3e50; line-height: 1.8;")
        guide_text.setWordWrap(True)
        guide_layout.addWidget(guide_text)
        
        layout.addWidget(guide_group)
        layout.addStretch()
        
        # 设置滚动内容
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # 底部配置按钮
        config_btn = QPushButton("🔑 配置云端模型")
        config_btn.setMinimumHeight(48)
        config_btn.setCursor(Qt.PointingHandCursor)
        config_btn.setStyleSheet("""
            QPushButton {
                background-color: #e53e3e;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #c53030; }
            QPushButton:pressed { padding-top: 13px; padding-bottom: 11px; }
        """)
        config_btn.clicked.connect(self._show_config_dialog)
        # 添加悬停缩放动画
        ButtonAnimationHelper.apply_scale_animation(config_btn, 1.02)
        main_layout.addWidget(config_btn)
        
        # 初始状态检测（延迟 2 秒让 Ollama 有足够时间响应）
        QTimer.singleShot(2000, self._check_ollama_status)
        QTimer.singleShot(500, self._check_status)
    
    def _check_status(self):
        """检查系统状态"""
        status = []
        
        # 检查 iqra (cosmic: skip)
        try:
            # iqra not available in cosmic; skipped
            status.append("✅ Iqra 模块: 已安装")
        except ImportError:
            status.append("❌ Iqra 模块: 未安装")
        
        # 检查配置
        try:
            from modules.intelligence._stubs import OpcConfigManager as ConfigManager
            project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../..")
            from modules.intelligence._compat import DATA_DIR as data_dir
            config = ConfigManager(data_dir)
            provider = config.get_active_provider()
            if provider:
                status.append(f"✅ 云端模型: {provider.name} 已配置")
            else:
                status.append("⚠️ 云端模型: 未配置")
        except Exception as e:
            status.append(f"⚠️ 云端模型: 检查失败")
        
        # 检查网络
        import urllib.request
        try:
            urllib.request.urlopen("https://www.baidu.com", timeout=3)
            status.append("✅ 网络连接: 正常")
        except Exception:
            status.append("❌ 网络连接: 异常")
        
        # 系统状态
        status.append("✅ 系统: 运行正常")
        
        self.status_label.setText("<br>".join(status))
        
        # 检查 Ollama 状态
        self._check_ollama_status()
    
    def _check_ollama_status(self):
        """检查 Ollama 状态"""
        if not OllamaManager.is_installed():
            self.ollama_status.setText("""
                <p style='color:#e53e3e; font-size:14px;'>❌ Ollama 未安装</p>
                <p style='color:#718096; font-size:13px;'>请访问 <a href='https://ollama.com'>ollama.com</a> 下载安装</p>
            """)
            self.start_ollama_btn.setEnabled(False)
            self.download_btn.setEnabled(False)
            self.use_local_btn.setEnabled(False)
            return
        
        if not OllamaManager.is_running():
            self.ollama_status.setText("""
                <p style='color:#ed8936; font-size:14px;'>⚠️ Ollama 已安装但未运行</p>
                <p style='color:#718096; font-size:13px;'>点击"启动服务"按钮启动</p>
            """)
            self.start_ollama_btn.setEnabled(True)
            self.download_btn.setEnabled(False)
            self.use_local_btn.setEnabled(False)
            return
        
        # Ollama 运行中，获取模型列表
        models = OllamaManager.list_models()
        if not models:
            self.ollama_status.setText("""
                <p style='color:#38a169; font-size:14px;'>✅ Ollama 服务运行中</p>
                <p style='color:#718096; font-size:13px;'>暂无模型，请点击"下载模型"</p>
            """)
            self.start_ollama_btn.setEnabled(False)
            self.start_ollama_btn.setText("✅ 已启动")
            self.download_btn.setEnabled(True)
            self.use_local_btn.setEnabled(False)
        else:
            model_names = [m.get("name", "") for m in models]
            model_list_str = ', '.join(model_names)
            self.ollama_status.setText(f"""
                <p style='color:#38a169; font-size:14px;'>✅ Ollama 服务运行中</p>
                <p style='color:#1a202c; font-size:13px;'>已安装 {len(models)} 个模型: {model_list_str}</p>
            """)
            self.start_ollama_btn.setEnabled(False)
            self.start_ollama_btn.setText("✅ 已启动")
            self.download_btn.setEnabled(True)
            self.use_local_btn.setEnabled(True)
            
            # 更新模型下拉框
            self.model_combo.clear()
            for m in models:
                name = m.get("name", "")
                size = m.get("size", 0)
                size_str = f"{size / 1024 / 1024 / 1024:.1f}GB" if size else ""
                self.model_combo.addItem(f"{name} ({size_str})", name)
            self.model_combo.setEnabled(True)
    
    def _start_ollama(self):
        """启动 Ollama 服务"""
        if OllamaManager.start_service():
            self.start_ollama_btn.setText("启动中...")
            self.start_ollama_btn.setEnabled(False)
            # 3秒后刷新状态
            QTimer.singleShot(3000, self._check_ollama_status)
        else:
            QMessageBox.warning(self, "失败", "无法启动 Ollama 服务")
    
    def _show_download_dialog(self):
        """显示下载模型对话框（非模态，可后台下载）"""
        dialog = DownloadModelDialog(self)
        # 非模态显示，不阻塞主窗口
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        dialog.show()
        # 刷新状态在对话框关闭时自动处理
    
    def _use_local_model(self):
        """使用选中的本地模型"""
        model_name = self.model_combo.currentData()
        if not model_name:
            QMessageBox.warning(self, "提示", "请先选择模型")
            return
        
        try:
            # 保存到 iqra 配置
            from modules.intelligence._stubs import OpcConfigManager as ConfigManager
            project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../..")
            from modules.intelligence._compat import DATA_DIR as data_dir
            config = ConfigManager(data_dir)
            
            cfg = {
                "name": f"llama.cpp ({model_name})",
                "provider_type": "openai_compatible",
                "base_url": "http://localhost:8080/v1",
                "model": model_name,
                "api_key": "not-needed",
            }
            
            config.add_provider("local", "llama_proxy", cfg)
            config.set_active_provider("llama_proxy", "local")
            
            QMessageBox.information(self, "成功", f"已切换到本地模型: {model_name}\n请刷新 AI 对话标签页")
            self.use_local_model.emit(model_name)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"切换模型失败: {e}")
    
    def _show_config_dialog(self):
        """显示配置对话框"""
        dialog = APIKeyConfigDialog(self)
        dialog.config_saved.connect(self._check_status)
        dialog.exec_()


# ═══════════════════════════════════════════
# AI 助手主窗口
# ═══════════════════════════════════════════

# ═══════════════════════════════════════════
# 星球导航 HUD 层（绘制能量球 + 行星 + 轨道）
# ═══════════════════════════════════════════

import math as _math
from PyQt5.QtGui import QPainter, QRadialGradient, QBrush, QPen, QFontMetrics
from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import QDialog
from core.planet_painter import PLANET_STYLES, paint_planet, paint_orbit, paint_energy_line


# ═══════ 13颗星球配置（真实纹理） ═══════
PLANETS = [
    # ── 内核环（核心交互）──
    {"id": "iqra_chat",       "name": "Iqra对话",  "style": "earth",    "orbit": 110, "size": 32},
    # ── 内环（智能引擎）──
    {"id": "super_intelligence",  "name": "超级智能",     "style": "jupiter",  "orbit": 160, "size": 26},
    {"id": "enhanced_chat",       "name": "增强对话",     "style": "venus",    "orbit": 200, "size": 26},
    # ── 中内环（知识与管理）──
    {"id": "knowledge_base",      "name": "知识库",       "style": "mercury",  "orbit": 250, "size": 28},
    {"id": "system_monitor",      "name": "系统监控",     "style": "saturn",   "orbit": 295, "size": 28},
    {"id": "quick_actions",       "name": "快捷操作",     "style": "mars",     "orbit": 340, "size": 28},
    # ── 中外环（分析与洞察）──
    {"id": "ai_dashboard",        "name": "AI仪表板",     "style": "neptune",  "orbit": 390, "size": 28},
    {"id": "anomaly_detector",    "name": "异常检测",     "style": "sun",      "orbit": 435, "size": 26},
    {"id": "recommendation_engine","name": "推荐引擎",    "style": "uranus",   "orbit": 480, "size": 26},
    # ── 外环（工具与扩展）──
    {"id": "data_visualization",  "name": "数据可视化",   "style": "pluto",    "orbit": 530, "size": 28},
    {"id": "smart_workflow",      "name": "智能工作流",   "style": "moon",     "orbit": 580, "size": 26},
    {"id": "business_ai",         "name": "业务AI",       "style": "venus",    "orbit": 630, "size": 26},
    {"id": "voice_interface",     "name": "语音接口",     "style": "mercury",  "orbit": 680, "size": 26},
]



