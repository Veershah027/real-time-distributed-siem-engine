"""Simulator CLI.

python -m simulator --rate 500                 # continuous, normal traffic
python -m simulator --scenario ssh_brute_force # continuous, dedicated attack
python -m simulator --scenario mixed --attack-ratio 0.1
python -m simulator --once port_scan          # emit a single attack instance
python -m simulator --rate 200 --sink console # print JSON lines, no broker
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import signal

import redis.asyncio as redis

from simulator.config import CONFIG
from simulator.engine import SimulatorEngine
from simulator.producers import ConsoleProducer, KafkaProducer
from simulator.scenarios import SCENARIOS

SCENARIO_CHOICES = ["normal", "mixed", *sorted(SCENARIOS)]


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        "siem-simulator", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--rate",
        type=int,
        default=CONFIG.events_per_second,
        help="events per second (default from env)",
    )
    p.add_argument("--scenario", choices=SCENARIO_CHOICES, default=CONFIG.scenario)
    p.add_argument(
        "--attack-ratio",
        type=float,
        default=CONFIG.attack_ratio,
        help="fraction of malicious traffic in 'mixed' scenario",
    )
    p.add_argument("--sink", choices=["kafka", "console"], default=CONFIG.sink)
    p.add_argument(
        "--once",
        metavar="SCENARIO",
        choices=sorted(SCENARIOS),
        help="emit one instance of SCENARIO and exit",
    )
    p.add_argument(
        "--no-redis-control",
        action="store_true",
        help="ignore the dashboard control plane; use CLI args only",
    )
    p.add_argument(
        "--duration", type=int, default=0, help="stop after N seconds (0 = run until interrupted)"
    )
    return p.parse_args(argv)


def _make_producer(sink: str):
    if sink == "console":
        return ConsoleProducer()
    return KafkaProducer(CONFIG.kafka_bootstrap_servers, CONFIG.kafka_topic)


async def _run(args: argparse.Namespace) -> None:
    producer = _make_producer(args.sink)
    redis_client = None
    if args.sink == "kafka" and not args.no_redis_control:
        with contextlib.suppress(Exception):
            redis_client = redis.from_url(CONFIG.redis_url, decode_responses=True)

    cfg = CONFIG
    cfg.control_via_redis = not args.no_redis_control

    engine = SimulatorEngine(producer, cfg, redis_client)
    engine.state.rate = args.rate
    engine.state.scenario = args.scenario
    engine.state.attack_ratio = args.attack_ratio
    engine.state.running = True

    if args.once:
        n = await engine.run_scenario_once(args.once)
        print(f"emitted {n} events for scenario '{args.once}'")
        return

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, engine.request_stop)

    task = asyncio.create_task(engine.run())
    if args.duration > 0:
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(asyncio.shield(task), timeout=args.duration)
        engine.request_stop()
    await task
    if redis_client:
        await redis_client.aclose()


def main() -> None:
    args = _parse_args()
    with contextlib.suppress(KeyboardInterrupt):  # pragma: no cover
        asyncio.run(_run(args))


if __name__ == "__main__":
    main()
