# -*- coding: utf-8 -*-
"""悬浮球右键菜单 Mixin — QMenu 原生实现（从备份恢复）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt5.QtWidgets import QMenu
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QCursor
from core.shapes import SHAPE_MODES


class FloatingPlanetMenuMixin:
    """右键菜单：QMenu 原生方案"""

    def contextMenuEvent(self, event):
        """macOS 触摸板双指点按：延迟弹出打破事件循环死锁"""
        # 清除拖拽状态，避免 mousePressEvent 残留干扰
        if hasattr(self, '_dragging'):
            self._dragging = False
        global_pos = QCursor.pos()
        QTimer.singleShot(10, lambda gp=global_pos: self._show_context_menu(gp))
        event.accept()

    def _smart_raise(self):
        """智能置顶：仅当无子窗口可见时才 raise()"""
        from PyQt5.QtWidgets import QApplication
        try:
            for widget in QApplication.topLevelWidgets():
                if widget is self:
                    continue
                if widget.isVisible() and widget.windowFlags() & Qt.Window:
                    return
        except Exception:
            pass
        self.raise_()

    def _show_context_menu(self, global_pos: QPoint):
        """QMenu 右键菜单 — 从 6月18日全局备份恢复"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: rgba(20, 20, 40, 240);
                color: #e0e0ff;
                border: 1px solid rgba(100, 160, 255, 80);
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 6px 28px 6px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: rgba(80, 140, 255, 60);
            }
        """)

        shape_icons = {
            k: v.get("name", k) for k, v in SHAPE_MODES.items()
        }

        # ═══════════ 悬浮球子菜单 ═══════════
        floating_menu = menu.addMenu("悬浮球")
        floating_menu.setStyleSheet(menu.styleSheet())

        planet_menu = floating_menu.addMenu("星球形态")
        planet_menu.setStyleSheet(floating_menu.styleSheet())
        for key in self._planet_keys:
            label = shape_icons.get(key, key)
            action = planet_menu.addAction(label)
            action.triggered.connect(
                lambda checked, cat="planet", k=key: self._switch_to_shape(cat, k)
            )

        alien_menu = floating_menu.addMenu("外星人形态")
        alien_menu.setStyleSheet(floating_menu.styleSheet())
        for key in self._alien_keys:
            label = shape_icons.get(key, key)
            action = alien_menu.addAction(label)
            action.triggered.connect(
                lambda checked, cat="alien", k=key: self._switch_to_shape(cat, k)
            )

        starship_menu = floating_menu.addMenu("太空星舰")
        starship_menu.setStyleSheet(floating_menu.styleSheet())
        for key in self._starship_keys:
            label = shape_icons.get(key, key)
            action = starship_menu.addAction(label)
            action.triggered.connect(
                lambda checked, cat="starship", k=key: self._switch_to_shape(cat, k)
            )

        # ═══════════ AI对话子菜单 ═══════════
        ai_menu = menu.addMenu("AI对话")
        ai_menu.setStyleSheet(menu.styleSheet())

        chat_action = ai_menu.addAction("AI 对话")
        chat_action.triggered.connect(self._open_chat)

        ai_menu.addSeparator()

        model_action = ai_menu.addAction("模型设置")
        model_action.triggered.connect(self._open_model_config)

        ai_menu.addSeparator()

        # 打开各模块
        modules_menu = ai_menu.addMenu("打开模块")
        modules_menu.setStyleSheet(ai_menu.styleSheet())
        modules = [
            ("business", "业务管理"),
            ("intelligence", "智能中心"),
            ("data", "数据中心"),
            ("digital_emp", "数字员工工作台"),
        ]
        if self._role == "admin":
            modules += [
                ("personnel", "人员管理"),
                ("system", "系统设置"),
            ]

        for mid, mname in modules:
            action = modules_menu.addAction(mname)
            action.setData(mid)
            action.triggered.connect(
                lambda checked, m=mid: self._open_module(m)
            )

        # ═══════════ 语音对话子菜单 ═══════════
        voice_menu = menu.addMenu("语音对话")
        voice_menu.setStyleSheet(menu.styleSheet())

        voice_action = voice_menu.addAction("语音对话")
        voice_action.triggered.connect(self._start_voice_chat)

        voice_menu.addSeparator()

        wake_action = voice_menu.addAction("语音唤醒 (开)" if self._wake_word_mode else "语音唤醒 (关)")
        wake_action.triggered.connect(self._toggle_wake_word)

        # ═══════════ 缩放倍数子菜单 ═══════════
        scale_menu = menu.addMenu("缩放倍数")
        scale_menu.setStyleSheet(menu.styleSheet())
        scale_options = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
        for val in scale_options:
            label = f"{val:.2f}x" if val != int(val) else f"{val:.1f}x"
            if abs(self._scale_multiplier - val) < 0.01:
                label = f"✓ {label}"
            action = scale_menu.addAction(label)
            action.triggered.connect(
                lambda checked, v=val: self._set_scale_multiplier(v)
            )

        menu.addSeparator()

        # ═══════════ 第一层独立项 ═══════════
        move_action = menu.addAction("自动漫游 (开)" if self._auto_move else "自动漫游 (关)")
        move_action.triggered.connect(self._toggle_auto_move)

        exit_action = menu.addAction("退出悬浮球")
        exit_action.triggered.connect(self._on_exit)

        menu.exec_(global_pos)
