"""Isolated 100-card owner follow-up: retain fixed images, search unresolved items once."""
import argparse
import csv
import hashlib
import html
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "A004R_CONDITIONAL_100"
sys.path.insert(0, str(ROOT / "collect data script"))
import imagecollector as image
from image_scorer import SiglipImageScorer

SOURCE_EXPORT = Path("D:/Download/A004R-review-2026-11-23.json")
EXPORT_COPY = HERE / "owner_review_export.json"
PLAN = HERE / "followup_plan.json"
RESULTS = HERE / "retrieval_results.json"
GALLERY = HERE / "review_gallery.html"
QUERY = {
    18: "sun in blue sky illustration", 33: "single desktop computer isolated white background",
    36: "family parents children portrait illustration", 38: "two friends together illustration",
    41: "today calendar current day highlighted illustration", 42: "tomorrow next day calendar illustration",
    43: "yesterday previous day calendar illustration", 47: "easy task simple puzzle illustration",
    48: "difficult task challenging puzzle illustration", 50: "strong arm muscle icon",
    51: "person walking away icon", 52: "person reading book icon",
    54: "student studying at desk icon", 55: "person working at desk icon",
    57: "person eating food icon", 60: "helping hand icon", 64: "choosing between options icon",
    66: "software application screen icon", 70: "language speech bubbles icon",
    72: "business meeting icon", 74: "project plan teamwork illustration",
    75: "learning from experience illustration", 77: "important exclamation mark icon",
    78: "different objects comparison icon", 79: "danger warning sign icon",
    80: "impossible blocked action icon", 82: "always repeating arrow icon",
    84: "people together icon", 85: "where location question mark icon",
    86: "thinking why question mark icon", 87: "person waving hello icon",
    88: "person asking politely icon", 89: "person thanking another icon",
    92: "dictionary book icon",
}
A001_PASS = {7, 10, 83, 96, 100}
OWNER_FIXED = {21, 31, 46, 59, 63}
INTERNAL_FIXED = {81}
CONFLICT = {36, 57}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(temp, path)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def checked_asset(path, digest):
    if not path or not digest or not isinstance(path, str) or Path(path).is_absolute() or ".." in Path(path).parts:
        raise ValueError(f"Unsafe/missing image path: {path}")
    target = (ROOT / path).resolve()
    if not target.is_relative_to(ROOT.resolve()) or not target.is_file() or sha(target) != digest:
        raise ValueError(f"Image path/hash mismatch: {path}")
    return {"path": path, "sha256": digest}


