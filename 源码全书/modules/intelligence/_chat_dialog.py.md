# `modules/intelligence/_chat_dialog.py`

> 路径：`modules/intelligence/_chat_dialog.py` | 行数：284


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

        # 流式输出（打字机效果）
        if hasattr(self._opcclaw, 'chat_stream'):
            self._stream_accumulated = ""
            self._stream_header = f'<p style="color:#44ccff;font-weight:700;">[{now}] AI:</p>'
            self._stream_chunks_received = False

            # 先插入流式占位块，防止 on_chunk 第一帧误删用户消息
            self._chat_log.append(
                f'{self._stream_header}'
                f'<p style="color:#ccaaff;">'
                f'<span style="color:#88ff88;">_</span></p>'
            )

            try:
                self._opcclaw.chat_stream(
                    text,
                    self._on_stream_chunk,
                    self._on_stream_done,
                    self._on_stream_tool,
                )
                return
            except Exception:
                import traceback; traceback.print_exc()

    # ═══ 流式回调（实例方法 — 确保 QueuedConnection 派发到主线程） ═══

    def _on_stream_chunk(self, chunk: str):
        self._stream_accumulated += chunk
        self._stream_chunks_received = True
        # 移除最后一个块（占位块或上一次流式块）
        cursor = self._chat_log.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.BlockUnderCursor)
        cursor.removeSelectedText()
        display = self._stream_accumulated[-600:].replace('\n', '<br>')
        self._chat_log.append(
            f'{self._stream_header}'
            f'<p style="color:#ccaaff;">{display}'
            f'<span style="color:#88ff88;">_</span></p>'
        )
        sb = self._chat_log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_stream_done(self, full_text: str):
        # 移除最后一个块（流式占位或最后一块内容）
        cursor = self._chat_log.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.BlockUnderCursor)
        cursor.removeSelectedText()
        final = full_text.replace('\n', '<br>') if full_text else ''
        if not final and not self._stream_chunks_received:
            # 流式完全没返回内容：显示错误提示
            self._chat_log.append(
                f'{self._stream_header}'
                f'<p style="color:#ff8888;">[响应为空，请重试]</p>'
            )
        else:
            self._chat_log.append(
                f'{self._stream_header}'
                f'<p style="color:#ccaaff;">{final}</p>'
            )
        self._chat_input.setEnabled(True)
        self._chat_input.setFocus()
        sb = self._chat_log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_stream_tool(self, name: str, status: str):
        icon = "[OK]" if status == "OK" else "[FAIL]" if status == "Failed" else "[...]"
        cursor = self._chat_log.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.BlockUnderCursor)
        cursor.removeSelectedText()
        display = (self._stream_accumulated[-400:] or "").replace('\n', '<br>')
        self._chat_log.append(
            f'{self._stream_header}'
            f'<p style="color:#ccaaff;">{display}'
            f'<span style="color:#888888;"> {name} {icon}</span> '
            f'<span style="color:#88ff88;">_</span></p>'
        )

        # 同步模式（回退）
        try:
            reply = self._opcclaw.chat(text)
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

```
