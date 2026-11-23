"""Render comparison_matrix.csv, review_gallery.html and evaluation_report.md (offline; no network/model)."""

import csv
import html
import json
from collections import Counter
from pathlib import Path

from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

# AI-preliminary desk review of thumbnails (agent), per item: selected-output preference + arm notes.
# Labels: NORMAL_BETTER / ICON_BETTER / BOTH_GOOD / BOTH_BAD. Not human decisions.
AI = {
    "vocab-000001": ("BOTH_GOOD", "Selected: red/green apples photo; clear.", "Selected: flat red-apple icon; clear. Pool risk: 4/6 icons are the Apple Inc. logo (brand ambiguity).", "pool_brand_collision"),
    "vocab-000011": ("BOTH_GOOD", "Selected: cat photo; clear.", "Selected: line-art cat face; clear. Pool: 4 candidates have alpha/fake checkerboard silhouettes.", "alpha_artifacts"),
    "vocab-000016": ("BOTH_GOOD", "Selected: alpine peaks over village (= A-001 image); clear.", "Selected: blue mountain pictogram; clear. Pool: ICON-ICONS watermarks on 05/07.", "watermark_in_pool"),
    "vocab-000021": ("ICON_BETTER", "Selected: house under construction; normal query 'house building' drifts to construction (query-sense defect, as in A-001).", "Selected: white house pictogram; clear. 03 flattened to a black square.", "normal_query_sense"),
    "vocab-000028": ("NORMAL_BETTER", "Selected: classic car in desert; clear.", "Selected: car icon with 'shutterstock' text watermark; 6/7 candidates flattened to black squares (transparent PNGs).", "alpha_black_squares"),
    "vocab-000031": ("ICON_BETTER", "Selected: 'BOOK OBJECT ART' exhibition poster, wrong referent; pool is book clip-art collections with alamy footers. Query 'book object' drifts.", "Selected: dark stacked-books icon (alpha flattened, dark); 03 open book and 06 book stack are clearer.", "normal_query_sense"),
    "vocab-000057": ("NORMAL_BETTER", "Selected: woman eating salad; clear action.", "All candidates show a music artist (name collision on 'eat icon'); semantically wrong.", "icon_semantic_failure"),
    "vocab-000059": ("ICON_BETTER", "Selected: 'Action' retail store (brand match); pool is action figures; wrong meaning.", "Selected: 'BUY' button with hand: answer-revealing text. Pool 01/02/05 shopping-cart icons are text-free and clear.", "icon_selected_text"),
    "vocab-000063": ("BOTH_BAD", "Selected: give-vs-receive flowchart (= A-001 image); text-heavy. Pool: worksheets/screenshots.", "Selected: 'Receive icons' web page with text, a ranking miss. Pool 01 (hand receiving box) and 07 (box between hands) are good.", "ranking_miss_icon_pool_good"),
    "vocab-000045": ("BOTH_GOOD", "Selected: 3D smiling emoji (= A-001 image); clear.", "Selected: laughing emoji on black (alpha flattened); clear. 01 has an ICON-ICONS watermark.", "alpha_artifacts"),
    "vocab-000046": ("ICON_BETTER", "Selected: 'Hunger vs Appetite' infographic (= A-001 image); text-dominant.", "Selected: drooling emoji thinking of a burger; text-free, clear. Pool: several person-thinking-of-food icons, some flattened to dark backgrounds.", "normal_text_heavy"),
    "vocab-000083": ("BOTH_BAD", "Selected: event poster with 'Sometimes' text; pool is text or grammar slides.", "Only 1 result: a visual-search web page screenshot; unusable.", "no_suitable_image"),
}


def alpha_flags(raw_path, image_path):
    with Image.open(ROOT / raw_path) as raw:
        alpha = "A" in raw.mode or "transparency" in raw.info
    with Image.open(ROOT / image_path) as jpg:
        mean = ImageStat.Stat(jpg.convert("L")).mean[0]
    return alpha, alpha and mean < 12