def prepare(export_path=SOURCE_EXPORT):
    owner = read(export_path)
    routes = {r["vocab_id"]: r for r in csv.DictReader((PRIOR / "routing_matrix.csv").open(encoding="utf-8-sig", newline=""))}
    previous = read(PRIOR / "retrieval_results.json")
    prior_manifest = read(PRIOR / "experiment_manifest.json")
    if owner.get("task_id") != "A-004R" or owner.get("routing_sha256") != prior_manifest["routing_matrix_sha256"] or owner.get("dataset_sha256") != prior_manifest["dataset_sha256"]:
        raise ValueError("Owner export does not match frozen A-004R routing/dataset")
    reviews = owner.get("reviews")
    if not isinstance(reviews, list) or len(reviews) != 100 or len({r["vocab_id"] for r in reviews}) != 100 or {r["vocab_id"] for r in reviews} != set(routes) == set(previous):
        raise ValueError("Owner export must contain exactly the 100 frozen IDs")
    by_id = {r["vocab_id"]: r for r in reviews}
    items = []
    for vid, route in routes.items():
        review = by_id[vid]
        number = int(vid[-6:])
        selected = review.get("selected_candidate_id") or ""
        label = review.get("image_label")
        if label not in {"PASS", "FAIL", "NEEDS_REVIEW", "UNREVIEWED"}:
            raise ValueError(f"Invalid image label: {vid}")
        fixed = None
        if selected and selected != "NO_SUITABLE_IMAGE":
            matches = [c for c in previous[vid]["candidates"] if c["candidate_id"] == selected and c["download_status"] == "SUCCESS"]
            if len(matches) != 1:
                raise ValueError(f"Unknown/unavailable selected candidate: {vid} {selected}")
            candidate = matches[0]
            if review.get("selected_jpeg_path") != candidate["jpeg_path"] or review.get("selected_jpeg_sha256") != candidate["jpeg_sha256"]:
                raise ValueError(f"Exported candidate/path/hash mismatch: {vid}")
            checked_asset(candidate["jpeg_path"], candidate["jpeg_sha256"])
            if label == "PASS":
                fixed = {"candidate_id": selected, "source": "A004R_OWNER_PASS", **checked_asset(candidate["jpeg_path"], candidate["jpeg_sha256"])}
        elif selected == "NO_SUITABLE_IMAGE":
            if review.get("selected_jpeg_path") or review.get("selected_jpeg_sha256"):
                raise ValueError(f"NO_SUITABLE_IMAGE must not point to a file: {vid}")
        elif review.get("selected_jpeg_path") or review.get("selected_jpeg_sha256"):
            raise ValueError(f"Unselected row contains image path/hash: {vid}")
        if number in A001_PASS and label == "PASS" and not selected:
            fixed = {"candidate_id": "A001_REFERENCE", "source": "A001_OWNER_PASS", **checked_asset(route["a001_image_path"], route["a001_image_sha256"])}
        if number in OWNER_FIXED:
            fixed = {"candidate_id": route["owner_candidate_id"], "source": "A003_OWNER_DECISION", **checked_asset(route["owner_image_path"], route["owner_image_sha256"])}
        if number in INTERNAL_FIXED:
            fixed = {"candidate_id": route["owner_candidate_id"], "source": "INTERNAL_ONLY_TEMPORARY", **checked_asset(route["owner_image_path"], route["owner_image_sha256"])}
        if number in CONFLICT:
            fixed = None
        if fixed and number == 83:
            fixed["supersedes_quality_decision"] = "A003_NO_SUITABLE_IMAGE; new owner PASS requests A001 reference"
        if not fixed and number not in QUERY:
            raise ValueError(f"Unresolved ID missing query plan: {vid}")
        if fixed and number in QUERY:
            raise ValueError(f"Fixed ID also scheduled for search: {vid}")
        reference = None
        if not fixed and route.get("a001_image_path") and route.get("a001_image_sha256"):
            reference = checked_asset(route["a001_image_path"], route["a001_image_sha256"])
        items.append({"vocab_id": vid, "english": route["english"], "japanese": route["japanese"],
                      "vietnamese": route["vietnamese"], "prior_label": label, "owner_note": review.get("notes") or "",
                      "prior_selected_candidate_id": selected, "fixed": fixed, "a001_reference": reference,
                      "query": QUERY.get(number), "strategy": "ICON" if QUERY.get(number, "").endswith(" icon") else "SCENE" if not fixed else "KEEP"})
    if len(items) != 100 or sum(bool(i["fixed"]) for i in items) != 66 or sum(not i["fixed"] for i in items) != 34:
        raise ValueError("Unexpected fixed/unresolved count")
    plan = {"task_id": "A004R_OWNER_FOLLOWUP_100", "source_export_sha256": sha(export_path),
            "source_routing_sha256": owner["routing_sha256"], "dataset_sha256": owner["dataset_sha256"],
            "source_retrieval_sha256": sha(PRIOR / "retrieval_results.json"),
            "fixed_count": 66, "search_count": 34, "rights": "UNKNOWN; because INTERNAL_ONLY_TEMPORARY",
            "items": items}
    if PLAN.exists() or EXPORT_COPY.exists():
        raise ValueError("Frozen follow-up plan already exists; refusing overwrite")
    shutil.copyfile(export_path, EXPORT_COPY)
    save(PLAN, plan)
    save(RESULTS, {})
    return plan


