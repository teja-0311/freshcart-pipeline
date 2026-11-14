"""
D1: Routing Table Demonstration
Shows all 6 routing keys from the assignment and which drivers match each.
"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.test_stream_routing import match_topic_pattern

DRIVERS = {
    "Ravi":    "bangalore.koramangala.*",
    "Priya":   "bangalore.indiranagar.*",
    "Arjun":   "bangalore.*.ride",
    "Meena":   "bangalore.*.food",
    "Karthik": "chennai.tnagar.food",
    "Control": "bangalore.#",
}

ROUTING_KEYS = [
    ("bangalore.koramangala.food",  "1"),
    ("bangalore.indiranagar.ride",  "2"),
    ("bangalore.whitefield.ride",   "3"),
    ("chennai.tnagar.food",         "4"),
    ("chennai.whitefield.ride",     "5"),
    ("bangalore.koramangala",       "6 (only 2 words!)"),
]

BANNER = "=" * 76

print(BANNER)
print("  PART D1: RabbitMQ Topic Exchange — Routing Table")
print("  Exchange: rapido-dispatch  |  Exchange type: topic")
print(BANNER)
print()
print("  Wildcard rules:")
print("    *  = matches EXACTLY one word (one dot-separated segment)")
print("    #  = matches ZERO or more words")
print()
print("  Driver Subscriptions:")
for name, pattern in DRIVERS.items():
    print(f"    {name:8s}  -->  {pattern}")
print()

print(BANNER)
print("  SCREENSHOT D1 — Routing Table (paste this into your report too)")
print(BANNER)
print()

header = f"  {'#':>3}  {'Routing Key':<35}  {'Matched Drivers':<40}  {'Dropped?'}"
print(header)
print(f"  {'-'*3}  {'-'*35}  {'-'*40}  {'-'*8}")

for key, label in ROUTING_KEYS:
    matched = [name for name, pattern in DRIVERS.items()
               if match_topic_pattern(pattern, key)]
    dropped = "YES (no driver)" if not matched else "no"
    matched_str = ", ".join(matched) if matched else "(none)"
    print(f"  {label:>3}  {key:<35}  {matched_str:<40}  {dropped}")

print()
print("  Explanation for Routing Key 6 (bangalore.koramangala — only 2 words):")
print("    Ravi    -> 'bangalore.koramangala.*'  FAILS: * requires EXACTLY 1 more word.")
print("    Priya   -> 'bangalore.indiranagar.*'  FAILS: zone doesn't match 'indiranagar'.")
print("    Arjun   -> 'bangalore.*.ride'         FAILS: missing type word 'ride'.")
print("    Meena   -> 'bangalore.*.food'         FAILS: missing type word 'food'.")
print("    Karthik -> 'chennai.tnagar.food'      FAILS: city is bangalore, not chennai.")
print("    Control -> 'bangalore.#'              PASSES: # matches 0 or more words.")
print()
print(BANNER)
print("  Take 1 screenshot of the routing table above (SCREENSHOT D1).")
print(BANNER)
