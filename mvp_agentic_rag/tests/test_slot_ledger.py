from __future__ import annotations

import unittest

from mvp_agentic_rag.schemas import ClaimAssessment, Passage, Sample, VerifierOutput
from mvp_agentic_rag.slot_ledger import SlotLedger, build_slot_plan


class SlotLedgerTests(unittest.TestCase):
    def test_builds_final_target_slot_for_date_question(self) -> None:
        sample = _sample("When did the rapper release Best Day Ever?")

        plan = build_slot_plan(sample)

        self.assertEqual("final_target", plan.final_slot)
        self.assertEqual("date", plan.final_target_type)
        self.assertIn("final_target", plan.slot_names)
        self.assertGreaterEqual(len(plan.slot_names), 2)

    def test_builds_final_target_slot_for_person_question(self) -> None:
        sample = _sample("Who won the 1993 Indy Car race in the city with the largest population?")

        plan = build_slot_plan(sample)

        self.assertEqual("person", plan.final_target_type)
        self.assertEqual("final_target", plan.final_slot)

    def test_network_final_question_is_not_overridden_by_bridge_location(self) -> None:
        plan = build_slot_plan(
            Sample(
                "s-network",
                (
                    "Country A contains the bay where General Santos is located. "
                    "What network created country A's version of The Biggest Loser?"
                ),
                "NBC",
            )
        )

        self.assertEqual("network", plan.final_target_type)

    def test_count_final_question_is_not_overridden_by_nested_location(self) -> None:
        plan = build_slot_plan(
            Sample(
                "s-count",
                "How many groups were discussed in the city where the label is located?",
                "two",
            )
        )

        self.assertEqual("count", plan.final_target_type)

    def test_binds_supported_final_target_claim_to_final_slot(self) -> None:
        sample = _sample("When did the rapper release Best Day Ever?")
        ledger = SlotLedger(build_slot_plan(sample))
        verifier_output = _verifier(
            [
                ClaimAssessment(
                    claim="Best Day Ever was released on March 11, 2011.",
                    status="supported",
                    evidence_ids=["p1"],
                    is_critical=True,
                )
            ]
        )

        ledger.update_from_verifier(verifier_output, source_query=sample.question, round_idx=1)

        self.assertTrue(ledger.has_final_target_evidence())
        self.assertEqual(["p1"], ledger.final_target_evidence_ids())
        self.assertEqual("supported", ledger.slots["final_target"].status)

    def test_strict_binding_does_not_bind_non_final_claim_to_final_slot(self) -> None:
        sample = _sample("Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups?")
        ledger = SlotLedger(build_slot_plan(sample))
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    claim="Salma Hayek plays the wife in Grown Ups.",
                    status="supported",
                    evidence_ids=["p1"],
                    is_critical=True,
                )
            ],
            overall_sufficiency="sufficient",
            need_more_evidence=False,
            final_target_match=False,
            answer_slot="intermediate entity",
        )

        ledger.update_from_verifier(
            verifier_output,
            source_query=sample.question,
            round_idx=1,
            require_final_target_match=True,
        )

        self.assertFalse(ledger.has_final_target_evidence())
        self.assertEqual(["p1"], ledger.slots["bridge_1"].evidence_ids)

    def test_evidence_binding_vetoes_explicit_non_final_match(self) -> None:
        sample = _sample("Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups?")
        ledger = SlotLedger(build_slot_plan(sample))
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    claim="Salma Hayek plays the wife in Grown Ups.",
                    status="supported",
                    evidence_ids=["s1::p1"],
                    is_critical=True,
                )
            ],
            overall_sufficiency="sufficient",
            need_more_evidence=False,
            final_target_match=False,
            answer_slot="intermediate entity",
        )

        ledger.update_from_verifier(
            verifier_output,
            source_query=sample.question,
            round_idx=1,
            sample_id=sample.sample_id,
            binding_policy="evidence",
        )

        self.assertFalse(ledger.has_final_target_evidence())
        self.assertEqual(["s1::p1"], ledger.slots["bridge_1"].evidence_ids)

    def test_evidence_binding_allows_century_final_value_despite_date_component_label(self) -> None:
        sample = _sample("What century did the author of A Treatise Concerning the Principles of Human Knowledge live in?")
        ledger = SlotLedger(build_slot_plan(sample))
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    claim="George Berkeley lived in the 18th century.",
                    status="supported",
                    evidence_ids=["s1::p10"],
                    is_critical=True,
                )
            ],
            overall_sufficiency="sufficient",
            need_more_evidence=False,
            final_target_match=False,
            answer_slot="date component",
        )

        ledger.update_from_verifier(
            verifier_output,
            source_query=sample.question,
            round_idx=1,
            sample_id=sample.sample_id,
            binding_policy="evidence",
        )

        self.assertTrue(ledger.has_final_target_evidence())
        self.assertEqual(["s1::p10"], ledger.final_target_evidence_ids())

    def test_evidence_binding_allows_local_evidence_without_boolean_self_report(self) -> None:
        sample = _sample("When did the rapper release Best Day Ever?")
        ledger = SlotLedger(build_slot_plan(sample))
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    claim="Best Day Ever was released on March 11, 2011.",
                    status="supported",
                    evidence_ids=["s1::p1"],
                    is_critical=True,
                )
            ],
            overall_sufficiency="sufficient",
            need_more_evidence=False,
            final_target_match=None,
        )

        ledger.update_from_verifier(
            verifier_output,
            source_query=sample.question,
            round_idx=1,
            sample_id=sample.sample_id,
            binding_policy="evidence",
        )

        self.assertTrue(ledger.has_final_target_evidence())
        self.assertEqual(["s1::p1"], ledger.final_target_evidence_ids())

    def test_evidence_binding_rejects_cross_sample_final_target_evidence(self) -> None:
        sample = _sample("What's the population of the largest state in the region?")
        ledger = SlotLedger(build_slot_plan(sample))
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    claim="The population of the largest state is 39.3 million.",
                    status="supported",
                    evidence_ids=["other_sample::p13"],
                    is_critical=True,
                )
            ],
            overall_sufficiency="sufficient",
            need_more_evidence=False,
            final_target_match=True,
        )

        ledger.update_from_verifier(
            verifier_output,
            source_query=sample.question,
            round_idx=1,
            sample_id=sample.sample_id,
            binding_policy="evidence",
        )

        self.assertFalse(ledger.has_final_target_evidence())
        self.assertEqual(["other_sample::p13"], ledger.slots["bridge_1"].evidence_ids)

    def test_evidence_binding_allows_musique_sibling_chain_evidence(self) -> None:
        sample = Sample(
            sample_id="3hop1__136129_87694_124169",
            question="What year did the Governor of the city where the basilica named after the same saint die?",
            gold_answer="1952",
        )
        ledger = SlotLedger(build_slot_plan(sample))
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    claim="The Governor of Vatican City died in 1952.",
                    status="supported",
                    evidence_ids=["3hop1__64957_87694_124169::p1", "3hop1__603558_87694_124169::p17"],
                    is_critical=True,
                )
            ],
            overall_sufficiency="sufficient",
            need_more_evidence=False,
            final_target_match=False,
            answer_slot="date component",
        )

        ledger.update_from_verifier(
            verifier_output,
            source_query=sample.question,
            round_idx=1,
            sample_id=sample.sample_id,
            binding_policy="evidence",
        )

        self.assertTrue(ledger.has_final_target_evidence())
        self.assertEqual(
            ["3hop1__64957_87694_124169::p1", "3hop1__603558_87694_124169::p17"],
            ledger.final_target_evidence_ids(),
        )

    def test_evidence_binding_rejects_unrelated_same_hop_evidence(self) -> None:
        sample = Sample(
            sample_id="3hop1__136129_87694_124169",
            question="What year did the Governor of the city where the basilica named after the same saint die?",
            gold_answer="1952",
        )
        ledger = SlotLedger(build_slot_plan(sample))
        verifier_output = VerifierOutput(
            claims=[
                ClaimAssessment(
                    claim="The Governor died in 1952.",
                    status="supported",
                    evidence_ids=["3hop1__999999_888888_777777::p1"],
                    is_critical=True,
                )
            ],
            overall_sufficiency="sufficient",
            need_more_evidence=False,
            final_target_match=False,
            answer_slot="date component",
        )

        ledger.update_from_verifier(
            verifier_output,
            source_query=sample.question,
            round_idx=1,
            sample_id=sample.sample_id,
            binding_policy="evidence",
        )

        self.assertFalse(ledger.has_final_target_evidence())

    def test_binds_supported_non_final_claim_to_bridge_slot(self) -> None:
        sample = _sample("When did the rapper on On and On and Beyond release Best Day Ever?")
        ledger = SlotLedger(build_slot_plan(sample))
        verifier_output = _verifier(
            [
                ClaimAssessment(
                    claim="The rapper on On and On and Beyond is Mac Miller.",
                    status="supported",
                    evidence_ids=["p_bridge"],
                    is_critical=True,
                )
            ]
        )

        ledger.update_from_verifier(verifier_output, source_query=sample.question, round_idx=1)

        self.assertFalse(ledger.has_final_target_evidence())
        self.assertEqual(["p_bridge"], ledger.slots["bridge_1"].evidence_ids)
        self.assertEqual("supported", ledger.slots["bridge_1"].status)

    def test_next_query_targets_pending_final_slot_after_bridge_is_supported(self) -> None:
        sample = _sample("When did the rapper on On and On and Beyond release Best Day Ever?")
        ledger = SlotLedger(build_slot_plan(sample))
        ledger.update_from_verifier(
            _verifier(
                [
                    ClaimAssessment(
                        claim="The rapper on On and On and Beyond is Mac Miller.",
                        status="supported",
                        evidence_ids=["p_bridge"],
                        is_critical=True,
                    )
                ]
            ),
            source_query=sample.question,
            round_idx=1,
        )

        query = ledger.next_query(sample.question, verifier_suggested_query="What is Best Day Ever?")

        self.assertIn("date", query.lower())
        self.assertIn("Best Day Ever", query)
        self.assertNotEqual(sample.question, query)

    def test_next_query_uses_supported_author_bridge_for_century_lived_question(self) -> None:
        sample = _sample("What century did the author of A Treatise Concerning the Principles of Human Knowledge live in?")
        ledger = SlotLedger(build_slot_plan(sample))
        ledger.update_from_verifier(
            _verifier(
                [
                    ClaimAssessment(
                        claim="George Berkeley wrote A Treatise Concerning the Principles of Human Knowledge.",
                        status="supported",
                        evidence_ids=["p_bridge"],
                        is_critical=True,
                    )
                ]
            ),
            source_query=sample.question,
            round_idx=1,
        )

        query = ledger.next_query(sample.question, verifier_suggested_query="A Treatise Concerning the Principles of Human Knowledge")

        self.assertIn("century", query.lower())
        self.assertIn("George Berkeley", query)
        self.assertIn("live", query.lower())
        self.assertNotIn("A Treatise Concerning", query)

    def test_filters_final_target_evidence_passages(self) -> None:
        sample = _sample("When did the rapper release Best Day Ever?")
        ledger = SlotLedger(build_slot_plan(sample))
        ledger.update_from_verifier(
            _verifier(
                [
                    ClaimAssessment(
                        claim="Best Day Ever was released on March 11, 2011.",
                        status="supported",
                        evidence_ids=["p1"],
                        is_critical=True,
                    )
                ]
            ),
            source_query=sample.question,
            round_idx=1,
        )

        evidence = [
            Passage("p1", "Best Day Ever", "Best Day Ever was released on March 11, 2011."),
            Passage("p2", "Mac Miller", "Mac Miller was an American rapper."),
        ]

        self.assertEqual(["p1"], [p.passage_id for p in ledger.final_target_evidence(evidence)])

    def test_to_record_returns_snapshot_not_live_slot_lists(self) -> None:
        sample = _sample("When did the rapper release Best Day Ever?")
        ledger = SlotLedger(build_slot_plan(sample))
        ledger.update_from_verifier(
            _verifier(
                [
                    ClaimAssessment(
                        claim="Best Day Ever was released on March 11, 2011.",
                        status="supported",
                        evidence_ids=["p1"],
                        is_critical=True,
                    )
                ]
            ),
            source_query=sample.question,
            round_idx=1,
        )
        record = ledger.to_record()

        ledger.update_from_verifier(
            _verifier(
                [
                    ClaimAssessment(
                        claim="Best Day Ever was released on March 12, 2011.",
                        status="supported",
                        evidence_ids=["p2"],
                        is_critical=True,
                    )
                ]
            ),
            source_query=sample.question,
            round_idx=2,
        )

        final_slot = record["slots"]["final_target"]
        self.assertEqual(["p1"], final_slot["evidence_ids"])
        self.assertEqual(["Best Day Ever was released on March 11, 2011."], final_slot["claims"])

    def test_direct_completion_prefers_death_year_for_year_question(self) -> None:
        sample = Sample(
            "s1",
            "What year did the Governor of Vatican City die?",
            "1952",
        )
        ledger = SlotLedger(build_slot_plan(sample))

        completion = ledger.complete_from_retrieved_evidence(
            sample,
            [
                Passage(
                    "s1::p1",
                    "Governor of Vatican City",
                    "The post was held by Marchese Camillo Serafini from the foundation of the state in 1929 until his death in 1952.",
                )
            ],
        )

        self.assertEqual("1952", completion["value"])
        self.assertEqual(["s1::p1"], ledger.final_target_evidence_ids())

    def test_direct_completion_rejects_intermediate_year_without_final_cue(self) -> None:
        sample = Sample(
            "s1",
            "What year did the writer's final film premiere?",
            "1930",
        )
        ledger = SlotLedger(build_slot_plan(sample))

        completion = ledger.complete_from_retrieved_evidence(
            sample,
            [
                Passage(
                    "s1::p1",
                    "Bridge person",
                    "The writer moved to Paris in 1990 and later collaborated with several filmmakers.",
                )
            ],
        )

        self.assertEqual({}, completion)
        self.assertEqual([], ledger.final_target_evidence_ids())

    def test_direct_completion_rejects_count_from_bridge_date(self) -> None:
        sample = Sample(
            "s1",
            "How many times did the plague occur in the city where the painter died?",
            "22",
        )
        ledger = SlotLedger(build_slot_plan(sample))

        completion = ledger.complete_from_retrieved_evidence(
            sample,
            [
                Passage(
                    "s1::p1",
                    "Painter",
                    "The painter died in 1523 after working in Venice for many years.",
                )
            ],
        )

        self.assertEqual({}, completion)
        self.assertEqual([], ledger.final_target_evidence_ids())

    def test_direct_completion_rejects_bare_year_for_day_question(self) -> None:
        sample = Sample(
            "s1",
            "What day is the Feast held in the city where the headquarters is located?",
            "May 4",
        )
        ledger = SlotLedger(build_slot_plan(sample))

        completion = ledger.complete_from_retrieved_evidence(
            sample,
            [
                Passage(
                    "s1::p1",
                    "Feast of Our Lady of the Rosary",
                    "The feast is celebrated on 7 October, the anniversary of a decisive victory in 1571.",
                )
            ],
        )

        self.assertEqual({}, completion)
        self.assertEqual([], ledger.final_target_evidence_ids())


def _sample(question: str) -> Sample:
    return Sample(sample_id="s1", question=question, gold_answer="")


def _verifier(claims: list[ClaimAssessment]) -> VerifierOutput:
    return VerifierOutput(
        claims=claims,
        overall_sufficiency="sufficient",
        need_more_evidence=False,
    )


if __name__ == "__main__":
    unittest.main()
