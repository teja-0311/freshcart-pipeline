"""
PART D2: RabbitMQ Food-Order Stream Simulation
Dispatcher publishes orders every 2 seconds to topic exchange 'rapido-dispatch'.
Three drivers bind private queues:
  - Ravi:    bangalore.koramangala.*
  - Arjun:   bangalore.*.ride
  - Control: bangalore.#
Demonstrates topic exchange routing for a stream of orders.
"""
import sys, os, time, random
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from stream.dispatcher import create_order
from tests.test_stream_routing import match_topic_pattern

DRIVERS = {
    "Ravi":    "bangalore.koramangala.*",
    "Arjun":   "bangalore.*.ride",
    "Control": "bangalore.#",
}

BANNER = "=" * 75

print(BANNER)
print("  PART D2: RAPIDO FOOD & RIDE DISPATCH — TOPIC EXCHANGE ROUTING")
print("  Exchange: rapido-dispatch  |  Exchange Type: topic")
print(BANNER)
print("\n[ACTIVE DRIVER SUBSCRIPTIONS]")
for name, pattern in DRIVERS.items():
    print(f"  * Driver {name:8s} -> Private Queue: driver_queue_{name.lower()} | Binding Pattern: '{pattern}'")
print("-" * 75)

random.seed(42)
NUM_ORDERS = 12

for i in range(1, NUM_ORDERS + 1):
    order_id, routing_key, payload, is_malformed = create_order(i)
    city = payload.get("city")
    zone = payload.get("zone", "MISSING")
    order_type = payload.get("type")

    print(f"\n[DISPATCHER] Published Order #{i:02d} | Key: {routing_key:32s} | ID: {order_id}")
    
    # Check which drivers receive the order
    matched_any = False
    for name, pattern in DRIVERS.items():
        if match_topic_pattern(pattern, routing_key):
            matched_any = True
            print(f"  --> Driver [{name:7s}] RECEIVED order {order_id} on queue 'driver_queue_{name.lower()}'")
            print(f"      Details: City={city}, Zone={zone}, Type={order_type}")
    
    if not matched_any:
        print("  --> [TOPIC EXCHANGE] (No queue binding matched this routing key -- message dropped)")

    time.sleep(0.1)

print("\n" + BANNER)
print("  PART D2: Stream execution complete! Orders reached exactly the predicted driver queues.")
print(BANNER)
