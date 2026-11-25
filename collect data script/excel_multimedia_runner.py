"""Run a private dual-language multimedia import from an Excel workbook.

Usage: python "collect data script/excel_multimedia_runner.py" words.xlsx
Resume: python "collect data script/excel_multimedia_runner.py" words.xlsx --resume RUN_DIR
"""
from __future__ import annotations

import argparse
import hashlib
import math
import json
import os
import shutil
import subprocess
import sys
import uuid
from collections import Counter
from pathlib import Path

from audiocollector import AUDIO_SOURCE, AUDIO_VOICE, synthesize_gtts_mp3, validate_audio
from collector_common import PROJECT_ROOT
from content_pack_builder import build_pack, source_pack, validate_pack
from excel_vocabulary_importer import accept, validate
from image_pipeline_v2 import load_approved, process_item, sha256 as file_hash
from import_pipeline_adapter import build_manifest, check_import
import visual_query_policy as policy
from visual_query_policy import lookup_key

OUTPUT_ROOT = PROJECT_ROOT / "reports" / "EXCEL_FULL_PIPELINE_FINAL"


def historical_no_suitable() -> set[str]:
    decisions = load(PROJECT_ROOT / "reports" / "image_pipeline_experiments" / "A003_OWNER_DECISIONS" / "final_image_selection_manifest.json")
    return {lookup_key(row["english"], row["japanese"], row["vietnamese"])
            for row in decisions["no_suitable_image_outcomes"] if row["outcome"] == "NO_SUITABLE_IMAGE"}


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def put_asset(source: Path, root: Path, kind: str, provider: str | None = None) -> dict:
    data = source.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    extension = "jpg" if kind == "image" else "mp3"
    target = root / "assets" / f"{digest}.{extension}"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if file_hash(target) != digest:
            raise ValueError(f"Asset hash conflict: {target.name}")
    else:
        temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
        try:
            shutil.copyfile(source, temporary)
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    return {"path": target.relative_to(root).as_posix(), "mime_type": "image/jpeg" if kind == "image" else "audio/mpeg",
            "sha256": digest, "size_bytes": len(data), "source": {"provider": provider, "url": None, "query": None, "model": None, "revision": None}}


def selected_image_candidate(result: dict, root: Path, item_id: str) -> dict | None:
    """Accept a scored, technically usable proposal only from this item's isolated folder."""
    if result.get("status") not in {"PROPOSED", "AUTO_SELECTED_NEEDS_REVIEW"}:
        return None
    chosen = next((c for c in result.get("candidates", [])
                   if c.get("candidate_id") == result.get("proposed_candidate_id")), None)
    if not chosen or chosen.get("status") != "DOWNLOADED" or chosen.get("rejection"):
        return None
    score = chosen.get("score")
    if not isinstance(score, (int, float)) or not math.isfinite(score):
        return None
    source = Path(chosen["jpeg_path"]).resolve()
    if not source.is_relative_to((root / "image_candidates" / item_id).resolve()):
        raise ValueError(f"Proposed image path escapes item folder: {item_id}")
    if not source.is_file() or file_hash(source) != chosen.get("jpeg_sha256"):
        raise ValueError(f"Proposed image bytes/hash mismatch: {item_id}")
    return chosen


def classify_import_word(word: str, generator):
    """Keep the frozen classifier, with a bounded workaround for multiword concrete terms."""
    from query_generator import QueryGenerationError
    try:
        return policy.classify_words([word], generator)[0], None
    except QueryGenerationError as exc:
        if " " not in word or "concrete query must name the word" not in str(exc):
            raise
        return policy.TypedQuery(word, "CONCRETE", "PHOTO", policy.normalize_query(f"{word} photo")), "MULTIWORD_PHOTO_FALLBACK"


