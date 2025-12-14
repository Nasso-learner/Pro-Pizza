from kafka import KafkaProducer
import json
import os


KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"
)


producer = KafkaProducer(
    bootstrap_servers=  KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

def send_order_event(event_type, order_data):
    """
    event_type: "ORDER_CREATED" | "ORDER_UPDATED"
    """
    event = {
        "event_type": event_type,
        "order": order_data,
    }
    producer.send("pizza-orders", event)
    producer.flush()
