# Stratified45 Final-Target Binding Pilot

## Per-Hop Comparison
| run | hop | n | answer_f1 | coverage | selective_answer_f1 | avg_rounds | binding_reject | closure_not_final | closure_success | nonjson |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 2hop | 15 | 0.5000 | 0.7333 | 0.6818 | 1.6000 | 0 | 0 | 1 | 0 |
| baseline | 3hop | 15 | 0.1903 | 0.3333 | 0.5710 | 2.2000 | 0 | 0 | 1 | 0 |
| baseline | 4hop | 15 | 0.1000 | 0.3333 | 0.3000 | 2.5333 | 0 | 0 | 5 | 1 |
| baseline | all | 45 | 0.2634 | 0.4667 | 0.5645 | 2.1111 | 0 | 0 | 7 | 1 |
| final_target_binding | 2hop | 15 | 0.4867 | 0.7333 | 0.6636 | 1.4667 | 0 | 0 | 0 | 0 |
| final_target_binding | 3hop | 15 | 0.2570 | 0.4667 | 0.5507 | 2.0000 | 0 | 0 | 2 | 0 |
| final_target_binding | 4hop | 15 | 0.1000 | 0.3333 | 0.3000 | 2.4667 | 0 | 0 | 4 | 0 |
| final_target_binding | all | 45 | 0.2812 | 0.5111 | 0.5502 | 1.9778 | 0 | 0 | 6 | 0 |

## Changed Cases
| id | hop | delta_f1 | baseline | new | gold | binding_reject | closure_not_final |
|---|---|---:|---|---|---|---:|---:|
| 3hop1__140786_2053_52946 | 3hop | 1.000 | abstain  r2 f1=0.000 | answer February 7, 2018 r1 f1=1.000 | February 7, 2018 | 0 | 0 |
| 2hop__10620_49084 | 2hop | 0.800 | abstain  r2 f1=0.000 | answer Liam Garrigan r1 f1=0.800 | Liam Thomas Garrigan | 0 | 0 |
| 4hop1__28352_53706_795904_580996 | 4hop | 0.000 | abstain  r3 f1=0.000 | answer Canada r3 f1=0.000 | Rio Linda | 0 | 0 |
| 4hop1__264443_49925_13759_736921 | 4hop | 0.000 | abstain  r3 f1=0.000 | abstain  r2 f1=0.000 | Saxony-Anhalt | 0 | 0 |
| 4hop1__166471_49925_13759_736921 | 4hop | 0.000 | answer New York r2 f1=0.000 | abstain  r2 f1=0.000 | Saxony-Anhalt | 0 | 0 |
| 4hop1__161605_32392_823060_610794 | 4hop | 0.000 | answer Charleston County r3 f1=0.500 | answer Charleston County r2 f1=0.500 | Richland County | 0 | 0 |
| 4hop1__151650_5274_458768_33637 | 4hop | 0.000 | abstain  r2 f1=0.000 | abstain  r3 f1=0.000 | two | 0 | 0 |
| 4hop1__151650_5274_458768_33632 | 4hop | 0.000 | answer 7 October r2 f1=0.000 | abstain  r2 f1=0.000 | May 4 | 0 | 0 |
| 4hop1__145494_698949_157828_162309 | 4hop | 0.000 | abstain  r2 f1=0.000 | answer 1920 r3 f1=0.000 | 2016 | 0 | 0 |
| 4hop1__105688_17130_70784_79935 | 4hop | 0.000 | abstain  r3 f1=0.000 | abstain  r2 f1=0.000 | 1930 | 0 | 0 |
| 3hop1__145194_160545_62931 | 3hop | 0.000 | answer Koh Phi Phi r2 f1=0.800 | answer Koh Phi Phi r1 f1=0.800 | island Koh Phi Phi | 0 | 0 |
| 3hop1__144439_443779_52195 | 3hop | 0.000 | abstain  r2 f1=0.000 | answer Xanana Gusmão r2 f1=0.000 | Francisco Guterres | 0 | 0 |
| 3hop1__140786_2053_5289 | 3hop | 0.000 | abstain  r3 f1=0.000 | abstain  r2 f1=0.000 | Oriole Records. | 0 | 0 |
| 2hop__194469_83289 | 2hop | 0.000 | answer Matt Bennett r2 f1=1.000 | answer Matt Bennett r1 f1=1.000 | Matt Bennett | 0 | 0 |
| 2hop__167577_31122 | 2hop | -1.000 | answer 18th r3 f1=1.000 | abstain  r3 f1=0.000 | 18th | 0 | 0 |

## Closure Success Quality
| run | successes | exact_f1_1 | partial_positive | f1_zero | mean_f1 |
|---|---:|---:|---:|---:|---:|
| baseline | 7 | 2 | 1 | 4 | 0.3571 |
| final_target_binding | 6 | 0 | 1 | 5 | 0.0833 |