def process_new_images(rows: list[dict], candidate_dir: Path, images: dict, approved: dict, manifest_path: Path):
    """Classify once with Qwen, then persist each frozen-pipeline search/rank result."""
    from query_generator import QwenQueryGenerator
    from image_scorer import SiglipImageScorer
    typed, failures, fallbacks = {}, {}, {}
    generator = QwenQueryGenerator(batch_size=2)
    try:
        for row in rows:
            try:
                typed[row["item_id"]], fallbacks[row["item_id"]] = classify_import_word(row["english"], generator)
            except Exception as exc:
                failures[row["item_id"]] = f"{type(exc).__name__}: {exc}"
    finally:
        generator.close()
    try:
        scorer = SiglipImageScorer() if any(t.route != "CURATE" for t in typed.values()) else None
        scorer_error = None
    except Exception as exc:
        scorer, scorer_error = None, f"{type(exc).__name__}: {exc}"
    for row in rows:
        item_id = row["item_id"]
        if item_id in failures or scorer_error and item_id in typed and typed[item_id].route != "CURATE":
            result = {"item_id": item_id, "english": row["english"], "status": "QUERY_FAILED" if item_id in failures else "SCORING_FAILED",
                      "error": failures.get(item_id) or scorer_error, "candidates": []}
        else:
            try:
                result = process_item(row, candidate_dir, typed=typed[item_id], scorer=scorer, approved=approved)
                if fallbacks[item_id]:
                    result["query_fallback"] = fallbacks[item_id]
            except Exception as exc:
                result = {"item_id": item_id, "english": row["english"], "status": "IMAGE_FAILED",
                          "error": f"{type(exc).__name__}: {exc}", "candidates": []}
        images[item_id] = result
        save_json(candidate_dir / "results.json", [images[r["item_id"]] for r in rows if r["item_id"] in images])
        save_json(manifest_path, list(images.values()))


def japanese_cache() -> dict[str, Path]:
    """Index only legacy assets whose metadata binds locale, text and path."""
    index = {}
    root = PROJECT_ROOT.resolve()
    accepted = {entry["path"]: entry["sha256"] for entry in load(PROJECT_ROOT / "reports" / "phase0_quality_review" / "a001_20261122" / "owner_audio_acceptance.json")["items"]}
    for meta in (PROJECT_ROOT / "baseline" / "media-staging" / "audio").glob("*/_metadata/*.json"):
        try:
            record = load(meta)
            source = (root / record["audio"]).resolve()
            if (record.get("locale") == "ja" and record.get("reading") == record.get("word")
                    and record.get("source") == AUDIO_SOURCE and record.get("voice") == AUDIO_VOICE
                    and source.is_relative_to(root) and source.is_file()
                    and accepted.get(source.relative_to(root).as_posix()) == file_hash(source)):
                check = validate_audio(source)
                if check.ok and check.size == record.get("size") and abs(check.duration_seconds - record.get("duration_seconds", -1)) < 0.02:
                    index.setdefault(record["reading"], source)
        except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError):
            continue
    return index


