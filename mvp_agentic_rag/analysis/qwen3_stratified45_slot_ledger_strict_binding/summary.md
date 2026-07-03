# Qwen3 Stratified45 Slot Ledger Strict-Binding Pilot

## Per-Hop Comparison
| run | hop | n | answer_f1 | coverage | selective_answer_f1 | avg_rounds | zero_answered | slot_answer | slot_missing | closure_success | closure_not_final | nonjson |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 2hop | 15 | 0.5000 | 0.7333 | 0.6818 | 1.6000 | 3 | 0 | 0 | 1 | 0 | 0 |
| baseline | 3hop | 15 | 0.1903 | 0.3333 | 0.5710 | 2.2000 | 1 | 0 | 0 | 1 | 0 | 0 |
| baseline | 4hop | 15 | 0.1000 | 0.3333 | 0.3000 | 2.5333 | 3 | 0 | 0 | 5 | 0 | 1 |
| baseline | all | 45 | 0.2634 | 0.4667 | 0.5645 | 2.1111 | 7 | 0 | 0 | 7 | 0 | 1 |
| soft_binding | 2hop | 15 | 0.4867 | 0.7333 | 0.6636 | 1.4667 | 3 | 0 | 0 | 0 | 0 | 0 |
| soft_binding | 3hop | 15 | 0.2570 | 0.4667 | 0.5507 | 2.0000 | 2 | 0 | 0 | 2 | 0 | 0 |
| soft_binding | 4hop | 15 | 0.1000 | 0.3333 | 0.3000 | 2.4667 | 3 | 0 | 0 | 4 | 0 | 0 |
| soft_binding | all | 45 | 0.2812 | 0.5111 | 0.5502 | 1.9778 | 8 | 0 | 0 | 6 | 0 | 0 |
| slot_ledger_v1 | 2hop | 15 | 0.5422 | 0.8000 | 0.6778 | 1.4000 | 2 | 11 | 1 | 2 | 0 | 0 |
| slot_ledger_v1 | 3hop | 15 | 0.3237 | 0.6000 | 0.5394 | 2.0667 | 3 | 11 | 0 | 4 | 0 | 0 |
| slot_ledger_v1 | 4hop | 15 | 0.1000 | 0.4000 | 0.2500 | 2.1333 | 4 | 6 | 0 | 6 | 0 | 0 |
| slot_ledger_v1 | all | 45 | 0.3220 | 0.6000 | 0.5366 | 1.8667 | 9 | 28 | 1 | 12 | 0 | 0 |
| slot_ledger_strict_binding | 2hop | 15 | 0.4756 | 0.7333 | 0.6485 | 1.4000 | 2 | 10 | 3 | 1 | 0 | 0 |
| slot_ledger_strict_binding | 3hop | 15 | 0.1903 | 0.4000 | 0.4758 | 1.8667 | 2 | 3 | 4 | 3 | 0 | 0 |
| slot_ledger_strict_binding | 4hop | 15 | 0.0667 | 0.2000 | 0.3333 | 2.0000 | 2 | 0 | 7 | 3 | 0 | 0 |
| slot_ledger_strict_binding | all | 45 | 0.2442 | 0.4444 | 0.5494 | 1.7556 | 6 | 13 | 14 | 7 | 0 | 0 |

## Closure Success Quality
| run | successes | exact | partial | zero | mean_f1 |
|---|---:|---:|---:|---:|---:|
| baseline | 7 | 2 | 1 | 4 | 0.3571 |
| soft_binding | 6 | 0 | 1 | 5 | 0.0833 |
| slot_ledger_v1 | 12 | 2 | 3 | 7 | 0.2599 |
| slot_ledger_strict_binding | 7 | 1 | 2 | 4 | 0.2313 |

## Strict Binding Zero-F1 Answered Cases
| id | hop | answer | gold | slot_answer | closure_success | question |
|---|---|---|---|---:|---:|---|
| 2hop__131951_643670 | 2hop | Nieuwe Maas River | Het Scheur | 1 | 0 | What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum? |
| 2hop__247353_55227 | 2hop | Salma Hayek | Maria Bello | 1 | 0 | Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups? |
| 3hop1__104996_160713_77246 | 3hop | Islam | the country of India | 0 | 1 | What is the meaning of the word that is also a majority religion in the area that became India when the country that release Ankahi was created in Arabic dictionary? |
| 3hop1__159803_89752_75165 | 3hop | 39.3 million | 1,335,907 | 0 | 1 | What's the population of the largest state in the region of the U.S. where trading practices were once threatened by the Navigation Acts? |
| 4hop1__152146_5274_458768_33632 | 4hop | 18 November | May 4 | 0 | 1 | What day is the Feast held in the city where the headquarters of the only group larger than Långa nätter's record label is located? |
| 4hop1__28352_53706_795904_580996 | 4hop | Canada | Rio Linda | 0 | 1 | What shares a border with the city where the person who went to the state where the planes were originally going on 9/11 during the gold rush works? |

