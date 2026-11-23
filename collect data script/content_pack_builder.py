"""Offline B-001 Content Pack validator and private pack exporter."""

import argparse
import hashlib
import json
import re
import shutil
import sys
import unicodedata
import uuid
import wave
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from excel_vocabulary_importer import payload_hash

QUALITY = ("semantic_correctness", "image_relevance", "image_visual_quality", "audio_pronunciation")
ITEM_KEYS = {"item_id", "source_row", "english", "japanese", "vietnamese", "target_sense", "status", "review_status", "quality", "technical_integrity", "distribution", "image", "audio", "errors"}
ASSET_KEYS = {"path", "mime_type", "sha256", "size_bytes", "source"}
EXTENSIONS = {"image/png": "png", "image/jpeg": "jpg", "audio/mpeg": "mp3", "audio/wav": "wav"}
SHA = re.compile(r"[0-9a-f]{64}\Z")
WHITESPACE = "\t\n\v\f\r \u0085\u00a0\u1680" + "".join(map(chr, range(0x2000, 0x200b))) + "\u2028\u2029\u202f\u205f\u3000"


class PackError(ValueError):
    pass


def load_json(path):
    def unique(pairs):
        value = {}
        for key, entry in pairs:
            if key in value:
                raise PackError(f"Duplicate JSON key: {key}")
            value[key] = entry
        return value
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PackError(f"Cannot load JSON {path}: {exc}") from exc


def valid_id(value, prefix):
    if not isinstance(value, str) or not value.startswith(prefix):
        return False
    raw = value[len(prefix):]
    try:
        parsed = uuid.UUID(raw)
        return parsed.version == 4 and str(parsed) == raw
    except ValueError:
        return False


def fields(value, required, where, errors, optional=()):
    if not isinstance(value, dict):
        errors.append(f"{where}: expected object")
        return False
    missing = required - value.keys()
    extra = value.keys() - required - set(optional)
    for key in sorted(missing):
        errors.append(f"{where}.{key}: required")
    for key in sorted(extra):
        errors.append(f"{where}.{key}: unknown field")
    return not missing


def asset_file(asset, root, where, errors, check_assets):
    if not fields(asset, ASSET_KEYS, where, errors):
        return
    mime, digest, rel = asset.get("mime_type"), asset.get("sha256"), asset.get("path")
    extension = EXTENSIONS.get(mime)
    if mime not in EXTENSIONS or not mime.startswith(where.rsplit(".", 1)[-1] + "/"):
        errors.append(f"{where}.mime_type: unsupported for this field")
    if not isinstance(digest, str) or not SHA.fullmatch(digest):
        errors.append(f"{where}.sha256: expected lowercase SHA-256")
    expected = f"assets/{digest}.{extension}" if extension and isinstance(digest, str) else None
    if not isinstance(rel, str) or rel != expected:
        errors.append(f"{where}.path: expected safe content-addressed pack-relative path")
    size = asset.get("size_bytes")
    if type(size) is not int or size <= 0:
        errors.append(f"{where}.size_bytes: expected positive integer")
    source = asset.get("source")
    if source is not None:
        keys = {"provider", "url", "query", "model", "revision"}
        if fields(source, keys, where + ".source", errors):
            for key in keys:
                if source.get(key) is not None and not isinstance(source[key], str):
                    errors.append(f"{where}.source.{key}: expected text or null")
            url = source.get("url")
            if url and (not isinstance(url, str) or not re.fullmatch(r"https://[^/@?#\s]+/[^?#\s]*", url)):
                errors.append(f"{where}.source.url: public HTTPS URL without credentials/query only")
    if not check_assets or rel != expected or not expected:
        return
    if root is None:
        errors.append(f"{where}.path: asset root required")
        return
    root = Path(root).resolve()
    path = root / rel
    if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
        errors.append(f"{where}.path: asset missing or unsafe")
        return
    data = path.read_bytes()
    if len(data) != size:
        errors.append(f"{where}.size_bytes: file size mismatch")
    if hashlib.sha256(data).hexdigest() != digest:
        errors.append(f"{where}.sha256: file hash mismatch")
    if mime == "image/png" and not data.startswith(b"\x89PNG\r\n\x1a\n"):
        errors.append(f"{where}.mime_type: PNG signature mismatch")
    elif mime == "image/jpeg" and not data.startswith(b"\xff\xd8\xff"):
        errors.append(f"{where}.mime_type: JPEG signature mismatch")
    elif mime in {"image/png", "image/jpeg"}:
        try:
            with Image.open(path) as picture:
                if picture.format != ("PNG" if mime == "image/png" else "JPEG"):
                    raise ValueError("wrong image format")
                picture.verify()
        except (UnidentifiedImageError, OSError, ValueError):
            errors.append(f"{where}.mime_type: invalid image data")
    elif mime == "audio/wav":
        try:
            with wave.open(str(path), "rb") as audio:
                if audio.getnframes() == 0:
                    raise ValueError("empty audio")
        except (wave.Error, EOFError, ValueError):
            errors.append(f"{where}.mime_type: invalid WAV")
    elif mime == "audio/mpeg":
        from audiocollector import validate_audio
        if not validate_audio(path).ok:
            errors.append(f"{where}.mime_type: invalid MP3 frames")