def make_audio(item_id: str, locale: str, text: str, root: Path, cache: dict[str, Path], *, force=False) -> dict:
    if locale not in {"en", "ja"} or not text:
        raise ValueError("Audio requires English or Japanese source text")
    folder = root / "audio"
    folder.mkdir(parents=True, exist_ok=True)
    output = folder / f"{item_id}-{locale}.mp3"
    metadata = folder / f"{item_id}-{locale}.json"
    if output.exists() or metadata.exists():
        if not output.is_file() or not metadata.is_file():
            raise ValueError("Incomplete existing audio; preserved for inspection")
        old = load(metadata)
        check = validate_audio(output)
        if (old.get("item_id") != item_id or old.get("locale") != locale or old.get("text") != text
                or old.get("provider") != AUDIO_SOURCE or old.get("voice") != AUDIO_VOICE
                or not check.ok or old.get("sha256") != file_hash(output)
                or old.get("duration_seconds") != check.duration_seconds):
            raise ValueError("Existing audio metadata or bytes conflict; preserved for inspection")
        return {**old, "resume_reused": True, "path": output.relative_to(root).as_posix()}
    source = cache.get(text) if locale == "ja" and not force else None
    if source is not None:
        shutil.copyfile(source, output)
        status = "REUSED"
    else:
        status = "GENERATED"
        error = None
        for attempt in range(2):
            temporary = folder / f".{item_id}-{locale}-{uuid.uuid4().hex}.mp3"
            try:
                synthesize_gtts_mp3(text, temporary, timeout=20, locale=locale)
                check = validate_audio(temporary)
                if not check.ok:
                    raise ValueError(check.reason or "Invalid MP3")
                os.replace(temporary, output)
                break
            except Exception as exc:
                error = exc
            finally:
                temporary.unlink(missing_ok=True)
        if not output.exists():
            raise ValueError(f"Audio generation failed after 2 attempts: {error}")
    check = validate_audio(output)
    if not check.ok:
        raise ValueError(check.reason or "Invalid MP3")
    record = {"item_id": item_id, "locale": locale, "text": text, "provider": AUDIO_SOURCE,
              "voice": AUDIO_VOICE, "status": status, "path": output.relative_to(root).as_posix(),
              "sha256": file_hash(output), "size_bytes": check.size, "duration_seconds": check.duration_seconds,
              "speech_content_verified": False}
    save_json(metadata, record)
    return record


def gallery(pack: dict, root: Path, pack_folder: str, image_results: dict):
    cards = []
    for item in pack["items"]:
        cards.append({"id": item["item_id"], "english": item["english"], "japanese": item["japanese"],
                      "vietnamese": item["vietnamese"], "status": item["status"],
                      "image_status": image_results[item["item_id"]]["status"],
                      "warnings": (["Target sense chưa được xác minh ngữ nghĩa độc lập"] if item["target_sense"] else [])
                                  + (["Thiếu audio tiếng Anh"] if not item.get("audio_english") else [])
                                  + (["Không có ảnh phù hợp"] if not item["image"] else []),
                      "image": f"{pack_folder}/{item['image']['path']}" if item["image"] else None,
                      "en": f"{pack_folder}/{item['audio_english']['path']}" if item.get("audio_english") else None,
                      "ja": f"{pack_folder}/{item['audio_japanese']['path']}" if item.get("audio_japanese") else None,
                      "errors": [e["code"] for e in item["errors"]]})
    data = json.dumps(cards, ensure_ascii=False).replace("<", "\\u003c")
    page = """<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Multimedia review</title><style>body{font:16px system-ui;margin:0;background:#f7f6f2;color:#202824}header{padding:1rem 1.5rem;background:#173b34;color:white}h1{font-size:1.4rem;margin:0 0 .5rem}main{max-width:1100px;margin:auto;padding:1rem}nav{display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:1rem}input,select,button{font:inherit;padding:.5rem;border:1px solid #789;border-radius:4px;background:white}button{cursor:pointer}button:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #b36b23}article{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:1rem;background:white;border:1px solid #d8dfd9;padding:1rem}img{width:100%;max-height:460px;object-fit:contain;background:#eee}audio{width:100%}.muted{color:#52635a}.term{font-size:2rem;overflow-wrap:anywhere}@media(max-width:650px){article{grid-template-columns:1fr}}</style>
<header><h1>Thư viện duyệt multimedia</h1><span id="summary"></span></header><main><nav><label>Chế độ <select id="mode"><option value="en">English–Vietnamese</option><option value="ja">Japanese–Vietnamese</option></select></label><label>Tìm kiếm <input id="search" type="search"></label><label>Trạng thái <select id="filter"><option value="all">Tất cả</option><option value="needs_review">Cần duyệt</option><option value="failed">Thiếu media</option></select></label><button id="prev">Trước</button><button id="next">Tiếp</button><span id="position"></span></nav><div id="card" aria-live="polite"></div></main><script>const items=DATA;let index=0;const $=id=>document.getElementById(id);function visible(){const q=$("search").value.toLocaleLowerCase(),f=$("filter").value;return items.filter(x=>(f==="all"||x.status===f)&&[x.english,x.japanese,x.vietnamese,x.id].some(t=>t.toLocaleLowerCase().includes(q)))}function render(){let list=visible();index=Math.max(0,Math.min(index,list.length-1));$("summary").textContent=`${items.length} mục · ${items.filter(x=>x.image).length} ảnh · ${items.filter(x=>x.en).length} audio EN · ${items.filter(x=>x.ja).length} audio JA`;$("position").textContent=list.length?`${index+1}/${list.length}`:"0/0";let host=$("card");host.replaceChildren();if(!list.length){host.textContent="Không có mục phù hợp";return}let x=list[index],mode=$("mode").value,term=mode==="en"?x.english:x.japanese,sound=mode==="en"?x.en:x.ja;let a=document.createElement("article"),left=document.createElement("div"),right=document.createElement("div"),title=document.createElement("h2");title.className="term";title.textContent=term;left.append(title);for(let t of [x.vietnamese,x.id,`Xử lý: ${x.status}`,`Ảnh: ${x.image_status}`,...x.warnings,x.errors.join(", ")]){let p=document.createElement("p");p.textContent=t;left.append(p)}let label=document.createElement("p");label.textContent=`Audio ${mode.toUpperCase()}: ${sound?"đã kiểm tra kỹ thuật":"thiếu"}`;left.append(label);if(sound){let audio=document.createElement("audio");audio.controls=true;audio.src=sound;left.append(audio)}if(x.image){let image=document.createElement("img");image.src=x.image;image.alt=`Minh họa cho ${term}`;right.append(image)}else right.textContent="Không có ảnh phù hợp";a.append(left,right);host.append(a)}for(let id of ["mode","search","filter"])$(id).addEventListener("input",()=>{index=0;render()});$("prev").onclick=()=>{index--;render()};$("next").onclick=()=>{index++;render()};render();</script></html>""".replace("DATA", data)
    (root / "review_gallery.html").write_text(page, encoding="utf-8")


