"""
Part D Screenshot Runner - RabbitMQ Topic Exchange Simulation
No live RabbitMQ required - simulates routing logic.
Run this and take screenshots of each labeled section.
"""
import sys, os, json, random, re
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from stream.dispatcher import create_order

# ── AMQP topic pattern matching (mirrors RabbitMQ spec) ─────────────────────
def match_topic(pattern, routing_key):
    parts = pattern.split(".")
    r_parts = []
    for p in parts:
        if p == "*":
            r_parts.append(r"[^.]+")
        elif p == "#":
            r_parts.append(r"(?:[^.]+\.)*[^.]+|(?:)")
        else:
            r_parts.append(re.escape(p))
    regex = "^" + r"\." .join(r_parts) + "$"
    return bool(re.match(regex, routing_key))

# ── Driver subscriptions ─────────────────────────────────────────────────────
DRIVERS = {
    "Ravi":    "bangalore.koramangala.*",
    "Arjun":   "bangalore.*.ride",
    "Control": "bangalore.#",
}

NUM_ORDERS = 20
BANNER = "=" * 72

def banner(title):
    print(f"\n{BANNER}")
    print(f"  {title}")
    print(f"{BANNER}")

# ── Generate all orders first ────────────────────────────────────────────────
random.seed(99)
orders = []
for i in range(1, NUM_ORDERS + 1):
    order_id, routing_key, payload, is_malformed = create_order(i)
    orders.append((i, order_id, routing_key, payload, is_malformed))

# ── HEADER ───────────────────────────────────────────────────────────────────
banner("RAPIDO FOOD & RIDE STREAMING — RabbitMQ Topic Exchange Simulation")
print(f"  Exchange : rapido-dispatch  |  Exchange type: topic")
print(f"  Orders   : {NUM_ORDERS}  |  Malformed: every 10th order (#{10}, #{20})")
print()
print("  Active Driver Subscriptions:")
for name, pattern in DRIVERS.items():
    print(f"    * {name:8s}  -->  pattern: '{pattern}'")

# ── SECTION 1: Dispatcher Publishing ─────────────────────────────────────────
banner("SCREENSHOT D1 — DISPATCHER PUBLISHING (all orders)")
for i, order_id, routing_key, payload, is_malformed in orders:
    tag = "[MALFORMED - zone=MISSING]" if is_malformed else "[VALID          ]"
    print(f"  [DISPATCHER] #{i:02d} {tag}  key='{routing_key}'  id={order_id}")

# ── SECTION 2: Driver Ravi ────────────────────────────────────────────────────
name = "Ravi"
pattern = DRIVERS[name]
banner(f"SCREENSHOT D2 — DRIVER {name}: '{pattern}'")
count = 0
for i, order_id, routing_key, payload, is_malformed in orders:
    if match_topic(pattern, routing_key):
        zone = payload.get("zone", "MISSING")
        city = payload.get("city", "")
        otype = payload.get("type", "")
        if is_malformed or not zone or zone == "unknown":
            print(f"  [{name:8s}] [NACK] REJECTED #{i:02d} {order_id}  (zone missing)  requeue=False")
        else:
            print(f"  [{name:8s}] [ACK ] ACCEPTED #{i:02d} {order_id}  city={city}  zone={zone}  type={otype}")
        count += 1
print(f"\n  >>> {name} received {count} message(s) matching '{pattern}'")

# ── SECTION 3: Driver Arjun ───────────────────────────────────────────────────
name = "Arjun"
pattern = DRIVERS[name]
banner(f"SCREENSHOT D3 — DRIVER {name}: '{pattern}'")
count = 0
for i, order_id, routing_key, payload, is_malformed in orders:
    if match_topic(pattern, routing_key):
        zone = payload.get("zone", "MISSING")
        city = payload.get("city", "")
        otype = payload.get("type", "")
        if is_malformed or not zone or zone == "unknown":
            print(f"  [{name:8s}] [NACK] REJECTED #{i:02d} {order_id}  (zone missing)  requeue=False")
        else:
            print(f"  [{name:8s}] [ACK ] ACCEPTED #{i:02d} {order_id}  city={city}  zone={zone}  type={otype}")
        count += 1
print(f"\n  >>> {name} received {count} message(s) matching '{pattern}'")

