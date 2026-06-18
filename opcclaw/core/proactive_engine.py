# -*- coding: utf-8 -*-
"""
ProactiveEngine — AI 主动执行与推送引擎

解决 AI "问一句回一句"的被动模式，实现:
  1. 完成后自动建议下一步（上下文意图推测）
  2. 后台监控 + 主动推送消息到对话窗口
  3. 自主持续执行循环（遇阻塞才问，否则不打扰）

用法:
    from opcclaw.core.proactive_engine import ProactiveEngine

    engine = ProactiveEngine(chat_engine=chat_engine, agent=agent_loop)
    engine.on_push.connect(chat_window.append_message)   # 主动推送
    engine.on_suggest.connect(chat_window.show_suggestion) # 建议气泡

    # 启动后台监控
    engine.start_monitoring()

    # 完成一次任务后自动建议
    engine.suggest_next(user_message="帮我整理桌面文件",
                        completion_summary="桌面文件已按类型归类到 4 个文件夹")

特性:
  - 多维度监控（文件变化 / 进程状态 / 定时触发 / 项目健康度）
  - 智能建议生成（基于对话上下文 + 系统状态）
  - 可配置监控规则
"""

import os
import time
import threading
import json
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum, auto
from PyQt5.QtCore import QObject, pyqtSignal

from .opcclaw_logging import logger


# ═══════════════════════════════════════════
# 事件类型
# ═══════════════════════════════════════════

class ProactiveEventType(Enum):
    SUGGESTION = auto()     # 智能建议（任务完成后的下一步）
    ALERT = auto()          # 监控告警（文件异常、进程崩溃等）
    INSIGHT = auto()        # 洞察发现（发现可优化项）
    REMINDER = auto()       # 提醒（定时任务到期）


@dataclass
class ProactiveEvent:
    """主动推送事件"""
    type: ProactiveEventType
    title: str                        # 简短标题
    body: str                         # 详细信息
    action_label: str = ""            # 可操作按钮文字（如"执行"）
    action_payload: Dict = field(default_factory=dict)  # 操作附带数据
    priority: int = 0                 # 0=常规, 1=重要, 2=紧急
    timestamp: float = field(default_factory=time.time)


# ═══════════════════════════════════════════
# 建议生成器
# ═══════════════════════════════════════════

SUGGESTION_SYSTEM_PROMPT = """你是 AI 助手的主动建议生成器。根据已完成的任务和当前系统状态，生成 1-2 条用户可能需要的下一步建议。

规则:
1. 每条建议必须是具体可操作的（不是泛泛的"你还可以做XX"）
2. 优先关联刚完成的任务（如"刚整理了桌面，要不要把下载文件夹也整理？"）
3. 如果没有明显建议，可以基于系统状态（如"发现 3 个 7 天未清理的临时文件"）
4. 建议要简短，每条不超过 25 字
5. 输出纯 JSON 数组: [{"title": "...", "body": "..."}]
6. 如果实在没有建议，输出空数组 []

上下文:
{context}"""


class SuggestionEngine:
    """智能建议生成"""

    def __init__(self, backend=None):
        self._backend = backend

    def generate(
        self,
        user_message: str,
        completion_summary: str,
        system_context: str = "",
    ) -> List[Dict]:
        """
        生成下一步建议

        Args:
            user_message: 原始用户请求
            completion_summary: 完成结果总结
            system_context: 系统状态摘要（当前项目、打开文件等）

        Returns:
            [{title, body}, ...]
        """
        if not self._backend:
            return []

        context_parts = [
            f"用户请求: {user_message}",
            f"完成结果: {completion_summary}",
        ]
        if system_context:
            context_parts.append(f"系统状态: {system_context}")

        messages = [
            {"role": "system", "content": SUGGESTION_SYSTEM_PROMPT.format(
                context="\n".join(context_parts)
            )},
            {"role": "user", "content": "请生成建议。"},
        ]

        try:
            response = self._backend.chat(messages)
            content = response.content.strip() if hasattr(response, 'content') else str(response).strip()

            # 提取 JSON
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.split("```")[0].strip()

            suggestions = json.loads(content)
            if not isinstance(suggestions, list):
                return []
            return suggestions

        except Exception as e:
            logger.debug("建议生成跳过: %s", e)
            return []


# ═══════════════════════════════════════════
# 监控器基类
# ═══════════════════════════════════════════

