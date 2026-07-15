from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


_GENERIC_ENTITIES = {
    "answer",
    "author",
    "bridge",
    "city",
    "company",
    "country",
    "country a",
    "date",
    "entity",
    "final answer",
    "final target",
    "location",
    "model",
    "network",
    "organization",
    "person",
    "place",
    "state",
    "target",
    "value",
    "year",
}

_ENTITY_TOKEN_ALIASES = {
    "mohamed": "mohammed",
    "mohammad": "mohammed",
    "muhammad": "mohammed",
}

_ORGANIZATION_SUFFIXES = {
    "co",
    "company",
    "corp",
    "corporation",
    "inc",
    "incorporated",
    "ltd",
    "limited",
    "llc",
}

_RELATION_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("manufacturer", ("manufacturer", "manufactured by", "produced by", "company that makes", "makes")),
    ("owned_vehicle_model", ("has model", "model of", "vehicle model", "car model", "owned model")),
    ("headquarters_location", ("headquarters location", "headquartered in", "headquarters", "based in", "main office")),
    ("administrative_location", ("administrative territorial entity", "administrative location")),
    ("located_in", ("located in", "location", "contains the", "country that contains")),
    ("death_year", ("death year", "died in", "year did", "date did", "death")),
    ("office_end_date", ("end of office", "office end", "term ended", "end date")),
    ("count", ("how many", "number of", "count", "amount of")),
    ("century", ("what century", "which century", "century")),
    ("author", ("written by", "author of", "author")),
    ("created_by", ("created by", "creator", "network created", "created")),
    ("named_after", ("named after",)),
    ("featured_character", ("featured character", "character featured", "featured in", "legendary figure featured")),
    ("record_label", ("record label", "label of")),
    ("parent_organization", ("parent organization", "parent company", "only group larger", "larger group")),
    ("president", ("president of", "officeholder", "president")),
    ("network", ("television network", "broadcast network", "network")),
    ("country", ("country of", "country",)),
    ("city", ("city of", "city",)),
    ("owned_vehicle_model", ("model",)),
)

_EXPECTED_OBJECT_TYPES = {
    "manufacturer": "organization",
    "owned_vehicle_model": "vehicle_model",
    "headquarters_location": "city",
    "administrative_location": "administrative_area",
    "located_in": "location",
    "death_year": "year",
    "office_end_date": "date",
    "count": "count",
    "century": "ordinal",
    "author": "person",
    "created_by": "organization",
    "named_after": "entity",
    "featured_character": "character",
    "record_label": "organization",
    "parent_organization": "organization",
    "president": "person",
    "network": "organization",
    "country": "country",
    "city": "city",
    "model": "entity",
}


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(character for character in text if not unicodedata.combining(character))
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return " ".join(text.split())


def canonical_hop_id(value: object) -> str:
    """Normalize supported legacy hop references without guessing unknown IDs."""

    raw = " ".join(str(value or "").strip().split())
    normalized = normalize_text(raw)
    patterns = (
        r"(?:required\s+)?hop\s+(\d+)",
        r"hop\s+index\s+(\d+)",
        r"(\d+)",
    )
    for pattern in patterns:
        match = re.fullmatch(pattern, normalized)
        if match:
            return f"required_hop_{int(match.group(1))}"
    return raw


def canonical_entity_id(value: object, entity_type: str = "") -> str:
    tokens = normalize_text(value).split()
    if tokens and tokens[0] == "the":
        tokens = tokens[1:]
    tokens = [_ENTITY_TOKEN_ALIASES.get(token, token) for token in tokens]
    if normalize_text(entity_type) in {"organization", "company", "network"}:
        while tokens and tokens[-1] in _ORGANIZATION_SUFFIXES:
            tokens.pop()
    return "_".join(tokens)


def is_generic_entity(value: object) -> bool:
    return normalize_text(value) in _GENERIC_ENTITIES


