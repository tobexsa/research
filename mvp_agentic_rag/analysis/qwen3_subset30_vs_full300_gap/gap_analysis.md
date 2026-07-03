# Subset30 vs Full300 Answer-F1 Gap Analysis

## Summary
- subset30_run: n=30, answer_f1=0.5833, coverage=0.8000, avg_rounds=1.6333, actions={'abstain': 6, 'answer': 24}, hops={'2hop': 30}, non_json=0
- full300_same_first30_ids: n=30, answer_f1=0.5833, coverage=0.8000, avg_rounds=1.6333, actions={'abstain': 6, 'answer': 24}, hops={'2hop': 30}, non_json=0
- full300_remaining270: n=270, answer_f1=0.2063, coverage=0.4407, avg_rounds=2.1444, actions={'abstain': 151, 'answer': 119}, hops={'2hop': 70, '3hop': 100, '4hop': 100}, non_json=4
- full300_all300: n=300, answer_f1=0.2440, coverage=0.4767, avg_rounds=2.0933, actions={'abstain': 157, 'answer': 143}, hops={'2hop': 100, '3hop': 100, '4hop': 100}, non_json=4

## Hop Slices
| group | hop | n | answer_f1 | coverage | answer_count | abstain_count |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| subset30_run | 2hop | 30 | 0.5833 | 0.8000 | 24 | 6 |
| full300_same_first30_ids | 2hop | 30 | 0.5833 | 0.8000 | 24 | 6 |
| full300_remaining270 | 2hop | 70 | 0.3846 | 0.7143 | 50 | 20 |
| full300_remaining270 | 3hop | 100 | 0.1871 | 0.3900 | 39 | 61 |
| full300_remaining270 | 4hop | 100 | 0.1006 | 0.3000 | 30 | 70 |
| full300_all300 | 2hop | 100 | 0.4442 | 0.7400 | 74 | 26 |
| full300_all300 | 3hop | 100 | 0.1871 | 0.3900 | 39 | 61 |
| full300_all300 | 4hop | 100 | 0.1006 | 0.3000 | 30 | 70 |

## Closure Success Quality
| group | successes | exact_f1_1 | partial_positive | f1_zero | mean_f1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| full_all300 | 33 | 5 | 11 | 17 | 0.3057 |
| full_first30 | 1 | 1 | 0 | 0 | 1.0000 |
| full_rest270 | 32 | 4 | 11 | 17 | 0.2840 |
| subset30 | 1 | 1 | 0 | 0 | 1.0000 |

