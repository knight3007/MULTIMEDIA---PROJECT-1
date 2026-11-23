"""Read-only reconstruction of existing image and query evidence for this audit."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


AUDIT = Path(__file__).resolve().parent
ROOT = AUDIT.parents[2]

# Additional observations made from this audit's local contact sheets. These are
# provisional visual assessments, not owner review or licensed-use decisions.
CONTACT_OBSERVATIONS = {
    7: (["embedded_text"], "Milk image contains a large beverage headline."),
    23: (["embedded_text", "visible_watermark"], "School is a labeled institutions collage with Alamy preview mark."),
    30: (["embedded_text"], "Bridge is a labeled structural diagram rather than a simple scene."),
    33: (["embedded_text"], "Computer is a text-heavy input/output devices chart."),
    34: (["visible_watermark"], "Umbrella has repeated stock preview marks."),
    35: (["wrong_referent", "embedded_text"], "Shirt image is an anatomical nose diagram."),
    46: (["embedded_text", "low_visual_suitability"], "Hungry image is a hunger-versus-appetite infographic."),
    53: (["wrong_referent", "embedded_text"], "Write image is a how-to-write-an-action-plan infographic."),
    61: (["wrong_referent", "embedded_text"], "Understand image is a grammar lesson thumbnail about action verbs."),
    62: (["wrong_referent", "embedded_text"], "Remember image advertises a memory game about objects."),
    63: (["embedded_text", "low_visual_suitability"], "Receive image is a small labeled action-flow chart."),
    71: (["wrong_referent", "embedded_text"], "Problem image is an object-oriented programming diagram."),
    72: (["visible_watermark", "ambiguous"], "Business image is a watermarked college-of-business building."),
    74: (["wrong_referent", "embedded_text"], "Project image is an object-management software screenshot."),
    75: (["wrong_referent", "embedded_text"], "Experience image is a user-experience technology poster."),
    77: (["wrong_referent"], "Important image is a grid of stone fragments without visible importance cue."),
    81: (["embedded_text", "low_visual_suitability"], "Because image is a grammar teaching slide."),
    82: (["wrong_referent", "embedded_text"], "Always image is an examination question about mechanics."),
    83: (["embedded_text", "low_visual_suitability"], "Sometimes image relies on printed word variants."),
    84: (["embedded_text", "low_visual_suitability"], "Together image is a small 'things that go together' chart."),
    87: (["wrong_referent", "embedded_text"], "Hello image is a screen from a work titled Hello Objects."),
    89: (["embedded_text", "low_visual_suitability"], "Thanks image is a list of gratitude phrases."),
    91: (["visible_watermark"], "Apartment building photo has visible stock marks."),
    95: (["ambiguous"], "Museum candidate shows a museum sign rather than an identifiable museum exhibit or building."),
    98: (["visible_watermark"], "Neighbor image has visible stock preview marks."),
}
QUERY_FIRST_ERROR = {18, 19, 41, 42, 43, 47, 48, 54, 55, 56, 59, 62, 77, 82, 85, 87, 88}
WATERMARK_ON_OTHERWISE_RECOGNIZABLE_IMAGE = {34, 40, 91, 97, 98}


def load(path: str | Path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_json(name: str, value) -> None:
    (AUDIT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(name: str, rows: list[dict]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with (AUDIT / name).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
                             for key, value in row.items()})


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def asset_info(path_text: str | None, metadata_text: str | None, label: str, run_id: str | None):
    path = ROOT / path_text if path_text else None
    metadata_path = ROOT / metadata_text if metadata_text else None
    info = {"state": label, "source_run_id": run_id, "path": path_text,
            "metadata_path": metadata_text, "exists": bool(path and path.is_file()),
            "metadata_exists": bool(metadata_path and metadata_path.is_file()),
            "sha256": None, "size_bytes": None, "dimensions": None,
            "metadata_word": None, "metadata_query": None, "image_url": None,
            "source_page_url": None, "siglip_selection": None, "metadata_error": None}
    if path and path.is_file():
        info["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        info["size_bytes"] = path.stat().st_size
        try:
            with Image.open(path) as image:
                info["dimensions"] = [image.width, image.height]
                info["format"] = image.format
                image.verify()
        except (OSError, ValueError) as error:
            info["metadata_error"] = f"image decode: {error}"
    if metadata_path and metadata_path.is_file():
        try:
            meta = json.loads(metadata_path.read_text(encoding="utf-8"))
            info.update(metadata_word=meta.get("word"), metadata_query=meta.get("search_query"),
                        image_url=meta.get("image_url"), source_page_url=meta.get("source_page_url"),
                        siglip_selection=meta.get("image_selection"),
                        query_provenance=meta.get("query_provenance"))
        except (OSError, ValueError) as error:
            info["metadata_error"] = f"metadata parse: {error}"
    return info


def font(size: int):
    for name in ("C:/Windows/Fonts/meiryo.ttc", "C:/Windows/Fonts/msgothic.ttc"):
        if Path(name).is_file():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def contact_sheets(rows: list[dict]) -> None:
    target = AUDIT / "contact_sheets"
    target.mkdir(exist_ok=True)
    label_font = font(15)
    small_font = font(13)
    for start in range(0, 100, 20):
        sheet = Image.new("RGB", (1400, 1480), "#f2f2f2")
        draw = ImageDraw.Draw(sheet)
        for offset, row in enumerate(rows[start:start + 20]):
            col, band = offset % 4, offset // 4
            x, y = col * 350, band * 296
            draw.rectangle((x + 3, y + 3, x + 347, y + 293), fill="white", outline="#cccccc", width=2)
            path_text = row.get("selected_asset_path")
            if path_text and (ROOT / path_text).is_file():
                try:
                    with Image.open(ROOT / path_text) as opened:
                        thumb = ImageOps.contain(opened.convert("RGB"), (336, 187))
                    sheet.paste(thumb, (x + 7 + (336 - thumb.width) // 2, y + 8 + (187 - thumb.height) // 2))
                except OSError:
                    draw.text((x + 20, y + 75), "CORRUPT JPEG", fill="#b00020", font=label_font)
            else:
                draw.text((x + 20, y + 75), "MISSING IMAGE", fill="#b00020", font=label_font)
            draw.text((x + 8, y + 196), row["vocab_id"], fill="#111111", font=label_font)
            draw.text((x + 8, y + 215), f"{row['english']}  {row['japanese']}"[:35],
                      fill="#111111", font=label_font)
            query = row.get("effective_image_query") or "[no approved query]"
            draw.text((x + 8, y + 236), f"query: {query[:39]}", fill="#333333", font=small_font)
            score = row.get("selected_image_score")
            score_text = "n/a" if score is None else f"{score:.3f}"
            state = "missing" if not path_text else "production" if path_text.startswith("data/") else "staging"
            draw.text((x + 8, y + 255), f"{state} | SigLIP {score_text}",
                      fill="#333333", font=small_font)
            issue = row.get("quality_flags") or []
            draw.text((x + 8, y + 274), f"flags: {', '.join(issue)[:39] if issue else 'unreviewed'}",
                      fill="#9b1717" if issue else "#555555", font=small_font)
        sheet.save(target / f"images_{start+1:03d}_{start+20:03d}.jpg", quality=88)


def main() -> None:
    dataset = load("data/vocabulary/unified_dataset_v1.json")
    registry = load("data/vocabulary/id_registry_v1.json")
    decisions = load("data/vocabulary/semantic_decisions_v1.json")
    prior = load("reports/full_media_staging_inventory_v1.json")
    original = load("data/query/generated_qwen.json")
    alternate = load("data/query/generated_qwen_water_beverage.json")
    prefix = load("baseline/media-staging/image-queries/generated_qwen_full_v1.json")
    sparse = load("baseline/media-staging/image-queries/generated_qwen_sparse_v1.json")
    records = dataset["records"]
    assert len(records) == len(registry["entries"]) == len(prior["records"]) == 100
    assert len({r["vocab_id"] for r in records}) == 100
    assert len(original["records"]) == len(alternate["records"]) == 10
    assert len(prefix["records"]) == len(sparse["records"]) == 50
    assert original["records"] == alternate["records"] == prefix["records"][:10]
    assert original["signature"] == prefix["signature"] == sparse["vocabulary_signature"]
    assert sparse["prefix_sha256"] == hashlib.sha256(
        (ROOT / "baseline/media-staging/image-queries/generated_qwen_full_v1.json").read_bytes()).hexdigest()
    prior_by_id = {r["vocab_id"]: r for r in prior["records"]}
    decision_by_id = {r["vocab_id"]: r for group in ("approved", "context")
                      for r in decisions[group]}
    reviews = load("data/vocabulary/image_media_reviews_v1.json")["reviews"]
    reviews_by_path = {r["candidate_path"]: r for r in reviews}

    manifests = sorted((ROOT / "baseline/media-staging/images").glob("*/run_manifest.json"))
    events = defaultdict(list)
    for path in manifests:
        doc = json.loads(path.read_text(encoding="utf-8"))
        for item in doc.get("targets", []):
            if item.get("vocab_id"):
                events[item["vocab_id"]].append({"run_id": doc.get("run_id", path.parent.name),
                                                   "purpose": doc.get("purpose"), **item})

    query_rows, lineage_rows, quality_rows = [], [], []
    asset_refs = set()
    hashes = defaultdict(list)
    for index, record in enumerate(records):
        vocab_id, english = record["vocab_id"], record["english"]
        assert registry["entries"][index]["vocab_id"] == vocab_id
        assert registry["entries"][index]["triple"][0] == english
        existing = prior_by_id[vocab_id]
        qrecord = prefix["records"][index] if index < 50 else sparse["records"][index - 50]
        assert qrecord["word"] == english
        if index >= 50:
            assert qrecord["source_row_index"] == index + 1 and qrecord["status"] == "generated"
        parsed = qrecord["query"]
        correction = qrecord.get("correction_prompt")
        raw = qrecord.get("corrected_raw_output")
        effective = existing["image"].get("effective_query")
        provenance = existing["image"].get("query_provenance")
        approved = decision_by_id.get(vocab_id, {})
        if approved.get("review_status") == "approved":
            assert effective == approved.get("image_search_intent")
        else:
            assert effective == parsed
        source = ("data/query/generated_qwen.json" if index < 10 else
                  "baseline/media-staging/image-queries/generated_qwen_full_v1.json" if index < 50 else
                  "baseline/media-staging/image-queries/generated_qwen_sparse_v1.json")
        query_flag = ("suspected_wrong_sense" if existing["image"].get("quality_flags") and
                      any(flag == "wrong_referent" for flag in existing["image"]["quality_flags"]) and
                      parsed != effective else
                      "needs_semantic_review" if parsed.endswith((" object", " action", " timepiece", " illumination"))
                      else "not_independently_validated")
        query_rows.append({"vocab_id": vocab_id, "english": english,
                           "japanese": record["japanese"]["reading"], "vietnamese": record["vietnamese"],
                           "target_sense": record.get("target_sense"),
                           "semantic_review_status": record["review_status"],
                           "qwen_model": prefix["model"],
                           "qwen_prompt_version": f"cache_signature:{prefix['signature']}",
                           "raw_qwen_output": raw, "parsed_qwen_query": parsed,
                           "effective_image_query": effective, "query_provenance": provenance,
                           "cache_status": "original_prefix" if index < 10 else
                           "staging_prefix" if index < 50 else "staging_sparse",
                           "evidence_source_file": source,
                           "source_run_id": None,
                           "linked_image_run_id": existing["image"].get("primary_asset", {}).get("source_run_id")
                           if isinstance(existing["image"].get("primary_asset"), dict) else None,
                           "generation_timestamp_if_known": None,
                           "query_quality_flag": query_flag,
                           "diagnostic_notes": "Raw text not persisted; parsed query is proven by cache" if raw is None else
                           "Accepted raw text saved for corrected verb prompt",
                           "prior_rejected_output_evidence": qrecord.get("prior_failure"),
                           "correction_prompt": correction})

        assets = []
        production_path = record["image"].get("path")
        if production_path:
            metadata_path = record["image"].get("metadata_ref")
            assets.append(asset_info(production_path, metadata_path, "production", None))
        for event in events.get(vocab_id, []):
            image_path = event.get("staged_image_path")
            metadata_path = event.get("staged_metadata_path")
            if image_path or metadata_path:
                asset = asset_info(image_path, metadata_path, "staging", event["run_id"])
                asset["manifest_sha256"] = event.get("sha256")
                asset["manifest_dimensions"] = event.get("dimensions")
                asset["manifest_query"] = event.get("query", event.get("effective_query"))
                asset["manifest_selected_url"] = (event.get("selected_result") or {}).get("image_url")
                assets.append(asset)
        for asset in assets:
            if asset["path"]:
                asset_refs.add(asset["path"])
                if asset["sha256"]:
                    hashes[asset["sha256"]].append((vocab_id, asset["path"]))
            if asset["metadata_path"]:
                asset_refs.add(asset["metadata_path"])
            asset["review_record"] = reviews_by_path.get(asset["path"])
            asset["word_matches"] = asset["metadata_word"] == english if asset["metadata_exists"] else None
            asset["integrity_findings"] = []
            if asset["path"] and not asset["exists"]:
                asset["integrity_findings"].append("asset_missing")
            if asset["metadata_path"] and not asset["metadata_exists"]:
                asset["integrity_findings"].append("metadata_missing")
            if asset["word_matches"] is False:
                asset["integrity_findings"].append("metadata_word_mismatch")
            if asset.get("manifest_sha256") and asset["sha256"] != asset["manifest_sha256"]:
                asset["integrity_findings"].append("manifest_sha256_mismatch")
            if asset.get("manifest_dimensions") and asset["dimensions"] != asset["manifest_dimensions"]:
                asset["integrity_findings"].append("manifest_dimensions_mismatch")
            if asset.get("manifest_query") and asset["metadata_query"] != asset["manifest_query"]:
                asset["integrity_findings"].append("manifest_query_mismatch")
            if asset.get("manifest_selected_url") and asset["image_url"] != asset["manifest_selected_url"]:
                asset["integrity_findings"].append("manifest_selected_url_mismatch")
        selected_path = existing["image"].get("path")
        selected = next((asset for asset in assets if asset["path"] == selected_path), None)
        if selected_path and selected is None:
            selected = asset_info(selected_path, existing["image"].get("primary_asset", {}).get("metadata_path"),
                                  "unmatched_prior_inventory", None)
            assets.append(selected)
        selected_event = next((event for event in events.get(vocab_id, [])
                               if event.get("staged_image_path") == selected_path), None)
        retrieval = selected_event.get("candidate_retrieval") if selected_event else None
        score = selected.get("siglip_selection", {}).get("score") if selected and isinstance(selected.get("siglip_selection"), dict) else None
        previous_flags = existing["image"].get("quality_flags") or []
        new_flags, new_note = CONTACT_OBSERVATIONS.get(index + 1, ([], None))
        flags = sorted(set(previous_flags + new_flags))
        notes = "; ".join(filter(None, (existing["image"].get("quality_notes"), new_note))) or None
        lineage = {"vocab_id": vocab_id, "english": english,
                   "japanese": record["japanese"]["reading"], "vietnamese": record["vietnamese"],
                   "target_sense": record.get("target_sense"), "raw_qwen_output": raw,
                   "parsed_qwen_query": parsed, "effective_image_query": effective,
                   "query_provenance": provenance, "search_backend": selected_event.get("search_backend") if selected_event else
                   ("unrecorded" if production_path else None),
                   "search_status": selected_event.get("status") if selected_event else
                   ("historical_production" if production_path else "not_searched"),
                   "raw_result_count": retrieval.get("raw_results") if retrieval else None,
                   "candidate_count": retrieval.get("valid_results") if retrieval else None,
                   "downloaded_candidate_count": retrieval.get("downloaded_candidates") if retrieval else None,
                   "candidate_image_urls": None, "candidate_scores": None,
                   "siglip_model": selected.get("siglip_selection", {}).get("model") if selected and isinstance(selected.get("siglip_selection"), dict) else None,
                   "selected_image_url": selected.get("image_url") if selected else None,
                   "selected_image_score": score,
                   "selected_asset_path": selected_path, "asset_state": existing["image"].get("technical_status"),
                   "selected_dimensions": selected.get("dimensions") if selected else None,
                   "selected_sha256": selected.get("sha256") if selected else None,
                   "selected_source_page_url": selected.get("source_page_url") if selected else None,
                   "license_status": existing["image"].get("license_status"),
                   "media_review_status": existing["image"].get("owner_approval_status"),
                   "failure_reason": existing["image"].get("failure"),
                   "run_ids": sorted({event["run_id"] for event in events.get(vocab_id, [])}),
                   "quality_flags": flags, "quality_notes": notes,
                   "assets": assets, "run_events": events.get(vocab_id, []),
                   "unified_dataset_image_path": production_path}
        lineage_rows.append(lineage)

        categories = []
        first_stage, confidence = "F", "insufficient_evidence"
        if vocab_id in {"vocab-000004", "vocab-000009"}:
            categories.append("query_wrong_sense")
            categories.append("suitable_candidate")
            first_stage, confidence = "A_historical_production", "high"
        if flags:
            if "visible_watermark" in flags or "embedded_text" in flags:
                categories.append("image_text_or_watermark")
            if "ambiguous" in flags:
                categories.append("missing_evidence")
            if index + 1 in QUERY_FIRST_ERROR:
                categories.append("query_wrong_sense")
                first_stage, confidence = "A", "medium"
            elif parsed.endswith((" object", " action")) and "wrong_referent" in flags:
                categories.append("query_too_generic")
            if index + 1 in WATERMARK_ON_OTHERWISE_RECOGNIZABLE_IMAGE and first_stage == "F":
                first_stage, confidence = "E", "medium"
            if not categories:
                categories.append("missing_evidence")
        else:
            categories.append("visually_unreviewed")
        if existing["image"].get("license_status") == "verified_restricted":
            categories.append("license_restricted")
            if first_stage == "F":
                first_stage, confidence = "E", "high"
        if not selected_path:
            categories.append("missing_evidence")
        quality_rows.append({"vocab_id": vocab_id, "english": english,
                             "japanese": record["japanese"]["reading"],
                             "effective_query": effective, "asset_path": selected_path,
                             "review_basis": "model_assessed_unverified:prior_screening_and_contact_sheet" if previous_flags and new_flags else
                             "model_assessed_unverified:prior_screening" if previous_flags else
                             "model_assessed_unverified:audit_contact_sheet" if new_flags else
                             "documented_asset_review" if vocab_id in {"vocab-000004", "vocab-000009"} else
                             "not_visually_reviewed",
                             "owner_visual_approval": "not_recorded",
                             "categories": sorted(set(categories)),
                             "first_observable_failure_stage": first_stage,
                             "stage_confidence": confidence,
                             "observed_notes": notes,
                             "license_status": existing["image"].get("license_status")})

    assert len(query_rows) == len(lineage_rows) == len(quality_rows) == 100
    write_json("02_qwen_queries_100.json", query_rows)
    write_csv("02_qwen_queries_100.csv", query_rows)
    write_json("03_image_lineage_100.json", lineage_rows)
    write_csv("03_image_lineage_100.csv", [{key: value for key, value in row.items()
                                           if key not in {"assets", "run_events"}} for row in lineage_rows])
    write_csv("04_image_quality_review.csv", quality_rows)
    contact_sheets(lineage_rows)

    tracked = set(subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode("utf-8").split("\0"))
    inventory = []
    for base in ("data", "baseline", "collect data script", "docs", "reports", "tasks", "schedule", "game", "web"):
        for path in (ROOT / base).rglob("*"):
            if not path.is_file() or AUDIT in path.parents:
                continue
            rel = relative(path)
            inventory.append({"path": rel, "directory": path.parent.relative_to(ROOT).as_posix(),
                              "extension": path.suffix.lower(), "size_bytes": path.stat().st_size,
                              "tracked_in_HEAD": rel in tracked,
                              "role": "production_image" if rel.startswith("data/image/en/") else
                              "production_audio" if rel.startswith("data/audio/jp/") else
                              "staged_media_or_run" if rel.startswith("baseline/media-staging/") else
                              "legacy_baseline" if rel.startswith("baseline/") else
                              "source_or_registry" if rel.startswith("data/vocabulary/") else
                              "query_cache" if rel.startswith("data/query/") else
                              "code_or_test" if rel.startswith("collect data script/") else "report_or_task"})
    for path in ROOT.iterdir():
        if path.is_file():
            rel = relative(path)
            inventory.append({"path": rel, "directory": ".", "extension": path.suffix.lower(),
                              "size_bytes": path.stat().st_size, "tracked_in_HEAD": rel in tracked,
                              "role": "root_document_or_config"})
    write_csv("05_repository_inventory.csv", inventory)
    all_image_files = {relative(p) for base in (ROOT / "data/image/en", ROOT / "baseline/media-staging/images")
                       for p in base.rglob("*") if p.is_file() and p.suffix.lower() == ".jpg"}
    all_metadata = {relative(p) for base in (ROOT / "data/image/en/_metadata", ROOT / "baseline/media-staging/images")
                    for p in base.rglob("*.json") if p.parent.name == "_metadata"}
    stats = {"vocabulary_ids": 100, "original_qwen_parsed": 10,
             "staging_prefix_parsed": 50, "staging_sparse_parsed": 50,
             "unique_historical_parsed_qwen": 100,
             "accepted_raw_output_saved": sum(r["raw_qwen_output"] is not None for r in query_rows),
             "new_diagnostic_inference": 0,
             "missing_parsed_qwen": sum(r["parsed_qwen_query"] is None for r in query_rows),
             "missing_accepted_raw_qwen": sum(r["raw_qwen_output"] is None for r in query_rows),
             "production_jpegs": sum(bool(r["unified_dataset_image_path"]) for r in lineage_rows),
             "selected_image_paths": sum(bool(r["selected_asset_path"]) for r in lineage_rows),
             "selected_staging_jpegs": sum(bool(r["selected_asset_path"] and r["selected_asset_path"].startswith("baseline/")) for r in lineage_rows),
             "all_historical_image_manifests": len(manifests),
             "all_historical_image_events": sum(len(v) for v in events.values()),
             "all_referenced_asset_versions": sum(len(r["assets"]) for r in lineage_rows),
             "selected_downloaded_candidate_total_known": sum(r["downloaded_candidate_count"] or 0 for r in lineage_rows),
             "selected_candidate_count_known_ids": sum(r["downloaded_candidate_count"] is not None for r in lineage_rows),
             "full_candidate_url_lists_saved": 0,
             "full_candidate_score_lists_saved": 0,
             "orphan_jpegs": sorted(all_image_files - asset_refs),
             "orphan_metadata": sorted(all_metadata - asset_refs),
             "duplicate_image_sha256_across_ids": {digest: entries for digest, entries in hashes.items()
                                                   if len({item[0] for item in entries}) > 1},
             "asset_integrity_findings": [dict(vocab_id=row["vocab_id"], path=asset["path"], findings=asset["integrity_findings"])
                                          for row in lineage_rows for asset in row["assets"] if asset["integrity_findings"]],
             "saved_candidate_image_files": sum(1 for p in (ROOT / "baseline/media-staging/images").rglob("*.img") if p.is_file()),
             "missing_selected_source_page_urls": sum(bool(r["selected_asset_path"] and not r["selected_source_page_url"]) for r in lineage_rows),
             "quality_flags_prior_model_screening": sum(bool(r["image"].get("quality_flags"))
                                                        for r in prior["records"]),
             "additional_contact_sheet_observations": len(CONTACT_OBSERVATIONS),
             "quality_flags_any_model_screening": sum(bool(r["quality_flags"]) for r in lineage_rows),
             "quality_stage_counts": dict(Counter(r["first_observable_failure_stage"] for r in quality_rows)),
             "repository_inventory_files": len(inventory)}
    write_json("audit_statistics.json", stats)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
