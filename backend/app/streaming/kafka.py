"""Kafka / Redpanda client wrappers (aiokafka).

Redpanda speaks the Kafka protocol, so the same ``aiokafka`` producer and
consumer work unchanged against Redpanda or Apache Kafka — only
``SIEM_KAFKA_BOOTSTRAP_SERVERS`` changes.  Wrappers add: bounded retries with
backoff on connect, structured logging, and graceful shutdown.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import orjson
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("streaming.kafka")


class EventProducer:
    def __init__(self, bootstrap: str | None = None, topic: str | None = None) -> None:
        self.bootstrap = bootstrap or settings.kafka_bootstrap_servers
        self.topic = topic or settings.kafka_topic_events
        self._producer: AIOKafkaProducer | None = None

    @retry(
        retry=retry_if_exception_type(KafkaConnectionError),
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=0.5, max=10),
        reraise=True,
    )
    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap,
            client_id=f"{settings.kafka_client_id}-producer",
            value_serializer=lambda v: orjson.dumps(v),
            key_serializer=lambda k: k.encode() if isinstance(k, str) else k,
            acks="all",
            enable_idempotence=True,
            linger_ms=20,
            compression_type="gzip",
        )
        await self._producer.start()
        log.info("producer_started", bootstrap=self.bootstrap, topic=self.topic)

    async def send(self, value: dict, key: str | None = None) -> None:
        if self._producer is None:
            raise RuntimeError("producer not started")
        await self._producer.send_and_wait(self.topic, value=value, key=key)

    async def send_batch(self, values: list[tuple[str | None, dict]]) -> None:
        if self._producer is None:
            raise RuntimeError("producer not started")
        batch = self._producer.create_batch()
        pending: list[tuple[str | None, dict]] = []
        for key, value in values:
            metadata = batch.append(
                key=key.encode() if key else None,
                value=orjson.dumps(value),
                timestamp=None,
            )
            if metadata is None:  # batch full — flush and open a new one
                await self._producer.send_batch(batch, self.topic, partition=None)
                batch = self._producer.create_batch()
                batch.append(
                    key=key.encode() if key else None,
                    value=orjson.dumps(value),
                    timestamp=None,
                )
            pending.append((key, value))
        batch.close()
        await self._producer.send_batch(batch, self.topic, partition=None)

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            log.info("producer_stopped")
        self._producer = None


class EventConsumer:
    def __init__(
        self,
        *,
        bootstrap: str | None = None,
        topic: str | None = None,
        group_id: str | None = None,
    ) -> None:
        self.bootstrap = bootstrap or settings.kafka_bootstrap_servers
        self.topic = topic or settings.kafka_topic_events
        self.group_id = group_id or settings.kafka_consumer_group
        self._consumer: AIOKafkaConsumer | None = None
        self._stopping = asyncio.Event()

    @retry(
        retry=retry_if_exception_type(KafkaConnectionError),
        stop=stop_after_attempt(30),
        wait=wait_exponential(multiplier=0.5, max=15),
        reraise=True,
    )
    async def start(self) -> None:
        self._consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap,
            group_id=self.group_id,
            client_id=f"{settings.kafka_client_id}-consumer",
            enable_auto_commit=False,
            auto_offset_reset="latest",
            max_poll_records=settings.consumer_batch_max,
            session_timeout_ms=30_000,
            heartbeat_interval_ms=8_000,
        )
        await self._consumer.start()
        log.info(
            "consumer_started",
            bootstrap=self.bootstrap,
            topic=self.topic,
            group_id=self.group_id,
        )

    async def batches(self) -> AsyncIterator[list[dict]]:
        """Yield decoded record batches. Caller commits via ``commit()``."""
        if self._consumer is None:
            raise RuntimeError("consumer not started")
        while not self._stopping.is_set():
            try:
                result = await self._consumer.getmany(timeout_ms=1000, max_records=settings.consumer_batch_max)
            except KafkaConnectionError as exc:
                log.warning("consumer_connection_error", error=str(exc))
                await asyncio.sleep(1)
                continue
            if not result:
                continue
            decoded: list[dict] = []
            for _tp, messages in result.items():
                for msg in messages:
                    try:
                        decoded.append(orjson.loads(msg.value))
                    except orjson.JSONDecodeError:
                        log.warning("undecodable_message", offset=msg.offset)
            if decoded:
                yield decoded

    async def commit(self) -> None:
        if self._consumer is not None:
            await self._consumer.commit()

    async def stop(self) -> None:
        self._stopping.set()
        if self._consumer is not None:
            await self._consumer.stop()
            log.info("consumer_stopped")
        self._consumer = None