# Owner notes that the frozen rules missed. Applied by `amend` with an audit record; the plan is not refrozen.
AMENDMENTS = {
    66: {"action": "A001_REFERENCE", "reason": "owner note 'lấy ảnh A001' with label UNREVIEWED; the A001_PASS rule only matched PASS labels"},
}


# One-time query repairs after the follow-up run: these queries produced no usable candidate for a
# technical/query reason (word collision or a single result), not an owner taste decision.
QUERY_REPAIRS = {
    33: ("desktop computer monitor keyboard icon", "'single' in the query returned 'Being Single' quote images"),
    60: ("person helping another person icon", "only 1 result (sticker sheet)"),
    79: ("danger warning triangle sign icon", "only 1 result (text poster)"),
    80: ("impossible task icon", "'blocked action' returned rifle images (Action brand collision)"),
}


def repair_queries():
    plan = read(PLAN)
    results = read(RESULTS)
    done = {a["vocab_id"] for a in plan.get("amendments", []) if a["action"] == "QUERY_REPAIR"}
    targets = []
    for number, (query, reason) in QUERY_REPAIRS.items():
        vid = f"vocab-{number:06d}"
        item = next(i for i in plan["items"] if i["vocab_id"] == vid)
        if vid in done or item["fixed"]:
            continue
        before = {"query": item["query"], "result_status": results.get(vid, {}).get("status"),
                  "valid_candidates": sum(c["download_status"] == "SUCCESS" for c in results.get(vid, {}).get("candidates", []))}
        item.update(superseded_query=item["query"], query=query,
                    strategy="ICON" if query.endswith(" icon") else "SCENE")
        plan.setdefault("amendments", []).append({"vocab_id": vid, "action": "QUERY_REPAIR", "reason": reason,
                                                   "before": before, "applied_at": datetime.now(timezone.utc).isoformat()})
        targets.append(vid)
    save(PLAN, plan)
    return run(only_ids=set(targets)) if targets else results


def amend():
    plan = read(PLAN)
    if sha(EXPORT_COPY) != plan["source_export_sha256"]:
        raise ValueError("Frozen owner export changed")
    routes = {r["vocab_id"]: r for r in csv.DictReader((PRIOR / "routing_matrix.csv").open(encoding="utf-8-sig", newline=""))}
    done = {a["vocab_id"] for a in plan.get("amendments", [])}
    for number, change in AMENDMENTS.items():
        vid = f"vocab-{number:06d}"
        if vid in done:
            continue
        item = next(i for i in plan["items"] if i["vocab_id"] == vid)
        if change["action"] != "A001_REFERENCE" or "A001" not in item["owner_note"].replace(" ", "").upper():
            raise ValueError(f"Amendment does not match owner note: {vid}")
        route = routes[vid]
        before = {"fixed": item["fixed"], "query": item["query"], "strategy": item["strategy"]}
        item.update(fixed={"candidate_id": "A001_REFERENCE", "source": "A001_OWNER_NOTE",
                           **checked_asset(route["a001_image_path"], route["a001_image_sha256"])},
                    strategy="KEEP", superseded_query=item["query"], query=None)
        plan.setdefault("amendments", []).append({"vocab_id": vid, **change, "before": before,
                                                   "applied_at": datetime.now(timezone.utc).isoformat()})
    plan["fixed_count"] = sum(bool(i["fixed"]) for i in plan["items"])
    plan["search_count"] = sum(bool(i["query"]) for i in plan["items"])
    save(PLAN, plan)
    return plan


