"""
OPCclaw - AI Agent 对话窗口 (入口模块)

此文件为轻量入口，所有类已拆分到独立模块文件中。
保持对外接口不变，其他模块 import ChatWindow 等不受影响。

拆分结构:
- _shared.py           → COLORS, _styled_btn, _styled_input
- animations.py        → ButtonAnimationHelper, ButtonHoverFilter, LoadingAnimationHelper
- message_bubble.py    → MessageBubble
- login_dialog.py      → LoginDialog
- config_manager.py    → ConfigManager
- sidebar_panel.py     → Sidebar
- cloud_model_panel.py → CloudModelPanel
- local_model_panel.py → LocalModelPanel
- skills_panel.py      → SkillsPanel
- general_settings_panel.py → GeneralSettingsPanel
- chat_worker.py       → ChatWorker
- chat_window_core.py  → ChatWindow
"""

from opcclaw.modules.chat_window_core import (
    ChatWindow,
    _guess_deep_model,
    _guess_reasoning_model,
)
from opcclaw.modules.animations import (
    ButtonAnimationHelper,
    ButtonHoverFilter,
    LoadingAnimationHelper,
)
from opcclaw.modules.message_bubble import MessageBubble
from opcclaw.modules.login_dialog import LoginDialog
from opcclaw.modules.config_manager import ConfigManager
from opcclaw.modules.sidebar_panel import Sidebar
from opcclaw.modules.cloud_model_panel import CloudModelPanel
from opcclaw.modules.local_model_panel import LocalModelPanel
from opcclaw.modules.skills_panel import SkillsPanel
from opcclaw.modules.general_settings_panel import GeneralSettingsPanel
from opcclaw.modules.chat_worker import ChatWorker
from opcclaw.modules._shared import COLORS, _styled_btn, _styled_input

__all__ = [
    "ChatWindow",
    "ButtonAnimationHelper", "ButtonHoverFilter", "LoadingAnimationHelper",
    "MessageBubble", "LoginDialog", "ConfigManager",
    "Sidebar", "CloudModelPanel", "LocalModelPanel",
    "SkillsPanel", "GeneralSettingsPanel", "ChatWorker",
    "COLORS", "_styled_btn", "_styled_input",
    "_guess_deep_model", "_guess_reasoning_model",
]


# ── 独立运行入口 ──

def main():
    import sys
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QFont

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QFont("PingFang SC", 10)
    app.setFont(font)

    win = ChatWindow()
    win.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
