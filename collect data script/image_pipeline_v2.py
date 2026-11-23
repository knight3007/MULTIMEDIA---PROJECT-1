"""Image pipeline v2 runner (frozen policy, see docs/IMAGE_PIPELINE_V2.md).

Per item: approved-image reuse -> Qwen v2 word type + query -> route
(PHOTO/ICON/SCENE search, CONNECTOR -> NEEDS_CURATION) -> download + normalize (FIX-001)
-> technical rejection -> SigLIP rank -> proposal with alternatives, always `needs_review`.

Writes only under the given output directory. It never edits data/, the registry or the dataset.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import visual_query_policy as policy
from collector_common import PROJECT_ROOT, CollectionError

SEARCH_SETTINGS = {"page_size": 7, "timeout": 20, "retries": 2, "retry_delay": 2.0}
DOWNLOAD_SETTINGS = {"timeout": 20, "retries": 2, "retry_delay": 2.0}
APPROVED_REGISTRY = PROJECT_ROOT / "data" / "vocabulary" / "approved_images_v1.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_approved(path: Path = APPROVED_REGISTRY) -> dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {entry["lookup_key"]: entry for entry in data["entries"]}


def reuse_approved(item: dict, approved: dict, root: Path = PROJECT_ROOT) -> dict | None:
    entry = approved.get(policy.lookup_key(item["english"], item["japanese"], item["vietnamese"]))
    if not entry:
        return None
    if sha256(root / entry["image_path"]) != entry["image_sha256"]:
        raise CollectionError(f"approved image hash mismatch for {item['english']!r}")
    return {"status": "APPROVED_REUSE", "image_path": entry["image_path"], "image_sha256": entry["image_sha256"],
            "source_vocab_id": entry["vocab_id"], "usage_restriction": entry["usage_restriction"],
            "rights": entry["rights"], "review_status": "owner_approved_quality"}


def process_item(item: dict, out_dir: Path, *, typed: policy.TypedQuery | None = None, generator=None,
                 scorer=None, approved: dict | None = None, search=None, download=None, normalize=None) -> dict:
    """Process one {item_id, english, japanese, vietnamese}. Dependencies are injectable for tests."""
    import imagecollector as image
    search = search or image.search_images
    download = download or image.download_candidate_image
    normalize = normalize or image.normalize_image_to_jpeg
    result = {"item_id": item["item_id"], "english": item["english"], "policy_version": policy.POLICY_VERSION,
              "started_at": datetime.now(timezone.utc).isoformat()}
    reused = reuse_approved(item, approved or {})
    if reused:
        return {**result, **reused}
    if typed is None:
        typed = policy.classify_words([item["english"]], generator)[0]
    result.update(word_type=typed.word_type, route=typed.route, query=typed.query)
    if typed.route == "CURATE":
        return {**result, "status": "NEEDS_CURATION", "review_status": "needs_review", "candidates": []}
    try:
        batch = search(typed.query, page_size=SEARCH_SETTINGS["page_size"], timeout=SEARCH_SETTINGS["timeout"],
                       retries=SEARCH_SETTINGS["retries"], retry_delay=SEARCH_SETTINGS["retry_delay"])
    except Exception as error:  # search failure is recorded, never turned into an image
        return {**result, "status": "SEARCH_FAILED", "error": f"{type(error).__name__}: {error}",
                "review_status": "needs_review", "candidates": []}
    folder = Path(out_dir) / item["item_id"]
    folder.mkdir(parents=True, exist_ok=True)
    candidates = []
    for rank, source in enumerate(batch.candidates[:SEARCH_SETTINGS["page_size"]], 1):
        raw, jpeg = folder / f"{rank:02d}.img", folder / f"{rank:02d}.jpg"
        c = {"candidate_id": f"{item['item_id']}-{rank:02d}", "retrieval_rank": rank,
             "image_url": source.get("image_url"), "source_page_url": source.get("source_page_url"),
             "title": source.get("title"), "status": "DOWNLOAD_FAILED", "rejection": None, "score": None}
        try:
            download(source["image_url"], raw, **DOWNLOAD_SETTINGS)
            normalize(raw, jpeg)
            c.update(status="DOWNLOADED", raw_path=str(raw), raw_sha256=sha256(raw),
                     jpeg_path=str(jpeg), jpeg_sha256=sha256(jpeg), rejection=policy.technical_rejection(jpeg))
        except Exception as error:
            c["error"] = f"{type(error).__name__}: {error}"
            raw.unlink(missing_ok=True)
            jpeg.unlink(missing_ok=True)
        candidates.append(c)
    usable = [c for c in candidates if c["status"] == "DOWNLOADED" and not c["rejection"]]
    if usable and scorer is not None:
        for c, score in zip(usable, scorer.score_batch(typed.query, [Path(c["raw_path"]) for c in usable]), strict=True):
            c["score"] = float(score.score)
    proposal = policy.propose(candidates)
    return {**result, **proposal, "candidates": candidates, "raw_result_count": batch.raw_count,
            "finished_at": datetime.now(timezone.utc).isoformat()}


def run(items: list[dict], out_dir: Path) -> list[dict]:
    """Batch runner: Qwen classification first, then release Qwen before SigLIP (GPU memory)."""
    from query_generator import QwenQueryGenerator
    from image_scorer import SiglipImageScorer
    approved = load_approved()
    pending = [i for i in items if not reuse_approved(i, approved)]
    generator = QwenQueryGenerator(batch_size=2)
    try:
        typed = {t.word: t for t in policy.classify_words([i["english"] for i in pending], generator)} if pending else {}
    finally:
        generator.close()
    scorer = SiglipImageScorer() if any(t.route != "CURATE" for t in typed.values()) else None
    results = []
    for item in items:
        results.append(process_item(item, out_dir, typed=typed.get(item["english"]), scorer=scorer, approved=approved))
        (Path(out_dir) / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return results


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("items_json", type=Path, help="JSON list of {item_id, english, japanese, vietnamese}")
    parser.add_argument("out_dir", type=Path)
    args = parser.parse_args(argv)
    items = json.loads(args.items_json.read_text(encoding="utf-8"))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    results = run(items, args.out_dir)
    for r in results:
        print(r["item_id"], r["english"], r["status"], r.get("route"), r.get("query"), r.get("proposed_candidate_id"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
