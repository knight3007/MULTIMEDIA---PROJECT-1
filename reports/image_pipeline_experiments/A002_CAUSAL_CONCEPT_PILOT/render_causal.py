"""Render comparison.csv, review_gallery.html and experiment_report.md from saved results (no network/model)."""

import csv
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "reports/phase0_quality_review/a001_20261122/evaluation_matrix.json"
ICON_RESULTS = ROOT / "reports/image_pipeline_experiments/A002_ICON_PILOT_20/retrieval_results.json"
VOCAB_ID = "vocab-000081"

# AI-preliminary desk observations (agent viewed thumbnails); NOT human decisions.
AI_NOTES = {
    "ORIGINAL": "Grammar slide 'Because Sentence' with example sentences; dominant English text; not text-independent.",
    "ICON": "Selected 81-01 is an abstract three-node graph shaped like the ∴ (therefore) sign; 81-02..05 are ∴/∵ dot symbols (mathematical notation, and ∴ is the opposite connective). 81-06/07 show a person with a question mark beside rain: closest to a reason, but ambiguous (07 has an alamy watermark).",
    "V1": "All pool members are business fishbone or labelled diagrams; selected V1-05 is a 'CAUSE & EFFECT DIAGRAM' text sign. Text-dominant and abstract; poor for learners.",
    "V2": "Selected V2-05 is a 'REASON / RESULT' letter-tile crossword (pure English text). Pool member V2-01 (same file as V3-01) is the strongest conceptual image: rain cloud + sun → arrow → tree, but labelled CAUSE/EFFECT and carrying a vertical Adobe Stock watermark.",
    "V3": "Selected V3-01 is the same image as V2-01: a concrete cause→effect scene (rain and sun make a tree grow) with an arrow, but printed labels and a watermark. Other pool members are fishbone templates, flow charts and a text-heavy anchor chart.",
    "V4": "Text-free child illustrations: rain + umbrella (selected V4-03 girl with umbrella; V4-02 boy with red umbrella has no visible watermark). The cause (rain) and the response (umbrella) are both present, but the link is implicit: a learner may read it as 'rain' or 'umbrella', not 'because'. V4-01/06 have watermarks; V4-05 has a dreamstime footer.",
}
AUTOMATED_VERDICT = "NO_SUITABLE_VISUAL_FOUND (AI preliminary): no candidate is simultaneously text-free, watermark-free and explicit about the because-relation. Closest: V2-01/V3-01 (explicit causality, but text and watermark) and V4-02/V4-03 (text-free, but implicit causality)."


