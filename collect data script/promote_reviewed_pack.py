"""G-004-R1: apply an owner's per-item review to a Content Pack v1 snapshot, as a NEW reviewed pack.

Two steps, both offline and read-only on the source:
  1. --make-form: write a review form bound to the source manifest SHA-256, item IDs and asset hashes.
  2. promote:     the owner fills the form; this applies only the contract transitions
                  needs_review -> ready (approved, four quality passes), needs_review -> failed (rejected),
                  or keeps needs_review (pending / a quality fail), bumps pack_version and writes a new
                  folder through content_pack_builder.build_pack (validate, copy assets, re-validate).
No status is ever changed without an explicit owner decision recorded in the form.
"""

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

from content_pack_builder import PackError, build_pack, load_json

FORM_SCHEMA = "mp1_owner_pack_review_v1"
QUALITY = ("semantic_correctness", "image_relevance", "image_visual_quality", "audio_pronunciation")
DECISIONS = {"pending", "approved", "rejected"}
DIMENSION_VALUES = {"pending", "pass", "fail"}


class PromotionError(ValueError):
    pass


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _asset_sha(item, field):
    asset = item.get(field)
    return asset["sha256"] if isinstance(asset, dict) else None


def make_form(manifest):
    """Review form with every decision pending; it records exactly which bytes the owner is judging."""
    manifest = Path(manifest)
    pack = load_json(manifest)
    return {
        "schema": FORM_SCHEMA,
        "source_manifest": manifest.as_posix(),
        "source_manifest_sha256": sha256_file(manifest),
        "source_pack_id": pack["pack_id"],
        "source_pack_version": pack["pack_version"],
        "reviewer": "owner",
        "basis": "",
        "instructions": ("For each item set decision to approved/rejected/pending and each quality dimension to "
                         "pass/fail/pending. approved requires all four = pass. audio_pronunciation covers BOTH "
                         "English and Japanese audio. Fill 'basis' with how you reviewed (e.g. final_review_gallery.html, "
                         "listened to EN and JA). Do not edit IDs or hashes."),
        "items": [{
            "item_id": item["item_id"], "source_row": item["source_row"],
            "english": item["english"], "japanese": item["japanese"], "vietnamese": item["vietnamese"],
            "current_status": item["status"],
            "image_sha256": _asset_sha(item, "image"),
            "audio_english_sha256": _asset_sha(item, "audio_english"),
            "audio_japanese_sha256": _asset_sha(item, "audio_japanese") or _asset_sha(item, "audio"),
            "decision": "pending", **{d: "pending" for d in QUALITY}, "note": "",
        } for item in pack["items"]],
    }


def _evidence(dimension, reviewer, basis, sha):
    return {"dimension": dimension, "reviewer": reviewer, "basis": basis, "asset_sha256": sha}


