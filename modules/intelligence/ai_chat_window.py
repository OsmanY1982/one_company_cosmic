"""
AI助手 · NEURAL — 独立子窗口
消息历史 + 输入框 + 快捷提示按钮 + 离线分析
"""
import os, sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel,
)
from PyQt5.QtCore import Qt

# ═══════ 样式常量 ═══════
INPUT_STYLE = """
    QLineEdit, QTextEdit {
        background: rgba(12,6,22,230); color: #ccbbdd;
        border: 1px solid rgba(170,80,255,35); border-radius: 6px;
        padding: 6px 10px; font-size: 12px;
    }
    QLineEdit:focus { border: 1px solid rgba(180,100,255,180); }
"""
BTN_PRIMARY = """
    QPushButton {
        background: rgba(150,60,220,40); color: #ddaaff;
        border: 1px solid rgba(170,80,240,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(170,80,240,70); }
"""
BTN_DANGER = """
    QPushButton {
        background: rgba(200,60,40,40); color: #ffaaaa;
        border: 1px solid rgba(200,80,50,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px;
    }
    QPushButton:hover { background: rgba(220,80,50,70); }
"""

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")


class AiChatWindow(QDialog):
    """AI助手 · NEURAL"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI助手 · NEURAL")
        self.setMinimumSize(700, 550)
        self.setStyleSheet("background: rgba(10,5,20,240);")
        self._build_ui()

    def _build_ui(self):
        l = QVBoxLayout(self)
        l.setSpacing(10)
        l.setContentsMargins(16, 12, 16, 12)

        info = QLabel("AI 助手 — 基于大模型的智能对话")
        info.setStyleSheet("color: #776699; font-size: 12px; background: transparent; margin-bottom: 8px;")
        l.addWidget(info)

        self.ai_chat = QTextEdit()
        self.ai_chat.setReadOnly(True)
        self.ai_chat.setStyleSheet("""
            QTextEdit {
                background: rgba(8,4,16,230); color: #bb99dd;
                border: 1px solid rgba(170,80,255,35); border-radius: 10px;
                padding: 12px; font-size: 12px; line-height: 1.6;
            }
        """)
        l.addWidget(self.ai_chat, 1)

        # 快捷提示按钮行
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
            btn.clicked.connect(lambda _, pt=prompt_text: self._ai_quick_prompt(pt))
            prompts_row.addWidget(btn)
        prompts_row.addStretch()
        l.addLayout(prompts_row)

        ir = QHBoxLayout()
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("输入问题，如：分析本月销售趋势...")
        self.ai_input.setStyleSheet(INPUT_STYLE)
        self.ai_input.returnPressed.connect(self._ai_send)
        ir.addWidget(self.ai_input, 1)

        send = QPushButton("发送")
        send.setStyleSheet(BTN_PRIMARY)
        send.clicked.connect(self._ai_send)
        ir.addWidget(send)

        clear_btn = QPushButton("清屏")
        clear_btn.setStyleSheet(BTN_DANGER)
        clear_btn.clicked.connect(lambda: self.ai_chat.clear())
        ir.addWidget(clear_btn)
        l.addLayout(ir)

    def _ai_quick_prompt(self, prompt_text):
        self.ai_input.setText(prompt_text)
        self._ai_send()

    def _ai_send(self):
        text = self.ai_input.text().strip()
        if not text:
            return
        self.ai_input.clear()
        now = datetime.now().strftime("%H:%M:%S")
        self.ai_chat.append(f'<p style="color:#ffaa44;font-weight:700;">[{now}] 你:</p><p style="color:#ddccff;">{text}</p>')
        try:
            db_path = os.path.join(DATA_DIR, "order.db")
            context_hint = ""
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                total = conn.execute("SELECT COUNT(*) as c, COALESCE(SUM(total_amount),0) as s FROM orders").fetchone()
                conn.close()
                if total['c'] > 0:
                    context_hint = f"\n[系统上下文: 订单总数{total['c']}, 总金额¥{total['s']:.0f}]"

            parent = self.parent()
            if hasattr(parent, '_llm') and parent._llm:
                resp = parent._llm.chat([{"role": "user", "content": text + context_hint}])
                self.ai_chat.append(f'<p style="color:#44ccff;font-weight:700;">[{now}] AI:</p><p style="color:#ccaaff;">{resp}</p>')
            else:
                offline_resp = self._offline_analysis(text)
                self.ai_chat.append(f'<p style="color:#44ccff;font-weight:700;">[{now}] AI(离线):</p><p style="color:#ccaaff;">{offline_resp}</p>')
        except Exception as e:
            self.ai_chat.append(f'<p style="color:#ff6666;">错误: {e}</p>')

    def _offline_analysis(self, text: str) -> str:
        db_path = os.path.join(DATA_DIR, "order.db")
        if not os.path.exists(db_path):
            return "离线模式：当前无订单数据，请先导入数据或连接AI引擎。"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            total = conn.execute("SELECT COUNT(*) as c, COALESCE(SUM(total_amount),0) as s FROM orders").fetchone()
            top = conn.execute(
                "SELECT product_name, COUNT(*) as cnt FROM orders GROUP BY product_name ORDER BY cnt DESC LIMIT 3"
            ).fetchall()
            recent = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 5").fetchall()
            conn.close()
            lines = [f"离线模式 — 基于本地 {total['c']} 条订单数据分析："]
            lines.append(f"  总金额: ¥{total['s']:.2f}")
            if top:
                lines.append("  热门产品: " + ", ".join(f"{r['product_name']}({r['cnt']}单)" for r in top))
            if recent:
                latest = recent[0]
                lines.append(f"  最新订单: {latest['order_no']} ({latest['customer_name']} ¥{latest['total_amount']:.0f})")
            return "<br>".join(lines)
        except Exception as e:
            conn.close()
            return f"离线模式：数据分析出错 - {e}"
        finally:
            try:
                conn.close()
            except Exception:
                pass