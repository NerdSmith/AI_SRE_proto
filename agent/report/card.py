from pathlib import Path

from ..models import Report

STATUS = {
    "cause_found": "Причина найдена",
    "no_incident": "Инцидента нет",
    "insufficient_observations": "Недостаточно данных",
}


def render_card(report: Report) -> str:
    diagnosis = report.diagnosis
    stats = report.stats
    lines = [
        f"# Инцидент: {report.container}",
        "",
        f"**Статус:** {STATUS[diagnosis.status]}  ",
        f"**Категория:** `{diagnosis.category}`  ",
        f"**Образ:** `{report.image}`",
        "",
        "## Что произошло",
        diagnosis.summary,
        "",
        "## Вероятная причина",
        diagnosis.root_cause,
        "",
        "## Рекомендуемое действие",
        diagnosis.action,
        "",
        "## Доказательства",
    ]
    observations = {item.id: item for item in report.observations}
    for claim in diagnosis.claims:
        mark = "✓" if claim.supported else "✗"
        lines.append(f"- {mark} {claim.text}")
        for citation in claim.citations:
            item = observations.get(citation.observation_id)
            times = f" {item.first_seen}-{item.last_seen}, x{item.count}" if item and item.kind == "log" else ""
            lines.append(f"  - `{citation.observation_id}`{times}: `{citation.quote[:220]}`")
    lines += [
        "",
        "## Обработка",
        f"- Событий: {stats.events}, шаблонов: {stats.templates}",
        f"- Объём логов: {stats.raw_chars} → {stats.compact_chars} символов",
        f"- Замаскировано значений: {stats.masked_values}",
        f"- Токенов на вход: {stats.prompt_tokens}, время модели: {stats.seconds} с",
    ]
    return "\n".join(lines) + "\n"


def save_report(report: Report, directory: str) -> Path:
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    (target / f"{report.scenario}.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
    path = target / f"{report.scenario}.md"
    path.write_text(render_card(report), encoding="utf-8")
    return path
