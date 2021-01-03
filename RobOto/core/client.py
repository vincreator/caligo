import logging
import signal

from pyrogram import Client, asyncio, idle
from typing import Optional, Any, Awaitable, List
from . import pool
from ..util import Config


LOG = logging.getLogger(__name__)

INIT_TASKS: List[asyncio.Task] = []


class Roboto(Client):
    "RobOto, client"

    def __init__(self, **kawrgs) -> None:
        LOG.info("Setting up RobOto...")
        kwargs = {
            "api_id": Config.API_ID,
            "api_hash": Config.API_HASH,
            "session_name": Config.STRING_SESSION or ":memory:"
        }
        super().__init__(**kwargs)

    async def start(self) -> None:
        """ Start client """
        pool.start()
        LOG.info("Starting RobOto userbot...")
        await super().start()

    async def stop(self) -> None:
        """ Stop client """
        LOG.info("Stopping RobOto userbot...")
        await super().stop()
        await pool.stop()

    def go(self, coro: Optional[Awaitable[Any]] = None) -> None:
        """ Start RobOto """

        lock = asyncio.Lock()
        tasks: List[asyncio.Task] = []

        async def finalized() -> None:
            async with lock:
                for task in tasks:
                    task.cancel()
                if self.is_initialized:
                    await self.stop()
                [t.cancel() for t in asyncio.all_tasks() if t is not asyncio.current_task()]
                await self.loop.shutdown_asyncgens()
                self.loop.stop()
                LOG.info("Loop stopped")

        async def shutdown(sig: signal.Signals) -> None:
            LOG.info(f"Received Stop Signal [{sig.name}], Exiting...")
            await finalized()

        for sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
            self.loop.add_signal_handler(
                sig, lambda sig=sig: self.loop.create_task(shutdown(sig)))

        self.loop.run_until_complete(self.start())

#        for task in self._tasks:
#            tasks.append(self.loop.create_task(task()))
        try:
            if coro:
                LOG.info("Running Coroutine")
                self.loop.run_until_complete(coro)
            else:
                LOG.info("Idling")
                idle()
            self.loop.run_until_complete(finalized())
        except (asyncio.exceptions.CancelledError, RuntimeError):
            pass
        finally:
            self.loop.close()
            LOG.info("Loop closed")
