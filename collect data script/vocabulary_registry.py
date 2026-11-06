"""Persisted vocabulary identities. Source row numbers are only audit hints."""

import json
import re
from pathlib import Path


REGISTRY_PATH = Path("data/vocabulary/id_registry_v1.json")
ID_PATTERN = re.compile(r"^vocab-[0-9]{6}$")


def initialize_registry(rows, path: Path):
    """Explicit one-time initialization; never called by normal dataset builds."""
    entries = [{"vocab_id": f"vocab-{index:06d}", "row_hint": index,
                "triple": list(row), "history": []}
               for index, row in enumerate(rows, 1)]
    registry = {"schema_version": 1, "entries": entries}
    validate_registry(rows, registry)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(registry, output, ensure_ascii=False, indent=2)
        output.write("\n")
    return registry


def load_registry(root: Path):
    path = root / REGISTRY_PATH
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot load ID registry {path}: {error}") from error


def reconcile_entry(registry, vocab_id, old_triple, new_triple, reason):
    """Record an explicitly authorized text edit without changing identity."""
    matches = [entry for entry in registry["entries"] if entry["vocab_id"] == vocab_id]
    if len(matches) != 1 or matches[0]["triple"] != list(old_triple):
        raise ValueError(f"Cannot reconcile {vocab_id}: old triple does not match registry")
    if not reason or not all(isinstance(value, str) and value for value in new_triple):
        raise ValueError("Reconciliation requires a reason and nonempty new triple")
    entry = matches[0]
    entry["history"].append({"old_triple": list(old_triple),
                             "new_triple": list(new_triple), "reason": reason})
    entry["triple"] = list(new_triple)


def validate_registry(rows, registry):
    if not isinstance(registry, dict) or registry.get("schema_version") != 1:
        raise ValueError("Invalid ID registry schema version")
    entries = registry.get("entries")
    if not isinstance(entries, list) or len(entries) != len(rows):
        raise ValueError(f"ID registry count mismatch: {len(entries) if isinstance(entries, list) else 'invalid'} entries for {len(rows)} rows")
    ids = []
    triples = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Invalid ID registry entry")
        vocab_id, triple = entry.get("vocab_id"), entry.get("triple")
        if not isinstance(vocab_id, str) or not ID_PATTERN.fullmatch(vocab_id):
            raise ValueError(f"Invalid vocabulary ID: {vocab_id!r}")
        if vocab_id in ids:
            raise ValueError(f"ID registry has duplicate ID: {vocab_id}")
        if not isinstance(triple, list) or len(triple) != 3 or not all(
                isinstance(value, str) and value for value in triple):
            raise ValueError(f"ID registry has invalid triple for {vocab_id}")
        key = tuple(triple)
        if key in triples:
            raise ValueError(f"ID registry has duplicate triple: {key!r}")
        ids.append(vocab_id)
        triples[key] = vocab_id
    ordered = []
    for index, row in enumerate(rows, 1):
        key = tuple(row)
        if key not in triples:
            raise ValueError(f"Source row {index} unmatched in ID registry: {key!r}; reconcile explicitly")
        ordered.append(triples[key])
    if len(set(ordered)) != len(entries):
        raise ValueError("Source row mapping is duplicate or ambiguous")
    return ordered
