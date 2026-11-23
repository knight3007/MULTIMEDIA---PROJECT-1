import copy
import json
import tempfile
import unittest
from pathlib import Path

from kaggle_batch import driver, snapshot, notebook_runtime


VALID = {"visual_type": "food", "search_query": "cooked rice bowl",
         "visual_description": "A bowl of cooked rice is on a table.",
         "negative_constraints": [], "reason": "It shows the intended food."}


def approved(mode="poc", experiment_id="offline-poc-01", batch_size=10):
    _, _, vocab_hash, prompt_hash = driver.snapshot()
    plan = {"experiment_id": experiment_id, "approval_status": "owner_approved",
            "approved_commit": "a" * 40, "mode": mode, "variant": "B",
            "ordered_ids": list(snapshot.POC_IDS) if mode == "poc" else list(range(1, 101)),
            "snapshot_sha256": vocab_hash, "prompt_sha256": prompt_hash,
            "model_revision": "main" if mode == "poc" else "b" * 40,
            "generation_settings": {"max_new_tokens": 256, "do_sample": False,
                                    "enable_thinking": False, "max_input_tokens": 2048},
            "generation_budget": 5 if mode == "poc" else 100,
            "batch_size": batch_size, "inference_cutoff_seconds": 3000,
            "timeout_seconds": 3600, "quota_preflight_verified": True}
    plan["fingerprint"] = driver.fingerprint(plan)
    return plan


