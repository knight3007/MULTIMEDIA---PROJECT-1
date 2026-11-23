"""Format the completed local review data; no AI, media fetch or source mutation."""
from pathlib import Path
from collections import Counter
import csv
import html
import json

OUT = Path(__file__).resolve().parent
items = json.loads((OUT/'evaluation_matrix.json').read_text(encoding='utf-8'))['items']
stats = json.loads((OUT/'statistics.json').read_text(encoding='utf-8'))


def write(name, text):
    (OUT/name).write_text(text.rstrip()+'\n', encoding='utf-8')


def table(rows):
    return '\n'.join('| '+' | '.join(str(v).replace('|','/').replace('\n',' ') for v in row)+' |' for row in rows)


def stat_table(keys):
    rows=[['Metric','PASS','FAIL','NEEDS_REVIEW','UNKNOWN','P+F denominator','PASS/(P+F)'],['---']*7]
    for k in keys:
        s=stats[k];c=s['counts']
        rows.append([k,*[c[x] for x in ['PASS','FAIL','NEEDS_REVIEW','UNKNOWN']],s['definitive_pass_fail_denominator'],str(s['pass_percent_definitive_only'])+'%'])
    return table(rows)


intro='''**Run:** A-001 / 22/11/2026, existing-output review only. Every query/image label below is **AI preliminary**, not independent human ground truth. All 100 IDs assessed; 99 selected images viewed through newly generated contact sheets, with seven full-resolution follow-ups. No inference, download or new audio listening. Current primary selected assets (including staged replacements for 004/009) are distinct from old production assets. Historical labels are retained in the JSON matrix; new labels do not rewrite them. License is context only, excluded from quality scores.
'''

write('02_semantic_assessment.md','# Semantic assessment — 100 queries\n\n'+intro+'''
## Rubric and denominators

PASS: meaning/context preserved and sufficiently specific for visual search. FAIL: clear mismatch or inadequate visual-search representation under the stated flashcard rubric. NEEDS_REVIEW: ambiguity, register, chosen sense, visual metaphor or specificity needs human decision. UNKNOWN: evidence cannot support assessment. Query overall is FAIL if any of six dimensions FAIL; otherwise UNKNOWN if any unknown, then NEEDS_REVIEW if any such flag, else PASS. It is stricter than correct_meaning alone. These are per-ID judgments with rationale, not regex classifications. Human approval of a target sense does not approve a raw query.

'''+stat_table(['query_overall','query_correct_meaning','query_specificity','query_context_appropriateness','query_ambiguity','query_translation_consistency','query_visual_search_suitability'])+'''

All rows use N=100; counts are also percentages of the complete set. PASS/(P+F) excludes NEEDS_REVIEW/UNKNOWN and must not be read as accuracy on all 100. For query overall it is 37/59=62.71%; meaning alone is 75/91=82.42%. No human semantic accuracy estimate is certified.

The underlying 100 queries are a heterogeneous historical cache/staging collection: six corrected-verb raw outputs, original prompt signature evidence, human overrides for 004/009. They are not a controlled fresh 100-item run of one immutable prompt/revision. Accepted raw decoded text is missing for 94 IDs. Every parsed query was rechecked against its referenced cache file (100 matches). Exact historical model revisions remain MISSING_EVIDENCE; do not substitute the revision of a later 25-row A/B experiment.

## Per-ID preliminary judgment

Detailed six-dimensional labels and original/effective query are in evaluation_matrix.csv/JSON. Reasons below are preliminary linguistic/visual-search judgments; pending semantic decisions remain unchanged.

'''+table([['ID','EN / JP / VN','Original parsed query','Overall','Reason'],['---']*5]+[[x['vocab_id'],f"{x['english']} / {x['japanese']} / {x['vietnamese']}",x['parsed_qwen_query'],x['query_overall'],x['query_reason']] for x in items]))

