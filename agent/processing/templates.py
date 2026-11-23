import re
from dataclasses import dataclass

from ..models import LogEvent

NORMALIZERS = [
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"), "<uuid>"),
    (re.compile(r"\b(order|id)=[0-9a-f]{6,}\b"), r"\1=<id>"),
    (re.compile(r"\b[0-9a-f]{12,}\b"), "<hex>"),
    (re.compile(r"\b\d+\.\d+\.\d+\.\d+\b"), "<ip>"),
    (re.compile(r"\btotal=\d+(?:\.\d+)?"), "total=<num>"),
]
SEVERITY = {"CRITICAL": 0, "ERROR": 1, "WARNING": 2, "INFO": 3, "DEBUG": 4}


@dataclass
class Template:
    pattern: str
    level: str
    sample: str
    count: int
    first_seen: str
    last_seen: str


def normalize(text: str) -> str:
    for pattern, replacement in NORMALIZERS:
        text = pattern.sub(replacement, text)
    return text


def mine(events: list[LogEvent]) -> list[Template]:
    groups: dict[tuple[str, str], Template] = {}
    for event in events:
        key = (event.level, normalize(event.text))
        stamp = event.timestamp.strftime("%H:%M:%S")
        if key in groups:
            groups[key].count += 1
            groups[key].last_seen = stamp
        else:
            groups[key] = Template(key[1], event.level, event.text, 1, stamp, stamp)
    return sorted(groups.values(), key=lambda item: (SEVERITY.get(item.level, 9), -item.count))
