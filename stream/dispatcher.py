import argparse
import json
import os
import random
import time
from datetime import datetime, timezone
import pika
from dotenv import load_dotenv

load_dotenv()

EXCHANGE_NAME = "rapido-dispatch"
EXCHANGE_TYPE = "topic"

# Available cities and valid zones
ZONES = {
    "bangalore": ["koramangala", "indiranagar", "whitefield", "jayanagar"],
    "chennai": ["tnagar", "velachery", "adyar"],
}
TYPES = ["ride", "food"]


def get_connection():
    """Connect to RabbitMQ using URL or host/credentials from environment."""
    url = os.getenv("RABBITMQ_URL")
    if url:
        params = pika.URLParameters(url)
    else:
        host = os.getenv("RABBITMQ_HOST", "localhost")
        port = int(os.getenv("RABBITMQ_PORT", 5672))
        user = os.getenv("RABBITMQ_USER", "guest")
        password = os.getenv("RABBITMQ_PASSWORD", "guest")
        credentials = pika.PlainCredentials(user, password)
        params = pika.ConnectionParameters(host=host, port=port, credentials=credentials)
    return pika.BlockingConnection(params)


def create_order(msg_counter):
    """Generate a random order. Every 10th message is deliberately malformed (missing zone)."""
    city = random.choice(list(ZONES.keys()))
    order_type = random.choice(TYPES)
    ts = datetime.now(timezone.utc).isoformat()
    order_id = f"ORD-{msg_counter:04d}-{random.randint(100, 999)}"

    is_malformed = (msg_counter % 10 == 0)

    if is_malformed:
        # Deliberately malformed: omit zone
        zone = "unknown"
        payload = {
            "id": order_id,
            "city": city,
            # zone omitted
            "type": order_type,
            "ts": ts,
        }
        routing_key = f"{city}.unknown.{order_type}"
    else:
        zone = random.choice(ZONES[city])
        payload = {
            "id": order_id,
            "city": city,
            "zone": zone,
            "type": order_type,
            "ts": ts,
        }
        routing_key = f"{city}.{zone}.{order_type}"

    return order_id, routing_key, payload, is_malformed


def run_dispatcher(interval=2.0, count=None):
    """Publish food/ride orders to rapido-dispatch topic exchange."""
    connection = get_connection()
    channel = connection.channel()

    # Declare topic exchange
    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type=EXCHANGE_TYPE,
        durable=True,
    )
    print(f"[Dispatcher] Connected to RabbitMQ. Exchange: '{EXCHANGE_NAME}' (type: {EXCHANGE_TYPE})")
    print(f"[Dispatcher] Dispatching orders every {interval}s (deliberate malformed message every 10th order)...")

    msg_counter = 1
    try:
        while True:
            order_id, routing_key, payload, is_malformed = create_order(msg_counter)
            body = json.dumps(payload)

            channel.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key=routing_key,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type="application/json",
                ),
            )

            status_tag = "[MALFORMED - MISSING ZONE]" if is_malformed else "[VALID]"
            print(f"[Dispatcher] #{msg_counter:03d} {status_tag} Sent key='{routing_key}' payload={body}")

            if count and msg_counter >= count:
                print(f"[Dispatcher] Reached target count of {count} messages. Exiting.")
                break

            msg_counter += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[Dispatcher] Stopped by user.")
    finally:
        connection.close()
        print("[Dispatcher] Connection closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rapido Order Dispatcher")
    parser.add_argument("--interval", type=float, default=2.0, help="Interval between messages in seconds")
    parser.add_argument("--count", type=int, default=None, help="Stop after sending N messages")
    args = parser.parse_args()

    run_dispatcher(interval=args.interval, count=args.count)