def validate_pack(pack, asset_root=None, check_assets=True, mode="private"):
    """Return diagnostics without changing a source snapshot."""
    if isinstance(pack, (str, Path)):
        path = Path(pack)
        if asset_root is None:
            asset_root = path.parent
        pack = load_json(path)
    errors, unavailable = [], []
    if not fields(pack, {"contract_version", "pack_id", "pack_version", "import_id", "test_only", "items"}, "pack", errors, optional={"extensions"}):
        return {"valid": False, "errors": errors, "game_ready_count": 0, "not_game_ready": []}
    if type(pack["contract_version"]) is not int or pack["contract_version"] != 1:
        errors.append("pack.contract_version: unsupported")
    for key, prefix in (("pack_id", "pack-"), ("import_id", "imp-")):
        if not valid_id(pack[key], prefix):
            errors.append(f"pack.{key}: invalid UUIDv4")
    if type(pack["pack_version"]) is not int or not 1 <= pack["pack_version"] <= 9007199254740991:
        errors.append("pack.pack_version: expected positive safe integer")
    if type(pack["test_only"]) is not bool:
        errors.append("pack.test_only: expected boolean")
    if "extensions" in pack and not isinstance(pack["extensions"], dict):
        errors.append("pack.extensions: expected object")
    items = pack["items"]
    if not isinstance(items, list) or not items:
        errors.append("pack.items: expected nonempty list")
        return {"valid": False, "errors": errors, "game_ready_count": 0, "not_game_ready": []}
    seen_ids, seen_keys, ready = set(), set(), 0
    for index, item in enumerate(items):
        where = f"items[{index}]"
        if not fields(item, ITEM_KEYS, where, errors, optional={"extensions"}):
            continue
        if not valid_id(item["item_id"], "item-") or item["item_id"] in seen_ids:
            errors.append(f"{where}.item_id: invalid or duplicate UUIDv4")
        seen_ids.add(item["item_id"])
        row = item["source_row"]
        if type(row) is not int or not 2 <= row <= 9007199254740991:
            errors.append(f"{where}.source_row: expected Excel row >= 2")
        for key in ("english", "japanese", "vietnamese"):
            value = item[key]
            if not isinstance(value, str) or not value or unicodedata.normalize("NFC", value.strip(WHITESPACE)) != value:
                errors.append(f"{where}.{key}: expected normalized nonempty text")
        sense = item["target_sense"]
        if sense is not None and (not isinstance(sense, str) or not sense or unicodedata.normalize("NFC", sense.strip(WHITESPACE)) != sense):
            errors.append(f"{where}.target_sense: expected normalized text or null")
        identity = tuple(item[key].casefold() if isinstance(item[key], str) and key != "japanese" else item[key] for key in ("english", "japanese", "vietnamese", "target_sense"))
        if identity in seen_keys:
            errors.append(f"{where}: duplicate normalized vocabulary record")
        seen_keys.add(identity)
        status = item["status"]
        if status not in {"pending", "processing", "needs_review", "ready", "failed"}:
            errors.append(f"{where}.status: invalid")
        if item["review_status"] not in {"pending", "approved", "rejected"}:
            errors.append(f"{where}.review_status: invalid")
        if item["technical_integrity"] not in {"unknown", "pass", "fail"}:
            errors.append(f"{where}.technical_integrity: invalid")
        quality = item["quality"]
        evidence = []
        if fields(quality, set(QUALITY) | {"evidence"}, where + ".quality", errors):
            evidence = quality["evidence"] if isinstance(quality["evidence"], list) else []
            if not isinstance(quality["evidence"], list):
                errors.append(f"{where}.quality.evidence: expected list")
            for key in QUALITY:
                if quality[key] not in {"unknown", "pass", "fail"}:
                    errors.append(f"{where}.quality.{key}: invalid")
            for number, entry in enumerate(evidence):
                prefix = f"{where}.quality.evidence[{number}]"
                if fields(entry, {"dimension", "reviewer", "basis", "asset_sha256"}, prefix, errors):
                    if entry["dimension"] not in set(QUALITY) | {"technical_integrity", "content_review"}:
                        errors.append(f"{prefix}.dimension: invalid")
                    for key in ("reviewer", "basis"):
                        if not isinstance(entry[key], str) or not entry[key]:
                            errors.append(f"{prefix}.{key}: expected nonempty text")
                    digest = entry["asset_sha256"]
                    if digest is not None and (not isinstance(digest, str) or not SHA.fullmatch(digest)):
                        errors.append(f"{prefix}.asset_sha256: invalid")
            for key in QUALITY:
                if quality[key] in {"pass", "fail"}:
                    linked = item["image"] if key.startswith("image_") else item["audio"] if key == "audio_pronunciation" else None
                    digest = linked.get("sha256") if isinstance(linked, dict) else None
                    if not any(isinstance(e, dict) and e.get("dimension") == key and e.get("asset_sha256") == digest for e in evidence):
                        errors.append(f"{where}.quality.{key}: matching evidence required")
        if item["review_status"] == "approved" and not any(isinstance(e, dict) and e.get("dimension") == "content_review" for e in evidence):
            errors.append(f"{where}.review_status: content_review evidence required")
        dist = item["distribution"]
        if fields(dist, {"status", "evidence"}, where + ".distribution", errors):
            if dist["status"] not in {"unknown", "permitted", "restricted"}:
                errors.append(f"{where}.distribution.status: invalid")
            if dist["evidence"] is not None and not isinstance(dist["evidence"], str):
                errors.append(f"{where}.distribution.evidence: expected text or null")
            if dist["status"] == "permitted" and not dist["evidence"]:
                errors.append(f"{where}.distribution: permission evidence required")
        for kind in ("image", "audio"):
            if item[kind] is not None:
                asset_file(item[kind], asset_root, where + "." + kind, errors, check_assets)
        item_errors = item["errors"]
        if not isinstance(item_errors, list):
            errors.append(f"{where}.errors: expected list")
            item_errors = []
        for number, error in enumerate(item_errors):
            prefix = f"{where}.errors[{number}]"
            if fields(error, {"stage", "code", "message", "retryable"}, prefix, errors):
                if error["stage"] not in {"import", "query", "image", "audio", "validation", "review"} or not isinstance(error["code"], str) or not error["code"] or not isinstance(error["message"], str) or not error["message"] or type(error["retryable"]) is not bool:
                    errors.append(f"{prefix}: invalid error entry")
        if bool(item_errors) != (status == "failed"):
            errors.append(f"{where}.errors: failed requires errors; other states require empty errors")
        if status in {"needs_review", "ready"} and (not item["image"] or not item["audio"] or item["technical_integrity"] != "pass"):
            errors.append(f"{where}.status: both verified media and technical pass required")
        if status == "ready":
            ready += 1
            if item["review_status"] != "approved" or not isinstance(quality, dict) or any(quality.get(key) != "pass" for key in QUALITY):
                errors.append(f"{where}.status: ready requires approval and four quality passes")
        else:
            unavailable.append({"item_id": item["item_id"], "status": status, "missing_media": [k for k in ("image", "audio") if item[k] is None]})
    if mode == "public":
        if pack["test_only"]:
            errors.append("pack.test_only: synthetic/test content cannot be released")
        if not ready:
            errors.append("pack.items: public subset has no ready item")
        for index, item in enumerate(items):
            if isinstance(item, dict) and (item.get("status") != "ready" or not isinstance(item.get("distribution"), dict) or item["distribution"].get("status") != "permitted" or not item["distribution"].get("evidence")):
                errors.append(f"items[{index}]: not public eligible (ready + permitted evidence required)")
    return {"valid": not errors, "errors": errors, "game_ready_count": ready, "not_game_ready": unavailable}


