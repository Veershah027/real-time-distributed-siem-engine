# ADR 0001 — Message broker: Redpanda over Apache Kafka

- **Status:** Accepted
- **Date:** 2026-09-07
- **Context:** the pipeline needs a durable, partitioned event log between the
  log producers and the stream processor. It must demonstrate real distributed
  event streaming (consumer groups, partitions, offset commits) while staying
  light enough to run in Docker Compose on a laptop alongside Postgres, Redis, a
  Python API, a worker, a simulator, and a frontend.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **Apache Kafka (KRaft)** | Reference implementation; ubiquitous in job descriptions. | ~1 GB+ JVM footprint; slower start; more config surface for a demo. |
| **Apache Kafka + ZooKeeper** | Battle-tested. | Two stateful services; deprecated topology. |
| **Redpanda** | Kafka wire-compatible; single C++ binary; no JVM/ZooKeeper; fast start; `rpk` tooling. | Smaller ecosystem; some admin APIs differ. |
| **Redis Streams** | Already have Redis. | Weaker partition/consumer-group story; muddies "Redis = ephemeral state" boundary. |
| **NATS JetStream** | Light, fast. | Not Kafka-compatible; less transferable as a talking point. |

## Decision

Use **Redpanda** for local development and CI.

The application code speaks the **Kafka protocol** via `aiokafka`
(`app/streaming/kafka.py`). Nothing in the codebase is Redpanda-specific — the
producer, consumer, consumer group, manual offset commits, and topic
(`siem.events.raw`, 6 partitions) are all standard Kafka. Migrating to Apache
Kafka is a change to `SIEM_KAFKA_BOOTSTRAP_SERVERS` and the compose service
definition.

## Consequences

- **Positive:** the whole stack boots in well under a minute; the broker uses
  ~512 MB; `rpk` gives a one-liner health check for the compose `healthcheck`.
- **Positive:** the distributed-streaming story is intact and portable — a
  reviewer sees a real consumer group with lag, not a queue table.
- **Negative:** consumer-lag metrics require the Redpanda admin API rather than
  JMX; deferred to the roadmap.
- **Negative:** anyone expecting literal Apache Kafka needs the note above (it is
  in the README and `docs/architecture.md`).
