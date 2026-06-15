"""
消息路由引擎 — MessageRouter

接收所有频道的入站消息，统一路由到 ChatEngine。
支持频道级限流、白名单/黑名单用户、独立会话上下文。

职责:
    1. 多频道并发消息聚合
    2. 频道级速率限制 (Rate Limiting)
    3. 用户级权限控制 (白名单 / 黑名单)
    4. 会话上下文保持 (per chat_id)
    5. 消息分发到 ChatEngine
"""

import logging
import threading
import time
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

from opcclaw.adapters.channels import (
    ChannelManager,
    IncomingMessage,
    OutgoingMessage,
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    滑动窗口速率限制器 — 按 key 独立计数。

    用法:
        limiter = RateLimiter(max_per_window=10, window_seconds=10)
        if limiter.allow("user_123"):
            process()
    """

    def __init__(self, max_per_window: int = 10, window_seconds: float = 10.0):
        self._max = max_per_window
        self._window = window_seconds
        self._buckets: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        """检查是否允许此次请求"""
        now = time.time()
        with self._lock:
            bucket = self._buckets[key]
            # 清理过期记录
            cutoff = now - self._window
            bucket[:] = [t for t in bucket if t > cutoff]
            if len(bucket) >= self._max:
                return False
            bucket.append(now)
            return True

    def reset(self, key: str) -> None:
        with self._lock:
            self._buckets.pop(key, None)


class AccessControl:
    """
    用户级权限控制。

    模式:
        mode="allowlist"  — 仅白名单用户可交互
        mode="blocklist"  — 黑名单用户被拒绝
        mode=None         — 不限制
    """

    def __init__(self, mode: Optional[str] = None,
                 allowlist: Optional[List[str]] = None,
                 blocklist: Optional[List[str]] = None):
        self.mode = mode
        self.allowlist: set = set(allowlist or [])
        self.blocklist: set = set(blocklist or [])

    def is_allowed(self, user_id: str) -> bool:
        if not self.mode:
            return True
        if self.mode == "allowlist":
            return user_id in self.allowlist
        if self.mode == "blocklist":
            return user_id not in self.blocklist
        return True

    def set_allowlist(self, users: List[str]) -> None:
        self.mode = "allowlist"
        self.allowlist = set(users)

    def set_blocklist(self, users: List[str]) -> None:
        self.mode = "blocklist"
        self.blocklist = set(users)

    def clear(self) -> None:
        self.mode = None
        self.allowlist.clear()
        self.blocklist.clear()


class SessionContext:
    """
    会话上下文 — 每个 chat_id 维护独立的对话上下文。

    用于保持多轮对话时的上下文连续性。
    """

    def __init__(self, chat_id: str, channel: str):
        self.chat_id = chat_id
        self.channel = channel
        self.history: List[dict] = []         # [{"role": "user"/"assistant", "content": "..."}]
        self.metadata: Dict[str, Any] = {}
        self.created_at = time.time()
        self.last_active = time.time()

    def add_message(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})
        self.last_active = time.time()
        # 保留最近 50 条历史，避免无限增长
        if len(self.history) > 50:
            self.history = self.history[-50:]

    def touch(self) -> None:
        self.last_active = time.time()

    def is_expired(self, ttl_seconds: float = 3600.0) -> bool:
        return (time.time() - self.last_active) > ttl_seconds

    def to_dict(self) -> dict:
        return {
            "chat_id": self.chat_id,
            "channel": self.channel,
            "history_length": len(self.history),
            "created_at": self.created_at,
            "last_active": self.last_active,
        }


class MessageRouter:
    """
    消息路由引擎 — 多频道消息统一分发中心。

    架构:
        IM → Adapter → Router → ChatEngine → Router → Adapter → IM
                              ↑
                         [RateLimiter]
                         [AccessControl]
                         [SessionContext]

    用法:
        router = MessageRouter(manager)
        router.set_handler(lambda msg: generate_reply(msg))
        router.start("telegram")
    """

    def __init__(self, channel_manager: ChannelManager,
                 rate_limit_per_channel: int = 10,
                 rate_limit_window: float = 10.0):
        self._manager = channel_manager
        self._rate_limiters: Dict[str, RateLimiter] = {}
        self._access_controls: Dict[str, AccessControl] = {}
        self._sessions: Dict[str, SessionContext] = defaultdict(
            lambda: None  # lazy init
        )
        self._handler: Optional[Callable[[IncomingMessage], Optional[OutgoingMessage]]] = None
        self._lock = threading.Lock()

        # 默认限流参数
        self._default_rate_limit = rate_limit_per_channel
        self._default_window = rate_limit_window

    # ── 处理器 ──

    def set_handler(self, handler: Callable[[IncomingMessage], Optional[OutgoingMessage]]) -> None:
        """
        设置消息处理器 — 每个入站消息都会调用 handler。

        handler 签名: (IncomingMessage) -> Optional[OutgoingMessage]
        返回 None 表示不回复。
        """
        self._handler = handler

    # ── 会话 ──

    def get_session(self, chat_id: str, channel: str = "") -> SessionContext:
        """获取或创建会话上下文"""
        key = f"{channel}:{chat_id}" if channel else chat_id
        with self._lock:
            session = self._sessions.get(key)
            if session is None or session.is_expired():
                session = SessionContext(chat_id, channel)
                self._sessions[key] = session
            else:
                session.touch()
            return session

    def clear_session(self, chat_id: str, channel: str = "") -> None:
        """清除指定会话"""
        key = f"{channel}:{chat_id}" if channel else chat_id
        with self._lock:
            self._sessions.pop(key, None)

    def list_sessions(self) -> List[dict]:
        """列出所有活跃会话"""
        with self._lock:
            return [s.to_dict() for s in self._sessions.values() if not s.is_expired()]

    # ── 限流 ──

    def get_rate_limiter(self, channel_name: str) -> RateLimiter:
        """获取频道级限流器"""
        if channel_name not in self._rate_limiters:
            self._rate_limiters[channel_name] = RateLimiter(
                max_per_window=self._default_rate_limit,
                window_seconds=self._default_window,
            )
        return self._rate_limiters[channel_name]

    def set_rate_limit(self, channel_name: str, max_per_window: int,
                       window_seconds: float = 10.0) -> None:
        """设置频道限流参数"""
        self._rate_limiters[channel_name] = RateLimiter(
            max_per_window=max_per_window,
            window_seconds=window_seconds,
        )

    # ── 权限 ──

    def get_access_control(self, channel_name: str) -> AccessControl:
        """获取频道级访问控制"""
        if channel_name not in self._access_controls:
            self._access_controls[channel_name] = AccessControl()
        return self._access_controls[channel_name]

    def set_allowlist(self, channel_name: str, users: List[str]) -> None:
        self.get_access_control(channel_name).set_allowlist(users)

    def set_blocklist(self, channel_name: str, users: List[str]) -> None:
        self.get_access_control(channel_name).set_blocklist(users)

    # ── 启动 / 停止 ──

    def start(self, channel_name: str) -> bool:
        """
        启动指定频道的消息监听（自动注册路由回调）。

        回调链路:
            Adapter 收到消息 → _on_message → 限流/权限 → handler → reply
        """
        return self._manager.start_channel(channel_name, callback=self._on_message)

    def start_all(self) -> Dict[str, bool]:
        """启动所有已注册频道的监听"""
        return self._manager.start_all(callback=self._on_message)

    def stop(self, channel_name: str) -> bool:
        return self._manager.stop_channel(channel_name)

    def stop_all(self) -> Dict[str, bool]:
        return self._manager.stop_all()

    # ── 路由核心 ──

    def _on_message(self, msg: IncomingMessage) -> None:
        """
        消息路由入口 — 处理入站消息的完整流水线:

        1. 权限检查
        2. 限流检查
        3. 会话上下文记录
        4. 分发到 handler
        5. 回复路由回频道
        """
        channel = msg.channel

        # 1. 权限
        ac = self.get_access_control(channel)
        if not ac.is_allowed(msg.user_id):
            logger.info(f"用户 {msg.user_id} 被 {channel} 频道拦截（权限控制）")
            return

        # 2. 限流
        limiter = self.get_rate_limiter(channel)
        if not limiter.allow(msg.user_id):
            logger.info(f"用户 {msg.user_id} 在 {channel} 频道触发限流")
            return

        # 3. 会话上下文
        session = self.get_session(msg.chat_id, channel)
        session.add_message("user", msg.text)

        # 4. 分发
        if not self._handler:
            logger.warning("MessageRouter 未设置 handler，消息被丢弃")
            return

        try:
            reply = self._handler(msg)
        except Exception as e:
            logger.error(f"消息处理器异常: {e}")
            return

        # 5. 回复
        if reply:
            session.add_message("assistant", reply.text)
            adapter = self._manager.get_adapter(channel)
            if adapter:
                target = msg.chat_id
                try:
                    adapter.send_message(target, reply)
                except Exception as e:
                    logger.error(f"回复发送失败 ({channel}/{target}): {e}")

    # ── 状态 ──

    def get_status(self) -> dict:
        """获取路由引擎状态摘要"""
        return {
            "channels": self._manager.get_status(),
            "sessions": len(self.list_sessions()),
            "registered_channels": self._manager.registered_count,
            "running_channels": self._manager.running_count,
        }
