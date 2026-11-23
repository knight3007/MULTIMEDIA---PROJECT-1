"""Offline B-004.1 content-pack contract and packaging checks."""
import copy
import json
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import content_pack_builder as builder
FIXTURE = ROOT / "tests/fixtures/b001/content_pack_states.json"
PROCESSING = ROOT / "baseline/imports/imp-3e130d77-9848-4f67-b52a-aab79c2512c7/processing_manifest.json"
IMPORT = ROOT / "reports/b002_import_demo/fixture_private_import.json"


class PackBuilderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_real_three_item_draft_and_move(self):
        output = self.root / "private"
        report = builder.build_pack(PROCESSING, output, import_path=IMPORT)
        self.assertTrue(report["valid"])
        self.assertEqual(report["game_ready_count"], 0)
        pack = json.loads((output / "content_pack.json").read_text(encoding="utf-8"))
        self.assertEqual(len(pack["items"]), 3)
        self.assertEqual(pack["items"][2]["target_sense"], "rain weather")
        self.assertEqual([i["source_row"] for i in pack["items"]], [2, 3, 4])
        self.assertTrue(all(i["image"] is None and i["audio"] is None for i in pack["items"]))
        self.assertFalse((output / "assets").exists())
        moved = self.root / "moved"
        output.rename(moved)
        self.assertTrue(builder.validate_pack(moved / "content_pack.json")["valid"])
        with self.assertRaises(builder.PackError):
            builder.build_pack(PROCESSING, moved, import_path=IMPORT)

    def test_b002_record_can_start_private_pack(self):
        output = self.root / "from-import"
        report = builder.build_pack(IMPORT, output)
        self.assertTrue(report["valid"])
        pack = json.loads((output / "content_pack.json").read_text(encoding="utf-8"))
        imported = json.loads(IMPORT.read_text(encoding="utf-8"))
        self.assertEqual([i["item_id"] for i in pack["items"]], [r["item_id"] for r in imported["rows"]])
        self.assertTrue(all(i["status"] == "pending" for i in pack["items"]))

    def test_changed_processing_snapshot_needs_pack_version(self):
        manifest = json.loads(PROCESSING.read_text(encoding="utf-8"))
        manifest["items"][0]["status"] = "processing"
        with self.assertRaises(builder.PackError):
            builder.source_pack(manifest)
        manifest["pack_version"] = 2
        self.assertEqual(builder.source_pack(manifest)["pack_version"], 2)

    def test_fixture_media_copy_and_integrity(self):
        output = self.root / "fixture"
        report = builder.build_pack(FIXTURE, output)
        self.assertTrue(report["valid"])
        self.assertEqual(report["game_ready_count"], 1)
        self.assertEqual(len(list((output / "assets").iterdir())), 2)
        moved = self.root / "relocated"
        output.rename(moved)
        self.assertTrue(builder.validate_pack(moved / "content_pack.json")["valid"])
        image = next((moved / "assets").glob("*.png"))
        image.write_bytes(b"bad")
        result = builder.validate_pack(moved / "content_pack.json")
        self.assertFalse(result["valid"])
        self.assertTrue(any("sha256" in e or "size_bytes" in e for e in result["errors"]))

    def test_invalid_schema_ids_states_and_media(self):
        mutations = [
            lambda p: p["items"].append(copy.deepcopy(p["items"][0])),
            lambda p: p["items"][0]["image"].update(path="../secret.png"),
            lambda p: p["items"][0].update(audio=None),
            lambda p: p["items"][0].update(review_status="pending"),
            lambda p: p["items"][0]["image"].update(sha256="0" * 64),
            lambda p: p["items"][0].update(extra="unknown"),
        ]
        for mutate in mutations:
            pack = copy.deepcopy(self.fixture)
            mutate(pack)
            with self.subTest(mutate=mutate):
                self.assertFalse(builder.validate_pack(pack, asset_root=FIXTURE.parent)["valid"])

    def test_release_rejects_fixture_internal_only_and_unreviewed(self):
        public_check = builder.validate_pack(self.fixture, asset_root=FIXTURE.parent, mode="public")
        self.assertFalse(public_check["valid"])
        self.assertTrue(any("test_only" in e for e in public_check["errors"]))
        with self.assertRaises(builder.PackError):
            builder.build_pack(FIXTURE, self.root / "release", mode="public")
        for state in ("restricted", "unknown"):
            pack = copy.deepcopy(self.fixture)
            pack["test_only"] = False
            pack["items"] = [pack["items"][0]]
            pack["items"][0]["distribution"] = {"status": state, "evidence": "internal only" if state == "restricted" else None}
            result = builder.validate_pack(pack, asset_root=FIXTURE.parent, mode="public")
            self.assertFalse(result["valid"])
            self.assertTrue(any("not public eligible" in e for e in result["errors"]))
            with self.subTest(state=state), self.assertRaises(builder.PackError):
                builder.build_pack(pack, self.root / f"release-{state}", asset_root=FIXTURE.parent, mode="public")
        pack = copy.deepcopy(self.fixture)
        pack["test_only"] = False
        pack["items"] = [pack["items"][3]]
        with self.assertRaises(builder.PackError):
            builder.build_pack(pack, self.root / "unreviewed", mode="public")

    def test_public_write_stays_blocked_even_with_declared_permission(self):
        pack = copy.deepcopy(self.fixture)
        pack["test_only"] = False
        pack["items"] = [pack["items"][0]]
        pack["items"][0]["distribution"] = {"status": "permitted", "evidence": "synthetic declaration"}
        self.assertTrue(builder.validate_pack(pack, asset_root=FIXTURE.parent, mode="public")["valid"])
        with self.assertRaisesRegex(builder.PackError, "Public export blocked"):
            builder.build_pack(pack, self.root / "untrusted-release", asset_root=FIXTURE.parent, mode="public")

    def test_invalid_json_and_duplicate_keys(self):
        path = self.root / "bad.json"
        for text in ("{bad", '{"contract_version":1,"contract_version":1}'):
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(builder.PackError):
                builder.load_json(path)

    def test_missing_media_no_suitable_and_more_than_100(self):
        pack = copy.deepcopy(self.fixture)
        item = copy.deepcopy(pack["items"][3])
        pack["items"] = []
        for n in range(101):
            row = copy.deepcopy(item)
            row["item_id"] = "item-" + str(uuid.UUID(int=(4 << 76) | (2 << 62) | n, version=4))
            row["source_row"] = n + 2
            row["english"] = f"sample {n}"
            pack["items"].append(row)
        pack["items"][0]["status"] = "failed"
        pack["items"][0]["errors"] = [{"stage": "image", "code": "NO_SUITABLE_IMAGE", "message": "No suitable image", "retryable": False}]
        result = builder.validate_pack(pack, check_assets=False)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["game_ready_count"], 0)
        self.assertEqual(len(result["not_game_ready"]), 101)

    def test_deterministic_manifest(self):
        a = self.root / "a"
        b = self.root / "b"
        builder.build_pack(PROCESSING, a, import_path=IMPORT)
        builder.build_pack(PROCESSING, b, import_path=IMPORT)
        self.assertEqual((a / "content_pack.json").read_bytes(), (b / "content_pack.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
