"""
Telegram Bot 适配器

使用 python-telegram-bot 库接入 Telegram Bot API。
支持长轮询 (polling) 模式接收消息，发送文本和图片。

环境变量:
    TELEGRAM_BOT_TOKEN — Bot Token（从 @BotFather 获取）

依赖（可选）:
    python-telegram-bot>=20.0
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

_HAS_TELEGRAM = False
_Application = None
_ext = None

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    from telegram.constants import ParseMode
    _HAS_TELEGRAM = True
except ImportError:
    pass


class TelegramAdapter(BaseChannelAdapter):
    """
    Telegram Bot 适配器。

    用法:
        adapter = TelegramAdapter()
        adapter.set_callback(lambda msg: print(f"收到: {msg.text}"))
        adapter.start()
        adapter.send_message(chat_id, OutgoingMessage(text="Hello"))
    """

    channel_name = "telegram"

    def __init__(self, token: Optional[str] = None):
        super().__init__()
        self._token = token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self._app: Optional[Application] = None
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None

    # ── 启动 / 停止 ──

    def start(self) -> bool:
        if not _HAS_TELEGRAM:
            logger.warning("python-telegram-bot 未安装，Telegram 适配器不可用")
            return False

        if not self._token:
            logger.warning("TELEGRAM_BOT_TOKEN 未设置，Telegram 适配器不可用")
            return False

        if self.is_running:
            return True

        try:
            self._app = Application.builder().token(self._token).build()

            # 注册处理器
            self._app.add_handler(MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self._handle_message,
            ))
            self._app.add_handler(CommandHandler("start", self._handle_start))

            # 在独立线程中运行事件循环
            self._event_loop = asyncio.new_event_loop()
            self._thread = threading.Thread(
                target=self._run_polling,
                daemon=True,
                name="telegram-polling",
            )
            self._thread.start()
            self.is_running = True
            logger.info("Telegram Bot 已启动 polling")
            return True

        except Exception as e:
            logger.error(f"启动 Telegram Bot 失败: {e}")
            self.is_running = False
            return False

    def stop(self) -> bool:
        if not self._app:
            self.is_running = False
            return True

        try:
            async def _shutdown():
                if self._app:
                    await self._app.stop()
                    await self._app.shutdown()

            if self._event_loop and self._event_loop.is_running():
                self._event_loop.call_soon_threadsafe(
                    lambda: asyncio.ensure_future(_shutdown(), loop=self._event_loop)
                )
            self.is_running = False
            logger.info("Telegram Bot 已停止")
            return True
        except Exception as e:
            logger.error(f"停止 Telegram Bot 失败: {e}")
            self.is_running = False
            return False

    def _run_polling(self) -> None:
        """在独立线程的事件循环中运行 polling"""
        asyncio.set_event_loop(self._event_loop)
        try:
            self._app.run_polling(close_loop=False)
        except Exception as e:
            if self.is_running:
                logger.error(f"Telegram polling 异常: {e}")

    # ── 消息处理 ──

    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        if update.effective_chat:
            await update.message.reply_text(
                "你好！我是 iqra AI 助手。有什么可以帮你的？"
            )

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理普通文本消息"""
        if not update.message or not update.effective_user:
            return

        msg = IncomingMessage(
            channel="telegram",
            user_id=str(update.effective_user.id),
            user_name=update.effective_user.full_name or update.effective_user.username or "",
            text=update.message.text or "",
            chat_id=str(update.effective_chat.id) if update.effective_chat else "",
        )

        # 处理附件
        if update.message.photo:
            photo = update.message.photo[-1]  # 取最大分辨率
            msg.attachments.append({
                "type": "photo",
                "file_id": photo.file_id,
                "width": str(photo.width),
                "height": str(photo.height),
            })

        self._notify(msg)

    # ── 发送 ──

    def send_message(self, target_id: str, message: OutgoingMessage) -> bool:
        """
        发送文本消息到指定 chat_id。

        target_id: Telegram chat_id（支持负数表示群组）
        """
        if not self._app:
            logger.warning("Telegram Bot 未启动，无法发送消息")
            return False

        try:
            async def _send():
                await self._app.bot.send_message(
                    chat_id=int(target_id),
                    text=message.text,
                    parse_mode=ParseMode.HTML,
                    reply_to_message_id=int(message.reply_to) if message.reply_to else None,
                )

            self._run_async(_send())
            return True
        except Exception as e:
            logger.error(f"Telegram 发送消息失败: {e}")
            return False

    def send_photo(self, target_id: str, image_path: str, caption: str = "") -> bool:
        """
        发送图片到指定 chat_id。
        """
        if not self._app:
            logger.warning("Telegram Bot 未启动，无法发送图片")
            return False

        if not os.path.exists(image_path):
            logger.error(f"图片不存在: {image_path}")
            return False

        try:
            async def _send():
                await self._app.bot.send_photo(
                    chat_id=int(target_id),
                    photo=open(image_path, "rb"),
                    caption=caption or None,
                    parse_mode=ParseMode.HTML,
                )

            self._run_async(_send())
            return True
        except Exception as e:
            logger.error(f"Telegram 发送图片失败: {e}")
            return False

    def _run_async(self, coro):
        """在事件循环中安全地运行协程"""
        if self._event_loop and self._event_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(coro, self._event_loop)
            future.result(timeout=30)
        else:
            asyncio.run(coro)
