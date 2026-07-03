from __future__ import annotations

import re
from dataclasses import dataclass, field

from .schemas import Passage, Sample, VerifierOutput


@dataclass(frozen=True)
class SlotPlan:
    final_target_type: str
    final_slot: str = "final_target"
    slot_names: list[str] = field(default_factory=lambda: ["bridge_1", "final_target"])

    def to_record(self) -> dict:
        return {
            "final_target_type": self.final_target_type,
            "final_slot": self.final_slot,
            "slot_names": self.slot_names,
        }


@dataclass
class SlotState:
    name: str
    status: str = "pending"
    evidence_ids: list[str] = field(default_factory=list)
    claims: list[str] = field(default_factory=list)
    source_queries: list[str] = field(default_factory=list)

    def add_claim(self, claim: str, evidence_ids: list[str], source_query: str = "") -> None:
        self.status = "supported"
        self.claims.append(claim)
        if source_query:
            self.source_queries.append(source_query)
        seen = set(self.evidence_ids)
        for evidence_id in evidence_ids:
            if evidence_id not in seen:
                self.evidence_ids.append(evidence_id)
                seen.add(evidence_id)

    def to_record(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "evidence_ids": list(self.evidence_ids),
            "claims": list(self.claims),
            "source_queries": list(self.source_queries),
        }


