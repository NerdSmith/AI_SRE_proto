import os
import sys
import time
from datetime import datetime, timezone

from .analysis.investigator import investigate, run_baseline
from .collectors.docker_source import collect
from .llm.client import LlmClient
from .models import Report
from .report.card import render_card, save_report


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    time.sleep(int(os.getenv("WINDOW_SECONDS", "25")))
    snapshot = collect()
    llm = LlmClient()
    diagnosis, observations, stats = investigate(snapshot, llm)
    baseline = run_baseline(snapshot, llm) if os.getenv("COMPARE") == "1" else None
    report = Report(
        scenario=os.getenv("SCENARIO", "manual"),
        container=snapshot.container,
        image=snapshot.image,
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        diagnosis=diagnosis,
        observations=observations,
        stats=stats,
        baseline=baseline,
    )
    save_report(report, os.getenv("REPORT_DIR", "/reports"))
    print(render_card(report), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
