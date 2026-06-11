# `modules/git_panel.py`

> 路径：`modules/git_panel.py` | 行数：256


---


```python
# -*- coding: utf-8 -*-
"""
Git 面板 — 侧栏 Git 状态视图

不污染 chat_window.py，通过独立模块注入。
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTextEdit, QScrollArea, QSizePolicy, QSpacerItem, QGroupBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from opcclaw.core.git_ops import GitOps

COLORS = {
    "bg": "#0D1117",
    "card_bg": "#161B22",
    "border": "#30363D",
    "text": "#C9D1D9",
    "text_light": "#8B949E",
    "accent": "#58A6FF",
    "green": "#3FB950",
    "red": "#F85149",
    "yellow": "#D29922",
    "purple": "#A371F7",
}


def _find_git_root():
    current = os.getcwd()
    for _ in range(10):
        if os.path.isdir(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return os.getcwd()


class GitRefreshThread(QThread):
    """后台刷新 Git 状态"""
    result = pyqtSignal(dict)

    def run(self):
        try:
            g = GitOps(_find_git_root())
            s = g.status()
            commits = g.log(max_count=10)
            remote = g.get_remote_url()
            self.result.emit({
                "ok": True,
                "branch": s.branch,
                "ahead": s.ahead,
                "behind": s.behind,
                "is_clean": s.is_clean,
                "has_conflicts": s.has_conflicts,
                "staged": len(s.staged),
                "modified": len(s.modified),
                "untracked": len(s.untracked),
                "deleted": len(s.deleted),
                "commits": [
                    {"hash": c.short_hash, "author": c.author, "date": c.date, "message": c.message}
                    for c in commits
                ],
                "remote": remote,
            })
        except Exception as e:
            self.result.emit({"ok": False, "error": str(e)})


class GitPanel(QWidget):
    """Git 状态与操作面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._git_root = _find_git_root()
        self._in_git_repo = os.path.isdir(os.path.join(self._git_root, ".git"))
        self._build()
        if self._in_git_repo:
            self._refresh()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Git 版本管理")
        title.setFont(QFont("PingFang SC", 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text']}; padding-bottom: 4px;")
        layout.addWidget(title)

        if not self._in_git_repo:
            no_git = QLabel("当前目录非 Git 仓库")
            no_git.setStyleSheet(f"color: {COLORS['text_light']}; padding: 20px;")
            no_git.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_git)
            layout.addStretch()
            return

        # ── 仓库信息条 ──
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{ background: {COLORS['card_bg']}; border: 1px solid {COLORS['border']}; border-radius: 8px; }}
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(12, 10, 12, 10)
        info_layout.setSpacing(4)

        self._repo_label = QLabel(f"仓库: {os.path.basename(self._git_root)}")
        self._repo_label.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 11px;")
        info_layout.addWidget(self._repo_label)

        self._branch_label = QLabel("分支: --")
        self._branch_label.setFont(QFont("PingFang SC", 13, QFont.Bold))
        self._branch_label.setStyleSheet(f"color: {COLORS['accent']};")
        info_layout.addWidget(self._branch_label)

        self._sync_label = QLabel("")
        self._sync_label.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 11px;")
        info_layout.addWidget(self._sync_label)

        layout.addWidget(info_frame)

        # ── 状态摘要 ──
        status_frame = QFrame()
        status_frame.setStyleSheet(f"""
            QFrame {{ background: {COLORS['card_bg']}; border: 1px solid {COLORS['border']}; border-radius: 8px; }}
        """)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(12, 8, 12, 8)
        status_layout.setSpacing(16)

        self._clean_label = QLabel("状态: --")
        status_layout.addWidget(self._clean_label)

        self._staged_label = QLabel("已暂存: --")
        status_layout.addWidget(self._staged_label)

        self._mod_label = QLabel("已修改: --")
        status_layout.addWidget(self._mod_label)

        layout.addWidget(status_frame)

        # ── 操作按钮 ──
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 4, 0, 0)
        btn_layout.setSpacing(8)

        buttons = [
            ("刷新", self._refresh, COLORS["accent"]),
            ("提交", lambda: None, COLORS["green"]),
            ("拉取", lambda: None, COLORS["yellow"]),
            ("推送", lambda: None, COLORS["purple"]),
            ("暂存", lambda: None, COLORS["text_light"]),
        ]
        for label, callback, color in buttons:
            btn = QPushButton(label)
            btn.setMinimumHeight(30)
            btn.setFont(QFont("PingFang SC", 11))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 4px 12px;
                }}
                QPushButton:hover {{
                    opacity: 0.85;
                }}
            """)
            btn.clicked.connect(callback)
            btn_layout.addWidget(btn)

        layout.addWidget(btn_frame)

        # ── 最近提交 ──
        commits_group = QGroupBox("最近提交")
        commits_group.setFont(QFont("PingFang SC", 12, QFont.Bold))
        commits_group.setStyleSheet(f"""
            QGroupBox {{ color: {COLORS['text']}; border: none; margin-top: 8px; }}
            QGroupBox::title {{ padding-bottom: 4px; }}
        """)
        commits_layout = QVBoxLayout(commits_group)
        commits_layout.setContentsMargins(0, 4, 0, 0)

        self._commits_text = QTextEdit()
        self._commits_text.setReadOnly(True)
        self._commits_text.setMinimumHeight(200)
        self._commits_text.setStyleSheet(f"""
            QTextEdit {{
                background: {COLORS['card_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                font-family: 'JetBrains Mono', 'Menlo', monospace;
                font-size: 11px;
                padding: 8px;
            }}
        """)
        commits_layout.addWidget(self._commits_text)

        layout.addWidget(commits_group, stretch=1)

        # 加载提示
        self._loading_label = QLabel("正在加载...")
        self._loading_label.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 11px;")
        self._loading_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._loading_label)

    def _refresh(self):
        self._loading_label.setText("正在刷新...")
        self._thread = GitRefreshThread()
        self._thread.result.connect(self._on_result)
        self._thread.start()

    def _on_result(self, data: dict):
        if not data.get("ok"):
            self._loading_label.setText(f"错误: {data.get('error', '未知')}")
            return

        self._loading_label.setText("")
        self._branch_label.setText(f"分支: {data['branch']}")

        # 同步状态
        ahead, behind = data["ahead"], data["behind"]
        parts = []
        if ahead:
            parts.append(f"领先 {ahead}")
        if behind:
            parts.append(f"落后 {behind}")
        self._sync_label.setText(" | ".join(parts) if parts else "已同步")

        # 状态摘要
        if data["is_clean"]:
            self._clean_label.setText(f"状态: 干净")
            self._clean_label.setStyleSheet(f"color: {COLORS['green']}; font-weight: bold;")
        else:
            self._clean_label.setText(f"状态: 有变更")
            self._clean_label.setStyleSheet(f"color: {COLORS['yellow']}; font-weight: bold;")

        self._staged_label.setText(f"已暂存: {data['staged']}")
        self._mod_label.setText(f"已修改: {data['modified']}")

        # 提交历史
        lines = []
        for c in data["commits"]:
            lines.append(f"{c['hash']}  {c['date']}  {c['author']}")
            lines.append(f"    {c['message']}")
        self._commits_text.setText("\n".join(lines))

```
