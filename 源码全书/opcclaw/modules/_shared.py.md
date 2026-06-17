# `opcclaw/modules/_shared.py`

> 路径：`opcclaw/modules/_shared.py` | 行数：78


---


```python
"""
OPCclaw - 共享常量与工具函数
供 chat_window 各子模块导入使用。
"""

from PyQt5.QtWidgets import QPushButton, QLineEdit
from PyQt5.QtGui import QFont

# ═══════════════════════════════════════════
# 颜色常量
# ═══════════════════════════════════════════

COLORS = {
    "bg": "#F5F6FA",
    "bg_alt": "#EBEDF3",
    "sidebar": "#1E2A3A",
    "sidebar_hover": "#2C3E50",
    "sidebar_active": "#3498DB",
    "header": "#2C3E50",
    "card": "#FFFFFF",
    "border": "#E0E4EA",
    "primary": "#3498DB",
    "primary_hover": "#2980B9",
    "secondary": "#E8F4FD",
    "secondary_hover": "#D4ECFA",
    "success": "#27AE60",
    "warning": "#F39C12",
    "danger": "#E74C3C",
    "text": "#2C3E50",
    "text_light": "#7F8C8D",
    "text_white": "#FFFFFF",
    "input_bg": "#F8F9FA",
}


# ═══════════════════════════════════════════
# 通用工具函数
# ═══════════════════════════════════════════

def _styled_btn(text: str, color: str = COLORS["primary"], height: int = 36,
                font_size: int = 13) -> QPushButton:
    """创建统一样式的按钮"""
    btn = QPushButton(text)
    btn.setMinimumHeight(height)
    btn.setFont(QFont("PingFang SC", font_size))
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {color};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 6px 16px;
        }}
        QPushButton:hover {{ opacity: 0.9; }}
        QPushButton:disabled {{ background: #BDC3C7; }}
    """)
    return btn


def _styled_input(placeholder: str = "", password: bool = False,
                  height: int = 38) -> QLineEdit:
    """创建统一样式的输入框"""
    inp = QLineEdit()
    if password:
        inp.setEchoMode(QLineEdit.Password)
    inp.setPlaceholderText(placeholder)
    inp.setMinimumHeight(height)
    inp.setStyleSheet(f"""
        QLineEdit {{
            border: 2px solid {COLORS['border']};
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 13px;
            background: {COLORS['input_bg']};
        }}
        QLineEdit:focus {{ border-color: {COLORS['primary']}; background: white; }}
    """)
    return inp

```
