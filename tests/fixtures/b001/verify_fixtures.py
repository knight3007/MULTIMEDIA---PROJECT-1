"""Bounded B-001 fixture consistency checks; not a production importer."""
import copy
import hashlib
import json
import re
import struct
import unicodedata
import uuid
import wave
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
DIMS = {"semantic_correctness", "image_relevance", "image_visual_quality", "audio_pronunciation"}
STATUSES = {"pending", "processing", "needs_review", "ready", "failed"}
WHITE_SPACE = "\u0009\u000a\u000b\u000c\u000d\u0020\u0085\u00a0\u1680" + "".join(chr(i) for i in range(0x2000, 0x200b)) + "\u2028\u2029\u202f\u205f\u3000"


def normalized(value):
    return unicodedata.normalize("NFC", value.strip(WHITE_SPACE)) if value else None


def identity(row):
    values = [normalized(x) for x in row]
    return tuple(v.casefold() if v and n != 1 else v for n, v in enumerate(values))


def workbook_matrix(path):
    """Inspect only the authored single-sheet text fixtures, not arbitrary XLSX."""
    with ZipFile(path) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        sheets = wb.findall("s:sheets/s:sheet", NS)
        assert len(sheets) == 1 and sheets[0].get("name") == "Vocabulary"
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            shared = ["".join(n.itertext()) for n in ET.fromstring(z.read("xl/sharedStrings.xml"))]
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
        cells = {}
        for cell in sheet.findall(".//s:sheetData/s:row/s:c", NS):
            assert cell.find("s:f", NS) is None
            v = cell.find("s:v", NS)
            if cell.get("t") == "s":
                value = shared[int(v.text)]
            elif cell.get("t") == "inlineStr":
                value = "".join(x.text or "" for x in cell.findall(".//s:t", NS))
            else:
                value = v.text if v is not None else None
            cells[cell.get("r")] = value
        return cells


def id_ok(value, prefix):
    assert value.startswith(prefix)
    raw = value[len(prefix):]
    u = uuid.UUID(raw)
    assert str(u) == raw and u.version == 4


