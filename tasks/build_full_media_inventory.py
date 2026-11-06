"""Build the read-only 100-ID staging index from validated manifests."""

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "collect data script"))

import audiocollector as audio
from dataset_builder import build_dataset
from media_review import load_reviews
from stage_vocabulary_images import _validated_asset, prepare_staging_queries


# Local screening observations only. None is an owner or license approval.
VISUAL_ISSUES = {
    18: (["wrong_referent", "embedded_text"], "Sun candidate is a spectral chart, not a visible sun."),
    19: (["wrong_referent", "visible_watermark"], "Rain candidate is a night resort photo with a logo."),
    36: (["embedded_text", "low_visual_suitability"], "Family candidate is a text-heavy classroom slide."),
    40: (["visible_watermark"], "Engineer photo carries a stock watermark."),
    41: (["wrong_referent"], "Today candidate is a wristwatch."),
    42: (["wrong_referent", "embedded_text"], "Tomorrow candidate is a watch-video graphic."),
    43: (["wrong_referent", "embedded_text"], "Yesterday candidate is a television drama poster."),
    47: (["wrong_referent", "embedded_text"], "Easy candidate is a drawing tutorial thumbnail."),
    48: (["wrong_referent", "embedded_text"], "Difficult candidate is a drawing tutorial thumbnail."),
    49: (["ambiguous"], "Beautiful candidate is one decorative object with no visible comparison."),
    50: (["embedded_text", "low_visual_suitability"], "Strong candidate is a materials infographic."),
    51: (["wrong_referent"], "Go candidate is a static portrait with no visible movement."),
    54: (["wrong_referent", "embedded_text", "visible_watermark"], "Study candidate is a Diwali greeting with watermark."),
    55: (["wrong_referent", "embedded_text"], "Work candidate is an advertisement for Work Objects."),
    56: (["visible_watermark", "low_visual_suitability"], "Sleep candidate is a marked stock preview sheet."),
    59: (["wrong_referent", "embedded_text"], "Buy candidate depicts the Action retail brand."),
    64: (["visible_watermark", "low_visual_suitability"], "Choose candidate is a VectorStock preview collage."),
    65: (["wrong_referent"], "Swim candidate is a portrait with no swimming activity."),
    66: (["visible_watermark", "ambiguous"], "Software illustration has repeated preview marks."),
    67: (["embedded_text", "low_visual_suitability"], "Database candidate is a text-heavy technical diagram."),
    68: (["embedded_text", "low_visual_suitability"], "Password candidate is a branded blog graphic."),
    69: (["visible_watermark", "low_visual_suitability"], "Music candidate is a Dreamstime preview collage."),
    70: (["embedded_text", "low_visual_suitability"], "Language candidate is a text-heavy slide."),
    78: (["visible_watermark", "low_visual_suitability"], "Different candidate is a Depositphotos preview collage."),
    79: (["embedded_text", "low_visual_suitability"], "Dangerous candidate is a labeled classroom chart."),
    85: (["wrong_referent", "embedded_text"], "Where candidate is a film poster."),
    88: (["wrong_referent", "embedded_text", "visible_watermark"], "Please candidate is an iStock text preview."),
    96: (["ambiguous", "low_visual_suitability"], "Waterfall candidate resembles a decorative model, not a natural waterfall scene."),
    97: (["visible_watermark"], "Firefighter candidate carries Adobe Stock preview marks."),
}
SOURCE_REVIEW_HOSTS = ("pinimg.com", "dreamstime.com", "istockphoto.com", "ftcdn.net",
                       "freepik.com", "vectorstock.com", "depositphotos.com", "alamy.com",
                       "creativemarket.com")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def image_size(path):
    with Image.open(path) as opened:
        dimensions = [opened.width, opened.height]
        opened.verify()
    return dimensions


