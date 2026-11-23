"""Render the seven-item internal review from recorded assets; no promotion."""
import csv
import hashlib
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
A003 = ROOT / "reports/image_pipeline_experiments/A003_CONDITIONAL_SEARCH"
DIAG = ROOT / "reports/image_pipeline_experiments/A003_RANKING_DIAGNOSIS"
feedback = json.loads((DIAG / "owner_feedback.json").read_text(encoding="utf-8"))
pairs = json.loads((A003 / "retrieval_results.json").read_text(encoding="utf-8"))["pairs"]
new = json.loads((HERE / "targeted_retrieval_results.json").read_text(encoding="utf-8"))
sample = {r["vocab_id"]: r for r in csv.DictReader((A003 / "frozen_sample.csv").open(encoding="utf-8-sig", newline=""))}
scores = {r["candidate_id"]: r for r in csv.DictReader((DIAG / "scoring_comparison.csv").open(encoding="utf-8-sig", newline=""))}
candidate = {c["candidate_id"]: c for p in pairs for c in p["candidates"]}
candidate.update({c["candidate_id"]: c for v in new["variants"] for c in v["candidates"]})

# These are review proposals, never approvals. Hungry/eat retain the owner's A/B preference.
plans = {
    "vocab-000046": ("vocab-000046-NORMAL-01", "vocab-000046-ICON-01", ["vocab-000046-NORMAL-05"], "Owner prefers the existing hungry icon over the text-heavy NORMAL result."),
    "vocab-000057": ("vocab-000057-ICON-07", "vocab-000057-NORMAL-06", [], "Owner prefers the eating photograph; icon search returned an unrelated musician."),
    "vocab-000063": ("vocab-000063-ICON-03", "vocab-000063-ICON-07", ["vocab-000063-ICON-02"], "The selected icon is a web-page screenshot. ICON-07 shows a parcel passing between hands with more balanced framing; ICON-02 is larger and fills its frame."),
    "vocab-000059": ("vocab-000059-ICON-06", "vocab-000059-ICON-01", ["vocab-000059-ICON-05"], "Owner prefers the icon arm. ICON-01 shows a purchase cart and money without printing BUY; selected ICON-06 reveals the answer."),
    "vocab-000021": ("vocab-000021-NORMAL-01", "vocab-000021-NORMAL-05", [], "NORMAL-05 is a photograph of a complete constructed house; selected NORMAL-01 is an unfinished frame."),
    "vocab-000031": ("vocab-000031-NORMAL-06", "vocab-000031-ICON-03", ["vocab-000031-ICON-01"], "The existing ICON-03 clearly depicts a physical open book without prominent text; selected NORMAL-06 is an exhibition poster."),
    "vocab-000083": ("vocab-000083-NORMAL-04", None, ["vocab-000083-ICON-01", "vocab-000083-S1-03", "vocab-000083-S2-07"], "Neither old arm nor the two new query pools clearly teaches occasional frequency. Leave the image missing unless the owner finds a suitable candidate."),
}


def checked_asset(c):
    if not c or c["status"] != "DOWNLOADED":
        return None
    path = ROOT / c["image_path"]
    assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == c["image_sha256"], c["candidate_id"]
    return c


def asset_html(cid, role):
    c = checked_asset(candidate.get(cid))
    if not c:
        return "<p>Không có ảnh</p>"
    src = "../../../" + c["image_path"]
    q = c.get("query_score")
    meaning = scores.get(cid, {}).get("post_fix_meaning_score")
    detail = " · ".join(x for x in [f"SigLIP(query) {q:.3f}" if q is not None else "Chưa chấm SigLIP",
                                    f"SigLIP(nghĩa) {float(meaning):.3f}" if meaning else ""] if x)
    source = c.get("source_url")
    link = f'<a href="{html.escape(source, quote=True)}" target="_blank" rel="noreferrer">Nguồn ảnh</a>' if source else "Nguồn chưa có"
    return (f'<figure><img src="{html.escape(src, quote=True)}" alt="{html.escape(role + " " + cid)}" loading="lazy">'
            f'<figcaption><strong>{html.escape(cid)}</strong><br>{html.escape(detail)}<br>{link}<br>'
            f'SHA-256 {html.escape(c["image_sha256"][:16])}…</figcaption></figure>')


