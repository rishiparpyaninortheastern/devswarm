from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Incident(Contract):
    service: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$")
    environment: str = Field(min_length=1, max_length=40, pattern=r"^[a-zA-Z0-9_.-]+$")
    exception_type: str = Field(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_.]+$")
    message: str = Field(min_length=1, max_length=4000)
    stack: list[str] = Field(default_factory=list, max_length=30)
    occurred_at: AwareDatetime
    sanitized: Literal[True]


class Evidence(Contract):
    id: str
    field: str
    excerpt: str


class BugDraft(Contract):
    fingerprint: str
    title: str
    summary: str
    evidence: list[Evidence]
    hypotheses: list[str]
    reproduction: list[str]
    status: Literal["needs_human_review"] = "needs_human_review"
    provider: str = "local-deterministic"


class Receipt(Contract):
    fingerprint: str
    occurrences: int
    duplicate: bool
    state: str