def run(limit=None, retry_failed=False, only_ids=None):
    plan = read(PLAN)
    if sha(EXPORT_COPY) != plan["source_export_sha256"] or sha(PRIOR / "retrieval_results.json") != plan["source_retrieval_sha256"]:
        raise ValueError("Frozen source changed")
    results = read(RESULTS)
    if only_ids:
        pending = [item for item in plan["items"] if item["query"] and item["vocab_id"] in only_ids]
    elif retry_failed:
        # Retry only searches that failed before any candidate existed (timeouts); keep the failed attempt.
        pending = [item for item in plan["items"] if item["query"] and results.get(item["vocab_id"], {}).get("status") == "FAILED"
                   and not results[item["vocab_id"]]["candidates"]]
    else:
        pending = [item for item in plan["items"] if item["query"] and item["vocab_id"] not in results]
    if limit is not None:
        pending = pending[:limit]
    scorer = None
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    for item in pending:
        vid, query = item["vocab_id"], item["query"]
        history = []
        if vid in results:
            old = results[vid]
            history = old.pop("previous_attempts", []) + [old]
        result = {"vocab_id": vid, "query": query, "strategy": item["strategy"], "status": "ATTEMPTED",
                  "search_attempted": False, "score_attempted": False, "candidates": [], "error": None,
                  "search_retries": 2 if (retry_failed or only_ids) else 0,
                  "attempted_at": datetime.now(timezone.utc).isoformat()}
        if history:
            result["previous_attempts"] = history
        results[vid] = result
        save(RESULTS, results)
        try:
            if scorer is None:
                scorer = SiglipImageScorer(device="auto", dtype="auto")
            result["search_attempted"] = True
            save(RESULTS, results)
            found = image.search_images(query, page_size=7, timeout=20, retries=result["search_retries"],
                                        retry_delay=2, backend="auto")
            result["raw_result_count"] = found.raw_count
            result["search_backend"] = found.backend
            # Attempts that replace earlier downloaded candidates get their own folder/IDs so old hashes stay valid.
            attempt = 1 + sum(1 for h in history if h.get("candidates"))
            suffix = "" if attempt == 1 else f"-R{attempt}"
            for n, source in enumerate(found.candidates[:7], 1):
                c = {"candidate_id": f"{vid}-FOLLOWUP{suffix}-{n:02d}", "retrieval_rank": n, "source": source,
                     "download_status": "NOT_ATTEMPTED", "raw_path": None, "raw_sha256": None,
                     "jpeg_path": None, "jpeg_sha256": None, "siglip_score": None, "error": None}
                result["candidates"].append(c)
            save(RESULTS, results)
            paths = []
            for c in result["candidates"]:
                folder = HERE / "images" / vid / (f"attempt{attempt}" if attempt > 1 else "")
                folder.mkdir(parents=True, exist_ok=True)
                raw = folder / f'{c["retrieval_rank"]:02d}.img'
                jpeg = folder / f'{c["retrieval_rank"]:02d}.jpg'
                c["download_status"] = "ATTEMPTED"
                save(RESULTS, results)
                try:
                    image.download_candidate_image(c["source"]["image_url"], raw, timeout=20, retries=0, retry_delay=2)
                    image.normalize_image_to_jpeg(raw, jpeg)
                    c.update(download_status="SUCCESS", raw_path=raw.relative_to(ROOT).as_posix(),
                             raw_sha256=sha(raw), jpeg_path=jpeg.relative_to(ROOT).as_posix(), jpeg_sha256=sha(jpeg))
                    paths.append(raw)
                except Exception as exc:
                    c.update(download_status="FAILED", error=f"{type(exc).__name__}: {exc}")
                save(RESULTS, results)
            if paths:
                result["score_attempted"] = True
                save(RESULTS, results)
                scores = {str(s.image_path): float(s.score) for s in scorer.score_batch(query, paths)}
                valid = []
                for c in result["candidates"]:
                    if c["download_status"] == "SUCCESS":
                        c["siglip_score"] = scores[str(ROOT / c["raw_path"])]
                        valid.append(c)
                for rank, c in enumerate(sorted(valid, key=lambda c: c["siglip_score"], reverse=True), 1):
                    c["siglip_rank"] = rank
                result["status"] = "RANKED" if valid else "NO_VALID_CANDIDATES"
            else:
                result["status"] = "NO_VALID_CANDIDATES"
        except Exception as exc:
            result.update(status="FAILED", error=f"{type(exc).__name__}: {exc}")
        result["finished_at"] = datetime.now(timezone.utc).isoformat()
        save(RESULTS, results)
        print(vid, query, result["status"], flush=True)
    return results


