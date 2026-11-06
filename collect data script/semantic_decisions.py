"""Versioned owner decisions and context-only annotations."""

import json
from pathlib import Path


DECISIONS_PATH = Path("data/vocabulary/semantic_decisions_v1.json")
APPROVED_IDS = {"vocab-000004", "vocab-000009", "vocab-000038"}
CONTEXT_IDS = {f"vocab-{row:06d}" for row in
               (7, 15, 19, 30, 35, 37, 45, 47, 49, 53, 60, 70, 78, 81,
                87, 88, 90, 91, 98, 100)}
APPROVED_VALUES = {
    "vocab-000004": ("cooked rice", "cooked rice"),
    "vocab-000009": ("chicken meat", "chicken meat"),
    "vocab-000038": ("one friend (singular)", None),
}


def load_decisions(root: Path, registry):
    path = root / DECISIONS_PATH
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot load semantic decisions {path}: {error}") from error
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise ValueError("Invalid semantic decision schema version")
    known = {entry["vocab_id"]: entry for entry in registry["entries"]}
    result = {}
    seen = set()
    for group in ("approved", "context"):
        records = raw.get(group)
        if not isinstance(records, list):
            raise ValueError(f"Semantic decision group {group} must be a list")
        result[group] = {}
        for item in records:
            if not isinstance(item, dict):
                raise ValueError(f"Invalid {group} record")
            vocab_id = item.get("vocab_id")
            if vocab_id not in known or vocab_id in seen:
                raise ValueError(f"Unknown or duplicate semantic decision ID: {vocab_id}")
            if item.get("source_row_index") != known[vocab_id]["row_hint"]:
                raise ValueError(f"Decision row reference mismatch for {vocab_id}")
            if group == "approved":
                if (item.get("review_status") != "approved"
                        or item.get("decision_source") != "owner_approved"
                        or not isinstance(item.get("target_sense"), str)
                        or not item["target_sense"].strip()
                        or not item.get("reviewer") or not item.get("approval_recorded_on")
                        or not item.get("rationale")):
                    raise ValueError(f"Incomplete owner approval for {vocab_id}")
            elif (item.get("review_status") != "needs_decision"
                  or item.get("annotation_status") != "context_added_pending_review"
                  or item.get("target_sense") is not None
                  or item.get("image_search_intent") is not None):
                raise ValueError(f"Context annotation cannot approve meaning: {vocab_id}")
            for optional in ("usage_note", "written_form", "image_search_intent"):
                if optional in item and item[optional] is not None and (
                        not isinstance(item[optional], str) or not item[optional].strip()):
                    raise ValueError(f"Invalid {optional} for {vocab_id}")
            result[group][vocab_id] = item
            seen.add(vocab_id)
    if set(result["approved"]) != APPROVED_IDS:
        raise ValueError("Semantic ledger approved IDs differ from the three owner decisions")
    for vocab_id, (sense, intent) in APPROVED_VALUES.items():
        item = result["approved"][vocab_id]
        if (item["target_sense"], item.get("image_search_intent")) != (sense, intent):
            raise ValueError(f"Semantic ledger differs from owner decision for {vocab_id}")
    if set(result["context"]) != CONTEXT_IDS:
        raise ValueError("Semantic ledger context IDs differ from the 20 pending entries")
    return result


def select_effective_query(vocab_id, model_query, decisions):
    decision = decisions["approved"].get(vocab_id)
    if decision:
        intent = decision.get("image_search_intent")
        if not intent:
            raise ValueError(f"Approved target sense has no image search intent: {vocab_id}")
        return intent, "human_approved"
    return model_query, "model_generated_unreviewed"
