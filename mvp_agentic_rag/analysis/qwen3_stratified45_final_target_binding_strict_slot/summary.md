# Stratified45 Strict Slot Binding Pilot

## Per-Hop Claim Risk Comparison
| run | hop | n | answer_f1 | coverage | selective_answer_f1 | avg_rounds | binding_reject | closure_not_final | closure_success | nonjson |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 2hop | 15 | 0.5000 | 0.7333 | 0.6818 | 1.6000 | 0 | 0 | 1 | 0 |
| baseline | 3hop | 15 | 0.1903 | 0.3333 | 0.5710 | 2.2000 | 0 | 0 | 1 | 0 |
| baseline | 4hop | 15 | 0.1000 | 0.3333 | 0.3000 | 2.5333 | 0 | 0 | 5 | 1 |
| baseline | all | 45 | 0.2634 | 0.4667 | 0.5645 | 2.1111 | 0 | 0 | 7 | 1 |
| soft_binding | 2hop | 15 | 0.4867 | 0.7333 | 0.6636 | 1.4667 | 0 | 0 | 0 | 0 |
| soft_binding | 3hop | 15 | 0.2570 | 0.4667 | 0.5507 | 2.0000 | 0 | 0 | 2 | 0 |
| soft_binding | 4hop | 15 | 0.1000 | 0.3333 | 0.3000 | 2.4667 | 0 | 0 | 4 | 0 |
| soft_binding | all | 45 | 0.2812 | 0.5111 | 0.5502 | 1.9778 | 0 | 0 | 6 | 0 |
| strict_slot | 2hop | 15 | 0.3533 | 0.5333 | 0.6625 | 1.6000 | 3 | 0 | 0 | 0 |
| strict_slot | 3hop | 15 | 0.0703 | 0.2667 | 0.2637 | 2.1333 | 3 | 0 | 2 | 0 |
| strict_slot | 4hop | 15 | 0.1000 | 0.2000 | 0.5000 | 2.5333 | 0 | 2 | 2 | 0 |
| strict_slot | all | 45 | 0.1746 | 0.3333 | 0.5237 | 2.0889 | 6 | 2 | 4 | 0 |

## Closure Success Quality
| run | successes | exact_f1_1 | partial_positive | f1_zero | mean_f1 |
|---|---:|---:|---:|---:|---:|
| baseline | 7 | 2 | 1 | 4 | 0.3571 |
| soft_binding | 6 | 0 | 1 | 5 | 0.0833 |
| strict_slot | 4 | 0 | 1 | 3 | 0.1250 |

## Strict Slot Reject Cases
| id | hop | soft | strict | gold | reject_slot | strict_minus_soft |
|---|---|---|---|---|---|---:|
| 2hop__136179_13529 | 2hop | answer June 1982 f1=1.000 | abstain  f1=0.000 | June 1982 | date component, date component | -1.000 |
| 2hop__142699_67465 | 2hop | answer March 11, 2011 f1=1.000 | abstain  f1=0.000 | March 11, 2011 | date component, date component | -1.000 |
| 2hop__249867_557232 | 2hop | answer Arizona f1=0.000 | abstain  f1=0.000 | Maricopa County | container/location | 0.000 |
| 3hop1__136129_87694_124169 | 3hop | answer 1952 f1=1.000 | abstain  f1=0.000 | 1952 | date component, date component | -1.000 |
| 3hop1__140786_2053_52946 | 3hop | answer February 7, 2018 f1=1.000 | abstain  f1=0.000 | February 7, 2018 | date component, date component | -1.000 |
| 3hop1__145194_160545_62931 | 3hop | answer Koh Phi Phi f1=0.800 | abstain  f1=0.000 | island Koh Phi Phi | container/location | -0.800 |
| 4hop1__145494_698949_157828_162309 | 4hop | answer 1920 f1=0.000 | abstain  f1=0.000 | 2016 |  | 0.000 |
| 4hop1__152146_5274_458768_33632 | 4hop | answer 18 November f1=0.000 | abstain  f1=0.000 | May 4 |  | 0.000 |