class SlotLedger:
    def __init__(self, plan: SlotPlan):
        self.plan = plan
        self.slots = {name: SlotState(name=name) for name in plan.slot_names}
        self._gap_signals: list[dict] = []
        self._gap_round_attempted: bool = False

    def _record_gap(self, verifier_output: VerifierOutput) -> None:
        """Record verifier rejection info for gap-directed query generation."""
        gap = {
            "final_target_match": verifier_output.final_target_match,
            "answer_slot": verifier_output.answer_slot,
            "missing_evidence": [
                {
                    "claim": claim.claim,
                    "status": claim.status,
                    "missing_evidence": claim.missing_evidence,
                }
                for claim in verifier_output.claims
                if claim.status in {"unsupported", "unclear", "contradicted"}
            ],
        }
        if gap["final_target_match"] is False or gap["missing_evidence"]:
            self._gap_signals.append(gap)

    def update_from_verifier(
        self,
        verifier_output: VerifierOutput,
        source_query: str = "",
        round_idx: int = 0,
        require_final_target_match: bool = False,
        sample_id: str = "",
        binding_policy: str = "heuristic",
    ) -> None:
        del round_idx
        for claim in verifier_output.claims:
            if claim.status != "supported" or not claim.evidence_ids:
                continue
            slot_name = (
                self.plan.final_slot
                if self._can_bind_final_target(
                    verifier_output,
                    claim.claim,
                    claim.evidence_ids,
                    require_final_target_match,
                    sample_id=sample_id,
                    binding_policy=binding_policy,
                )
                else self._bridge_slot_name()
            )
            self.slots[slot_name].add_claim(claim.claim, claim.evidence_ids, source_query=source_query)
        if not self.has_final_target_evidence():
            self._record_gap(verifier_output)

    def has_final_target_evidence(self) -> bool:
        return bool(self.final_target_evidence_ids())

    def final_target_evidence_ids(self) -> list[str]:
        return list(self.slots[self.plan.final_slot].evidence_ids)

    def final_target_evidence(self, evidence: list[Passage]) -> list[Passage]:
        target_ids = set(self.final_target_evidence_ids())
        return [passage for passage in evidence if passage.passage_id in target_ids]

    def answer_evidence(self, evidence: list[Passage]) -> list[Passage]:
        target_ids = set()
        for slot in self.slots.values():
            target_ids.update(slot.evidence_ids)
        return [passage for passage in evidence if passage.passage_id in target_ids]

    def complete_from_retrieved_evidence(self, sample: Sample, evidence: list[Passage]) -> dict:
        if self.plan.final_target_type not in {"date", "year", "century", "count", "population", "number"}:
            return {}
        for passage in evidence:
            if not _has_local_evidence([passage.passage_id], sample.sample_id):
                continue
            value = _extract_structured_final_value(
                self.plan.final_target_type,
                passage.text,
                question=sample.question,
            )
            if not value:
                continue
            claim = f"Retrieved evidence directly completes final {self.plan.final_target_type}: {value}"
            self.slots[self.plan.final_slot].add_claim(claim, [passage.passage_id], source_query="direct_completion")
            return {
                "value": value,
                "evidence_ids": [passage.passage_id],
                "target_type": self.plan.final_target_type,
            }
        return {}

    def next_query(self, original_question: str, verifier_suggested_query: str = "") -> str:
        if not self.has_final_target_evidence():
            if not self._gap_round_attempted:
                gap_query = self._build_gap_directed_query(
                    original_question, verifier_suggested_query
                )
                if gap_query:
                    self._gap_round_attempted = True
                    return gap_query
            bridge_query = _bridge_claim_final_query(original_question, self.plan.final_target_type, self.slots)
            if bridge_query:
                return bridge_query
            focus = _extract_focus(original_question)
            target = self.plan.final_target_type
            if focus:
                return f"What {target} answers {focus}?"
            if verifier_suggested_query:
                return _prefix_target_type(verifier_suggested_query, target)
            return f"What {target} is requested by: {original_question}"
        pending_bridge = next((slot for slot in self.slots.values() if slot.status != "supported"), None)
        if pending_bridge is not None:
            return verifier_suggested_query or original_question
        return verifier_suggested_query or original_question

    def _build_gap_directed_query(
        self, original_question: str, verifier_suggested_query: str = ""
    ) -> str:
        """Build a targeted follow-up query from verifier gap signals.

        Instead of a generic bridge query like "What person answers X?",
        ask a query that targets the specific evidence gap identified by the verifier.
        """
        if not self._gap_signals:
            return ""
        latest = self._gap_signals[-1]
        target_type = self.plan.final_target_type

        # Prefer verifier's suggested_query if it names a specific missing entity/relation
        suggested = (verifier_suggested_query or "").strip()
        if suggested and len(suggested) >= 10 and suggested != original_question:
            if not _is_generic_bridge_query(suggested, original_question, target_type):
                return _prefix_target_type(suggested, target_type)

        # Build gap query from missing_evidence claims
        missing_claims = [
            m for m in latest.get("missing_evidence", [])
            if m.get("missing_evidence", "").strip()
        ]
        if missing_claims:
            missing_text = missing_claims[0]["missing_evidence"].strip()
            # If missing_evidence is short and specific, use it directly
            if len(missing_text.split()) <= 15 and len(missing_text) >= 3:
                return f"{missing_text} ({target_type})"
            # Otherwise construct a targeted question from the first unsupported claim
            claim_text = missing_claims[0].get("claim", "")
            if claim_text and len(claim_text) >= 5:
                return f"Evidence directly supporting final {target_type}: {claim_text}"

        # Fallback: address the verifier's answer_slot mismatch
        answer_slot = latest.get("answer_slot", "")
        if answer_slot and answer_slot not in {"unknown", "final requested target"}:
            focus = _extract_focus(original_question)
            if focus:
                return f"What specific {target_type} value (not {answer_slot}) answers {focus}?"

        return ""

    def to_record(self) -> dict:
        return {
            "plan": self.plan.to_record(),
            "slots": {name: slot.to_record() for name, slot in self.slots.items()},
            "gap_signals": list(self._gap_signals),
            "gap_round_attempted": self._gap_round_attempted,
        }

    def _claim_matches_final_target(self, claim_text: str) -> bool:
        normalized = " ".join(str(claim_text or "").lower().split())
        target_type = self.plan.final_target_type
        if target_type in {"date", "year", "century"}:
            return _contains_date_value(normalized)
        if target_type in {"count", "population", "number"}:
            return bool(re.search(r"\b\d[\d,]*(?:\.\d+)?\b", normalized))
        if target_type in {"county", "city", "state", "country", "location", "place"}:
            return _contains_location_label(normalized, target_type)
        if target_type in {"person", "organization", "network", "company"}:
            return _contains_named_entity_signal(claim_text)
        return bool(normalized)

    def _can_bind_final_target(
        self,
        verifier_output: VerifierOutput,
        claim_text: str,
        evidence_ids: list[str],
        require_final_target_match: bool,
        sample_id: str = "",
        binding_policy: str = "heuristic",
    ) -> bool:
        policy = str(binding_policy or "heuristic").lower()
        if policy == "evidence":
            if sample_id and not _has_local_evidence(evidence_ids, sample_id):
                return False
            if verifier_output.final_target_match is False and not self._can_override_false_target_label(
                verifier_output.answer_slot,
                claim_text,
            ):
                return False
            return self._claim_matches_final_target(claim_text)
        if require_final_target_match and verifier_output.final_target_match is not True:
            return False
        return self._claim_matches_final_target(claim_text)

    def _can_override_false_target_label(self, answer_slot: str, claim_text: str) -> bool:
        if self.plan.final_target_type not in {"date", "year", "century"}:
            return False
        normalized_slot = " ".join(str(answer_slot or "").lower().split())
        if normalized_slot and normalized_slot not in {"date component", "unknown", "final requested target"}:
            return False
        return _contains_date_value(str(claim_text or "").lower())

    def _bridge_slot_name(self) -> str:
        for slot_name in self.plan.slot_names:
            if slot_name != self.plan.final_slot:
                return slot_name
        return self.plan.final_slot