write('03_image_assessment.md','# Selected-image assessment — 100 IDs\n\n'+intro+'''
## Rubric

Relevance concerns the intended referent/action/context, not license. Visual quality concerns clarity, distracting clutter and text/preview contamination at vocabulary-card scale. Learning suitability combines these observations with whether a simple visual can teach the term. Text is not automatically a failure: incidental package labels/signage can remain NEEDS_REVIEW, while dense slide text/preview overlays obstruct the intended use. Review is at contact-sheet scale; full file links remain available for the owner. This is not an exhaustive pixel-level review of every original.

'''+stat_table(['image_relevance','image_visual_quality','image_learning_suitability','image_technical'])+'''

N=100 IDs, 99 actual selected images and one absent (038). Relevance definitive subset is 71, visual 86, learning suitability 82. PASS/(P+F) is respectively 61.97%, 45.35%, 32.93%; these exclude uncertain/missing items. Reviewed images with any visual judgment: 99. AI visual assessment is not owner approval. All 99 decoded, matched saved hashes/dimensions/word/query metadata. This does not make them semantically suitable.

Rice/chicken primary images now depict the approved food senses, but source queries are human/curated replacements; old production images still depict the wrong senses. Correct replacements must not inflate original Qwen performance. ID038 has no chosen image because the existing semantic input gate lacks approved image intent; it is UNKNOWN/MISSING_EVIDENCE, not an image FAIL.

'''+table([['ID','Relevance','Visual','Learning','Contamination','Scene/object observation'],['---']*6]+[[x['vocab_id'],x['image_relevance'],x['image_visual_quality'],x['image_learning_suitability'],x['image_contamination'],x['image_scene_observation']] for x in items]))

write('04_audio_assessment.md','# Audio assessment — owner acceptance recorded\n\n'+intro+'''
## Current user decision supersedes a request for further listening

User instruction in this session: **“audio đều pass cả không cần review lại chỉ có ảnh là cần xử lý cho chính xác hơn”**. All 100 current audio are recorded PASS by owner batch acceptance, bound to observed paths and SHA-256 in owner_audio_acceptance.json. No new listening or independent per-file phonetic certification is claimed. Audio re-review is not an A-001 blocker or recommended next task.

Technical checks freshly parsed complete MP3 frames with existing validate_audio, checked SHA-256, duration, byte size, Japanese word/reading, source row key, provider/locale/voice and stored path against metadata. All 100 PASS; metadata strings match canonical Japanese text. This verifies association and technical consistency, not a new listening judgment. Historical exact-hash listening records for the first 10 were independently cross-referenced to the pilot/batch-2 reports and current hashes; later historical pending/general-feedback records are retained unchanged. The new owner acceptance governs current audio status.

'''+stat_table(['audio_technical','audio_pronunciation_review'])+'''

N=100; owner-accepted pronunciation 100/100; new agent listening 0; historical exact-hash report approvals verified 10/100. No recorded pronunciation failure was newly discovered, and no claim is made that an independent phonetic review of the other 90 was performed. Distribution rights are separate from this acceptance and only reviewed for actual release subset.

'''+table([['ID','Japanese','Integrity/metadata','Current acceptance','Historical listening record'],['---']*5]+[[x['vocab_id'],x['japanese'],x['audio_technical']['status'],'PASS — owner batch acceptance',x['audio_evidence']['owner_listening_status']] for x in items]))

causes=Counter((c['classification'],c['certainty']) for x in items for c in x['error_attribution'])
write('05_error_attribution.md','# Error attribution and correction priorities\n\n'+intro+'''
## Evidence standard

CONFIRMED: a saved query/decision or explicit gate establishes the issue. CONFIRMED_OBSERVATION: a visible defect or recorded pool condition, **not necessarily the sole root cause**. SUSPECTED: plausible cause from preliminary judgment. UNRESOLVED: missing alternative candidates/scores prevents discrimination. Query, retrieval and ranking can contribute together; do not sum category counts as mutually exclusive error rates.

'''+table([['Classification','Certainty','IDs (overlap allowed)'],['---']*3]+[[k[0],k[1],v] for k,v in sorted(causes.items())])+'''

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

'''+table([['ID','Attribution and evidence level','Basis'],['---']*3]+[[x['vocab_id'],'; '.join(c['classification']+' / '+c['certainty'] for c in x['error_attribution']),'; '.join(c['basis'] for c in x['error_attribution'])] for x in items]))

