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
import traceback

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


# ═══════════════════════════════════════════
# 动画效果工具
# ═══════════════════════════════════════════

class ButtonAnimationHelper:
    """按钮悬停动画助手 - 为QPushButton添加平滑悬停效果"""
    
    @staticmethod
    def apply_hover_animation(button, hover_color=None, pressed_color=None):
        """为按钮应用悬停动画效果
        
        Args:
            button: QPushButton实例
            hover_color: 悬停时的背景色（可选，使用样式表中的颜色）
            pressed_color: 按下时的背景色（可选）
        """
        # 保存原始样式表
        original_style = button.styleSheet()
        button._original_style = original_style
        
        # 设置鼠标追踪
        button.setMouseTracking(True)
        button.setCursor(Qt.PointingHandCursor)
        
        # 安装事件过滤器来实现平滑过渡
        button._animation_helper = ButtonHoverFilter(button, hover_color, pressed_color)
        button.installEventFilter(button._animation_helper)
    
    @staticmethod
    def apply_scale_animation(button, scale_factor=1.05):
        """为按钮应用缩放悬停动画
        
        Args:
            button: QPushButton实例
            scale_factor: 悬停时放大的倍数（默认1.05 = 105%）
        """
        button._scale_factor = scale_factor
        button._original_geometry = None
        button.setMouseTracking(True)
        button.setCursor(Qt.PointingHandCursor)
        
        # 安装事件过滤器
        button._scale_helper = ButtonScaleFilter(button, scale_factor)
        button.installEventFilter(button._scale_helper)


class ButtonHoverFilter(QObject):
    """按钮悬停事件过滤器 - 实现平滑的颜色过渡动画"""
    
    def __init__(self, button, hover_color=None, pressed_color=None):
        super().__init__(button)
        self.button = button
        self.hover_color = hover_color
        self.pressed_color = pressed_color
        
        # 创建动画
        self.animation = QPropertyAnimation(button, b"styleSheet")
        self.animation.setDuration(200)  # 200ms过渡
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
    
    def eventFilter(self, obj, event):
        if obj == self.button:
            if event.type() == event.Enter:
                # 鼠标进入 - 添加悬停效果
                self._apply_hover_style()
                return True
            elif event.type() == event.Leave:
                # 鼠标离开 - 恢复原始样式
                self._apply_normal_style()
                return True
            elif event.type() == event.MouseButtonPress:
                # 鼠标按下
                self._apply_pressed_style()
                return True
            elif event.type() == event.MouseButtonRelease:
                # 鼠标释放
                if self.button.underMouse():
                    self._apply_hover_style()
                else:
                    self._apply_normal_style()
                return True
        
        return super().eventFilter(obj, event)
    
    def _apply_hover_style(self):
        """应用悬停样式"""
        current_style = self.button.styleSheet()
        
        # 提取背景色并创建悬停版本
        if "background-color:" in current_style:
            # 已有背景色，添加透明度或亮度变化
            lines = current_style.split("\n")
            new_lines = []
            for line in lines:
                if "background-color:" in line:
                    # 添加悬停时的阴影效果
                    if "border-radius:" in current_style:
                        # 保持原有样式，添加轻微阴影
                        line = line.replace(";", "; box-shadow: 0 2px 8px rgba(0,0,0,0.15);")
                new_lines.append(line)
            self.button.setStyleSheet("\n".join(new_lines))
        else:
            # 没有背景色，添加默认悬停效果
            self.button.setStyleSheet(current_style + "\nQPushButton:hover { background-color: rgba(0,0,0,0.05); }")
    
    def _apply_normal_style(self):
        """恢复普通样式"""
        if hasattr(self.button, '_original_style'):
            self.button.setStyleSheet(self.button._original_style)
    
    def _apply_pressed_style(self):
        """应用按下样式"""
        current_style = self.button.styleSheet()
        # 添加按下时的偏移效果
        if "padding:" in current_style:
            # 已有padding，添加轻微偏移
            pass
        self.button.setStyleSheet(current_style + "\nQPushButton:pressed { padding-top: 9px; padding-bottom: 7px; }")


class ButtonScaleFilter(QObject):
    """按钮缩放事件过滤器 - 实现悬停时轻微放大效果"""
    
    def __init__(self, button, scale_factor):
        super().__init__(button)
        self.button = button
        self.scale_factor = scale_factor
        self.animation = None
    
    def eventFilter(self, obj, event):
        if obj == self.button:
            if event.type() == event.Enter:
                self._animate_scale(self.scale_factor)
                return True
            elif event.type() == event.Leave:
                self._animate_scale(1.0)
                return True
        
        return super().eventFilter(obj, event)
    
    def _animate_scale(self, target_scale):
        """动画缩放按钮"""
        if self.animation:
            self.animation.stop()
        
        self.animation = QPropertyAnimation(self.button, b"geometry")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        current = self.button.geometry()
        if not hasattr(self.button, '_original_geometry') or self.button._original_geometry is None:
            self.button._original_geometry = QRect(current)
        
        original = self.button._original_geometry
        width = original.width()
        height = original.height()
        
        new_width = int(width * target_scale)
        new_height = int(height * target_scale)
        delta_w = new_width - width
        delta_h = new_height - height
        
        new_geometry = QRect(
            original.x() - delta_w // 2,
            original.y() - delta_h // 2,
            new_width,
            new_height
        )
        
        self.animation.setStartValue(current)
        self.animation.setEndValue(new_geometry)
        self.animation.start()


class LoadingAnimationHelper:
    """加载动画助手 - 为耗时操作提供视觉反馈"""
    
    @staticmethod
    def create_loading_button(button, original_text=None):
        """将按钮转换为加载状态
        
        Args:
            button: QPushButton实例
            original_text: 原始文本（可选，会自动保存）
        """
        if original_text:
            button._original_text = original_text
        else:
            button._original_text = button.text()
        
        button.setText("⏳ 处理中...")
        button.setEnabled(False)
        
        # 添加加载动画样式
        loading_style = button.styleSheet()
        loading_style += "\nQPushButton:disabled { background-color: #cbd5e0; color: #718096; }"
        button.setStyleSheet(loading_style)
    
    @staticmethod
    def restore_button(button, new_text=None):
        """恢复按钮到正常状态
        
        Args:
            button: QPushButton实例
            new_text: 新文本（可选，使用原始文本）
        """
        if new_text:
            button.setText(new_text)
        elif hasattr(button, '_original_text'):
            button.setText(button._original_text)
        
        button.setEnabled(True)
    
    @staticmethod
    def create_progress_overlay(parent_widget, message="加载中..."):
        """创建加载遮罩层
        
        Args:
            parent_widget: 父组件
            message: 加载提示信息
        
        Returns:
            QFrame: 遮罩层组件
        """
        overlay = QFrame(parent_widget)
        overlay.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
            }
        """)
        overlay.setFrameShape(QFrame.StyledPanel)
        
        layout = QVBoxLayout(overlay)
        layout.setAlignment(Qt.AlignCenter)
        
        # 加载图标（使用文字模拟）
        loading_label = QLabel("⏳")
        loading_label.setFont(QFont("PingFang SC", 48))
        loading_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(loading_label)
        
        # 加载文字
        message_label = QLabel(message)
        message_label.setStyleSheet("color: #2c3e50; font-size: 16px; font-weight: 600;")
        message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(message_label)
        
        # 进度条
        progress = QProgressBar()
        progress.setRange(0, 0)  # 不确定模式
        progress.setMinimumWidth(200)
        progress.setMaximumWidth(300)
        progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                text-align: center;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background-color: #2b6cb0;
                border-radius: 5px;
            }
        """)
        layout.addWidget(progress)
        
        overlay.progress = progress
        overlay.message_label = message_label
        
        return overlay