class FakeKaggle:
    def __init__(self):
        self.refs = {}
        self.calls = []
        self.raw_override = None
        self.bad_hash = False
        self.bad_count = False
        self.version_override = None
        self.conflict = False

    def list_refs(self, prefix):
        self.calls.append(("list", prefix))
        refs = sorted(r for r in self.refs if r.split("/", 1)[1].startswith(prefix))
        if self.conflict and prefix == "qwen3-4b-vocab-":
            refs.append("knight3007/qwen3-4b-vocab-poc-otherxx-b01-a01")
        return refs

    def status(self, ref):
        self.calls.append(("status", ref))
        if ref.startswith("knight3007/qwen3-4b-vocab-poc-otherxx"):
            return "running"
        return self.refs[ref.rsplit("/", 1)[0]]["status"]

    def pull_source(self, ref, folder):
        self.calls.append(("pull", ref))
        return copy.deepcopy(self.refs[ref.rsplit("/", 1)[0]]["config"])

    def output(self, ref, folder):
        self.calls.append(("output", ref))
        cfg = self.refs[ref.rsplit("/", 1)[0]]["config"]
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        if self.refs[ref.rsplit("/", 1)[0]]["status"] == "error":
            self._put(folder, "manifest.json", {"input": cfg,
                "generation_started": self.refs[ref.rsplit("/", 1)[0]].get("started", 0),
                "generation_completed": 0, "records": [], "completion_reason": "incomplete"})
            return
        files, records = [], []
        for row in cfg["rows"]:
            ident = f"{row['source_row_index']:03d}"
            raw = self.raw_override if self.raw_override is not None else json.dumps(VALID)
            valid = self.raw_override is None
            files.append(self._put(folder, f"raw_{ident}.json", {"id": ident, "raw": raw,
                "raw_sha256": driver.sha(raw.encode()), "input_tokens": 100,
                "output_tokens": 42, "latency_seconds": 0.1, "ended_with_eos": True}))
            files.append(self._put(folder, f"parsed_{ident}.json", {"id": ident,
                "parsed": VALID if valid else None, "error": None if valid else "invalid JSON",
                "validation_status": "valid" if valid else "invalid"}))
            records.append({"id": ident, "vocab_id": row["vocab_id"],
                            "raw_sha256": driver.sha(raw.encode()), "parse_valid": valid})
        files.append(self._put(folder, "events.json", []))
        if self.bad_hash:
            files[0]["sha256"] = "0" * 64
        if self.bad_count:
            records.pop()
        manifest = {"input": cfg, "records": records, "files": files,
                    "generation_started": len(cfg["rows"]),
                    "generation_completed": len(cfg["rows"]),
                    "model_revision": "c" * 40 if cfg["model_revision"] == "main" else cfg["model_revision"],
                    "collection": "complete", "completion_reason": "complete",
                    "quality": "parse_valid" if self.raw_override is None else "needs_review"}
        self._put(folder, "manifest.json", manifest)

    @staticmethod
    def _put(folder, name, obj):
        blob = (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode()
        (folder / name).write_bytes(blob)
        return {"file": name, "sha256": driver.sha(blob), "bytes": len(blob)}

    def push(self, folder, ref, timeout):
        self.calls.append(("push", ref))
        notebook = json.loads((Path(folder) / "batch.ipynb").read_text(encoding="utf-8"))
        metadata = json.loads((Path(folder) / "kernel-metadata.json").read_text(encoding="utf-8"))
        if metadata["id"] != ref or not metadata["is_private"]:
            raise AssertionError("Unsafe metadata")
        self.refs[ref] = {"status": "complete", "config": driver.source_config(notebook)}
        return self.version_override or ref + "/1"

    def quota(self):
        self.calls.append(("quota",))
        return 7200

    def confirm_absent(self, ref):
        self.calls.append(("absent", ref))
        return ref.rsplit("/", 1)[0] not in self.refs


class OfflineD2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.prompt, _, _ = driver.snapshot()

    def test_two_batches_strictly_sequential_and_verified(self):
        plan, fake = approved("full"), FakeKaggle()
        one = driver.step(plan, self.rows, self.prompt, 1, fake, True)
        two = driver.step(plan, self.rows, self.prompt, 2, fake, True)
        self.assertEqual((one["quality"], two["quality"]), ("parse_valid", "parse_valid"))
        calls = fake.calls
        second_push = next(i for i, c in enumerate(calls) if c == ("push", driver.slug(plan, 2, 1)))
        first_verify = max(i for i, c in enumerate(calls[:second_push]) if c == ("output", driver.slug(plan, 1, 1) + "/1"))
        self.assertLess(first_verify, second_push)
        self.assertIn(("pull", driver.slug(plan, 1, 1) + "/1"), calls[:second_push])

    def test_second_cannot_start_without_verified_first(self):
        plan, fake = approved("full"), FakeKaggle()
        with self.assertRaises(driver.SafeStop):
            driver.step(plan, self.rows, self.prompt, 2, fake, True)
        self.assertFalse(any(c[0] == "push" for c in fake.calls))

    def test_exact_version_and_latest_only_rejected(self):
        plan, fake = approved(), FakeKaggle()
        fake.version_override = driver.slug(plan, 1, 1) + "/2"
        with self.assertRaises(driver.SafeStop):
            driver.step(plan, self.rows, self.prompt, 1, fake, True)
        self.assertFalse(any(c[0] == "output" for c in fake.calls))

    def test_duplicate_same_id_no_new_inference(self):
        plan, fake = approved(), FakeKaggle()
        driver.step(plan, self.rows, self.prompt, 1, fake, True)
        again = driver.step(plan, self.rows, self.prompt, 1, fake, True)
        self.assertEqual(again["action"], "already_verified")
        self.assertEqual(sum(c[0] == "push" for c in fake.calls), 1)

    def test_different_github_run_id_same_experiment_no_new_inference(self):
        plan, fake = approved(), FakeKaggle()
        driver.step(plan, self.rows, self.prompt, 1, fake, True)
        # GitHub run ID is deliberately absent from the stable experiment key.
        for _github_run_id in (101, 202):
            self.assertEqual(driver.step(plan, self.rows, self.prompt, 1, fake, True)["action"], "already_verified")
        self.assertEqual(sum(c[0] == "push" for c in fake.calls), 1)

    def test_distinct_experiment_id_same_fingerprint_fails(self):
        one, two = approved(), approved(experiment_id="offline-poc-02")
        two["fingerprint"] = one["fingerprint"]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "catalog.json"
            path.write_text(json.dumps({"experiments": [one, two]}), encoding="utf-8")
            with self.assertRaises(driver.SafeStop):
                driver.load_plan(two["experiment_id"], catalog_path=path)

    def test_cancel_after_push_blocks_replacement(self):
        plan, fake = approved(), FakeKaggle()
        cfg = driver.config(plan, self.rows, self.prompt, 1, 1)
        fake.refs[driver.slug(plan, 1, 1)] = {"status": "running", "config": cfg}
        with self.assertRaises(driver.SafeStop):
            driver.step(plan, self.rows, self.prompt, 1, fake, True)
        self.assertFalse(any(c[0] == "push" for c in fake.calls))

    def test_artifact_expired_recovered_from_kaggle(self):
        plan, fake = approved(), FakeKaggle()
        driver.step(plan, self.rows, self.prompt, 1, fake, True)
        result = driver.local_status(plan, self.rows, self.prompt, fake)
        self.assertEqual(result[0]["collection"], "verified_complete")
        self.assertEqual(result[0]["quality"], "parse_valid")

    def test_missing_or_contradictory_evidence_safe_stop(self):
        plan, fake = approved(), FakeKaggle()
        driver.step(plan, self.rows, self.prompt, 1, fake, True)
        fake.refs[driver.slug(plan, 1, 1)]["config"]["fingerprint"] = "wrong"
        with self.assertRaises(driver.SafeStop):
            driver.local_status(plan, self.rows, self.prompt, fake)

    def test_invalid_json_preserved_without_retry(self):
        plan, fake = approved(), FakeKaggle()
        fake.raw_override = "{invalid"
        result = driver.step(plan, self.rows, self.prompt, 1, fake, True)
        self.assertEqual(result["quality"], "needs_review")
        with self.assertRaises(driver.SafeStop):
            driver.step(plan, self.rows, self.prompt, 1, fake, True)
        self.assertEqual(sum(c[0] == "push" for c in fake.calls), 1)

    def test_notebook_parser_matches_original_contract_cases(self):
        self.assertEqual(notebook_runtime.parse(json.dumps(VALID), True), (VALID, None))
        self.assertIsNone(notebook_runtime.parse("{invalid", True)[0])
        self.assertIsNone(notebook_runtime.parse(json.dumps(VALID), False)[0])
        bad = dict(VALID, extra="unexpected")
        self.assertIsNone(notebook_runtime.parse(json.dumps(bad), True)[0])

    def test_wrong_checksum_and_missing_records(self):
        plan = approved()
        for field in ("bad_hash", "bad_count"):
            fake = FakeKaggle()
            setattr(fake, field, True)
            with self.assertRaises(driver.SafeStop):
                driver.step(plan, self.rows, self.prompt, 1, fake, True)

    def test_exhausted_unknown_budget_blocks(self):
        plan, fake = approved(), FakeKaggle()
        plan["generation_budget"] = 0
        with self.assertRaises(driver.SafeStop):
            driver.step(plan, self.rows, self.prompt, 1, fake, True)
        self.assertFalse(any(c[0] == "push" for c in fake.calls))

    def test_full_resume_only_after_proven_zero_generation_error(self):
        plan, fake = approved("full"), FakeKaggle()
        first = driver.slug(plan, 1, 1)
        fake.refs[first] = {"status": "error", "config": driver.config(plan, self.rows, self.prompt, 1, 1), "started": 0}
        with self.assertRaises(driver.SafeStop):
            driver.step(plan, self.rows, self.prompt, 1, fake, True, allow_retry=False)
        result = driver.step(plan, self.rows, self.prompt, 1, fake, True, allow_retry=True)
        self.assertEqual(result["quality"], "parse_valid")
        self.assertIn(("push", driver.slug(plan, 1, 2)), fake.calls)
        fake.refs[first]["started"] = 1
        with self.assertRaises(driver.SafeStop):
            driver.local_status(plan, self.rows, self.prompt, fake)

    def test_download_merges_only_verified_without_overwrite(self):
        plan, fake = approved(), FakeKaggle()
        driver.step(plan, self.rows, self.prompt, 1, fake, True)
        with tempfile.TemporaryDirectory() as temp:
            result = driver.download_verified(plan, self.rows, self.prompt, fake, temp)
            self.assertEqual(result["records"], 5)
            self.assertEqual(len(json.loads((Path(result["downloaded_to"]) / "merged.json").read_text(encoding="utf-8"))["records"]), 5)
            with self.assertRaises(driver.SafeStop):
                driver.download_verified(plan, self.rows, self.prompt, fake, temp)

    def test_gpu_conflict_and_missing_reservation(self):
        plan, fake = approved(), FakeKaggle()
        with self.assertRaises(driver.SafeStop):
            driver.step(plan, self.rows, self.prompt, 1, fake, False)
        fake.conflict = True
        with self.assertRaises(driver.SafeStop):
            driver.step(plan, self.rows, self.prompt, 1, fake, True)
        self.assertFalse(any(c[0] == "push" for c in fake.calls))

    def test_snapshot_prompt_matches_original_d1_contract(self):
        generated = snapshot.build()
        self.assertEqual(generated["vocabulary_100.json"], (snapshot.INPUT_DIR / "vocabulary_100.json").read_bytes())
        self.assertEqual(generated["variant_b_prompt.json"], (snapshot.INPUT_DIR / "variant_b_prompt.json").read_bytes())
        d1 = json.loads((snapshot.ROOT / "reports/remote_qwen/d1-five-20261107-qwen4b-v4/experiment_manifest.json").read_text(encoding="utf-8"))
        by_number = {r["source_row_index"]: r for r in self.rows}
        for request in d1["requests"]:
            if request["variant"] == "b":
                self.assertEqual(request["system_prompt"], self.prompt["system_prompt"])
                self.assertEqual(request["user_prompt"], snapshot.render_user(by_number[request["source_row_index"]]))

    def test_poc_cannot_expand_to_100(self):
        plan = approved()
        self.assertEqual(driver.batches(plan), [snapshot.POC_IDS])
        self.assertEqual(driver.step(plan, self.rows, self.prompt, 2, FakeKaggle(), True)["action"], "no_batch")
        plan["ordered_ids"] = list(range(1, 101))
        plan["fingerprint"] = driver.fingerprint(plan)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "catalog.json"
            path.write_text(json.dumps({"experiments": [plan]}), encoding="utf-8")
            with self.assertRaises(driver.SafeStop):
                driver.load_plan(plan["experiment_id"], catalog_path=path)

    def test_workflow_and_notebook_draft_are_offline_safe(self):
        workflow = (snapshot.ROOT / ".github/workflows/kaggle_qwen3_4b_batch.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertIn("queue: max", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertEqual(workflow.count("timeout-minutes: 330"), 10)
        for i in range(2, 11):
            self.assertIn(f"needs: [approval, batch_{i - 1}]", workflow)
        self.assertEqual(read_catalog_count(), 0)
        compile(driver.RUNTIME.read_text(encoding="utf-8"), str(driver.RUNTIME), "exec")


def read_catalog_count():
    return len(json.loads(driver.CATALOG.read_text(encoding="utf-8"))["experiments"])


if __name__ == "__main__":
    unittest.main()
