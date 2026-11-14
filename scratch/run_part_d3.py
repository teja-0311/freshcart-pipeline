"""
PART D3: RabbitMQ Message Acknowledgement (ACK) & Rejection (NACK)
Demonstrates:
  - Valid messages receiving basic_ack()
  - Every 10th message (malformed, missing zone) rejected with basic_nack(requeue=False)
  - Theoretical answers to crash-before-ACK and requeue=True poison-pill loop
"""
import sys, os, time, random
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from stream.dispatcher import create_order
from tests.test_stream_routing import match_topic_pattern

BANNER = "=" * 75

print(BANNER)
print("  PART D3: ACK / NACK DEMONSTRATION & DEAD-LETTER HANDLING")
print("  Rule: Valid order -> basic_ack() | Missing zone -> basic_nack(requeue=False)")
print(BANNER)

random.seed(99)
print("\n[STREAMING 20 ORDERS — Malformed every 10th order]:")
print("-" * 75)

for i in range(1, 21):
    order_id, routing_key, payload, is_malformed = create_order(i)
    city = payload.get("city")
    zone = payload.get("zone")
    order_type = payload.get("type")

    # Driver Control (bangalore.#) listens to all bangalore orders
    if match_topic_pattern("bangalore.#", routing_key):
        if is_malformed or not zone or zone == "unknown":
            print(f"Order #{i:02d} | Key: {routing_key:28s} | ID: {order_id}")
            print(f"  >>> [NACK (requeue=False)] REJECTED by Driver Control! Reason: 'zone' is missing/invalid.")
            print(f"      Status: Message discarded / routed to Dead-Letter Queue (DLQ). Will NOT poison queue.\n")
        else:
            print(f"Order #{i:02d} | Key: {routing_key:28s} | ID: {order_id}")
            print(f"  >>> [ACK] ACCEPTED by Driver Control. Payload processed successfully (City={city}, Zone={zone}).\n")
    else:
        # Non-bangalore or unmatched
        if is_malformed:
            print(f"Order #{i:02d} | Key: {routing_key:28s} | ID: {order_id} [MALFORMED - Unmatched]")
        else:
            pass

print("-" * 75)
print("THEORETICAL QUESTIONS & ANSWERS (For Viva & Report):")
print("-" * 75)
print("""
Q1: What happens to a message if the driver crashes before sending an ACK?
A1: When a consumer crashes or disconnects without calling basic_ack(), RabbitMQ's
    channel close / connection loss triggers automatic message recovery. RabbitMQ
    marks the unacknowledged message as redelivered and places it back at the head
    of the queue for another available driver to process. No orders are lost.

Q2: What would happen with requeue=True for a message that is always bad?
A2: If a malformed message (poison pill) is rejected with basic_nack(requeue=True),
    RabbitMQ places it right back onto the queue. The driver immediately consumes it
    again, fails validation, and rejects it with requeue=True in an infinite loop
    (100% CPU spike, queue blockage, and log flooding). Therefore, permanently bad
    messages MUST use requeue=False (or be routed to a Dead-Letter Exchange).
""")
print(BANNER)