def source_pack(source, import_path=None):
    record = load_json(source) if not isinstance(source, dict) else source
    if record.get("contract_version") == 1 and "rows" in record:
        rows = record["rows"]
        if not isinstance(rows, list) or not rows or payload_hash(rows) != record.get("normalized_payload_sha256"):
            raise PackError("B-002 normalized payload mismatch")
        pack = {"contract_version": 1, "pack_id": record["pack_id"], "pack_version": 1,
                "import_id": record["import_id"], "test_only": True, "items": []}
        for row in rows:
            item = {key: row[key] for key in ("item_id", "source_row", "english", "japanese", "vietnamese", "target_sense")}
            item.update(status="pending", review_status="pending",
                        quality={**{key: "unknown" for key in QUALITY}, "evidence": []},
                        technical_integrity="unknown", distribution={"status": "unknown", "evidence": None},
                        image=None, audio=None, errors=[])
            pack["items"].append(item)
    elif "contract_version" in record:
        pack = record
    elif record.get("manifest_version") == 1 and record.get("purpose") == "PRIVATE_MEDIA_PROCESSING_PLAN":
        if "pack_version" not in record and any(item.get("status") != "pending" or item.get("image") is not None or item.get("audio") is not None for item in record["items"]):
            raise PackError("Changed B-003 processing snapshot requires explicit pack_version")
        pack = {"contract_version": 1, "pack_id": record["pack_id"], "pack_version": record.get("pack_version", 1),
                "import_id": record["import_id"], "test_only": True,
                "items": [{key: item[key] for key in ITEM_KEYS} for item in record["items"]]}
    else:
        raise PackError("Expected B-003.1 processing manifest or Content Pack v1")
    if import_path is not None:
        imported = load_json(import_path)
        if imported.get("import_id") != pack.get("import_id") or imported.get("pack_id") != pack.get("pack_id") or not isinstance(imported.get("rows"), list) or payload_hash(imported["rows"]) != imported.get("normalized_payload_sha256"):
            raise PackError("B-002 import identity/payload mismatch")
        if len(imported["rows"]) != len(pack["items"]):
            raise PackError("B-002 and processing item count mismatch")
        keys = ("item_id", "source_row", "english", "japanese", "vietnamese", "target_sense")
        for index, (row, item) in enumerate(zip(imported["rows"], pack["items"])):
            if any(row.get(key) != item.get(key) for key in keys):
                raise PackError(f"items[{index}]: B-002 row identity/text mismatch")
        if "normalized_payload_sha256" in record and record["normalized_payload_sha256"] != imported["normalized_payload_sha256"]:
            raise PackError("B-003.1 payload fingerprint mismatch")
    return pack


