from __future__ import annotations

from dataclasses import dataclass, field

from .schemas import VerifierOutput


@dataclass(frozen=True)
class EvidenceUtilizationAssessment:
    evidence_present_but_unresolved: bool = False
    reason: str = ""
    evidence_ids: list[str] = field(default_factory=list)


def assess_evidence_utilization(
    verifier_output: VerifierOutput,
    retrieved_evidence_ids: set[str],
    accepted_evidence_ids: set[str],
    min_existing_evidence_ids: int = 1,
) -> EvidenceUtilizationAssessment:
    del retrieved_evidence_ids
    existing_ids = set(accepted_evidence_ids)
    unresolved_existing_ids: list[str] = []
    for claim in verifier_output.claims:
        if not claim.is_critical:
            continue
        if claim.status not in {"unsupported", "unclear", "contradicted"}:
            continue
        for evidence_id in claim.evidence_ids:
            if evidence_id in existing_ids and evidence_id not in unresolved_existing_ids:
                unresolved_existing_ids.append(evidence_id)
    if len(unresolved_existing_ids) < min_existing_evidence_ids:
        return EvidenceUtilizationAssessment()
    return EvidenceUtilizationAssessment(
        evidence_present_but_unresolved=True,
        reason="evidence_present_but_unresolved",
        evidence_ids=unresolved_existing_ids,
    )
