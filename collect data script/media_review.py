"""Validate isolated image reviews; never change production media or dataset state."""

import hashlib
import json
import re
from pathlib import Path


STAGING_BASE = Path("baseline/media-staging/images")
LICENSE_STATUSES = {"verified_permitted", "verified_restricted", "unknown"}
SUITABILITY_STATUSES = {"suitable", "blocked_watermark", "unsuitable"}
OWNER_STATUSES = {"pending", "not_granted", "approved"}


def promotion_eligible(review: dict) -> bool:
    """An explicit owner decision and suitable, permitted exact candidate are required."""
    visual = review.get("visual_review") or {}
    return (review.get("target_sense_approval") == "owner_approved"
            and visual.get("semantic_match") is True
            and visual.get("production_suitability") == "suitable"
            and review.get("license_status") == "verified_permitted"
            and review.get("owner_promotion_approval") == "approved")


def validate_reviews(root: Path, data: dict) -> None:
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("reviews"), list):
        raise ValueError("Invalid media review document")
    root = root.resolve()
    base = (root / STAGING_BASE).resolve()
    if base != root / STAGING_BASE:
        raise ValueError("Staging base is redirected")
    seen = set()
    for review in data["reviews"]:
        if not isinstance(review, dict) or review.get("asset_type") != "image":
            raise ValueError("Invalid image review")
        vocab_id, run_id = review.get("vocab_id"), review.get("staging_run_id")
        if not isinstance(vocab_id, str) or not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
            raise ValueError("Invalid review identity")
        relative = review.get("candidate_path")
        if not isinstance(relative, str):
            raise ValueError("Missing candidate path")
        expected = STAGING_BASE / run_id
        path = (root / relative).resolve()
        if path.parent != (root / expected).resolve() or path.suffix.lower() != ".jpg" or not path.is_relative_to(base):
            raise ValueError("Unsafe or mismatched candidate path")
        digest = review.get("sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Invalid SHA-256")
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("Candidate SHA-256 mismatch")
        identity = (vocab_id, digest)
        if identity in seen:
            raise ValueError("Duplicate image review")
        seen.add(identity)
        manifest = json.loads((root / expected / "run_manifest.json").read_text(encoding="utf-8"))
        targets = manifest.get("targets", [])
        selected = next((entry for entry in targets if
                entry.get("vocab_id") == vocab_id and entry.get("status") == "staged"
                and entry.get("staged_image_path") == relative
                and entry.get("target_sense") == review.get("target_sense")), None)
        if manifest.get("run_id") != run_id or selected is None:
            raise ValueError("Review does not match staged manifest")
        visual = review.get("visual_review")
        if (review.get("target_sense_approval") != "owner_approved"
                or not isinstance(visual, dict)
                or not isinstance(visual.get("semantic_match"), bool)
                or visual.get("production_suitability") not in SUITABILITY_STATUSES
                or review.get("license_status") not in LICENSE_STATUSES
                or review.get("owner_promotion_approval") not in OWNER_STATUSES
                or not isinstance(review.get("notes"), str)):
            raise ValueError("Invalid review decision")
        evidence = review.get("source_evidence")
        if not isinstance(evidence, dict) or not isinstance(evidence.get("image_url"), str):
            raise ValueError("Missing source evidence")
        result = selected.get("selected_result") or {}
        if (evidence["image_url"] != result.get("image_url")
                or evidence.get("source_page_url") != result.get("source_page_url")):
            raise ValueError("Review source evidence does not match staged selection")
        if review["license_status"] != "unknown" and not all(
                isinstance(evidence.get(field), str) and evidence[field]
                for field in ("source_page_url", "license_url", "attribution")):
            raise ValueError("Verified license requires source, license and attribution evidence")


def load_reviews(root: Path, relative: Path = Path("data/vocabulary/image_media_reviews_v1.json")) -> dict:
    data = json.loads((root / relative).read_text(encoding="utf-8"))
    validate_reviews(root, data)
    return data