## Largest Strict Regressions vs Soft Binding
| id | hop | delta | soft | strict | gold | reject | question |
|---|---|---:|---|---|---|---:|---|
| 2hop__136179_13529 | 2hop | -1.000 | answer June 1982 r1 f1=1.000 | abstain  r2 f1=0.000 | June 1982 | 1 | When was the player that Iglesia Maradoniana is named after signed by Barcelona? |
| 2hop__142699_67465 | 2hop | -1.000 | answer March 11, 2011 r1 f1=1.000 | abstain  r2 f1=0.000 | March 11, 2011 | 1 | When did the rapper on On and On and Beyond release Best day Ever? |
| 3hop1__136129_87694_124169 | 3hop | -1.000 | answer 1952 r2 f1=1.000 | abstain  r3 f1=0.000 | 1952 | 1 | What year did the Governor of the city where the basilica named after the same saint as the one that Mantua Cathedral is dedicated to die? |
| 3hop1__140786_2053_52946 | 3hop | -1.000 | answer February 7, 2018 r1 f1=1.000 | abstain  r2 f1=0.000 | February 7, 2018 | 1 | When is Celebrity Big Brother coming to the broadcast company that, along with the network of Just Men!?, and ABC, is one of the major broadcasters based in New York? |
| 3hop1__145194_160545_62931 | 3hop | -0.800 | answer Koh Phi Phi r1 f1=0.800 | abstain  r1 f1=0.000 | island Koh Phi Phi | 1 | The Beach was filmed in what location of the country that contains the birth city of Siddhi Savetsila? |
| 2hop__167577_31122 | 2hop | 0.000 | abstain  r3 f1=0.000 | abstain  r3 f1=0.000 | 18th | 0 | What century did the author of A Treatise Concerning the Principles of Human Knowledge live in? |
| 2hop__129721_40482 | 2hop | 0.000 | answer Edmund Bellinger r1 f1=1.000 | answer Edmund Bellinger r1 f1=1.000 | Edmund Bellinger | 0 | From whom did the Huguenots in the state encompassing Zubly Cemetery purchase land from? |
| 2hop__131951_643670 | 2hop | 0.000 | answer Nieuwe Maas River r1 f1=0.000 | answer Nieuwe Maas River r1 f1=0.000 | Het Scheur | 0 | What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum? |
| 2hop__132854_417697 | 2hop | 0.000 | abstain  r2 f1=0.000 | abstain  r2 f1=0.000 | Nissan Altima | 0 | Mohammed Atta has what kind of model of the company that makes Datsun Type 12? |
| 2hop__151750_141308 | 2hop | 0.000 | answer Apple Records r1 f1=0.500 | answer Apple Records r1 f1=0.500 | Apple Corps | 0 | What company is the record label of Magic Christian Music part of? |
| 2hop__153573_44085 | 2hop | 0.000 | abstain  r2 f1=0.000 | abstain  r2 f1=0.000 | The Mickey Mouse Club | 0 | What was the show named after the character featured in the video game Mickey's Safari in Letterland? |
| 2hop__194469_83289 | 2hop | 0.000 | answer Matt Bennett r1 f1=1.000 | answer Matt Bennett r1 f1=1.000 | Matt Bennett | 0 | Who is the guy in the One Last Time video by the participant in The Listening Sessions? |

## Interpretation
- Strict slot binding reduced answer_f1 and coverage on the stratified gate. The hard slot requirement rejected several useful answers, including exact 2-hop and 3-hop cases, so the self-reported `answer_slot` is too noisy for a hard gate.
- The stricter gate did remove most closure successes, but this mostly suppresses both good and bad closure rather than selectively removing wrong-target closure.
- This result argues against promoting prompt-only strict slot binding to subset90/full300. The next useful method change is an explicit slot ledger that binds question decomposition targets to evidence, instead of trusting verifier self-labels after answer generation.