def build_slot_plan(sample: Sample) -> SlotPlan:
    final_target_type = classify_final_target_type(sample.question)
    bridge_count = max(1, min(3, _estimate_bridge_count(sample.question)))
    slot_names = [f"bridge_{idx}" for idx in range(1, bridge_count + 1)]
    slot_names.append("final_target")
    return SlotPlan(final_target_type=final_target_type, slot_names=slot_names)


def classify_final_target_type(question: str) -> str:
    normalized = " ".join(str(question or "").lower().split())
    if normalized.startswith("when ") or " what day " in f" {normalized} " or "what date" in normalized:
        return "date"
    if "what year" in normalized:
        return "year"
    if "what century" in normalized:
        return "century"
    if normalized.startswith("who ") or " who " in f" {normalized} ":
        return "person"
    if "what county" in normalized:
        return "county"
    if "what city" in normalized:
        return "city"
    if "what state" in normalized or " in what state" in normalized:
        return "state"
    if "what country" in normalized:
        return "country"
    if normalized.startswith("where ") or " located" in normalized:
        return "location"
    if "population" in normalized:
        return "population"
    if normalized.startswith("how many ") or "how much" in normalized:
        return "count"
    if "what network" in normalized:
        return "network"
    if "what company" in normalized:
        return "company"
    return "entity"


def _estimate_bridge_count(question: str) -> int:
    normalized = " ".join(str(question or "").lower().split())
    markers = [
        " that ",
        " who ",
        " where ",
        " with ",
        " of ",
        " in ",
        " named after ",
        " author of ",
        " creator of ",
        " release ",
        " located ",
    ]
    return sum(1 for marker in markers if marker in normalized)


def _contains_date_value(text: str) -> bool:
    months = (
        "january|february|march|april|may|june|july|august|september|october|november|december|"
        "jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec"
    )
    return bool(
        re.search(rf"\b({months})\b", text)
        or re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", text)
        or re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", text)
        or re.search(r"\b\d{1,2}(?:st|nd|rd|th)\s+century\b", text)
    )