rows = []
cards = []
for item in feedback["feedback"]:
    vid = item["vocab_id"]
    old_id, proposed_id, alternatives, reason = plans[vid]
    row = sample[vid]
    old = checked_asset(candidate[old_id])
    proposed = checked_asset(candidate.get(proposed_id))
    baseline_path = row["a001_image_path"]
    assert (ROOT / baseline_path).is_file()
    assert hashlib.sha256((ROOT / baseline_path).read_bytes()).hexdigest() == row["a001_image_sha256"]
    rows.append({
        "vocab_id": vid, "english": row["english"], "japanese": row["japanese"], "vietnamese": row["vietnamese"],
        "owner_statement": item["statement"], "owner_ab_preference": item["preference"] or "UNSPECIFIED",
        "a001_baseline_path": baseline_path, "a001_baseline_sha256": row["a001_image_sha256"],
        "comparison_current_candidate_id": old_id, "comparison_current_path": old["image_path"],
        "comparison_current_sha256": old["image_sha256"],
        "proposed_candidate_id": proposed_id or "", "proposed_path": proposed["image_path"] if proposed else "",
        "proposed_sha256": proposed["image_sha256"] if proposed else "",
        "proposed_source_url": proposed["source_url"] if proposed else "",
        "proposed_query_score": proposed.get("query_score") if proposed else "",
        "proposed_meaning_score": scores.get(proposed_id, {}).get("post_fix_meaning_score", "") if proposed else "",
        "proposed_outcome": "CANDIDATE_FOR_REVIEW" if proposed else "NO_SUITABLE_IMAGE",
        "approval_state": "OWNER_REVIEW_PENDING", "reason": reason,
    })
    extras = "".join(asset_html(cid, "Ứng viên khác") for cid in alternatives)
    extra_section = f'<details><summary>Ứng viên liên quan ({len(alternatives)})</summary><div class="extra">{extras}</div></details>' if alternatives else ""
    proposed_html = asset_html(proposed_id, "Đề xuất") if proposed_id else '<div class="empty">NO_SUITABLE_IMAGE<br><small>Không ép chọn ảnh từ các ứng viên hiện có.</small></div>'
    baseline_html = (f'<details><summary>Ảnh A-001 baseline</summary><img class="baseline" src="{html.escape("../../../" + baseline_path, quote=True)}" '
                     f'alt="Ảnh A-001 {html.escape(row["english"])}"></details>')
    cards.append(f'''<article id="{vid}"><header><h2>{html.escape(row["english"])} <small>{html.escape(vid)}</small></h2>
      <p><strong>Nghĩa:</strong> {html.escape(row["japanese"])} · {html.escape(row["vietnamese"])}</p>
      <p><strong>Chủ dự án:</strong> {html.escape(item["statement"])} <span class="tag">{html.escape(item["preference"] or "Chưa chọn A/B")}</span></p></header>
      <div class="pair"><section><h3>Ảnh đang so sánh</h3>{asset_html(old_id, "Hiện tại")}</section>
      <section><h3>Đề xuất để duyệt</h3>{proposed_html}</section></div>
      <p class="reason"><strong>Lý do:</strong> {html.escape(reason)}</p>{extra_section}{baseline_html}
      <div class="review"><label>Quyết định
        <select data-id="{vid}" data-field="decision"><option value="">— Chưa chọn —</option>
        <option>ACCEPT_PROPOSED</option><option>KEEP_ORIGINAL</option><option>NONE_SUITABLE</option><option>NEEDS_REVIEW</option></select></label>
        <label>Ghi chú <textarea data-id="{vid}" data-field="notes"></textarea></label></div></article>''')