write('06_human_review_instructions.md','''# Human review package

Open `review_gallery.html` locally while keeping it inside the repository. All image/audio paths resolve to existing local files; no media is fetched from the Internet. No server/framework/model required. `gallery.js`, `gallery.css` and inline data are local. If file-origin storage is unavailable, keep the page open and Export JSON before closing. The matrix CSV/JSON is the fallback and authoritative machine-readable evidence.

1. Search by ID/word or filter AI query status. Each item shows EN/JP/VN, original Qwen query, actual query for the selected image, local image/audio, AI preliminary reasoning and metadata/hash/attribution details.
2. Enter reviewer identity. Review query and selected image independently using PASS / FAIL / NEEDS_REVIEW / UNKNOWN. No status is prefilled from AI. Owner acceptance already marks audio PASS; there is no required audio re-review control.
3. Add notes about intended sense, wrong scene/object, clutter/text, or missing evidence. For ambiguous terms, resolve context explicitly instead of assuming a single canonical meaning.
4. Drafts are saved in this browser under a run-specific key when available. Export JSON for handoff; it downloads a draft file locally and does not overwrite any source/old review. The owner must provide/export labels before they can become new evidence in a later task. Different browsers/file locations may have separate drafts.
5. Confirm exported query text/image/audio hashes still match this run before importing a future human review. This gallery does not itself approve production assets or rewrite ledgers/manifests. Inspect images even when AI says PASS.

The gallery is an academic local evaluation tool, not a public product. Do not publish restricted/unknown assets via this package. Rights inventory for all 100 items is not a quality gate; only actual public release assets require the release checks. Avoid moving the HTML out of its folder; use the CSV paths if relocating the repository.
''')

write('01_evaluation_summary.md','# A-001 first quality round — preliminary\n\n'+intro+'''
## Decision gate

**First evidence-based review package complete; final human-verified quality evaluation remains NEEDS_REVIEW.** B-002/Web Game work remains paused by the current user instruction. Audio has been accepted PASS for all 100 by the owner during this session and needs no further listening review. Main work is correcting selected images and the query/retrieval/ranking decisions feeding them.

'''+stat_table(['query_overall','query_correct_meaning','image_relevance','image_visual_quality','image_learning_suitability','audio_pronunciation_review','image_technical','audio_technical'])+'''

Each row uses N=100 vocabulary IDs; counts are also percentages of the total set. Query composite PASS requires all six checks; correct meaning alone is a different metric. Definitive P+F denominators are reported explicitly and exclude uncertain IDs. No UNKNOWN is counted as PASS. Image N=99 available files + 1 missing ID (038). Query/image labels are AI preliminary, **zero new independent human per-item query/image labels**. Audio 100/100 is a separate current owner batch acceptance, not an inferred consequence of MP3 existence.

## Answers for next decisions

1. **Qwen level:** original parsed query meaning: 75 PASS / 16 FAIL / 9 NEEDS_REVIEW; composite suitability: 37 / 22 / 41. This is not controlled model accuracy or proof of 100/100. Two original query mismatches (004/009) have approved target evidence; remaining linguistic judgments need owner review.
2. **Images:** relevance 44 PASS / 27 FAIL / 28 NEEDS_REVIEW / 1 UNKNOWN; learning suitability 27 / 55 / 17 / 1. Technical validation passes for 99 files, which does not make their content correct. Primary rice/chicken replacements differ from old production images; both versions retained in matrix evidence.
3. **Severe failures:** 035 shirt retrieves a nasal diagram; 041/042 time words become watches; 043/085/087 title matches; 051/065 action queries yield portraits; dense charts/preview text contaminate many outputs. See 03/05 reports and contact sheets.
4. **Change model?** Insufficient comparative evidence. Fix sense/visual intent and retrieval/acceptance first; preserve candidates/scores before diagnosing ranking. No proof a 4B model or Native runtime solves these failures.
5. **First corrections:** owner decides uncertain meanings/selected image labels; specify noun/action/time-aware queries; reject wrong titles, text-dominated previews and irrelevant one-candidate pools; retain complete evidence for later ranking tests. No changes made to pipeline.
6. **Next experiments:** frozen small failure/control set, fixed-input prompt comparison, then fixed-query retrieval and retained-candidate ranking comparison, only with separate execution authorization. No model/media/network run in this round.
7. **A-002 entry:** user requests it; consume this matrix and owner labels, confirm current asset hashes and choose diagnostic cases. Missing full candidate/score history must stay MISSING_EVIDENCE. A-002 can inspect known cases but cannot claim ranking root cause or rerun models/download without additional authorization. Do not auto-start A-002 or B-002.

## Evidence gaps and interpretation

- 94 accepted raw decoded query outputs missing; all 100 parsed queries verified against existing cache.
- Exact generation revisions for these historical 100 items missing. Original cache signature/correction prompt evidence is stored per ID, not replaced with a later benchmark revision.
- Full historical candidate list/bytes and complete SigLIP score ordering are missing for all 98 applicable search-selected primary assets. ID009 is a curated direct replacement (no comparative pool); ID038 was blocked before retrieval. 99 selected-image scores exist, including the curated score, but no score threshold is inferred. Counts identify the one-candidate cases, not every rejected alternative.
- ID038 selected image missing due an approved-image-intent gate, not a corrupted media file.
- No new agent audio listening; current owner acceptance governs all 100 audio. Historical listening records remain preserved for provenance.
- No independent human query/image labels collected by the agent. Gallery enables owner review and export. Quality is separate from rights/public eligibility; no full copyright audit performed.

## Outputs and verification

`evaluation_matrix.csv` / JSON: 100 IDs, full reconstruction and six query dimensions, image observations, audio evidence, hashes, historical labels, missing evidence and attribution. `02_semantic_assessment.md`, `03_image_assessment.md`, `04_audio_assessment.md`, `05_error_attribution.md`: per-ID judgments and denominators. `review_gallery.html` + local JS/CSS: owner package; `06_human_review_instructions.md`: use/export instructions. `owner_audio_acceptance.json`: current batch acceptance bound to 100 hashes. `statistics.json`, evidence/baseline hashes and authoring label table preserve provenance. `verification.md` records checks and browser results.
''')