def canonical_relation_id(value: object) -> str:
    normalized = normalize_text(value)
    if not normalized:
        return ""
    padded = f" {normalized} "
    for relation_id, aliases in _RELATION_PATTERNS:
        if any(f" {normalize_text(alias)} " in padded for alias in aliases):
            return relation_id
    return normalized.replace(" ", "_")


def canonical_relation_hint(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    relation_piece = text.rsplit("->", 1)[-1].strip() if "->" in text else text
    normalized = normalize_text(relation_piece)
    padded = f" {normalized} "
    for relation_id, aliases in _RELATION_PATTERNS:
        if any(f" {normalize_text(alias)} " in padded for alias in aliases):
            return relation_id
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*(?:\s+[A-Za-z][A-Za-z0-9_-]*){0,3}", relation_piece):
        # Short relation labels such as event_after_departure are useful typed
        # hints. Longer prose/entity descriptions remain untyped and can only
        # resolve through a unique dependency frontier.
        return canonical_relation_id(relation_piece)
    return ""


def infer_expected_object_type(relation_id: str, object_value: object = "") -> str:
    canonical = canonical_relation_id(relation_id)
    if canonical in _EXPECTED_OBJECT_TYPES:
        return _EXPECTED_OBJECT_TYPES[canonical]
    value = normalize_text(object_value)
    if re.fullmatch(r"\d{4}", value):
        return "year"
    if re.fullmatch(r"\d+", value):
        return "number"
    return "entity"


def infer_subject_type(value: object) -> str:
    normalized = normalize_text(value)
    if not normalized:
        return "entity"
    if any(token in normalized for token in ("company", "corporation", "group", "network", "embassy")):
        return "organization"
    if any(token in normalized for token in ("city", "country", "state", "county", "bay")):
        return "location"
    if any(token in normalized for token in ("president", "governor", "author", "actor", "person")):
        return "person"
    return "entity"


def typed_hop_identity(
    record: dict,
    *,
    canonical_is_final_hop: bool,
    default_hop_id: str,
    dependency_hop_ids: tuple[str, ...] = (),
    dependency_object_entity_id: str = "",
) -> dict:
    subject = str(record.get("subject") or "").strip()
    subject_type = str(record.get("subject_type") or "").strip() or infer_subject_type(subject)
    subject_entity_id = str(record.get("subject_entity_id") or "").strip()
    if not subject_entity_id:
        subject_entity_id = canonical_entity_id(subject, subject_type)
    if (not subject_entity_id or is_generic_entity(subject)) and dependency_object_entity_id:
        subject_entity_id = dependency_object_entity_id
    relation_id = str(record.get("canonical_relation") or record.get("relation_id") or "").strip()
    relation_id = canonical_relation_id(relation_id or record.get("relation"))
    expected_type = str(record.get("expected_object_type") or "").strip()
    if not expected_type:
        expected_type = infer_expected_object_type(relation_id, record.get("object"))
    raw_dependencies = record.get("dependency_hop_ids")
    dependencies = dependency_hop_ids
    if isinstance(raw_dependencies, list) and all(isinstance(value, str) for value in raw_dependencies):
        dependencies = tuple(canonical_hop_id(value) for value in raw_dependencies if value)
    return {
        "hop_id": canonical_hop_id(record.get("hop_id") or default_hop_id),
        "subject_entity_id": subject_entity_id,
        "subject_type": normalize_text(subject_type).replace(" ", "_") or "entity",
        "relation_id": relation_id,
        "expected_object_type": normalize_text(expected_type).replace(" ", "_") or "entity",
        "dependency_hop_ids": dependencies,
        "is_final_hop": bool(canonical_is_final_hop),
    }


def relation_compatible(left: object, right: object) -> bool:
    left_id = canonical_relation_id(left)
    right_id = canonical_relation_id(right)
    return bool(left_id and right_id and left_id == right_id)


def entity_compatible(left: object, right: object, *, entity_type: str = "") -> bool:
    if is_generic_entity(left) or is_generic_entity(right):
        return True
    left_id = canonical_entity_id(left, entity_type)
    right_id = canonical_entity_id(right, entity_type)
    return bool(left_id and right_id and left_id == right_id)


@dataclass(frozen=True)
class HopUpdateResolution:
    status: str
    hop_id: str = ""
    reason: str = ""
    candidate_hop_ids: tuple[str, ...] = ()
    metadata: dict = field(default_factory=dict)

    def to_record(self) -> dict:
        return {
            "status": self.status,
            "hop_id": self.hop_id,
            "reason": self.reason,
            "candidate_hop_ids": list(self.candidate_hop_ids),
            "metadata": dict(self.metadata),
        }


def resolve_hop_update(hops: list[dict], incoming: dict, *, canonical_is_final_hop: bool) -> HopUpdateResolution:
    by_id = {
        canonical_hop_id(hop.get("hop_id")): hop
        for hop in hops
        if canonical_hop_id(hop.get("hop_id"))
    }
    explicit_id = canonical_hop_id(
        incoming.get("hop_id") or incoming.get("target_hop_id") or ""
    )
    if explicit_id:
        prior = by_id.get(explicit_id)
        if prior is None:
            return HopUpdateResolution("rejected", reason="unknown_hop_id")
        if not _identity_compatible(prior, incoming, canonical_is_final_hop=canonical_is_final_hop):
            return HopUpdateResolution("rejected", hop_id=explicit_id, reason="hop_identity_mismatch")
        return HopUpdateResolution("resolved", hop_id=explicit_id, reason="explicit_hop_id")

    matches = [
        hop
        for hop in hops
        if _identity_compatible(hop, incoming, canonical_is_final_hop=canonical_is_final_hop)
    ]
    if len(matches) == 1:
        return HopUpdateResolution(
            "resolved",
            hop_id=str(matches[0].get("hop_id") or ""),
            reason="unique_typed_identity",
        )
    if len(matches) > 1:
        return HopUpdateResolution(
            "ambiguous",
            reason="multiple_typed_hop_matches",
            candidate_hop_ids=tuple(str(hop.get("hop_id") or "") for hop in matches),
        )
    return HopUpdateResolution("unmapped", reason="no_typed_hop_match")


def normalize_missing_requirement(raw: object) -> dict:
    if isinstance(raw, dict):
        anchor = raw.get("anchor_entity")
        if isinstance(anchor, dict):
            anchor_name = str(anchor.get("canonical_name") or anchor.get("name") or "")
            anchor_id = str(anchor.get("entity_id") or "")
            anchor_type = str(anchor.get("entity_type") or "")
        else:
            anchor_name = str(anchor or "")
            anchor_id = str(raw.get("anchor_entity_id") or "")
            anchor_type = str(raw.get("anchor_entity_type") or "")
        relation = str(
            raw.get("canonical_relation")
            or raw.get("relation_id")
            or raw.get("target_relation")
            or raw.get("relation")
            or ""
        )
        return {
            "target_hop_id": canonical_hop_id(
                raw.get("target_hop_id") or raw.get("hop_id") or ""
            ),
            "anchor_entity": anchor_name,
            "anchor_entity_id": anchor_id or canonical_entity_id(anchor_name, anchor_type),
            "anchor_entity_type": normalize_text(anchor_type).replace(" ", "_"),
            "canonical_relation": canonical_relation_id(relation),
            "expected_object_type": normalize_text(raw.get("expected_object_type")).replace(" ", "_"),
            "missing_component": normalize_text(raw.get("missing_component") or "object").replace(" ", "_"),
            "suggested_query": " ".join(str(raw.get("suggested_query") or raw.get("single_hop_query") or "").split()),
            "raw_hint": " ".join(str(raw.get("raw_hint") or relation or anchor_name).split()),
        }
    text = " ".join(str(raw or "").split())
    normalized = normalize_text(text)
    canonical = canonical_hop_id(text)
    target_hop_id = canonical if canonical.startswith("required_hop_") else ""
    return {
        "target_hop_id": target_hop_id,
        "anchor_entity": "",
        "anchor_entity_id": "",
        "anchor_entity_type": "",
        "canonical_relation": "" if target_hop_id else canonical_relation_hint(text),
        "expected_object_type": "",
        "missing_component": "object",
        "suggested_query": "",
        "raw_hint": text,
    }


def resolve_missing_requirement(hops: list[dict], raw: object) -> HopUpdateResolution:
    requirement = normalize_missing_requirement(raw)
    by_id = {canonical_hop_id(hop.get("hop_id")): hop for hop in hops}
    repairable = [
        hop for hop in hops
        if str(hop.get("status") or "") not in {"verified", "conflicted"}
    ]
    verified_ids = {
        str(hop.get("hop_id") or "")
        for hop in hops
        if str(hop.get("status") or "") == "verified"
    }
    frontier = [
        hop for hop in repairable
        if set(hop.get("dependency_hop_ids") or ()).issubset(verified_ids)
    ]
    explicit_id = requirement["target_hop_id"]
    if explicit_id:
        hop = by_id.get(explicit_id)
        if hop is None:
            return HopUpdateResolution("rejected", reason="unknown_target_hop_id", metadata=requirement)
        if hop not in repairable:
            return HopUpdateResolution("rejected", hop_id=explicit_id, reason="target_hop_not_repairable", metadata=requirement)
        if hop not in frontier:
            return HopUpdateResolution("rejected", hop_id=explicit_id, reason="target_hop_dependencies_incomplete", metadata=requirement)
        mismatch_reason, mismatch = _requirement_mismatch(hop, requirement)
        if mismatch_reason:
            return HopUpdateResolution(
                "rejected",
                hop_id=explicit_id,
                reason=mismatch_reason,
                metadata={**requirement, "binding_mismatch": mismatch},
            )
        return HopUpdateResolution("resolved", hop_id=explicit_id, reason="explicit_target_hop_id", metadata=requirement)

    compatible = [hop for hop in frontier if _requirement_compatible(hop, requirement)]
    has_typed_signal = bool(
        requirement["anchor_entity_id"]
        or requirement["canonical_relation"]
        or requirement["expected_object_type"]
    )
    if len(compatible) == 1:
        return HopUpdateResolution(
            "resolved",
            hop_id=str(compatible[0].get("hop_id") or ""),
            reason="unique_typed_frontier_match" if has_typed_signal else "unique_dependency_frontier",
            metadata=requirement,
        )
    if len(compatible) > 1:
        return HopUpdateResolution(
            "ambiguous",
            reason="multiple_typed_frontier_matches",
            candidate_hop_ids=tuple(str(hop.get("hop_id") or "") for hop in compatible),
            metadata=requirement,
        )
    mismatch_reason, mismatch = _frontier_requirement_mismatch(frontier, requirement)
    return HopUpdateResolution(
        "unmapped",
        reason=mismatch_reason or "no_typed_frontier_match",
        metadata={**requirement, **({"binding_mismatch": mismatch} if mismatch else {})},
    )


def _identity_compatible(prior: dict, incoming: dict, *, canonical_is_final_hop: bool) -> bool:
    if bool(prior.get("is_final_hop")) != bool(canonical_is_final_hop):
        return False
    prior_relation = prior.get("relation_id") or prior.get("relation")
    incoming_relation = incoming.get("canonical_relation") or incoming.get("relation_id") or incoming.get("relation")
    if not relation_compatible(prior_relation, incoming_relation):
        return False
    prior_type = normalize_text(prior.get("expected_object_type")).replace(" ", "_")
    incoming_type = normalize_text(incoming.get("expected_object_type")).replace(" ", "_")
    if incoming_type and prior_type and incoming_type != prior_type:
        return False
    prior_subject_id = str(prior.get("subject_entity_id") or "")
    incoming_subject_id = str(incoming.get("subject_entity_id") or "")
    incoming_subject = incoming.get("subject")
    if not incoming_subject_id:
        incoming_subject_id = canonical_entity_id(incoming_subject, str(prior.get("subject_type") or ""))
    if prior_subject_id and incoming_subject_id and prior_subject_id != incoming_subject_id:
        if not is_generic_entity(prior.get("subject")) and not is_generic_entity(incoming_subject):
            dependency_object_ids = set(prior.get("dependency_object_entity_ids") or ())
            if incoming_subject_id not in dependency_object_ids:
                return False
    return True


def _requirement_compatible(hop: dict, requirement: dict) -> bool:
    relation = requirement.get("canonical_relation")
    if relation and not relation_compatible(hop.get("relation_id") or hop.get("relation"), relation):
        return False
    expected = normalize_text(requirement.get("expected_object_type")).replace(" ", "_")
    hop_expected = normalize_text(hop.get("expected_object_type")).replace(" ", "_")
    if expected and hop_expected and expected != hop_expected:
        return False
    anchor_id = str(requirement.get("anchor_entity_id") or "")
    if anchor_id:
        hop_subject_id = str(hop.get("subject_entity_id") or "")
        dependency_object_ids = set(hop.get("dependency_object_entity_ids") or ())
        if anchor_id != hop_subject_id and anchor_id not in dependency_object_ids:
            return False
    return True


def _requirement_mismatch(hop: dict, requirement: dict) -> tuple[str, dict]:
    relation = requirement.get("canonical_relation")
    hop_relation = hop.get("relation_id") or hop.get("relation")
    if relation and not relation_compatible(hop_relation, relation):
        return "hop_binding_relation_mismatch", {
            "component": "relation",
            "expected": canonical_relation_id(hop_relation),
            "observed": canonical_relation_id(relation),
        }
    expected = normalize_text(requirement.get("expected_object_type")).replace(" ", "_")
    hop_expected = normalize_text(hop.get("expected_object_type")).replace(" ", "_")
    if expected and hop_expected and expected != hop_expected:
        return "hop_binding_expected_type_mismatch", {
            "component": "expected_object_type",
            "expected": hop_expected,
            "observed": expected,
        }
    anchor_id = str(requirement.get("anchor_entity_id") or "")
    if anchor_id:
        hop_subject_id = str(hop.get("subject_entity_id") or "")
        dependency_object_ids = set(hop.get("dependency_object_entity_ids") or ())
        if anchor_id != hop_subject_id and anchor_id not in dependency_object_ids:
            return "hop_binding_subject_mismatch", {
                "component": "subject",
                "expected": hop_subject_id,
                "observed": anchor_id,
                "dependency_object_entity_ids": sorted(dependency_object_ids),
            }
    return "", {}


def _frontier_requirement_mismatch(frontier: list[dict], requirement: dict) -> tuple[str, dict]:
    if not frontier:
        return "", {}
    reasons = [_requirement_mismatch(hop, requirement) for hop in frontier]
    nonempty = [(reason, detail) for reason, detail in reasons if reason]
    if not nonempty:
        return "", {}
    reason_kinds = {reason for reason, _ in nonempty}
    if len(reason_kinds) == 1:
        reason = nonempty[0][0]
        return reason, {
            "component": nonempty[0][1].get("component", ""),
            "frontier_hop_ids": [str(hop.get("hop_id") or "") for hop in frontier],
            "candidates": [detail for _, detail in nonempty],
        }
    # A typed signal can fail different frontier hops for different reasons;
    # report the earliest semantic layer shared by the attempted mapping.
    priority = (
        "hop_binding_relation_mismatch",
        "hop_binding_expected_type_mismatch",
        "hop_binding_subject_mismatch",
    )
    for reason in priority:
        details = [detail for current, detail in nonempty if current == reason]
        if details:
            return reason, {
                "component": details[0].get("component", ""),
                "frontier_hop_ids": [str(hop.get("hop_id") or "") for hop in frontier],
                "candidates": details,
                "mixed_frontier_mismatch": True,
            }
    return "", {}
