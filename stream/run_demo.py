import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from stream.dispatcher import create_order
from tests.test_stream_routing import match_topic_pattern

DRIVERS = {
    "Ravi": "bangalore.koramangala.*",
    "Arjun": "bangalore.*.ride",
    "Control": "bangalore.#",
}

def run_simulation(num_orders=15):
    print("=" * 70)
    print(" RAPIDO FOOD & RIDE STREAMING SIMULATION (RabbitMQ Topic Exchange)")
    print(" Exchange: rapido-dispatch | Exchange Type: topic")
    print("=" * 70)
    print("\n[ACTIVE DRIVER SUBSCRIPTIONS]")
    for name, pattern in DRIVERS.items():
        print(f"  * Driver {name:8s} -> Bound to pattern: '{pattern}'")
    print("-" * 70)

    for i in range(1, num_orders + 1):
        order_id, routing_key, order, is_malformed = create_order(i)
        city = order.get("city")
        order_type = order.get("type")
        zone = order.get("zone", "MISSING")

        print(f"\n[DISPATCHER] Published Order #{i:02d} | Key: {routing_key:28s} | Order ID: {order_id}")
        if is_malformed:
            print("  --> [ALERT] Published deliberate malformed order (omitted zone)")

        # Evaluate routing for each driver
        matched_drivers = []
        for name, pattern in DRIVERS.items():
            if match_topic_pattern(pattern, routing_key):
                matched_drivers.append(name)
                # Driver processes order
                if not order.get("zone") or str(order.get("zone")).strip().lower() in ["none", "unknown", ""]:
                    print(f"  --> [{name:7s}] [NACK] REJECTED {order_id} (Reason: 'zone' missing). requeue=False (Dead-Lettered).")
                else:
                    print(f"  --> [{name:7s}] [ACK]  ACCEPTED {order_id} | City: {city} | Zone: {zone} | Type: {order_type}")

        if not matched_drivers:
            print("  --> [ROUTER] (Dropped: No driver pattern matched this routing key)")

        time.sleep(0.3)

    print("\n" + "=" * 70)
    print(" Simulation Completed Successfully!")
    print("=" * 70)

if __name__ == "__main__":
    run_simulation(12)
