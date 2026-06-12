# `opcclaw/modules/animations.py`

> 路径：`opcclaw/modules/animations.py` | 行数：110


---


```python
"""
OPCclaw - 按钮动画与交互辅助组件
"""

from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QRect, QObject, QEvent
from PyQt5.QtWidgets import QPushButton


class ButtonAnimationHelper:
    """按钮悬停动画辅助类 - 缩放效果"""

    @staticmethod
    def apply_scale_animation(button, scale_factor=1.05):
        """为按钮应用缩放悬停动画"""
        # 保存原始尺寸
        original_size = button.sizeHint()
        button._original_size = original_size
        button._scale_factor = scale_factor

        # 创建动画
        animation = QPropertyAnimation(button, b"geometry")
        animation.setDuration(200)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        button._hover_animation = animation

        # 安装事件过滤器
        button.installEventFilter(button)

        # 保存原始事件处理方法
        original_enter = button.enterEvent
        original_leave = button.leaveEvent

        def new_enter(event):
            if original_enter != button.enterEvent:
                original_enter(event)
            ButtonAnimationHelper._animate_scale(button, True)
            QPushButton.enterEvent(button, event)

        def new_leave(event):
            if original_leave != button.leaveEvent:
                original_leave(event)
            ButtonAnimationHelper._animate_scale(button, False)
            QPushButton.leaveEvent(button, event)

        button.enterEvent = new_enter
        button.leaveEvent = new_leave

    @staticmethod
    def _animate_scale(button, hover):
        """执行缩放动画"""
        if not hasattr(button, '_hover_animation'):
            return

        animation = button._hover_animation
        rect = button.geometry()

        if hover:
            # 放大
            new_width = int(rect.width() * button._scale_factor)
            new_height = int(rect.height() * button._scale_factor)
            x_offset = (rect.width() - new_width) // 2
            y_offset = (rect.height() - new_height) // 2
            animation.setStartValue(rect)
            animation.setEndValue(QRect(rect.x() + x_offset, rect.y() + y_offset,
                                       new_width, new_height))
        else:
            # 恢复原始尺寸
            new_width = int(rect.width() / button._scale_factor)
            new_height = int(rect.height() / button._scale_factor)
            x_offset = (rect.width() - new_width) // 2
            y_offset = (rect.height() - new_height) // 2
            animation.setStartValue(rect)
            animation.setEndValue(QRect(rect.x() + x_offset, rect.y() + y_offset,
                                       new_width, new_height))

        animation.start()


class ButtonHoverFilter(QObject):
    """按钮悬停颜色过滤器的简化版本"""

    def __init__(self, button, hover_color, normal_color):
        super().__init__(button)
        self.button = button
        self.hover_color = hover_color
        self.normal_color = normal_color

    def eventFilter(self, obj, event):
        if obj == self.button:
            if event.type() == QEvent.Enter:
                obj.setStyleSheet(obj.styleSheet().replace(self.normal_color, self.hover_color))
            elif event.type() == QEvent.Leave:
                obj.setStyleSheet(obj.styleSheet().replace(self.hover_color, self.normal_color))
        return super().eventFilter(obj, event)


class LoadingAnimationHelper:
    """加载动画辅助类"""

    @staticmethod
    def set_loading(button, loading=True, original_text=None):
        """设置按钮加载状态"""
        if loading:
            button.setEnabled(False)
            button._original_text = button.text()
            button.setText("\u23f3 加载中...")
        else:
            button.setEnabled(True)
            if hasattr(button, '_original_text'):
                button.setText(button._original_text)

```
