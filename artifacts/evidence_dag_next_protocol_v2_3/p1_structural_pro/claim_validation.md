# P1 Claim Validation

| Claim | Metric | Expected | Observed | Verdict |
|---|---|---|---|---|
| Direct Topology is usable after P0B passes | Route A topology match | materially above 16.67% majority | 0/60 (0%) | refuted |
| Hop→Shape improves end-to-end topology | C2P topology match | usable macro-F1 and low invalid | 7/60; macro-F1 0.0751; 18/60 invalid | refuted |
| Gold decomposition exposes a usable pairwise structural upper bound | C4A exact graph / consistency | high consistency and exact recovery | 1/60 exact; 2/60 consistent | refuted |
| P0 proves the API can enforce fixed schema payloads | P0A/P0B canonical/semantic | 100% | 216/216 P0A and 432/432 P0B | supported, but scope narrowed to fixed-copy tasks |
| P1 failure is only transport failure | transport success | failures correlate with transport loss | 362/362 transport success | refuted |
| Decoder pathology is lexical token repetition | repeated-token defect | repeated lexical tokens in length rows | 0 detected; raw shows whitespace loops | refuted; whitespace-loop mechanism supported |

Primary failure type: `direction_underperforming`, with an additional provider-guided-decoding whitespace-loop mechanism. Comparison quality is high for dataset and metric identity, but model-only attribution is limited because the provider revision/backend is undisclosed.
