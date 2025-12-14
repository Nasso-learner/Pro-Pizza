from kafka import KafkaConsumer
import json
import os


KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"
)


consumer = KafkaConsumer(
    "pizza-orders",
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    group_id="pizza-order-consumer"
)

print("🚀 Kafka Consumer started...")

for message in consumer:
    event = message.value
    print(f"📥 Received Event: {event['event_type']}")
    print(f"Order Data: {event['order']}")
    # Here you can add logic like sending email, updating delivery system, etc.