def apply_review(pack, form):
    """Return (new pack dict, summary). Raises PromotionError on any mismatch; never mutates the input."""
    if form.get("schema") != FORM_SCHEMA:
        raise PromotionError("Review form schema mismatch")
    if form.get("source_pack_id") != pack["pack_id"] or form.get("source_pack_version") != pack["pack_version"]:
        raise PromotionError("Review form is for a different pack or pack_version")
    reviewer = (form.get("reviewer") or "").strip()
    if not reviewer:
        raise PromotionError("Reviewer is required")
    basis = (form.get("basis") or "").strip() or "owner review recorded in G-004-R1 review form"
    entries = {}
    for entry in form.get("items", []):
        if entry.get("item_id") in entries:
            raise PromotionError(f"Duplicate item in form: {entry.get('item_id')}")
        entries[entry.get("item_id")] = entry
    known = {item["item_id"] for item in pack["items"]}
    unknown = set(entries) - known
    if unknown:
        raise PromotionError(f"Form lists items not in the pack: {sorted(unknown)}")

    out = copy.deepcopy(pack)
    out["pack_version"] = pack["pack_version"] + 1
    summary = {"ready": 0, "failed": 0, "needs_review": 0, "unchanged": 0, "items": []}
    for item in out["items"]:
        entry = entries.get(item["item_id"])
        if entry is None or entry.get("decision") == "pending" and all(entry.get(d) == "pending" for d in QUALITY):
            summary["unchanged"] += 1
            summary["items"].append({"item_id": item["item_id"], "result": item["status"]})
            if item["status"] == "needs_review":
                summary["needs_review"] += 1
            continue
        decision = entry.get("decision")
        if decision not in DECISIONS or any(entry.get(d) not in DIMENSION_VALUES for d in QUALITY):
            raise PromotionError(f"{item['item_id']}: invalid decision or dimension value")
        if item["status"] != "needs_review" or item["technical_integrity"] != "pass" or item["errors"]:
            raise PromotionError(f"{item['item_id']}: only technically passing needs_review items can be reviewed (is {item['status']})")
        image_sha = _asset_sha(item, "image")
        en_sha, ja_sha = _asset_sha(item, "audio_english"), _asset_sha(item, "audio_japanese") or _asset_sha(item, "audio")
        if (entry.get("image_sha256"), entry.get("audio_english_sha256"), entry.get("audio_japanese_sha256")) != (image_sha, en_sha, ja_sha):
            raise PromotionError(f"{item['item_id']}: asset hashes in the form do not match the pack (review was of different bytes)")
        if decision == "approved" and any(entry[d] != "pass" for d in QUALITY):
            raise PromotionError(f"{item['item_id']}: approved requires all four quality dimensions = pass")

        note = (entry.get("note") or "").strip()
        item_basis = f"{basis}; note: {note}" if note else basis
        quality = item["quality"]
        evidence = []
        for d in QUALITY:
            quality[d] = entry[d] if entry[d] in {"pass", "fail"} else "unknown"
            if quality[d] == "unknown":
                continue
            if d == "semantic_correctness":
                # Meaning may be checked by someone other than the media reviewer (e.g. the agent, on the owner's delegation).
                sem_reviewer = (entry.get("semantic_reviewer") or "").strip() or reviewer
                sem_basis = (entry.get("semantic_basis") or "").strip() or item_basis
                evidence.append(_evidence(d, sem_reviewer, sem_basis, None))
            elif d.startswith("image_"):
                evidence.append(_evidence(d, reviewer, item_basis, image_sha))
            else:  # one observation per pronunciation file; JA first because legacy `audio` is its alias
                evidence.append(_evidence(d, reviewer, item_basis + " (Japanese audio)", ja_sha))
                if en_sha:
                    evidence.append(_evidence(d, reviewer, item_basis + " (English audio)", en_sha))
        if decision == "approved":
            evidence.append(_evidence("content_review", reviewer, item_basis, None))
            item.update(status="ready", review_status="approved", errors=[])
            summary["ready"] += 1
        elif decision == "rejected":
            item.update(status="failed", review_status="rejected", errors=[{
                "stage": "review", "code": "owner_rejected", "retryable": True,
                "message": ("Owner rejected the item" + (f": {note}" if note else "."))}])
            summary["failed"] += 1
        else:
            summary["needs_review"] += 1  # a quality fail may stay needs_review while a replacement is pending
        quality["evidence"] = quality.get("evidence", []) + evidence
        summary["items"].append({"item_id": item["item_id"], "result": item["status"]})
    return out, summary


def promote(manifest, form_path, output):
    manifest, output = Path(manifest), Path(output)
    form = load_json(form_path)
    if form.get("source_manifest_sha256") != sha256_file(manifest):
        raise PromotionError("Source manifest changed since the review form was made")
    if output.exists():
        raise PromotionError(f"Output exists: {output}")
    pack, summary = apply_review(load_json(manifest), form)
    try:
        report = build_pack(pack, output, asset_root=manifest.parent)
    except PackError as exc:
        raise PromotionError(str(exc)) from exc
    summary.update(source_manifest=manifest.as_posix(), source_manifest_sha256=form["source_manifest_sha256"],
                   review_form_sha256=sha256_file(form_path), pack_id=pack["pack_id"], pack_version=pack["pack_version"],
                   validation_valid=report["valid"], game_ready_count=report["game_ready_count"])
    (output / "promotion_report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("manifest", type=Path, help="source content_pack.json (never modified)")
    parser.add_argument("--make-form", type=Path, help="write a new review form here and stop")
    parser.add_argument("--review", type=Path, help="owner-filled review form")
    parser.add_argument("--output", type=Path, help="new reviewed pack folder (must not exist)")
    args = parser.parse_args(argv)
    try:
        if args.make_form:
            if args.make_form.exists():
                raise PromotionError(f"Form exists: {args.make_form}")
            args.make_form.write_text(json.dumps(make_form(args.manifest), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"Review form written: {args.make_form}")
            return 0
        if not (args.review and args.output):
            parser.error("--review and --output are required to promote")
        print(json.dumps(promote(args.manifest, args.review, args.output), ensure_ascii=False, indent=2))
        return 0
    except (PromotionError, KeyError, TypeError) as exc:
        print(f"G-004-R1: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
