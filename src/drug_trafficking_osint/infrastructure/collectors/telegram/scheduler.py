"""Scheduler for periodic Telegram collection."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timedelta

from drug_trafficking_osint.infrastructure.collectors.telegram.client import TelegramClient
from drug_trafficking_osint.infrastructure.collectors.telegram.collector import (
    MessageSink,
    TelegramCollector,
)
from drug_trafficking_osint.infrastructure.collectors.telegram.filters import MessageFilter
from drug_trafficking_osint.infrastructure.collectors.telegram.models import UnifiedMessage


@dataclass
class CollectionJob:
    """A scheduled collection job."""

    channel: str
    interval: timedelta
    filter_config: MessageFilter
    limit: int = 100
    callback: Callable[[list[UnifiedMessage]], None] | None = None
    last_run: datetime | None = None
    next_run: datetime | None = None

    def __post_init__(self) -> None:
        if self.next_run is None:
            self.next_run = datetime.now()


class TelegramScheduler:
    """Schedule periodic collection from Telegram channels."""

    def __init__(self, client: TelegramClient, sink: MessageSink | None = None) -> None:
        self._client = client
        self._collector = TelegramCollector(client, sink=sink)
        self._jobs: list[CollectionJob] = []
        self._running = False
        self._task: asyncio.Task[None] | None = None

    def add_job(self, job: CollectionJob) -> None:
        """Add a collection job to the schedule."""
        self._jobs.append(job)

    def remove_job(self, channel: str) -> bool:
        """Remove a job by channel name."""
        for i, job in enumerate(self._jobs):
            if job.channel == channel:
                self._jobs.pop(i)
                return True
        return False

    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def _run_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            now = datetime.now()
            for job in self._jobs:
                if job.next_run and now >= job.next_run:
                    await self._run_job(job)
                    job.last_run = now
                    job.next_run = now + job.interval

            await asyncio.sleep(60)  # Check every minute

    async def _run_job(self, job: CollectionJob) -> None:
        """Execute a collection job."""
        try:
            messages = self._collector.collect_channel(
                job.channel,
                limit=job.limit,
            )
            message_list = [msg async for msg in messages]

            if job.callback:
                job.callback(message_list)

        except Exception as e:
            # Log error but don't stop scheduler
            print(f"Collection job failed for {job.channel}: {e}")
