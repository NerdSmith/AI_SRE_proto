import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "bad_release": "bad_release",
    "bad_config": "misconfiguration",
    "pool_leak": "resource_exhaustion",
    "healthy": "no_incident",
}


def compose(env_file: Path, *args: str) -> subprocess.CompletedProcess:
    command = ["docker", "compose", "--env-file", str(env_file), *args]
    environment = {**os.environ, "COMPARE": "1"}
    return subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True, encoding="utf-8", errors="replace")


def run_scenario(name: str) -> dict:
    env_file = ROOT / "scenarios" / f"{name}.env"
    report_path = ROOT / "reports" / f"{name}.json"
    report_path.unlink(missing_ok=True)
    try:
        result = compose(env_file, "up", "--build", "--exit-code-from", "agent")
        if result.returncode != 0:
            raise RuntimeError(result.stdout[-1500:] + result.stderr[-1500:])
    finally:
        compose(env_file, "down", "-v", "--remove-orphans")
    return json.loads(report_path.read_text(encoding="utf-8"))


def row(name: str, report: dict) -> dict:
    expected = EXPECTED[name]
    diagnosis = report["diagnosis"]
    stats = report["stats"]
    baseline = report["baseline"]
    claims = diagnosis["claims"]
    return {
        "scenario": name,
        "expected": expected,
        "agent": diagnosis["category"],
        "agent_ok": diagnosis["category"] == expected,
        "agent_supported": f"{sum(c['supported'] for c in claims)}/{len(claims)}",
        "agent_tokens": stats["prompt_tokens"],
        "agent_seconds": stats["seconds"],
        "baseline": baseline["category"],
        "baseline_ok": baseline["category"] == expected,
        "baseline_supported": f"{baseline['claims_supported']}/{baseline['claims_total']}",
        "baseline_tokens": baseline["prompt_tokens"],
        "baseline_seconds": baseline["seconds"],
        "raw_chars": stats["raw_chars"],
        "compact_chars": stats["compact_chars"],
    }


def render(rows: list[dict]) -> str:
    lines = [
        "| Сценарий | Ожидается | Агент | Подтверждено | Токены | Сек | Сырые логи + LLM | Подтверждено | Токены | Сек |",
        "|---|---|---|---|---:|---:|---|---|---:|---:|",
    ]
    for item in rows:
        lines.append(
            f"| {item['scenario']} | {item['expected']} | {'✓' if item['agent_ok'] else '✗'} {item['agent']} "
            f"| {item['agent_supported']} | {item['agent_tokens']} | {item['agent_seconds']} "
            f"| {'✓' if item['baseline_ok'] else '✗'} {item['baseline']} | {item['baseline_supported']} "
            f"| {item['baseline_tokens']} | {item['baseline_seconds']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    names = sys.argv[1:] or list(EXPECTED)
    rows = []
    for name in names:
        print(f"running {name}", flush=True)
        rows.append(row(name, run_scenario(name)))
    table = render(rows)
    (ROOT / "reports" / "summary.md").write_text(table, encoding="utf-8")
    (ROOT / "reports" / "summary.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(table)


if __name__ == "__main__":
    main()
