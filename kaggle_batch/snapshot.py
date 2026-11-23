"""Freeze only the vocabulary fields used by the original Variant B contract."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "batch_inputs" / "d2_v1"
PROMPT_SOURCE = ROOT / "reports/image_pipeline_benchmark/20261106-image-query-v1/prompts.json"
FIELDS = ("english", "japanese", "vietnamese", "semantic_review_status",
          "target_sense", "image_search_intent", "usage_note")
POC_IDS = (4, 9, 41, 54, 65)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def render_user(row: dict) -> str:
    return "Vocabulary record (JSON): " + json.dumps({k: row[k] for k in FIELDS}, ensure_ascii=False)


def build(root: Path = ROOT) -> dict[str, bytes]:
    base = root / "data/vocabulary"
    dataset = json.loads((base / "unified_dataset_v1.json").read_text(encoding="utf-8"))["records"]
    registry = json.loads((base / "id_registry_v1.json").read_text(encoding="utf-8"))["entries"]
    decisions = json.loads((base / "semantic_decisions_v1.json").read_text(encoding="utf-8"))
    approved = {r["vocab_id"]: r for r in decisions["approved"]}
    context = {r["vocab_id"]: r for r in decisions["context"]}
    if len(dataset) != 100 or len(registry) != 100:
        raise ValueError("Expected 100 canonical entries")
    rows = []
    for number, (record, entry) in enumerate(zip(dataset, registry), 1):
        vocab_id = f"vocab-{number:06d}"
        if (record["vocab_id"] != vocab_id or entry["vocab_id"] != vocab_id
                or record["source_row_index"] != number or entry["row_hint"] != number
                or entry["triple"] != [record["english"], record["japanese"]["display"], record["vietnamese"]]):
            raise ValueError(f"Canonical mismatch at {number}")
        decision = approved.get(vocab_id)
        status = "approved" if decision else "needs_decision" if vocab_id in context else "unreviewed"
        if record["review_status"] != status or record["target_sense"] != (decision["target_sense"] if decision else None):
            raise ValueError(f"Semantic mismatch at {number}")
        rows.append({"source_row_index": number, "vocab_id": vocab_id,
                     "english": record["english"], "japanese": record["japanese"],
                     "vietnamese": record["vietnamese"], "semantic_review_status": status,
                     "target_sense": record["target_sense"],
                     "image_search_intent": decision.get("image_search_intent") if decision else None,
                     "usage_note": record["usage_note"]})
    prompt = json.loads((root / PROMPT_SOURCE.relative_to(ROOT)).read_text(encoding="utf-8"))["variant_b"]
    return {"vocabulary_100.json": encode({"schema_version": 1, "records": rows}),
            "variant_b_prompt.json": encode(prompt)}


def write_new(directory: Path = INPUT_DIR, root: Path = ROOT) -> None:
    blobs = build(root)
    if directory.exists():
        raise FileExistsError(directory)
    directory.mkdir(parents=True)
    for name, blob in blobs.items():
        (directory / name).write_bytes(blob)


if __name__ == "__main__":
    write_new()