def build_pack(source, output, import_path=None, asset_root=None, mode="private"):
    """Write a new immutable pack directory only after all source checks pass."""
    if mode not in {"private", "public"}:
        raise PackError("Mode must be private or public")
    pack = source_pack(source, import_path)
    root = Path(asset_root) if asset_root else Path(source).parent if not isinstance(source, dict) else None
    if mode == "public":
        raise PackError("Public export blocked: per-asset distribution evidence and safe public metadata export are not established by B-003.1; validation only")
    report = validate_pack(pack, root)
    if not report["valid"]:
        raise PackError("Invalid source pack:\n" + "\n".join(report["errors"]))
    output = Path(output)
    if output.exists():
        raise PackError(f"Output exists: {output}")
    assets = {asset["path"] for item in pack["items"] for asset in (item["image"], item["audio"]) if asset}
    try:
        output.mkdir(parents=True, exist_ok=False)
        for relative in sorted(assets):
            target = output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(Path(root) / relative, target)
        (output / "content_pack.json").write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report = validate_pack(pack, output)
        (output / "validation_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not report["valid"]:
            raise PackError("Copied pack failed validation")
    except Exception:
        shutil.rmtree(output)
        raise
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="B-003.1 processing manifest or Content Pack v1 JSON")
    parser.add_argument("--output", type=Path, help="new private pack directory")
    parser.add_argument("--import-record", type=Path, help="B-002 accepted import to cross-check identities")
    parser.add_argument("--asset-root", type=Path, help="root of source assets/; defaults to source JSON directory")
    parser.add_argument("--mode", choices=("private", "public"), default="private")
    args = parser.parse_args(argv)
    try:
        pack = source_pack(args.source, args.import_record)
        root = args.asset_root or args.source.parent
        if args.output:
            result = build_pack(args.source, args.output, args.import_record, root, args.mode)
        else:
            result = validate_pack(pack, root, mode=args.mode)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["valid"] else 1
    except (PackError, KeyError, TypeError) as exc:
        print(f"B-004.1: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
