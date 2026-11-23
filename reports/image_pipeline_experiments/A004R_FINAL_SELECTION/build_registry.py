"""Write data/vocabulary/approved_images_v1.json from the validated final selection manifest.

Exact EN+JP+VN lookup for pipeline v2 reuse. Carries restrictions; rights stay UNKNOWN. Refuses overwrite.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "collect data script"))
from visual_query_policy import lookup_key  # noqa: E402

OUT = ROOT / "data/vocabulary/approved_images_v1.json"


def main():
    manifest_path = HERE / "final_selection_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if OUT.exists():
        raise SystemExit("approved_images_v1.json already exists; refusing to overwrite")
    entries = []
    for item in manifest["items"]:
        if hashlib.sha256((ROOT / item["image_path"]).read_bytes()).hexdigest() != item["image_sha256"]:
            raise SystemExit(f"hash mismatch {item['vocab_id']}")
        entries.append({"lookup_key": lookup_key(item["english"], item["japanese"], item["vietnamese"]),
                        "vocab_id": item["vocab_id"], "english": item["english"], "japanese": item["japanese"],
                        "vietnamese": item["vietnamese"], "image_path": item["image_path"],
                        "image_sha256": item["image_sha256"], "query_strategy": item["query_strategy"],
                        "search_query": item["search_query"], "owner_decision_source": item["owner_decision_source"],
                        "usage_restriction": item["usage_restriction"], "rights": item["rights"]})
    if len({e["lookup_key"] for e in entries}) != len(entries):
        raise SystemExit("duplicate lookup keys")
    OUT.write_text(json.dumps({
        "schema_version": 1, "policy": "image-pipeline-v2",
        "source_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "reviewer": manifest["reviewer"],
        "status": "OWNER_APPROVED_QUALITY; NOT_PROMOTED; rights UNKNOWN; not read by dataset_builder",
        "entries": entries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(len(entries), "entries ->", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
