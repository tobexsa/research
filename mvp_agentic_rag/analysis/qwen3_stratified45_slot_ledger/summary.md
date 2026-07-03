# Qwen3 Stratified45 Explicit Slot Ledger Pilot

## Headline

- Explicit slot ledger is compared on the same 15 x 2-hop, 15 x 3-hop, 15 x 4-hop stratified gate.
- The run uses only `claim_risk`, with guarded closure + cost cleanup + soft final-target prompt constraints kept enabled.

## Per-Hop Claim Risk Comparison
| run | hop | n | answer_f1 | coverage | selective_answer_f1 | avg_rounds | slot_answer | slot_missing | slot_next_query | closure_success | nonjson |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 2hop | 15 | 0.5000 | 0.7333 | 0.6818 | 1.6000 | 0 | 0 | 0 | 1 | 0 |
| baseline | 3hop | 15 | 0.1903 | 0.3333 | 0.5710 | 2.2000 | 0 | 0 | 0 | 1 | 0 |
| baseline | 4hop | 15 | 0.1000 | 0.3333 | 0.3000 | 2.5333 | 0 | 0 | 0 | 5 | 1 |
| baseline | all | 45 | 0.2634 | 0.4667 | 0.5645 | 2.1111 | 0 | 0 | 0 | 7 | 1 |
| soft_binding | 2hop | 15 | 0.4867 | 0.7333 | 0.6636 | 1.4667 | 0 | 0 | 0 | 0 | 0 |
| soft_binding | 3hop | 15 | 0.2570 | 0.4667 | 0.5507 | 2.0000 | 0 | 0 | 0 | 2 | 0 |
| soft_binding | 4hop | 15 | 0.1000 | 0.3333 | 0.3000 | 2.4667 | 0 | 0 | 0 | 4 | 0 |
| soft_binding | all | 45 | 0.2812 | 0.5111 | 0.5502 | 1.9778 | 0 | 0 | 0 | 6 | 0 |
| strict_slot | 2hop | 15 | 0.3533 | 0.5333 | 0.6625 | 1.6000 | 0 | 0 | 0 | 0 | 0 |
| strict_slot | 3hop | 15 | 0.0703 | 0.2667 | 0.2637 | 2.1333 | 0 | 0 | 0 | 2 | 0 |
| strict_slot | 4hop | 15 | 0.1000 | 0.2000 | 0.5000 | 2.5333 | 0 | 0 | 0 | 2 | 0 |
| strict_slot | all | 45 | 0.1746 | 0.3333 | 0.5237 | 2.0889 | 0 | 0 | 0 | 4 | 0 |
| explicit_slot_ledger | 2hop | 15 | 0.5422 | 0.8000 | 0.6778 | 1.4000 | 11 | 1 | 6 | 2 | 0 |
| explicit_slot_ledger | 3hop | 15 | 0.3237 | 0.6000 | 0.5394 | 2.0667 | 11 | 0 | 13 | 4 | 0 |
| explicit_slot_ledger | 4hop | 15 | 0.1000 | 0.4000 | 0.2500 | 2.1333 | 6 | 0 | 14 | 6 | 0 |
| explicit_slot_ledger | all | 45 | 0.3220 | 0.6000 | 0.5366 | 1.8667 | 28 | 1 | 33 | 12 | 0 |

## Closure Success Quality
| run | successes | exact_f1_1 | partial_positive | f1_zero | mean_f1 |
|---|---:|---:|---:|---:|---:|
| baseline | 7 | 2 | 1 | 4 | 0.3571 |
| soft_binding | 6 | 0 | 1 | 5 | 0.0833 |
| strict_slot | 4 | 0 | 1 | 3 | 0.1250 |
| explicit_slot_ledger | 12 | 2 | 3 | 7 | 0.2599 |

## Largest Improvements vs Soft Binding
| id | hop | delta | soft | slot_ledger | gold | slot_answer | slot_missing | question |
|---|---|---:|---|---|---|---:|---:|---|
| 3hop1__140786_2053_5289 | 3hop | 1.000 | abstain  r2 f1=0.000 | answer Oriole Records r2 f1=1.000 | Oriole Records. | 1 | 0 | What UK label was bought by the major broadcaster that, along with ABC and the network of the show Just Men!?, is based in New York? |
| 2hop__167577_31122 | 2hop | 1.000 | abstain  r3 f1=0.000 | answer 18th r2 f1=1.000 | 18th | 1 | 0 | What century did the author of A Treatise Concerning the Principles of Human Knowledge live in? |
| 2hop__153573_44085 | 2hop | 0.333 | abstain  r2 f1=0.000 | answer Metal Mickey r2 f1=0.333 | The Mickey Mouse Club | 0 | 0 | What was the show named after the character featured in the video game Mickey's Safari in Letterland? |
| 4hop1__28352_53706_795904_580996 | 4hop | 0.000 | answer Canada r3 f1=0.000 | answer Canada r3 f1=0.000 | Rio Linda | 0 | 0 | What shares a border with the city where the person who went to the state where the planes were originally going on 9/11 during the gold rush works? |
| 4hop1__264443_49925_13759_736921 | 4hop | 0.000 | abstain  r2 f1=0.000 | abstain  r2 f1=0.000 | Saxony-Anhalt | 1 | 0 | Where is the district that the person who wanted to reform and address Edward Egan's religion preached a sermon on Marian devotion before his death located? |
| 4hop1__236903_153080_33897_81096 | 4hop | 0.000 | abstain  r3 f1=0.000 | abstain  r3 f1=0.000 | Mario Andretti | 1 | 0 | Who won the indy car race in the most populated city of the state where the performer of East Coasting is from? |
| 4hop1__17192_17130_70784_79935 | 4hop | 0.000 | abstain  r3 f1=0.000 | abstain  r2 f1=0.000 | 1930 | 0 | 0 | When was the region immediately north of the region where the country that secured southern Lebanon is located and the Persian Gulf created? |
| 4hop1__166471_49925_13759_736921 | 4hop | 0.000 | abstain  r2 f1=0.000 | abstain  r2 f1=0.000 | Saxony-Anhalt | 0 | 0 | In what state is the district where the one who wanted to reform and address the institution behind the religion of Egidio Vagnozzi preached a sermon? |
| 4hop1__161810_583746_457883_650651 | 4hop | 0.000 | answer NBC r3 f1=1.000 | answer NBC r2 f1=1.000 | NBC | 0 | 0 | Country A has an embassy from the country that contains the bay where the city of General Santos is located. What network created country A's version of The Biggest Loser |
| 4hop1__161605_32392_823060_610794 | 4hop | 0.000 | answer Charleston County r2 f1=0.500 | answer Charleston County r2 f1=0.500 | Richland County | 1 | 0 | What county is the city that shares a border with the state capital of the state where Darlington County located in? |
| 4hop1__152146_5274_458768_33632 | 4hop | 0.000 | answer 18 November r1 f1=0.000 | answer 18 November r1 f1=0.000 | May 4 | 0 | 0 | What day is the Feast held in the city where the headquarters of the only group larger than Långa nätter's record label is located? |
| 4hop1__151650_5274_458768_33637 | 4hop | 0.000 | abstain  r3 f1=0.000 | abstain  r2 f1=0.000 | two | 0 | 0 | How many ethnic minorities were looked at differently in the city where the headquarters of the only group larger than Desde El Principio's record label is located? |