with (HERE / "proposed_image_selections.csv").open("w", encoding="utf-8-sig", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

meta = {"task_id": "A-003.2", "kind": "HUMAN_REVIEW_DRAFT_NOT_AUTO_APPROVAL", "proposals": [
    {"vocab_id": r["vocab_id"], "proposed_candidate_id": r["proposed_candidate_id"],
     "proposed_sha256": r["proposed_sha256"], "proposed_outcome": r["proposed_outcome"]} for r in rows]}
embedded = json.dumps(meta, ensure_ascii=False).replace("<", "\\u003c")
page = f'''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self' file:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'">
<title>A-003.2 · Duyệt ảnh chọn lọc</title><style>
:root{{--bg:#f5f6f5;--paper:#fff;--ink:#1b252b;--muted:#53616b;--line:#c8d1d3;--accent:#155e63}}
*{{box-sizing:border-box}}body{{max-width:1100px;margin:auto;padding:1rem;font:16px/1.5 system-ui,sans-serif;color:var(--ink);background:var(--bg)}}
h1{{font-size:1.7rem;margin:.2rem 0}}h2{{font-size:1.35rem;margin:.2rem 0}}h3{{font-size:1rem;margin:0 0 .5rem}}small{{font-size:.78rem;color:var(--muted)}}
header p{{margin:.35rem 0}}article{{background:var(--paper);border:1px solid var(--line);padding:1rem;margin:1rem 0}}.top{{background:var(--paper);border:1px solid var(--line);padding:1rem}}.tag{{border:1px solid var(--line);padding:.1rem .4rem;white-space:nowrap}}
.pair{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}}.pair section{{min-width:0}}figure{{margin:0}}figure img{{display:block;width:100%;height:240px;object-fit:contain;background:#e5e9e9}}figcaption{{font-size:.78rem;overflow-wrap:anywhere;color:var(--muted);margin:.35rem 0}}.reason{{border-left:3px solid var(--accent);padding-left:.7rem}}
.extra{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:.75rem;margin:.5rem 0}}.extra img{{height:150px}}.baseline{{max-width:100%;max-height:200px;object-fit:contain}}.empty{{min-height:240px;display:grid;place-content:center;text-align:center;background:#f0f2ef;border:1px dashed var(--line)}}
.review{{display:grid;grid-template-columns:minmax(180px,300px) 1fr;gap:1rem;margin-top:1rem}}label{{display:grid;gap:.25rem;font-weight:600}}select,textarea,input,button{{font:inherit;padding:.45rem;color:var(--ink)}}textarea{{min-height:4rem}}button{{background:var(--accent);color:white;border:0;cursor:pointer}}button:focus-visible,select:focus-visible,textarea:focus-visible,input:focus-visible,a:focus-visible,summary:focus-visible{{outline:3px solid #bf7e1c;outline-offset:2px}}
@media(max-width:700px){{.pair,.review{{grid-template-columns:1fr}}}}
</style><main><div class="top"><h1>A-003.2 · Duyệt ảnh chọn lọc</h1><p>Chỉ là đề xuất nội bộ; chưa ảnh nào được duyệt để đưa vào dữ liệu production. Chọn quyết định, nhập tên người duyệt, rồi xuất JSON.</p>
<label>Người duyệt <input id="reviewer" autocomplete="name"></label><p><button id="export" type="button">Export JSON</button> <small>Bản nháp được lưu trong trình duyệt này.</small></p></div>
{''.join(cards)}</main><script id="meta" type="application/json">{embedded}</script><script>
const key='A003_SELECTIVE_REPAIR_DRAFT_V1';let draft={{}};try{{draft=JSON.parse(localStorage.getItem(key)||'{{}}')}}catch{{}}
document.querySelectorAll('[data-id]').forEach(el=>{{const id=el.dataset.id,field=el.dataset.field;el.value=draft[id]?.[field]||'';
el.addEventListener('input',()=>{{draft[id]??={{}};draft[id][field]=el.value;try{{localStorage.setItem(key,JSON.stringify(draft))}}catch{{}}}})}});
document.getElementById('export').addEventListener('click',()=>{{const reviewer=document.getElementById('reviewer').value.trim();if(!reviewer){{alert('Nhập tên người duyệt');return}}
const reviews=Object.fromEntries(Object.entries(draft).filter(([id,v])=>v.decision).map(([id,v])=>[id,{{decision:v.decision,notes:v.notes||''}}]));
const out={{...JSON.parse(document.getElementById('meta').textContent),reviewer,exported_at:new Date().toISOString(),reviews}};
const url=URL.createObjectURL(new Blob([JSON.stringify(out,null,2)],{{type:'application/json'}}));const a=document.createElement('a');a.href=url;a.download='A003-selective-repair-review.json';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000)}});
</script></html>'''
(HERE / "review_gallery.html").write_text(page, encoding="utf-8")
print("Rendered", len(rows), "items")
