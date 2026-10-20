"""Human-review export only. No GitHub client or write capability."""

from devswarm.shared.contracts import BugDraft


def export(draft: BugDraft) -> str:
    return draft.model_dump_json(indent=2)
