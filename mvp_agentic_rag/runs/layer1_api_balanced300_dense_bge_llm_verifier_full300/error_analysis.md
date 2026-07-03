# Error Analysis: layer1_api_balanced300_dense_bge_llm_verifier_full300

## Run Shape
- total records: 600
- paired samples with both methods: 300

## ours
- count: 300
- mean_f1: 0.044625
- median_f1: 0.000000
- f1_zero: 234 (78.0%)
- f1_positive: 66 (22.0%)
- f1_ge_0_5: 4 (1.3%)
- final_action_counts: {'answer': 76, 'abstain': 224}
- retrieval_call_counts: {1: 70, 2: 15, 3: 215}
- trajectory_round_counts: {1: 70, 2: 15, 3: 215}

## prompt_verifier
- count: 300
- mean_f1: 0.043416
- median_f1: 0.000000
- f1_zero: 239 (79.7%)
- f1_positive: 61 (20.3%)
- f1_ge_0_5: 4 (1.3%)
- final_action_counts: {'answer': 69, 'abstain': 231}
- retrieval_call_counts: {1: 300}
- trajectory_round_counts: {1: 300}

## Pairwise Comparison
- ours wins: 21
- ours losses: 18
- ties: 261
- ours answer / prompt abstain: 11
- ours abstain / prompt answer: 4
- both answer: 65
- both abstain: 220

## Ours Retrieval Behavior
- extra_retrieval_records: 230 (76.7%)
- no_new_evidence_records: 230 (76.7%)
- no_new_evidence_and_abstain: 224
- no_new_evidence_and_answer: 6
- mean_f1_with_no_new_evidence: 0.002820
- mean_f1_without_no_new_evidence: 0.181985

## Ours Verifier Decision Signals
- need_more_evidence_counts_by_step: {'False': 78, 'True': 667}
- overall_sufficiency_counts_by_step: {'sufficient': 77, 'insufficient': 664, 'unclear': 3, 'conflicting': 1}
- risk_score_mean: 0.000000
- risk_score_max: 0.000000
- suggested_query_nonempty_steps: 667
- suggested_query_empty_steps: 78

