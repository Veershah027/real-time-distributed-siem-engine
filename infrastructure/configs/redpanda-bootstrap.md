# Redpanda bootstrap & inspection

The `redpanda-init` compose service creates the events topic on first boot:

```
rpk topic create siem.events.raw --brokers redpanda:9092 -p 6 -r 1
```

- **6 partitions** so the `siem-stream-processor` consumer group can parallelize
  across multiple `worker` replicas.
- **replication factor 1** — single-node local broker.

## Inspect the broker

```bash
# cluster health (used by the compose healthcheck)
docker compose exec redpanda rpk cluster health

# list topics
docker compose exec redpanda rpk topic list

# describe the events topic (partitions, offsets)
docker compose exec redpanda rpk topic describe siem.events.raw

# tail live events off the topic
docker compose exec redpanda rpk topic consume siem.events.raw --num 5

# consumer group lag (proves the worker is a real consumer group)
docker compose exec redpanda rpk group describe siem-stream-processor
```

## Switching to Apache Kafka

Nothing in the application is Redpanda-specific. To run against Apache Kafka,
replace the `redpanda` service with a Kafka image and set
`SIEM_KAFKA_BOOTSTRAP_SERVERS` accordingly. See
[`docs/adr/0001-message-broker.md`](../../docs/adr/0001-message-broker.md).
