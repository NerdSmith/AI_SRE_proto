import re

from ..models import LogEvent

PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "<email>"),
    (re.compile(r"(?<![\w=])(?:\d[ -]?){13,19}(?!\w)"), "<card>"),
    (re.compile(r"(?<![\w=])(?:\+7|8)[\s(-]*\d{3}[\s)-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}(?!\w)"), "<phone>"),
    (re.compile(r"(?i)\b(password|passwd|token|secret|api_key)=\S+"), r"\1=<secret>"),
]


def mask_text(text: str) -> tuple[str, int]:
    total = 0
    for pattern, replacement in PATTERNS:
        text, count = pattern.subn(replacement, text)
        total += count
    return text, total


def mask_events(events: list[LogEvent]) -> tuple[list[LogEvent], int]:
    masked = []
    total = 0
    for event in events:
        text, count = mask_text(event.text)
        total += count
        masked.append(event.model_copy(update={"text": text}))
    return masked, total
