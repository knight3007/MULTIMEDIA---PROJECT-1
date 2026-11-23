# Error attribution and correction priorities

**Run:** A-001 / 22/11/2026, existing-output review only. Every query/image label below is **AI preliminary**, not independent human ground truth. All 100 IDs assessed; 99 selected images viewed through newly generated contact sheets, with seven full-resolution follow-ups. No inference, download or new audio listening. Current primary selected assets (including staged replacements for 004/009) are distinct from old production assets. Historical labels are retained in the JSON matrix; new labels do not rewrite them. License is context only, excluded from quality scores.

## Evidence standard

CONFIRMED: a saved query/decision or explicit gate establishes the issue. CONFIRMED_OBSERVATION: a visible defect or recorded pool condition, **not necessarily the sole root cause**. SUSPECTED: plausible cause from preliminary judgment. UNRESOLVED: missing alternative candidates/scores prevents discrimination. Query, retrieval and ranking can contribute together; do not sum category counts as mutually exclusive error rates.

| Classification | Certainty | IDs (overlap allowed) |
| --- | --- | --- |
| CANDIDATE_POOL_MISMATCH | CONFIRMED_OBSERVATION | 2 |
| INPUT_APPROVAL_GATE | CONFIRMED | 1 |
| NO_CONFIRMED_ROOT_CAUSE | UNKNOWN | 39 |
| QWEN_QUERY_DESIGN | SUSPECTED | 20 |
| QWEN_TARGET_MISMATCH | CONFIRMED | 2 |
| RETRIEVAL_OR_RANKING | UNRESOLVED | 11 |
| VISUAL_ACCEPTANCE_GAP | CONFIRMED_OBSERVATION | 49 |

## Most informative failures

- 004/009: raw saved rice grain/chicken animal contradict approved food meanings. Confirmed query-to-target mismatch, not proof a larger model fixes the task. The primary selected food replacements came from overrides/curation.
- 035 shirt: source title says nasal-cavity anatomy; metadata and viewed image agree. Exactly one candidate downloaded. The sampled candidate pool was irrelevant; SigLIP had no retained alternative to choose. Do not blame a wrong pairwise ordering. Need candidate-quality and acceptance gates.
- 018 sun: one downloaded candidate is a spectrum chart. Query sun illumination is underspecified for the desired visible sun. Candidate-pool mismatch observed; query contribution suspected.
- 065 swim and 051 go: queries describe actions, selected images are static portraits. Final-output mismatch observed; all candidate bytes/scores are not retained, so retrieval vs SigLIP cannot be resolved.
- 058 drink: input nomu/uống is a verb but query drink beverage and image show nouns. Suspected grammatical/visual-intent problem before ranking.
- 092 dictionary: query permits computing dictionary, chosen key/value diagram is the wrong lesson referent. Sense disambiguation and candidate screening need review; no evidence proves the ranker rejected a better dictionary photo.

## Implementation observations (read-only)

`collect data script/imagecollector.py:295-397` downloads candidates, scores against the same query, sorts descending and unconditionally returns top score; `:580-630` saves/normalizes chosen bytes and cleans candidate cache. `image_scorer.py` supplies ranking scores; selected scores are not calibrated approval probabilities. No full retained candidate URLs/bytes/scores were found in the referenced historical ledger for the 100 selected items. Some counts/selected scores are available, enough for the one-candidate observations, not a fresh ranking benchmark.

## Prioritized actions — proposals only

1. **P0 input/meaning:** resolve 038 image intent and pending sense/register choices; label all uncertain query/image cases through the local gallery. Keep audio accepted; no re-listening queue.
2. **P0 query intent:** distinguish noun/action/adjective/time/function word; prefer observable scene/action/comparison instead of generic object/action suffixes. Freeze a revised prompt separately; do not alter historical caches to hide failures.
3. **P0 retrieval/acceptance:** reject title/metadata mismatches (035), ensure there are appropriate candidates and a reject-all/needs_review outcome. Screen dominant text/watermark as visual defects; license remains separate.
4. **P1 ranking evidence:** retain per-candidate source/title/hash, downloaded validity, score/order and exact prompt/model revision in future authorized experiments. Include positive/negative examples; no universal raw-score threshold justified here.
5. **P1 experiment:** after owner review, select a frozen small failure/control panel (004,009,019,035,041,051,058,065,092 plus clear noun controls). Compare prompt changes with fixed candidates, then retrieval changes with fixed queries; assess ranking only when candidate sets are retained. Record latency and coverage. Do not run any of these experiments during A-001.

No evidence yet justifies switching model size/provider over correcting intent, candidate selection and acceptance logic. A later model comparison needs identical inputs/prompts/budgets and independent labels; existing mixed history is not an apples-to-apples Qwen-vs-alternative benchmark.

## Per-ID attribution (multiple contributions allowed)