def pack_ok(pack, check_files=True):
    serialized = json.dumps(pack, ensure_ascii=False)
    assert not re.search(r"[A-Za-z]:\\|file://|Bearer |sk-[A-Za-z0-9]{12,}|https://[^/\s]+@", serialized)
    assert set(pack) == {"contract_version", "pack_id", "pack_version", "import_id", "test_only", "items"}
    assert pack["contract_version"] == 1 and type(pack["contract_version"]) is int
    id_ok(pack["pack_id"], "pack-"); id_ok(pack["import_id"], "imp-")
    assert type(pack["pack_version"]) is int and 1 <= pack["pack_version"] <= 9007199254740991
    assert type(pack["test_only"]) is bool and pack["items"]
    seen = set()
    identities = set()
    item_keys = {"item_id", "source_row", "english", "japanese", "vietnamese", "target_sense", "status", "review_status", "quality", "technical_integrity", "distribution", "image", "audio", "errors"}
    for item in pack["items"]:
        assert set(item) == item_keys
        id_ok(item["item_id"], "item-")
        assert item["item_id"] not in seen; seen.add(item["item_id"])
        assert type(item["source_row"]) is int and item["source_row"] >= 2
        for k in ("english", "japanese", "vietnamese"):
            assert isinstance(item[k], str) and item[k] and normalized(item[k]) == item[k]
        assert item["target_sense"] is None or isinstance(item["target_sense"], str) and item["target_sense"]
        key = identity([item[k] for k in ("english", "japanese", "vietnamese", "target_sense")])
        assert key not in identities; identities.add(key)
        assert item["status"] in STATUSES
        assert item["review_status"] in {"pending", "approved", "rejected"}
        assert item["technical_integrity"] in {"unknown", "pass", "fail"}
        quality = item["quality"]
        assert set(quality) == DIMS | {"evidence"}
        assert all(quality[k] in {"unknown", "pass", "fail"} for k in DIMS)
        evidence = quality["evidence"]
        for e in evidence:
            assert set(e) == {"dimension", "reviewer", "basis", "asset_sha256"}
            assert e["dimension"] in DIMS | {"technical_integrity", "content_review"}
            assert e["reviewer"] and e["basis"]
            assert e["asset_sha256"] is None or re.fullmatch(r"[0-9a-f]{64}", e["asset_sha256"])
        for k in DIMS:
            if quality[k] != "unknown":
                expected = item["image"]["sha256"] if k.startswith("image_") else item["audio"]["sha256"] if k == "audio_pronunciation" else None
                assert any(e["dimension"] == k and e["asset_sha256"] == expected for e in evidence)
        if item["review_status"] == "approved":
            assert any(e["dimension"] == "content_review" for e in evidence)
        dist = item["distribution"]
        assert set(dist) == {"status", "evidence"} and dist["status"] in {"unknown", "permitted", "restricted"}
        assert dist["evidence"] is None or isinstance(dist["evidence"], str)
        if dist["status"] == "permitted": assert dist["evidence"]
        for key in ("image", "audio"):
            a = item[key]
            if a is None: continue
            assert set(a) == {"path", "mime_type", "sha256", "size_bytes", "source"}
            assert re.fullmatch(r"[0-9a-f]{64}", a["sha256"])
            ext = {"image/png": "png", "image/jpeg": "jpg", "audio/mpeg": "mp3", "audio/wav": "wav"}[a["mime_type"]]
            assert a["mime_type"].startswith(key + "/")
            assert a["path"] == "assets/" + a["sha256"] + "." + ext
            assert type(a["size_bytes"]) is int and a["size_bytes"] > 0
            if a["source"] is not None:
                assert set(a["source"]) == {"provider", "url", "query", "model", "revision"}
                assert all(v is None or isinstance(v, str) for v in a["source"].values())
                if a["source"]["url"]:
                    assert re.fullmatch(r"https://[^/@?#]+/[^?#]*", a["source"]["url"])
            if check_files:
                data = (ROOT / a["path"]).read_bytes()
                assert len(data) == a["size_bytes"] and hashlib.sha256(data).hexdigest() == a["sha256"]
                if ext == "png":
                    assert data[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack("!II", data[16:24]) == (16, 16)
                if ext == "wav":
                    with wave.open(str(ROOT / a["path"]), "rb") as w: assert w.getnframes() == 1600
        assert isinstance(item["errors"], list)
        for e in item["errors"]:
            assert set(e) == {"stage", "code", "message", "retryable"}
            assert e["stage"] in {"import", "query", "image", "audio", "validation", "review"}
            assert e["code"] and e["message"] and type(e["retryable"]) is bool
        assert bool(item["errors"]) == (item["status"] == "failed")
        if item["status"] in {"ready", "needs_review"}:
            assert item["image"] and item["audio"] and item["technical_integrity"] == "pass"
        if item["status"] == "ready":
            assert item["review_status"] == "approved" and all(quality[k] == "pass" for k in DIMS)


def main():
    expected = json.loads((ROOT / "expected.json").read_text(encoding="utf-8"))
    for name, case in expected["cases"].items():
        cells = workbook_matrix(ROOT / name)
        rows = sorted({int(re.search(r"\d+", c)[0]) for c in cells if int(re.search(r"\d+", c)[0]) > 1})
        if name == "excel_missing_column.xlsx":
            assert cells.get("C1") is None and case["errors"][0]["column"] == "vietnamese"
            continue
        assert [cells[c + "1"] for c in "ABCD"] == ["english", "japanese", "vietnamese", "target_sense"]
        nonempty = [n for n in rows if any(normalized(cells.get(c + str(n))) for c in "ABCD")]
        if name == "excel_duplicate.xlsx":
            assert identity([cells.get(c + "2") for c in "ABCD"]) == identity([cells.get(c + "3") for c in "ABCD"])
            assert case["errors"][0]["related_row"] == 2 and not case["accepted_rows"]
        else: assert nonempty == case["accepted_rows"] and not case["errors"]
        if case["empty_rows"]: assert all(n not in nonempty for n in case["empty_rows"])
        if "normalized_row" in case:
            assert [normalized(cells.get(c + "2")) for c in "ABCD"] == case["normalized_row"]
    pack = json.loads((ROOT / "content_pack_states.json").read_text(encoding="utf-8"))
    pack_ok(pack)
    assert {x["status"] for x in pack["items"]} == STATUSES
    assert pack["test_only"] and pack["items"][0]["distribution"]["status"] == "unknown"
    mutations = [lambda p: p["items"][0].update(review_status="pending"), lambda p: p["items"][0].update(image=None), lambda p: p["items"][0]["image"].update(path="../secret.png"), lambda p: p["items"][1].update(item_id=p["items"][0]["item_id"]), lambda p: p["items"][0].update(status="complete"), lambda p: p["items"][0].update(item_id="vocab-000001"), lambda p: p["items"][1].update(errors=[])]
    for mutate in mutations:
        bad = copy.deepcopy(pack); mutate(bad)
        try: pack_ok(bad)
        except (AssertionError, TypeError, KeyError): pass
        else: raise AssertionError("Invalid fixture mutation accepted")
    large = copy.deepcopy(pack); large["items"] = []
    for n in range(101):
        item = copy.deepcopy(pack["items"][3]); item["item_id"] = "item-" + str(uuid.uuid4()); item["source_row"] = n + 2; item["english"] = "sample " + str(n); large["items"].append(item)
    pack_ok(large, check_files=False)
    print("PASS: 5 XLSX fixtures; 5 pack states; media sizes/hashes; 7 negative mutations; 101-item example; namespaces and local references")


if __name__ == "__main__":
    main()
