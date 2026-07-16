# Targeted Runtime Smoke Retrieval Details v1.3.5

Run: `runs/layer1_siliconflow_qwen3_14b_repair_closure_targeted_runtime_smoke_v1_3_5_20260707`

## 2hop__10620_49084

Question: Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time?
Gold answer: `Liam Thomas Garrigan`
Final: `answer` / `Liam Garrigan`
Gold supporting passages: `2hop__10620_49084::p18`, `2hop__10620_49084::p2`
Cumulative gold hits: `2hop__10620_49084::p18`

### Round 1 - action `answer`

Query: Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time?
Evidence gain: 0.5; budget_remaining: 2
Gold hits this round: `2hop__10620_49084::p18`
Verifier: suff=sufficient, final_target_match=True, answer_slot=final requested target, suggested_query=''
Slot binding: bound='Liam Garrigan', role=final_answer, relation=fills_final_slot, typed_accept=True, typed_reason=structured_final_slot_acceptance, category=None, decision=answer

| rank | passage_id | title | gold | local | verifier_used | slot_used | snippet |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `2hop__10620_49084::p18` | Liam Garrigan | True | True | True | True | Liam Thomas Garrigan (born 17 October 1981) is an English theatre and television actor. As a youth he attended classes at Kingston upon Hull's Northern Stage Company and was a student at Wyke College, Kingston upon Hull. His first television role was as ... |
| 2 | `2hop__28203_55840::p5` | The King's Speech | False | False | False | False | The King's Speech is a 2010 British historical drama film directed by Tom Hooper and written by David Seidler. Colin Firth plays the future King George VI who, to cope with a stammer, sees Lionel Logue, an Australian speech and language therapist played by ... |
| 3 | `2hop__10620_49084::p6` | Beverley Elliott | False | True | False | False | Beverley Elliott (born 31 December) is a Canadian actress and singer - songwriter. She is best known for playing the role of Granny in Once Upon a Time, Maggie Krell in Harper's Island, Brick Bannerman in Kingdom Hospital and Sally Duffield in Bordertown. |


## 2hop__167577_31122

Question: What century did the author of A Treatise Concerning the Principles of Human Knowledge live in?
Gold answer: `18th`
Final: `answer` / `18th century`
Gold supporting passages: `2hop__167577_31122::p10`, `2hop__167577_31122::p14`
Cumulative gold hits: `2hop__167577_31122::p10`

### Round 1 - action `answer`

Query: What century did the author of A Treatise Concerning the Principles of Human Knowledge live in?
Evidence gain: 0.5; budget_remaining: 2
Gold hits this round: `2hop__167577_31122::p10`
Verifier: suff=sufficient, final_target_match=True, answer_slot=final requested target, suggested_query=''
Slot binding: bound='18th century', role=final_answer, relation=fills_final_slot, typed_accept=True, typed_reason=structured_final_slot_acceptance, category=None, decision=answer