def prior_choices(vid):
    """Earlier images the owner already saw: A-003 owner reference and valid A-004R candidates (hash-checked)."""
    prior = read(PRIOR / "retrieval_results.json")[vid]
    out = []
    if prior.get("owner_image_path") and prior.get("owner_image_sha256"):
        ref = checked_asset(prior["owner_image_path"], prior["owner_image_sha256"])
        out.append(("PRIOR_OWNER_REFERENCE", ref["path"], ref["sha256"], f'Ảnh đã chọn trước ({prior.get("owner_candidate_id")})'))
    for c in prior.get("candidates", []):
        if c.get("download_status") == "SUCCESS" and c.get("jpeg_path"):
            checked_asset(c["jpeg_path"], c["jpeg_sha256"])
            out.append((c["candidate_id"], c["jpeg_path"], c["jpeg_sha256"], "Ứng viên A-004R trước"))
    return out


_THUMBS = {}


def thumb(path, size=(320, 320)):
    """Embed a small JPEG thumbnail so the gallery renders in viewers that cannot load sibling files."""
    if path not in _THUMBS:
        import base64
        import io
        from PIL import Image
        with Image.open(ROOT / path) as source:
            small = source.convert("RGB")
            small.thumbnail(size)
            buffer = io.BytesIO()
            small.save(buffer, format="JPEG", quality=72, optimize=True)
        _THUMBS[path] = "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
    return _THUMBS[path]


