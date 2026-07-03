# Qwen3 Regression Diagnosis

- method: `claim_risk`
- shared cases: 30
- regressions: 8
- improvements: 5
- ties: 17

## Diagnosis Counts

- tie_or_small_difference: 14
- qwen_verifier_or_answer_more_permissive: 6
- answer_generation_lower_quality: 5
- qwen_abstained_despite_sufficient_verifier: 2
- answer_repair_not_triggered_or_not_needed_by_qwen: 1
- qwen_verifier_stricter_or_answer_not_supported: 1
- qwen_answer_generation_improved: 1

## Largest Regressions

### 2hop__25396_593388 delta=-1.0000

- diagnosis: `qwen_abstained_despite_sufficient_verifier`
- question: Who was the father of the person who issued the Tamworth manifesto?
- gold: Sir Robert Peel, 1st Baronet
- original: action=answer f1=1.0000 repair=0 suff=sufficient answer=Sir Robert Peel, 1st Baronet
- qwen: action=abstain f1=0.0000 repair=0 suff=sufficient answer=

### 2hop__286093_361551 delta=-1.0000

- diagnosis: `answer_generation_lower_quality`
- question: In which county was James Finch born?
- gold: Bay County
- original: action=answer f1=1.0000 repair=0 suff=sufficient answer=Bay County
- qwen: action=answer f1=0.0000 repair=0 suff=sufficient answer=Florida

### 2hop__374495_68633 delta=-1.0000

- diagnosis: `qwen_abstained_despite_sufficient_verifier`
- question: Who is the president of the organization that Avery Brundage is a member of?
- gold: Thomas Bach
- original: action=answer f1=1.0000 repair=0 suff=sufficient answer=Thomas Bach
- qwen: action=abstain f1=0.0000 repair=0 suff=sufficient answer=

### 2hop__29873_679424 delta=-0.6667

- diagnosis: `answer_generation_lower_quality`
- question: In which country is the province where Serbian and Croatian languages are both official?
- gold: SR Serbia
- original: action=answer f1=0.6667 repair=0 suff=sufficient answer=Serbia
- qwen: action=answer f1=0.0000 repair=0 suff=sufficient answer=Vojvodina

### 2hop__23459_35124 delta=-0.6000

- diagnosis: `answer_generation_lower_quality`
- question: How many books were said to be written by the most influential in Islamic philosophy?
- gold: 450
- original: action=answer f1=1.0000 repair=0 suff=sufficient answer=450
- qwen: action=answer f1=0.4000 repair=0 suff=sufficient answer=More than 450 books.

### 2hop__341176_711757 delta=-0.5000

- diagnosis: `answer_generation_lower_quality`
- question: What other district is found in the same county as Gmina Stężyca?
- gold: Gmina Ryki
- original: action=answer f1=1.0000 repair=0 suff=sufficient answer=Gmina Ryki
- qwen: action=answer f1=0.5000 repair=0 suff=sufficient answer=Ryki County

### 2hop__153573_44085 delta=-0.3333

- diagnosis: `answer_repair_not_triggered_or_not_needed_by_qwen`
- question: What was the show named after the character featured in the video game Mickey's Safari in Letterland?
- gold: The Mickey Mouse Club
- original: action=answer f1=0.3333 repair=1 suff=sufficient answer=Metal Mickey
- qwen: action=abstain f1=0.0000 repair=0 suff=insufficient answer=

### 2hop__269766_43945 delta=-0.0714

- diagnosis: `answer_generation_lower_quality`
- question: Common Sense which was written by the author of The Age of Reason was an important work because?
- gold: crystallized the rebellious demand for independence from Great Britain
- original: action=answer f1=0.5000 repair=0 suff=sufficient answer=advocating independence from Great Britain to people in the Thirteen Colonies
- qwen: action=answer f1=0.4286 repair=0 suff=sufficient answer=Because it advocated independence from Great Britain and encouraged people in the Thirteen Colonies to fight for egalitarian government.


## Largest Improvements

### 2hop__129721_40482 delta=1.0000

- diagnosis: `qwen_verifier_or_answer_more_permissive`
- question: From whom did the Huguenots in the state encompassing Zubly Cemetery purchase land from?
- gold: Edmund Bellinger
- original: action=abstain f1=0.0000 repair=0 suff=insufficient answer=
- qwen: action=answer f1=1.0000 repair=0 suff=sufficient answer=Edmund Bellinger

### 2hop__20268_42014 delta=1.0000

- diagnosis: `qwen_verifier_or_answer_more_permissive`
- question: How many members in the seats of the organization that enacted the Directory of Public Worship into law are members of the Scottish Government?
- gold: 2
- original: action=abstain f1=0.0000 repair=0 suff=insufficient answer=
- qwen: action=answer f1=1.0000 repair=0 suff=sufficient answer=2

### 2hop__167577_31122 delta=0.6667

- diagnosis: `qwen_verifier_or_answer_more_permissive`
- question: What century did the author of A Treatise Concerning the Principles of Human Knowledge live in?
- gold: 18th
- original: action=abstain f1=0.0000 repair=0 suff=unclear answer=
- qwen: action=answer f1=0.6667 repair=0 suff=sufficient answer=18th century.

### 2hop__315267_277284 delta=0.6667

- diagnosis: `qwen_verifier_or_answer_more_permissive`
- question: What administrative territorial entity includes the place where Bill Cockcroft was educated?
- gold: Tonbridge, Kent
- original: action=abstain f1=0.0000 repair=0 suff=insufficient answer=
- qwen: action=answer f1=0.6667 repair=0 suff=sufficient answer=Kent

### 2hop__142699_67465 delta=0.5000

- diagnosis: `qwen_answer_generation_improved`
- question: When did the rapper on On and On and Beyond release Best day Ever?
- gold: March 11, 2011
- original: action=answer f1=0.5000 repair=0 suff=sufficient answer=2011
- qwen: action=answer f1=1.0000 repair=0 suff=sufficient answer=March 11, 2011.

### 2hop__10620_49084 delta=0.0000

- diagnosis: `tie_or_small_difference`
- question: Who plays the legendary figure featured in Historia Regum Britanniae in the show Once Upon a Time?
- gold: Liam Thomas Garrigan
- original: action=answer f1=0.8000 repair=1 suff=sufficient answer=Liam Garrigan
- qwen: action=answer f1=0.8000 repair=0 suff=sufficient answer=Liam Garrigan

### 2hop__131951_643670 delta=0.0000

- diagnosis: `qwen_verifier_or_answer_more_permissive`
- question: What is the name for the mouth of the watercourse of the body of water by Rotterdam Centrum?
- gold: Het Scheur
- original: action=abstain f1=0.0000 repair=0 suff=insufficient answer=
- qwen: action=answer f1=0.0000 repair=0 suff=sufficient answer=Nieuwe Maas River

### 2hop__132854_417697 delta=0.0000

- diagnosis: `tie_or_small_difference`
- question: Mohammed Atta has what kind of model of the company that makes Datsun Type 12?
- gold: Nissan Altima
- original: action=abstain f1=0.0000 repair=0 suff=insufficient answer=
- qwen: action=abstain f1=0.0000 repair=0 suff=insufficient answer=

