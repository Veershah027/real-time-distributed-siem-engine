from __future__ import annotations

import pytest

from simulator.config import SimulatorConfig
from simulator.engine import SimulatorEngine


class RecordingProducer:
    def __init__(self):
        self.sent = []
        self.started = False

    async def start(self):
        self.started = True

    async def send(self, event):
        self.sent.append(event)

    async def flush(self):
        pass

    async def stop(self):
        pass


@pytest.fixture
def cfg():
    c = SimulatorConfig()
    c.control_via_redis = False
    return c


async def test_run_scenario_once_emits_events(cfg):
    prod = RecordingProducer()
    engine = SimulatorEngine(prod, cfg, None)
    n = await engine.run_scenario_once("ssh_brute_force")
    assert n == len(prod.sent) >= 10
    assert prod.started


async def test_run_scenario_once_rejects_unknown(cfg):
    engine = SimulatorEngine(RecordingProducer(), cfg, None)
    with pytest.raises(ValueError):
        await engine.run_scenario_once("does_not_exist")


async def test_dedicated_scenario_enqueues_attack_events(cfg):
    engine = SimulatorEngine(RecordingProducer(), cfg, None)
    engine.state.scenario = "port_scan"
    engine._enqueue_scenario("port_scan")
    assert len(engine._attack_queue) > 20
    assert engine._scenario_runs == 1


async def test_stats_report_structure(cfg):
    engine = SimulatorEngine(RecordingProducer(), cfg, None)
    stats = engine.stats()
    assert {"sent_total", "effective_eps", "queue_depth", "state"} <= stats.keys()