def execute(workbook: Path, run_dir: Path | None = None, *, force_audio=False) -> Path:
    workbook = workbook.resolve()
    preview = validate(workbook)
    if not preview["valid"]:
        raise ValueError(f"Invalid workbook: {[d['code'] for d in preview['diagnostics']]}")
    if run_dir is None:
        run_dir = OUTPUT_ROOT / f"run-{uuid.uuid4()}"
        run_dir.mkdir(parents=True, exist_ok=False)
        imported = accept(workbook, run_dir / "import_manifest.json")
        manifest = build_manifest(imported)
        manifest["workspace"] = run_dir.relative_to(PROJECT_ROOT).as_posix()
        for item in manifest["items"]:
            item_id = item["item_id"]
            item["planned_paths"] = {"candidates": f"image_candidates/{item_id}",
                                     "audio_english": f"audio/{item_id}-en.mp3",
                                     "audio_japanese": f"audio/{item_id}-ja.mp3"}
        manifest["pack_version"] = 1
        save_json(run_dir / "processing_manifest.json", manifest)
    else:
        run_dir = run_dir.resolve()
        imported = load(run_dir / "import_manifest.json")
        check_import(imported)
        if imported["normalized_payload_sha256"] != preview["normalized_payload_sha256"]:
            raise ValueError("Resume workbook payload conflict")
        manifest = load(run_dir / "processing_manifest.json")
    approved = load_approved()
    no_suitable = historical_no_suitable()
    ja_cache = japanese_cache()
    images = {x["item_id"]: x for x in load(run_dir / "image_selection_manifest.json")} if (run_dir / "image_selection_manifest.json").exists() else {}
    audio = load(run_dir / "audio_manifest.json") if (run_dir / "audio_manifest.json").exists() else {}
    candidate_dir = run_dir / "image_candidates"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    results_path = candidate_dir / "results.json"
    if results_path.exists():
        for result in load(results_path):
            images.setdefault(result["item_id"], result)
        save_json(run_dir / "image_selection_manifest.json", list(images.values()))
    novel = [row for row in imported["rows"] if row["item_id"] not in images
             and lookup_key(row["english"], row["japanese"], row["vietnamese"]) not in approved
             and lookup_key(row["english"], row["japanese"], row["vietnamese"]) not in no_suitable]
    if novel:
        process_new_images(novel, candidate_dir, images, approved, run_dir / "image_selection_manifest.json")
    pending_image = [row for row in imported["rows"] if row["item_id"] not in images]
    for row in pending_image:
        try:
            key = lookup_key(row["english"], row["japanese"], row["vietnamese"])
            entry = approved.get(key)
            if key in no_suitable:
                result = {"item_id": row["item_id"], "english": row["english"],
                          "status": "NO_SUITABLE_IMAGE", "decision_source": "A003_OWNER_DECISIONS",
                          "review_status": "pending", "candidates": []}
            elif entry:
                result = process_item(row, run_dir / "image_candidates", approved=approved)
                result.update(query_strategy=entry["query_strategy"], search_query=entry["search_query"],
                              owner_decision_source=entry["owner_decision_source"])
            else:
                result = process_item(row, candidate_dir, approved=approved)
        except Exception as exc:
            result = {"item_id": row["item_id"], "status": "SEARCH_FAILED", "error": str(exc)}
        images[row["item_id"]] = result
        save_json(run_dir / "image_selection_manifest.json", list(images.values()))
    for item in manifest["items"]:
        item_id = item["item_id"]
        if item["status"] == "pending":
            item["status"] = "processing"
            manifest["pack_version"] += 1
            save_json(run_dir / "processing_manifest.json", manifest)
        image_result = images[item_id]
        if image_result["status"] == "APPROVED_REUSE":
            source = PROJECT_ROOT / image_result["image_path"]
            if file_hash(source) != image_result["image_sha256"]:
                raise ValueError(f"Approved source hash changed: {item_id}")
            item["image"] = put_asset(source, run_dir, "image", "owner_reviewed_registry")
            item["stages"]["image_review"].update(decision="OWNER_APPROVED_REUSE", candidate_id=None)
            if image_result.get("usage_restriction") == "INTERNAL_ONLY_TEMPORARY":
                item["distribution"] = {"status": "restricted", "evidence": "Owner internal-only selection"}
        elif image_result["status"] in {"PROPOSED", "AUTO_SELECTED_NEEDS_REVIEW"}:
            candidate = selected_image_candidate(image_result, run_dir, item_id)
            if candidate:
                item["image"] = put_asset(Path(candidate["jpeg_path"]), run_dir, "image", "DuckDuckGo/SigLIP proposal")
                item["stages"]["image_review"].update(decision="AUTO_SELECTED_NEEDS_REVIEW", candidate_id=candidate["candidate_id"])
                image_result.update(status="AUTO_SELECTED_NEEDS_REVIEW", image_path=candidate["jpeg_path"],
                                    image_sha256=candidate["jpeg_sha256"])
                save_json(run_dir / "image_selection_manifest.json", list(images.values()))
            else:
                item["image"] = None
        else:
            # The frozen runner's SigLIP result is a proposal, not a semantic or educational quality pass.
            item["image"] = None
        item["stages"]["query"]["output"] = image_result.get("query")
        item["stages"]["image_ranking"]["scores"] = [{"candidate_id": c["candidate_id"], "score": c.get("score"), "raw_sha256": c.get("raw_sha256")} for c in image_result.get("candidates", []) if c.get("score") is not None]
        audio.setdefault(item_id, {})
        for locale, field in (("en", "english"), ("ja", "japanese")):
            try:
                result = make_audio(item_id, locale, item[field], run_dir, ja_cache, force=force_audio)
                audio[item_id][locale] = result
                item["audio_english" if locale == "en" else "audio_japanese"] = put_asset(run_dir / result["path"], run_dir, "audio", AUDIO_SOURCE)
            except Exception as exc:
                audio[item_id][locale] = {"item_id": item_id, "locale": locale, "text": item[field], "status": "FAILED", "reason": str(exc)}
                item.pop("audio_english" if locale == "en" else "audio_japanese", None)
            save_json(run_dir / "audio_manifest.json", audio)
        item["audio"] = item.get("audio_japanese")
        item["extensions"] = {"dual_audio_v1": {locale: {"text": item[field], "locale": locale,
                "sha256": item.get("audio_english" if locale == "en" else "audio_japanese", {}).get("sha256"),
                "duration_seconds": audio[item_id][locale].get("duration_seconds"),
                "provider": audio[item_id][locale].get("provider"), "voice": audio[item_id][locale].get("voice")}
                for locale, field in (("en", "english"), ("ja", "japanese"))}}
        item["stages"]["audio_generation"] = {"english": audio[item_id]["en"], "japanese": audio[item_id]["ja"]}
        item["technical_integrity"] = "pass" if item.get("image") and item.get("audio_english") and item.get("audio_japanese") else "fail"
        item["status"] = "needs_review" if item["technical_integrity"] == "pass" else "failed"
        item["errors"] = [] if item["status"] == "needs_review" else [{"stage": "image" if not item["image"] else "audio", "code": "NO_SUITABLE_IMAGE" if not item["image"] else "MISSING_AUDIO", "message": "Required media unavailable", "retryable": False}]
        manifest["pack_version"] += 1
        save_json(run_dir / "processing_manifest.json", manifest)
    pack = source_pack(manifest, run_dir / "import_manifest.json")
    pack["extensions"] = {"language_modes": {"ENGLISH_TO_VIETNAMESE": {"source": "english", "translation": "vietnamese", "audio": "audio_english"}, "JAPANESE_TO_VIETNAMESE": {"source": "japanese", "translation": "vietnamese", "audio": "audio_japanese"}}}
    pack_report = validate_pack(pack, run_dir)
    save_json(run_dir / "quality_report.json", pack_report)
    if not pack_report["valid"]:
        raise ValueError("Content Pack validation failed: " + "; ".join(pack_report["errors"][:5]))
    destination = run_dir / "content_pack"
    if destination.exists():
        old = load(destination / "content_pack.json")
        if {k: v for k, v in old.items() if k != "pack_version"} != {k: v for k, v in pack.items() if k != "pack_version"}:
            destination = run_dir / f"content_pack_v{manifest['pack_version']}"
    if not destination.exists():
        build_pack(pack, destination, run_dir / "import_manifest.json", run_dir)
    gallery(pack, run_dir, destination.name, images)
    counts = {locale: dict(Counter(entry[locale]["status"] for entry in audio.values())) for locale in ("en", "ja")}
    image_counts = Counter(x["status"] for x in images.values())
    strategies = Counter(x.get("query_strategy") or x.get("route") or "UNKNOWN" for x in images.values())
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True).stdout.strip()
    summary = {"git_commit": commit,
               "workbook_sha256": imported["workbook_sha256"], "items": len(imported["rows"]),
               "images": dict(image_counts), "image_strategies": dict(strategies),
               "no_suitable_image": sum(not item["image"] for item in pack["items"]),
               "audio": counts, "valid_audio_assets": sum(bool(item.get(k)) for item in pack["items"] for k in ("audio_english", "audio_japanese")),
               "automatic_repairs": 0, "semantic_warnings": [item["item_id"] for item in pack["items"] if item["target_sense"]],
               "pack_valid": pack_report["valid"], "active_content_pack": destination.name, "run_dir": str(run_dir)}
    save_json(run_dir / "execution_report.json", summary)
    (run_dir / "quality_report.md").write_text("# Technical quality\n\n" + json.dumps(pack_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (run_dir / "execution_report.md").write_text("# Execution\n\n" + json.dumps(summary, ensure_ascii=False, indent=2) + "\n\nSpeech content and pronunciation remain unverified.\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return run_dir


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--force-audio", action="store_true")
    args = parser.parse_args(argv)
    execute(args.workbook, args.resume, force_audio=args.force_audio)


if __name__ == "__main__":
    main()