def main():
    item = next(x for x in json.loads(SOURCE.read_text(encoding="utf-8"))["items"] if x["vocab_id"] == VOCAB_ID)
    icon = next(x for x in json.loads(ICON_RESULTS.read_text(encoding="utf-8"))["items"] if x["vocab_id"] == VOCAB_ID)
    results = json.loads((HERE / "retrieval_results.json").read_text(encoding="utf-8"))
    ref = results.get("reference_fixed_scores") or {"scores": {}, "text": ""}
    icon_candidates = [dict(c, siglip_query_score=c.get("siglip_score"), siglip_fixed_score=ref["scores"].get(c["candidate_id"]))
                       for c in icon["candidates"]]
    options = [
        {"option": "ORIGINAL", "query": item["parsed_qwen_query"], "search_status": "REFERENCE (A-001, not re-searched)",
         "candidates": [], "selected": {"candidate_id": "ORIGINAL", "image_path": item["image_path"],
            "image_sha256": item["image_sha256"], "siglip_query_score": None,
            "siglip_fixed_score": ref["scores"].get("ORIGINAL"), "source_url": None}},
        {"option": "ICON", "query": "because icon", "search_status": "REFERENCE (A002_ICON_PILOT_20, not re-searched)",
         "candidates": icon_candidates,
         "selected": next(c for c in icon_candidates if c["candidate_id"] == icon["selected_candidate_id"])},
    ]
    for v in results["variants"]:
        options.append({"option": v["variant"], "query": v["query"], "search_status": v["search_status"],
                        "candidates": v["candidates"], "ranking_status": v["ranking_status"],
                        "selected": next((c for c in v["candidates"] if c["candidate_id"] == v["selected_candidate_id"]), {})})

    def fmt(x):
        return "NOT_RUN" if x is None else f"{x:.3f}"

    rows = []
    for o in options:
        s, cands = o["selected"], o["candidates"]
        rows.append({"option": o["option"], "vocab_id": VOCAB_ID, "query": o["query"], "search_status": o["search_status"],
            "candidate_count": len(cands), "downloaded_count": sum(c["status"] == "DOWNLOADED" for c in cands),
            "selected_candidate_id": s.get("candidate_id", ""), "selected_image": s.get("image_path", ""),
            "selected_image_sha256": s.get("image_sha256", ""), "siglip_query_score": fmt(s.get("siglip_query_score")),
            "siglip_fixed_text_score": fmt(s.get("siglip_fixed_score")),
            "best_fixed_text_candidate": max((c for c in cands if c.get("siglip_fixed_score") is not None),
                                             key=lambda c: c["siglip_fixed_score"], default={}).get("candidate_id", ""),
            "ai_preliminary_note": AI_NOTES[o["option"]], "human_choice": "NOT_REVIEWED", "reviewer_notes": ""})
    decision_path = HERE / "owner_review_decision.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8")) if decision_path.exists() else None
    if decision:
        for r in rows:
            if r["option"] + "_BEST" == decision["choice"]:
                r["human_choice"] = f"{decision['choice']} ({decision['candidate_id']}, {decision['kind']})"
    with (HERE / "comparison.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    def img(path, alt, h=260):
        return (f'<img src="../../../{html.escape(path, quote=True)}" alt="{html.escape(alt, quote=True)}" style="height:{h}px">'
                if path else '<p class="missing">Không có ảnh</p>')

    tops = "".join(f'''<section class="opt"><h3>{o["option"]}</h3><p class="q">{html.escape(o["query"])}</p>{img(o["selected"].get("image_path"), o["option"])}
<small>Chọn: {html.escape(o["selected"].get("candidate_id", "-"))} · SigLIP(query) {fmt(o["selected"].get("siglip_query_score"))} · SigLIP(cố định) {fmt(o["selected"].get("siglip_fixed_score"))}<br>{html.escape(o["search_status"])}</small>
<p class="ai">AI sơ bộ: {html.escape(AI_NOTES[o["option"]])}</p></section>''' for o in options)
    pools = []
    for o in options:
        if not o["candidates"]:
            continue
        figs = "".join(f'''<figure>{img(c.get("image_path"), c["candidate_id"], 140)}<figcaption><b>{html.escape(c["candidate_id"])}</b> · {html.escape(c["status"])}{" (dup " + html.escape(c["duplicate_of"]) + ")" if c.get("duplicate_of") else ""}<br>query {fmt(c.get("siglip_query_score"))} · cố định {fmt(c.get("siglip_fixed_score"))}<br>{html.escape(c.get("title") or "")}<br>{('<a href="' + html.escape(c["source_url"], quote=True) + '" rel="noreferrer" target="_blank">nguồn</a>') if c.get("source_url") else ""} {html.escape(c.get("error") or "")}</figcaption></figure>''' for c in o["candidates"])
        pools.append(f'<details><summary>{o["option"]} · ứng viên ({len(o["candidates"])}) · <code>{html.escape(o["query"])}</code></summary><div class="cands">{figs}</div></details>')
    choices = ["ORIGINAL_BEST", "ICON_BEST", "V1_BEST", "V2_BEST", "V3_BEST", "V4_BEST", "NONE_SUITABLE"]
    meta = {"experiment_id": "A002_CAUSAL_CONCEPT_PILOT", "vocab_id": VOCAB_ID, "fixed_text": ref["text"],
            "options": [{"option": r["option"], "query": r["query"], "selected_candidate_id": r["selected_candidate_id"],
                         "selected_image_sha256": r["selected_image_sha256"]} for r in rows]}
    page = f'''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self' file:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'">
<title>Because Causal Review</title><style>
:root{{--bg:#f6f8fa;--card:#fff;--fg:#182433;--line:#d3dce4;--muted:#5a6878;--ai:#7a4b00}}
@media (prefers-color-scheme:dark){{:root{{--bg:#11161c;--card:#1a2129;--fg:#e4e9ee;--line:#34404c;--muted:#9aa7b4;--ai:#f0c46a}}}}
body{{font:16px/1.5 system-ui,sans-serif;max-width:1240px;margin:auto;padding:1rem;color:var(--fg);background:var(--bg)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:.8rem}}
.opt,details,.review{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:.7rem;min-width:0}}
.opt img,.cands img{{width:100%;object-fit:contain;background:#eee}} .opt h3{{margin:.1rem 0}} .q{{font-family:monospace;margin:.2rem 0}}
small,.ai,figcaption{{display:block;overflow-wrap:anywhere;color:var(--muted)}} .ai{{color:var(--ai);font-size:.85rem}}
details{{margin:.6rem 0}} .cands{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:.5rem;margin-top:.5rem}}
figure{{margin:0;border:1px solid var(--line);padding:.3rem}} figcaption{{font-size:.78rem}} a{{color:inherit}}
.review{{margin:1rem 0;display:grid;gap:.6rem}} .review label{{display:block}} textarea{{width:100%;max-width:640px;min-height:5rem}}
.verdict{{border-left:4px solid var(--ai);padding:.4rem .7rem;background:var(--card)}} .missing{{height:260px;display:grid;place-items:center}}
</style>
<h1>vocab-000081 · because · なぜなら · bởi vì</h1>
<p>Công cụ review nội bộ cho A002_CAUSAL_CONCEPT_PILOT; không phải Game UI. Không biến thể nào được tự động phê duyệt. Điểm SigLIP theo query không so sánh được giữa các query khác nhau; điểm "cố định" dùng chung câu mô tả: <i>{html.escape(ref["text"])}</i>.</p>
<p class="verdict">{html.escape(AUTOMATED_VERDICT)}</p>
<p>Tiêu chí: thể hiện quan hệ nhân quả · khớp nghĩa "because" (lý do được nêu cho một kết quả, không phải "therefore") · rõ ràng · hữu ích cho học · không phụ thuộc chữ · ít mơ hồ · ít rối nền · phù hợp làm media học từ.</p>
<div class="grid">{tops}</div>
<h2>Ứng viên và nguồn</h2>{"".join(pools)}
<div class="review"><b>Quyết định của reviewer</b>
<label>Reviewer <input id="reviewer" autocomplete="name"></label>
<label>Lựa chọn <select id="choice"><option>NOT_REVIEWED</option>{"".join(f"<option>{c}</option>" for c in choices)}</select></label>
<label>Ứng viên cụ thể (tuỳ chọn, ví dụ V2-01) <input id="candidate"></label>
<label>Ghi chú <textarea id="notes"></textarea></label>
<button id="export">Export JSON</button><small>Nháp lưu trong trình duyệt này; hãy Export JSON để bàn giao.</small></div>
<script type="application/json" id="review-meta">{json.dumps(meta, ensure_ascii=False).replace("</", "<\\/")}</script>
<script>
const meta=JSON.parse(document.getElementById('review-meta').textContent),key='A002_CAUSAL_CONCEPT_PILOT_review',ids=['reviewer','choice','candidate','notes'];
let draft={{}};try{{draft=JSON.parse(localStorage.getItem(key)||'{{}}')}}catch{{}}
ids.forEach(id=>{{const el=document.getElementById(id);if(draft[id])el.value=draft[id];el.addEventListener('input',()=>{{draft[id]=el.value;try{{localStorage.setItem(key,JSON.stringify(draft))}}catch{{}}}})}});
document.getElementById('export').addEventListener('click',()=>{{const v=Object.fromEntries(ids.map(id=>[id,document.getElementById(id).value.trim()]));
if(!v.reviewer){{alert('Nhập tên reviewer');return}} if(v.choice==='NOT_REVIEWED'){{alert('Chọn một lựa chọn');return}}
const out={{...meta,kind:'HUMAN_REVIEW_DRAFT_NOT_AUTO_APPROVAL',exported_at:new Date().toISOString(),reviewer:v.reviewer,choice:v.choice,candidate_id:v.candidate||null,notes:v.notes}};
const a=document.createElement('a'),u=URL.createObjectURL(new Blob([JSON.stringify(out,null,2)],{{type:'application/json'}}));a.href=u;a.download='A002-causal-because-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)}});
</script></html>'''
    (HERE / "review_gallery.html").write_text(page, encoding="utf-8")

    var_rows = "".join(f"| {r['option']} | `{r['query']}` | {r['search_status']} | {r['downloaded_count']}/{r['candidate_count']} | {r['selected_candidate_id']} | {r['siglip_query_score']} | {r['siglip_fixed_text_score']} | {r['best_fixed_text_candidate'] or '-'} |\n" for r in rows)
    fails = "; ".join(f"{c['candidate_id']} ({c['error']})" for v in results["variants"] for c in v["candidates"] if c["status"] != "DOWNLOADED") or "none"
    dups = "; ".join(f"{c['candidate_id']} = {c['duplicate_of']}" for v in results["variants"] for c in v["candidates"] if c.get("duplicate_of")) or "none"
    owner = (f'''## Owner decision

- **{decision["choice"]}: candidate `{decision["candidate_id"]}`** (same image as `{decision["duplicate_of"]}`). Recorded {decision["recorded_at_utc"]} from the owner's chat message "{decision["owner_statement"]}". No gallery export file exists (see `owner_review_decision.json` for why).
- Image SHA-256 `{decision["image_sha256"]}`; source {decision["source_url"]}.
- Open issues: {" ".join(decision["open_issues"])}
- This is an experiment preference only. Nothing is promoted to production and the query strategy is unchanged.

''' if decision else "")
    status = ("automated retrieval complete; owner selected " + decision["candidate_id"] if decision
              else "automated retrieval complete; human review pending (0/1 decisions)")
    report = f'''# A002_CAUSAL_CONCEPT_PILOT — "because" (vocab-000081)

Status: **{status}.** Internal experiment only; production query strategy, Qwen prompts, routing, registry and media unchanged. Game UX/UI remains undecided.

{owner}## Target and meaning

- `vocab-000081` · EN *because* · JP *なぜなら* · VN *bởi vì* (A-001 matrix and `data/vocabulary/*.txt` row 81).
- なぜなら is a sentence-initial connective that introduces the reason for a statement already made (often closed with から). It is not interchangeable with clause-final から/ので in every context. `semantic_decisions_v1.json` marks this ID `needs_decision`.
- "because" presents the **effect first, then its reason** (B, because A). "therefore" runs the other way (A, therefore B). A left-to-right cause→effect picture is closer to "therefore"/"cause and effect" than to "because".

## Why `because icon` falls short

"because" names a logical relation between two events, not an object or an action. The icon search returned mostly ∴/∵-style dot symbols and a three-node graph (mathematical notation, some of which mean *therefore*). Its two pictorial candidates (a person with a question mark beside rain) are ambiguous.

## Variants (exact; V4 written and recorded before searching, no Qwen)

| Option | Query | Search | Downloaded | Selected | SigLIP(query) | SigLIP(fixed) | Best by fixed text |
|---|---|---|---|---|---|---|---|
{var_rows}
- V4 rationale: {html.unescape(next(v["rationale"] for v in results["variants"] if v["variant"] == "V4"))}
- Failed downloads: {fails}. Duplicate URLs reused without a second download: {dups}.
- 4 real searches (DuckDuckGo `wt-wt`, moderate safesearch, 7 results each); retry/timeouts match A002_ICON_PILOT_20 (12 s, search retry 1, download retry 0).

## SigLIP results and limits

- Model `google/siglip2-so400m-patch16-384`, production `score_batch` formula (raw `logits_per_text`).
- **Query score**: each candidate is scored against its own variant's query, as in production; the top score is selected. These scores are **not comparable across variants**.
- **Fixed-text score**: every candidate, plus the original image and all icon-pilot candidates, is also scored against one fixed description, "{ref["text"]}". It is a weak, shared yardstick only.
  - The highest fixed-text score is V2-01/V3-01 (1.65). Next come V1-05 (-1.35) and V1-01 (-2.86).
  - The V4 child images score low (-6.9 to -11.5) even though they contain no text.
  - The original scores -9.05; the icon pick scores -11.88; the best icon-pool image (81-06) scores -6.85.
  - SigLIP rewards printed words like "cause/effect" and does not measure text independence or learner clarity.
- Query-score selection picked text-dominant images for V1 (V1-05) and V2 (V2-05). This shows that query-matched SigLIP ranking is unreliable for this category.

## Automated assessment (AI preliminary, not human)

{AUTOMATED_VERDICT}

| Option | Observation |
|---|---|
''' + "".join(f"| {k} | {v} |\n" for k, v in AI_NOTES.items()) + '''
Criteria applied: causality, alignment with "because" (versus cause, effect, therefore), clarity, educational use, text independence, ambiguity, clutter, later media suitability. Rights are not assessed. Adobe Stock, alamy and dreamstime watermarks suggest restricted sources (see D-003/META-001).

## Strategy assessment (options only; nothing adopted)

1. **Ordinary icon search** is not suitable for logical connectors. It returns notation or abstract glyphs, and some carry the opposite meaning (∴).
2. **Cause-and-effect diagram search** returns explicit causality but almost always printed labels, business fishbone charts or stock watermarks. It also encodes cause→effect order (closer to "therefore").
3. **Concrete contextual illustration search (V4)** gives text-free, child-friendly images. The relation stays implicit, though, and the image tends to teach the noun (rain or umbrella) instead.
4. **Multi-panel examples**: two panels, effect then reason (for example a wet or umbrella scene, then a rain cloud, with a back-pointing link). This could match "B because A" and なぜなら word order, but search is unlikely to find it ready-made; it would need curation or composition.
5. **Manual curation for abstract connectors** (because, therefore, but, if…): a small, human-picked set reviewed against the criteria above. For this category it is likely more reliable than automated ranking.

Similar words for possible future pilots (identified only, not searched): therefore, so, but, if, although and other connectors, where they exist in the benchmark. A separate authorization is required.

## Files

`experiment_manifest.json`, `query_variants.csv`, `retrieval_results.json` (all candidates, URLs, titles, hashes, both scores, errors), `comparison.csv`, `review_gallery.html`, `images/V1..V4/NN.{img,jpg}`, `run_causal.py` (resumable runner), `render_causal.py` (offline renderer).
'''
    (HERE / "experiment_report.md").write_text(report, encoding="utf-8")
    print("rendered", len(rows), "options")


if __name__ == "__main__":
    main()