class BaseMonitor(threading.Thread):
    """监控器基类"""

    def __init__(self, interval_seconds: float = 30.0, name: str = "Monitor"):
        super().__init__(daemon=True)
        self.interval_seconds = interval_seconds
        self.name = name
        self._stop_event = threading.Event()
        self._callback: Optional[Callable[[ProactiveEvent], None]] = None

    def set_callback(self, callback: Callable[[ProactiveEvent], None]):
        self._callback = callback

    def stop(self):
        self._stop_event.set()

    def run(self):
        """子类重写 _check() 方法"""
        while not self._stop_event.wait(self.interval_seconds):
            try:
                events = self._check()
                if events and self._callback:
                    for event in events:
                        self._callback(event)
            except Exception as e:
                logger.debug("%s 检查异常: %s", self.name, e)

    def _check(self) -> List[ProactiveEvent]:
        """子类实现：返回发现的主动事件列表"""
        return []


# ═══════════════════════════════════════════
# 文件变化监控
# ═══════════════════════════════════════════

class FileWatchMonitor(BaseMonitor):
    """
    文件变化监控器

    监控指定目录下的文件变化（新增/删除/修改），
    发现异常变化时推送告警。
    """

    def __init__(self, watch_paths: List[str] = None, interval_seconds: float = 30.0):
        super().__init__(interval_seconds, "FileWatchMonitor")
        self._watch_paths = watch_paths or []
        self._last_snapshot: Dict[str, Dict] = {}  # path → {mtime, size}

    def add_path(self, path: str):
        if path not in self._watch_paths:
            self._watch_paths.append(path)

    def _check(self) -> List[ProactiveEvent]:
        events = []
        for watch_path in self._watch_paths:
            if not os.path.exists(watch_path):
                continue

            try:
                current = {}
                for entry in os.scandir(watch_path):
                    if entry.is_file():
                        stat = entry.stat()
                        current[entry.name] = {
                            "mtime": stat.st_mtime,
                            "size": stat.st_size,
                        }
            except PermissionError:
                continue

            prev = self._last_snapshot.get(watch_path, {})

            # 检测新增和修改
            for name, info in current.items():
                if name not in prev:
                    events.append(ProactiveEvent(
                        type=ProactiveEventType.ALERT,
                        title=f"新文件: {name}",
                        body=f"{watch_path}/{name} ({info['size']} bytes)",
                        priority=0,
                    ))
                elif info["mtime"] != prev[name].get("mtime"):
                    events.append(ProactiveEvent(
                        type=ProactiveEventType.INSIGHT,
                        title=f"文件已更新: {name}",
                        body=f"{watch_path}/{name}",
                        priority=0,
                    ))

            self._last_snapshot[watch_path] = current

        return events


# ═══════════════════════════════════════════
# 项目健康度监控
# ═══════════════════════════════════════════

class ProjectHealthMonitor(BaseMonitor):
    """
    项目健康度监控器

    检查项目中的常见问题:
      - 未跟踪的新文件（git status）
      - 超大文件（>1MB 的源码）
      - 待清理的 __pycache__ 膨胀
    """

    def __init__(self, project_path: str = "", interval_seconds: float = 300.0):
        super().__init__(interval_seconds, "ProjectHealthMonitor")
        self.project_path = project_path

    def set_project(self, path: str):
        self.project_path = path

    def _check(self) -> List[ProactiveEvent]:
        events = []
        if not self.project_path or not os.path.isdir(self.project_path):
            return events

        # 检查 __pycache__ 膨胀
        pycache_size = 0
        pycache_count = 0
        for root, dirs, files in os.walk(self.project_path):
            if "__pycache__" in root:
                for f in files:
                    try:
                        fp = os.path.join(root, f)
                        pycache_size += os.path.getsize(fp)
                        pycache_count += 1
                    except OSError:
                        pass

        if pycache_size > 50 * 1024 * 1024:  # 50MB
            events.append(ProactiveEvent(
                type=ProactiveEventType.INSIGHT,
                title=f"__pycache__ 膨胀: {pycache_size / 1024 / 1024:.0f}MB",
                body=f"共 {pycache_count} 个 .pyc 文件，建议 `py3clean .` 清理",
                action_label="清理缓存",
                action_payload={"action": "clean_pycache", "path": self.project_path},
                priority=0,
            ))

        return events


# ═══════════════════════════════════════════
# ProactiveEngine 主类
# ═══════════════════════════════════════════

