"""Console sink — prints events as JSON lines. Useful for `--sink console`."""

from __future__ import annotations

import sys

import orjson


class ConsoleProducer:
    def __init__(self, *_args, **_kwargs) -> None:
        self._count = 0

    async def start(self) -> None:
        pass

    async def send(self, event: dict) -> None:
        sys.stdout.buffer.write(orjson.dumps(event) + b"\n")
        self._count += 1
        if self._count % 100 == 0:
            sys.stdout.flush()

    async def flush(self) -> None:
        sys.stdout.flush()

    async def stop(self) -> None:
        sys.stdout.flush()