| ID | Attribution and evidence level | Basis |
| --- | --- | --- |
| vocab-000001 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000002 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000003 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000004 | QWEN_TARGET_MISMATCH / CONFIRMED | Saved original parsed query contradicts owner-approved sense; selected replacement is human/curated, not evidence Qwen improved. |
| vocab-000005 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000006 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000007 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000008 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000009 | QWEN_TARGET_MISMATCH / CONFIRMED | Saved original parsed query contradicts owner-approved sense; selected replacement is human/curated, not evidence Qwen improved. |
| vocab-000010 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000011 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000012 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000013 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000014 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000015 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000016 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000017 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000018 | CANDIDATE_POOL_MISMATCH / CONFIRMED_OBSERVATION; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Only one downloaded candidate was reported and selected; it is irrelevant. No better-candidate comparison exists.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000019 | QWEN_QUERY_DESIGN / SUSPECTED | Illumination misclassifies rain; rain/weather context is lost, with kana sense pending. |
| vocab-000020 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000021 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000022 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000023 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000024 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000025 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000026 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000027 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000028 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000029 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000030 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000031 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000032 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000033 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000034 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000035 | CANDIDATE_POOL_MISMATCH / CONFIRMED_OBSERVATION; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Only one downloaded candidate was reported and selected; it is irrelevant. No better-candidate comparison exists.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000036 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000037 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000038 | INPUT_APPROVAL_GATE / CONFIRMED | Saved staging history blocked absent approved image_search_intent; no image request for this item. |
| vocab-000039 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000040 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000041 | QWEN_QUERY_DESIGN / SUSPECTED | Today is a time relation, not a timepiece object. |
| vocab-000042 | QWEN_QUERY_DESIGN / SUSPECTED; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Tomorrow is a future day, not a timepiece category.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000043 | QWEN_QUERY_DESIGN / SUSPECTED; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Yesterday is past time, not a place.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000044 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000045 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000046 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000047 | QWEN_QUERY_DESIGN / SUSPECTED; RETRIEVAL_OR_RANKING / UNRESOLVED; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Easy object does not specify what task is easy or contrast difficulty; yasashii sense pending.; Selected image conflicts with query; absent full candidates/scores prevents separating retrieval from ranking.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000048 | QWEN_QUERY_DESIGN / SUSPECTED; RETRIEVAL_OR_RANKING / UNRESOLVED; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Difficult object is underspecified; need a difficult task or comparison.; Selected image conflicts with query; absent full candidates/scores prevents separating retrieval from ranking.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000049 | QWEN_QUERY_DESIGN / SUSPECTED | Beautiful object is arbitrary and kirei may mean clean; no chosen visual context. |
| vocab-000050 | QWEN_QUERY_DESIGN / SUSPECTED; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Strong object lacks person/material context or a visible strength comparison.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000051 | RETRIEVAL_OR_RANKING / UNRESOLVED | Selected image conflicts with query; absent full candidates/scores prevents separating retrieval from ranking. |
| vocab-000052 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000053 | RETRIEVAL_OR_RANKING / UNRESOLVED; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Selected image conflicts with query; absent full candidates/scores prevents separating retrieval from ranking.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000054 | QWEN_QUERY_DESIGN / SUSPECTED; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Study object converts benkyou-suru action into an unspecified object.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000055 | QWEN_QUERY_DESIGN / SUSPECTED; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Work object loses hataraku action and invites product-name matches.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000056 | QWEN_QUERY_DESIGN / SUSPECTED; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Sleep object loses neru action and invites related accessories.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000057 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000058 | QWEN_QUERY_DESIGN / SUSPECTED | Drink beverage selects a noun while nomu/uống are the drinking action. |
| vocab-000059 | RETRIEVAL_OR_RANKING / UNRESOLVED | Selected image conflicts with query; absent full candidates/scores prevents separating retrieval from ranking. |
| vocab-000060 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000061 | RETRIEVAL_OR_RANKING / UNRESOLVED; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Selected image conflicts with query; absent full candidates/scores prevents separating retrieval from ranking.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000062 | QWEN_QUERY_DESIGN / SUSPECTED; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Remember object turns memory action into an object phrase; need a recall scenario.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000063 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000064 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000065 | RETRIEVAL_OR_RANKING / UNRESOLVED | Selected image conflicts with query; absent full candidates/scores prevents separating retrieval from ranking. |
| vocab-000066 | QWEN_QUERY_DESIGN / SUSPECTED; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Software is not a physical device; classifier misleads toward electronics.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000067 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000068 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000069 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000070 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000071 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000072 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000073 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000074 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000075 | QWEN_QUERY_DESIGN / SUSPECTED; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Experience object converts experiential knowledge to an object phrase; user-experience drift.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000076 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000077 | QWEN_QUERY_DESIGN / SUSPECTED; RETRIEVAL_OR_RANKING / UNRESOLVED | Important object supplies no cue why something is important; adjective remains underspecified.; Selected image conflicts with query; absent full candidates/scores prevents separating retrieval from ranking. |
| vocab-000078 | QWEN_QUERY_DESIGN / SUSPECTED; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Different object has no explicit comparison relation; chigau is relational.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000079 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000080 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000081 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000082 | QWEN_QUERY_DESIGN / SUSPECTED; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Always is frequency, not an object; missing repeated-time representation.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000083 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000084 | QWEN_QUERY_DESIGN / SUSPECTED; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Together is a relation/adverb, not an object category; needs people/things acting together.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000085 | RETRIEVAL_OR_RANKING / UNRESOLVED; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Selected image conflicts with query; absent full candidates/scores prevents separating retrieval from ranking.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000086 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000087 | QWEN_QUERY_DESIGN / SUSPECTED; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Hello is a greeting, not an object; daytime Japanese greeting context also pending.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000088 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000089 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000090 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000091 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000092 | RETRIEVAL_OR_RANKING / UNRESOLVED; VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Selected image conflicts with query; absent full candidates/scores prevents separating retrieval from ranking.; Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000093 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000094 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000095 | RETRIEVAL_OR_RANKING / UNRESOLVED | Selected image conflicts with query; absent full candidates/scores prevents separating retrieval from ranking. |
| vocab-000096 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000097 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000098 | VISUAL_ACCEPTANCE_GAP / CONFIRMED_OBSERVATION | Visible text/preview contamination in chosen bytes; no standalone proof SigLIP ranked a better candidate below it. |
| vocab-000099 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
| vocab-000100 | NO_CONFIRMED_ROOT_CAUSE / UNKNOWN | Preliminary review only; inspect complete candidate evidence before causal claims. |