## Full300 Remaining270 Bad Closure Successes
| id | hop | f1 | candidate | gold | question |
| --- | --- | ---: | --- | --- | --- |
| 2hop__46550_85990 | 2hop | 0.000 | Nancy Pelosi | anti-slavery activists, modernizers, ex Whigs and ex Free Soilers | Who were the leaders of the opposition of the party that controlled the house of representatives in 2002? |
| 2hop__753715_51329 | 2hop | 0.000 | Broadway's Like That | The African Queen | with what movie did Mary Philips' husband win his only oscar? |
| 2hop__82669_768138 | 2hop | 0.000 | Christopher Masterson | Matthew Lawrence | Who is the brother of the Melissa and Joey Theme Song singer? |
| 2hop__91211_90973 | 2hop | 0.000 | Sanaa Lathan | Lacey Chabert | Who did the original voice of the character played by mila kunis in the cleveland show? |
| 3hop1__159803_89752_75165 | 3hop | 0.000 | 39.3 million | 1,335,907 | What's the population of the largest state in the region of the U.S. where trading practices were once threatened by the Navigation Acts? |
| 3hop1__390673_228453_10972 | 3hop | 0.000 | 1973 | 1970s | When did the headquarters city of Kentucky Tavern's manufacturer elect its first black mayor? |
| 3hop1__465684_160545_62931 | 3hop | 0.000 | Venezuela | island Koh Phi Phi | Where in the country where Bodindecha was born was The Beach filmed? |
| 3hop1__635099_131926_89261 | 3hop | 0.000 | Matagorda Bay | the Mississippi River Delta | Where does the body of water by the city where Write This Down was formed empty into the Gulf of Mexico? |
| 3hop2__93066_88342_90766 | 3hop | 0.000 | 2017 | 1981 | When was the last time the winner of the American League East in 2017 met the Dodgers in the event after which the MLB MVP award is given out? |
| 4hop1__151650_5274_458768_33632 | 4hop | 0.000 | 7 October | May 4 | What day is the Feast in the city where the headquarters of the only group larger than Desde El Principio's record label held on? |
| 4hop1__152146_5274_458768_33632 | 4hop | 0.000 | 18 November | May 4 | What day is the Feast held in the city where the headquarters of the only group larger than Långa nätter's record label is located? |
| 4hop1__166471_49925_13759_736921 | 4hop | 0.000 | New York | Saxony-Anhalt | In what state is the district where the one who wanted to reform and address the institution behind the religion of Egidio Vagnozzi preached a sermon? |
| 4hop1__391525_49925_13759_736921 | 4hop | 0.000 | Ghaziabad, Uttar Pradesh | Saxony-Anhalt | Where is the district that the person who wanted to reform and address John Kodwo Amissah's religion preached a sermon on Marian devotion before his death located? |
| 4hop1__58323_375563_161848_61344 | 4hop | 0.000 | Africa | submerged continent of Zealandia | What continent is the country located near the country of citizenship of The Book Thief's author part of? |
| 4hop1__726391_153080_33952_34109 | 4hop | 0.000 | Oklahoma City | KUAT-TV 6 | What is the PBS station in the second largest city in the state where Oh Yeah's performer is from? |
| 4hop1__749065_698949_157828_162309 | 4hop | 0.000 | 1992 | 2016 | When did the country whose co-official language was used in the show named for the place Slavko Surdonja died first attend the Olympics games as an independent team? |
| 4hop1__814776_378185_282674_759393 | 4hop | 0.000 | Charlotte | Green Bay | What city is the capital of the county, that shares a border with the other county, that contains the city where Western Islands is headquartered? |
| 3hop1__593597_40769_64047 | 3hop | 0.286 | 2012 | Sales began worldwide in April 2012 | When did the luxury division of the manufacturer of Scion Fuse change the body style of the RX 350? |
| 4hop2__161602_426860_88460_21057 | 4hop | 0.286 | Teak | 75% of the world's teak | During British rule, what wood product was produced primarily in the country between the country that hosted the tournament and the country where That Dam is from? |
| 4hop1__88342_49853_128008_86588 | 4hop | 0.333 | 575 feet | 582 feet (177 m) | What's the longest homer in the history of the league where the team with the most titles from the event after which they give out the MLB MVP award plays? |
| 4hop1__58323_375563_161848_83118 | 4hop | 0.444 | First Sunday of November | the first Sunday in April | When does daylight savings end in the country near the country where the author of The Book Thief is from? |
| 2hop__435184_84856 | 2hop | 0.500 | 2017 | January 20, 2017 | When does the new season of the show starring the cast member of Pizza Man start? |
| 4hop1__161605_32392_823060_610794 | 4hop | 0.500 | Charleston County | Richland County | What county is the city that shares a border with the state capital of the state where Darlington County located in? |
| 4hop1__463635_624859_355213_203322 | 4hop | 0.500 | Gaston County | Cabarrus County | What county shares a border with the county where the birthplace of Tonight You're Mine's performer is located? |
| 4hop1__767417_624859_355213_203322 | 4hop | 0.500 | Gaston County | Cabarrus County | What county shares a border with the county where the performer of Change of Heart was born? |
| 4hop1__777217_32392_823060_610794 | 4hop | 0.500 | Charleston County | Richland County | What county is the city that shares a border with the state capital of the state where Andrew Deveaux was born located in? |
| 4hop1__860115_798482_131926_13165 | 4hop | 0.571 | Treaty of Guadalupe Hidalgo | Treaty of Paris | What treaty ceded territory to the US extending west to the river by the city sharing a border with Elizabeth Berg's birthplace? |
| 3hop2__91678_90098_10557 | 3hop | 0.667 | Latin | Medieval Latin | What was the form of the language that the last name Sylvester comes from, used in the era of the first Holy Roman Emperor, later known as? |

## Full300 Remaining270 Outcome Buckets
- 2hop: n=70, answer_f1=0.3846, coverage=0.7143, f1_zero=38, f1_ge_0_5=30, closure_success=6, non_json=0
- 3hop: n=100, answer_f1=0.1871, coverage=0.3900, f1_zero=76, f1_ge_0_5=21, closure_success=8, non_json=0
- 4hop: n=100, answer_f1=0.1006, coverage=0.3000, f1_zero=84, f1_ge_0_5=11, closure_success=18, non_json=4