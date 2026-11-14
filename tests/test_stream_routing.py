import re
from stream.dispatcher import create_order


def match_topic_pattern(pattern: str, routing_key: str) -> bool:
    """Implement AMQP topic exchange wildcard matching specification:
    * (star) matches exactly one word.
    # (hash) matches zero or more words.
    Words are separated by dots (.).
    """
    regex_parts = []
    tokens = pattern.split(".")
    for i, token in enumerate(tokens):
        if token == "*":
            regex_parts.append(r"[^.]+")
        elif token == "#":
            regex_parts.append(r"(?:[^.]+(?:\.[^.]+)*)?")
        else:
            regex_parts.append(re.escape(token))

    # Join handling dots around #
    pattern_regex = r"^\." + r"\.".join(regex_parts) + r"\.$"
    pattern_regex = pattern_regex.replace(r"\.(?:[^.]+(?:\.[^.]+)*)?\.", r"(?:\.[^.]+)*\.")
    pattern_regex = pattern_regex.replace(r"^\.(?:[^.]+(?:\.[^.]+)*)?", r"^(?:[^.]+\.)*")
    pattern_regex = pattern_regex.replace(r"(?:[^.]+(?:\.[^.]+)*)?\.$", r"(?:\.[^.]+)*$")

    # Clean standardized AMQP topic regex conversion:
    parts = pattern.split(".")
    r_parts = []
    for p in parts:
        if p == "*":
            r_parts.append(r"[^.]+")
        elif p == "#":
            r_parts.append(r".*")
        else:
            r_parts.append(re.escape(p))

    final_regex = "^" + r"\.".join(r_parts).replace(r"\..*", r"(?:\..*)?").replace(r".*\.", r"(?:.*\.)?") + "$"
    return bool(re.match(final_regex, routing_key))


DRIVERS = {
    "Ravi": "bangalore.koramangala.*",
    "Priya": "bangalore.indiranagar.*",
    "Arjun": "bangalore.*.ride",
    "Meena": "bangalore.*.food",
    "Karthik": "chennai.tnagar.food",
    "Control": "bangalore.#",
}


def get_matching_drivers(routing_key: str):
    matches = []
    for name, pattern in DRIVERS.items():
        if match_topic_pattern(pattern, routing_key):
            matches.append(name)
    return matches


def test_d1_paper_routing_key_1():
    key = "bangalore.koramangala.food"
    matches = get_matching_drivers(key)
    assert set(matches) == {"Ravi", "Meena", "Control"}


def test_d1_paper_routing_key_2():
    key = "bangalore.indiranagar.ride"
    matches = get_matching_drivers(key)
    assert set(matches) == {"Priya", "Arjun", "Control"}


def test_d1_paper_routing_key_3():
    key = "bangalore.whitefield.ride"
    matches = get_matching_drivers(key)
    assert set(matches) == {"Arjun", "Control"}


def test_d1_paper_routing_key_4():
    key = "chennai.tnagar.food"
    matches = get_matching_drivers(key)
    assert set(matches) == {"Karthik"}


def test_d1_paper_routing_key_5_dropped():
    key = "chennai.whitefield.ride"
    matches = get_matching_drivers(key)
    assert len(matches) == 0, f"Expected dropped message, got matches: {matches}"


def test_d1_paper_routing_key_6_two_words():
    key = "bangalore.koramangala"
    matches = get_matching_drivers(key)
    # Ravi requires exactly 3 words (.* at end), so Ravi fails!
    # Control has # (zero or more words), so Control matches!
    assert "Ravi" not in matches
    assert "Control" in matches
    assert set(matches) == {"Control"}


def test_dispatcher_creates_valid_and_malformed_messages():
    # Regular message 1..9 must contain zone
    for i in range(1, 10):
        _, key, payload, is_malformed = create_order(i)
        assert not is_malformed
        assert "zone" in payload
        assert len(key.split(".")) == 3

    # Message 10 must be malformed (missing zone)
    _, key_10, payload_10, is_malformed_10 = create_order(10)
    assert is_malformed_10
    assert "zone" not in payload_10
    assert "unknown" in key_10