def _extract_structured_final_value(target_type: str, text: str, question: str = "") -> str:
    normalized_type = str(target_type or "").lower()
    source = str(text or "")
    normalized_question = " ".join(str(question or "").lower().split())
    cues = _direct_completion_cues(question, normalized_type)
    if normalized_type == "century":
        match = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)[-\s]+century\b", source, flags=re.IGNORECASE)
        if match:
            return f"{match.group(1)}th" if match.group(1).endswith("0") else _ordinal(match.group(1))
        return ""
    if normalized_type == "year":
        for cue in cues:
            cue_context = re.search(
                rf"\b(?:{cue})\b[^\d]{{0,80}}\b(1[0-9]{{3}}|20[0-9]{{2}})\b",
                source,
                flags=re.IGNORECASE,
            )
            if cue_context:
                return cue_context.group(1)
            reverse_context = re.search(
                rf"\b(1[0-9]{{3}}|20[0-9]{{2}})\b[^\n.;:]{{0,80}}\b(?:{cue})\b",
                source,
                flags=re.IGNORECASE,
            )
            if reverse_context:
                return reverse_context.group(1)
        if cues:
            return ""
        match = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", source)
        return match.group(1) if match else ""
    if normalized_type == "date":
        date_match = re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", source)
        if date_match and _value_has_direct_cue(source, date_match.group(0), cues):
            return date_match.group(0)
        month_names = (
            "January|February|March|April|May|June|July|August|September|October|November|December|"
            "Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
        )
        month_day_year = re.search(
            rf"\b(?:{month_names})\.?\s+\d{{1,2}},?\s+\d{{4}}\b",
            source,
            flags=re.IGNORECASE,
        )
        if month_day_year and _value_has_direct_cue(source, month_day_year.group(0), cues):
            return month_day_year.group(0).rstrip(".")
        day_month_year = re.search(
            rf"\b\d{{1,2}}\s+(?:{month_names})\.?\s+\d{{4}}\b",
            source,
            flags=re.IGNORECASE,
        )
        if day_month_year and _value_has_direct_cue(source, day_month_year.group(0), cues):
            return day_month_year.group(0).rstrip(".")
        if "what day" in normalized_question:
            return ""
        year_match = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", source)
        if year_match and cues and not _value_has_direct_cue(source, year_match.group(1), cues):
            return ""
        return year_match.group(1) if year_match else ""
    if normalized_type in {"count", "population", "number"}:
        if cues and not re.search(r"\b(?:" + "|".join(cues) + r")\b", source, flags=re.IGNORECASE):
            return ""
        match = re.search(r"\b\d[\d,]*(?:\.\d+)?\b", source)
        if match and cues and not _value_has_direct_cue(source, match.group(0), cues):
            return ""
        return match.group(0) if match else ""
    return ""


def _direct_completion_cues(question: str, target_type: str) -> list[str]:
    normalized = " ".join(str(question or "").lower().split())
    if target_type in {"count", "population", "number"}:
        cue_groups = [
            ({"occur", "occurred", "occurs", "times"}, ["occur", "occurred", "occurs", "times"]),
            ({"population"}, ["population"]),
            ({"count", "number", "total"}, ["count", "number", "total"]),
        ]
    else:
        cue_groups = [
            ({"death", "died", "die", "dies"}, ["death", "died", "die", "dies"]),
            ({"born", "birth"}, ["born", "birth"]),
            ({"release", "released"}, ["release", "released"]),
            ({"premiere", "premiered"}, ["premiere", "premiered"]),
            ({"published", "publication", "publish"}, ["published", "publication", "publish"]),
            ({"founded", "founding", "established", "formed"}, ["founded", "founding", "established", "formed"]),
            ({"created", "creation", "opened", "launched"}, ["created", "creation", "opened", "launched"]),
        ]
    cues: list[str] = []
    for triggers, group_cues in cue_groups:
        if any(trigger in normalized for trigger in triggers):
            cues.extend(group_cues)
    if target_type in {"count", "population", "number"} and not cues:
        cues.extend(["count", "number", "total", "population"])
    return list(dict.fromkeys(re.escape(cue) for cue in cues))


def _value_has_direct_cue(text: str, value: str, cues: list[str]) -> bool:
    if not cues:
        return True
    source = str(text or "")
    value_text = str(value or "")
    value_index = source.lower().find(value_text.lower())
    if value_index < 0:
        return False
    window_start = max(0, value_index - 100)
    window_end = min(len(source), value_index + len(value_text) + 100)
    window = source[window_start:window_end]
    return bool(re.search(r"\b(?:" + "|".join(cues) + r")\b", window, flags=re.IGNORECASE))


def _ordinal(number_text: str) -> str:
    number = int(number_text)
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def _contains_location_label(text: str, target_type: str) -> bool:
    if target_type in text:
        return True
    labels = ["county", "city", "state", "country", "district", "province", "island", "river"]
    return any(label in text for label in labels)


