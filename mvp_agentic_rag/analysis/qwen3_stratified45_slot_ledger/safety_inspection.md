# Slot Ledger Safety Inspection

## Counts
- answered: 27
- zero-F1 answered: 9
- slot-answer answered: 21
- slot-answer zero-F1: 6
- closure successes: 12
- closure zero-F1: 7

## By Hop
| hop | n | answered | zero_answered | slot_answered | slot_zero_answered | closure_success |
|---|---:|---:|---:|---:|---:|---:|
| 2hop | 15 | 12 | 2 | 11 | 2 | 2 |
| 3hop | 15 | 9 | 3 | 7 | 2 | 4 |
| 4hop | 15 | 6 | 4 | 3 | 2 | 6 |

## Zero-F1 Answered Cases
| id | hop | final | gold | slot_answer | closure | final_evidence_ids | question |
|---|---|---|---|---:|---:|---|---|
| 2hop__131951_643670 | 2hop | Nieuwe Maas River | Het Scheur | 1 | 0 | 2hop__131951_643670::p6 | What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum? |
| 2hop__247353_55227 | 2hop | Salma Hayek | Maria Bello | 1 | 0 | 2hop__247353_55227::p17, 2hop__247353_55227::p6 | Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups? |
| 3hop1__104996_160713_77246 | 3hop | Islam | the country of India | 0 | 1 |  | What is the meaning of the word that is also a majority religion in the area that became India when the country that release Ankahi was created in Arabic dictionary? |
| 3hop1__105767_443779_52195 | 3hop | Susilo Bambang Yudhoyono | Francisco Guterres | 1 | 1 | 3hop1__144439_443779_52195::p7, 3hop1__105767_443779_52195::p3, 3hop1__103881_443779_52195::p7 | Who is the president of the newly declared independent country that is part of the commission of truth and friendship with the country that eats Kemplang? |
| 3hop1__159803_89752_75165 | 3hop | 39.3 million | 1,335,907 | 1 | 1 | 2hop__40270_11402::p13 | What's the population of the largest state in the region of the U.S. where trading practices were once threatened by the Navigation Acts? |
| 4hop1__145494_698949_157828_162309 | 4hop | 1920 | 2016 | 1 | 1 | 3hop1__105767_443779_52195::p1 | When did the country whose co-official language was used in the movie named after the place where Bela Linder died first attend the Olympics games as an independent team? |
| 4hop1__151650_5274_458768_33632 | 4hop | 18 November | May 4 | 1 | 1 | 4hop1__152146_5274_458768_33632::p18, 3hop1__64957_87694_124169::p15 | What day is the Feast in the city where the headquarters of the only group larger than Desde El Principio's record label held on? |
| 4hop1__152146_5274_458768_33632 | 4hop | 18 November | May 4 | 0 | 1 |  | What day is the Feast held in the city where the headquarters of the only group larger than Långa nätter's record label is located? |
| 4hop1__28352_53706_795904_580996 | 4hop | Canada | Rio Linda | 0 | 1 |  | What shares a border with the city where the person who went to the state where the planes were originally going on 9/11 during the gold rush works? |

## Closure Success Cases
| id | hop | f1 | candidate | gold | evidence_ids | question |
|---|---|---:|---|---|---|---|
| 2hop__153573_44085 | 2hop | 0.333 | Metal Mickey | The Mickey Mouse Club | 2hop__153573_44085::p14, 2hop__153573_44085::p9 | What was the show named after the character featured in the video game Mickey's Safari in Letterland? |
| 2hop__167577_31122 | 2hop | 1.000 | 18th | 18th | 2hop__167577_31122::p10 | What century did the author of A Treatise Concerning the Principles of Human Knowledge live in? |
| 3hop1__103751_24918_24991 | 3hop | 0.286 | Dissolution of the Soviet Union | Soviet flag | 3hop1__103751_24918_24991::p11 | What went down after the Soviet President visiting the country of origin of Ethella Chupryk while the protests were taking place departed from the Kremlin? |
| 3hop1__104996_160713_77246 | 3hop | 0.000 | Islam | the country of India | 3hop1__248929_160713_77246::p3, 3hop1__104996_160713_77246::p15, 3hop1__104996_160713_77246::p18 | What is the meaning of the word that is also a majority religion in the area that became India when the country that release Ankahi was created in Arabic dictionary? |
| 3hop1__105767_443779_52195 | 3hop | 0.000 | Susilo Bambang Yudhoyono | Francisco Guterres | 3hop1__144439_443779_52195::p7, 3hop1__105767_443779_52195::p3, 3hop1__103881_443779_52195::p7 | Who is the president of the newly declared independent country that is part of the commission of truth and friendship with the country that eats Kemplang? |
| 3hop1__159803_89752_75165 | 3hop | 0.000 | 39.3 million | 1,335,907 | 2hop__40270_11402::p13 | What's the population of the largest state in the region of the U.S. where trading practices were once threatened by the Navigation Acts? |
| 4hop1__145494_698949_157828_162309 | 4hop | 0.000 | 1920 | 2016 | 3hop1__105767_443779_52195::p1, 4hop1__145494_698949_157828_162309::p0 | When did the country whose co-official language was used in the movie named after the place where Bela Linder died first attend the Olympics games as an independent team? |
| 4hop1__151650_5274_458768_33632 | 4hop | 0.000 | 18 November | May 4 | 3hop1__64957_87694_124169::p15 | What day is the Feast in the city where the headquarters of the only group larger than Desde El Principio's record label held on? |
| 4hop1__152146_5274_458768_33632 | 4hop | 0.000 | 18 November | May 4 | 4hop3__668721_132409_371500_35031::p19, 3hop2__851134_613770_7713::p13, 3hop1__64957_87694_124169::p15 | What day is the Feast held in the city where the headquarters of the only group larger than Långa nätter's record label is located? |
| 4hop1__161605_32392_823060_610794 | 4hop | 0.500 | Charleston County | Richland County | 4hop3__387712_132409_223216_35031::p10, 3hop1__159803_89752_75165::p8 | What county is the city that shares a border with the state capital of the state where Darlington County located in? |
| 4hop1__161810_583746_457883_650651 | 4hop | 1.000 | NBC | NBC | 4hop1__161810_583746_457883_650651::p18, 4hop1__161810_583746_457883_650651::p10 | Country A has an embassy from the country that contains the bay where the city of General Santos is located. What network created country A's version of The Biggest Loser? |
| 4hop1__28352_53706_795904_580996 | 4hop | 0.000 | Canada | Rio Linda | 4hop1__463635_624859_355213_203322::p10, 4hop1__43565_624859_355213_203322::p8 | What shares a border with the city where the person who went to the state where the planes were originally going on 9/11 during the gold rush works? |

## Safety Takeaway
- Slot ledger improves the numeric gate, but zero-F1 answered cases remain common. Several are slot-answer cases, so deterministic claim-to-slot binding is still too permissive for named entities and locations.
- Closure remains unsafe as a promotion path: 12 closure successes include 7 zero-F1 candidates.
- Do not run full300 from this version before tightening slot binding / disabling or constraining closure under slot-ledger mode.
