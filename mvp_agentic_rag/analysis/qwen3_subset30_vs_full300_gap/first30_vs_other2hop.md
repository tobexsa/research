# First30 2-hop vs Remaining 2-hop

## first30_2hop
- n=30 answer_f1=0.5833 coverage=0.8000 actions={'abstain': 6, 'answer': 24} rounds={2: 11, 1: 15, 3: 4}
- closure_attempt=7 closure_success=1 cost_cleanup=2 nonjson=0
- answer_type={'short_entity': 18, 'date/number': 8, 'place/entity': 3, 'long_phrase': 1}
- type_f1={'date/number': 0.75, 'long_phrase': 0.3333, 'place/entity': 0.3333, 'short_entity': 0.5648}

## remaining70_2hop
- n=70 answer_f1=0.3846 coverage=0.7143 actions={'abstain': 20, 'answer': 50} rounds={3: 6, 2: 37, 1: 27}
- closure_attempt=18 closure_success=6 cost_cleanup=8 nonjson=0
- answer_type={'short_entity': 50, 'date/number': 6, 'long_phrase': 5, 'place/entity': 9}
- type_f1={'date/number': 0.5833, 'long_phrase': 0.04, 'place/entity': 0.3333, 'short_entity': 0.4045}

## Remaining70 2-hop F1-zero Examples
| id | action | f1 | answer | gold | rounds | closure_success | cost_cleanup | question |
|---|---|---:|---|---|---:|---|---|---|
| 2hop__37656_36240 | abstain | 0.000 |  | Genesis 3:15 | 3 | False | False | What specific part of the document that is the highest authority in Protestantism for morals reference Mary? |
| 2hop__39063_593388 | abstain | 0.000 |  | Sir Robert Peel, 1st Baronet | 2 | False | False | Who is the father of the person who came up with the concept of the "new" police? |
| 2hop__40270_11402 | abstain | 0.000 |  | 17.037 square miles | 2 | False | True | According to the agency that considers if Los Angeles County is to be a separate metropolitan area, what is the total area in square miles? |
| 2hop__496792_392646 | abstain | 0.000 |  | Scottish clan | 2 | False | True | A participant of the Battle of Brechin is an instance of? |
| 2hop__511454_120259 | abstain | 0.000 |  | 918 | 2 | False | False | When was Lady Godiva's birthplace abolished? |
| 2hop__557743_92763 | abstain | 0.000 |  | 16,801 | 2 | False | False | What is the enrollment at Henry Latimer's alma mater? |
| 2hop__562154_69048 | abstain | 0.000 |  | Honorable Justice Abiodun Smith | 2 | False | False | Who is the Chief Judge in the place where DeltaWomen's headquarters in located? |
| 2hop__57638_615257 | abstain | 0.000 |  | Oklahoma City Thunder | 2 | False | True | What team is the person with the highest point average in NBA history on? |
| 2hop__593633_82341 | abstain | 0.000 |  | in Northern Florida | 2 | False | True | Where is New Perry's place of death found in Florida? |
| 2hop__61924_712629 | abstain | 0.000 |  | Philip Mountbatten | 2 | False | False | Who is the spouse of the current queen of England? |
| 2hop__62369_84616 | abstain | 0.000 |  | for Best Performance by a Leading Actress in a Play in Ondine | 2 | False | True | What did the singer of "Moon River" in the movie Breakfast at Tiffany win a Tony for? |
| 2hop__684287_78303 | abstain | 0.000 |  | Cordell Walker | 2 | False | True | what was the name of the producer of Forest Warrior walker texas ranger? |
| 2hop__71034_343058 | abstain | 0.000 |  | Adrian Edmondson | 2 | False | False | Who is the spouse of the person who sang holding out for a hero in shrek 2? |
| 2hop__73719_510545 | abstain | 0.000 |  | Jennifer Connelly | 2 | False | True | Who is the spouse of the actor who plays Jarvis in Iron Man? |
| 2hop__809785_606637 | abstain | 0.000 |  | Secret City Records | 3 | False | False | What record label does the performer of Adventures in Your Own Backyard belong to? |
| 2hop__810411_159673 | abstain | 0.000 |  | The Hateful Eight | 2 | False | True | What other film is the cast member of Now You See Him, Now You Don't a character for? |
| 2hop__818302_25719 | abstain | 0.000 |  | 406 | 2 | False | False | At the end of which year did the tribes from the location of the Lusatia invade the Roman Empire? |
| 2hop__82910_75184 | abstain | 0.000 |  | Claudia Wells | 2 | False | False | Who played the girlfriend of Alex P. Keaton's actor on Family Ties in Back to the Future? |
| 2hop__85455_158105 | abstain | 0.000 |  | ease of use and enhanced support for Plug and Play | 3 | False | False | Which two features were played up the person who had the biggest net worth in 2017? |
| 2hop__91626_96912 | abstain | 0.000 |  | University of Cambridge | 2 | False | False | Who gives out the prize named after the author of The Wealth of Nations? |
| 2hop__38030_23241 | answer | 0.000 | 49.3% | 48.8 percent | 2 | False | False | According to Pew, in 2010, what percent of Nigeria's population practiced the religion dominant in the countries surrounding Armenia? |
| 2hop__417937_158105 | answer | 0.000 | digital infrastructures, information networks | ease of use and enhanced support for Plug and Play | 1 | False | False | Which two features were played up by the author of Business @ the Speed of Thought? |
| 2hop__46550_85990 | answer | 0.000 | Nancy Pelosi | anti-slavery activists, modernizers, ex Whigs and ex Free Soilers | 2 | True | False | Who were the leaders of the opposition of the party that controlled the house of representatives in 2002? |
| 2hop__471509_136043 | answer | 0.000 | Nina Sky | Natalie Albino | 1 | False | False | The Nicole and Natalie album's band is named after who? |
| 2hop__607517_161450 | answer | 0.000 | Golestan Province | in the north-east of the country south of the Caspian Sea | 1 | False | False | Where is the province containing Bandar-e Gaz County located? |
| 2hop__62951_64006 | answer | 0.000 | Europe | 30% to 65% | 1 | False | False | As a result of the Black Death, how much was the population reduced in the place that the US helped with the Marshall Plan? |
| 2hop__645448_77615 | answer | 0.000 | 1922 | 1912 | 1 | False | False | When did military instruction start at the place where Larry Alcala was educated? |
| 2hop__686395_141338 | answer | 0.000 | Brooklyn College | City University of New York | 2 | False | False | What company is Frederic Ewen's employer part of? |
| 2hop__704217_82341 | answer | 0.000 | Ocala | in Northern Florida | 1 | False | False | Where is Sean Hampton's birth place in the state of Florida? |
| 2hop__708145_30351 | answer | 0.000 | Ludwig von Mises | the Austrian government | 1 | False | False | Who did Hayek work for upon being hired by the author of Bureaucracy? |
| 2hop__748182_78303 | answer | 0.000 | Chuck Norris | Cordell Walker | 1 | False | False | What was the name of one of Top Dog's cast members in the Walker, Texas Ranger? |
| 2hop__75207_365216 | answer | 0.000 | Chile | Talca Province | 2 | False | False | In which province is San Clemente, from the country where Fuser and Alberto meet the indigenous couple who were traveling to look for work? |
| 2hop__753715_51329 | answer | 0.000 | Broadway's Like That | The African Queen | 3 | True | False | with what movie did Mary Philips' husband win his only oscar? |
| 2hop__77518_548781 | answer | 0.000 | Calvin Coolidge | Plymouth Notch | 1 | False | False | Where was the president born on the fourth of July born? |
| 2hop__82669_768138 | answer | 0.000 | Christopher Masterson | Matthew Lawrence | 2 | True | False | Who is the brother of the Melissa and Joey Theme Song singer? |