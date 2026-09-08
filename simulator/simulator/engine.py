"""Simulator engine — rate control, scenario mixing, Redis control plane."""

from __future__ import annotations

import asyncio
import contextlib
import json
import random
import time
from collections import deque
from dataclasses import asdict, dataclass

import redis.asyncio as redis
import structlog

from simulator.generators import normal_event
from simulator.scenarios import SCENARIOS

log = structlog.get_logger("simulator.engine")

_TICKS_PER_SECOND = 10
CONTROL_KEY = "siem:simulator:control"
HEARTBEAT_KEY = "siem:simulator:heartbeat"
STATS_KEY = "siem:simulator:stats"

_SCENARIO_ALIASES = {
    "normal": None,
    "mixed": "mixed",
    "ssh_brute_force": "ssh_brute_force",
    "port_scan": "port_scan",
    "credential_attack": "credential_attack",
    "privilege_escalation": "privilege_escalation",
    "data_exfiltration": "data_exfiltration",
    "web_attack": "web_attack",
    "sql_attack": "sql_attack",
}


@dataclass
class EngineState:
    running: bool
    rate: int
    scenario: str
    attack_ratio: float
    burst: bool = False


class SimulatorEngine:
    def __init__(self, producer, cfg, redis_client: redis.Redis | None = None) -> None:
        self.producer = producer
        self.cfg = cfg
        self.redis = redis_client
        self.state = EngineState(
            running=cfg.autostart,
            rate=cfg.events_per_second,
            scenario=cfg.scenario,
            attack_ratio=cfg.attack_ratio,
        )
        self._attack_queue: deque[dict] = deque()
        self._stop = asyncio.Event()
        self._sent_total = 0
        self._sent_attack = 0
        self._scenario_runs = 0
        self._started_at = time.time()
        self._burst_until = 0.0

    # ------------------------------------------------------------------ #
    def request_stop(self) -> None:
        self._stop.set()

    async def _sync_from_redis(self) -> None:
        if not self.redis or not self.cfg.control_via_redis:
            return
        with contextlib.suppress(Exception):
            raw = await self.redis.get(CONTROL_KEY)
            if not raw:
                return
            data = json.loads(raw)
            self.state.running = bool(data.get("running", self.state.running))
            self.state.rate = int(data.get("rate", self.state.rate))
            self.state.scenario = str(data.get("scenario", self.state.scenario))
            self.state.attack_ratio = float(data.get("attack_ratio", self.state.attack_ratio))
            if data.get("burst"):
                self._burst_until = time.time() + 8
                # clear the one-shot flag so a burst is a pulse, not a mode
                data["burst"] = False
                await self.redis.set(CONTROL_KEY, json.dumps(data))

    async def _heartbeat(self) -> None:
        if not self.redis:
            return
        with contextlib.suppress(Exception):
            await self.redis.set(
                HEARTBEAT_KEY,
                json.dumps({"ts": time.time(), "state": asdict(self.state)}),
                ex=20,
            )
            await self.redis.set(
                STATS_KEY,
                json.dumps(self.stats()),
                ex=30,
            )

    def stats(self) -> dict:
        elapsed = max(time.time() - self._started_at, 1e-6)
        return {
            "sent_total": self._sent_total,
            "sent_attack_events": self._sent_attack,
            "scenario_runs": self._scenario_runs,
            "effective_eps": round(self._sent_total / elapsed, 2),
            "queue_depth": len(self._attack_queue),
            "uptime_seconds": round(elapsed, 1),
            "state": asdict(self.state),
        }

    # ------------------------------------------------------------------ #
    def _enqueue_scenario(self, name: str) -> None:
        fn = SCENARIOS.get(name)
        if fn is None:
            return
        events = fn()
        self._attack_queue.extend(events)
        self._scenario_runs += 1
        log.info("scenario_enqueued", scenario=name, events=len(events))

    def _maybe_launch_scenario(self) -> None:
        scenario = _SCENARIO_ALIASES.get(self.state.scenario, None)
        if scenario is None:
            return
        if scenario == "mixed":
            # attack_ratio ~ fraction of events that are malicious; convert to a
            # per-second launch probability assuming ~20 events per scenario.
            per_sec_p = min(0.9, self.state.attack_ratio * self.state.rate / 20 / _TICKS_PER_SECOND)
            if random.random() < per_sec_p:
                self._enqueue_scenario(random.choice(list(SCENARIOS)))
        else:
            # dedicated scenario: keep a steady drip so alerts stay fresh
            if not self._attack_queue and random.random() < 0.15:
                self._enqueue_scenario(scenario)

    async def _emit_tick(self, budget: int) -> None:
        for _ in range(budget):
            if self._attack_queue:
                event = self._attack_queue.popleft()
                self._sent_attack += 1
            else:
                event = normal_event()
            try:
                await self.producer.send(event)
                self._sent_total += 1
            except Exception as exc:  # noqa: BLE001
                log.warning("send_failed", error=str(exc))
                return

    async def run(self) -> None:
        await self.producer.start()
        log.info("engine_started", state=asdict(self.state))
        tick = 0
        try:
            while not self._stop.is_set():
                tick_started = time.perf_counter()
                if tick % (_TICKS_PER_SECOND * 2) == 0:
                    await self._sync_from_redis()
                if tick % (_TICKS_PER_SECOND * 5) == 0:
                    await self._heartbeat()

                if self.state.running and self.state.rate > 0:
                    rate = self.state.rate
                    if time.time() < self._burst_until:
                        rate *= 10
                    self._maybe_launch_scenario()
                    base = rate // _TICKS_PER_SECOND
                    remainder = 1 if (tick % _TICKS_PER_SECOND) < (rate % _TICKS_PER_SECOND) else 0
                    await self._emit_tick(base + remainder)

                tick += 1
                elapsed = time.perf_counter() - tick_started
                await asyncio.sleep(max(0.0, (1 / _TICKS_PER_SECOND) - elapsed))
        finally:
            with contextlib.suppress(Exception):
                await self.producer.flush()
                await self.producer.stop()
            if self.redis:
                with contextlib.suppress(Exception):
                    await self.redis.delete(HEARTBEAT_KEY)
            log.info("engine_stopped", stats=self.stats())

    async def run_scenario_once(self, name: str) -> int:
        """One-shot: emit a single scenario instance immediately (CLI helper)."""
        await self.producer.start()
        fn = SCENARIOS.get(name)
        if fn is None:
            raise ValueError(f"unknown scenario: {name}")
        events = fn()
        for ev in events:
            await self.producer.send(ev)
        await self.producer.flush()
        await self.producer.stop()
        log.info("scenario_emitted", scenario=name, events=len(events))
        return len(events)
