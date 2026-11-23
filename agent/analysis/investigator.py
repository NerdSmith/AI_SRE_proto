from ..llm.client import LlmClient
from ..models import Baseline, Citation, Diagnosis, Observation, ModelDiagnosis, RunStats, Snapshot, VerifiedClaim
from ..processing.observations import build_observations, error_share, render_observations
from ..processing.masking import mask_events, mask_text
from ..processing.templates import mine
from .prompts import OBSERVATIONS_PROMPT, RAW_PROMPT, SYSTEM_PROMPT
from .verifier import quote_found, verify

MAX_RAW_CHARS = 80_000
RAW_HEAD_CHARS = 8_000
NO_INCIDENT_SHARE = 0.01


def _fit_context(raw: str) -> str:
    if len(raw) <= MAX_RAW_CHARS:
        return raw
    return raw[:RAW_HEAD_CHARS] + "\n...\n" + raw[-(MAX_RAW_CHARS - RAW_HEAD_CHARS):]


def _healthy(snapshot: Snapshot, share: float) -> bool:
    return share < NO_INCIDENT_SHARE and snapshot.restarts == 0 and not snapshot.oom_killed


def _no_incident(observations: list[Observation]) -> Diagnosis:
    fact = next(item for item in observations if item.id == "F2")
    claim = VerifiedClaim(
        text="Доля ошибок ниже порога инцидента",
        citations=[Citation(observation_id="F2", quote=fact.text)],
        supported=True,
    )
    return Diagnosis(
        status="no_incident",
        category="no_incident",
        summary="Устойчивой проблемы не обнаружено",
        root_cause="Нет",
        action="Действий не требуется",
        claims=[claim],
        used_model=False,
    )


def investigate(snapshot: Snapshot, llm: LlmClient) -> tuple[Diagnosis, list[Observation], RunStats]:
    events, masked = mask_events(snapshot.events)
    templates = mine(events)
    observations = build_observations(snapshot, events, templates)
    compact = render_observations(observations)
    stats = RunStats(
        raw_chars=len(snapshot.raw_text),
        compact_chars=len(compact),
        events=len(events),
        templates=len(templates),
        masked_values=masked,
    )
    if _healthy(snapshot, error_share(events)):
        return _no_incident(observations), observations, stats
    prompt = OBSERVATIONS_PROMPT.format(
        container=snapshot.container,
        image=snapshot.image,
        started_at=snapshot.started_at,
        observations=compact,
    )
    completion = llm.complete(SYSTEM_PROMPT, prompt, ModelDiagnosis)
    stats.prompt_tokens = completion.prompt_tokens
    stats.completion_tokens = completion.completion_tokens
    stats.seconds = round(completion.seconds, 1)
    return verify(ModelDiagnosis(**completion.data), observations), observations, stats


def run_baseline(snapshot: Snapshot, llm: LlmClient) -> Baseline:
    logs, _ = mask_text(_fit_context(snapshot.raw_text))
    prompt = RAW_PROMPT.format(container=snapshot.container, logs=logs)
    completion = llm.complete(SYSTEM_PROMPT, prompt, ModelDiagnosis)
    result = ModelDiagnosis(**completion.data)
    supported = sum(
        1 for claim in result.claims
        if all(quote_found(citation.quote, logs) for citation in claim.citations)
    )
    return Baseline(
        category=result.category,
        root_cause=result.root_cause,
        claims_total=len(result.claims),
        claims_supported=supported,
        prompt_tokens=completion.prompt_tokens,
        seconds=round(completion.seconds, 1),
    )