# ── SECTION 4: Driver Control ─────────────────────────────────────────────────
name = "Control"
pattern = DRIVERS[name]
banner(f"SCREENSHOT D4 — DRIVER {name}: '{pattern}'  (catches all bangalore)")
count = 0
for i, order_id, routing_key, payload, is_malformed in orders:
    if match_topic(pattern, routing_key):
        zone = payload.get("zone", "MISSING")
        city = payload.get("city", "")
        otype = payload.get("type", "")
        if is_malformed or not zone or zone == "unknown":
            print(f"  [{name:8s}] [NACK] REJECTED #{i:02d} {order_id}  (zone missing)  requeue=False  -->  Dead-Letter Queue")
        else:
            print(f"  [{name:8s}] [ACK ] ACCEPTED #{i:02d} {order_id}  city={city}  zone={zone}  type={otype}")
        count += 1
print(f"\n  >>> {name} received {count} message(s) matching '{pattern}'")

# ── SECTION 5: ACK/NACK Demonstration ────────────────────────────────────────
banner("SCREENSHOT D5 — ACK / NACK DEMONSTRATION")
print()
print("  AMQP ACK/NACK behaviour:")
print("  +------------------------------------------------------------------+")
print("  |  Valid order  -->  driver calls basic_ack(delivery_tag)         |")
print("  |                    message removed from queue                   |")
print("  |                                                                  |")
print("  |  Missing zone -->  driver calls basic_nack(delivery_tag,        |")
print("  |                    requeue=False)  -->  dead-lettered, dropped  |")
print("  +------------------------------------------------------------------+")

# Show first valid ACK example
print()
print("  [EXAMPLE: VALID ORDER -> ACK]")
for i, order_id, routing_key, payload, is_malformed in orders:
    if not is_malformed and "bangalore" in routing_key:
        zone = payload.get("zone","")
        city = payload.get("city","")
        otype = payload.get("type","")
        matched = [n for n, p in DRIVERS.items() if match_topic(p, routing_key)]
        print(f"    Order #{i:02d}  id={order_id}")
        print(f"    routing_key = '{routing_key}'")
        print(f"    payload     = city={city}  zone={zone}  type={otype}")
        print(f"    Received by : {matched}")
        print(f"    Action      : basic_ack(delivery_tag)  [message removed from queue]")
        break

# Show NACK example (order #10 or #20)
print()
print("  [EXAMPLE: MALFORMED ORDER -> NACK (requeue=False)]")
for i, order_id, routing_key, payload, is_malformed in orders:
    if is_malformed:
        zone = payload.get("zone", "MISSING")
        city = payload.get("city","")
        otype = payload.get("type","")
        matched = [n for n, p in DRIVERS.items() if match_topic(p, routing_key)]
        print(f"    Order #{i:02d}  id={order_id}  <-- MALFORMED (zone field omitted)")
        print(f"    routing_key = '{routing_key}'")
        print(f"    payload     = city={city}  zone=MISSING  type={otype}")
        print(f"    Received by : {matched if matched else '(no match - dropped)'}")
        if matched:
            print(f"    Action      : basic_nack(delivery_tag, requeue=False)")
            print(f"                  --> message dead-lettered, NOT requeued")
        else:
            print(f"    Action      : (no driver matched - silently dropped by exchange)")
        print()

# ── SECTION 6: Combined Chronological View ────────────────────────────────────
banner("COMBINED CHRONOLOGICAL VIEW — All 20 orders with routing decisions")
for i, order_id, routing_key, payload, is_malformed in orders:
    matched = [n for n, p in DRIVERS.items() if match_topic(p, routing_key)]
    zone = payload.get("zone","MISSING")
    if is_malformed or not zone or zone == "unknown":
        ack_tag = "NACK"
        matched_str = ", ".join(matched) if matched else "(no match - dropped)"
    else:
        ack_tag = "ACK "
        matched_str = ", ".join(matched) if matched else "(no match - dropped)"
    tag = "MALFORMED" if is_malformed else "VALID    "
    print(f"  #{i:02d} [{tag}] key={routing_key:<35s}  drivers={matched_str:<30s}  --> {ack_tag}")

print(f"\n{BANNER}")
print("  Simulation complete. Take screenshots of sections D1 through D5 above.")
print(f"{BANNER}\n")