| rank | passage_id | title | gold | local | verifier_used | slot_used | snippet |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `2hop__167577_31122::p10` | A Treatise Concerning the Principles of Human Knowledge | True | True | True | True | A Treatise Concerning the Principles of Human Knowledge (commonly called Treatise when referring to Berkeley's works) is a 1710 work, in English, by Irish Empiricist philosopher George Berkeley. This book largely seeks to refute the claims made by ... |
| 2 | `2hop__167577_31122::p9` | Humanism | False | True | False | False | Eliot and her circle, who included her companion George Henry Lewes (the biographer of Goethe) and the abolitionist and social theorist Harriet Martineau, were much influenced by the positivism of Auguste Comte, whom Martineau had translated. Comte had ... |
| 3 | `2hop__167577_31122::p17` | Humanism | False | True | False | False | Religious humanism is an integration of humanist ethical philosophy with religious rituals and beliefs that centre on human needs, interests, and abilities. Though practitioners of religious humanism did not officially organise under the name of "humanism" ... |


## 2hop__194469_83289

Question: Who is the guy in the One Last Time video by the participant in The Listening Sessions?
Gold answer: `Matt Bennett`
Final: `abstain` / ``
Gold supporting passages: `2hop__194469_83289::p7`, `2hop__194469_83289::p19`
Cumulative gold hits: `2hop__194469_83289::p19`

### Round 1 - action `ordered_hop_repair`

Query: Who is the guy in the One Last Time video by the participant in The Listening Sessions?
Evidence gain: 0.5; budget_remaining: 2
Gold hits this round: `2hop__194469_83289::p19`
Verifier: suff=insufficient, final_target_match=False, answer_slot=intermediate entity, suggested_query='Who is the participant in The Listening Sessions?'
Slot binding: bound='', role=bridge_entity, relation=supports_bridge, typed_accept=False, typed_reason=binding_verifier_rejected, category=empty_binding, decision=ordered_hop_repair
Repair: action=ordered_hop_repair, next_query='Matt Bennett participant', state=repair_unresolved_terminal, closed=repair_unresolved_terminal, quality=entity-only

| rank | passage_id | title | gold | local | verifier_used | slot_used | snippet |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `2hop__194469_83289::p19` | One Last Time (Ariana Grande song) | True | True | True | True | The music video was filmed in early January 2015 and it also stars Matt Bennett, who was also Grande's co-star from the Nickelodeon sitcom Victorious. Max Landis also confirmed that one of the voices of the news reporters in the beginning of the video was ... |
| 2 | `2hop__194469_83289::p11` | Standing on a Beach | False | True | False | False | The man featured on the album cover was not a member of the Cure; he was chosen because his appearance fit the desired aesthetic of the album. His name is John Button, and was at the time a retired fisherman. He also appeared in the music video for ... |
| 3 | `2hop__73719_510545::p16` | Zach McGowan | False | False | False | False | Zachary Brendan McGowan (born May 5, 1980) is an American film and television actor and voice - over artist. He is known for his roles in television series Shameless as Jody, Agents of S.H.I.E.L.D. as Anton Ivanov / The Superior, Black Sails as Charles ... |

### Round 2 - action `ordered_hop_repair`

Query: Matt Bennett participant
Evidence gain: 0.0; budget_remaining: 1
Gold hits this round: `2hop__194469_83289::p19`
Verifier: suff=insufficient, final_target_match=False, answer_slot=intermediate entity, suggested_query='Who is the participant in The Listening Sessions?'
Slot binding: bound='', role=bridge_entity, relation=supports_bridge, typed_accept=False, typed_reason=binding_verifier_rejected, category=empty_binding, decision=ordered_hop_repair
Repair: action=ordered_hop_repair, next_query='Matt Bennett is the guy in the One Last Time video', state=repair_unresolved_terminal, closed=repair_unresolved_terminal, quality=entity-only

| rank | passage_id | title | gold | local | verifier_used | slot_used | snippet |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `4hop2__161602_426860_88460_21034::p12` | 2018 ACC Men's Basketball Tournament | False | False | False | False | The 2018 ACC Men's Basketball Tournament was the postseason men's basketball tournament for the Atlantic Coast Conference held at Barclays Center in Brooklyn, New York from March 6 -- 10, 2018. It was the 65th annual edition of the tournament, and the ... |
| 2 | `2hop__286093_361551::p13` | Andy Finch | False | False | False | False | Andrew Joseph "Andy" Finch (born March 20, 1981) is an American snowboarder. His accomplishments include winning the overall U.S. Grand Prix Halfpipe Title in 2003 and 2004, taking first place in the Arctic Challenge in Norway in April 2004, winning the ... |
| 3 | `2hop__28203_55840::p2` | Taylor King | False | False | False | False | Taylor King (born May 30, 1988) is an American retired professional basketball player. King played for the Villanova University Wildcats, where he played the forward position. King attended Mater Dei High School of Santa Ana, where he enjoyed a successful ... |
| 4 | `2hop__194469_83289::p19` | One Last Time (Ariana Grande song) | True | True | True | True | The music video was filmed in early January 2015 and it also stars Matt Bennett, who was also Grande's co-star from the Nickelodeon sitcom Victorious. Max Landis also confirmed that one of the voices of the news reporters in the beginning of the video was ... |
| 5 | `2hop__194469_83289::p11` | Standing on a Beach | False | True | False | False | The man featured on the album cover was not a member of the Cure; he was chosen because his appearance fit the desired aesthetic of the album. His name is John Button, and was at the time a retired fisherman. He also appeared in the music video for ... |

### Round 3 - action `abstain`

Query: Matt Bennett is the guy in the One Last Time video
Evidence gain: 0.0; budget_remaining: 0
Gold hits this round: `2hop__194469_83289::p19`
Verifier: suff=insufficient, final_target_match=False, answer_slot=intermediate entity, suggested_query='Who is the participant in The Listening Sessions?'
Slot binding: bound='', role=unknown, relation=ambiguous, typed_accept=False, typed_reason=binding_verifier_rejected, category=empty_binding, decision=abstain
Repair: action=ordered_hop_repair, next_query='Matt Bennett is the guy in the One Last Time video', state=repair_failed, closed=repair_rejected, quality=entity-only

| rank | passage_id | title | gold | local | verifier_used | slot_used | snippet |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `2hop__194469_83289::p19` | One Last Time (Ariana Grande song) | True | True | True | False | The music video was filmed in early January 2015 and it also stars Matt Bennett, who was also Grande's co-star from the Nickelodeon sitcom Victorious. Max Landis also confirmed that one of the voices of the news reporters in the beginning of the video was ... |
| 2 | `2hop__10620_49084::p18` | Liam Garrigan | False | False | False | False | Liam Thomas Garrigan (born 17 October 1981) is an English theatre and television actor. As a youth he attended classes at Kingston upon Hull's Northern Stage Company and was a student at Wyke College, Kingston upon Hull. His first television role was as ... |
| 3 | `2hop__194469_83289::p10` | ...Baby One More Time (song) | False | True | False | False | ``... Baby One More Time ''was released on October 23, 1998 through Jive Records. It reached number one in every country it charted in, including the United Kingdom, where it earned double - platinum certification from the British Phonographic Industry ... |
| 4 | `2hop__194469_83289::p11` | Standing on a Beach | False | True | False | False | The man featured on the album cover was not a member of the Cure; he was chosen because his appearance fit the desired aesthetic of the album. His name is John Button, and was at the time a retired fisherman. He also appeared in the music video for ... |
| 5 | `2hop__73719_510545::p16` | Zach McGowan | False | False | False | False | Zachary Brendan McGowan (born May 5, 1980) is an American film and television actor and voice - over artist. He is known for his roles in television series Shameless as Jody, Agents of S.H.I.E.L.D. as Anton Ivanov / The Superior, Black Sails as Charles ... |


## 3hop1__145194_160545_62931

Question: The Beach was filmed in what location of the country that contains the birth city of Siddhi Savetsila?
Gold answer: `island Koh Phi Phi`
Final: `abstain` / ``
Gold supporting passages: `3hop1__145194_160545_62931::p9`, `3hop1__145194_160545_62931::p19`, `3hop1__145194_160545_62931::p5`
Cumulative gold hits: `3hop1__145194_160545_62931::p19`, `3hop1__145194_160545_62931::p9`

### Round 1 - action `abstain`

Query: The Beach was filmed in what location of the country that contains the birth city of Siddhi Savetsila?
Evidence gain: 0.6666666666666666; budget_remaining: 2
Gold hits this round: `3hop1__145194_160545_62931::p19`, `3hop1__145194_160545_62931::p9`
Verifier: suff=sufficient, final_target_match=True, answer_slot=final requested target, suggested_query=''
Slot binding: bound='', role=unknown, relation=ambiguous, typed_accept=False, typed_reason=binding_verifier_rejected, category=empty_binding, decision=abstain

| rank | passage_id | title | gold | local | verifier_used | slot_used | snippet |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `3hop1__465684_160545_62931::p14` | The Beach (film) | False | False | True | False | The Beach is a 2000 English - language drama film directed by Danny Boyle and based on the 1996 novel of the same name by Alex Garland, which was adapted for the film by John Hodge. The film stars Leonardo DiCaprio, Tilda Swinton, Virginie Ledoyen, ... |
| 2 | `3hop1__145194_160545_62931::p19` | The Beach (film) | True | True | True | False | The Beach is a 2000 English - language drama film directed by Danny Boyle and based on the 1996 novel of the same name by Alex Garland, which was adapted for the film by John Hodge. The film stars Leonardo DiCaprio, Tilda Swinton, Virginie Ledoyen, ... |
| 3 | `3hop1__145194_160545_62931::p9` | Siddhi Savetsila | True | True | True | False | Siddhi Savetsila was born in Bangkok. He comes from an aristocratic background. His father was a high-ranking official in the royal government. His paternal grandfather was Henry Alabaster who was the British consul in Siam during the reign of King Rama IV ... |
| 4 | `3hop1__145194_160545_62931::p18` | Snow White and the Huntsman | False | True | False | False | Principal photography took place in the United Kingdom. The beach scenes were predominantly filmed in Pembrokeshire, on the Marloes Sands beach near the village of Marloes between September 26 and 29, 2011. Though the beach was not closed to the public ... |
| 5 | `4hop3__668721_132409_371500_35031::p19` | Kathmandu | False | False | False | False | Kathmandu(/ˌkɑːtmɑːnˈduː/; Nepali pronunciation: [kɑʈʰmɑɳɖu]) is the capital and largest municipality of Nepal. It also hosts the headquarters of the South Asian Association for Regional Cooperation (SAARC). It is the only city of Nepal with the ... |


## 3hop1__144439_443779_52195

Question: who is the president of newly declared independent country of the country of the birthplace of Mulham Arufin–Timor Leste Commission of Truth and Friendship?
Gold answer: `Francisco Guterres`
Final: `abstain` / ``
Gold supporting passages: `3hop1__144439_443779_52195::p3`, `3hop1__144439_443779_52195::p2`, `3hop1__144439_443779_52195::p7`
Cumulative gold hits: `3hop1__144439_443779_52195::p7`, `3hop1__144439_443779_52195::p2`

### Round 1 - action `refine_query`

Query: who is the president of newly declared independent country of the country of the birthplace of Mulham Arufin–Timor Leste Commission of Truth and Friendship?
Evidence gain: 0.3333333333333333; budget_remaining: 2
Gold hits this round: `3hop1__144439_443779_52195::p7`
Verifier: suff=insufficient, final_target_match=False, answer_slot=unknown, suggested_query='What is the birthplace of Mulham Arufin, and who was the president of the newly declared independent country at the time?'
Slot binding: bound='', role=unknown, relation=ambiguous, typed_accept=False, typed_reason=binding_verifier_rejected, category=empty_binding, decision=abstain

| rank | passage_id | title | gold | local | verifier_used | slot_used | snippet |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `3hop1__144439_443779_52195::p7` | Indonesia–Timor Leste Commission of Truth and Friendship | True | True | True | False | The Indonesia–Timor Leste Commission on Truth and Friendship was a truth commission established jointly by the governments of Indonesia and East Timor in August 2005. The commission was officially created to investigate acts of violence that occurred ... |
| 2 | `3hop1__105767_443779_52195::p3` | Indonesia–Timor Leste Commission of Truth and Friendship | False | False | True | False | The Indonesia–Timor Leste Commission on Truth and Friendship was a truth commission established jointly by the governments of Indonesia and East Timor in August 2005. The commission was officially created to investigate acts of violence that occurred ... |
| 3 | `3hop1__103881_443779_52195::p7` | Indonesia–Timor Leste Commission of Truth and Friendship | False | False | True | False | The Indonesia–Timor Leste Commission on Truth and Friendship was a truth commission established jointly by the governments of Indonesia and East Timor in August 2005. The commission was officially created to investigate acts of violence that occurred ... |
| 4 | `2hop__91211_90973::p9` | Friends with Benefits (film) | False | False | False | False | Friends with Benefits is a 2011 American romantic comedy film directed by Will Gluck, and starring Justin Timberlake and Mila Kunis in the lead roles. The film features Patricia Clarkson, Jenna Elfman, Bryan Greenberg, Nolan Gould, Richard Jenkins, and ... |
| 5 | `2hop__471509_136043::p0` | Are You the One? | False | False | False | False | Couple Week Result Ethan & Keyana Not A Match Anthony & Geles Not A Match Malcolm & Nurys Not A Match Dimitri & Nicole Not A Match Clinton & Uche 5 Not A Match Keith & Alexis 6 Not A Match Keith & Alivia 7 Not A Match Michael & Audrey 8 Not A Match Tyler & ... |

### Round 2 - action `refine_query`

Query: What is the birthplace of Mulham Arufin, and who was the president of the newly declared independent country at the time? (person)
Evidence gain: 0.3333333333333333; budget_remaining: 1
Gold hits this round: `3hop1__144439_443779_52195::p2`, `3hop1__144439_443779_52195::p7`
Verifier: suff=insufficient, final_target_match=False, answer_slot=unknown, suggested_query='What is the birthplace of Mulham Arufin, and who is the current president of that country?'
Slot binding: bound='', role=unknown, relation=ambiguous, typed_accept=False, typed_reason=binding_verifier_rejected, category=empty_binding, decision=abstain

| rank | passage_id | title | gold | local | verifier_used | slot_used | snippet |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `3hop1__144439_443779_52195::p2` | Mulham Arufin | True | True | True | False | Mulham Arufin (born November 17, 1990) is an Indonesian footballer who currently plays for Gresik United in the Indonesia Super League. |
| 2 | `2hop__61924_712629::p10` | Elizabeth II | False | False | False | False | Elizabeth II (Elizabeth Alexandra Mary; born 21 April 1926) has been Queen of the United Kingdom, Canada, Australia, and New Zealand since 6 February 1952. Additionally, she is Head of the Commonwealth and Queen of 12 countries that have become independent ... |
| 3 | `3hop1__105767_443779_52195::p6` | Namibia | False | False | False | False | The Namibian Constitution adopted in February 1990 incorporated protection for human rights, compensation for state expropriations of private property, an independent judiciary and an executive presidency (the constituent assembly became the national ... |
| 4 | `2hop__6827_86319::p19` | Khwaja Abdul Ghani | False | False | False | False | Khwaja Abdul Ghani was the second son of Khwaja Alimullah, who consolidated the Khwaja family estate to become the first Nawab of the family. He inherited the estate from his father, which included the French "kuthi" at Kumartuli bought by Alimullah in ... |
| 5 | `3hop1__144439_443779_52195::p7` | Indonesia–Timor Leste Commission of Truth and Friendship | True | True | True | False | The Indonesia–Timor Leste Commission on Truth and Friendship was a truth commission established jointly by the governments of Indonesia and East Timor in August 2005. The commission was officially created to investigate acts of violence that occurred ... |

### Round 3 - action `abstain`

Query: What person answers Friendship?
Evidence gain: 0.0; budget_remaining: 0
Gold hits this round: `3hop1__144439_443779_52195::p7`
Verifier: suff=insufficient, final_target_match=False, answer_slot=unknown, suggested_query='Who is the president of Timor-Leste?'
Slot binding: bound='', role=unknown, relation=ambiguous, typed_accept=False, typed_reason=binding_verifier_rejected, category=empty_binding, decision=abstain

| rank | passage_id | title | gold | local | verifier_used | slot_used | snippet |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `2hop__23459_35124::p11` | Answer to History | False | False | False | False | Answer to History (French: Réponse à l'histoire; Persian: پاسخ به تاریخ) is a memoir written by the last Shah of Iran, Mohammad Reza Pahlavi, shortly after his overthrow in 1979 by Islamic revolution. The book was originally written in French and was ... |
| 2 | `2hop__708145_30351::p17` | Friedrich Hayek | False | False | False | False | In 1984, he was appointed as a member of the Order of the Companions of Honour (CH) by Queen Elizabeth II of the United Kingdom on the advice of the British Prime Minister Margaret Thatcher for his "services to the study of economics". Hayek had hoped to ... |
| 3 | `4hop1__31050_725495_49925_267352::p15` | Peter Agricola | False | False | False | False | Peter Agricola (June 29, 1525 – July 5 or 7, 1585) was a German Renaissance humanist, educator, classical scholar and theologian, diplomat and statesman, disciple of Martin Luther, friend and collaborator of Philipp Melanchthon. |
| 4 | `3hop1__144439_443779_52195::p7` | Indonesia–Timor Leste Commission of Truth and Friendship | True | True | True | False | The Indonesia–Timor Leste Commission on Truth and Friendship was a truth commission established jointly by the governments of Indonesia and East Timor in August 2005. The commission was officially created to investigate acts of violence that occurred ... |
| 5 | `3hop1__105767_443779_52195::p3` | Indonesia–Timor Leste Commission of Truth and Friendship | False | False | True | False | The Indonesia–Timor Leste Commission on Truth and Friendship was a truth commission established jointly by the governments of Indonesia and East Timor in August 2005. The commission was officially created to investigate acts of violence that occurred ... |


## 2hop__131951_643670

Question: What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum?
Gold answer: `Het Scheur`
Final: `answer` / `Nieuwe Waterweg`
Gold supporting passages: `2hop__131951_643670::p10`, `2hop__131951_643670::p6`
Cumulative gold hits: `2hop__131951_643670::p6`, `2hop__131951_643670::p10`

### Round 1 - action `ordered_hop_repair`

Query: What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum?
Evidence gain: 1.0; budget_remaining: 2
Gold hits this round: `2hop__131951_643670::p6`, `2hop__131951_643670::p10`
Verifier: suff=sufficient, final_target_match=True, answer_slot=final requested target, suggested_query=''
Slot binding: bound='Nieuwe Waterweg', role=distractor, relation=local_support_only, typed_accept=False, typed_reason=mouth_watercourse_downstream_continuation, category=wrong_target, decision=ordered_hop_repair
Repair: action=ordered_hop_repair, next_query='Nieuwe Maas River mouth of the watercourse', state=repair_superseded_by_final_answer, closed=repair_superseded_by_final_answer, quality=entity-only

| rank | passage_id | title | gold | local | verifier_used | slot_used | snippet |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `2hop__131951_643670::p6` | Rotterdam Centrum | True | True | True | True | Rotterdam Centrum is bounded by the emplacement of the Rotterdam Centraal railway station and the Goudsesingel in the North, the Tunneltraverse of the Henegouwerlaan and 's-Gravendijkwal in the West, the Nieuwe Maas River in the South and the Oostplein in ... |
| 2 | `2hop__131951_643670::p10` | Het Scheur | True | True | True | True | Het Scheur (; Dutch for "The Rip") is a branch of the Rhine-Meuse delta in South Holland, Netherlands, that flows west from the confluence of the Oude Maas and Nieuwe Maas branches past the towns of Rozenburg and Maassluis. It continues as the Nieuwe ... |
| 3 | `4hop1__726391_153080_33952_34109::p1` | Utrecht | False | False | False | False | A large indoor shopping centre Hoog Catharijne (nl) is located between Utrecht Centraal railway station and the city centre. The corridors are treated as public places like streets, and the route between the station and the city centre is open all night. ... |

### Round 2 - action `answer`

Query: Nieuwe Maas River mouth of the watercourse
Evidence gain: 0.0; budget_remaining: 1
Gold hits this round: `2hop__131951_643670::p10`, `2hop__131951_643670::p6`
Verifier: suff=sufficient, final_target_match=True, answer_slot=final requested target, suggested_query=''
Slot binding: bound='', role=unknown, relation=ambiguous, typed_accept=False, typed_reason=binding_verifier_rejected, category=empty_binding, decision=abstain
Repair: action=ordered_hop_repair, next_query='Nieuwe Maas River mouth of the watercourse', state=repair_accepted, closed=accepted_final, quality=entity-only

| rank | passage_id | title | gold | local | verifier_used | slot_used | snippet |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `2hop__131951_643670::p10` | Het Scheur | True | True | True | False | Het Scheur (; Dutch for "The Rip") is a branch of the Rhine-Meuse delta in South Holland, Netherlands, that flows west from the confluence of the Oude Maas and Nieuwe Maas branches past the towns of Rozenburg and Maassluis. It continues as the Nieuwe ... |
| 2 | `4hop1__860115_798482_131926_90707::p17` | Water supply and sanitation in South Africa | False | False | False | False | Total annual water withdrawal was estimated at 12.5 km3 in 2000, of which about 17% was for municipal water use. In the northern parts of the country, both surface water and groundwater resources are nearly fully developed and utilised. In the well - ... |
| 3 | `4hop1__860115_798482_131926_13165::p9` | Water supply and sanitation in South Africa | False | False | False | False | Total annual water withdrawal was estimated at 12.5 km3 in 2000, of which about 17% was for municipal water use. In the northern parts of the country, both surface water and groundwater resources are nearly fully developed and utilised. In the well - ... |
| 4 | `2hop__131951_643670::p6` | Rotterdam Centrum | True | True | True | False | Rotterdam Centrum is bounded by the emplacement of the Rotterdam Centraal railway station and the Goudsesingel in the North, the Tunneltraverse of the Henegouwerlaan and 's-Gravendijkwal in the West, the Nieuwe Maas River in the South and the Oostplein in ... |
| 5 | `4hop1__726391_153080_33952_34109::p1` | Utrecht | False | False | False | False | A large indoor shopping centre Hoog Catharijne (nl) is located between Utrecht Centraal railway station and the city centre. The corridors are treated as public places like streets, and the route between the station and the city centre is open all night. ... |

