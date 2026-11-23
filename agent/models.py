from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Category = Literal[
    "bad_release",
    "misconfiguration",
    "resource_exhaustion",
    "dependency_failure",
    "no_incident",
    "unknown",
]


class LogEvent(BaseModel):
    timestamp: datetime
    level: str
    text: str


class Snapshot(BaseModel):
    container: str
    image: str
    status: str
    restarts: int
    oom_killed: bool
    started_at: str
    events: list[LogEvent]
    raw_text: str


class Observation(BaseModel):
    id: str
    kind: Literal["log", "fact"]
    text: str
    level: str = "INFO"
    count: int = 1
    first_seen: str | None = None
    last_seen: str | None = None


class Citation(BaseModel):
    observation_id: str
    quote: str


class ModelClaim(BaseModel):
    text: str
    citations: list[Citation] = Field(min_length=1, max_length=3)


class ModelDiagnosis(BaseModel):
    category: Category
    summary: str
    root_cause: str
    claims: list[ModelClaim] = Field(min_length=1, max_length=5)
    action: str


class VerifiedClaim(ModelClaim):
    supported: bool


class Diagnosis(BaseModel):
    status: Literal["cause_found", "no_incident", "insufficient_observations"]
    category: Category
    summary: str
    root_cause: str
    action: str
    claims: list[VerifiedClaim] = []
    used_model: bool = True


class RunStats(BaseModel):
    raw_chars: int
    compact_chars: int
    events: int
    templates: int
    masked_values: int
    prompt_tokens: int = 0
    completion_tokens: int = 0
    seconds: float = 0


class Baseline(BaseModel):
    category: Category
    root_cause: str
    claims_total: int
    claims_supported: int
    prompt_tokens: int
    seconds: float


class Report(BaseModel):
    scenario: str
    container: str
    image: str
    created_at: str
    diagnosis: Diagnosis
    observations: list[Observation]
    stats: RunStats
    baseline: Baseline | None = None