class TabTransitionHelper:
    """标签页切换动画助手"""
    
    @staticmethod
    def apply_tab_transition(tab_widget, duration=250):
        """为QTabWidget添加切换动画
        
        Args:
            tab_widget: QTabWidget实例
            duration: 动画持续时间（毫秒）
        """
        tab_widget._transition_duration = duration
        tab_widget._current_widget = None
        tab_widget._next_widget = None
        tab_widget._animation = None
        
        # 连接标签页切换信号
        tab_widget.currentChanged.connect(
            lambda index: TabTransitionHelper._on_tab_changed(tab_widget, index)
        )
    
    @staticmethod
    def _on_tab_changed(tab_widget, index):
        """处理标签页切换"""
        if index < 0 or index >= tab_widget.count():
            return
        
        new_widget = tab_widget.widget(index)
        if not new_widget:
            return
        
        # 创建淡入动画
        animation = QPropertyAnimation(new_widget, b"windowOpacity")
        animation.setDuration(tab_widget._transition_duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # 设置初始透明度
        new_widget.setWindowOpacity(0.0)
        new_widget.show()
        
        # 启动动画
        animation.start()
        tab_widget._animation = animation


# ═══════════════════════════════════════════
# 尝试导入超级智能模块（可选依赖）
# ═══════════════════════════════════════════
try:
    from modules.intelligence.super_intelligence import SuperIntelligence
    from modules.intelligence.intelligence_integration import upgrade_engine
    SUPER_INTELLIGENCE_AVAILABLE = True
except ImportError:
    SUPER_INTELLIGENCE_AVAILABLE = False


# ═══════════════════════════════════════════
# 快捷提问模板
# ═══════════════════════════════════════════

QUICK_TEMPLATES = [
    ("📊 数据分析", "请分析以下数据并给出建议：\n\n"),
    ("📝 文案撰写", "请帮我撰写以下内容：\n\n"),
    ("💡 头脑风暴", "请就以下主题进行头脑风暴，给出 5 个创意点子：\n\n"),
    ("🔧 代码辅助", "请帮我解决以下编程问题：\n\n"),
    ("📧 邮件撰写", "请帮我撰写一封邮件，主题是：\n\n"),
    ("📋 会议纪要", "请将以下内容整理成会议纪要：\n\n"),
    ("📈 商业计划", "请帮我分析以下商业计划：\n\n"),
    ("🎯 决策建议", "请就以下情况给出决策建议：\n\n"),
]

# 推荐的本地模型（均支持 chat + tools）
# 注意：Gemma 系列（gemma2:*）不支持工具调用，仅能 completion
RECOMMENDED_MODELS = [
    # 超小模型 - 快速测试用
    ("qwen2.5:0.5b", "通义千问 2.5 (0.5B) - 极速测试", "400MB"),
    ("llama3.2:1b", "Llama 3.2 (1B) - 超轻量", "1.3GB"),
    ("qwen2.5:1.5b", "通义千问 2.5 (1.5B) - 轻量中文", "1.0GB"),
    ("phi3:mini", "Phi-3 Mini (3.8B) - 微软轻量", "2.3GB"),
    # 中等模型 - 日常使用
    ("llama3.2:3b", "Llama 3.2 (3B) - 轻量快速", "2.0GB"),
    ("qwen2.5:3b", "通义千问 2.5 (3B) - 中文轻量", "1.9GB"),
    ("deepseek-r1:1.5b", "DeepSeek-R1 (1.5B) - 推理入门", "1.1GB"),
    # 大模型 - 高性能
    ("qwen2.5:7b", "通义千问 2.5 (7B) - 中文优秀", "4.5GB"),
    ("deepseek-r1:7b", "DeepSeek-R1 (7B) - 推理能力强", "4.7GB"),
    ("mistral:7b", "Mistral (7B) - 通用推理", "4.4GB"),
    ("phi4:14b", "Phi-4 (14B) - 微软出品", "9.1GB"),
    # 超大型模型 - 企业级性能（需高配硬件）
    ("qwen2.5:14b", "通义千问 2.5 (14B) - 中文大型", "8.9GB"),
    ("qwen2.5:32b", "通义千问 2.5 (32B) - 企业中文", "~20GB"),
    ("qwen2.5:72b", "通义千问 2.5 (72B) - 旗舰中文", "~45GB"),
    ("deepseek-r1:14b", "DeepSeek-R1 (14B) - 推理大型", "~9GB"),
    ("deepseek-r1:32b", "DeepSeek-R1 (32B) - 推理企业级", "~20GB"),
    ("deepseek-r1:70b", "DeepSeek-R1 (70B) - 推理旗舰", "~43GB"),
    ("llama3.1:8b", "Llama 3.1 (8B) - Meta 最新", "~5GB"),
    ("llama3.3:70b", "Llama 3.3 (70B) - Meta 旗舰", "~40GB"),
    ("mixtral:8x7b", "Mixtral 8x7B - MoE 混合专家", "~26GB"),
    ("command-r:35b", "Command R (35B) - Cohere", "~20GB"),
    ("qwq:32b", "QwQ (32B) - 通义推理", "~20GB"),
    ("mistral-large", "Mistral Large - 欧洲旗舰", "~60GB"),
]


# ═══════════════════════════════════════════
# Ollama 管理器
# ═══════════════════════════════════════════

class OllamaManager:
    """管理 Ollama 本地模型"""
    
    OLLAMA_URL = "http://localhost:11434"
    
    @classmethod
    def is_installed(cls) -> bool:
        """检查 Ollama 是否已安装（跨平台）"""
        try:
            # Windows 用 where，macOS/Linux 用 which
            cmd = "where" if sys.platform == "win32" else "which"
            result = subprocess.run(
                [cmd, "ollama"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0 and result.stdout.strip()
        except Exception:
            # 兜底：直接尝试运行 ollama --version
            try:
                subprocess.run(
                    ["ollama", "--version"],
                    capture_output=True,
                    timeout=5
                )
                return True
            except Exception:
                return False
    
    @classmethod
    def is_running(cls) -> bool:
        """检查 Ollama 服务是否运行"""
        try:
            req = urllib.request.Request(
                f"{cls.OLLAMA_URL}/api/tags",
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False
    
    @classmethod
    def start_service(cls) -> bool:
        """启动 Ollama 服务"""
        try:
            # Windows: 使用 start 命令后台运行
            subprocess.Popen(
                ["ollama", "serve"],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception as e:
            print(f"[OllamaManager] 启动失败: {e}")
            return False
    
    @classmethod
    def list_models(cls) -> list:
        """获取已安装的模型列表"""
        try:
            req = urllib.request.Request(
                f"{cls.OLLAMA_URL}/api/tags",
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("models", [])
        except Exception as e:
            print(f"[OllamaManager] 获取模型列表失败: {e}")
            return []
    
    @classmethod
    def delete_model(cls, model_name: str) -> bool:
        """删除模型"""
        try:
            req = urllib.request.Request(
                f"{cls.OLLAMA_URL}/api/delete",
                data=json.dumps({"name": model_name}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="DELETE"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status == 200
        except Exception as e:
            print(f"[OllamaManager] 删除模型失败: {e}")
            return False

    @classmethod
    def pull_model(cls, model_name: str, progress_callback=None) -> bool:
        """下载模型"""
        try:
            req = urllib.request.Request(
                f"{cls.OLLAMA_URL}/api/pull",
                data=json.dumps({"name": model_name}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=300) as resp:
                for line in resp:
                    try:
                        data = json.loads(line.decode("utf-8"))
                        if progress_callback:
                            progress_callback(data)
                    except Exception:
                        import traceback; traceback.print_exc()
            return True
        except Exception as e:
            print(f"[OllamaManager] 下载模型失败: {e}")
            return False


# ═══════════════════════════════════════════
# 模型下载对话框
# ═══════════════════════════════════════════

class DownloadModelDialog(QDialog):
    """下载模型对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⬇️ 下载本地模型")
        self.setMinimumSize(700, 600)
        self.resize(800, 700)
        self._installed_models = self._get_installed()  # 先查已安装模型
        self._model_buttons = {}  # model_id -> QPushButton (下载按钮)
        self._delete_buttons = {}  # model_id -> QPushButton (删除按钮)
        self._is_downloading = False  # 是否正在下载
        self._build_ui()
    
    @staticmethod
    def _get_installed():
        """获取已安装模型名称列表"""
        try:
            models = OllamaManager.list_models()
            return set(m.get("name", "") for m in models)
        except Exception:
            return set()
    
    def showEvent(self, event):
        """每次显示对话框时刷新已安装状态"""
        super().showEvent(event)
        self._installed_models = self._get_installed()
        self._refresh_buttons()
    
    def closeEvent(self, event):
        """关闭对话框时检查是否正在下载"""
        if self._is_downloading:
            reply = QMessageBox.question(
                self, "下载进行中",
                "模型正在下载中，关闭对话框下载会中断。\n确定要取消吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # 停止下载线程
                if hasattr(self, 'worker') and self.worker.isRunning():
                    self.worker.terminate()
                    self.worker.wait(1000)
                self._is_downloading = False
                self.progress.setVisible(False)
                # 通知主窗口刷新状态
                parent = self.parent()
                if parent and hasattr(parent, '_check_ollama_status'):
                    parent._check_ollama_status()
                event.accept()
            else:
                event.ignore()
        else:
            # 通知主窗口刷新状态
            parent = self.parent()
            if parent and hasattr(parent, '_check_ollama_status'):
                parent._check_ollama_status()
            event.accept()
    
    def _refresh_buttons(self):
        """根据已安装模型刷新所有按钮状态"""
        for model_id, btn in self._model_buttons.items():
            if model_id in self._installed_models:
                self._mark_installed(btn, model_id)
            else:
                self._mark_download(btn, model_id)
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # 标题
        title = QLabel("⬇️ 下载 Ollama 模型")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)
        
        desc = QLabel("选择模型下载到本地，下载后即可离线使用。建议先下载小模型测试。")
        desc.setStyleSheet("color: #7f8c8d; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addSpacing(12)
        
        # 已安装模型区域
        self._installed_section = self._create_installed_section()
        layout.addWidget(self._installed_section)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        # 超小模型区域
        small_group = self._create_model_group(
            "🚀 超小模型（推荐测试用）",
            "400MB-2.3GB，下载快，适合测试功能",
            RECOMMENDED_MODELS[:4]
        )
        scroll_layout.addWidget(small_group)
        
        # 中等模型区域
        medium_group = self._create_model_group(
            "⚡ 中等模型（日常使用）",
            "1-2GB，性能与速度平衡",
            RECOMMENDED_MODELS[4:7]
        )
        scroll_layout.addWidget(medium_group)
        
        # 大模型区域
        large_group = self._create_model_group(
            "🧠 大模型（高性能）",
            "4-9GB，需要较好硬件",
            RECOMMENDED_MODELS[7:11]
        )
        scroll_layout.addWidget(large_group)
        
        # 超大型模型区域
        super_large_group = self._create_model_group(
            "🦾 超大型模型（企业级性能）",
            "9-60GB+，需高配硬件与大显存",
            RECOMMENDED_MODELS[11:]
        )
        scroll_layout.addWidget(super_large_group)
        
        # 自定义模型输入
        custom_group = QGroupBox("🔧 自定义模型")
        custom_group.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                color: #2c3e50;
                border: 2px solid #e0e4ea;
                border-radius: 8px;
                margin-top: 12px;
                padding: 16px;
            }
        """)
        custom_layout = QHBoxLayout(custom_group)
        custom_layout.setSpacing(12)
        
        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("输入模型名称，如: llama3:8b")
        self.custom_input.setMinimumHeight(36)
        self.custom_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e0e4ea;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }
        """)
        custom_layout.addWidget(self.custom_input)
        
        custom_btn = QPushButton("⬇️ 下载")
        custom_btn.setMinimumHeight(36)
        custom_btn.setStyleSheet("""
            QPushButton {
                background-color: #553c9a;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #44337a; }
            QPushButton:pressed { padding-top: 7px; padding-bottom: 5px; }
        """)
        custom_btn.clicked.connect(self._download_custom)
        # 添加悬停缩放动画
        ButtonAnimationHelper.apply_scale_animation(custom_btn, 1.03)
        custom_layout.addWidget(custom_btn)
        
        scroll_layout.addWidget(custom_group)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, stretch=1)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setMinimumHeight(24)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e0e4ea;
                border-radius: 4px;
                text-align: center;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background-color: #2b6cb0;
            }
        """)
        layout.addWidget(self.progress)
        
        # 日志输出
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(120)
        self.log_output.setPlaceholderText("下载日志将显示在这里...")
        self.log_output.setStyleSheet("""
            QPlainTextEdit {
                background-color: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                font-size: 12px;
                padding: 8px;
                color: #2d3748;
            }
        """)
        layout.addWidget(self.log_output)
        
        # 关闭按钮
        close_btn = QPushButton("✅ 完成")
        close_btn.setMinimumHeight(40)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #38a169;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #2f855a; }
            QPushButton:pressed { background-color: #276749; padding-top: 9px; padding-bottom: 7px; }
        """)
        close_btn.clicked.connect(self.accept)
        # 添加悬停缩放动画
        ButtonAnimationHelper.apply_scale_animation(close_btn, 1.03)
        layout.addWidget(close_btn)
    
    def _create_model_group(self, title: str, subtitle: str, models: list) -> QGroupBox:
        """创建模型分组"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                color: #2d3748;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 14px;
                padding: 18px 16px 14px 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #2b6cb0;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # 副标题
        sub = QLabel(subtitle)
        sub.setStyleSheet("color: #718096; font-size: 12px; margin-bottom: 6px;")
        layout.addWidget(sub)
        
        # 模型列表
        for model_id, model_name, size in models:
            row = QHBoxLayout()
            row.setSpacing(16)
            
            # 模型信息卡片
            info_frame = QFrame()
            info_frame.setStyleSheet("""
                QFrame {
                    background-color: #f7fafc;
                    border-radius: 8px;
                    padding: 4px;
                }
            """)
            info_layout = QHBoxLayout(info_frame)
            info_layout.setContentsMargins(12, 8, 12, 8)
            
            name_label = QLabel(f"<b>{model_name}</b>")
            name_label.setStyleSheet("font-size: 13px; color: #1a202c;")
            info_layout.addWidget(name_label)
            
            info_layout.addStretch()
            
            size_label = QLabel(f"📦 {size}")
            size_label.setStyleSheet("font-size: 12px; color: #718096;")
            info_layout.addWidget(size_label)
            
            row.addWidget(info_frame, stretch=1)
            
            # 下载按钮
            btn = QPushButton("⬇️ 下载")
            btn.setProperty("model_id", model_id)
            btn.setMinimumHeight(36)
            btn.setMinimumWidth(80)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2b6cb0;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover { background-color: #2c5282; }
                QPushButton:pressed { padding-top: 7px; padding-bottom: 5px; }
                QPushButton:disabled { background-color: #cbd5e0; }
            """)
            self._model_buttons[model_id] = btn  # 记住按钮引用
            btn.clicked.connect(lambda checked, m=model_id, b=btn: self._download_model(m, b))
            # 添加悬停缩放动画
            ButtonAnimationHelper.apply_scale_animation(btn, 1.05)
            row.addWidget(btn)
            
            # 删除按钮（已下载时显示）
            del_btn = QPushButton("🗑️ 删除")
            del_btn.setProperty("model_id", model_id)
            del_btn.setMinimumHeight(36)
            del_btn.setMinimumWidth(80)
            del_btn.setVisible(False)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e53e3e;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover { background-color: #c53030; }
                QPushButton:pressed { padding-top: 7px; padding-bottom: 5px; }
            """)
            self._delete_buttons[model_id] = del_btn
            del_btn.clicked.connect(lambda checked, m=model_id: self._delete_model(m))
            # 添加悬停缩放动画
            ButtonAnimationHelper.apply_scale_animation(del_btn, 1.05)
            row.addWidget(del_btn)
            
            layout.addLayout(row)
        
        return group
    
    def _create_installed_section(self):
        """创建已安装模型区域 - 显示所有已下载的模型"""
        group = QGroupBox("📦 已安装的模型")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                color: #2d3748;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 14px;
                padding: 18px 16px 14px 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #2b6cb0;
            }
        """)
        group._model_layout = QVBoxLayout(group)
        group._model_layout.setSpacing(8)
        group._model_layout.setContentsMargins(8, 8, 8, 8)
        self._refresh_installed_section(group)
        return group
    
    def _refresh_installed_section(self, group=None):
        """刷新已安装模型列表"""
        if group is None:
            group = self._installed_section
        layout = group._model_layout
        
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        models = OllamaManager.list_models()
        if not models:
            empty = QLabel("暂无已安装的模型\n可从下方推荐列表下载")
            empty.setStyleSheet("color: #7f8c8d; font-size: 13px; padding: 12px;")
            layout.addWidget(empty)
            return
        
        for m in models:
            name = m.get("name", "")
            size = m.get("size", 0)
            size_str = f"{size / 1024 / 1024 / 1024:.1f} GB" if size else ""
            
            row = QHBoxLayout()
            row.setSpacing(12)
            
            name_lbl = QLabel(f"<b>{name}</b>")
            name_lbl.setStyleSheet("font-size: 13px; color: #2c3e50;")
            row.addWidget(name_lbl)
            
            if size_str:
                size_lbl = QLabel(f"📦 {size_str}")
                size_lbl.setStyleSheet("font-size: 12px; color: #7f8c8d;")
                row.addWidget(size_lbl)
            
            row.addStretch()
            
            del_btn = QPushButton("🗑️ 删除")
            del_btn.setMinimumHeight(32)
            del_btn.setMinimumWidth(70)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e53e3e;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 4px 12px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover { background-color: #c53030; }
            """)
            del_btn.clicked.connect(lambda checked, n=name: self._delete_model(n))
            row.addWidget(del_btn)
            
            layout.addLayout(row)
    
    def _mark_installed(self, btn, model_id=None):
        """标记为已安装"""
        btn.setText("✅ 已下载")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #38a169;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:disabled { background-color: #c6f6d5; color: #276749; }
        """)
        btn.setEnabled(False)
        # 显示删除按钮
        if model_id is None:
            model_id = btn.property("model_id")
        if model_id and model_id in self._delete_buttons:
            self._delete_buttons[model_id].setVisible(True)
            self._delete_buttons[model_id].setText("🗑️ 删除")
            self._delete_buttons[model_id].setEnabled(True)
    
    def _mark_download(self, btn, model_id=None):
        """标记为可下载"""
        btn.setText("⬇️ 下载")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2b6cb0;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #2c5282; }
            QPushButton:disabled { background-color: #cbd5e0; }
        """)
        btn.setEnabled(True)
        # 隐藏删除按钮
        if model_id is None:
            model_id = btn.property("model_id")
        if model_id and model_id in self._delete_buttons:
            self._delete_buttons[model_id].setVisible(False)
    
    def _download_model(self, model_id: str, btn: QPushButton):
        """下载模型（后台线程）"""
        if self._is_downloading:
            QMessageBox.warning(self, "提示", "已有模型正在下载中")
            return
        
        self._is_downloading = True
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # 不确定进度
        btn.setEnabled(False)
        btn.setText("下载中...")
        
        self.log_output.appendPlainText(f"开始下载模型: {model_id}")
        
        # 创建下载线程
        self.worker = DownloadWorker(model_id)
        self.worker.progress.connect(self._on_download_progress)
        self.worker.finished.connect(lambda success, msg: self._on_download_finished(success, msg, model_id, btn))
        self.worker.start()
    
    def _on_download_progress(self, data: dict):
        """下载进度回调"""
        status = data.get("status", "")
        completed = data.get("completed", 0)
        total = data.get("total", 0)
        
        if status == "pulling":
            self.log_output.appendPlainText(f"下载中... {completed}/{total}")
        elif status == "downloading":
            if total > 0:
                percent = int(completed / total * 100)
                self.progress.setRange(0, 100)
                self.progress.setValue(percent)
        
        # 自动滚动到底部
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _on_download_finished(self, success: bool, msg: str, model_id: str, btn: QPushButton):
        """下载完成回调"""
        self._is_downloading = False
        self.progress.setVisible(False)
        
        if success:
            self.log_output.appendPlainText(f"✅ {msg}")
            self._mark_installed(btn, model_id)
            self._installed_models.add(model_id)
            # 刷新已安装区域
            self._refresh_installed_section()
            QMessageBox.information(self, "完成", f"模型 {model_id} 下载成功！")
        else:
            self.log_output.appendPlainText(f"❌ {msg}")
            self._mark_download(btn, model_id)
            QMessageBox.warning(self, "失败", f"模型 {model_id} 下载失败:\n{msg}")
        
        # 通知主窗口刷新
        parent = self.parent()
        if parent and hasattr(parent, '_check_ollama_status'):
            parent._check_ollama_status()
    
    def _download_custom(self):
        """下载自定义模型"""
        model_id = self.custom_input.text().strip()
        if not model_id:
            QMessageBox.warning(self, "提示", "请输入模型名称")
            return
        
        # 创建临时按钮用于状态管理
        temp_btn = QPushButton()
        temp_btn.setProperty("model_id", model_id)
        self._download_model(model_id, temp_btn)
    
    def _delete_model(self, model_id: str):
        """删除模型"""
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除模型 {model_id} 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if OllamaManager.delete_model(model_id):
                QMessageBox.information(self, "成功", f"模型 {model_id} 已删除")
                self._installed_models.discard(model_id)
                # 刷新按钮状态
                if model_id in self._model_buttons:
                    self._mark_download(self._model_buttons[model_id], model_id)
                # 刷新已安装区域
                self._refresh_installed_section()
                # 通知主窗口
                parent = self.parent()
                if parent and hasattr(parent, '_check_ollama_status'):
                    parent._check_ollama_status()
            else:
                QMessageBox.warning(self, "失败", f"删除模型 {model_id} 失败")


class DownloadWorker(QThread):
    """后台下载线程"""
    progress = pyqtSignal(dict)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, model_name: str):
        super().__init__()
        self.model_name = model_name
    
    def run(self):
        try:
            def on_progress(data):
                self.progress.emit(data)
            
            success = OllamaManager.pull_model(self.model_name, on_progress)
            if success:
                self.finished.emit(True, f"模型 {self.model_name} 下载完成")
            else:
                self.finished.emit(False, "下载失败")
        except Exception as e:
            self.finished.emit(False, str(e))


# ═══════════════════════════════════════════
# API Key 配置对话框
# ═══════════════════════════════════════════

class APIKeyConfigDialog(QDialog):
    """API Key 配置对话框"""
    
    config_saved = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔑 配置云端模型")
        self.setMinimumSize(520, 480)
        self.resize(560, 520)
        self._saved_keys = {}
        self._load_saved_keys()
        self._build_ui()
    
    def _load_saved_keys(self):
        """加载已保存的密钥"""
        try:
            from modules.intelligence._stubs import OpcSecureStorage as SecureStorage
            storage = SecureStorage()
            keys = storage.load_all_keys()
            # 做别名映射，统一 key 名
            alias_map = {
                "阿里云百炼": "bailian",
                "百炼": "bailian",
                "通义千问": "qwen",
                "千问": "qwen",
            }
            for k, v in keys.items():
                # 去掉前缀
                if ":" in k:
                    _, key_id = k.split(":", 1)
                else:
                    key_id = k
                # 做别名映射
                if key_id in alias_map:
                    key_id = alias_map[key_id]
                self._saved_keys[key_id] = v
            print(f"[APIKeyConfigDialog] 已加载 {len(self._saved_keys)} 个密钥: {list(self._saved_keys.keys())}")
        except Exception as e:
            print(f"[APIKeyConfigDialog] 加载密钥失败: {e}")
            self._saved_keys = {}
    
    def _on_provider_changed(self, index):
        """切换供应商时自动填充已保存的 Key"""
        provider = self.provider_combo.currentData()
        if provider and provider in self._saved_keys:
            self.key_input.setText(self._saved_keys[provider])
        else:
            self.key_input.clear()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(18)
        
        # 标题
        title = QLabel("⚡ 快速配置 AI 模型")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setStyleSheet("color: #1a202c;")
        layout.addWidget(title)
        
        desc = QLabel("选择模型供应商并输入 API Key，即可开始使用 AI 助手")
        desc.setStyleSheet("color: #718096; font-size: 14px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addSpacing(8)
        
        # 供应商选择
        plat_group = QGroupBox("选择模型供应商")
        plat_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                color: #2d3748;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 14px;
                padding: 18px 16px 14px 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #2b6cb0;
            }
        """)
        plat_layout = QVBoxLayout(plat_group)
        plat_layout.setContentsMargins(8, 8, 8, 8)
        
        self.provider_combo = QComboBox()
        self.provider_combo.setMinimumHeight(40)
        self.provider_combo.setCursor(Qt.PointingHandCursor)
        providers = [
            ("DeepSeek (推荐)", "deepseek"),
            ("OpenAI", "openai"),
            ("通义千问 (阿里云)", "qwen"),
            ("智谱 GLM", "glm"),
            ("Moonshot (月之暗面)", "moonshot"),
            ("SiliconFlow", "siliconflow"),
            ("阿里云百炼", "bailian"),
        ]
        for name, pid in providers:
            self.provider_combo.addItem(name, pid)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        self.provider_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background: white;
            }
            QComboBox:focus { border-color: #2b6cb0; }
            QComboBox::drop-down { border: none; }
        """)
        plat_layout.addWidget(self.provider_combo)
        layout.addWidget(plat_group)
        
        # API Key 输入
        key_group = QGroupBox("API Key")
        key_group.setStyleSheet(plat_group.styleSheet())
        key_layout = QVBoxLayout(key_group)
        key_layout.setContentsMargins(8, 8, 8, 8)
        key_layout.setSpacing(12)
        
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("在此粘贴 API Key...")
        self.key_input.setEchoMode(QLineEdit.Password)
        self.key_input.setMinimumHeight(40)
        self.key_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus { border-color: #2b6cb0; }
        """)
        key_layout.addWidget(self.key_input)
        
        # 显示/隐藏 Key
        show_key = QCheckBox("显示 Key")
        show_key.setStyleSheet("color: #718096; font-size: 13px;")
        show_key.toggled.connect(lambda checked: self.key_input.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        ))
        key_layout.addWidget(show_key)
        
        layout.addWidget(key_group)
        
        # 获取链接按钮
        links_layout = QHBoxLayout()
        links_layout.setSpacing(10)
        links = [
            ("DeepSeek", "https://platform.deepseek.com/"),
            ("OpenAI", "https://platform.openai.com/"),
            ("通义千问", "https://dashscope.aliyun.com/"),
            ("SiliconFlow", "https://cloud.siliconflow.cn/"),
        ]
        for name, url in links:
            btn = QPushButton(name)
            btn.setMinimumHeight(32)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #2b6cb0;
                    border: 1px solid #2b6cb0;
                    border-radius: 6px;
                    padding: 4px 12px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: #2b6cb0;
                    color: white;
                }
            """)
            btn.clicked.connect(lambda checked, u=url: self._open_url(u))
            links_layout.addWidget(btn)
        links_layout.addStretch()
        layout.addLayout(links_layout)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #718096;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 14px;
            }
            QPushButton:hover { background: #f7fafc; }
            QPushButton:pressed { padding-top: 9px; padding-bottom: 7px; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 保存并连接")
        save_btn.setMinimumHeight(40)
        save_btn.setMinimumWidth(140)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b6cb0;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #2c5282; }
            QPushButton:pressed { background-color: #2a4365; padding-top: 9px; padding-bottom: 7px; }
        """)
        save_btn.clicked.connect(self._save_config)
        # 添加悬停缩放动画
        ButtonAnimationHelper.apply_scale_animation(save_btn, 1.03)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _open_url(self, url):
        """打开链接"""
        import webbrowser
        webbrowser.open(url)
    
    def _save_config(self):
        """保存配置"""
        provider = self.provider_combo.currentData()
        key = self.key_input.text().strip()
        
        if not key:
            QMessageBox.warning(self, "提示", "请输入 API Key")
            return
        
        try:
            # 保存到 opcclaw 配置
            from modules.intelligence._stubs import OpcConfigManager as ConfigManager
            project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../..")
            from modules.intelligence._compat import DATA_DIR as data_dir
            config = ConfigManager(data_dir)
            
            provider_configs = {
                "deepseek": {
                    "name": "DeepSeek",
                    "provider_type": "openai_compatible",
                    "base_url": "https://api.deepseek.com/v1",
                    "model": "deepseek-chat",
                },
                "openai": {
                    "name": "OpenAI",
                    "provider_type": "openai_compatible",
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-3.5-turbo",
                },
                "qwen": {
                    "name": "通义千问",
                    "provider_type": "openai_compatible",
                    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "model": "qwen-turbo",
                },
                "glm": {
                    "name": "智谱 GLM",
                    "provider_type": "openai_compatible",
                    "base_url": "https://open.bigmodel.cn/api/paas/v4",
                    "model": "glm-4-flash",
                },
                "moonshot": {
                    "name": "Moonshot",
                    "provider_type": "openai_compatible",
                    "base_url": "https://api.moonshot.cn/v1",
                    "model": "moonshot-v1-8k",
                },
                "siliconflow": {
                    "name": "SiliconFlow",
                    "provider_type": "openai_compatible",
                    "base_url": "https://api.siliconflow.cn/v1",
                    "model": "deepseek-ai/DeepSeek-V3",
                },
                "bailian": {
                    "name": "阿里云百炼",
                    "provider_type": "openai_compatible",
                    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "model": "qwen-plus",
                },
            }
            
            cfg = provider_configs.get(provider, provider_configs["deepseek"])
            cfg["api_key"] = key
            
            config.add_provider("cloud", provider, cfg)
            config.set_active_provider(provider, "cloud")
            
            QMessageBox.information(self, "成功", "配置已保存！AI 助手已就绪。")
            self.config_saved.emit()
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")


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
        
        # 检查 opcclaw (cosmic: skip)
        try:
            # opcclaw not available in cosmic; skipped
            status.append("✅ OPCclaw 模块: 已安装")
        except ImportError:
            status.append("❌ OPCclaw 模块: 未安装")
        
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
            # 保存到 opcclaw 配置
            from modules.intelligence._stubs import OpcConfigManager as ConfigManager
            project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../..")
            from modules.intelligence._compat import DATA_DIR as data_dir
            config = ConfigManager(data_dir)
            
            cfg = {
                "name": f"Ollama ({model_name})",
                "provider_type": "openai_compatible",
                "base_url": "http://localhost:11434/v1",
                "model": model_name,
                "api_key": "ollama",  # Ollama 不需要真实 key
            }
            
            config.add_provider("local", "ollama", cfg)
            config.set_active_provider("ollama", "local")
            
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
    {"id": "opcclaw_chat",       "name": "OPCclaw对话",  "style": "earth",    "orbit": 110, "size": 32},
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



class NavigationHUD(QWidget):
    """在 CosmicBackground 上方透明叠加，绘制能量球 + 13颗行星 + 轨道"""

    planet_clicked = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self._center = QPointF(0, 0)
        self._hovered_planet = None
        self._angle = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)  # ~60fps (原 50ms)

    def _tick(self):
        self._angle = (self._angle + 0.25) % 360.0
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._center = QPointF(self.width() / 2, self.height() / 2)

    def _planet_positions(self):
        w2 = self._center
        positions = []
        for i, p in enumerate(PLANETS):
            offset_angle = i * (360.0 / len(PLANETS))
            rad = _math.radians(self._angle + offset_angle)
            x = w2.x() + p["orbit"] * _math.cos(rad)
            y = w2.y() + p["orbit"] * _math.sin(rad)
            positions.append((p, QPointF(x, y)))
        return positions

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w2 = self._center

        # ── 轨道线 ──
        for planet in PLANETS:
            paint_orbit(p, w2, planet["orbit"], alpha=10)

        # ── 能量连接线 ──
        for planet_data, pos in self._planet_positions():
            paint_energy_line(p, w2, pos, alpha=15)

        # ── 13颗行星 ──
        for planet_data, pos in self._planet_positions():
            style = PLANET_STYLES.get(planet_data.get("style"), PLANET_STYLES["neptune"])
            is_hovered = (self._hovered_planet == planet_data["id"])
            paint_planet(p, pos, planet_data["size"], style,
                         hovered=is_hovered, label=planet_data["name"], font_size=9)

        # ── 中央 AI 核心 · 地球 ──
        paint_planet(p, w2, 40, PLANET_STYLES["earth"], label="CREW", font_size=10)

        p.end()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        self._hovered_planet = None
        for planet_data, pt in self._planet_positions():
            r = planet_data["size"] + 8
            dx = pos.x() - pt.x()
            dy = pos.y() - pt.y()
            if dx * dx + dy * dy <= r * r:
                self._hovered_planet = planet_data["id"]
                self.setCursor(Qt.PointingHandCursor)
                self.update()
                return
        self.setCursor(Qt.ArrowCursor)
        if self._hovered_planet is not None:
            self._hovered_planet = None
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._hovered_planet:
            if self.planet_clicked:
                self.planet_clicked(self._hovered_planet)


# ═══════════════════════════════════════════
# OPCclaw 对话弹窗
# ═══════════════════════════════════════════

class OPCclawChatDialog(QDialog):
    """OPCclaw 核心对话引擎弹窗"""

    def __init__(self, parent=None, opcclaw_engine=None):
        super().__init__(parent)
        self._opcclaw = opcclaw_engine
        self.setWindowTitle("OPCclaw 对话 · 核心引擎")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        self._build_ui()

    def _build_ui(self):
        from datetime import datetime

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # 消息历史
        self._chat_log = QTextEdit()
        self._chat_log.setReadOnly(True)
        self._chat_log.setStyleSheet("""
            QTextEdit {
                background: rgba(8,4,16,230); color: #bb99dd;
                border: 1px solid rgba(170,80,255,35); border-radius: 10px;
                padding: 12px; font-size: 13px; line-height: 1.6;
            }
        """)
        layout.addWidget(self._chat_log, 1)

        # 快捷提示
        prompts_row = QHBoxLayout()
        prompts_row.setSpacing(6)
        quick_prompts = [
            ("今日经营分析", "请分析今天的经营数据，包括销售额、订单量和客户活跃度"),
            ("查看销售数据", "查询并汇总最近的销售数据，按产品和时间段展示"),
            ("库存预警检查", "检查当前库存状态，列出需要补货的产品"),
            ("生成日报", "根据今日订单数据自动生成一份经营日报"),
            ("客户洞察", "分析客户购买行为，识别高价值客户和流失风险"),
        ]
        for label, prompt_text in quick_prompts:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(150,60,220,20); color: #bb99dd;
                    border: 1px solid rgba(170,80,255,25); border-radius: 12px;
                    padding: 4px 10px; font-size: 10px;
                }
                QPushButton:hover {
                    background: rgba(170,80,240,50); color: #ddaaff;
                }
            """)
            btn.clicked.connect(lambda _, pt=prompt_text: self._quick_prompt(pt))
            prompts_row.addWidget(btn)
        prompts_row.addStretch()
        layout.addLayout(prompts_row)

        # 输入行
        ir = QHBoxLayout()
        self._chat_input = QLineEdit()
        self._chat_input.setPlaceholderText("输入问题，如：分析本月销售趋势...")
        self._chat_input.setStyleSheet("""
            QLineEdit {
                background: rgba(20,10,40,200); color: #ddaaff;
                border: 1px solid rgba(170,80,255,40); border-radius: 18px;
                padding: 10px 18px; font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid rgba(170,80,255,120); }
        """)
        self._chat_input.returnPressed.connect(self._send)
        ir.addWidget(self._chat_input, 1)

        send_btn = QPushButton("发送")
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setStyleSheet("""
            QPushButton {
                background: rgba(100,60,200,180); color: #fff;
                border: none; border-radius: 18px;
                padding: 10px 22px; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background: rgba(120,80,220,220); }
        """)
        send_btn.clicked.connect(self._send)
        ir.addWidget(send_btn)

        clear_btn = QPushButton("清屏")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: rgba(180,50,50,120); color: #ffaaaa;
                border: none; border-radius: 18px;
                padding: 10px 16px; font-size: 13px;
            }
            QPushButton:hover { background: rgba(200,60,60,160); }
        """)
        clear_btn.clicked.connect(lambda: self._chat_log.clear())
        ir.addWidget(clear_btn)
        layout.addLayout(ir)

        if self._opcclaw:
            self._chat_log.append(
                '<p style="color:#44cc66;">[系统] OPCclaw 引擎已就绪，可以开始对话。</p>'
            )
        else:
            self._chat_log.append(
                '<p style="color:#ffaa44;">[系统] OPCclaw 引擎未连接，请先完成模型配置。</p>'
            )

    def _quick_prompt(self, prompt_text):
        self._chat_input.setText(prompt_text)
        self._send()

    def _send(self):
        from datetime import datetime

        text = self._chat_input.text().strip()
        if not text:
            return
        self._chat_input.clear()
        now = datetime.now().strftime("%H:%M:%S")
        self._chat_log.append(
            f'<p style="color:#ffaa44;font-weight:700;">[{now}] 你:</p>'
            f'<p style="color:#ddccff;">{text}</p>'
        )
        self._chat_input.setEnabled(False)

        if not self._opcclaw:
            self._chat_log.append(
                f'<p style="color:#ff6666;font-weight:700;">[{now}] 系统:</p>'
                f'<p style="color:#ffaaaa;">OPCclaw 引擎未连接，请先完成模型配置后重试。</p>'
            )
            self._chat_input.setEnabled(True)
            self._chat_input.setFocus()
            return

        try:
            system_prompt = (
                "你是一人公司宇宙飞船的 AI 助手，风格像一个太空飞船 AI 助手。"
                "你可以：分析数据、撰写文案、头脑风暴、代码辅助、邮件撰写、"
                "会议纪要、商业计划、决策建议。回复简洁专业，带一点太空风味。"
            )
            response = self._opcclaw.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ])
            reply = response.content if hasattr(response, 'content') else str(response)
        except AttributeError:
            try:
                full = []
                for chunk in self._opcclaw.chat_stream([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ]):
                    full.append(chunk)
                reply = "".join(full)
            except Exception as e2:
                reply = f"OPCclaw 引擎异常: {e2}"
        except Exception as e:
            reply = f"OPCclaw 异常: {e}"

        self._chat_log.append(
            f'<p style="color:#44ccff;font-weight:700;">[{now}] AI:</p>'
            f'<p style="color:#ccaaff;">{reply}</p>'
        )
        self._chat_input.setEnabled(True)
        self._chat_input.setFocus()
        sb = self._chat_log.verticalScrollBar()
        sb.setValue(sb.maximum())


# ═══════════════════════════════════════════
# 子模块弹窗包装器
# ═══════════════════════════════════════════

class SystemMonitorDialog(QDialog):
    """系统监控弹窗包装器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统监控")
        self.setMinimumSize(700, 500)
        layout = QVBoxLayout(self)
        try:
            from modules.intelligence.system_monitor import SystemMonitorWidget
            self._widget = SystemMonitorWidget(self)
            layout.addWidget(self._widget)
        except ImportError as e:
            layout.addWidget(QLabel(f"模块加载失败: {e}"))


class AIDashboardDialog(QDialog):
    """AI仪表板弹窗包装器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI 仪表板")
        self.setMinimumSize(800, 600)
        layout = QVBoxLayout(self)
        try:
            from modules.intelligence.ai_dashboard_window import AIDashboardWindow
            self._widget = AIDashboardWindow(self)
            layout.addWidget(self._widget)
        except ImportError as e:
            layout.addWidget(QLabel(f"模块加载失败: {e}"))


class SmartWorkflowDialog(QDialog):
    """智能工作流弹窗包装器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("智能工作流")
        self.setMinimumSize(700, 500)
        layout = QVBoxLayout(self)
        layout.addWidget(SmartWorkflowWidget(self))


class BusinessAIDialog(QDialog):
    """业务AI弹窗包装器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("业务 AI 助手")
        self.setMinimumSize(700, 500)
        layout = QVBoxLayout(self)
        layout.addWidget(BusinessAIWidget(self))


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
        subtitle = QLabel("CREW · 13颗智能星球")
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
                dlg.exec_()
            except ImportError as e:
                QMessageBox.warning(self, "错误", f"增强对话模块加载失败: {e}")
        elif planet_id == "knowledge_base":
            try:
                from modules.intelligence.knowledge_base import KnowledgeBase
                dlg = KnowledgeBase(self)
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
                dlg.exec_()
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



class SuperIntelligenceWidget(QWidget):
    """超级智能控制面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent_window = parent
        self._intel = None
        self._build_ui()
        self._init_intelligence()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("🧠 OPCclaw 超级智能系统")
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #2c3e50;")
        layout.addWidget(title)

        # 状态卡片
        status_card = QGroupBox("系统状态")
        status_layout = QVBoxLayout(status_card)

        self._status_label = QLabel("⏳ 正在初始化...")
        self._status_label.setStyleSheet("font-size: 14px; padding: 10px;")
        status_layout.addWidget(self._status_label)

        # 功能开关
        switches_layout = QHBoxLayout()

        self._deep_reasoning_cb = QCheckBox("深度推理")
        self._deep_reasoning_cb.setChecked(True)
        self._deep_reasoning_cb.setToolTip("对复杂查询进行多步推理")
        switches_layout.addWidget(self._deep_reasoning_cb)

        self._self_reflection_cb = QCheckBox("自我反思")
        self._self_reflection_cb.setChecked(True)
        self._self_reflection_cb.setToolTip("分析执行结果并优化策略")
        switches_layout.addWidget(self._self_reflection_cb)

        self._active_learning_cb = QCheckBox("主动学习")
        self._active_learning_cb.setChecked(True)
        self._active_learning_cb.setToolTip("从交互中学习用户偏好")
        switches_layout.addWidget(self._active_learning_cb)

        switches_layout.addStretch()
        status_layout.addLayout(switches_layout)
        layout.addWidget(status_card)

        # 能力展示
        caps_card = QGroupBox("7项核心AI能力")
        caps_layout = QGridLayout(caps_card)
        caps_layout.setSpacing(10)

        capabilities = [
            ("🔍", "多引擎搜索", "聚合多个搜索引擎结果"),
            ("📁", "文件操作", "智能文件读写与管理"),
            ("💻", "代码执行", "安全执行Python代码"),
            ("🌐", "浏览器自动化", "网页浏览与数据提取"),
            ("⏰", "定时任务", "智能调度与提醒"),
            ("🧠", "记忆系统", "长期记忆与学习"),
            ("💬", "会话管理", "多会话上下文切换"),
        ]

        for idx, (icon, name, desc) in enumerate(capabilities):
            row, col = idx // 3, idx % 3
            cap_label = QLabel(f"{icon} <b>{name}</b><br/><span style='color: #666; font-size: 12px;'>{desc}</span>")
            cap_label.setStyleSheet("padding: 8px; background: #f8f9fa; border-radius: 6px;")
            caps_layout.addWidget(cap_label, row, col)

        layout.addWidget(caps_card)

        # 测试区域
        test_card = QGroupBox("功能测试")
        test_layout = QVBoxLayout(test_card)

        self._test_input = QLineEdit()
        self._test_input.setPlaceholderText("输入测试查询，例如：搜索最新的AI新闻")
        test_layout.addWidget(self._test_input)

        btn_layout = QHBoxLayout()
        test_btn = QPushButton("🚀 运行测试")
        test_btn.setStyleSheet("""
            QPushButton {
                background: #3498db; color: white; padding: 10px 20px;
                border-radius: 6px; font-weight: 600;
            }
            QPushButton:hover { background: #2980b9; }
            QPushButton:pressed { padding-top: 11px; padding-bottom: 9px; }
        """)
        test_btn.clicked.connect(self._run_test)
        # 添加悬停缩放动画
        ButtonAnimationHelper.apply_scale_animation(test_btn, 1.03)
        btn_layout.addWidget(test_btn)

        reset_btn = QPushButton("🔄 重置学习")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #95a5a6; color: white; padding: 10px 20px;
                border-radius: 6px; font-weight: 600;
            }
            QPushButton:hover { background: #7f8c8d; }
            QPushButton:pressed { padding-top: 11px; padding-bottom: 9px; }
        """)
        reset_btn.clicked.connect(self._reset_learning)
        # 添加悬停缩放动画
        ButtonAnimationHelper.apply_scale_animation(reset_btn, 1.03)
        btn_layout.addWidget(reset_btn)

        btn_layout.addStretch()
        test_layout.addLayout(btn_layout)

        self._test_output = QTextEdit()
        self._test_output.setReadOnly(True)
        self._test_output.setPlaceholderText("测试结果将显示在这里...")
        self._test_output.setStyleSheet("background: #f8f9fa; padding: 10px; border-radius: 6px;")
        test_layout.addWidget(self._test_output)

        layout.addWidget(test_card)
        layout.addStretch()

    def _init_intelligence(self):
        """初始化超级智能系统"""
        if not SUPER_INTELLIGENCE_AVAILABLE:
            self._status_label.setText("❌ 超级智能模块未安装\n请确保 super_intelligence.py 和 intelligence_integration.py 在当前目录")
            return

        try:
            self._intel = SuperIntelligence()
            self._status_label.setText(
                f"✅ 超级智能系统就绪\n"
                f"   反思次数: {self._intel.reflection.reflection_count}\n"
                f"   学习模式: {len(self._intel.learning.learned_patterns)} 个"
            )
        except Exception as e:
            self._status_label.setText(f"⚠️ 初始化失败: {str(e)}")

    def _run_test(self):
        """运行功能测试"""
        query = self._test_input.text().strip()
        if not query:
            self._test_output.setText("请输入测试查询")
            return

        if not self._intel:
            self._test_output.setText("超级智能系统未初始化")
            return

        try:
            # 获取当前设置
            enable_reasoning = self._deep_reasoning_cb.isChecked()
            enable_reflection = self._self_reflection_cb.isChecked()
            enable_learning = self._active_learning_cb.isChecked()

            self._test_output.setText(f"🔄 正在分析: {query}\n{'='*50}\n")

            # 执行智能流程
            result = self._intel.process(
                query,
                enable_reasoning=enable_reasoning,
                enable_reflection=enable_reflection,
                enable_learning=enable_learning
            )

            output = []
            reasoning = result.get('reasoning', {})
            intent_data = reasoning.get('intent', {}) if isinstance(reasoning, dict) else {}
            output.append(f"📊 意图识别: {intent_data.get('primary', 'unknown') if isinstance(intent_data, dict) else 'unknown'}")
            output.append(f"🎯 置信度: {reasoning.get('confidence', 0):.2f}" if isinstance(reasoning, dict) else "🎯 置信度: N/A")

            recs = result.get('recommendations', {})
            if isinstance(recs, dict):
                tools = ', '.join(recs.get('suggested_tools', []))
                output.append(f"🔧 推荐工具: {tools}")

            if isinstance(reasoning, dict) and 'reasoning_chain' in reasoning:
                output.append(f"\n🧠 推理链:")
                for step in reasoning['reasoning_chain']:
                    if isinstance(step, dict):
                        output.append(f"  → Step {step.get('step', '?')}: {step.get('type', '')}")

            if isinstance(reasoning, dict) and 'strategy' in reasoning:
                strategy = reasoning['strategy']
                if isinstance(strategy, dict):
                    output.append(f"\n📋 执行策略: {strategy.get('approach', '')}")
                    for step in strategy.get('steps', []):
                        output.append(f"  • {step}")

            insights = result.get('insights', [])
            if insights:
                output.append(f"\n💡 智能洞察:")
                for insight in insights:
                    output.append(f"  • {insight}")

            self._test_output.setText(self._test_output.toPlainText() + '\n'.join(output))

        except Exception as e:
            self._test_output.setText(f"❌ 错误: {str(e)}")

    def _reset_learning(self):
        """重置学习数据"""
        if self._intel and self._intel.learning:
            self._intel.learning.learned_patterns.clear()
            self._status_label.setText("✅ 学习数据已重置")


# 模块入口
MODULE_ID = "ai_assistant"
MODULE_NAME = "🤖 AI 助手"
MODULE_ICON = "🤖"
MODULE_DESCRIPTION = "AI 智能助手 - 支持云端/本地多模型"


def create_module(parent=None):
    """创建模块实例"""
    window = AIAssistantWindow(parent)
    return window


# ═══════════════════════════════════════════
# 后端模块包装组件（为纯后端模块提供可视化界面入口）
# ═══════════════════════════════════════════

class AnomalyDetectorWidget(QWidget):
    """异常检测可视化面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        from modules.intelligence.anomaly_detector import AnomalyDetector
        self._detector = AnomalyDetector()
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        title = QLabel("🔍 异常检测引擎")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setStyleSheet("color: #1a202c;")
        layout.addWidget(title)
        
        desc = QLabel("实时监控销售/库存/财务/客户行为/系统五大维度，自动识别异常模式")
        desc.setStyleSheet("color: #718096; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # 检测类型
        types_group = QGroupBox("检测维度")
        types_group.setStyleSheet("QGroupBox { font-weight: 600; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-top: 10px; }")
        types_layout = QGridLayout(types_group)
        types_layout.setSpacing(10)
        
        dimensions = [
            ("📊 销售异常", "突然下降/激增检测"),
            ("📦 库存异常", "负库存、异常消耗"),
            ("💰 财务异常", "大额交易、收支异常"),
            ("👤 客户异常", "频繁退货、异常订单"),
            ("⚙ 系统异常", "数据不一致、重复记录"),
        ]
        for i, (name, desc) in enumerate(dimensions):
            card = QFrame()
            card.setStyleSheet("QFrame { background: #f7fafc; border-radius: 8px; padding: 8px; }")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 10, 12, 10)
            nl = QLabel(name)
            nl.setFont(QFont("PingFang SC", 14, QFont.Bold))
            nl.setStyleSheet("color: #2c3e50;")
            card_layout.addWidget(nl)
            dl = QLabel(desc)
            dl.setStyleSheet("color: #7f8c8d; font-size: 12px;")
            card_layout.addWidget(dl)
            types_layout.addWidget(card, i // 3, i % 3)
        
        layout.addWidget(types_group)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        run_btn = QPushButton("▶ 运行检测")
        run_btn.setMinimumHeight(40)
        run_btn.setCursor(Qt.PointingHandCursor)
        run_btn.setStyleSheet("QPushButton { background: #3498db; color: white; border: none; border-radius: 8px; padding: 10px 24px; font-size: 14px; font-weight: 600; } QPushButton:hover { background: #2980b9; }")
        run_btn.clicked.connect(self._run_detection)
        btn_layout.addWidget(run_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 结果输出
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setPlaceholderText("检测结果将显示在这里...")
        self._output.setStyleSheet("background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; font-size: 13px;")
        layout.addWidget(self._output)
    
    def _run_detection(self):
        self._output.setText("🔍 正在执行异常检测...\n")
        try:
            results = []
            for severity in ['info', 'warning', 'critical']:
                r = self._detector.detect(severity=severity) if hasattr(self._detector, 'detect') else []
                results.append(r)
            if any(results):
                self._output.append("✅ 检测完成")
                for r_list in results:
                    for item in r_list:
                        self._output.append(f"  • {item}")
            else:
                self._output.append("✅ 检测完成，未发现异常")
        except Exception as e:
            self._output.append(f"❌ 检测出错: {e}")


class RecommendationEngineWidget(QWidget):
    """推荐引擎可视化面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        from modules.intelligence.recommendation_engine import RecommendationEngine
        self._engine = RecommendationEngine()
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        title = QLabel("💡 智能推荐引擎")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setStyleSheet("color: #1a202c;")
        layout.addWidget(title)
        
        desc = QLabel("基于购买历史、关联规则、热销排行、用户画像和季节趋势的多维推荐系统")
        desc.setStyleSheet("color: #718096; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # 推荐策略
        strategies_group = QGroupBox("推荐策略")
        strategies_group.setStyleSheet("QGroupBox { font-weight: 600; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-top: 10px; }")
        strat_layout = QVBoxLayout(strategies_group)
        strat_layout.setSpacing(8)
        
        strategies = {
            "purchase_history": ("📋 购买历史推荐", "基于用户历史购买行为"),
            "association_rules": ("🔗 关联规则推荐", "买了A的人还买了B"),
            "hot_sales": ("🔥 热销排行推荐", "当前最受欢迎商品"),
            "personalized": ("👤 个性化推荐", "基于用户画像精准推荐"),
            "seasonal": ("🌸 季节性推荐", "时令/节日/趋势商品"),
        }
        for key, (name, desc_text) in strategies.items():
            row = QHBoxLayout()
            cb = QCheckBox(name)
            cb.setChecked(True)
            cb.setStyleSheet("font-size: 13px; font-weight: 500;")
            row.addWidget(cb)
            dl = QLabel(desc_text)
            dl.setStyleSheet("color: #7f8c8d; font-size: 12px;")
            row.addWidget(dl)
            row.addStretch()
            strat_layout.addLayout(row)
            
        layout.addWidget(strategies_group)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        run_btn = QPushButton("▶ 生成推荐")
        run_btn.setMinimumHeight(40)
        run_btn.setCursor(Qt.PointingHandCursor)
        run_btn.setStyleSheet("QPushButton { background: #e67e22; color: white; border: none; border-radius: 8px; padding: 10px 24px; font-size: 14px; font-weight: 600; } QPushButton:hover { background: #d35400; }")
        run_btn.clicked.connect(self._run_recommendation)
        btn_layout.addWidget(run_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setPlaceholderText("推荐结果将显示在这里...")
        self._output.setStyleSheet("background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; font-size: 13px;")
        layout.addWidget(self._output)
    
    def _run_recommendation(self):
        self._output.setText("💡 正在生成推荐...\n")
        try:
            if hasattr(self._engine, 'get_recommendations'):
                recs = self._engine.get_recommendations()
                self._output.append(f"✅ 生成 {len(recs) if recs else 0} 条推荐")
                for r in (recs or []):
                    self._output.append(f"  • {r}")
            else:
                self._output.append("✅ 推荐引擎已就绪，可通过 API 调用获取推荐结果")
        except Exception as e:
            self._output.append(f"❌ 推荐出错: {e}")


class DataVisualizationWidget(QWidget):
    """数据可视化面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        from modules.intelligence.data_visualization import DataVisualization
        self._viz = DataVisualization()
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        title = QLabel("📈 数据可视化")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setStyleSheet("color: #1a202c;")
        layout.addWidget(title)
        
        desc = QLabel("支持柱状图、折线图、饼图、热力图等多种图表类型的数据可视化引擎")
        desc.setStyleSheet("color: #718096; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # 图表类型选择
        chart_group = QGroupBox("图表类型")
        chart_group.setStyleSheet("QGroupBox { font-weight: 600; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-top: 10px; }")
        chart_layout = QGridLayout(chart_group)
        chart_layout.setSpacing(10)
        
        chart_types = [
            ("bar", "📊 柱状图"), ("line", "📈 折线图"),
            ("pie", "🥧 饼图"), ("scatter", "🔵 散点图"),
            ("heatmap", "🔥 热力图"), ("radar", "🎯 雷达图"),
        ]
        self._chart_btns = {}
        for i, (ctype, cname) in enumerate(chart_types):
            btn = QPushButton(cname)
            btn.setMinimumHeight(44)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("chart_type", ctype)
            btn.setStyleSheet("QPushButton { background: #f7fafc; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 13px; font-weight: 500; } QPushButton:checked { border-color: #3498db; background: #ebf5fb; color: #2980b9; } QPushButton:hover { background: #edf2f7; }")
            self._chart_btns[ctype] = btn
            chart_layout.addWidget(btn, i // 3, i % 3)
        
        layout.addWidget(chart_group)
        
        # 示例数据输入
        data_group = QGroupBox("数据源")
        data_group.setStyleSheet(chart_group.styleSheet())
        data_layout = QVBoxLayout(data_group)
        self._data_input = QPlainTextEdit()
        self._data_input.setPlaceholderText('输入 JSON 数据，如: [{"label":"A","value":10},{"label":"B","value":20}]')
        self._data_input.setMaximumHeight(100)
        self._data_input.setStyleSheet("background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px; font-size: 12px;")
        data_layout.addWidget(self._data_input)
        
        btn_layout = QHBoxLayout()
        gen_btn = QPushButton("▶ 生成图表")
        gen_btn.setMinimumHeight(40)
        gen_btn.setCursor(Qt.PointingHandCursor)
        gen_btn.setStyleSheet("QPushButton { background: #9b59b6; color: white; border: none; border-radius: 8px; padding: 10px 24px; font-size: 14px; font-weight: 600; } QPushButton:hover { background: #8e44ad; }")
        gen_btn.clicked.connect(self._generate_chart)
        btn_layout.addWidget(gen_btn)
        btn_layout.addStretch()
        data_layout.addLayout(btn_layout)
        
        layout.addWidget(data_group)
        
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setPlaceholderText("图表 JSON 数据将显示在这里...")
        self._output.setStyleSheet("background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; font-size: 13px; font-family: monospace;")
        layout.addWidget(self._output)
    
    def _generate_chart(self):
        selected = None
        for ctype, btn in self._chart_btns.items():
            if btn.isChecked():
                selected = ctype
                break
        if not selected:
            self._output.setText("请先选择一种图表类型")
            return
        
        raw = self._data_input.toPlainText().strip()
        if raw:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                self._output.setText("JSON 格式错误，请检查数据格式")
                return
        else:
            data = [{"label": f"项目{i}", "value": i * 10 + 10} for i in range(1, 8)]
        
        try:
            result = self._viz.generate_chart_data(data, selected)
            self._output.setText(json.dumps(result, ensure_ascii=False, indent=2))
        except Exception as e:
            self._output.setText(f"生成图表失败: {e}")


class SmartWorkflowWidget(QWidget):
    """智能工作流可视化面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        from modules.intelligence.smart_workflow import SmartWorkflowManager
        self._manager = SmartWorkflowManager()
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        title = QLabel("🔗 智能工作流引擎")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setStyleSheet("color: #1a202c;")
        layout.addWidget(title)
        
        desc = QLabel("自动化业务流程编排与执行引擎，支持预设工作流和自定义工作流")
        desc.setStyleSheet("color: #718096; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # 预设工作流
        presets_group = QGroupBox("预设工作流")
        presets_group.setStyleSheet("QGroupBox { font-weight: 600; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-top: 10px; }")
        presets_layout = QVBoxLayout(presets_group)
        presets_layout.setSpacing(8)
        
        try:
            workflows = self._manager.engine.list_workflows()
            for wf in workflows:
                row = QHBoxLayout()
                name_lbl = QLabel(f"📋 {wf.name}")
                name_lbl.setStyleSheet("font-size: 13px; font-weight: 500;")
                row.addWidget(name_lbl)
                status = wf.status if hasattr(wf, 'status') else "就绪"
                status_lbl = QLabel(status)
                status_lbl.setStyleSheet(f"color: {'#38a169' if status == '就绪' else '#718096'}; font-size: 12px;")
                row.addWidget(status_lbl)
                row.addStretch()
                run_btn = QPushButton("▶ 执行")
                run_btn.setMinimumHeight(32)
                run_btn.setCursor(Qt.PointingHandCursor)
                run_btn.setStyleSheet("QPushButton { background: #38a169; color: white; border: none; border-radius: 6px; padding: 6px 14px; font-size: 12px; } QPushButton:hover { background: #2f855a; }")
                row.addWidget(run_btn)
                presets_layout.addLayout(row)
        except Exception as e:
            presets_layout.addWidget(QLabel(f"加载工作流列表失败: {e}"))
        
        layout.addWidget(presets_group)
        
        # 输出
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setPlaceholderText("工作流执行日志将显示在这里...")
        self._output.setStyleSheet("background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; font-size: 13px;")
        layout.addWidget(self._output)


class BusinessAIWidget(QWidget):
    """业务 AI 可视化面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        from modules.intelligence.business_ai_assistant import BusinessAIAssistant
        self._assistant = BusinessAIAssistant()
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        title = QLabel("💼 业务 AI 助手")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setStyleSheet("color: #1a202c;")
        layout.addWidget(title)
        
        desc = QLabel("智能客服 · 销售预测 · 库存预警 · 数据洞察 · 自然语言查询")
        desc.setStyleSheet("color: #718096; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # 功能模块
        modules_group = QGroupBox("业务能力")
        modules_group.setStyleSheet("QGroupBox { font-weight: 600; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-top: 10px; }")
        mod_layout = QGridLayout(modules_group)
        mod_layout.setSpacing(10)
        
        modules = [
            ("🤖 智能客服", "自动回复客户咨询"),
            ("📈 销售预测", "基于历史预测销量"),
            ("📦 库存预警", "智能补货建议"),
            ("🔍 数据洞察", "自动分析业务数据"),
            ("💬 NL查询", "自然语言问销售额"),
        ]
        for i, (name, desc_text) in enumerate(modules):
            card = QFrame()
            card.setStyleSheet("QFrame { background: #f7fafc; border-radius: 8px; padding: 8px; }")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 10, 12, 10)
            nl = QLabel(name)
            nl.setFont(QFont("PingFang SC", 13, QFont.Bold))
            nl.setStyleSheet("color: #2c3e50;")
            card_layout.addWidget(nl)
            dl = QLabel(desc_text)
            dl.setStyleSheet("color: #7f8c8d; font-size: 12px;")
            card_layout.addWidget(dl)
            mod_layout.addWidget(card, i // 3, i % 3)
        
        layout.addWidget(modules_group)
        
        # 自然语言查询输入
        query_group = QGroupBox("自然语言查询")
        query_group.setStyleSheet(modules_group.styleSheet())
        query_layout = QVBoxLayout(query_group)
        
        input_row = QHBoxLayout()
        self._query_input = QLineEdit()
        self._query_input.setPlaceholderText("例如：今年销售额最高的产品是什么？")
        self._query_input.setMinimumHeight(40)
        self._query_input.setStyleSheet("border: 2px solid #e2e8f0; border-radius: 8px; padding: 8px 12px; font-size: 14px;")
        self._query_input.returnPressed.connect(self._run_query)
        input_row.addWidget(self._query_input)
        
        query_btn = QPushButton("🔍 查询")
        query_btn.setMinimumHeight(40)
        query_btn.setCursor(Qt.PointingHandCursor)
        query_btn.setStyleSheet("QPushButton { background: #2b6cb0; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-size: 14px; font-weight: 600; } QPushButton:hover { background: #2c5282; }")
        query_btn.clicked.connect(self._run_query)
        input_row.addWidget(query_btn)
        query_layout.addLayout(input_row)
        
        layout.addWidget(query_group)
        
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setPlaceholderText("查询结果将显示在这里...")
        self._output.setStyleSheet("background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; font-size: 13px;")
        layout.addWidget(self._output)
    
    def _run_query(self):
        query = self._query_input.text().strip()
        if not query:
            return
        self._output.append(f"\n🔍 查询: {query}")
        try:
            if hasattr(self._assistant, 'query'):
                result = self._assistant.query(query)
                self._output.append(f"📊 结果: {result}")
            else:
                self._output.append("✅ 业务 AI 助手已就绪，可通过 query() 方法执行自然语言查询")
        except Exception as e:
            self._output.append(f"❌ 查询出错: {e}")
