"""Stream-processor entrypoint.

    python -m app.worker

Consumes from Redpanda/Kafka, runs the detection pipeline, persists to
Postgres, and fans out to Redis.  Deployed as its own container in
``docker-compose`` so ingestion/detection scales independently of the API.
"""

from __future__ import annotations

import asyncio
import contextlib
import signal

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.storage.db import dispose_engine
from app.storage.redis_client import close_redis, get_redis
from app.streaming.kafka import EventConsumer
from app.streaming.pipeline import Pipeline

log = get_logger("worker")


async def _gauge_refresher(pipeline: Pipeline, stop: asyncio.Event) -> None:
    import time

    while not stop.is_set():
        with contextlib.suppress(Exception):
            await pipeline.redis.set("siem:worker:heartbeat", str(time.time()), ex=30)
            await pipeline.refresh_active_alert_gauge()
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), timeout=10)


async def run() -> None:
    configure_logging()
    redis_client = get_redis()
    consumer = EventConsumer()
    pipeline = Pipeline(redis_client)
    stop = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop.set)

    log.info(
        "worker_starting",
        bootstrap=settings.kafka_bootstrap_servers,
        topic=settings.kafka_topic_events,
        group=settings.kafka_consumer_group,
    )
    await consumer.start()
    refresher = asyncio.create_task(_gauge_refresher(pipeline, stop))

    consumed = 0
    try:
        async for batch in consumer.batches():
            if stop.is_set():
                break
            try:
                await pipeline.process_batch(batch)
                await consumer.commit()
                consumed += len(batch)
                if consumed % 5000 < len(batch):
                    log.info("worker_progress", events_consumed=consumed)
            except Exception as exc:
                log.error("batch_failed", error=str(exc), batch_size=len(batch))
                await asyncio.sleep(1)
    finally:
        log.info("worker_stopping", events_consumed=consumed)
        stop.set()
        refresher.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await refresher
        await consumer.stop()
        await close_redis()
        await dispose_engine()
        log.info("worker_stopped")


def main() -> None:
    with contextlib.suppress(KeyboardInterrupt):  # pragma: no cover
        asyncio.run(run())


if __name__ == "__main__":
    main()
