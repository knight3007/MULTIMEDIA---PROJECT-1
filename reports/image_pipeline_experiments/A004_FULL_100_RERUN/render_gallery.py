"""Render the internal A-004 owner review page from frozen ledgers."""
import csv
import hashlib
import html
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def esc(value):
    return html.escape(str(value or ""), quote=True)


def asset(path, label):
    if not path or path == "MISSING_EVIDENCE":
        return f'<div class="empty">{esc(label)}: không có ảnh</div>'
    target = ROOT / path
    if not target.is_file():
        raise FileNotFoundError(target)
    url = Path(os.path.relpath(target, HERE)).as_posix()
    return f'<img loading="lazy" src="{esc(url)}" alt="{esc(label)}">'


def main():
    manifest = json.loads((HERE / "experiment_manifest.json").read_text(encoding="utf-8"))
    queries = json.loads((HERE / "query_results.json").read_text(encoding="utf-8"))
    retrieval = json.loads((HERE / "retrieval_results.json").read_text(encoding="utf-8"))
    with (HERE / "frozen_vocabulary.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    with (HERE / "evaluation_matrix.csv").open(encoding="utf-8-sig", newline="") as stream:
        assessments = {r["vocab_id"]: r for r in csv.DictReader(stream)}
    assert len(rows) == len(queries) == len(retrieval) == 100
    cards, export_items = [], {}
    for row in rows:
        vid = row["vocab_id"]
        q, result, assessment = queries[vid], retrieval[vid], assessments[vid]
        candidates = [c for c in result["candidates"] if c["download_status"] == "SUCCESS"]
        ranked = sorted(candidates, key=lambda c: c.get("siglip_rank", 999))
        proposed = next((c for c in ranked if c["candidate_id"] == result["proposed_candidate_id"]), None)
        options = ['<option value="">Chưa chọn</option>']
        for c in ranked:
            options.append(f'<option value="{esc(c["candidate_id"])}">{esc(c["candidate_id"])} · hạng {c["siglip_rank"]}</option>')
        options.append('<option value="NO_SUITABLE_IMAGE">NO_SUITABLE_IMAGE</option>')
        candidate_html = "".join(
            f'<figure>{asset(c["jpeg_path"], c["candidate_id"])}<figcaption>'
            f'{esc(c["candidate_id"])} · SigLIP #{c["siglip_rank"]} '
            f'({c["siglip_score"]:.3f}) · tìm kiếm #{c["retrieval_rank"]}'
            f'</figcaption></figure>' for c in ranked
        ) or '<p class="empty">Không có ứng viên hợp lệ.</p>'
        state = result["status"]
        note = assessment["ai_preliminary_note"] or "Chưa có đánh giá ngữ nghĩa của AI."
        cards.append(f'''<article class="item" data-id="{esc(vid)}" data-status="{esc(state)}">
<header><h2>{esc(vid)} · {esc(row["english"])}</h2><span class="status">{esc(state)}</span></header>
<p><strong>日本語:</strong> {esc(row["japanese"])} · <strong>Tiếng Việt:</strong> {esc(row["vietnamese"])}</p>
<p><strong>Nghĩa cần xét:</strong> {esc(row["expected_semantic_meaning"])}<br>
<strong>Truy vấn:</strong> {esc(q.get("effective_query") or q.get("normalized_query") or q.get("raw_decoded_text"))} · {esc(q["status"])}<br>
<strong>Lỗi:</strong> {esc(result.get("error") or q.get("error") or "không có")}</p>
<div class="pair"><figure><figcaption>Ảnh A-001 trước đó</figcaption>{asset(row["previous_image_path"], "Ảnh A-001 " + row["english"])}</figure>
<figure><figcaption>Ảnh đề xuất A-004 (chưa phê duyệt)</figcaption>{asset(proposed["jpeg_path"] if proposed else None, "Ảnh A-004 " + row["english"])}</figure></div>
<details><summary>Ứng viên hợp lệ ({len(ranked)}) và thứ hạng</summary><div class="candidates">{candidate_html}</div></details>
<p class="prelim"><strong>AI_PRELIMINARY:</strong> nghĩa {esc(assessment["ai_preliminary_image_relevance"])}; học tập {esc(assessment["ai_preliminary_educational_suitability"])}. {esc(note)}</p>
<fieldset><legend>Đánh giá của người duyệt</legend>
<label>Truy vấn <select data-field="query_label"><option value="UNREVIEWED">Chưa duyệt</option><option>PASS</option><option>FAIL</option><option>NEEDS_REVIEW</option></select></label>
<label>Chọn ảnh <select data-field="selected_candidate_id">{''.join(options)}</select></label>
<label>Chất lượng ảnh <select data-field="image_label"><option value="UNREVIEWED">Chưa duyệt</option><option>PASS</option><option>FAIL</option><option>NEEDS_REVIEW</option></select></label>
<label>Ghi chú <textarea data-field="notes" rows="2"></textarea></label>
</fieldset></article>''')
        export_items[vid] = {"query": q.get("effective_query"), "query_status": q["status"],
                             "image_status": state, "proposed_candidate_id": result["proposed_candidate_id"],
                             "candidates": {c["candidate_id"]: {"jpeg_path": c["jpeg_path"],
                                                               "jpeg_sha256": c["jpeg_sha256"]} for c in ranked}}
    metadata = {"task_id": "A-004", "kind": "HUMAN_REVIEW_DRAFT_NOT_AUTO_APPROVAL",
                "dataset_sha256": manifest["dataset_sha256"], "items": export_items}
    payload = json.dumps(metadata, ensure_ascii=False).replace("<", "\\u003c")
    page = '''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>A-004 · Duyệt ảnh nội bộ</title><style>
:root{font:16px/1.5 system-ui,sans-serif;color:#17212a;background:#f3f5f4}*{box-sizing:border-box}body{margin:0}main{max-width:1180px;margin:auto;padding:20px}h1{font-size:1.65rem;margin:0}h2{font-size:1.2rem;margin:0}p{margin:.5rem 0 1rem}.toolbar{position:sticky;top:0;z-index:2;background:#fff;border-bottom:1px solid #cbd5d2;padding:12px 20px;display:flex;gap:12px;align-items:end;flex-wrap:wrap}.toolbar label{display:grid;gap:4px}.toolbar input,.toolbar select,button,fieldset select,textarea{font:inherit;padding:7px;border:1px solid #8b9b98;border-radius:4px;background:#fff}button{background:#155c50;color:#fff;border-color:#155c50;cursor:pointer}button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible,summary:focus-visible{outline:3px solid #e09a2d;outline-offset:2px}.item{background:#fff;border:1px solid #ccd5d2;padding:16px;margin:16px 0}.item header{display:flex;justify-content:space-between;gap:10px;align-items:start}.status{font-size:.82rem;background:#e6eeeb;padding:3px 8px;border-radius:3px}.pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.pair figure,.candidates figure{margin:0;border:1px solid #dae1df;padding:8px}.pair img{width:100%;height:260px;object-fit:contain}.candidates{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:10px 0}.candidates img{width:100%;height:140px;object-fit:contain}.candidates figcaption,figcaption{font-size:.85rem;color:#41514d}.empty{min-height:90px;display:grid;place-items:center;background:#edf1ef;color:#52635e}.prelim{background:#f4f0df;padding:8px}fieldset{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;border:1px solid #b4c3bd}fieldset label{display:grid;gap:4px}fieldset label:last-child{grid-column:1/-1}textarea{width:100%;resize:vertical}@media(max-width:650px){main{padding:10px}.pair,fieldset{grid-template-columns:1fr}.pair img{height:210px}}@media print{.toolbar,fieldset{display:none}details{display:block}}
</style></head><body><div class="toolbar"><label>Tìm từ/ID<input id="search" type="search"></label><label>Trạng thái<select id="filter"><option value="">Tất cả</option><option>RANKED</option><option>SKIPPED_QUERY</option><option>NO_VALID_CANDIDATES</option><option>FAILED</option></select></label><label>Người duyệt<input id="reviewer" autocomplete="name"></label><button id="export" type="button">Export JSON</button><span id="count" role="status"></span></div>
<main><h1>A-004 · Duyệt ảnh nội bộ</h1><p>100 từ · Ảnh SigLIP là đề xuất, chưa được duyệt. Quyền phát hành phải xét riêng. Bản nháp lưu trong trình duyệt này; hãy Export JSON để chuyển quyết định.</p>
''' + "\n".join(cards) + '''</main><script id="metadata" type="application/json">''' + payload + '''</script><script>
const meta=JSON.parse(document.getElementById('metadata').textContent), key='A004_REVIEW_DRAFT_'+meta.dataset_sha256.slice(0,12);
let draft={};try{draft=JSON.parse(localStorage.getItem(key)||'{}')}catch{}
const items=[...document.querySelectorAll('.item')];for(const card of items){const saved=draft[card.dataset.id]||{};for(const field of card.querySelectorAll('[data-field]')){if(saved[field.dataset.field]!==undefined)field.value=saved[field.dataset.field];field.addEventListener('input',()=>{(draft[card.dataset.id]??={})[field.dataset.field]=field.value;try{localStorage.setItem(key,JSON.stringify(draft))}catch{}})}}
function update(){const query=document.getElementById('search').value.toLowerCase(),status=document.getElementById('filter').value;let visible=0;for(const card of items){const show=(!query||card.textContent.toLowerCase().includes(query))&&(!status||card.dataset.status===status);card.hidden=!show;if(show)visible++}document.getElementById('count').textContent=visible+' / '+items.length}
document.getElementById('search').addEventListener('input',update);document.getElementById('filter').addEventListener('change',update);update();
document.getElementById('export').addEventListener('click',()=>{const reviewer=document.getElementById('reviewer').value.trim();if(!reviewer){alert('Nhập tên người duyệt');return}const reviews=items.map(card=>{const id=card.dataset.id,values={};for(const field of card.querySelectorAll('[data-field]'))values[field.dataset.field]=field.value;const chosen=meta.items[id].candidates[values.selected_candidate_id]||null;return{vocab_id:id,...values,selected_jpeg_path:chosen?.jpeg_path||null,selected_jpeg_sha256:chosen?.jpeg_sha256||null}});const out={task_id:meta.task_id,kind:meta.kind,dataset_sha256:meta.dataset_sha256,reviewer,exported_at:new Date().toISOString(),reviews};const blob=new Blob([JSON.stringify(out,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='A004-review-'+new Date().toISOString().slice(0,10)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});
</script></body></html>'''
    (HERE / "review_gallery.html").write_text(page, encoding="utf-8")
    print("rendered", len(cards), "items", "sha256", hashlib.sha256(page.encode()).hexdigest())


if __name__ == "__main__":
    main()
