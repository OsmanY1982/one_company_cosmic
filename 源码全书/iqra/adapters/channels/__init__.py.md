# `iqra/adapters/channels/__init__.py`

> 路径：`iqra/adapters/channels/__init__.py` | 行数：314


---


```python
"""
多频道接入管理器 — Multi-Channel Adapter Hub

统一管理 Telegram、Discord、Slack、钉钉、飞书等 IM 频道的生命周期：
注册、启动、停止、消息收发、广播。

统一消息格式:
    IncomingMessage  — 入站消息（从 IM 收到）
    OutgoingMessage — 出站消息（发往 IM）

用法:
    manager = ChannelManager()
    manager.register_channel("telegram", TelegramAdapter())
    manager.start_channel("telegram")
    manager.broadcast(OutgoingMessage(text="Hello"))
"""

import logging
import threading
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# ── 统一消息格式 ──

@dataclass
class IncomingMessage:
    """入站消息 — 从 IM 频道收到的标准化消息"""
    channel: str                        # 频道名称: telegram / discord / slack / dingtalk / feishu
    user_id: str                        # 发送者 ID
    user_name: str = ""                 # 发送者显示名
    text: str = ""                      # 消息文本
    chat_id: str = ""                   # 会话/群组 ID
    attachments: List[Dict[str, str]] = field(default_factory=list)  # [{"type": "image", "url": "...", "path": "..."}]
    timestamp: float = 0.0              # Unix 时间戳

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().timestamp()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "IncomingMessage":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class OutgoingMessage:
    """出站消息 — 发往 IM 频道的标准化消息"""
    text: str = ""                      # 消息文本
    attachments: List[Dict[str, str]] = field(default_factory=list)  # [{"type": "image", "path": "..."}]
    reply_to: Optional[str] = None      # 回复的消息 ID

    def to_dict(self) -> dict:
        return asdict(self)


# ── 适配器接口 ──

class BaseChannelAdapter:
    """
    频道适配器基类 — 所有 IM 适配器必须实现此接口。

    每个子类代表一个 IM 平台的具体接入实现。
    属性:
        channel_name: str  — 频道唯一名称，子类必须覆盖
        is_running: bool   — 是否正在监听
    """
    channel_name: str = "__base__"

    def __init__(self):
        self.is_running = False
        self._message_callback: Optional[Callable[[IncomingMessage], None]] = None

    def set_callback(self, callback: Callable[[IncomingMessage], None]) -> None:
        """设置消息回调 — 收到消息时调用 callback(msg)"""
        self._message_callback = callback

    def start(self) -> bool:
        """启动频道监听（polling / WebSocket / webhook）"""
        raise NotImplementedError

    def stop(self) -> bool:
        """停止频道监听"""
        raise NotImplementedError

    def send_message(self, target_id: str, message: OutgoingMessage) -> bool:
        """
        发送消息到指定目标。
        target_id: 对于 Telegram 是 chat_id，Discord 是 channel_id 等。
        """
        raise NotImplementedError

    def send_photo(self, target_id: str, image_path: str, caption: str = "") -> bool:
        """
        发送图片到指定目标。
        默认降级为 send_message 中附带图片路径文本。
        """
        return self.send_message(target_id, OutgoingMessage(
            text=f"[图片] {caption}\n{image_path}" if caption else f"[图片] {image_path}"
        ))

    def _notify(self, msg: IncomingMessage) -> None:
        """通知上层回调"""
        if self._message_callback:
            try:
                self._message_callback(msg)
            except Exception as e:
                logger.error(f"[{self.channel_name}] 消息回调异常: {e}")


# ── 频道注册信息 ──

@dataclass
class ChannelInfo:
    """频道运行时信息"""
    name: str
    adapter: BaseChannelAdapter
    started_at: Optional[float] = None
    message_count: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def is_running(self) -> bool:
        return self.adapter.is_running

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "is_running": self.is_running,
            "started_at": self.started_at,
            "message_count": self.message_count,
        }


# ── ChannelManager ──

class ChannelManager:
    """
    频道管理器 — 多频道生命周期管理中心。

    职责:
    - 注册/注销频道适配器
    - 启动/停止各频道
    - 消息分发与广播
    - 线程安全的并发管理
    """

    def __init__(self):
        self._channels: Dict[str, ChannelInfo] = {}
        self._lock = threading.Lock()

    # ── 注册 ──

    def register_channel(self, channel_name: str, adapter: BaseChannelAdapter) -> bool:
        """注册一个频道适配器"""
        adapter.channel_name = channel_name
        with self._lock:
            if channel_name in self._channels:
                logger.warning(f"频道 {channel_name} 已注册，将被覆盖")
            self._channels[channel_name] = ChannelInfo(name=channel_name, adapter=adapter)
        logger.info(f"频道 {channel_name} 已注册")
        return True

    def unregister_channel(self, channel_name: str) -> bool:
        """注销一个频道"""
        with self._lock:
            info = self._channels.pop(channel_name, None)
        if info and info.is_running:
            info.adapter.stop()
        if info:
            logger.info(f"频道 {channel_name} 已注销")
            return True
        return False

    def get_adapter(self, channel_name: str) -> Optional[BaseChannelAdapter]:
        """获取频道适配器实例"""
        info = self._channels.get(channel_name)
        return info.adapter if info else None

    # ── 启停 ──

    def start_channel(self, channel_name: str, callback: Optional[Callable] = None) -> bool:
        """启动指定频道的消息监听"""
        info = self._channels.get(channel_name)
        if not info:
            logger.error(f"频道 {channel_name} 未注册")
            return False

        if info.is_running:
            logger.warning(f"频道 {channel_name} 已在运行")
            return True

        if callback:
            info.adapter.set_callback(callback)

        try:
            ok = info.adapter.start()
            if ok:
                info.started_at = datetime.now().timestamp()
                logger.info(f"频道 {channel_name} 已启动")
            return ok
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            info.errors.append(err)
            logger.error(f"启动频道 {channel_name} 失败: {err}")
            return False

    def stop_channel(self, channel_name: str) -> bool:
        """停止指定频道"""
        info = self._channels.get(channel_name)
        if not info:
            logger.error(f"频道 {channel_name} 未注册")
            return False

        if not info.is_running:
            return True

        try:
            ok = info.adapter.stop()
            logger.info(f"频道 {channel_name} 已停止")
            return ok
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            info.errors.append(err)
            logger.error(f"停止频道 {channel_name} 失败: {err}")
            return False

    def start_all(self, callback: Optional[Callable] = None) -> Dict[str, bool]:
        """启动所有已注册频道"""
        results = {}
        with self._lock:
            names = list(self._channels.keys())
        for name in names:
            results[name] = self.start_channel(name, callback=callback)
        return results

    def stop_all(self) -> Dict[str, bool]:
        """停止所有频道"""
        results = {}
        with self._lock:
            names = list(self._channels.keys())
        for name in names:
            results[name] = self.stop_channel(name)
        return results

    # ── 消息 ──

    def send_message(self, channel_name: str, target_id: str,
                     message: OutgoingMessage) -> bool:
        """向指定频道的指定目标发送消息"""
        adapter = self.get_adapter(channel_name)
        if not adapter:
            logger.error(f"频道 {channel_name} 未注册")
            return False
        try:
            return adapter.send_message(target_id, message)
        except Exception as e:
            logger.error(f"向 {channel_name}/{target_id} 发送消息失败: {e}")
            return False

    def broadcast(self, message: OutgoingMessage,
                  channels: Optional[List[str]] = None,
                  target_id: str = "") -> Dict[str, bool]:
        """
        向指定频道（或所有活跃频道）广播消息。

        channels=None 时广播到所有 running 状态的频道。
        target_id 为空时使用适配器默认目标。
        """
        results = {}
        with self._lock:
            info_list = list(self._channels.values())

        for info in info_list:
            if channels and info.name not in channels:
                continue
            if not info.is_running:
                continue
            results[info.name] = self.send_message(info.name, target_id or "broadcast", message)

        return results

    # ── 状态 ──

    def get_status(self) -> Dict[str, dict]:
        """获取所有频道的运行状态"""
        with self._lock:
            return {name: info.to_dict() for name, info in self._channels.items()}

    def list_channels(self) -> List[str]:
        """列出所有已注册频道名"""
        with self._lock:
            return list(self._channels.keys())

    def list_running(self) -> List[str]:
        """列出所有正在运行的频道名"""
        with self._lock:
            return [name for name, info in self._channels.items() if info.is_running]

    @property
    def registered_count(self) -> int:
        with self._lock:
            return len(self._channels)

    @property
    def running_count(self) -> int:
        with self._lock:
            return sum(1 for info in self._channels.values() if info.is_running)

```
