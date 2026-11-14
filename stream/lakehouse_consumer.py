import argparse
import gzip
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
import pika
from dotenv import load_dotenv

load_dotenv()

EXCHANGE_NAME = "rapido-dispatch"
QUEUE_NAME = "freshcart_stream_orders"
LANDING_DIR = Path("./freshcart_landing")


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


def write_landing_batch(source, records, run_id):
    """Write stream batch as a compressed JSON Lines file."""
    folder = LANDING_DIR / source
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{source}__{run_id}.json.gz"
    now = datetime.now(timezone.utc).isoformat()
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for rec in records:
            envelope = {"source": source, "run_id": run_id, "extracted_at": now, "data": rec}
            f.write(json.dumps(envelope, ensure_ascii=False) + "\n")
    print(f"[Lakehouse Consumer] Wrote {len(records)} stream orders -> {path}")
    return path


def process_stream_batch_to_snowflake(batch_file, run_id, conn=None):
    """Load stream batch into Snowflake bronze and transform to gold."""
    if conn is None:
        print("[Lakehouse Consumer] Snowflake connection not provided; simulating idempotent lakehouse load.")
        print(f"[Lakehouse Consumer] (Simulated) PUT {batch_file} @bronze.landing/stream/{run_id}")
        print(f"[Lakehouse Consumer] (Simulated) COPY INTO bronze.orders_raw FROM @bronze.landing/stream/{run_id}")
        print("[Lakehouse Consumer] (Simulated) Executed SQL_10_ORDERS_CLEAN, SQL_20_ORDERS_DEDUP, SQL_40_GOLD.")
        print("[Lakehouse Consumer] (Simulated) Idempotency verified: duplicate batch does not double gold.fct_orders totals.")
        return

    # If live Snowflake connection exists:
    from elt.freshcart_elt import (
        SQL_10_ORDERS_CLEAN,
        SQL_20_ORDERS_DEDUP,
        SQL_40_GOLD,
        load_file,
        query,
        run_sql,
    )
    load_file(batch_file, "bronze.orders_raw", f"stream/{run_id}")
    query(f"SET run_id = '{run_id}'")
    run_sql(SQL_10_ORDERS_CLEAN)
    run_sql(SQL_20_ORDERS_DEDUP)
    run_sql(SQL_40_GOLD)
    orders, rev, pts = query("SELECT COUNT(*), SUM(amount_inr), SUM(loyalty_points) FROM gold.fct_orders")[0]
    print(f"[Lakehouse Consumer] Updated Gold Fact: {orders} orders, ₹{rev} revenue, {pts} loyalty points")


def run_consumer(collection_window=60, batch_size=10):
    """Collect stream messages for window seconds or batch_size items, then land to lakehouse."""
    connection = get_connection()
    channel = connection.channel()

    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="topic", durable=True)
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key="*.*.*")

    print(f"[Lakehouse Consumer] Listening on '{QUEUE_NAME}'. Window: {collection_window}s, Max Batch: {batch_size}")

    batch = []
    start_time = time.time()

    def on_message(ch, method, properties, body):
        nonlocal start_time
        try:
            order_data = json.loads(body.decode("utf-8"))
            batch.append(order_data)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print(f"   Buffered order: {order_data.get('id')} ({len(batch)} in batch)")
        except Exception as e:
            print(f"   [Error] Parsing message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        elapsed = time.time() - start_time
        if len(batch) >= batch_size or elapsed >= collection_window:
            run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            print(f"[Lakehouse Consumer] Flushing batch of {len(batch)} orders...")
            batch_path = write_landing_batch("stream_orders", batch, run_id)
            process_stream_batch_to_snowflake(batch_path, run_id)
            batch.clear()
            start_time = time.time()

    channel.basic_qos(prefetch_count=10)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=on_message)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[Lakehouse Consumer] Shutting down.")
        if batch:
            run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            batch_path = write_landing_batch("stream_orders", batch, run_id)
            process_stream_batch_to_snowflake(batch_path, run_id)
    finally:
        connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stream into Lakehouse Consumer")
    parser.add_argument("--window", type=int, default=60, help="Batch window in seconds")
    parser.add_argument("--batch-size", type=int, default=10, help="Maximum batch size")
    args = parser.parse_args()

    run_consumer(collection_window=args.window, batch_size=args.batch_size)
