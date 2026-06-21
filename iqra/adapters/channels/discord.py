"""
Discord Bot 适配器

使用 discord.py 库接入 Discord Gateway API (WebSocket)。
支持接收消息（需 MESSAGE_CONTENT 特权意图）、发送文本和图片。

环境变量:
    DISCORD_BOT_TOKEN — Bot Token（从 Discord Developer Portal 获取）

依赖（可选）:
    discord.py>=2.0
"""

from __future__ import annotations

import logging
import os
import asyncio
import threading
from typing import Callable, Optional

from iqra.adapters.channels import (
    BaseChannelAdapter,
    IncomingMessage,
    OutgoingMessage,
)

logger = logging.getLogger(__name__)

_HAS_DISCORD = False

try:
    import discord
    from discord.ext import commands
    _HAS_DISCORD = True
except ImportError:
    pass


class DiscordAdapter(BaseChannelAdapter):
    """
    Discord Bot 适配器。

    用法:
        adapter = DiscordAdapter()
        adapter.set_callback(lambda msg: print(f"收到: {msg.text}"))
        adapter.start()
        adapter.send_message(channel_id, OutgoingMessage(text="Hello"))
    """

    channel_name = "discord"

    def __init__(self, token: Optional[str] = None):
        super().__init__()
        self._token = token or os.getenv("DISCORD_BOT_TOKEN", "")
        self._bot: Optional[commands.Bot] = None
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None

    # ── 启动 / 停止 ──

    def start(self) -> bool:
        if not _HAS_DISCORD:
            logger.warning("discord.py 未安装，Discord 适配器不可用")
            return False

        if not self._token:
            logger.warning("DISCORD_BOT_TOKEN 未设置，Discord 适配器不可用")
            return False

        if self.is_running:
            return True

        try:
            intents = discord.Intents.default()
            intents.message_content = True
            intents.guild_messages = True

            self._bot = commands.Bot(command_prefix="!", intents=intents)

            @self._bot.event
            async def on_ready():
                logger.info(f"Discord Bot 已登录: {self._bot.user}")

            @self._bot.event
            async def on_message(message: discord.Message):
                if message.author == self._bot.user:
                    return
                self._handle_message(message)

            self._event_loop = asyncio.new_event_loop()
            self._thread = threading.Thread(
                target=self._run_bot,
                daemon=True,
                name="discord-bot",
            )
            self._thread.start()
            self.is_running = True
            return True

        except Exception as e:
            logger.error(f"启动 Discord Bot 失败: {e}")
            self.is_running = False
            return False

    def stop(self) -> bool:
        if not self._bot:
            self.is_running = False
            return True

        try:
            async def _close():
                await self._bot.close()

            if self._event_loop and self._event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(_close(), self._event_loop)
                future.result(timeout=10)
            self.is_running = False
            logger.info("Discord Bot 已停止")
            return True
        except Exception as e:
            logger.error(f"停止 Discord Bot 失败: {e}")
            self.is_running = False
            return False

    def _run_bot(self) -> None:
        """在独立线程中运行 Discord Bot"""
        asyncio.set_event_loop(self._event_loop)
        try:
            self._event_loop.run_until_complete(self._bot.start(self._token))
        except discord.LoginFailure:
            logger.error("Discord Token 无效")
        except Exception as e:
            if self.is_running:
                logger.error(f"Discord Bot 运行异常: {e}")

    # ── 消息处理 ──

    def _handle_message(self, message) -> None:
        """处理接收到的 Discord 消息"""
        if not message.content:
            return

        msg = IncomingMessage(
            channel="discord",
            user_id=str(message.author.id),
            user_name=f"{message.author.name}#{message.author.discriminator}"
                       if message.author.discriminator != "0"
                       else message.author.name,
            text=message.content,
            chat_id=str(message.channel.id),
        )

        # 处理附件
        for attachment in message.attachments:
            att = {"type": attachment.content_type or "file", "url": attachment.url}
            if attachment.filename:
                att["filename"] = attachment.filename
            msg.attachments.append(att)

        self._notify(msg)

    # ── 发送 ──

    def send_message(self, target_id: str, message: OutgoingMessage) -> bool:
        """
        发送文本消息到指定 Discord 频道。

        target_id: Discord channel_id（数字字符串）
        """
        if not self._bot:
            logger.warning("Discord Bot 未启动，无法发送消息")
            return False

        try:
            async def _send():
                channel = self._bot.get_channel(int(target_id))
                if not channel:
                    channel = await self._bot.fetch_channel(int(target_id))
                if not channel:
                    raise ValueError(f"未找到频道: {target_id}")

                # Discord 消息最长 2000 字符
                text = message.text[:2000]
                await channel.send(text)

            self._run_async(_send())
            return True
        except Exception as e:
            logger.error(f"Discord 发送消息失败: {e}")
            return False

    def send_photo(self, target_id: str, image_path: str, caption: str = "") -> bool:
        """发送图片到指定 Discord 频道"""
        if not self._bot:
            return False

        if not os.path.exists(image_path):
            logger.error(f"图片不存在: {image_path}")
            return False

        try:
            async def _send():
                channel = self._bot.get_channel(int(target_id))
                if not channel:
                    channel = await self._bot.fetch_channel(int(target_id))
                file = discord.File(image_path)
                await channel.send(content=caption or None, file=file)

            self._run_async(_send())
            return True
        except Exception as e:
            logger.error(f"Discord 发送图片失败: {e}")
            return False

    def _run_async(self, coro):
        """安全地在事件循环中运行协程"""
        if self._event_loop and self._event_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(coro, self._event_loop)
            future.result(timeout=30)
        else:
            asyncio.run(coro)
