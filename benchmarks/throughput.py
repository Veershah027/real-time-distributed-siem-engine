#!/usr/bin/env python3
"""Throughput / latency benchmark for a running SIEM stack.

Measures, against ``docker compose up``:
  * events generated  (what the producer sent)
  * events processed  (rows that reached PostgreSQL during the window)
  * effective end-to-end rate
  * approximate pipeline latency (newest ingested_at - timestamp)
  * error count (invalid events)

It prints ACTUAL measured numbers. No throughput figure is asserted or assumed.
Results depend entirely on hardware and Docker configuration.

Usage:
    python benchmarks/throughput.py --duration 30 --rate 1000
    python benchmarks/throughput.py --duration 20 --rate 2000 --scenario mixed

Requires: the stack running, and `pip install httpx` (already a backend dep).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time

try:
    import httpx
except ImportError:  # pragma: no cover
    print("pip install httpx", file=sys.stderr)
    sys.exit(1)

API = "http://localhost:8000"


def _metrics(client: httpx.Client) -> dict:
    return client.get(f"{API}/api/metrics", timeout=10).json()


def _prom(client: httpx.Client) -> dict[str, float]:
    text = client.get(f"{API}/metrics", timeout=10).text
    out: dict[str, float] = {}
    for line in text.splitlines():
        if line.startswith("#") or " " not in line:
            continue
        name, _, value = line.partition(" ")
        try:
            out[name] = float(value)
        except ValueError:
            continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--duration", type=int, default=30, help="measurement window (s)")
    ap.add_argument("--rate", type=int, default=1000, help="target events/sec")
    ap.add_argument("--scenario", default="mixed")
    ap.add_argument("--no-simulator", action="store_true",
                    help="don't drive the simulator; just measure current load")
    args = ap.parse_args()

    client = httpx.Client()
    try:
        client.get(f"{API}/health", timeout=5).raise_for_status()
    except Exception as exc:  # noqa: BLE001
        print(f"stack not reachable at {API}: {exc}", file=sys.stderr)
        return 1

    if not args.no_simulator:
        print(f"→ setting simulator: rate={args.rate} scenario={args.scenario}")
        client.post(
            f"{API}/api/simulator/start",
            json={"rate": args.rate, "scenario": args.scenario},
            timeout=10,
        )
        time.sleep(3)  # let it ramp

    p0 = _prom(client)
    m0 = _metrics(client)
    t0 = time.time()
    print(f"→ measuring for {args.duration}s ...")
    time.sleep(args.duration)
    elapsed = time.time() - t0
    p1 = _prom(client)
    m1 = _metrics(client)

    ingested = p1.get("siem_events_ingested_total", 0) - p0.get("siem_events_ingested_total", 0)
    persisted = p1.get("siem_events_persisted_total", 0) - p0.get("siem_events_persisted_total", 0)
    invalid = sum(
        v for k, v in p1.items() if k.startswith("siem_events_invalid_total")
    ) - sum(v for k, v in p0.items() if k.startswith("siem_events_invalid_total"))
    alerts = p1.get("siem_alerts_created_total", 0) - p0.get("siem_alerts_created_total", 0)

    # pipeline latency histogram (sum/count) delta -> mean seconds
    lat_sum = p1.get("siem_pipeline_latency_seconds_sum", 0) - p0.get(
        "siem_pipeline_latency_seconds_sum", 0
    )
    lat_cnt = p1.get("siem_pipeline_latency_seconds_count", 0) - p0.get(
        "siem_pipeline_latency_seconds_count", 0
    )
    det_sum = p1.get("siem_detection_latency_seconds_sum", 0) - p0.get(
        "siem_detection_latency_seconds_sum", 0
    )
    det_cnt = p1.get("siem_detection_latency_seconds_count", 0) - p0.get(
        "siem_detection_latency_seconds_count", 0
    )

    print("\n================ BENCHMARK RESULTS (measured) ================")
    print(f"window seconds ............ {elapsed:.1f}")
    print(f"target rate .............. {args.rate}/s")
    print(f"events consumed .......... {ingested:.0f}  ({ingested / elapsed:.0f}/s)")
    print(f"events persisted (PG) .... {persisted:.0f}  ({persisted / elapsed:.0f}/s)")
    print(f"invalid events ........... {invalid:.0f}")
    print(f"alerts created ........... {alerts:.0f}")
    if lat_cnt:
        print(f"mean pipeline latency .... {lat_sum / lat_cnt * 1000:.2f} ms / event")
    if det_cnt:
        print(f"mean detection latency ... {det_sum / det_cnt * 1000:.2f} ms / event")
    print(f"dashboard eps (end) ...... {m1.get('events_per_second')}")
    print(f"total events (24h, end) .. {m1.get('events_last_24h')}")
    print("============================================================")
    print("NOTE: results depend on hardware and Docker configuration.")

    if not args.no_simulator:
        client.post(f"{API}/api/simulator/configure", json={"rate": 60}, timeout=10)
    return 0


def _compose_running() -> bool:  # pragma: no cover - convenience
    try:
        out = subprocess.run(  # noqa: S603
            ["docker", "compose", "ps", "--format", "json"],
            capture_output=True, text=True, timeout=10, check=False,
        )
        return "backend" in out.stdout
    except Exception:
        return False


if __name__ == "__main__":
    sys.exit(main())
