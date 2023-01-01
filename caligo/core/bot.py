import asyncio
import logging
from typing import Optional

import aiohttp
import pyrogram

from .command_dispatcher import CommandDispatcher
from .conversation_dispatcher import ConversationDispatcher
from .database_provider import DatabaseProvider
from .event_dispatcher import EventDispatcher
from .module_extender import ModuleExtender
from .telegram_bot import TelegramBot


class Bot(TelegramBot, CommandDispatcher, DatabaseProvider, EventDispatcher,
          ConversationDispatcher, ModuleExtender):
    client: pyrogram.Client
    http: aiohttp.ClientSession
    lock: asyncio.Lock
    log: logging.Logger
    loop: asyncio.AbstractEventLoop
    stop_manual: bool
    stopping: bool

    def __init__(self) -> None:
        self.log = logging.getLogger("Bot")
        self.loop = asyncio.get_event_loop()
        self.stop_manual = False
        self.stopping = False

        super().__init__()

        self.http = aiohttp.ClientSession()

    @classmethod
    async def create_and_run(cls,
                             *,
                             loop: Optional[asyncio.AbstractEventLoop] = None
                             ) -> "Bot":
        bot = None

        if loop:
            asyncio.set_event_loop(loop)

        try:
            bot = cls()
            await bot.run()
            return bot
        finally:
            if bot is None or not bot.stopping:
                asyncio.get_event_loop().stop()

    async def stop(self) -> None:
        self.stopping = True

        self.log.info("Stopping")
        if self.loaded:
            await self.dispatch_event("stop")
            if self.client.is_connected:
                if self.stop_manual:
                    await self.client.stop(block=False)
                else:
                    await self.client.stop()
        await self.http.close()
        await self.db.close()

        self.log.info("Running post-stop hooks")
        if self.loaded:
            await self.dispatch_event("stopped")
        self.loop.stop()
