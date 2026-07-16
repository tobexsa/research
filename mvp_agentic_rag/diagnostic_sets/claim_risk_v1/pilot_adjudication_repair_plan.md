# Pilot Adjudication Repair Plan

Source: `pilot_annotation_review_compact_2_1_fourth_audited.csv`.

Decision rule: convert `needs_fix` rows to `reviewed_ok` only when the note contains a concrete final diagnosis and the existing labels are schema-valid. Keep rows in adjudication when taxonomy or evidence pointers remain unresolved.

## verify_as_reviewed_ok (34)

- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::3hop1__144439_443779_52195::r2`
  - sample: `3hop1__144439_443779_52195` r2; risk/action: `repairable_missing_hop` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: needs_fix: candidate Francisco Guterres and the final East Timor president claim are supported, but the row evidence does not include the first-hop passage p2 showing Mulham Arufin's birthplace/country. Without the Mulham Arufin -> Indonesia hop, the full question chain is not sufficiently supported.
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::4hop1__13170_32392_823060_610794::r1`
  - sample: `4hop1__13170_32392_823060_610794` r1; risk/action: `wrong_target` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: needs_fix: current row cannot be reviewed_ok. candidate_answer is empty, final_answer_supported=false, evidence_sufficiency=insufficient, and all listed claims are unsupported. The retrieved evidence points to Confederate Arizona/Mesilla, not the South Carolina -> Columbia -> Forest Acres -> Richland County chain; repair the first-state/state-capital/county chain.
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::3hop1__145194_160545_62931::r1`
  - sample: `3hop1__145194_160545_62931` r1; risk/action: `repairable_missing_hop` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: needs_fix: not just answer extraction. Evidence supports Siddhi Savetsila born in Bangkok and The Beach filmed on Thai island Koh Phi Phi, but the row evidence does not include the Bangkok -> Thailand support passage (dataset support p5). Mark c3 unsupported and repair the missing location hop before answering.
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::4hop1__145494_698949_157828_162309::r2`
  - sample: `4hop1__145494_698949_157828_162309` r2; risk/action: `wrong_target` / `refine_query`
  - reason: Reviewer note asserts full evidence is insufficient and current labels encode a non-answer action.
  - note: fix: full evidence only gives Béla Linder/Death Mills/Madagascar/Yugoslavia fragments and does not establish the movie-language-country-Olympics chain
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::4hop1__152146_5274_458768_33632::r2`
  - sample: `4hop1__152146_5274_458768_33632` r2; risk/action: `wrong_target` / `refine_query`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: fix: full evidence mentions Kathmandu/SAARC and unrelated feast days but not Långa nätter's label, the larger group, or a May 4 feast
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::3hop1__222497_309482_27537::r2`
  - sample: `3hop1__222497_309482_27537` r2; risk/action: `repairable_missing_hop` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: fix: Roncalli left Venice for the conclave is supported, but full evidence does not show that Luigi Nono worked in Venice
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::3hop1__222497_309482_27537::r1`
  - sample: `3hop1__222497_309482_27537` r1; risk/action: `repairable_missing_hop` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: fix: p12 supports Roncalli leaving Venice for the conclave and p0 supports Luigi Nono as composer, but no passage connects Nono to Venice
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::4hop1__17192_17130_70784_79935::r1`
  - sample: `4hop1__17192_17130_70784_79935` r1; risk/action: `wrong_target` / `disambiguate_conflict`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: ambiguous: 'country that secured southern Lebanon' could refer to Israel or UN forces; need disambiguation first
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::3hop1__105767_443779_52195::r3`
  - sample: `3hop1__105767_443779_52195` r3; risk/action: `wrong_target` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: fix: evidence supports Indonesia/Susilo Bambang Yudhoyono, but the question asks for East Timor president; final answer is not supported
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::4hop1__151650_5274_458768_33637::r2`
  - sample: `4hop1__151650_5274_458768_33637` r2; risk/action: `critical_gap` / `refine_query`
  - reason: Reviewer note asserts full evidence is insufficient and current labels encode a non-answer action.
  - note: fix: full evidence contains Minneapolis and Desde El Principio/Sony label passages only; it does not establish the larger group headquarters city or the ethnic-minority count
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::2hop__10620_49084::r1`
  - sample: `2hop__10620_49084` r1; risk/action: `repairable_missing_hop` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: needs_fix: candidate Liam Garrigan is an alias of the gold answer, and p18 supports Garrigan playing King Arthur, but this row evidence does not include the supporting passage p2 that connects Arthur to Historia Regum Britanniae. The single bundled claim is therefore not fully supported by the retrieved evidence.
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__144439_443779_52195::r1`
  - sample: `3hop1__144439_443779_52195` r1; risk/action: `wrong_target` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: needs_fix: candidate_answer is already Francisco Guterres, but verifier claim/evidence drift to Susilo Bambang Yudhoyono/Indonesia. Evidence is missing the final East Timor president hop; do not treat current claim as supported.
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__105767_443779_52195::r3`
  - sample: `3hop1__105767_443779_52195` r3; risk/action: `wrong_target` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: fix: evidence supports Indonesia/Susilo Bambang Yudhoyono, but the question asks for East Timor president; final answer is not supported
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::3hop1__159803_89752_75165::r1`
  - sample: `3hop1__159803_89752_75165` r1; risk/action: `wrong_target` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: wrong target; Navigation Acts affected colonial New England, not California
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__140786_2053_5289::r3`
  - sample: `3hop1__140786_2053_5289` r3; risk/action: `wrong_target` / `disambiguate_conflict`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: needs_fix: target broadcaster should be CBS, not NBC. p5 supports Just Men!? aired on NBC, p17 lists ABC/CBS/NBC as major New York broadcasters, and p7 says CBS acquired Oriole Records. Claims resolving the target to NBC and the label to Sony Music are contradicted by the evidence, so this is a disambiguation conflict.
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::4hop1__131611_32392_823060_610794::r2`
  - sample: `4hop1__131611_32392_823060_610794` r2; risk/action: `wrong_target` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: missing hop: capitol of South Carolina is Columbia; need to find city bordering Columbia
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::2hop__131951_643670::r1`
  - sample: `2hop__131951_643670` r1; risk/action: `wrong_target` / `disambiguate_conflict`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: fix: p10 says Het Scheur flows from the Oude Maas/Nieuwe Maas confluence and then continues as Nieuwe Waterweg, so candidate points to the downstream continuation rather than the gold target Het Scheur
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::4hop1__145494_698949_157828_162309::r3`
  - sample: `4hop1__145494_698949_157828_162309` r3; risk/action: `wrong_target` / `disambiguate_conflict`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: same as r2; need to identify movie named after Belgrade first
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::2hop__131951_643670::r1`
  - sample: `2hop__131951_643670` r1; risk/action: `wrong_target` / `disambiguate_conflict`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: fix: p10 says Het Scheur flows from the Oude Maas/Nieuwe Maas confluence and then continues as Nieuwe Waterweg, so candidate points to the downstream continuation rather than the gold target Het Scheur
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__103881_443779_52195::r3`
  - sample: `3hop1__103881_443779_52195` r3; risk/action: `wrong_target` / `disambiguate_conflict`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: c3 wrong; Susilo Bambang Yudhoyono is Indonesia's president, not East Timor's
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::4hop1__105401_17130_70784_79935::r2`
  - sample: `4hop1__105401_17130_70784_79935` r2; risk/action: `wrong_target` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: no evidence about Strangers No More in provided passages; need to identify its location first
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::2hop__10620_49084::r2`
  - sample: `2hop__10620_49084` r2; risk/action: `repairable_missing_hop` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: needs_fix: c1 is supported by p18 (Liam Garrigan plays King Arthur), but c2 is not supported by the cited evidence. The current evidence cites King Arthur/Historia Brittonum and Catellus/Cherin in Historia Regum Britanniae, but it omits dataset support p2, which is the passage that states Historia Regum Britanniae contains stories and legends about Arthur.
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::2hop__247353_55227::r2`
  - sample: `2hop__247353_55227` r2; risk/action: `wrong_target` / `disambiguate_conflict`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: needs_fix: c1 is contradicted rather than merely unsupported. p6 identifies Kevin James as a Here Comes the Boom screenwriter/actor; p17 says Salma Hayek plays Lenny/Adam Sandler's wife, while Eric/Kevin James's wife Sally is played by Maria Bello. Keep wrong_target=true and treat as disambiguation conflict.
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::2hop__244193_461106::r2`
  - sample: `2hop__244193_461106` r2; risk/action: `wrong_target` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: no evidence about Washington Monument creator; need to identify architect first
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::4hop1__264443_49925_13759_736921::r2`
  - sample: `4hop1__264443_49925_13759_736921` r2; risk/action: `repairable_missing_hop` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: fix: full evidence supports Luther and a sermon at Wittenberg, but it does not state that Wittenberg is in Saxony-Anhalt
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::2hop__132854_417697::r2`
  - sample: `2hop__132854_417697` r2; risk/action: `repairable_missing_hop` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: needs_fix: dataset is reliable; the corpus has supporting passage p6 for Mohamed Atta's Nissan Altima and p10 for Datsun Type 12 -> Nissan. The current row retrieved Nissan/Datsun evidence but missed the Mohamed Atta -> Nissan Altima passage, so this is a repairable missing-hop retrieval failure, not a spurious association or wrong target.
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__145194_160545_62931::r1`
  - sample: `3hop1__145194_160545_62931` r1; risk/action: `repairable_missing_hop` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: needs_fix: candidate Koh Phi Phi matches the gold answer, and evidence supports The Beach was filmed on Thai island Koh Phi Phi and Siddhi Savetsila was born in Bangkok. However c3 (Bangkok is located in Thailand) is not supported by the cited row evidence; the dataset support passage p5 is missing from the retrieved evidence, so the full multi-hop chain is not sufficient.
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__222497_309482_27537::r3`
  - sample: `3hop1__222497_309482_27537` r3; risk/action: `repairable_missing_hop` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: fix: p12 supports Roncalli leaving Venice for the conclave, but full evidence does not support the claim that Al gran sole carico d'amore composer Luigi Nono worked in Venice
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__144439_443779_52195::r2`
  - sample: `3hop1__144439_443779_52195` r2; risk/action: `repairable_missing_hop` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: needs_fix: same issue as row 5. The evidence supports Francisco Guterres as East Timor president, but it omits p2 for Mulham Arufin's birthplace/country, so the full multi-hop chain remains incomplete.
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::4hop1__151650_5274_458768_33632::r1`
  - sample: `4hop1__151650_5274_458768_33632` r1; risk/action: `wrong_target` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: same as #11; chain from Desde El Principio to larger group to feast day is broken
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::2hop__153573_44085::r1`
  - sample: `2hop__153573_44085` r1; risk/action: `wrong_target` / `disambiguate_conflict`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: needs_fix: c1 should be contradicted. p14 says Mickey's Safari in Letterland stars Mickey Mouse, and p2 identifies The Mickey Mouse Club; Metal Mickey is a different character/show from p9. Treat as wrong-target/disambiguation conflict, not merely an unsupported missing hop.
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::3hop1__108833_720914_41132::r3`
  - sample: `3hop1__108833_720914_41132` r3; risk/action: `repairable_missing_hop` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: fix: full evidence supports Titian as the painter and Venice plague count 22, but it lacks the critical hop that Titian died in Venice
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::2hop__153573_44085::r3`
  - sample: `2hop__153573_44085` r3; risk/action: `wrong_target` / `disambiguate_conflict`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: needs_fix: same as row 57. The evidence distinguishes Mickey Mouse from Metal Mickey and includes the correct target passage for The Mickey Mouse Club; mark the Metal Mickey claim as contradicted and use disambiguate_conflict.
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::4hop1__166471_49925_13759_736921::r1`
  - sample: `4hop1__166471_49925_13759_736921` r1; risk/action: `repairable_missing_hop` / `repair_missing_hop`
  - reason: Reviewer note gives a concrete final diagnosis and the row labels are schema-valid.
  - note: needs_fix: current evidence supports only the Egidio Vagnozzi/Catholic Church side. It does not retrieve the Luther -> Wittenberg sermon passage or the Wittenberg -> Saxony-Anhalt passage. This is a repairable missing-hop case, not a true wrong-target case.

