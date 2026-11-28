import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import promote_reviewed_pack as promote
from content_pack_builder import validate_pack

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "b001"


def make_source(tmp):
    """One-item needs_review pack built from the contract fixture (real bytes, real hashes)."""
    src = json.loads((FIXTURE / "content_pack_states.json").read_text(encoding="utf-8"))
    item = next(i for i in src["items"] if i["status"] == "needs_review")
    pack = {k: src[k] for k in ("contract_version", "pack_id", "pack_version", "import_id", "test_only")}
    pack["items"] = [item]
    root = Path(tmp) / "source"
    for asset in (item["image"], item["audio"]):
        target = root / asset["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(FIXTURE / asset["path"], target)
    (root / "content_pack.json").write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    return root


def decide(form, **values):
    for entry in form["items"]:
        entry.update(values)
    return form


class PromoteReviewedPackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.source = make_source(self.tmp)
        self.manifest = self.source / "content_pack.json"
        self.before = hashlib.sha256(self.manifest.read_bytes()).hexdigest()
        self.form = promote.make_form(self.manifest)
        self.out = Path(self.tmp) / "reviewed"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_promote(self, form):
        path = Path(self.tmp) / "review.json"
        path.write_text(json.dumps(form, ensure_ascii=False), encoding="utf-8")
        return promote.promote(self.manifest, path, self.out)

    def assert_source_unchanged(self):
        self.assertEqual(self.before, hashlib.sha256(self.manifest.read_bytes()).hexdigest())

    def test_form_binds_identity_and_hashes_and_starts_pending(self):
        entry = self.form["items"][0]
        self.assertEqual(self.form["source_manifest_sha256"], self.before)
        self.assertEqual(entry["decision"], "pending")
        self.assertTrue(all(entry[d] == "pending" for d in promote.QUALITY))
        self.assertEqual(len(entry["image_sha256"]), 64)
        self.assertEqual(len(entry["audio_japanese_sha256"]), 64)

    def test_full_approval_produces_valid_ready_pack_in_new_folder(self):
        report = self.run_promote(decide(self.form, decision="approved", **{d: "pass" for d in promote.QUALITY}))
        pack = json.loads((self.out / "content_pack.json").read_text(encoding="utf-8"))
        item = pack["items"][0]
        self.assertEqual((item["status"], item["review_status"]), ("ready", "approved"))
        self.assertTrue(all(item["quality"][d] == "pass" for d in promote.QUALITY))
        dims = {e["dimension"] for e in item["quality"]["evidence"]}
        self.assertTrue(set(promote.QUALITY) | {"content_review"} <= dims, "existing evidence is kept, new evidence added")
        self.assertEqual(pack["pack_version"], json.loads(self.manifest.read_text(encoding="utf-8"))["pack_version"] + 1)
        self.assertEqual(report["ready"], 1)
        self.assertTrue(validate_pack(pack, self.out)["valid"])
        self.assertEqual(validate_pack(pack, self.out)["game_ready_count"], 1)
        self.assert_source_unchanged()

    def test_semantic_reviewer_is_recorded_separately(self):
        form = decide(self.form, decision="approved", **{d: "pass" for d in promote.QUALITY},
                      semantic_reviewer="agent (owner-delegated)", semantic_basis="checked EN/JA/VI agree")
        self.run_promote(form)
        ev = json.loads((self.out / "content_pack.json").read_text(encoding="utf-8"))["items"][0]["quality"]["evidence"]
        sem = [e for e in ev if e["dimension"] == "semantic_correctness" and e["reviewer"] == "agent (owner-delegated)"]
        self.assertEqual(len(sem), 1)
        self.assertEqual(sem[0]["basis"], "checked EN/JA/VI agree")
        self.assertTrue(any(e["dimension"] == "image_relevance" and e["reviewer"] == "owner" for e in ev))

    def test_pending_items_stay_needs_review(self):
        report = self.run_promote(self.form)
        item = json.loads((self.out / "content_pack.json").read_text(encoding="utf-8"))["items"][0]
        self.assertEqual(item["status"], "needs_review")
        self.assertEqual(report["ready"], 0)
        self.assert_source_unchanged()

    def test_approval_needs_all_four_passes(self):
        form = decide(self.form, decision="approved", **{d: "pass" for d in promote.QUALITY})
        form["items"][0]["audio_pronunciation"] = "pending"
        with self.assertRaises(promote.PromotionError):
            self.run_promote(form)
        self.assertFalse(self.out.exists())

    def test_quality_fail_without_rejection_stays_needs_review_with_evidence(self):
        form = decide(self.form, decision="pending", **{d: "pass" for d in promote.QUALITY})
        form["items"][0]["image_visual_quality"] = "fail"
        self.run_promote(form)
        item = json.loads((self.out / "content_pack.json").read_text(encoding="utf-8"))["items"][0]
        self.assertEqual(item["status"], "needs_review")
        self.assertEqual(item["quality"]["image_visual_quality"], "fail")
        self.assertTrue(validate_pack(json.loads((self.out / "content_pack.json").read_text(encoding="utf-8")), self.out)["valid"])

    def test_rejection_becomes_failed_with_review_error(self):
        form = decide(self.form, decision="rejected", note="sai nghĩa")
        report = self.run_promote(form)
        item = json.loads((self.out / "content_pack.json").read_text(encoding="utf-8"))["items"][0]
        self.assertEqual((item["status"], item["review_status"]), ("failed", "rejected"))
        self.assertEqual(item["errors"][0]["stage"], "review")
        self.assertEqual(report["failed"], 1)

    def test_hash_or_source_mismatch_is_refused(self):
        form = decide(copy.deepcopy(self.form), decision="approved", **{d: "pass" for d in promote.QUALITY})
        form["items"][0]["image_sha256"] = "0" * 64
        with self.assertRaises(promote.PromotionError):
            self.run_promote(form)
        form = decide(copy.deepcopy(self.form), decision="approved", **{d: "pass" for d in promote.QUALITY})
        form["source_manifest_sha256"] = "1" * 64
        with self.assertRaises(promote.PromotionError):
            self.run_promote(form)
        self.assertFalse(self.out.exists())
        self.assert_source_unchanged()

    def test_existing_output_and_unknown_items_are_refused(self):
        self.out.mkdir()
        with self.assertRaises(promote.PromotionError):
            self.run_promote(self.form)
        self.out.rmdir()
        form = copy.deepcopy(self.form)
        form["items"][0]["item_id"] = "item-99999999-9999-4999-8999-999999999999"
        with self.assertRaises(promote.PromotionError):
            self.run_promote(form)

    def test_only_needs_review_items_can_be_promoted(self):
        pack = json.loads(self.manifest.read_text(encoding="utf-8"))
        pack["items"][0]["status"] = "ready"
        self.manifest.write_text(json.dumps(pack), encoding="utf-8")
        form = decide(promote.make_form(self.manifest), decision="approved", **{d: "pass" for d in promote.QUALITY})
        with self.assertRaises(promote.PromotionError):
            self.run_promote(form)


if __name__ == "__main__":
    unittest.main()
