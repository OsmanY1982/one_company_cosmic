# `modules/styled_widgets.py`

> 路径：`modules/styled_widgets.py` | 行数：48


---


```python
"""
Iqra - 通用样式工具函数
"""
from PyQt5.QtWidgets import QPushButton, QLineEdit
from PyQt5.QtGui import QFont

from iqra.modules.widgets import COLORS


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
