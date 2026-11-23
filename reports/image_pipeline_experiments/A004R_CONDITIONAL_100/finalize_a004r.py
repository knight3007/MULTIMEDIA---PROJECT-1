"""Verify and publish A-004R's internal comparison and owner-review package."""
import csv
import hashlib
import html
import importlib.util
import json
import os
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SPEC = importlib.util.spec_from_file_location("a004r_runner", HERE / "run_a004r.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)

# Visual desk review of the nine A-004R top images. These are AI preliminary judgments.
NEW_REVIEW = {
    "vocab-000001": ("PASS", "NEEDS_REVIEW", "Apple is clear; small source mark at bottom."),
    "vocab-000008": ("PASS", "FAIL", "Bottled-water advertising and prominent text reveal/complicate the answer."),
    "vocab-000019": ("PASS", "NEEDS_REVIEW", "Rain icon is clear; inspect small source mark."),
    "vocab-000028": ("PASS", "PASS", "A clear car photo; brand and source rights require separate review."),
    "vocab-000053": ("PASS", "PASS", "Writing hand icon is easy to recognize."),
    "vocab-000056": ("PASS", "PASS", "Sleeping-person icon is easy to recognize."),
    "vocab-000061": ("NEEDS_REVIEW", "FAIL", "Prominent UNDERSTAND text and watermark; unsuitable as a learning prompt."),
    "vocab-000062": ("PASS", "PASS", "Remember/reminder icon conveys the intended action."),
    "vocab-000065": ("PASS", "PASS", "Swimming icon is easy to recognize."),
}


def check_candidate(candidate):
    if candidate["download_status"] != "SUCCESS":
        return
    for kind in ("raw", "jpeg"):
        path = ROOT / candidate[f"{kind}_path"]
        assert path.is_file() and runner.sha(path) == candidate[f"{kind}_sha256"], path


def asset(path, label):
    if not path:
        return '<div class="missing">Không có ảnh</div>'
    target = ROOT / path
    assert target.is_file(), target
    relative = Path(os.path.relpath(target, HERE)).as_posix()
    return f'<img loading="lazy" src="{html.escape(relative, quote=True)}" alt="{html.escape(label, quote=True)}">'


def proposed(result):
    return next((c for c in result["candidates"] if c["candidate_id"] == result["proposed_candidate_id"]), None)


def write_csv(name, fields, rows):
    with (HERE / name).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    manifest = runner.load_json(runner.MANIFEST)
    routes = runner.guard(manifest)
    results = runner.load_json(runner.RESULTS)
    assert len(results) == len(routes) == 100
    assert set(results) == {r["vocab_id"] for r in routes}
    assert len(manifest["batches"]) == 10
    old_matrix = {r["vocab_id"]: r for r in runner.read_csv(runner.A004 / "evaluation_matrix.csv")}
    old_results = runner.load_json(runner.A004 / "retrieval_results.json")
    rankings, matrix, cards, export_items = [], [], [], {}
    for row in routes:
        vid, result = row["vocab_id"], results[row["vocab_id"]]
        assert result["execution_source"] == row["execution_source"]
        if result["status"] == "RANKED_NEW":
            assert result["search_attempted"] and result["score_attempted"]
            assert result["query"] == row["experimental_search_query"]
            assert 1 <= len(result["candidates"]) <= 7
            ranked = sorted((c for c in result["candidates"] if c["download_status"] == "SUCCESS"),
                            key=lambda c: c["siglip_score"], reverse=True)
            assert ranked and ranked[0]["candidate_id"] == result["proposed_candidate_id"]
            assert [c["siglip_rank"] for c in ranked] == list(range(1, len(ranked) + 1))
        elif result["status"] == "REUSED_A004":
            assert result["provenance"]["new_search"] is False
            assert result["provenance"]["retrieval_sha256"] == manifest["a004_retrieval_sha256"]
            assert result["proposed_candidate_id"] == old_results[vid]["proposed_candidate_id"]
            assert not result["search_attempted"] and not result["score_attempted"]
        else:
            assert not result["search_attempted"] and not result["score_attempted"]
            assert not result["candidates"] and result["proposed_candidate_id"] is None
        for c in result["candidates"]:
            check_candidate(c)
            rankings.append({"vocab_id": vid, "execution_source": result["execution_source"],
                             "candidate_id": c["candidate_id"], "retrieval_rank": c["retrieval_rank"],
                             "siglip_rank": c.get("siglip_rank") or "", "siglip_score": c.get("siglip_score") or "",
                             "download_status": c["download_status"], "source_url": c["source"].get("image_url", ""),
                             "jpeg_path": c["jpeg_path"] or "", "jpeg_sha256": c["jpeg_sha256"] or ""})
        candidate = proposed(result)
        if result["status"] == "RANKED_NEW":
            relevance, suitability, note = NEW_REVIEW[vid]
            assessment_source = "A004R_AI_PRELIMINARY_VISUAL_REVIEW"
        elif result["status"] == "REUSED_A004":
            old = old_matrix[vid]
            relevance, suitability, note = (old["ai_preliminary_image_relevance"],
                                            old["ai_preliminary_educational_suitability"],
                                            old["ai_preliminary_note"])
            assessment_source = "REUSED_A004_AI_PRELIMINARY"
        else:
            relevance, suitability, note = "NOT_ASSESSED", "NOT_ASSESSED", result.get("error") or row["routing_rationale"]
            assessment_source = "NO_NEW_CANDIDATE"
        quality_gate = ("REJECTED_PRELIMINARY" if suitability == "FAIL" else
                        "NEEDS_OWNER_REVIEW" if candidate else "NO_NEW_CANDIDATE")
        old = old_matrix[vid]
        matrix.append({"vocab_id": vid, "english": row["english"], "japanese": row["japanese"],
                       "vietnamese": row["vietnamese"], "intended_meaning": row["intended_meaning"],
                       "routing_strategy": row["routing_strategy"], "experimental_query": result["query"],
                       "execution_source": result["execution_source"], "processing_status": result["status"],
                       "search_attempted_now": result["search_attempted"], "search_status": result["search_status"],
                       "candidate_count": len(result["candidates"]),
                       "valid_candidate_count": sum(c["download_status"] == "SUCCESS" for c in result["candidates"]),
                       "ranking_status": result["ranking_status"], "proposed_candidate_id": result["proposed_candidate_id"] or "",
                       "proposed_jpeg_path": candidate["jpeg_path"] if candidate else "",
                       "proposed_jpeg_sha256": candidate["jpeg_sha256"] if candidate else "",
                       "a001_image_path": row["a001_image_path"], "a001_image_sha256": row["a001_image_sha256"],
                       "a004_image_path": row["a004_image_path"], "a004_image_sha256": row["a004_image_sha256"],
                       "ai_preliminary_semantic_correctness": relevance,
                       "ai_preliminary_educational_suitability": suitability,
                       "ai_preliminary_source": assessment_source, "ai_preliminary_note": note,
                       "quality_gate": quality_gate, "owner_decision": row["owner_decision"],
                       "owner_candidate_id": row["owner_candidate_id"], "owner_image_path": row["owner_image_path"],
                       "owner_image_sha256": row["owner_image_sha256"],
                       "human_approval_of_new_image": result["human_approval_of_new_image"],
                       "usage_restriction": row["usage_restriction"], "public_eligibility": row["public_eligibility"]})
        esc = lambda value: html.escape(str(value or ""), quote=True)
        valid = sorted((c for c in result["candidates"] if c["download_status"] == "SUCCESS"),
                       key=lambda c: c.get("siglip_rank", 999))
        options = '<option value="">Chưa chọn</option>' + ''.join(
            f'<option value="{esc(c["candidate_id"])}">{esc(c["candidate_id"])} · #{c["siglip_rank"]}</option>' for c in valid)
        options += '<option value="NO_SUITABLE_IMAGE">NO_SUITABLE_IMAGE</option>'
        ranking_html = ''.join(
            f'<button type="button" class="candidate" data-candidate-id="{esc(c["candidate_id"])}" aria-pressed="false">'
            f'{asset(c["jpeg_path"], "Ứng viên " + c["candidate_id"])}'
            f'<span><b>#{c["siglip_rank"]} · {esc(c["candidate_id"])}</b><br>SigLIP {c["siglip_score"]:.3f} · tìm #{c["retrieval_rank"]}</span></button>'
            for c in valid) or '<p>Không có ứng viên trong lô này.</p>'
        pictures = [row["a001_image_path"], row["a004_image_path"],
                    candidate["jpeg_path"] if result["status"] == "RANKED_NEW" and candidate else "",
                    row["owner_image_path"]]
        labels = ["A-001 gốc", "A-004 truy vấn mặc định", "A-004R truy xuất mới", "Chủ sở hữu chọn / internal"]
        panels = ''.join(f'<figure><figcaption>{esc(label)}</figcaption>{asset(path, label + " " + row["english"])}</figure>'
                         for path, label in zip(pictures, labels))
        cards.append(f'''<article class="item" data-id="{esc(vid)}" data-status="{esc(result["status"])}">
<h2>{esc(vid)} · {esc(row["english"])}</h2><p>{esc(row["japanese"])} · {esc(row["vietnamese"])} · {esc(row["intended_meaning"])}</p>
<p><b>Định tuyến:</b> {esc(row["routing_strategy"])} · <b>Nguồn xử lý:</b> {esc(result["execution_source"])} · <b>Truy vấn thực tế:</b> {esc(result["query"] or "không chạy")}<br>
<b>Trạng thái:</b> {esc(result["status"])} · <b>Quyền:</b> {esc(row["public_eligibility"])} · <b>Giới hạn:</b> {esc(row["usage_restriction"])}</p>
<div class="pictures">{panels}</div><details {"open" if result["status"] == "RANKED_NEW" else ""}><summary>Xem và chọn ảnh trong {len(valid)} ứng viên (bấm vào ảnh)</summary><div class="candidates">{ranking_html}</div></details>
<p class="prelim"><b>AI_PRELIMINARY / {esc(assessment_source)}:</b> nghĩa {esc(relevance)}, học tập {esc(suitability)}; {esc(note)}. Cổng chất lượng: {esc(quality_gate)}.</p>
<p><b>Quyết định đã có của chủ sở hữu:</b> {esc(row["owner_decision"])} {esc(row["owner_candidate_id"])}</p>
<fieldset><legend>Phản hồi mới (chưa tự động phê duyệt)</legend><label>Chọn ứng viên <select data-field="selected_candidate_id">{options}</select></label>
<label>Đánh giá ảnh <select data-field="image_label"><option value="UNREVIEWED">Chưa duyệt</option><option>PASS</option><option>FAIL</option><option>NEEDS_REVIEW</option></select></label>
<label>Ghi chú <textarea data-field="notes" rows="2"></textarea></label></fieldset></article>''')
        export_items[vid] = {"execution_source": result["execution_source"], "routing_strategy": row["routing_strategy"],
                             "query": result["query"], "owner_decision": row["owner_decision"],
                             "candidates": {c["candidate_id"]: {"jpeg_path": c["jpeg_path"], "jpeg_sha256": c["jpeg_sha256"]}
                                            for c in valid}}
    write_csv("candidate_rankings.csv", list(rankings[0]), rankings)
    write_csv("evaluation_matrix.csv", list(matrix[0]), matrix)
    metadata = json.dumps({"task_id": "A-004R", "kind": "HUMAN_REVIEW_DRAFT_NOT_AUTO_APPROVAL",
                           "routing_sha256": manifest["routing_matrix_sha256"], "dataset_sha256": manifest["dataset_sha256"],
                           "items": export_items}, ensure_ascii=False).replace("<", "\\u003c")
    page = '''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>A-004R · Duyệt ảnh nội bộ</title><style>
:root{font:16px/1.5 system-ui,sans-serif;color:#17212a;background:#f3f5f4}*{box-sizing:border-box}body{margin:0}main{max-width:1300px;margin:auto;padding:20px}h1{font-size:1.6rem}h2{font-size:1.15rem}p{margin:.5rem 0 1rem}.toolbar{position:sticky;top:0;z-index:2;background:#fff;border-bottom:1px solid #cbd5d2;padding:12px 20px;display:flex;gap:12px;align-items:end;flex-wrap:wrap}.toolbar label,fieldset label{display:grid;gap:4px}input,select,button,textarea{font:inherit;padding:7px;border:1px solid #8b9b98;border-radius:4px;background:#fff}button{background:#155c50;color:#fff;cursor:pointer}button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible,summary:focus-visible{outline:3px solid #e09a2d;outline-offset:2px}.item{background:#fff;border:1px solid #ccd5d2;padding:16px;margin:16px 0}.pictures{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.pictures figure{margin:0;border:1px solid #dae1df;padding:8px;min-width:0}.pictures img{width:100%;height:200px;object-fit:contain}.pictures figcaption{font-size:.85rem;color:#41514d}.candidates{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px;margin:12px 0}.candidate{background:#fff;color:#17212a;text-align:left;padding:8px;border:2px solid #8b9b98}.candidate img{display:block;width:100%;height:145px;object-fit:contain}.candidate span{display:block;font-size:.8rem;overflow-wrap:anywhere}.candidate[aria-pressed="true"]{border-color:#155c50;background:#dcefe9}.missing{min-height:120px;display:grid;place-items:center;background:#edf1ef;color:#52635e}.prelim{background:#f4f0df;padding:8px}fieldset{display:grid;grid-template-columns:1fr 1fr;border:1px solid #b4c3bd;gap:10px}fieldset label:last-child{grid-column:1/-1}textarea{width:100%}[hidden]{display:none!important}@media(max-width:850px){.pictures{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:500px){main{padding:10px}.pictures,fieldset{grid-template-columns:1fr}.pictures img{height:180px}}
</style></head><body><div class="toolbar"><label>Tìm từ/ID<input id="search" type="search"></label><label>Trạng thái<select id="filter"><option value="">Tất cả</option><option>RANKED_NEW</option><option>REUSED_A004</option><option>BLOCKED_QUERY</option><option>OWNER_REFERENCE</option><option>NO_SUITABLE_IMAGE</option><option>INTERNAL_OVERRIDE</option></select></label><label>Người duyệt<input id="reviewer" autocomplete="name"></label><button id="export" type="button">Export JSON</button><span id="count" role="status"></span></div><main><h1>A-004R · So sánh và duyệt ảnh nội bộ</h1><p>100 từ. Mở danh sách ứng viên và bấm ảnh phù hợp; ảnh được chọn sẽ hiện trong ô “Chọn ứng viên”. Nếu không ảnh nào phù hợp, chọn NO_SUITABLE_IMAGE trong ô đó. Sau đó chọn đánh giá ảnh, nhập tên người duyệt và Export JSON. Ảnh SigLIP là đề xuất, chưa được phê duyệt; quyền phát hành xét riêng.</p>''' + '\n'.join(cards) + '''</main><script id="metadata" type="application/json">''' + metadata + '''</script><script>
const meta=JSON.parse(document.getElementById('metadata').textContent), key='A004R_REVIEW_DRAFT_'+meta.routing_sha256.slice(0,12);
let draft={};try{draft=JSON.parse(localStorage.getItem(key)||'{}')}catch{}
const items=[...document.querySelectorAll('.item')];for(const card of items){const saved=draft[card.dataset.id]||{};for(const field of card.querySelectorAll('[data-field]')){if(saved[field.dataset.field]!==undefined)field.value=saved[field.dataset.field];field.addEventListener('input',()=>{(draft[card.dataset.id]??={})[field.dataset.field]=field.value;try{localStorage.setItem(key,JSON.stringify(draft))}catch{}})}}
for(const card of items){const select=card.querySelector('[data-field="selected_candidate_id"]'),buttons=[...card.querySelectorAll('[data-candidate-id]')];const sync=()=>{for(const button of buttons)button.setAttribute('aria-pressed',String(button.dataset.candidateId===select.value))};for(const button of buttons)button.addEventListener('click',()=>{select.value=button.dataset.candidateId;select.dispatchEvent(new Event('input',{bubbles:true}));sync()});select.addEventListener('change',sync);sync()}
function update(){const query=document.getElementById('search').value.toLowerCase(),status=document.getElementById('filter').value;let visible=0;for(const card of items){const show=(!query||card.textContent.toLowerCase().includes(query))&&(!status||card.dataset.status===status);card.hidden=!show;if(show)visible++}document.getElementById('count').textContent=visible+' / '+items.length}
document.getElementById('search').addEventListener('input',update);document.getElementById('filter').addEventListener('change',update);update();
document.getElementById('export').addEventListener('click',()=>{const reviewer=document.getElementById('reviewer').value.trim();if(!reviewer){alert('Nhập tên người duyệt');return}const reviews=items.map(card=>{const id=card.dataset.id,values={};for(const field of card.querySelectorAll('[data-field]'))values[field.dataset.field]=field.value;const chosen=meta.items[id].candidates[values.selected_candidate_id]||null;return{vocab_id:id,...values,selected_jpeg_path:chosen?.jpeg_path||null,selected_jpeg_sha256:chosen?.jpeg_sha256||null}});const out={task_id:meta.task_id,kind:meta.kind,routing_sha256:meta.routing_sha256,dataset_sha256:meta.dataset_sha256,reviewer,exported_at:new Date().toISOString(),reviews};const blob=new Blob([JSON.stringify(out,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='A004R-review-'+new Date().toISOString().slice(0,10)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});
</script></body></html>'''
    (HERE / "review_gallery.html").write_text(page, encoding="utf-8")
    statuses = Counter(r["processing_status"] for r in matrix)
    suitability = Counter(r["ai_preliminary_educational_suitability"] for r in matrix)
    new_pass = sum(r["ai_preliminary_educational_suitability"] == "PASS" and r["processing_status"] == "RANKED_NEW" for r in matrix)
    lines = ["# A-004R conditional-query experiment", "",
             "100/100 IDs have explicit outcomes. This is an internal benchmark, not production selection or rights clearance.", "",
             "## Execution", "", f"- Routing: {dict(Counter(r['routing_strategy'] for r in routes))}.",
             f"- Outcome: {dict(statuses)}.", "- New searches: 9 (six ICON, three NORMAL), all ranked. A-004 reused rankings: 57; owner references: six; explicit no-image: one; internal-only override: one; query blockers: 26.",
             "- Owner references and A-004 cache are never counted as fresh retrieval or fresh ranking. Every new search used at most seven candidates, one SigLIP pass, no retry.",
             "- A default Python attempt stopped on duplicate OpenMP runtime before search/scoring; it was reset after verifying no search attempt. Live work used the repository .venv, as A-004 did.", "",
             "## Preliminary quality", "", f"- Nine fresh top images: {new_pass} PASS for educational suitability, two NEEDS_REVIEW, two FAIL. These are visual desk judgments, not owner approval.",
             "- Water has bottle advertising/answer text; understand has prominent answer text and watermark. Their SigLIP top-1 results are rejected at the preliminary gate. Apple and rain need source-mark review.",
             f"- Across 100 rows, suitability labels are {dict(suitability)}; 57 reused A-004 labels remain tagged REUSED_A004_AI_PRELIMINARY. The 34 owner/special/blocked rows have no new candidate assessment.",
             "- A-001 baseline, A-004 default-query image and A-004R new image are separate columns in the evaluation matrix and gallery. A-004R is newly paired for only nine IDs; six ICON queries are too few to claim a dataset-wide quality gain.",
             "- For the six new ICON searches, A-004→A-004R preliminary educational labels: sleep FAIL→PASS, write FAIL→PASS, remember FAIL→PASS, rain NEEDS_REVIEW→NEEDS_REVIEW, understand FAIL→FAIL; swim had no A-004 image and is now PASS. This is a small, partly unpaired comparison.",
             "- For the three new NORMAL searches: apple PASS→NEEDS_REVIEW (source mark), car PASS→PASS, water had no A-004 image and is now FAIL (advertising/text). A-001 images remain available for direct owner comparison in the gallery.",
             "- Six earlier owner-quality selections are preserved by exact path/hash and excluded from the nine fresh results. `sometimes` remains NO_SUITABLE_IMAGE; `because` remains INTERNAL_ONLY_TEMPORARY. Public rights remain unverified for all images.", "",
             "## Review and limits", "", "- Owner feedback and JSON export are available in `review_gallery.html`; generated candidates are NOT_REVIEWED and NOT_PROMOTED.",
             "- The 26 BLOCKED_QUERY items require explicit semantic query repair or contextual decisions before retrieval. Five other A-003 holdouts remain unreviewed separately.",
             "- No Qwen or SigLIP weights changed; no canonical vocabulary, production media, previous experiment or owner decision was overwritten.", ""]
    (HERE / "evaluation_report.md").write_text("\n".join(lines), encoding="utf-8")
    manifest["status"] = "COMPLETE_WITH_QUERY_BLOCKERS_OWNER_REVIEW_PENDING"
    manifest["completed_ids"] = [r["vocab_id"] for r in routes]
    manifest["final_counts"] = dict(statuses)
    manifest["artifacts"] = {name: runner.sha(HERE / name) for name in
                              ("routing_matrix.csv", "routing_preview.md", "retrieval_results.json",
                               "candidate_rankings.csv", "evaluation_matrix.csv", "review_gallery.html", "evaluation_report.md")}
    runner.save_json(runner.MANIFEST, manifest)
    print("Finalized", len(matrix), "IDs", dict(statuses), "rankings", len(rankings))


if __name__ == "__main__":
    main()