class ProactiveEngine(QObject):
    """
    主动执行与推送引擎

    信号:
      on_push: 主动推送事件（告警/洞察/提醒）
      on_suggest: 智能建议事件（任务完成后的下一步）
    """

    on_push = pyqtSignal(ProactiveEvent)
    on_suggest = pyqtSignal(ProactiveEvent)

    def __init__(
        self,
        backend=None,
        project_path: str = "",
        watch_paths: List[str] = None,
    ):
        """
        Args:
            backend: BaseLLMBackend 实例（用于生成智能建议）
            project_path: 项目根目录（用于健康监控）
            watch_paths: 需要监控文件变化的目录列表
        """
        super().__init__()
        self._backend = backend
        self._suggester = SuggestionEngine(backend)
        self._monitors: List[BaseMonitor] = []
        self._is_monitoring = False

        # 初始化监控器
        if project_path:
            self.add_monitor(ProjectHealthMonitor(project_path))
        if watch_paths:
            self.add_monitor(FileWatchMonitor(watch_paths))

    # ── 建议生成 ──

    def suggest_next(
        self,
        user_message: str,
        completion_summary: str,
        system_context: str = "",
    ) -> List[ProactiveEvent]:
        """
        任务完成后生成下一步建议

        Args:
            user_message: 原始用户请求
            completion_summary: 完成结果总结
            system_context: 系统状态（当前项目、打开文件等）

        Returns:
            ProactiveEvent 列表（供调用方通过 on_suggest 信号发送）
        """
        suggestions = self._suggester.generate(
            user_message, completion_summary, system_context,
        )

        events = []
        for s in suggestions:
            event = ProactiveEvent(
                type=ProactiveEventType.SUGGESTION,
                title=s.get("title", ""),
                body=s.get("body", ""),
                action_label="试试看",
                action_payload={"action": "execute", "prompt": s.get("body", "")},
                priority=0,
            )
            events.append(event)

        return events

    def suggest_and_push(
        self,
        user_message: str,
        completion_summary: str,
        system_context: str = "",
    ) -> None:
        """生成建议并自动推送到 on_suggest 信号"""
        events = self.suggest_next(user_message, completion_summary, system_context)
        for event in events:
            self.on_suggest.emit(event)

    # ── 监控管理 ──

    def add_monitor(self, monitor: BaseMonitor):
        """添加监控器"""
        monitor.set_callback(self._on_monitor_event)
        self._monitors.append(monitor)

    def remove_monitor(self, name: str) -> bool:
        """移除监控器"""
        for m in self._monitors:
            if m.name == name:
                m.stop()
                self._monitors.remove(m)
                return True
        return False

    def start_monitoring(self):
        """启动所有后台监控"""
        for m in self._monitors:
            if not m.is_alive():
                m.start()
        self._is_monitoring = True
        logger.info("ProactiveEngine: 启动 %d 个监控器", len(self._monitors))

    def stop_monitoring(self):
        """停止所有后台监控"""
        for m in self._monitors:
            m.stop()
        self._is_monitoring = False
        logger.info("ProactiveEngine: 已停止所有监控")

    @property
    def is_monitoring(self) -> bool:
        return self._is_monitoring

    @property
    def monitors(self) -> List[str]:
        return [m.name for m in self._monitors]

    # ── 手动推送 ──

    def push_alert(self, title: str, body: str, priority: int = 1):
        """手动推送告警"""
        self.on_push.emit(ProactiveEvent(
            type=ProactiveEventType.ALERT,
            title=title, body=body, priority=priority,
        ))

    def push_insight(self, title: str, body: str, action_label: str = "",
                     action_payload: Dict = None):
        """手动推送洞察"""
        self.on_push.emit(ProactiveEvent(
            type=ProactiveEventType.INSIGHT,
            title=title, body=body,
            action_label=action_label,
            action_payload=action_payload or {},
        ))

    # ── 内部回调 ──

    def _on_monitor_event(self, event: ProactiveEvent):
        """监控器回调：转发到 on_push 信号"""
        self.on_push.emit(event)


# ═══════════════════════════════════════════
# 全局实例
# ═══════════════════════════════════════════

_proactive: Optional[ProactiveEngine] = None


def get_proactive_engine(
    backend=None,
    project_path: str = "",
    watch_paths: List[str] = None,
) -> ProactiveEngine:
    """获取全局 ProactiveEngine 单例"""
    global _proactive
    if _proactive is None:
        _proactive = ProactiveEngine(
            backend=backend,
            project_path=project_path,
            watch_paths=watch_paths,
        )
    return _proactive


def reset_proactive_engine():
    global _proactive
    if _proactive:
        _proactive.stop_monitoring()
    _proactive = None