data=json.dumps({'run_id':OUT.name,'items':items},ensure_ascii=False).replace('<','\\u003c')
write('review_gallery.html','''<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self' file:; media-src 'self' file:; style-src 'self'; script-src 'self'; connect-src 'none'; base-uri 'none'; form-action 'none'">
<title>A-001 · Local vocabulary review</title><link rel="stylesheet" href="gallery.css"></head><body>
<header><h1>A-001 · Review 100 vocabulary items</h1><p class="intro">Ảnh và query: AI preliminary, chưa phải human-verified ground truth. Audio: cả 100 đã được chủ dự án chấp nhận PASS; không cần review lại. Gallery chỉ đọc asset local và lưu bản nháp review, không gọi inference/API.</p>
<nav aria-label="Tài liệu"><a href="01_evaluation_summary.md">Báo cáo tổng hợp</a> · <a href="evaluation_matrix.csv">Matrix CSV</a> · <a href="06_human_review_instructions.md">Hướng dẫn</a></nav>
<div class="toolbar"><label>Tìm ID hoặc từ<input type="search" id="search" placeholder="vocab-000035, shirt, ねこ…"></label><label>AI query status<select id="filter"><option value="">Tất cả</option><option>PASS</option><option>FAIL</option><option>NEEDS_REVIEW</option><option>UNKNOWN</option></select></label><label>Tên reviewer<input id="reviewer" autocomplete="off"></label><button id="export" type="button">Export review JSON</button></div>
<p id="count" class="review-count" aria-live="polite"></p><p id="storage" class="status" role="status"></p></header>
<main id="items" aria-label="Vocabulary review items"></main><script type="application/json" id="review-data">'''+data+'''</script><script src="gallery.js"></script></body></html>''')

with (OUT/'human_review_template.csv').open('w',encoding='utf-8-sig',newline='') as f:
    fields=['vocab_id','query_text','image_sha256','audio_sha256','human_query','human_image','audio_owner_accepted','reviewer','reviewer_notes']
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for x in items:w.writerow(dict(zip(fields,[x['vocab_id'],x['parsed_qwen_query'],x['image_sha256'],x['audio_sha256'],'NOT_REVIEWED','NOT_REVIEWED','PASS','',''])))

print('Created six reports, human template, and offline gallery (100 items; no external fetch).')
