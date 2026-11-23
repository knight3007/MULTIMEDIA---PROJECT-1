"""Render an offline A/B review gallery and comparison table from saved retrieval results."""

import csv
import hashlib
import html
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "reports/phase0_quality_review/a001_20261122/evaluation_matrix.json"


def main():
    with (HERE / "selected_vocabulary.csv").open(encoding="utf-8-sig", newline="") as file:
        selected = list(csv.DictReader(file))
    results = json.loads((HERE / "retrieval_results.json").read_text(encoding="utf-8"))["items"]
    by_id = {x["vocab_id"]: x for x in results}
    rows = []
    for item in selected:
        result = by_id.get(item["vocab_id"], {})
        chosen = next((c for c in result.get("candidates", [])
                       if c["candidate_id"] == result.get("selected_candidate_id")), {})
        rows.append({**item, "search_status": result.get("search_status", "NOT_RUN"),
            "search_error": result.get("search_error") or "",
            "raw_result_count": result.get("raw_result_count", 0),
            "candidate_count": len(result.get("candidates", [])),
            "downloaded_count": sum(c["status"] == "DOWNLOADED" for c in result.get("candidates", [])),
            "ranking_status": result.get("ranking_status", "NOT_RUN"),
            "selection_method": result.get("selection_method") or "",
            "selected_candidate_id": chosen.get("candidate_id", ""),
            "icon_image": chosen.get("image_path", ""), "icon_image_sha256": chosen.get("image_sha256", ""),
            "icon_score": chosen.get("siglip_score", "") if chosen else "",
            "human_preference": "NOT_REVIEWED", "reviewer": "", "reviewer_notes": ""})
    with (HERE / "comparison.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    src = json.loads(SOURCE.read_text(encoding="utf-8"))
    source_by_id = {x["vocab_id"]: x for x in src["items"]}
    cards = []
    for row in rows:
        original = source_by_id[row["vocab_id"]]
        result = by_id.get(row["vocab_id"], {})
        chosen = next((c for c in result.get("candidates", []) if c["candidate_id"] == row["selected_candidate_id"]), {})
        def img(path, alt):
            return f'<img src="../../../{html.escape(path, quote=True)}" alt="{html.escape(alt, quote=True)}" loading="lazy">' if path else '<p class="missing">Chưa có ảnh</p>'
        candidates = "".join(f'<figure>{img(c.get("image_path"), c["candidate_id"])}<figcaption>{html.escape(c["candidate_id"])} · {html.escape(c["status"])} · score {html.escape(str(c.get("siglip_score") if c.get("siglip_score") is not None else "NOT_RUN"))}<br>{html.escape(c.get("title") or "")}</figcaption></figure>' for c in result.get("candidates", []))
        cards.append(f'''<article id="{row['vocab_id']}"><h2>{row['vocab_id']} · {html.escape(row['english'])}</h2>
<p>{html.escape(row['japanese'])} · {html.escape(row['vietnamese'])} · {html.escape(row['selection_reason'])}</p>
<div class="pair"><section><h3>A · Ảnh hiện tại</h3><p>Qwen: {html.escape(row['baseline_query'])}</p>{img(row['baseline_image'], 'Baseline '+row['english'])}<small>AI sơ bộ: relevance {row['ai_image_relevance']}; learning {row['ai_image_learning_suitability']}<br>SHA-256: {html.escape(row['baseline_image_sha256'] or 'MISSING_EVIDENCE')}</small></section>
<section><h3>B · Icon pilot</h3><p>Query: {html.escape(row['icon_query'])}</p>{img(row['icon_image'], 'Icon pilot '+row['english'])}<small>Search: {row['search_status']}; downloaded {row['downloaded_count']}/{row['candidate_count']}; rank: {row['ranking_status']}<br>Selected score: {html.escape(str(row['icon_score'] if row['icon_score'] != '' else 'NOT_RUN'))}; SHA-256: {html.escape(row['icon_image_sha256'] or 'MISSING_EVIDENCE')}</small></section></div>
<details><summary>Ứng viên và nguồn ({row['candidate_count']})</summary><div class="candidates">{candidates or '<p>Không có ứng viên tải được.</p>'}</div><pre>{html.escape(json.dumps(result, ensure_ascii=False, indent=2))}</pre></details>
<div class="review"><label>Human A/B review <select data-id="{row['vocab_id']}" data-field="preference"><option>NOT_REVIEWED</option><option>ORIGINAL_BETTER</option><option>ICON_BETTER</option><option>BOTH_GOOD</option><option>BOTH_BAD</option><option>NEEDS_REVIEW</option></select></label><label>Ghi chú <textarea data-id="{row['vocab_id']}" data-field="notes"></textarea></label></div></article>''')
    data = {"experiment_id": "A002_ICON_PILOT_20", "items": [{"vocab_id": r["vocab_id"],
        "baseline_image_sha256": r["baseline_image_sha256"], "icon_image_sha256": r["icon_image_sha256"],
        "selected_candidate_id": r["selected_candidate_id"]} for r in rows]}
    script = '''const meta=JSON.parse(document.getElementById('review-meta').textContent),key='A002_ICON_PILOT_20_review';
let draft={};try{draft=JSON.parse(localStorage.getItem(key)||'{}')}catch{}
document.querySelectorAll('[data-id]').forEach(el=>{const id=el.dataset.id,f=el.dataset.field;el.value=draft[id]?.[f]||el.value;el.addEventListener('input',()=>{draft[id]??={};draft[id][f]=el.value;try{localStorage.setItem(key,JSON.stringify(draft))}catch{}})});
document.getElementById('export').addEventListener('click',()=>{const reviewer=document.getElementById('reviewer').value.trim();if(!reviewer){alert('Nhập tên reviewer');return}const output={...meta,kind:'HUMAN_REVIEW_DRAFT_NOT_AUTO_APPROVAL',reviewer,exported_at:new Date().toISOString(),reviews:draft};const a=document.createElement('a');const u=URL.createObjectURL(new Blob([JSON.stringify(output,null,2)],{type:'application/json'}));a.href=u;a.download='A002-icon-pilot-review-draft.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)});'''
    style = '''body{font:16px/1.5 system-ui,sans-serif;max-width:1180px;margin:auto;padding:1rem;color:#182433;background:#f6f8fa}h1{margin-bottom:.2rem}article{background:white;border:1px solid #d3dce4;border-radius:8px;padding:1rem;margin:1rem 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.pair section{min-width:0;border:1px solid #d3dce4;padding:.7rem;border-radius:6px}.pair img{width:100%;height:300px;object-fit:contain;background:#eee}.pair small{display:block;overflow-wrap:anywhere}.candidates{display:grid;grid-template-columns:repeat(auto-fill,minmax(145px,1fr));gap:.5rem}.candidates figure{margin:0;border:1px solid #ddd;padding:.3rem}.candidates img{width:100%;height:130px;object-fit:contain}.candidates figcaption{font-size:.8rem;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:.75rem}.review{display:grid;gap:.5rem;padding-top:1rem}.review select,.review textarea{display:block;width:100%;max-width:500px}.review textarea{min-height:4rem}.missing{height:300px;display:grid;place-items:center;background:#eee}@media(max-width:700px){.pair{grid-template-columns:1fr}.pair img,.missing{height:230px}}'''
    page = f'''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self' file:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'; media-src 'none'"><title>A-002 Icon Pilot Review</title><style>{style}</style><h1>A-002 · Icon Pilot A/B</h1><p>Công cụ review nội bộ; không phải Game UX/UI. Nhãn AI sơ bộ không phải phê duyệt. Xem ảnh A/B và ứng viên, ghi quyết định riêng.</p><label>Reviewer <input id="reviewer" autocomplete="name"></label> <button id="export">Export JSON</button><p>Chọn: ORIGINAL_BETTER, ICON_BETTER, BOTH_GOOD, BOTH_BAD hoặc NEEDS_REVIEW. Dữ liệu nháp lưu trong trình duyệt này; hãy Export JSON để bàn giao.</p>{''.join(cards)}<script type="application/json" id="review-meta">{html.escape(json.dumps(data, ensure_ascii=False)).replace('&quot;','"')}</script><script>{script}</script></html>'''
    (HERE / "review_gallery.html").write_text(page, encoding="utf-8")
    counts = Counter(r["search_status"] for r in rows)
    downloaded = sum(int(r["downloaded_count"]) for r in rows)
    report = f'''# A-002 icon pilot — automated retrieval report

Experiment `A002_ICON_PILOT_20`; 20 selected IDs. Source A-001 matrix SHA-256 `{hashlib.sha256(SOURCE.read_bytes()).hexdigest()}`. Query variant is exactly `<english> icon`; no Qwen rerun. Provider and SigLIP settings are in `experiment_manifest.json`.

- Search SUCCESS: {counts['SUCCESS']}/20; FAILED: {counts['FAILED']}; NOT_RUN: {counts['NOT_RUN']}.
- Candidate images downloaded and retained: {downloaded}; items with at least one downloaded image: {sum(int(r['downloaded_count'])>0 for r in rows)}/20.
- Items scored by SigLIP: {sum(r['ranking_status']=='SCORED' for r in rows)}/20. Selection without scoring uses first valid result and is labeled accordingly.
- Items with no suitable image: **UNKNOWN until human review**. Technical download success is not educational suitability.
- Human A/B decisions: 0. Do not call a winner before owner review.

## Differences from the production collector (recorded, not hidden)

- Same: `imagecollector.search_images` (DuckDuckGo via `ddgs`, region `wt-wt`, safesearch `moderate`), `DEFAULT_PAGE_SIZE` 7 candidates (below the 10-candidate cap), `download_candidate_image`/`normalize_image_to_jpeg`, and `SiglipImageScorer` with `google/siglip2-so400m-patch16-384`, ranking candidates against the search query and selecting the top score.
- Different: timeout 12 s (production default 20 s); search retries 1 (production 2); download retries 0 (production 2); 2 s pause between items; every downloaded candidate is normalized to JPEG and kept under `images/<vocab_id>/` instead of only the winner in `data/image/en/`.
- Baseline A images come from the original Qwen-query run (staging paths/hashes in `selected_vocabulary.csv`). The original search candidates were not retained, so A has no candidate pool to compare against B.
- Searches run on a different date than the original run, so search results can differ for reasons other than the query change.

## Per-item results

| ID | English | Icon query | Search | Downloaded | Ranking | Selected | Score |
|---|---|---|---|---|---|---|---|
''' + "".join(f"| {r['vocab_id']} | {r['english']} | `{r['icon_query']}` | {r['search_status']} | {r['downloaded_count']}/{r['candidate_count']} | {r['ranking_status']} | {r['selected_candidate_id'] or '-'} | {(f'{float(r['icon_score']):.4f}' if r['icon_score'] != '' else 'NOT_RUN')} |\n" for r in rows) + f'''
Failed downloads: {"; ".join(f"{c['candidate_id']} ({c['error']})" for x in results for c in x.get('candidates', []) if c['status'] != 'DOWNLOADED') or 'none'}.

SigLIP scores are comparable only within one item's candidate pool. They are not comparable across items or with the baseline, which was scored against a different query text.

AI-preliminary visual notes, which are not human decisions: `automated_visual_observations.md`.

See `comparison.csv` for baseline query/image/hash, icon query/selected image/hash, scores and blank human fields. `retrieval_results.json` preserves candidate IDs, URLs, titles, paths, hashes, errors and timings. Open `review_gallery.html` locally for side-by-side inspection and JSON export. This is internal evaluation only; Game UX/UI remains undecided. No production media or query strategy was replaced.
'''
    (HERE / "experiment_report.md").write_text(report, encoding="utf-8")
    print(dict(counts), "downloaded", downloaded, "scored", sum(r["ranking_status"] == "SCORED" for r in rows))


if __name__ == "__main__":
    main()