def _contains_named_entity_signal(text: str) -> bool:
    return bool(re.search(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", str(text or "")))


def _extract_focus(question: str) -> str:
    text = " ".join(str(question or "").split())
    quoted = re.findall(r'"([^"]+)"', text)
    if quoted:
        return quoted[-1]
    capitalized = re.findall(r"\b[A-Z][A-Za-z0-9!?&'.-]*(?:\s+[A-Z][A-Za-z0-9!?&'.-]*)*\b", text)
    stop = {"When", "What", "Who", "Where", "How", "The", "A", "An"}
    candidates = [item for item in capitalized if item.split()[0] not in stop]
    if candidates:
        return candidates[-1]
    return ""


def _bridge_claim_final_query(question: str, target_type: str, slots: dict[str, SlotState]) -> str:
    normalized_question = " ".join(str(question or "").lower().split())
    normalized_target = str(target_type or "").lower()
    if normalized_target == "century" and "live in" in normalized_question and "author of" in normalized_question:
        for claim in _bridge_claims(slots):
            author = _extract_author_subject(claim)
            if author:
                return f"What century did {author} live in?"
    return ""


def _bridge_claims(slots: dict[str, SlotState]) -> list[str]:
    claims: list[str] = []
    for name, slot in slots.items():
        if name == "final_target" or slot.status != "supported":
            continue
        claims.extend(slot.claims)
    return claims


def _extract_author_subject(claim: str) -> str:
    text = " ".join(str(claim or "").split())
    patterns = [
        r"^([A-Z][A-Za-z'.-]+(?:\s+[A-Z][A-Za-z'.-]+){1,4})\s+(?:wrote|authored|was the author of)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return ""


def _prefix_target_type(query: str, target_type: str) -> str:
    normalized = " ".join(str(query or "").split())
    if target_type in normalized.lower():
        return normalized
    return f"{normalized} ({target_type})"


def _is_generic_bridge_query(query: str, original_question: str, target_type: str) -> bool:
    """Check if query is a generic bridge pattern like 'What entity answers X?'."""
    normalized = " ".join(str(query or "").lower().split())
    generic_patterns = [
        rf"^what\s+(?:\S*\s?{re.escape(target_type)}|entity|thing|person|place|date|year|century|county|city|state|country|location|count|population|number|value|network|company)\s+answers?\b",
        r"^what\s+(?:entity|thing)\s+is\s+requested\s+by\b",
        r"^what\s+(?:entity|person|thing|date|year|value)\s+answers\s+[A-Z]",
    ]
    return any(re.search(pattern, normalized) for pattern in generic_patterns)


def _has_local_evidence(evidence_ids: list[str], sample_id: str) -> bool:
    prefix = f"{sample_id}::"
    return any(
        str(evidence_id).startswith(prefix) or _shares_musique_chain_suffix(str(evidence_id), sample_id)
        for evidence_id in evidence_ids
    )


def evidence_ids_are_local(evidence_ids: list[str], sample_id: str) -> bool:
    return _has_local_evidence(evidence_ids, sample_id)


def _shares_musique_chain_suffix(evidence_id: str, sample_id: str) -> bool:
    evidence_sample_id = str(evidence_id).split("::", 1)[0]
    sample_head, sample_parts = _split_musique_sample_id(sample_id)
    evidence_head, evidence_parts = _split_musique_sample_id(evidence_sample_id)
    if not sample_head or sample_head != evidence_head:
        return False
    if len(sample_parts) < 3 or len(evidence_parts) < 3:
        return False
    shared_suffix_len = 0
    for sample_part, evidence_part in zip(reversed(sample_parts), reversed(evidence_parts)):
        if sample_part != evidence_part:
            break
        shared_suffix_len += 1
    return shared_suffix_len >= 2


def _split_musique_sample_id(sample_id: str) -> tuple[str, list[str]]:
    if "__" not in str(sample_id):
        return "", []
    head, rest = str(sample_id).split("__", 1)
    return head, [part for part in rest.split("_") if part]