## Largest Regressions vs Soft Binding
| id | hop | delta | soft | slot_ledger | gold | slot_answer | slot_missing | question |
|---|---|---:|---|---|---|---:|---:|---|
| 2hop__23459_35124 | 2hop | -0.500 | answer 450 r1 f1=1.000 | answer More than 450 r1 f1=0.500 | 450 | 1 | 0 | How many books were said to be written by the most influential in Islamic philosophy? |
| 2hop__10620_49084 | 2hop | 0.000 | answer Liam Garrigan r1 f1=0.800 | answer Liam Garrigan r1 f1=0.800 | Liam Thomas Garrigan | 1 | 0 | Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time? |
| 2hop__129721_40482 | 2hop | 0.000 | answer Edmund Bellinger r1 f1=1.000 | answer Edmund Bellinger r1 f1=1.000 | Edmund Bellinger | 1 | 0 | From whom did the Huguenots in the state encompassing Zubly Cemetery purchase land from? |
| 2hop__131951_643670 | 2hop | 0.000 | answer Nieuwe Maas River r1 f1=0.000 | answer Nieuwe Maas River r1 f1=0.000 | Het Scheur | 1 | 0 | What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum? |
| 2hop__132854_417697 | 2hop | 0.000 | abstain  r2 f1=0.000 | abstain  r2 f1=0.000 | Nissan Altima | 0 | 0 | Mohammed Atta has what kind of model of the company that makes Datsun Type 12? |
| 2hop__136179_13529 | 2hop | 0.000 | answer June 1982 r1 f1=1.000 | answer June 1982 r1 f1=1.000 | June 1982 | 1 | 0 | When was the player that Iglesia Maradoniana is named after signed by Barcelona? |
| 2hop__142699_67465 | 2hop | 0.000 | answer March 11, 2011 r1 f1=1.000 | answer March 11, 2011. r1 f1=1.000 | March 11, 2011 | 1 | 0 | When did the rapper on On and On and Beyond release Best day Ever? |
| 2hop__151750_141308 | 2hop | 0.000 | answer Apple Records r1 f1=0.500 | answer Apple Records r1 f1=0.500 | Apple Corps | 1 | 0 | What company is the record label of Magic Christian Music part of? |
| 2hop__194469_83289 | 2hop | 0.000 | answer Matt Bennett r1 f1=1.000 | answer Matt Bennett r1 f1=1.000 | Matt Bennett | 1 | 0 | Who is the guy in the One Last Time video by the participant in The Listening Sessions? |
| 2hop__20268_42014 | 2hop | 0.000 | answer 2 r1 f1=1.000 | answer 2 r1 f1=1.000 | 2 | 1 | 0 | How many members in the seats of the organization that enacted the Directory of Public Worship into law are members of the Scottish Government? |
| 2hop__244193_461106 | 2hop | 0.000 | abstain  r3 f1=0.000 | abstain  r2 f1=0.000 | Greek Revival | 0 | 0 | What movement does the creator of the Washington Monument belong to? |
| 2hop__247353_55227 | 2hop | 0.000 | answer Salma Hayek r2 f1=0.000 | answer Salma Hayek r2 f1=0.000 | Maria Bello | 1 | 0 | Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups? |

## Slot-Ledger Mechanism Counts
- slot-answer cases: 28
- final-target-missing cases: 1
- contamination hits: think=0, nonjson=0

## Interpretation
- The explicit slot ledger clears the stratified45 promotion gate numerically: it beats guarded baseline and soft binding on overall answer_f1 and cost-normalized F1 while keeping final_answered_unsupported_rate at 0.
- The gain is mainly from higher coverage and lower average retrieval calls. Per-hop inspection is required before any larger run because 4-hop remains the hard boundary.
- This is a better direction than strict post-hoc slot binding: it does not hard-reject date answers as date components, and it shifts target binding before final answer generation.
- Recommended next step: inspect the largest regressions and 4-hop failures, then run a slightly larger stratified subset only if no new wrong-target safety issue appears in manual closure/slot inspection.
