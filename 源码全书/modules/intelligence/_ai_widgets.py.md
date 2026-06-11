# `modules/intelligence/_ai_widgets.py`

> 路径：`modules/intelligence/_ai_widgets.py` | 行数：783


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

from ._ai_shared import ButtonAnimationHelper, SUPER_INTELLIGENCE_AVAILABLE


# ═══════════════════════════════════════════
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
                f"   反思次数: {len(self._intel.reflection.reflections)}\n"
                f"   学习模式: {len(self._intel.learning.patterns.get('query_patterns', {}))} 个"
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

            # 设置功能开关
            self._intel.toggle_feature('reasoning', enable_reasoning)
            self._intel.toggle_feature('reflection', enable_reflection)
            self._intel.toggle_feature('learning', enable_learning)
            
            # 执行智能流程
            result = self._intel.process(query)

            output = []
            reasoning = result.get('reasoning', {})
            intent_data = reasoning.get('intent', {}) if isinstance(reasoning, dict) else {}
            output.append(f"📊 意图识别: {intent_data.get('primary', 'unknown') if isinstance(intent_data, dict) else 'unknown'}")
            output.append(f"🎯 置信度: {reasoning.get('intent', {}).get('confidence', 0):.2f}" if isinstance(reasoning, dict) else "🎯 置信度: N/A")

            recs = result.get('recommendations', {})
            if isinstance(recs, dict):
                tools = ', '.join(recs.get('suggested_tools', []))
                output.append(f"🔧 推荐工具: {tools}")

            if isinstance(reasoning, dict) and 'chain' in reasoning:
                output.append(f"\n🧠 推理链:")
                for step in reasoning['chain']:
                    if isinstance(step, dict):
                        output.append(f"  → Step {step.get('name', '?')}: {step.get('type', '')}")

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
            self._intel.learning.patterns.get('query_patterns', {}).clear()
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
        from modules.intelligence.self_monitor import SelfMonitor
        from modules.intelligence.performance_monitor import PerformanceMonitor
        
        self._detector = AnomalyDetector()
        self._self_monitor = SelfMonitor()
        self._perf_monitor = PerformanceMonitor()
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
            # 使用 detect_all() 综合检测
            result = self._detector.detect_all()
            summary = result.get('summary', {})
            anomalies = result.get('anomalies', [])
            
            self._output.append(f"✅ 检测完成")
            self._output.append(f"   总计异常: {summary.get('total_anomalies', 0)}")
            self._output.append(f"   严重: {summary.get('critical', 0)} | 警告: {summary.get('warning', 0)} | 信息: {summary.get('info', 0)}")
            
            # 系统自检
            health = self._self_monitor.health_check()
            checks = health.get('checks', {})
            self._output.append(f"\n🏥 系统健康检查:")
            for check_name, check_result in checks.items():
                if isinstance(check_result, dict):
                    if 'exists' in check_result:
                        status_icon = '✅' if check_result['exists'] else '❌'
                        self._output.append(f"   {status_icon} {check_name}")
                    elif 'total_gb' in check_result:
                        self._output.append(f"   💾 磁盘: {check_result['free_gb']:.1f}GB 可用 / {check_result['total_gb']:.1f}GB ({check_result['usage_pct']:.1f}%)")
                else:
                    self._output.append(f"   ℹ️ {check_name}: {check_result}")
            self._output.append(f"   总体状态: {health.get('status', '未知')}")
            
            # 显示严重异常
            critical = [a for a in anomalies if a.get('severity') == 'critical']
            if critical:
                self._output.append(f"\n🚨 严重异常:")
                for a in critical:
                    self._output.append(f"   • {a.get('message', '')}")
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
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
        from modules.intelligence.data_visualization import DataVisualization
        from modules.intelligence.analysis_tools import AnalysisTools
        from modules.intelligence.data_import_tools import import_csv_to_db, import_json_to_db
        
        self._viz = DataVisualization()
        self._data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
        self._analysis = AnalysisTools(self._data_dir)
        self._import_csv = import_csv_to_db
        self._import_json = import_json_to_db
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
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
        from modules.intelligence.smart_workflow import SmartWorkflowManager
        from modules.intelligence.workflow_engine import WorkflowEngine
        
        self._manager = SmartWorkflowManager()
        self._engine = WorkflowEngine()
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
            workflows = self._manager.list_available_workflows()
            for wf in workflows:
                row = QHBoxLayout()
                wf_name = wf.get('name', wf.name) if isinstance(wf, dict) else wf.name
                wf_status = wf.get('status', '就绪') if isinstance(wf, dict) else getattr(wf, 'status', '就绪')
                name_lbl = QLabel(f"📋 {wf_name}")
                name_lbl.setStyleSheet("font-size: 13px; font-weight: 500;")
                row.addWidget(name_lbl)
                status_lbl = QLabel(wf_status)
                status_lbl.setStyleSheet(f"color: {'#38a169' if wf_status == '就绪' else '#718096'}; font-size: 12px;")
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
        from modules.intelligence.business_tools import query_products, query_orders, query_customers, query_finance
        from modules.intelligence.crm_tools import analyze_customer_value, get_customer_segments, get_contact_reminders
        from modules.intelligence.inventory_tools import query_inventory, get_inventory_alerts, get_inventory_summary
        from modules.intelligence.marketing_tools import MarketingTools
        from modules.intelligence.smart_report_tools import generate_customer_ranking, generate_product_performance
        
        self._assistant = BusinessAIAssistant()
        
        # 星空版业务工具后端
        self._data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
        self._query_products = query_products
        self._query_orders = query_orders
        self._query_customers = query_customers
        self._query_finance = query_finance
        self._crm_analyze = analyze_customer_value
        self._crm_segments = get_customer_segments
        self._crm_reminders = get_contact_reminders
        self._inv_query = query_inventory
        self._inv_alerts = get_inventory_alerts
        self._inv_summary = get_inventory_summary
        self._marketing_tools = MarketingTools(self._data_dir)
        self._report_customer_ranking = generate_customer_ranking
        self._report_product_perf = generate_product_performance
        
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
            # 优先使用 BusinessAIAssistant
            if hasattr(self._assistant, 'natural_language_query'):
                result = self._assistant.natural_language_query(query)
                self._output.append(f"📊 结果: {result}")
            # 星空版工具作为补充数据源
            elif hasattr(self, '_query_products'):
                # 尝试产品查询
                if any(kw in query for kw in ['产品', '商品', 'product']):
                    data = self._query_products(self._data_dir, '')
                    self._output.append(f"📦 产品查询: {data.get('message', '')}")
                elif any(kw in query for kw in ['订单', '销售', 'order']):
                    data = self._query_orders(self._data_dir, '')
                    self._output.append(f"📋 订单查询: {data.get('message', '')}")
                elif any(kw in query for kw in ['客户', 'customer']):
                    data = self._query_customers(self._data_dir, '')
                    self._output.append(f"👤 客户查询: {data.get('message', '')}")
                elif any(kw in query for kw in ['财务', '收支', 'finance']):
                    data = self._query_finance(self._data_dir)
                    self._output.append(f"💰 财务查询: {data.get('message', '')}")
                else:
                    self._output.append("💡 请使用更具体的查询关键词（产品/订单/客户/财务）")
            else:
                self._output.append("✅ 业务 AI 助手已就绪，可通过 query() 方法执行自然语言查询")
        except Exception as e:
            self._output.append(f"❌ 查询出错: {e}")

```
