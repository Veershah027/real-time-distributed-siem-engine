"""aiokafka producer for the simulator."""

from __future__ import annotations

import orjson
import structlog
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError

log = structlog.get_logger("simulator.kafka")


class KafkaProducer:
    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        last_exc: Exception | None = None
        for attempt in range(1, 31):
            try:
                self._producer = AIOKafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    client_id="siem-simulator",
                    acks=1,
                    linger_ms=15,
                    compression_type="gzip",
                    value_serializer=lambda v: orjson.dumps(v),
                )
                await self._producer.start()
                log.info("kafka_connected", bootstrap=self.bootstrap_servers, topic=self.topic)
                return
            except KafkaConnectionError as exc:  # broker not up yet
                last_exc = exc
                wait = min(attempt * 1.5, 15)
                log.warning("kafka_connect_retry", attempt=attempt, wait=wait)
                import asyncio

                await asyncio.sleep(wait)
        raise RuntimeError(f"could not connect to Kafka/Redpanda: {last_exc}")

    async def send(self, event: dict) -> None:
        if self._producer is None:
            raise RuntimeError("producer not started")
        key = (event.get("source_ip") or event.get("source") or "").encode()
        await self._producer.send(self.topic, value=event, key=key or None)

    async def flush(self) -> None:
        if self._producer is not None:
            await self._producer.flush()

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            log.info("kafka_disconnected")
        self._producer = None