def main():
    dataset = build_dataset(ROOT)
    records = dataset["records"]
    assert len(records) == len({r["vocab_id"] for r in records}) == 100
    saved = json.loads((ROOT / "data/vocabulary/unified_dataset_v1.json").read_text(encoding="utf-8"))
    assert dataset == saved
    reviews = load_reviews(ROOT)["reviews"]
    review_by_id = defaultdict(list)
    for review in reviews:
        review_by_id[review["vocab_id"]].append(review)

    query_base = ROOT / "baseline/media-staging/image-queries"
    queries, errors = prepare_staging_queries(
        [r["english"] for r in records],
        query_base / "generated_qwen_full_v1.json",
        query_base / "generated_qwen_sparse_v1.json")
    assert len(queries) == 100 and errors == {}

    staged_images, image_history, image_runs = {}, defaultdict(list), []
    for run_dir in sorted((ROOT / "baseline/media-staging/images").iterdir()):
        manifest_path = run_dir / "run_manifest.json"
        if not manifest_path.is_file():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("purpose") != "generic_vocabulary_image_staging":
            continue
        image_runs.append(run_dir.name)
        assert manifest["run_id"] == run_dir.name
        assert manifest["vocab_ids"] == [e["vocab_id"] for e in manifest["targets"]]
        for entry in manifest["targets"]:
            vocab_id = entry["vocab_id"]
            image_history[vocab_id].append({"run_id": run_dir.name, "status": entry["status"],
                                            "failure": entry["failure"]})
            if entry["status"] != "staged":
                continue
            assert vocab_id not in staged_images
            checked = _validated_asset(ROOT, run_dir, entry, entry["sha256"])
            for field in ("staged_image_path", "staged_metadata_path", "dimensions", "size_bytes",
                          "sha256", "selected_result", "siglip_selection"):
                assert checked[field] == entry[field], (vocab_id, field)
            assert entry["resume_cache_status"] == "cache_hit"
            staged_images[vocab_id] = (run_dir.name, entry)
    assert len(staged_images) == 89

    staged_audio, audio_runs = {}, []
    for run_dir in sorted((ROOT / "baseline/media-staging/audio").iterdir()):
        if not run_dir.is_dir():
            continue
        manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
        audio_runs.append(run_dir.name)
        assert manifest["run_id"] == run_dir.name
        for entry in manifest["entries"]:
            vocab_id = entry["vocab_id"]
            assert vocab_id not in staged_audio and entry["status"] == "staged"
            path, metadata = ROOT / entry["mp3_path"], ROOT / entry["metadata_path"]
            checked = audio.validate_audio(path)
            assert checked.ok and audio.is_valid_audio_cache(
                path, metadata, entry["japanese_reading"], entry["japanese_reading"], checked)
            assert sha(path) == entry["sha256"]
            assert checked.size == entry["size_bytes"]
            assert abs(checked.duration_seconds - entry["duration_seconds"]) < 0.02
            assert entry["resume_cache_status"] == "cache_hit"
            staged_audio[vocab_id] = (run_dir.name, entry)
    assert len(staged_audio) == 100 and len(audio_runs) == 11

    index = []
    for record in records:
        vocab_id = record["vocab_id"]
        number = int(vocab_id[-6:])
        audio_run, audio_entry = staged_audio[vocab_id]
        assert (record["english"], record["japanese"]["reading"], record["vietnamese"]) == (
            audio_entry["english"], audio_entry["japanese_reading"], audio_entry["vietnamese"])
        listening = ("approved_exact_hash" if number <= 10 else
                     "general_positive_feedback_no_hash_approval" if number <= 20 else "pending")
        audio_info = {"technical_status": "staged", "path": audio_entry["mp3_path"],
                      "metadata_path": audio_entry["metadata_path"],
                      "sha256": audio_entry["sha256"], "duration_seconds": audio_entry["duration_seconds"],
                      "size_bytes": audio_entry["size_bytes"], "provider": audio_entry["provider"],
                      "locale": audio_entry["locale"], "voice": audio_entry["voice"],
                      "source_run_id": audio_run, "collection_provenance": audio_entry["cache_status"],
                      "resume_cache_status": audio_entry["resume_cache_status"],
                      "owner_listening_status": listening, "distribution_rights_status": "unresolved",
                      "production_approval_status": "pending", "public_media_url": None,
                      "failure": None}

        production = None
        if record["image"]["path"]:
            path = ROOT / record["image"]["path"]
            metadata_path = record["image"]["metadata_ref"]
            metadata = json.loads((ROOT / metadata_path).read_text(encoding="utf-8"))
            production = {"path": record["image"]["path"], "metadata_path": metadata_path,
                          "sha256": sha(path), "size_bytes": path.stat().st_size,
                          "dimensions": image_size(path), "query": metadata["search_query"],
                          "query_provenance": metadata.get("query_provenance", "model_generated_unreviewed"),
                          "provider": metadata["provider"], "image_url": metadata.get("image_url"),
                          "source_page_url": metadata.get("source_page_url"),
                          "siglip_selection": metadata.get("image_selection"),
                          "semantic_suitability": record["image"]["semantic_suitability"],
                          "license_status": "unknown"}

        reviewed_candidates = []
        for review in review_by_id[vocab_id]:
            path = ROOT / review["candidate_path"]
            manifest = json.loads((path.parent / "run_manifest.json").read_text(encoding="utf-8"))
            selected = next(e for e in manifest["targets"] if e["vocab_id"] == vocab_id and
                            e["status"] == "staged" and e["staged_image_path"] == review["candidate_path"])
            reviewed_candidates.append({"path": review["candidate_path"],
                                        "metadata_path": selected["staged_metadata_path"],
                                        "sha256": review["sha256"], "size_bytes": path.stat().st_size,
                                        "dimensions": image_size(path),
                                        "source_run_id": review["staging_run_id"],
                                        "query": selected["effective_query"],
                                        "query_provenance": selected["query_provenance"],
                                        "provider": selected["provider"],
                                        "search_backend": selected["search_backend"],
                                        "source": selected["selected_result"],
                                        "siglip_selection": selected["siglip_selection"],
                                        "license_status": review["license_status"],
                                        "license_evidence": review["source_evidence"],
                                        "visual_review": review["visual_review"],
                                        "owner_promotion_approval": review["owner_promotion_approval"]})

        if vocab_id in staged_images:
            run_id, entry = staged_images[vocab_id]
            issue = VISUAL_ISSUES.get(number)
            source = entry["selected_result"]
            host = urlsplit(source["image_url"]).hostname or ""
            primary = {"path": entry["staged_image_path"],
                       "metadata_path": entry["staged_metadata_path"], "sha256": entry["sha256"],
                       "size_bytes": entry["size_bytes"], "dimensions": entry["dimensions"],
                       "source_run_id": run_id, "query": entry["query"],
                       "query_provenance": entry["query_provenance"],
                       "provider": entry["provider"], "search_backend": entry["search_backend"],
                       "source": source, "siglip_selection": entry["siglip_selection"],
                       "candidate_retrieval": entry["candidate_retrieval"],
                       "license_status": "unknown"}
            status = "staged"
            flags = issue[0] if issue else []
            notes = issue[1] if issue else None
            screening = "issue_observed" if issue else "pending"
            license_status = "unknown"
            query = entry["query"]
            provenance = entry["query_provenance"]
            source_review = any(host.endswith(suffix) for suffix in SOURCE_REVIEW_HOSTS)
        elif number == 4:
            primary = reviewed_candidates[0]
            status = "staged_replacement_restricted"
            flags, notes, screening = [], "Cooked rice visually suitable in prior review; reuse rights restricted.", "prior_review_suitable"
            license_status = "verified_restricted"
            query, provenance, source_review = primary["query"], primary["query_provenance"], False
        elif number == 9:
            primary = next(item for item in reviewed_candidates if item["license_status"] == "verified_permitted")
            status = "staged_replacement_pending_promotion"
            flags, notes, screening = [], "Chicken meat candidate suitable in prior review; promotion still pending.", "prior_review_suitable"
            license_status = "verified_permitted"
            query, provenance, source_review = primary["query"], primary["query_provenance"], False
        elif production:
            primary = production
            status = "production_present_needs_review"
            flags, notes, screening = [], None, "pending"
            license_status = "unknown"
            query, provenance, source_review = primary["query"], primary["query_provenance"], False
        else:
            assert vocab_id == "vocab-000038"
            primary = None
            status = "blocked_semantic_review"
            flags, notes, screening = [], "Owner-approved friend sense has no approved image search intent.", "pending"
            license_status = "unknown"
            query, provenance, source_review = None, None, False

        image_info = {"technical_status": status, "path": primary["path"] if primary else None,
                      "primary_asset": primary, "production_asset": production,
                      "reviewed_staging_candidates": reviewed_candidates,
                      "model_query": queries[number - 1], "effective_query": query,
                      "query_provenance": provenance, "license_status": license_status,
                      "source_license_review_required": source_review,
                      "visual_screening_status": screening, "quality_flags": flags,
                      "quality_notes": notes, "owner_approval_status": "pending",
                      "public_media_url": None,
                      "history": image_history.get(vocab_id, []),
                      "failure": notes if status == "blocked_semantic_review" else None}
        blockers = ["audio_distribution_rights_unresolved", "media_production_approval_pending"]
        if license_status != "verified_permitted":
            blockers.append("image_license_" + license_status)
        if status == "blocked_semantic_review":
            blockers.append("image_search_intent_missing")
        if flags:
            blockers.append("image_visual_issue_observed")
        if listening != "approved_exact_hash":
            blockers.append("audio_exact_hash_listening_pending")
        index.append({"vocab_id": vocab_id, "english": record["english"],
                      "japanese_reading": record["japanese"]["reading"],
                      "vietnamese": record["vietnamese"],
                      "semantic_review_status": record["review_status"],
                      "target_sense": record["target_sense"],
                      "annotation_status": record["annotation_status"],
                      "image": image_info, "audio": audio_info,
                      "production_approval_status": "pending", "game_ready": False,
                      "blockers": blockers})

    assert len(index) == len({r["vocab_id"] for r in index}) == 100
    counts = Counter(r["image"]["technical_status"] for r in index)
    flagged = [r for r in index if r["image"]["quality_flags"]]
    semantic_issue_ids = sorted({r["vocab_id"] for r in index if
                                 (r["image"]["production_asset"] or {}).get("semantic_suitability") == "mismatch"
                                 or "wrong_referent" in r["image"]["quality_flags"]})
    totals = {"vocabulary_ids": 100, "valid_staged_audio": 100,
              "existing_audio_reused_from_prior_runs": 20,
              "new_audio_downloaded_this_execution": 80,
              "audio_original_download_provenance_total": sum(r["audio"]["collection_provenance"] == "downloaded" for r in index),
              "audio_smoke_cache_reuse_total": sum(r["audio"]["collection_provenance"] == "reused_smoke" for r in index),
              "audio_missing_or_failed": 0, "production_audio_mp3": 0,
              "production_jpegs": sum(r["image"]["production_asset"] is not None for r in index),
              "new_staged_jpegs": len(staged_images),
              "technical_image_coverage": sum(r["image"]["production_asset"] is not None or r["vocab_id"] in staged_images for r in index),
              "image_missing_or_blocked_ids": [r["vocab_id"] for r in index if r["image"]["path"] is None],
              "known_image_semantic_issue_ids": semantic_issue_ids,
              "new_image_visual_issue_observed": len(flagged),
              "new_images_pending_owner_review": len(staged_images),
              "new_image_license_unknown": sum(r["image"]["license_status"] == "unknown" and r["vocab_id"] in staged_images for r in index),
              "new_image_source_review_hosts": sum(r["image"]["source_license_review_required"] for r in index),
              "historical_reviewed_restricted_candidates": sum(x["license_status"] == "verified_restricted" for x in reviews),
              "promotion_eligible_now": 0, "game_ready_now": 0,
              "public_media_urls": 0,
              "image_status_counts": dict(counts)}
    assert totals["production_jpegs"] == 10 and totals["new_staged_jpegs"] == 89
    assert totals["technical_image_coverage"] == 99
    assert totals["image_missing_or_blocked_ids"] == ["vocab-000038"]
    assert totals["new_image_license_unknown"] == 89
    output = {"schema_version": 1, "scope": "isolated_staging_inventory_only",
              "source_dataset": "data/vocabulary/unified_dataset_v1.json",
              "image_run_ids": image_runs, "audio_run_ids": audio_runs,
              "qwen_prefix_cache": "baseline/media-staging/image-queries/generated_qwen_full_v1.json",
              "qwen_sparse_cache": "baseline/media-staging/image-queries/generated_qwen_sparse_v1.json",
              "visual_screening_note": "Only listed issue flags were locally screened; absence of a flag is not approval or proof of suitability.",
              "totals": totals, "records": index}
    target = ROOT / "reports/full_media_staging_inventory_v1.json"
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(output, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print("wrote", target)
    print(json.dumps(totals, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
