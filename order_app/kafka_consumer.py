from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    "pizza-orders",
    bootstrap_servers=["localhost:9092"],
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    group_id="pizza-order-consumer"
)

print("🚀 Kafka Consumer started...")

for message in consumer:
    event = message.value
    print(f"📥 Received Event: {event['event_type']}")
    print(f"Order Data: {event['order']}")
    # Here you can add logic like sending email, updating delivery system, etc.