## hold_adjudication (2)

- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::4hop1__151650_5274_458768_33637::r2`
  - sample: `4hop1__151650_5274_458768_33637` r2; risk/action: `wrong_target` / `repair_missing_hop`
  - reason: No clear final diagnosis pattern matched.
  - note: chain broken; evidence about Santa Monica ethnic minorities may not be relevant to target city
- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think::4hop1__17192_17130_70784_79935::r3`
  - sample: `4hop1__17192_17130_70784_79935` r3; risk/action: `wrong_target` / `disambiguate_conflict`
  - reason: Evidence pointer/corpus mismatch must be repaired before verification.
  - note: needs_fix: same wrong-target/disambiguation problem as r1, and claims c2/c4 cite evidence id 4hop2__9988_158985_70784_79935::p4, which is absent from musique_corpus.jsonl and from the row evidence preview. Correct the evidence pointer before using this row for mapping.

## schema_decision_needed (1)

- `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think::2hop__151750_141308::r1`
  - sample: `2hop__151750_141308` r1; risk/action: `answer_extraction_failure` / `answer`
  - reason: Answer-extraction failure is not a first-class risk type; keep out of verified set until taxonomy is decided.
  - note: needs_fix: claims c1-c3 are supported by the evidence chain Magic Christian Music -> Apple Records -> division of Apple Corps Ltd., but candidate_answer is empty. Treat as answer extraction/no-final-answer failure; oracle should answer Apple Corps.

## Taxonomy Cleanup Decision

- `answer_extraction_failure` is promoted to a formal `risk_type` before full batch generation. It captures cases where evidence and critical claims are sufficient, but runtime answer extraction/final-answer emission failed.
- The pilot row `2hop__151750_141308::r1` can now be `reviewed_ok` without mapping it to `critical_gap`.
