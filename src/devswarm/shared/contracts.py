from typing import Annotated, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Incident(Contract):
    model_config = ConfigDict(revalidate_instances="always")

    service: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$")
    environment: str = Field(min_length=1, max_length=40, pattern=r"^[a-zA-Z0-9_.-]+$")
    exception_type: str = Field(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_.]+$")
    message: str = Field(min_length=1, max_length=4000)
    stack: list[Annotated[str, StringConstraints(min_length=1, max_length=1000)]] = Field(
        default_factory=list, max_length=30
    )
    occurred_at: AwareDatetime
    sanitized: Literal[True]

    @field_validator("sanitized", mode="before")
    @classmethod
    def require_explicit_boolean(cls, value):
        if value is not True:
            raise ValueError("sanitized must be the JSON boolean true")
        return value


class Evidence(Contract):
    id: str
    field: str
    excerpt: str


class Observation(Contract):
    statement: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)


class BugDraft(Contract):
    fingerprint: str
    title: str
    summary: str
    evidence: list[Evidence] = Field(min_length=1)
    observations: list[Observation] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    hypotheses: list[str]
    reproduction: list[str]
    status: Literal["needs_human_review"] = "needs_human_review"
    provider: str = "local-deterministic"

    @model_validator(mode="after")
    def valid_evidence_references(self):
        ids = [evidence.id for evidence in self.evidence]
        if len(ids) != len(set(ids)):
            raise ValueError("Evidence IDs must be unique")
        for observation in self.observations:
            if not set(observation.evidence_ids).issubset(ids):
                raise ValueError("Observation refers to unavailable evidence")
        return self


class Receipt(Contract):
    fingerprint: str
    occurrences: int
    duplicate: bool
    state: str