def render():
    plan, results = read(PLAN), read(RESULTS)
    esc = lambda value: html.escape(str(value or ""), quote=True)
    cards, meta = [], {}
    for item in plan["items"]:
        vid, fixed = item["vocab_id"], item["fixed"]
        if fixed:
            cards.append(f'<article class="card fixed" data-id="{vid}"><h2>{vid} · {esc(item["english"])}</h2><p>{esc(item["japanese"])} · {esc(item["vietnamese"])}</p><p>Đã giữ ảnh PASS ({esc(fixed["source"])}); không hiển thị ứng viên thừa.</p><img src="{thumb(fixed["path"])}" alt="Ảnh đã chọn cho {esc(item["english"])}" title="{esc(fixed["path"])}"><p>{esc(item["owner_note"])}</p></article>')
            meta[vid] = {"fixed": fixed, "candidates": {}}
            continue
        result = results.get(vid, {})
        choices = []
        if item["a001_reference"]:
            ref = item["a001_reference"]
            choices.append(("A001_REFERENCE", ref["path"], ref["sha256"], "Ảnh A-001 để đối chiếu"))
        choices += prior_choices(vid)
        for c in sorted((c for c in result.get("candidates", []) if c["download_status"] == "SUCCESS"), key=lambda c: c.get("siglip_rank", 999)):
            choices.append((c["candidate_id"], c["jpeg_path"], c["jpeg_sha256"], f'#{c["siglip_rank"]} · SigLIP {c["siglip_score"]:.3f}'))
        options = '<option value="">Chưa chọn</option>' + ''.join(f'<option value="{esc(cid)}">{esc(cid)}</option>' for cid, *_ in choices) + '<option value="NO_SUITABLE_IMAGE">NO_SUITABLE_IMAGE</option>'
        thumbs = ''.join(f'<button type="button" class="choice" data-candidate="{esc(cid)}" aria-pressed="false"><img src="{thumb(path)}" alt="{esc(item["english"])} · {esc(cid)}" title="{esc(path)}"><span>{esc(cid)}<br>{esc(label)}</span></button>' for cid, path, _, label in choices)
        cards.append(f'<article class="card" data-id="{vid}"><h2>{vid} · {esc(item["english"])}</h2><p>{esc(item["japanese"])} · {esc(item["vietnamese"])} · {esc(item["strategy"])} · truy vấn: {esc(item["query"])}</p><p>Trước đó: {esc(item["prior_label"])}; {esc(item["owner_note"])}</p><div class="choices">{thumbs or "<p>Chưa có ảnh hợp lệ.</p>"}</div><label>Chọn ảnh <select data-field="selected_candidate_id">{options}</select></label><label>Đánh giá <select data-field="image_label"><option>UNREVIEWED</option><option>PASS</option><option>FAIL</option><option>NEEDS_REVIEW</option></select></label><label>Ghi chú <textarea data-field="notes" rows="2"></textarea></label></article>')
        meta[vid] = {"fixed": None, "candidates": {cid: {"jpeg_path": path, "jpeg_sha256": digest} for cid, path, digest, _ in choices}}
    metadata = json.dumps({"task_id": plan["task_id"], "source_export_sha256": plan["source_export_sha256"], "items": meta}, ensure_ascii=False).replace("<", "\\u003c")
    page = '''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>A-004R · Đánh giá tiếp 100 từ</title><style>
:root{font:16px/1.45 system-ui,sans-serif;color:#1b2926;background:#eef2f0}*{box-sizing:border-box}body{margin:0}.toolbar{position:sticky;top:0;background:#fff;padding:12px;display:flex;gap:12px;align-items:end;flex-wrap:wrap;z-index:2;border-bottom:1px solid #cbd5d2}label{display:grid;gap:4px}input,select,textarea,button{font:inherit;padding:7px;border:1px solid #879992;border-radius:4px;background:#fff}button{cursor:pointer}main{max-width:1300px;margin:auto;padding:16px}.card{background:#fff;border:1px solid #cbd5d2;margin:16px 0;padding:16px}.card.fixed{border-left:5px solid #27765c}.card>img{max-width:240px;max-height:190px;object-fit:contain}.choices{display:grid;grid-template-columns:repeat(auto-fill,minmax(175px,1fr));gap:10px;margin:12px 0}.choice{text-align:left;overflow-wrap:anywhere}.choice img{display:block;width:100%;height:145px;object-fit:contain}.choice span{font-size:.8rem}.choice[aria-pressed=true]{border:3px solid #27765c;background:#e0f2e9}.card label{margin:8px 0}.card textarea{width:100%}[hidden]{display:none!important}</style></head><body><div class="toolbar"><label>Tìm từ<input id="search"></label><label>Hiển thị<select id="filter"><option value="all">Tất cả</option><option value="open">Cần đánh giá</option><option value="fixed">Đã giữ PASS</option></select></label><label>Người duyệt<input id="reviewer"></label><button id="export">Export JSON</button><span id="count"></span></div><main><h1>Đánh giá tiếp 100 từ</h1><p>''' + f'{sum(bool(i["fixed"]) for i in plan["items"])} ảnh đã chốt được giữ lại và chỉ hiện một ảnh; {sum(not i["fixed"] for i in plan["items"])} từ cần xem lại' + ''' có ảnh A-001 tham chiếu, ảnh đã chọn/ứng viên trước đó (nếu có) và ứng viên mới nếu truy xuất thành công. Chọn PASS chỉ khi ảnh đúng nghĩa; nếu không có ảnh phù hợp chọn NO_SUITABLE_IMAGE. Điểm SigLIP chỉ là gợi ý. Quyền phát hành chưa được xác nhận.</p>''' + "\n".join(cards) + '''</main><script id="metadata" type="application/json">''' + metadata + '''</script><script>
const meta=JSON.parse(document.getElementById('metadata').textContent),key='A004R_FOLLOWUP_'+meta.source_export_sha256.slice(0,12),cards=[...document.querySelectorAll('.card')];let draft={};try{draft=JSON.parse(localStorage.getItem(key)||'{}')}catch{}for(const card of cards){if(card.classList.contains('fixed'))continue;const id=card.dataset.id,select=card.querySelector('[data-field="selected_candidate_id"]'),buttons=[...card.querySelectorAll('[data-candidate]')],sync=()=>buttons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.candidate===select.value)));for(const field of card.querySelectorAll('[data-field]')){if(draft[id]?.[field.dataset.field]!==undefined)field.value=draft[id][field.dataset.field];field.addEventListener('input',()=>{(draft[id]??={})[field.dataset.field]=field.value;try{localStorage.setItem(key,JSON.stringify(draft))}catch{}sync()})}buttons.forEach(b=>b.addEventListener('click',()=>{select.value=b.dataset.candidate;select.dispatchEvent(new Event('input',{bubbles:true}))}));sync()}
function update(){const q=document.getElementById('search').value.toLowerCase(),f=document.getElementById('filter').value;let n=0;for(const c of cards){c.hidden=!!q&&!c.textContent.toLowerCase().includes(q)||f==='open'&&c.classList.contains('fixed')||f==='fixed'&&!c.classList.contains('fixed');if(!c.hidden)n++}document.getElementById('count').textContent=n+' / '+cards.length}document.getElementById('search').addEventListener('input',update);document.getElementById('filter').addEventListener('change',update);update();document.getElementById('export').addEventListener('click',()=>{const reviewer=document.getElementById('reviewer').value.trim();if(!reviewer){alert('Nhập tên người duyệt');return}const reviews=cards.map(c=>{const id=c.dataset.id;if(meta.items[id].fixed)return{vocab_id:id,carried_forward:true,...meta.items[id].fixed};const v={};for(const f of c.querySelectorAll('[data-field]'))v[f.dataset.field]=f.value;const a=meta.items[id].candidates[v.selected_candidate_id]||null;return{vocab_id:id,carried_forward:false,...v,selected_jpeg_path:a?.jpeg_path||null,selected_jpeg_sha256:a?.jpeg_sha256||null}});const out={task_id:meta.task_id,source_export_sha256:meta.source_export_sha256,reviewer,exported_at:new Date().toISOString(),reviews},blob=new Blob([JSON.stringify(out,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='A004R-followup-review-'+new Date().toISOString().slice(0,10)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});
</script></body></html>'''
    GALLERY.write_text(page, encoding="utf-8", newline="\n")
    return {"cards": len(cards), "fixed": sum(bool(i["fixed"]) for i in plan["items"]), "searched": len(results)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("freeze", "amend", "run", "retry", "repair", "render", "verify"))
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.phase == "freeze":
        result = prepare()
        print("Frozen", len(result["items"]), "IDs; fixed", result["fixed_count"], "search", result["search_count"])
    elif args.phase == "amend":
        result = amend()
        print("Amended", [a["vocab_id"] for a in result.get("amendments", [])], "fixed", result["fixed_count"], "search", result["search_count"])
    elif args.phase == "run":
        run(args.limit)
    elif args.phase == "retry":
        run(args.limit, retry_failed=True)
    elif args.phase == "repair":
        repair_queries()
    elif args.phase == "render":
        print(render())
    else:
        plan = read(PLAN)
        if sha(EXPORT_COPY) != plan["source_export_sha256"] or len(plan["items"]) != 100:
            raise ValueError("Frozen owner export/plan mismatch")
        print("Verified", len(plan["items"]), "IDs; searches completed", len(read(RESULTS)))


if __name__ == "__main__":
    main()