def main():
    with (HERE / "frozen_sample.csv").open(encoding="utf-8-sig", newline="") as file:
        sample = list(csv.DictReader(file))
    pairs = {(p["vocab_id"], p["arm"]): p for p in json.loads((HERE / "retrieval_results.json").read_text(encoding="utf-8"))["pairs"]}
    for p in pairs.values():
        for c in p["candidates"]:
            c["alpha"], c["black"] = alpha_flags(c["raw_path"], c["image_path"]) if c["image_path"] else (False, False)

    def selected(p):
        return next((c for c in p["candidates"] if c["candidate_id"] == p["selected_candidate_id"]), {})

    def f(x):
        return "" if x is None else f"{x:.3f}"

    rows = []
    for s in sample:
        n, i = pairs[(s["vocab_id"], "NORMAL")], pairs[(s["vocab_id"], "ICON")]
        sn, si = selected(n), selected(i)
        pref, nn, ni, tag = AI[s["vocab_id"]]
        row = {k: s[k] for k in ("vocab_id", "category", "english", "japanese", "vietnamese", "normal_query", "icon_query")}
        for arm, p, sel in (("normal", n, sn), ("icon", i, si)):
            row.update({f"{arm}_search": p["search_status"], f"{arm}_downloaded": sum(c["status"] == "DOWNLOADED" for c in p["candidates"]),
                        f"{arm}_candidates": len(p["candidates"]), f"{arm}_ranking": p["ranking_status"],
                        f"{arm}_search_s": f(p["search_seconds"]), f"{arm}_download_s": f(p["download_seconds"]),
                        f"{arm}_failures": "; ".join(c["error"] for c in p["candidates"] if c["error"]),
                        f"{arm}_alpha_flattened": sum(c["alpha"] for c in p["candidates"]),
                        f"{arm}_black_squares": sum(c["black"] for c in p["candidates"]),
                        f"{arm}_selected": sel.get("candidate_id", ""), f"{arm}_selected_sha256": sel.get("image_sha256", ""),
                        f"{arm}_selected_query_score": f(sel.get("query_score")), f"{arm}_selected_shared_score": f(sel.get("shared_score")),
                        f"{arm}_best_shared_score": f(max((c["shared_score"] for c in p["candidates"] if c["shared_score"] is not None), default=None))})
        row.update({"a001_image": s["a001_image_path"], "a001_learning": s["a001_image_learning"],
                    "ai_preliminary_preference": pref, "ai_issue_tag": tag, "ai_normal_note": nn, "ai_icon_note": ni,
                    "human_preference": "NOT_REVIEWED", "human_no_suitable_normal": "", "human_no_suitable_icon": "", "human_notes": ""})
        rows.append(row)
    with (HERE / "comparison_matrix.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    # ---------- gallery ----------
    def img(path, alt, h):
        return f'<img src="../../../{html.escape(path, quote=True)}" alt="{html.escape(alt, quote=True)}" style="height:{h}px" loading="lazy">' if path else '<p class="missing">Không có ảnh</p>'

    def pool(p):
        out = []
        for c in p["candidates"]:
            flags = (" · <b>ALPHA→ĐEN</b>" if c["black"] else " · alpha" if c["alpha"] else "") + (" · ✔chọn" if c["candidate_id"] == p["selected_candidate_id"] else "")
            src = f'<a href="{html.escape(c["source_url"], quote=True)}" target="_blank" rel="noreferrer">nguồn</a>' if c.get("source_url") else ""
            out.append(f'<figure>{img(c.get("image_path"), c["candidate_id"], 120)}<figcaption><b>{c["candidate_id"][-8:]}</b> {html.escape(c["status"])}{flags}<br>query {f(c["query_score"]) or "–"} · từ {f(c["shared_score"]) or "–"}<br>{html.escape((c.get("title") or "")[:80])} {src} {html.escape(c.get("error") or "")}</figcaption></figure>')
        return "".join(out)

    cards = []
    for s, r in zip(sample, rows):
        n, i = pairs[(s["vocab_id"], "NORMAL")], pairs[(s["vocab_id"], "ICON")]
        vid = s["vocab_id"]
        arm_html = ""
        for label, cls, p, prefix in (("A · NORMAL", "normal", n, "normal"), ("B · ICON", "icon", i, "icon")):
            sel = selected(p)
            arm_html += f'''<section class="arm {cls}"><h3>{label}</h3><p class="q">{html.escape(p["query"])}</p>{img(sel.get("image_path"), label, 240)}
<small>{p["search_status"]} · tải {r[prefix + "_downloaded"]}/{r[prefix + "_candidates"]} · {p["ranking_status"]} · chọn {html.escape(sel.get("candidate_id", "-")[-8:])}<br>SigLIP(query) {r[prefix + "_selected_query_score"] or "–"} · SigLIP(từ) {r[prefix + "_selected_shared_score"] or "–"} · alpha {r[prefix + "_alpha_flattened"]}, đen {r[prefix + "_black_squares"]}</small>
<p class="ai">AI sơ bộ: {html.escape(r["ai_" + prefix + "_note"])}</p>
<label class="ns"><input type="checkbox" data-id="{vid}" data-field="no_suitable_{prefix}"> NO_SUITABLE_IMAGE cho nhánh này</label></section>'''
        cards.append(f'''<article id="{vid}"><h2>{vid} · {html.escape(s["english"])} · {html.escape(s["japanese"])} · {html.escape(s["vietnamese"])} <span class="cat">{s["category"]}</span></h2>
<div class="pair">{arm_html}</div>
<p class="ai">AI sơ bộ (kết quả được chọn): <b>{r["ai_preliminary_preference"]}</b> · {r["ai_issue_tag"]} · A-001 learning: {r["a001_learning"]}</p>
<details><summary>Ảnh A-001 và toàn bộ ứng viên</summary><div class="ref">A-001 hiện tại: {img(s["a001_image_path"], "A-001", 120)}</div><h4>NORMAL</h4><div class="cands">{pool(n)}</div><h4>ICON</h4><div class="cands">{pool(i)}</div></details>
<div class="review"><label>Đánh giá A/B <select data-id="{vid}" data-field="preference"><option>NOT_REVIEWED</option><option>NORMAL_BETTER</option><option>ICON_BETTER</option><option>BOTH_GOOD</option><option>BOTH_BAD</option><option>NEEDS_REVIEW</option></select></label>
<label>Ghi chú <textarea data-id="{vid}" data-field="notes"></textarea></label></div></article>''')
    meta = {"experiment_id": "A003_CONDITIONAL_SEARCH", "items": [{"vocab_id": r["vocab_id"], "category": r["category"],
            "normal_query": r["normal_query"], "icon_query": r["icon_query"], "normal_selected": r["normal_selected"],
            "normal_selected_sha256": r["normal_selected_sha256"], "icon_selected": r["icon_selected"],
            "icon_selected_sha256": r["icon_selected_sha256"]} for r in rows]}
    page = f'''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self' file:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'">
<title>A-003 Conditional Review</title><style>
:root{{--bg:#f6f8fa;--card:#fff;--fg:#182433;--line:#d3dce4;--muted:#5a6878;--ai:#7a4b00;--n:#1f6feb;--i:#8250df}}
@media (prefers-color-scheme:dark){{:root{{--bg:#11161c;--card:#1a2129;--fg:#e4e9ee;--line:#34404c;--muted:#9aa7b4;--ai:#f0c46a;--n:#58a6ff;--i:#bc8cff}}}}
body{{font:16px/1.5 system-ui,sans-serif;max-width:1240px;margin:auto;padding:1rem;color:var(--fg);background:var(--bg)}}
article{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:1rem;margin:1rem 0}}
.pair{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}} .arm{{min-width:0;border:2px solid var(--line);border-radius:6px;padding:.6rem}}
.arm.normal{{border-color:var(--n)}} .arm.icon{{border-color:var(--i)}} .arm.normal h3{{color:var(--n)}} .arm.icon h3{{color:var(--i)}}
.arm img{{width:100%;object-fit:contain;background:#ddd}} .q{{font-family:monospace;margin:.2rem 0}} .cat{{font-size:.75rem;border:1px solid var(--line);padding:.1rem .4rem;border-radius:4px}}
small,figcaption{{display:block;color:var(--muted);overflow-wrap:anywhere}} .ai{{color:var(--ai);font-size:.88rem}}
.cands{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:.5rem}} figure{{margin:0;border:1px solid var(--line);padding:.3rem}}
.cands img,.ref img{{width:100%;object-fit:contain;background:#ddd}} figcaption{{font-size:.76rem}} a{{color:inherit}}
.review{{display:grid;gap:.5rem;margin-top:.8rem}} .review select,.review textarea{{display:block;width:100%;max-width:520px}} textarea{{min-height:4rem}}
.missing{{height:240px;display:grid;place-items:center}} .top{{position:sticky;top:0;background:var(--bg);padding:.5rem 0;z-index:1}}
@media(max-width:700px){{.pair{{grid-template-columns:1fr}}}}
</style>
<h1>A-003 · Normal vs Icon (holdout 12)</h1>
<p>Công cụ review nội bộ; không phải Game UI. <b style="color:var(--n)">A · NORMAL</b> = query Qwen hiện có (cache). <b style="color:var(--i)">B · ICON</b> = <code>&lt;english&gt; icon</code>. Cùng nhà cung cấp, giới hạn 7 ứng viên, timeout/retry. Nhận xét AI chỉ là sơ bộ. "ALPHA→ĐEN" = PNG trong suốt bị bước chuẩn hoá hiện tại chuyển thành nền đen.</p>
<div class="top"><label>Reviewer <input id="reviewer" autocomplete="name"></label> <button id="export">Export JSON</button> <small>Nháp lưu trong trình duyệt; bấm Export để bàn giao file.</small></div>
{"".join(cards)}
<script type="application/json" id="review-meta">{json.dumps(meta, ensure_ascii=False).replace("</", "<\\/")}</script>
<script>
const meta=JSON.parse(document.getElementById('review-meta').textContent),key='A003_CONDITIONAL_SEARCH_review';
let draft={{}};try{{draft=JSON.parse(localStorage.getItem(key)||'{{}}')}}catch{{}}
document.querySelectorAll('[data-id]').forEach(el=>{{const id=el.dataset.id,f=el.dataset.field,cb=el.type==='checkbox';
 if(draft[id]&&f in draft[id]){{cb?el.checked=!!draft[id][f]:el.value=draft[id][f]}}
 el.addEventListener(cb?'change':'input',()=>{{draft[id]??={{}};draft[id][f]=cb?el.checked:el.value;try{{localStorage.setItem(key,JSON.stringify(draft))}}catch{{}}}})}});
document.getElementById('export').addEventListener('click',()=>{{const reviewer=document.getElementById('reviewer').value.trim();if(!reviewer){{alert('Nhập tên reviewer');return}}
 const out={{...meta,kind:'HUMAN_REVIEW_DRAFT_NOT_AUTO_APPROVAL',reviewer,exported_at:new Date().toISOString(),reviews:draft}};
 const a=document.createElement('a'),u=URL.createObjectURL(new Blob([JSON.stringify(out,null,2)],{{type:'application/json'}}));a.href=u;a.download='A003-conditional-review.json';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),1000)}});
</script></html>'''
    (HERE / "review_gallery.html").write_text(page, encoding="utf-8")

    # ---------- report ----------
    by_cat = {}
    for r in rows:
        group = "CONCRETE" if r["category"] == "CONCRETE" else "DIFFICULT"
        by_cat.setdefault(group, Counter())[r["ai_preliminary_preference"]] += 1
    tech = {arm: {"searches": sum(r[f"{arm}_search"] == "SUCCESS" for r in rows),
                  "cands": sum(r[f"{arm}_candidates"] for r in rows), "dl": sum(r[f"{arm}_downloaded"] for r in rows),
                  "alpha": sum(r[f"{arm}_alpha_flattened"] for r in rows), "black": sum(r[f"{arm}_black_squares"] for r in rows),
                  "ranked": sum(r[f"{arm}_ranking"] == "SCORED" for r in rows),
                  "search_s": sum(float(r[f"{arm}_search_s"] or 0) for r in rows) / len(rows),
                  "download_s": sum(float(r[f"{arm}_download_s"] or 0) for r in rows) / len(rows)} for arm in ("normal", "icon")}
    shared_wins = sum(float(r["icon_selected_shared_score"] or -99) > float(r["normal_selected_shared_score"] or -99) for r in rows)
    table = "".join(f"| {r['vocab_id'][-3:]} | {r['english']} | {r['category']} | `{r['normal_query']}` | {r['normal_downloaded']}/{r['normal_candidates']} | {r['normal_selected'][-9:]} | {r['normal_selected_shared_score']} | {r['icon_downloaded']}/{r['icon_candidates']} (đen {r['icon_black_squares']}) | {r['icon_selected'][-7:]} | {r['icon_selected_shared_score']} | **{r['ai_preliminary_preference']}** | {r['ai_issue_tag']} |\n" for r in rows)
    notes = "".join(f"- **{r['english']}**: Normal: {r['ai_normal_note']} Icon: {r['ai_icon_note']}\n" for r in rows)
    m = json.loads((HERE / "experiment_manifest.json").read_text(encoding="utf-8"))
    report = f'''# A-003 — Controlled evaluation of conditional image search

Status: **automated stages complete; human review pending (0/12).** Internal experiment. Production pipeline, Qwen prompts, routing, registry, `data/` and `unified_dataset_v1.json` (hash `644c2dc9…`) are unchanged. Game UX/UI remains undecided. Decisions D-015/D-016 ("because" V3-01 internal-only via an override file) are preserved and not reopened.

## Design

- **Holdout**: 12 IDs frozen in `frozen_sample.csv` before any request (git HEAD `{m["git_head"][:12]}`, sample SHA-256 in the manifest), with no substitution.
  - 6 CONCRETE: apple, cat, mountain, house, car, book.
  - 3 DIFFICULT_ACTION: eat, buy, receive.
  - 3 DIFFICULT_ABSTRACT: happy, hungry, sometimes.
  - Excluded: the 20 icon-pilot IDs, the causal ID 081, 086 *why* (its baseline query is already "why icon", which would confound the arms) and 038 *friend* (no baseline query).
  - The sample is chosen, not random: it covers the task's named examples and spans semantic groups and A-001 outcomes (PASS and FAIL). It is not the earlier pilot.
- **Arms**:
  - A NORMAL = the A-001 `effective_image_query` (cached Qwen output; Qwen not called).
  - B ICON = `<english> icon`.
  - Arm order alternates per item (NORMAL first on odd positions) to spread time effects.
- **Identical settings for both arms**: DuckDuckGo `wt-wt`, moderate safesearch, 7 results; production defaults of timeout 20 s, search retries 2, download retries 2, retry delay 2 s; 2 s pause.
- **Scoring**:
  - SigLIP `google/siglip2-so400m-patch16-384` with the unchanged `score_batch`.
  - **Query score**: each arm is scored against its own query (production rule) and the top score is selected.
  - **Shared score**: both arms are scored against the bare English word. This is a cross-arm yardstick only.

## Technical results

| Metric | NORMAL | ICON |
|---|---|---|
| Search success | {tech["normal"]["searches"]}/12 | {tech["icon"]["searches"]}/12 |
| Candidates / downloaded | {tech["normal"]["cands"]} / {tech["normal"]["dl"]} | {tech["icon"]["cands"]} / {tech["icon"]["dl"]} |
| Ranked (SigLIP) | {tech["normal"]["ranked"]}/12 | {tech["icon"]["ranked"]}/12 |
| Transparent (alpha) downloads | {tech["normal"]["alpha"]} | {tech["icon"]["alpha"]} |
| Flattened to a black square | {tech["normal"]["black"]} | {tech["icon"]["black"]} |
| Mean search / download time per arm (s) | {tech["normal"]["search_s"]:.2f} / {tech["normal"]["download_s"]:.2f} | {tech["icon"]["search_s"]:.2f} / {tech["icon"]["download_s"]:.2f} |

There were no search failures, timeouts or rate limits. Download failures (HTTP 402/403/404, non-image payloads) are listed per arm in `comparison_matrix.csv`. *sometimes icon* returned only 1 result.

**Technical defect found, affecting the icon strategy.** `imagecollector.normalize_image_to_jpeg` and `SiglipImageScorer.score_batch` call `.convert("RGB")` on transparent PNG/WebP images without compositing them onto a background, so transparent areas become black.
- Icon results are much more often transparent: ICON {tech["icon"]["alpha"]} vs NORMAL {tech["normal"]["alpha"]} candidates in this run.
- Here, 8 ICON candidates became solid black squares, 6 of 7 for *car icon*.
- SigLIP also ranks these blacked-out versions.
- In the earlier A002_ICON_PILOT_20, 61 of 129 candidates and **10 of 20 selected icons** had transparency flattened. Their black backgrounds come from this defect, not from the source images.

## Per-item comparison (AI preliminary; human 0/12)

| ID | Word | Category | Normal query | N dl | N selected | N shared | I dl | I selected | I shared | AI preference | Issue |
|---|---|---|---|---|---|---|---|---|---|---|---|
{table}
AI preliminary tally of the selected outputs:
- CONCRETE: {dict(by_cat.get("CONCRETE", {}))}
- DIFFICULT: {dict(by_cat.get("DIFFICULT", {}))}

The ICON selection had the higher shared-word SigLIP score in {shared_wins}/12 items. That is not quality evidence: SigLIP rewards printed words and logos, and both arms were scored against the bare word.

{notes}
## Decision gate (preliminary; 12 items, AI desk review, no human labels)

1. **Does "icon" improve difficult words on this sample?** It helped buy and hungry (the selected or pool images are clearly better). It hurt *eat* (name collision returned a musician). Receive had a good icon pool but a text page was selected. Neither arm worked for *sometimes*; happy was good in both. The result is **mixed, not a general improvement**: 2 better, 1 worse, 1 tie, 2 both bad out of 6.
2. **Does it harm simple concrete words?** Sometimes.
   - Car: the icon selection carries a shutterstock watermark, and 6/7 candidates were black squares.
   - Apple: the icon pool is dominated by the Apple Inc. logo, though the selected icon is fine.
   - Cat and mountain were fine in both arms.
   - House and book were *better* as icons, but only because their Qwen normal queries ("house building", "book object") drift. That is a query-sense problem, not evidence for icons.
3. **Which categories benefit?** Depictable actions, states and objects whose normal query returns infographics, brand pages or the wrong sense: buy, hungry, (receive pool), house, book. This matches the A-002 pilot pattern for motion verbs and weather.
4. **Which remain unresolved?**
   - Frequency and time adverbs (*sometimes*; *always/today/tomorrow* earlier relied on printed text).
   - Logical connectors (*because*: curated internal image only).
   - Words whose "<word> icon" collides with a name or brand (*eat*, *apple*).
5. **Is a conditional strategy justified?** **Partly, as a candidate source rather than a fixed routing rule.** A single word-category switch is not supported, because icon results also failed on an action (eat) and hurt a concrete noun (car). What the evidence supports better: generate **both pools** for non-concrete or low-confidence items, then reject bad candidates and let a person choose, rather than rely on SigLIP's top score.
6. **What evidence is missing?**
   - Human A/B labels for these 12 (and per-item labels for the 20-word pilot; the owner's feedback was qualitative).
   - A larger randomized sample per category.
   - Results after the alpha fix, since 10 of 20 pilot icons and several A-003 icons were scored and shown with black backgrounds.
   - Inter-rater agreement.
   - Rights for icon sources (ICON-ICONS, shutterstock, alamy marks).
   - Any measure of text or answer leakage.
7. **Minimal production changes that would be needed (proposal, not implemented)**:
   - (a) Composite RGBA/LA/P-with-transparency images onto white before `.convert("RGB")`, in both `normalize_image_to_jpeg` and `score_batch`, with a unit test using a transparent PNG.
   - (b) An optional second query arm, `<english> icon`, behind an explicit per-item flag or list. Never a default for all words; the normal arm is kept.
   - (c) Record both pools and a `NO_SUITABLE_IMAGE` outcome in metadata instead of always selecting a top score.
   - (d) A small manual-curation override path (the D-016 override file is a working precedent).
   - Qwen prompts and routing would not change.
8. **Proceed to integration or revise?** **Revise first; do not integrate yet.** Recommended order: alpha fix (low risk, clear defect) → owner reviews these 12 pairs → decide whether to adopt the dual-pool, human-in-the-loop approach for flagged words.

## Proposed `NO_SUITABLE_IMAGE` outcome (documentation only)

Reject a candidate when any of these hold; return `NO_SUITABLE_IMAGE` when no candidate in any arm survives:

1. **Semantic**: wrong referent or sense (brand or name collision, e.g. *eat icon* musician, Apple logo, "Action" store; construction for *house*).
2. **Text or answer leakage**: the target word or its translation is printed prominently, or text is the main content (BUY button, grammar slides, infographics, posters).
3. **Watermark or stock overlay** covering the subject (shutterstock, alamy, ICON-ICONS, Adobe Stock). This is flagged separately from rights.
4. **Technically invalid**: non-image payload, too small, mostly uniform or near-black after normalization, fake checkerboard "transparency".
5. **Ambiguity or learning unsuitability**: abstract notation (∴/∵), unrelated collage, or a scene that teaches a different word (*rain/umbrella* for "because").

Fallback order (proposal):
- Normal pool → icon pool (flagged words only) → manual curation or override file → leave the image **missing** with reason `NO_SUITABLE_IMAGE`.
- Never force the top SigLIP score.
- SigLIP can pre-sort, and automated checks can handle 4 (uniform or black detection) and part of 3. Rules 1, 2 and 5 need either an OCR/text detector (not present today) or human review.
- `dataset_builder` already supports `status: missing`, so this outcome needs no schema change for the record. Only the metadata reason field is new.

## Recommended conditional strategy (proposal)

| Category | Proposal | Evidence level |
|---|---|---|
| A — Concrete nouns | Keep the normal Qwen query. Fix query-sense drift (house, book) through `semantic_decisions` overrides, not icons. | Weak–moderate (6 items; owner's earlier qualitative OK) |
| B — Depictable actions/states | Fetch the normal and icon pools; a person picks, with rejection rules applied. Do not auto-select the icon top score. | Weak (pilot 20 qualitative + A-003 3 of 6 positive) |
| C — Abstract, time and connector words | Manual curation or override, a contextual or multi-panel image, or `NO_SUITABLE_IMAGE`. Do not generalize the "because" approach without per-word evidence. | Weak (because + sometimes) |

**Limitations**: 12 items chosen rather than randomly sampled, a single run, one provider, search results that drift over time, AI desk review only, black-flattened icons, and no rights review. No general effectiveness claim.

## Files

`experiment_manifest.json`, `frozen_sample.csv`, `retrieval_results.json`, `comparison_matrix.csv`, `review_gallery.html`, `images/<vocab_id>/<NORMAL|ICON>/NN.{{img,jpg}}`, `run_a003.py`, `render_a003.py`.
'''
    (HERE / "evaluation_report.md").write_text(report, encoding="utf-8")
    print("rendered", len(rows), {k: dict(v) for k, v in by_cat.items()}, tech)


if __name__ == "__main__":
    main()
