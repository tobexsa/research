# Qwen3 Stratified45 Guarded Cost-Cleanup Baseline

## Per-Hop Claim Risk Metrics
| hop | n | answer_f1 | coverage | selective_answer_f1 | avg_rounds | nonjson | closure_attempt | closure_success | cost_cleanup |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2hop | 15 | 0.5000 | 0.7333 | 0.6818 | 1.6000 | 0 | 5 | 1 | 1 |
| 3hop | 15 | 0.1903 | 0.3333 | 0.5710 | 2.2000 | 0 | 9 | 1 | 4 |
| 4hop | 15 | 0.1000 | 0.3333 | 0.3000 | 2.5333 | 1 | 12 | 5 | 1 |
| all | 45 | 0.2634 | 0.4667 | 0.5645 | 2.1111 | 1 | - | 7 | - |

## Closure Successes
| id | hop | f1 | candidate | gold | question |
|---|---|---:|---|---|---|
| 2hop__167577_31122 | 2hop | 1.000 | 18th | 18th | What century did the author of A Treatise Concerning the Principles of Human Knowledge live in? |
| 3hop1__159803_89752_75165 | 3hop | 0.000 | 39.3 million | 1,335,907 | What's the population of the largest state in the region of the U.S. where trading practices were once threatened by the Navigation Acts? |
| 4hop1__151650_5274_458768_33632 | 4hop | 0.000 | 7 October | May 4 | What day is the Feast in the city where the headquarters of the only group larger than Desde El Principio's record label held on? |
| 4hop1__152146_5274_458768_33632 | 4hop | 0.000 | 18 November | May 4 | What day is the Feast held in the city where the headquarters of the only group larger than Långa nätter's record label is located? |
| 4hop1__161605_32392_823060_610794 | 4hop | 0.500 | Charleston County | Richland County | What county is the city that shares a border with the state capital of the state where Darlington County located in? |
| 4hop1__161810_583746_457883_650651 | 4hop | 1.000 | NBC | NBC | Country A has an embassy from the country that contains the bay where the city of General Santos is located. What network created country A's version of The Biggest Loser? |
| 4hop1__166471_49925_13759_736921 | 4hop | 0.000 | New York | Saxony-Anhalt | In what state is the district where the one who wanted to reform and address the institution behind the religion of Egidio Vagnozzi preached a sermon? |