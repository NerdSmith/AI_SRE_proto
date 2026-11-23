from ..models import Observation, LogEvent, Snapshot
from .templates import Template

CONTEXT_MARKERS = ("release", "deployed", "config", "version=")
MAX_PROBLEMS = 12
MAX_ROUTINE = 3


def error_share(events: list[LogEvent]) -> float:
    if not events:
        return 0.0
    errors = sum(1 for event in events if event.level in ("ERROR", "CRITICAL"))
    return errors / len(events)


def build_observations(snapshot: Snapshot, events: list[LogEvent], templates: list[Template]) -> list[Observation]:
    errors = [event for event in events if event.level in ("ERROR", "CRITICAL")]
    first_error = errors[0].timestamp.strftime("%H:%M:%S") if errors else "none"
    items = [
        Observation(
            id="F1",
            kind="fact",
            text=f"container status={snapshot.status} restarts={snapshot.restarts} oom_killed={snapshot.oom_killed}",
        ),
        Observation(
            id="F2",
            kind="fact",
            text=f"events={len(events)} errors={len(errors)} error_share={error_share(events):.1%} first_error={first_error}",
        ),
    ]
    problems = [item for item in templates if item.level in ("CRITICAL", "ERROR", "WARNING")][:MAX_PROBLEMS]
    context = [
        item for item in templates
        if item.level == "INFO" and any(marker in item.pattern for marker in CONTEXT_MARKERS)
    ]
    routine = [item for item in templates if item.level == "INFO" and item not in context][:MAX_ROUTINE]
    for index, item in enumerate(problems + context + routine, start=1):
        items.append(
            Observation(
                id=f"L{index}",
                kind="log",
                text=item.sample,
                level=item.level,
                count=item.count,
                first_seen=item.first_seen,
                last_seen=item.last_seen,
            )
        )
    return items


def render_line(item: Observation) -> str:
    if item.kind == "fact":
        return f"[{item.id}] FACT {item.text}"
    return f"[{item.id}] {item.level} x{item.count} {item.first_seen}-{item.last_seen} {item.text}"


def render_observations(items: list[Observation]) -> str:
    return "\n".join(render_line(item) for item in items)