## Cases: Ours wins over prompt_verifier
1. id=4hop1__58323_375563_161848_83118
   - question: When does daylight savings end in the country near the country where the author of The Book Thief is from?
   - gold: the first Sunday in April
   - ours: action=answer f1=0.211 calls=2 answer=Based on the provided evidence, daylight savings ends on the first Sunday in November in the United States, which is near the country where the author of The Book Thief (likely ...
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=2 evidence_gain=0.0 suff=sufficient need_more=False risk=0.0 suggested=
2. id=3hop2__20335_82856_9331
   - question: What dissolved the privileges in Poland of the empire that helped the patriots during the Revolutionary War, the Kingdom that acquired some Thuringian territory in 1815, and the...
   - gold: March Constitution of Poland
   - ours: action=answer f1=0.207 calls=1 answer=The March Constitution of 1921 in the Second Polish Republic legally abolished the privileges of the szlachta (nobility) that had been dependent upon the policies of the partiti...
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=1 evidence_gain=0.3333333333333333 suff=sufficient need_more=False risk=0.0 suggested=
3. id=2hop__770487_494646
   - question: What administrative territorial entity contains the headquarters of the Mono Lake Committee?
   - gold: Mono County
   - ours: action=answer f1=0.174 calls=1 answer=The headquarters of the Mono Lake Committee is based in Lee Vining, California, which is located in Mono County, California. Therefore, the administrative territorial entity tha...
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=1 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
4. id=3hop1__820301_720914_27537
   - question: Why did Roncalli leave the place where Crucifixion's creator died?
   - gold: for the conclave in Rome
   - ours: action=answer f1=0.164 calls=1 answer=Roncalli left Venice for the conclave in Rome well aware that he was a candidate to become the Pope, after the death of Pope Pius XII. The evidence does not specify why the plac...
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=1 evidence_gain=0.3333333333333333 suff=sufficient need_more=False risk=0.0 suggested=
5. id=2hop__84847_148696
   - question: What is the position of the 1st governor general of India?
   - gold: Governor-General of India
   - ours: action=answer f1=0.116 calls=2 answer=The position of the 1st governor general of India, as mentioned in the evidence, was largely ceremonial after India gained independence, with the day-to-day power exercised by t...
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=2 evidence_gain=0.0 suff=sufficient need_more=False risk=0.0 suggested=
6. id=3hop1__140786_2053_52946
   - question: When is Celebrity Big Brother coming to the broadcast company that, along with the network of Just Men!?, and ABC, is one of the major broadcasters based in New York?
   - gold: February 7, 2018
   - ours: action=answer f1=0.333 calls=1 answer=Celebrity Big Brother is set to premiere on February 7, 2018, according to the evidence provided.
   - prompt: action=answer f1=0.222 calls=1 answer=Celebrity Big Brother is coming to the broadcast company (CBS) during the winter of the 2017 -- 18 network television season, set to premiere on February 7, 2018.
   - ours_last: round=1 evidence_gain=0.6666666666666666 suff=sufficient need_more=False risk=0.0 suggested=
7. id=3hop1__652852_2053_52946
   - question: When is Celebrity Big Brother coming to the network that, along with ABC and the distributor of The Cube, is one of the the major broadcasters based in New York?
   - gold: February 7, 2018
   - ours: action=answer f1=0.222 calls=1 answer=Celebrity Big Brother is coming to the network (CBS) during the winter of the 2017-18 network television season, with a premiere set for February 7, 2018.
   - prompt: action=answer f1=0.162 calls=1 answer=Celebrity Big Brother is coming to the network during the winter of the 2017-18 network television season, with a premiere set for February 7, 2018. The network in question, CBS...
   - ours_last: round=1 evidence_gain=0.6666666666666666 suff=sufficient need_more=False risk=0.0 suggested=
8. id=2hop__10620_49084
   - question: Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time?
   - gold: Liam Thomas Garrigan
   - ours: action=answer f1=0.211 calls=1 answer=Liam Garrigan plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time.
   - prompt: action=answer f1=0.154 calls=1 answer=Liam Garrigan plays King Arthur in the ABC series Once Upon a Time, and since King Arthur is a legendary figure featured in Historia Regum Britanniae, the answer is Liam Garrigan.
   - ours_last: round=1 evidence_gain=0.5 suff=sufficient need_more=False risk=0.0 suggested=
9. id=2hop__28203_55840
   - question: Who played king whose regal Name did Albert Adopt in the king's speech?
   - gold: Colin Firth
   - ours: action=answer f1=0.235 calls=1 answer=Colin Firth played the king (George VI) whose regal name Albert adopted in "The King's Speech".
   - prompt: action=answer f1=0.182 calls=1 answer=Colin Firth played the future King George VI in "The King's Speech," whose regal name he adopted after his brother's abdication.
   - ours_last: round=1 evidence_gain=1.0 suff=sufficient need_more=False risk=0.0 suggested=
10. id=2hop__5658_25002
   - question: How long did the pact last between Kravchuk and the person who signed the decree suspending the Communist Party of the Russian SFSR?
   - gold: 10-year
   - ours: action=answer f1=0.167 calls=1 answer=The pact lasted for 10 years between Kravchuk and Yeltsin.
   - prompt: action=answer f1=0.118 calls=1 answer=The pact between Kravchuk and Yeltsin lasted for 10 years, as mentioned in the evidence provided.
   - ours_last: round=1 evidence_gain=1.0 suff=sufficient need_more=False risk=0.0 suggested=

## Cases: Ours loses to prompt_verifier
1. id=2hop__75207_365216
   - question: In which province is San Clemente, from the country where Fuser and Alberto meet the indigenous couple who were traveling to look for work?
   - gold: Talca Province
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=answer f1=0.211 calls=1 answer=The province where San Clemente is located, based on the provided evidence, is the Talca Province in Chile's Maule Region.
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Provide information about Fuser and Alberto meeting an indigenous couple and the context of their meeting.
2. id=3hop1__38426_91850_685675
   - question: What team does the person who hit the first home run at the new stadium in South Bronx play for?
   - gold: New York Yankees
   - ours: action=answer f1=0.103 calls=1 answer=The evidence provided indicates that Jorge Posada hit the first Yankee home run in the new Yankee Stadium. Since Jorge Posada was a player for the New York Yankees, the answer t...
   - prompt: action=answer f1=0.273 calls=1 answer=The person who hit the first home run at the new stadium in South Bronx, Jorge Posada, played for the New York Yankees.
   - ours_last: round=1 evidence_gain=0.3333333333333333 suff=sufficient need_more=False risk=0.0 suggested=
3. id=2hop__142699_67465
   - question: When did the rapper on On and On and Beyond release Best day Ever?
   - gold: March 11, 2011
   - ours: action=answer f1=0.353 calls=1 answer=Based on the evidence provided, Mac Miller released "Best Day Ever" on March 11, 2011.
   - prompt: action=answer f1=0.462 calls=1 answer=Mac Miller released "Best Day Ever" on March 11, 2011.
   - ours_last: round=1 evidence_gain=1.0 suff=sufficient need_more=False risk=0.0 suggested=
4. id=3hop1__635099_131926_89261
   - question: Where does the body of water by the city where Write This Down was formed empty into the Gulf of Mexico?
   - gold: the Mississippi River Delta
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=answer f1=0.108 calls=1 answer=Based on the evidence provided, the body of water by the city where Write This Down was formed (assuming it refers to the Colorado River in Texas, given the context) empties int...
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What city is associated with the band Write This Down and does it have a body of water that flows into the Gulf of Me...
5. id=2hop__681463_402641
   - question: Who is the sibling of Chiang Hsiao-wen?
   - gold: Chiang Hsiao-wu
   - ours: action=answer f1=0.136 calls=1 answer=Based on the provided evidence, the siblings of Chiang Hsiao-wen include one younger sister named Hsiao-chang and two younger brothers named Hsiao-wu and Hsiao-yung. Additionall...
   - prompt: action=answer f1=0.240 calls=1 answer=The sibling of Chiang Hsiao-wen is Hsiao-chang, and he also has two younger brothers, Hsiao-wu and Hsiao-yung, as well as two half-brothers, Winston Chang and John Chiang.
   - ours_last: round=1 evidence_gain=1.0 suff=sufficient need_more=False risk=0.0 suggested=
6. id=2hop__151750_141308
   - question: What company is the record label of Magic Christian Music part of?
   - gold: Apple Corps
   - ours: action=abstain f1=0.000 calls=2 answer=
   - prompt: action=answer f1=0.093 calls=1 answer=Apple Records Based on the evidence provided, Magic Christian Music was released on Apple Records, which is part of Apple Corps Ltd., founded by the Beatles. There is no direct ...
   - ours_last: round=2 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Is Apple Corps Ltd. part of a larger company, or is it an independent entity?
7. id=2hop__91626_96912
   - question: Who gives out the prize named after the author of The Wealth of Nations?
   - gold: University of Cambridge
   - ours: action=answer f1=0.111 calls=1 answer=The evidence provided indicates that the Adam Smith Prize is named after the author of The Wealth of Nations, Adam Smith. However, the Adam Smith Prize is awarded for best perfo...
   - prompt: action=answer f1=0.158 calls=1 answer=The evidence provided indicates that the Adam Smith Prize is named after the author of The Wealth of Nations, Adam Smith. However, the prize is given out by the University of Ca...
   - ours_last: round=1 evidence_gain=1.0 suff=sufficient need_more=False risk=0.0 suggested=
8. id=3hop1__742464_15840_36002
   - question: What were the Genesis's advantages over the platform in which Robodemons is played?
   - gold: built on 16-bit architectures and offered improved graphics and sound
   - ours: action=answer f1=0.186 calls=2 answer=Based on the provided evidence, the Genesis (Sega Mega Drive) had several advantages over the platform in which Robodemons is played (the Nintendo Entertainment System or NES): ...
   - prompt: action=answer f1=0.229 calls=1 answer=Based on the provided evidence, the Genesis (Sega's 16-bit console) had advantages over the Nintendo Entertainment System (NES), in which Robodemons is played, such as improved ...
   - ours_last: round=2 evidence_gain=0.0 suff=sufficient need_more=False risk=0.0 suggested=
9. id=2hop__23459_35124
   - question: How many books were said to be written by the most influential in Islamic philosophy?
   - gold: 450
   - ours: action=answer f1=0.069 calls=1 answer=The evidence provided states that Ibn Sina (Avicenna) had more than 450 books attributed to him. Since he is regarded as the most influential philosopher of Islam, the answer to...
   - prompt: action=answer f1=0.111 calls=1 answer=The most influential in Islamic philosophy, Ibn Sina (Avicenna), had more than 450 books attributed to him.
   - ours_last: round=1 evidence_gain=1.0 suff=sufficient need_more=False risk=0.0 suggested=
10. id=2hop__25797_25855
   - question: What does Dell call the feature that enables drives using the feature where 1.1 was the first widely used version, to remain powered when a computer is off?
   - gold: PowerShare
   - ours: action=answer f1=0.067 calls=1 answer=Dell calls the feature PowerShare. This feature allows devices to remain powered and charge even when the computer is off, which aligns with the description of the sleep-and-cha...
   - prompt: action=answer f1=0.105 calls=1 answer=Dell calls the feature PowerShare. This feature allows devices to remain powered and charge even when the computer is off.
   - ours_last: round=1 evidence_gain=1.0 suff=sufficient need_more=False risk=0.0 suggested=

## Cases: Ours no-new-evidence abstentions
1. id=2hop__129721_40482
   - question: From whom did the Huguenots in the state encompassing Zubly Cemetery purchase land from?
   - gold: Edmund Bellinger
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Identify the original landowner or the entity from whom the Huguenots purchased the land for Zubly Cemetery.
2. id=2hop__131951_643670
   - question: What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum?
   - gold: Het Scheur
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What is the name of the mouth of the watercourse by Rotterdam Centrum?
3. id=2hop__132854_417697
   - question: Mohammed Atta has what kind of model of the company that makes Datsun Type 12?
   - gold: Nissan Altima
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Does Mohammed Atta own or possess a Datsun model?
4. id=2hop__194469_83289
   - question: Who is the guy in the One Last Time video by the participant in The Listening Sessions?
   - gold: Matt Bennett
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Who is the participant in The Listening Sessions and what is the identity of the 'guy' in the One Last Time video?
5. id=2hop__20268_42014
   - question: How many members in the seats of the organization that enacted the Directory of Public Worship into law are members of the Scottish Government?
   - gold: 2
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=How many of the 129 elected members (MSPs) in the Scottish Parliament are also members of the Scottish Government?
6. id=2hop__244193_461106
   - question: What movement does the creator of the Washington Monument belong to?
   - gold: Greek Revival
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What movement does Robert Mills, the creator of the Washington Monument, belong to?
7. id=2hop__247353_55227
   - question: Who plays the wife of Here Comes the Boom's screenwriter in Grown Ups?
   - gold: Maria Bello
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Who is the wife of Here Comes the Boom's screenwriter in the movie Grown Ups?
8. id=2hop__286093_361551
   - question: In which county was James Finch born?
   - gold: Bay County
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=unclear need_more=True risk=0.0 suggested=In which county is Lynn Haven, Florida located?
9. id=2hop__286621_84856
   - question: When does the new season of the show named for the Politically Incorrect cast member?
   - gold: January 20, 2017
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=Find a show named for a Politically Incorrect cast member and its new season premiere date.
10. id=2hop__315267_277284
   - question: What administrative territorial entity includes the place where Bill Cockcroft was educated?
   - gold: Tonbridge, Kent
   - ours: action=abstain f1=0.000 calls=3 answer=
   - prompt: action=abstain f1=0.000 calls=1 answer=
   - ours_last: round=3 evidence_gain=0.0 suff=insufficient need_more=True risk=0.0 suggested=What is the administrative territorial entity that includes the location of The Judd School?
