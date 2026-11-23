import re

from ..models import Diagnosis, Observation, ModelClaim, ModelDiagnosis, VerifiedClaim
from ..processing.observations import render_line


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def quote_found(quote: str, source: str) -> bool:
    cleaned = _clean(quote)
    return len(cleaned) >= 4 and cleaned in _clean(source)


def is_supported(claim: ModelClaim, observations: dict[str, Observation]) -> bool:
    return all(
        citation.observation_id in observations
        and quote_found(citation.quote, render_line(observations[citation.observation_id]))
        for citation in claim.citations
    )


def verify(result: ModelDiagnosis, items: list[Observation]) -> Diagnosis:
    observations = {item.id: item for item in items}
    claims = [
        VerifiedClaim(**claim.model_dump(), supported=is_supported(claim, observations))
        for claim in result.claims
    ]
    has_proof = any(claim.supported for claim in claims)
    if result.category == "unknown" or not has_proof:
        return Diagnosis(
            status="insufficient_observations",
            category="unknown",
            summary=result.summary,
            root_cause="Причина не подтверждена данными",
            action="Передать инциденту инженеру и собрать дополнительные данные",
            claims=claims,
        )
    status = "no_incident" if result.category == "no_incident" else "cause_found"
    return Diagnosis(
        status=status,
        category=result.category,
        summary=result.summary,
        root_cause=result.root_cause,
        action=result.action,
        claims=claims,
    )
