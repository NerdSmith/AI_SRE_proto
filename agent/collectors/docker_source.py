import re
from datetime import datetime

import docker

from ..models import LogEvent, Snapshot

TARGET_LABEL = "aisre.target=true"
APP_LINE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}[,.]\d+\s+(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+(.*)$"
)


def _parse_timestamp(value: str) -> datetime:
    head, _, tail = value.rstrip("Z").partition(".")
    return datetime.fromisoformat(f"{head}.{tail[:6].ljust(6, '0')}+00:00")


def _finish(event: dict) -> LogEvent:
    text = event["text"]
    extra = event["extra"]
    if extra:
        frames = [line.strip() for line in extra if line.strip().startswith("File ")]
        parts = [text]
        if frames:
            parts.append(frames[-1])
        parts.append(extra[-1].strip())
        text = " | ".join(parts)
    return LogEvent(timestamp=event["timestamp"], level=event["level"], text=text)


def parse_logs(raw: str) -> list[LogEvent]:
    events: list[LogEvent] = []
    current: dict | None = None
    for line in raw.splitlines():
        stamp, _, body = line.partition(" ")
        match = APP_LINE.match(body)
        if match:
            if current:
                events.append(_finish(current))
            current = {
                "timestamp": _parse_timestamp(stamp),
                "level": match.group(1),
                "text": match.group(2),
                "extra": [],
            }
        elif current and body.strip():
            current["extra"].append(body)
    if current:
        events.append(_finish(current))
    return events


def collect() -> Snapshot:
    client = docker.from_env()
    containers = client.containers.list(filters={"label": TARGET_LABEL})
    if not containers:
        raise RuntimeError("target container not found")
    container = containers[0]
    state = container.attrs["State"]
    raw = container.logs(timestamps=True).decode("utf-8", errors="replace")
    return Snapshot(
        container=container.name,
        image=container.image.tags[0] if container.image.tags else container.image.short_id,
        status=state["Status"],
        restarts=container.attrs.get("RestartCount", 0),
        oom_killed=state.get("OOMKilled", False),
        started_at=state["StartedAt"],
        events=parse_logs(raw),
        raw_text=raw,
    )
