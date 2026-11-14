import argparse
import json
import os
import sys
import pika
from dotenv import load_dotenv

load_dotenv()

EXCHANGE_NAME = "rapido-dispatch"
EXCHANGE_TYPE = "topic"


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


def start_driver(name, pattern, max_messages=None):
    """Start consumer listening on topic exchange with given binding pattern."""
    connection = get_connection()
    channel = connection.channel()

    # Declare topic exchange
    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type=EXCHANGE_TYPE,
        durable=True,
    )

    # Declare private exclusive queue
    queue_name = f"driver_queue_{name.lower()}"
    channel.queue_declare(queue=queue_name, exclusive=False, auto_delete=True)

    # Bind queue to topic exchange with binding pattern
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name, routing_key=pattern)

    print(f"[{name}] Listening on queue '{queue_name}' with pattern '{pattern}'")
    print(f"[{name}] Waiting for orders. Press CTRL+C to exit.\n")

    message_count = [0]

    def on_message_callback(ch, method, properties, body):
        message_count[0] += 1
        raw_text = body.decode("utf-8")
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError:
            print(f"[{name}] [NACK - INVALID JSON] Rejected malformed non-JSON message.")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        order_id = payload.get("id", "UNKNOWN")
        zone = payload.get("zone")

        # PART D4: ACK and NACK logic
        # Reject messages missing zone with basic_nack(requeue=False)
        if not zone or str(zone).strip().lower() in ["none", "unknown", ""]:
            print(f"[{name}] [NACK] REJECTED order {order_id} (Reason: 'zone' missing or invalid). Requeue=False.")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        else:
            # Valid order: acknowledge with basic_ack()
            city = payload.get("city", "")
            order_type = payload.get("type", "")
            print(f"[{name}] [ACK] ACCEPTED order {order_id} | City: {city} | Zone: {zone} | Type: {order_type} (Key: {method.routing_key})")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        if max_messages and message_count[0] >= max_messages:
            print(f"[{name}] Reached max messages ({max_messages}). Stopping consumer.")
            ch.stop_consuming()

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=on_message_callback)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print(f"\n[{name}] Driver shutting down.")
        channel.stop_consuming()
    finally:
        connection.close()
        print(f"[{name}] Connection closed.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python driver.py NAME PATTERN [--max-messages N]")
        print("Example: python driver.py Ravi 'bangalore.koramangala.*'")
        sys.exit(1)

    driver_name = sys.argv[1]
    binding_pattern = sys.argv[2]

    parser = argparse.ArgumentParser(description=f"Driver client for {driver_name}")
    parser.add_argument("name", type=str, help="Driver name")
    parser.add_argument("pattern", type=str, help="RabbitMQ binding pattern")
    parser.add_argument("--max-messages", type=int, default=None, help="Stop after N messages")
    args = parser.parse_args()

    start_driver(args.name, args.pattern, max_messages=args.max_messages)