## Largest Regressions vs Slot Ledger v1
| id | hop | delta | v1 | strict | gold | slot_missing | closure_not_final | question |
|---|---|---:|---|---|---|---:|---:|---|
| 2hop__167577_31122 | 2hop | -1.000 | answer 18th r2 f1=1.000 | abstain  r2 f1=0.000 | 18th | 0 | 0 | What century did the author of A Treatise Concerning the Principles of Human Knowledge live in? |
| 3hop1__136129_87694_124169 | 3hop | -1.000 | answer 1952 r3 f1=1.000 | abstain  r2 f1=0.000 | 1952 | 1 | 0 | What year did the Governor of the city where the basilica named after the same saint as the one that Mantua Cathedral is dedicated to die? |
| 3hop1__140786_2053_5289 | 3hop | -1.000 | answer Oriole Records r2 f1=1.000 | abstain  r2 f1=0.000 | Oriole Records. | 1 | 0 | What UK label was bought by the major broadcaster that, along with ABC and the network of the show Just Men!?, is based in New York? |
| 4hop1__161605_32392_823060_610794 | 4hop | -0.500 | answer Charleston County r2 f1=0.500 | abstain  r2 f1=0.000 | Richland County | 0 | 0 | What county is the city that shares a border with the state capital of the state where Darlington County located in? |
| 2hop__10620_49084 | 2hop | 0.000 | answer Liam Garrigan r1 f1=0.800 | answer Liam Garrigan r1 f1=0.800 | Liam Thomas Garrigan | 0 | 0 | Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time? |
| 2hop__129721_40482 | 2hop | 0.000 | answer Edmund Bellinger r1 f1=1.000 | answer Edmund Bellinger r1 f1=1.000 | Edmund Bellinger | 0 | 0 | From whom did the Huguenots in the state encompassing Zubly Cemetery purchase land from? |
| 2hop__131951_643670 | 2hop | 0.000 | answer Nieuwe Maas River r1 f1=0.000 | answer Nieuwe Maas River r1 f1=0.000 | Het Scheur | 0 | 0 | What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum? |
| 2hop__132854_417697 | 2hop | 0.000 | abstain  r2 f1=0.000 | abstain  r2 f1=0.000 | Nissan Altima | 1 | 0 | Mohammed Atta has what kind of model of the company that makes Datsun Type 12? |
| 2hop__136179_13529 | 2hop | 0.000 | answer June 1982 r1 f1=1.000 | answer June 1982 r1 f1=1.000 | June 1982 | 0 | 0 | When was the player that Iglesia Maradoniana is named after signed by Barcelona? |
| 2hop__142699_67465 | 2hop | 0.000 | answer March 11, 2011. r1 f1=1.000 | answer March 11, 2011. r1 f1=1.000 | March 11, 2011 | 0 | 0 | When did the rapper on On and On and Beyond release Best day Ever? |
| 2hop__151750_141308 | 2hop | 0.000 | answer Apple Records r1 f1=0.500 | answer Apple Records r1 f1=0.500 | Apple Corps | 0 | 0 | What company is the record label of Magic Christian Music part of? |
| 2hop__153573_44085 | 2hop | 0.000 | answer Metal Mickey r2 f1=0.333 | answer Metal Mickey r2 f1=0.333 | The Mickey Mouse Club | 0 | 0 | What was the show named after the character featured in the video game Mickey's Safari in Letterland? |

## Interpretation
- Strict final-target binding and slot-ledger closure safety reduced unsafe coverage, but also removed the v1 numeric gain. Overall answer_f1 falls to 0.2442, below both guarded baseline and soft binding.
- Safety improved only partially relative to v1: zero-F1 answered cases drop from 9 to 6, and closure successes drop from 12 to 7, but 4 closure successes are still zero-F1. The run also misses the F1 acceptance gate.
- The direction remains informative: pre-generation slot evidence helps when permissive, but relying on verifier final_target_match as a hard binding signal is too conservative, similar to the earlier strict post-hoc slot gate.
- Do not promote this strict-binding variant to full300. The next narrow fix should make final-target binding evidence-based rather than boolean self-report based, or disable closure while using a softer slot binding policy.
