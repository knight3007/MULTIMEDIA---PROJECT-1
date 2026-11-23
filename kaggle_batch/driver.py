"""CPU-only D2 orchestrator. No Kaggle call occurs while importing this module."""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .snapshot import INPUT_DIR, POC_IDS, ROOT, render_user, sha

CATALOG = Path(__file__).with_name("approved_experiments.json")
TEMPLATE = Path(__file__).with_name("notebook_template.ipynb")
RUNTIME = Path(__file__).with_name("notebook_runtime.py")
ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{5,35}\Z")
SHA_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
MODEL_SHA_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
OWNER = "knight3007"


class SafeStop(RuntimeError):
    """Ambiguous evidence must not create a new inference."""


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def canonical(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def snapshot():
    vocab_path = INPUT_DIR / "vocabulary_100.json"
    prompt_path = INPUT_DIR / "variant_b_prompt.json"
    rows = read_json(vocab_path)["records"]
    prompt = read_json(prompt_path)
    if len(rows) != 100 or [r["source_row_index"] for r in rows] != list(range(1, 101)):
        raise SafeStop("Snapshot must contain the 100 ordered canonical IDs")
    if not isinstance(prompt.get("system_prompt"), str) or not prompt["system_prompt"]:
        raise SafeStop("Variant B prompt absent")
    return rows, prompt, sha(vocab_path.read_bytes()), sha(prompt_path.read_bytes())


def batches(plan):
    ids = POC_IDS if plan["mode"] == "poc" else tuple(range(1, 101))
    size = 5 if plan["mode"] == "poc" else plan["batch_size"]
    if plan["mode"] == "full" and not 10 <= size <= 25:
        raise SafeStop("Full batch size must be 10 to 25")
    return [tuple(ids[i:i + size]) for i in range(0, len(ids), size)]


def fingerprint(plan):
    keys = ("mode", "variant", "ordered_ids", "snapshot_sha256", "prompt_sha256",
            "model_revision", "generation_settings")
    return sha(canonical({k: plan[k] for k in keys}))


def load_plan(experiment_id, dispatch_mode=None, catalog_path=CATALOG):
    if not ID_PATTERN.fullmatch(experiment_id):
        raise SafeStop("Unsafe experiment ID")
    entries = read_json(catalog_path)["experiments"]
    candidates = [e for e in entries if e.get("experiment_id") == experiment_id]
    if len(candidates) != 1:
        raise SafeStop("Experiment is not uniquely owner approved")
    plan = candidates[0]
    if plan.get("approval_status") != "owner_approved":
        raise SafeStop("Experiment approval missing")
    if dispatch_mode and dispatch_mode not in (plan["mode"], "resume"):
        raise SafeStop("Dispatch mode differs from approved experiment")
    if plan["mode"] not in ("poc", "full") or plan["variant"] != "B":
        raise SafeStop("D2 live gate permits only Variant B POC or full")
    if not re.fullmatch(r"[0-9a-f]{40}", plan.get("approved_commit", "")):
        raise SafeStop("Approved fixed commit missing")
    rows, prompt, vocab_sha, prompt_sha = snapshot()
    if plan.get("snapshot_sha256") != vocab_sha or plan.get("prompt_sha256") != prompt_sha:
        raise SafeStop("Approved snapshot checksum mismatch")
    if plan["ordered_ids"] != (list(POC_IDS) if plan["mode"] == "poc" else list(range(1, 101))):
        raise SafeStop("Approved IDs do not match mode")
    if plan["mode"] == "poc" and plan.get("generation_budget") != 5:
        raise SafeStop("POC budget must be exactly five")
    if plan["mode"] == "full" and plan.get("generation_budget") != 100:
        raise SafeStop("Full budget must be exactly 100")
    if plan["mode"] == "poc" and plan.get("model_revision") != "main":
        raise SafeStop("POC must resolve main revision")
    if plan["mode"] == "full" and not MODEL_SHA_PATTERN.fullmatch(plan.get("model_revision", "")):
        raise SafeStop("Full run requires pinned model SHA")
    if plan.get("generation_settings") != {"max_new_tokens": 256, "do_sample": False,
                                           "enable_thinking": False, "max_input_tokens": 2048}:
        raise SafeStop("Generation settings differ from V4 contract")
    if plan.get("fingerprint") != fingerprint(plan):
        raise SafeStop("Approved experiment fingerprint mismatch")
    for other in entries:
        if other is not plan and other.get("fingerprint") == plan["fingerprint"]:
            if (plan.get("repeat_of") != other.get("experiment_id")
                    or plan.get("repeat_approval") != "owner_approved"):
                raise SafeStop("Duplicate experiment fingerprint under another ID")
    return plan, rows, prompt


def verify_pinned_inputs(plan, pinned_root):
    pinned = Path(pinned_root) / "batch_inputs/d2_v1"
    for name, key in (("vocabulary_100.json", "snapshot_sha256"),
                      ("variant_b_prompt.json", "prompt_sha256")):
        path = pinned / name
        if not path.is_file() or sha(path.read_bytes()) != plan[key]:
            raise SafeStop(f"Pinned commit input mismatch: {name}")


def slug(plan, index, attempt):
    short = f"qwen3-4b-vocab-{plan['mode']}-{plan['experiment_id']}-b{index:02d}-a{attempt:02d}"
    if len(short) > 100:
        raise SafeStop("Kaggle slug too long")
    return f"{OWNER}/{short}"


def config(plan, rows, prompt, index, attempt):
    selected = batches(plan)[index - 1]
    by_number = {r["source_row_index"]: r for r in rows}
    chosen = []
    for number in selected:
        row = by_number[number]
        chosen.append({"source_row_index": number, "vocab_id": row["vocab_id"],
                       "user_prompt": render_user(row),
                       "user_prompt_sha256": sha(render_user(row).encode("utf-8"))})
    return {"experiment_id": plan["experiment_id"], "mode": plan["mode"],
            "batch_index": index, "attempt": attempt, "kaggle_ref": slug(plan, index, attempt) + "/1",
            "variant": "B", "rows": chosen, "system_prompt": prompt["system_prompt"],
            "system_prompt_sha256": sha(prompt["system_prompt"].encode("utf-8")),
            "snapshot_sha256": plan["snapshot_sha256"], "prompt_file_sha256": plan["prompt_sha256"],
            "approved_commit": plan["approved_commit"], "fingerprint": plan["fingerprint"],
            "model_revision": plan["model_revision"], "generation_limit": len(chosen),
            "inference_cutoff_seconds": 3000 if plan["mode"] == "poc" else plan["inference_cutoff_seconds"]}


def render_notebook(cfg):
    notebook = read_json(TEMPLATE)
    notebook["cells"][1]["source"] = ["CONFIG = " + repr(cfg) + "\n"]
    notebook["cells"][2]["source"] = RUNTIME.read_text(encoding="utf-8").splitlines(keepends=True) + ["\nmain()\n"]
    return notebook


def metadata(ref):
    # Only local generated files go into the push directory.
    return {"id": ref, "title": ref.split("/", 1)[1], "code_file": "batch.ipynb",
            "language": "python", "kernel_type": "notebook", "is_private": True,
            "enable_gpu": True, "enable_internet": True,
            "machine_shape": "NvidiaTeslaT4", "dataset_sources": [], "competition_sources": [],
            "kernel_sources": []}


def prepare_push(directory, cfg):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "batch.ipynb").write_text(json.dumps(render_notebook(cfg), ensure_ascii=False), encoding="utf-8")
    (directory / "kernel-metadata.json").write_text(json.dumps(metadata(cfg["kaggle_ref"].rsplit("/", 1)[0])), encoding="utf-8")


def source_config(notebook):
    source = "".join(notebook["cells"][1]["source"])
    if not source.startswith("CONFIG = "):
        raise SafeStop("Kaggle source lacks D2 config")
    import ast
    return ast.literal_eval(source[len("CONFIG = "):])


def verify_output(folder, expected, source):
    folder = Path(folder)
    if source != expected or source.get("kaggle_ref") != expected["kaggle_ref"]:
        raise SafeStop("Exact Kaggle version source/config mismatch")
    manifest_path = folder / "manifest.json"
    if not manifest_path.is_file():
        raise SafeStop("Kaggle version has no manifest")
    manifest = read_json(manifest_path)
    if manifest.get("input") != expected:
        raise SafeStop("Output manifest differs from exact version source")
    records = manifest.get("records", [])
    ids = [f"{r['source_row_index']:03d}" for r in expected["rows"]]
    if [r.get("id") for r in records] != ids or len(records) != len(ids):
        raise SafeStop("Record count or ID order differs")
    if manifest.get("generation_started") != len(ids) or manifest.get("generation_completed") != len(ids):
        raise SafeStop("Generation count differs")
    if manifest.get("collection") != "complete" or manifest.get("completion_reason") != "complete":
        raise SafeStop("Kaggle batch incomplete")
    revision = manifest.get("model_revision")
    if not isinstance(revision, str) or not MODEL_SHA_PATTERN.fullmatch(revision):
        raise SafeStop("Model revision unverified")
    if expected["model_revision"] != "main" and revision != expected["model_revision"]:
        raise SafeStop("Pinned model revision mismatch")
    files = manifest.get("files", [])
    names = [f.get("file") for f in files]
    required = {"events.json"} | {f"{kind}_{ident}.json" for kind in ("raw", "parsed") for ident in ids}
    if len(names) != len(set(names)) or set(names) != required:
        raise SafeStop("Output file inventory mismatch")
    if {p.name for p in folder.iterdir() if p.is_file()} != required | {"manifest.json"}:
        raise SafeStop("Unexpected or missing Kaggle output file")
    for entry in files:
        name = entry["file"]
        path = folder / name
        if not path.is_file() or path.stat().st_size != entry["bytes"] or sha(path.read_bytes()) != entry["sha256"]:
            raise SafeStop(f"Output checksum mismatch: {name}")
    for record in records:
        ident = record["id"]
        raw = read_json(folder / f"raw_{ident}.json")
        parsed = read_json(folder / f"parsed_{ident}.json")
        if raw.get("id") != ident or parsed.get("id") != ident:
            raise SafeStop("Record ID mismatch")
        if sha(raw["raw"].encode("utf-8")) != raw["raw_sha256"] or raw["raw_sha256"] != record["raw_sha256"]:
            raise SafeStop("Raw text checksum mismatch")
        if record["parse_valid"] != (parsed["validation_status"] == "valid"):
            raise SafeStop("Parsed status mismatch")
        if record["parse_valid"]:
            try:
                if json.loads(raw["raw"]) != parsed["parsed"] or parsed["error"] is not None:
                    raise SafeStop("Parsed content differs from raw JSON")
            except (ValueError, TypeError) as error:
                raise SafeStop("Raw JSON cannot support valid parse") from error
        elif parsed["parsed"] is not None or not parsed["error"]:
            raise SafeStop("Invalid parse must retain error and no parsed object")
    quality = "parse_valid" if all(r["parse_valid"] for r in records) else "needs_review"
    if manifest.get("quality") != quality:
        raise SafeStop("Quality status mismatch")
    return {"collection": "verified_complete", "quality": quality,
            "manifest_sha256": sha(manifest_path.read_bytes()), "model_revision": revision,
            "generation_count": len(ids)}


class KaggleCLI:
    """Strict adapter. Live formats and version semantics require D2-2 validation."""

    def _call(self, *parts):
        result = subprocess.run(["kaggle", *parts], text=True, capture_output=True, timeout=120)
        if result.returncode:
            raise SafeStop("Kaggle CLI call failed; details withheld from public logs")
        return result.stdout

    def list_refs(self, prefix):
        found = set()
        for page in range(1, 101):
            output = self._call("kernels", "list", "--mine", "--search", prefix,
                                "--page-size", "100", "-p", str(page), "-v")
            rows = list(csv.DictReader(io.StringIO(output)))
            if not rows:
                return sorted(found)
            if "ref" not in rows[0]:
                raise SafeStop("Unrecognized Kaggle list CSV; no push permitted")
            for row in rows:
                ref = row["ref"]
                if ref.startswith(f"{OWNER}/{prefix}"):
                    found.add(ref)
        raise SafeStop("Kaggle notebook enumeration exceeded 100 pages")

    def status(self, ref):
        output = self._call("kernels", "status", ref)
        # Deliberately narrow: any changed/ambiguous CLI wording stops safely.
        match = re.fullmatch(r"\s*Kernel status:\s*(queued|running|complete|error|cancelled)\s*", output, re.I)
        if not match:
            raise SafeStop("Unrecognized version-specific Kaggle status")
        return match.group(1).lower()

    def pull_source(self, ref, folder):
        Path(folder).mkdir(parents=True, exist_ok=True)
        self._call("kernels", "pull", ref, "-p", str(folder))
        files = list(Path(folder).glob("*.ipynb"))
        if len(files) != 1:
            raise SafeStop("Exact version source notebook missing")
        return source_config(read_json(files[0]))

    def output(self, ref, folder):
        self._call("kernels", "output", ref, "-p", str(folder), "-q")

    def push(self, folder, ref, timeout_seconds):
        output = self._call("kernels", "push", "-p", str(folder), "-t", str(timeout_seconds))
        if not re.search(r"\bversion\s+1\b", output, re.I):
            raise SafeStop("Push did not prove exact version 1; do not retry automatically")
        return ref + "/1"

    def quota(self):
        # D2-2 must establish the exact 2.2.5 JSON schema with the owner account.
        # Unknown hours must never be treated as approval to consume GPU.
        self._call("quota", "--format", "json")
        raise SafeStop("Kaggle quota schema not yet live validated; push disabled")

    def confirm_absent(self, ref):
        # A paginated list alone may lag after a canceled push. D2-2 must prove
        # exact-ref 404 semantics before permitting the first live push.
        raise SafeStop("Exact Kaggle slug absence check not yet live validated")


def inspect_attempt(gateway, expected, folder):
    ref = expected["kaggle_ref"]
    state = gateway.status(ref)
    source = gateway.pull_source(ref, folder / "source")
    if source != expected:
        raise SafeStop("Prior Kaggle version has contradictory source")
    if state in ("queued", "running"):
        return {"execution": state, "collection": "incomplete"}
    if state != "complete":
        raise SafeStop("Prior version failed or is unknown; manual review required")
    out = folder / "output"
    out.mkdir(parents=True, exist_ok=True)
    gateway.output(ref, out)
    result = verify_output(out, expected, source)
    return {"execution": state, **result}


def zero_generation_failure(gateway, expected, folder):
    ref = expected["kaggle_ref"]
    if gateway.status(ref) != "error":
        raise SafeStop("Prior attempt is not a verified terminal error")
    source = gateway.pull_source(ref, folder / "source")
    if source != expected:
        raise SafeStop("Failed attempt source differs from approved input")
    out = folder / "output"
    out.mkdir(parents=True, exist_ok=True)
    gateway.output(ref, out)
    manifest = read_json(out / "manifest.json")
    if (manifest.get("input") != expected or manifest.get("generation_started") != 0
            or manifest.get("generation_completed") != 0 or manifest.get("records") != []
            or manifest.get("completion_reason") != "incomplete"):
        raise SafeStop("Failed attempt generation count is unknown or nonzero")
    return True


def step(plan, rows, prompt, index, gateway, exclusive_gpu_reservation=False,
         work_root=None, allow_retry=False):
    series = batches(plan)
    if index > len(series):
        return {"action": "no_batch"}
    if index < 1:
        raise SafeStop("Invalid batch index")
    if not exclusive_gpu_reservation:
        raise SafeStop("Owner GPU reservation is required")
    prefix = f"qwen3-4b-vocab-{plan['mode']}-{plan['experiment_id']}-"
    refs = gateway.list_refs(prefix)
    if any(not re.fullmatch(rf"{OWNER}/{re.escape(prefix)}b\d{{2}}-a\d{{2}}", ref) for ref in refs):
        raise SafeStop("Unexpected Kaggle notebook under experiment prefix")
    # Includes all D2 notebook refs visible to the account; direct V4 sessions
    # require the owner's reservation because CLI cannot prove their absence.
    other_d2 = gateway.list_refs("qwen3-4b-vocab-")
    for ref in other_d2:
        if ref not in refs and gateway.status(ref + "/1") in ("queued", "running"):
            raise SafeStop("Another D2 GPU notebook is active")
    with tempfile.TemporaryDirectory(dir=work_root) as temp:
        base = Path(temp)
        for previous in range(1, index):
            candidates = [r for r in refs if f"-b{previous:02d}-" in r]
            if not candidates:
                raise SafeStop("Previous batch lacks one exact verified attempt")
            attempt = max(int(r.rsplit("-a", 1)[1]) for r in candidates)
            if len(candidates) != attempt:
                raise SafeStop("Previous batch attempt sequence is incomplete")
            for failed in range(1, attempt):
                zero_generation_failure(gateway, config(plan, rows, prompt, previous, failed),
                                        base / f"prev{previous}failed{failed}")
            result = inspect_attempt(gateway, config(plan, rows, prompt, previous, attempt), base / f"prev{previous}")
            if result.get("quality") != "parse_valid":
                raise SafeStop("Previous batch is unverified or needs review")
        current = sorted(r for r in refs if f"-b{index:02d}-" in r)
        next_attempt = 1
        if current:
            attempt = max(int(r.rsplit("-a", 1)[1]) for r in current)
            if len(current) != attempt:
                raise SafeStop("Current batch attempt sequence is incomplete")
            for failed in range(1, attempt):
                zero_generation_failure(gateway, config(plan, rows, prompt, index, failed),
                                        base / f"currentfailed{failed}")
            cfg_old = config(plan, rows, prompt, index, attempt)
            state = gateway.status(cfg_old["kaggle_ref"])
            if state == "error" and allow_retry and plan["mode"] == "full":
                zero_generation_failure(gateway, cfg_old, base / "currentfailedlast")
                next_attempt = attempt + 1
            else:
                result = inspect_attempt(gateway, cfg_old, base / "current")
                if result.get("quality") == "needs_review":
                    raise SafeStop("Raw preserved on Kaggle; parse needs review; no retry")
                if result.get("quality") == "parse_valid":
                    return {"action": "already_verified", **result}
                raise SafeStop("Existing Kaggle attempt is still active; no replacement")
        # Strict automatic generation budget: a missing attempt after earlier
        # verified batches may start; failed attempts require owner reconciliation.
        used = sum(len(x) for x in series[:index - 1])
        remaining = sum(len(x) for x in series[index - 1:])
        if used + remaining > plan["generation_budget"]:
            raise SafeStop("Generation budget exhausted or unknown")
        quota = gateway.quota()
        minimum = 3600 if plan["mode"] == "poc" else plan["timeout_seconds"]
        if type(quota) is not int or quota < minimum:
            raise SafeStop("Kaggle GPU quota is insufficient or unknown")
        if plan.get("quota_preflight_verified") is not True:
            raise SafeStop("Quota parser has not been owner approved")
        cfg = config(plan, rows, prompt, index, next_attempt)
        if gateway.confirm_absent(cfg["kaggle_ref"]) is not True:
            raise SafeStop("Kaggle version absence is unknown")
        push_dir = base / "push"
        prepare_push(push_dir, cfg)
        ref = gateway.push(push_dir, slug(plan, index, next_attempt),
                           3600 if plan["mode"] == "poc" else plan["timeout_seconds"])
        if ref != cfg["kaggle_ref"]:
            raise SafeStop("Push returned a different Kaggle version")
        # The subsequent poll never launches another attempt. A canceled Actions
        # job leaves a discoverable private slug for the next dispatch.
        deadline = time.monotonic() + (3900 if plan["mode"] == "poc" else plan["timeout_seconds"] + 300)
        while time.monotonic() < deadline:
            status = gateway.status(ref)
            if status in ("queued", "running"):
                time.sleep(30)
                continue
            return {"action": "pushed", **inspect_attempt(gateway, cfg, base / "pushed")}
        raise SafeStop("Actions poll timed out; Kaggle may still be running")


def local_status(plan, rows, prompt, gateway, download_dir=None):
    prefix = f"qwen3-4b-vocab-{plan['mode']}-{plan['experiment_id']}-"
    refs = gateway.list_refs(prefix)
    summary = []
    with tempfile.TemporaryDirectory() as temp:
        for index, _ in enumerate(batches(plan), 1):
            candidates = [r for r in refs if f"-b{index:02d}-" in r]
            if not candidates:
                summary.append({"batch": index, "status": "not_started"})
                continue
            attempt = max(int(r.rsplit("-a", 1)[1]) for r in candidates)
            if len(candidates) != attempt:
                raise SafeStop("Attempt sequence cannot be reconstructed")
            for failed in range(1, attempt):
                zero_generation_failure(gateway, config(plan, rows, prompt, index, failed),
                                        Path(temp) / f"{index}-failed-{failed}")
            cfg = config(plan, rows, prompt, index, attempt)
            folder = Path(temp) / str(index)
            result = inspect_attempt(gateway, cfg, folder)
            summary.append({"batch": index, "kaggle_ref": cfg["kaggle_ref"], **result})
            if download_dir is not None and result.get("collection") == "verified_complete":
                target = Path(download_dir) / f"batch-{index:02d}-attempt-{attempt:02d}"
                if target.exists():
                    raise SafeStop("Download target exists; refusing overwrite")
                shutil.copytree(folder / "output", target)
    return summary


def download_verified(plan, rows, prompt, gateway, output_base):
    output_base = Path(output_base)
    target = output_base / plan["experiment_id"]
    if target.exists():
        raise SafeStop("Experiment download directory exists; refusing overwrite")
    output_base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output_base) as temp:
        staging = Path(temp) / "result"
        staging.mkdir()
        summary = local_status(plan, rows, prompt, gateway, staging)
        if (len(summary) != len(batches(plan))
                or any(x.get("quality") != "parse_valid" for x in summary)):
            raise SafeStop("All batches must be verified before merging")
        merged = []
        for index, ids in enumerate(batches(plan), 1):
            attempt = int(summary[index - 1]["kaggle_ref"].rsplit("-a", 1)[1].split("/", 1)[0])
            folder = staging / f"batch-{index:02d}-attempt-{attempt:02d}"
            for number in ids:
                parsed = read_json(folder / f"parsed_{number:03d}.json")
                merged.append({"source_row_index": number, "parsed": parsed["parsed"]})
        expected = list(POC_IDS) if plan["mode"] == "poc" else list(range(1, 101))
        if [r["source_row_index"] for r in merged] != expected:
            raise SafeStop("Merged records have missing or duplicate IDs")
        (staging / "merged.json").write_text(json.dumps({"experiment_id": plan["experiment_id"],
            "kaggle_versions": [x["kaggle_ref"] for x in summary], "records": merged},
            ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        historical_path = ROOT / "reports/image_pipeline_benchmark/20261106-image-query-v1/query_experiment.json"
        if historical_path.is_file():
            historical = {r["source_row_index"]: r["variant_b"].get("parsed")
                          for r in read_json(historical_path)["records"]}
            comparison = [{"source_row_index": row["source_row_index"],
                           "qwen4b_variant_b": row["parsed"],
                           "qwen1_7b_variant_b": historical[row["source_row_index"]]}
                          for row in merged if row["source_row_index"] in historical]
            (staging / "comparison_existing_1_7b.json").write_text(
                json.dumps(comparison, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if target.exists():
            raise SafeStop("Experiment download directory appeared; refusing overwrite")
        staging.rename(target)
        return {"downloaded_to": str(target), "records": len(merged),
                "versions": [x["kaggle_ref"] for x in summary]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("approval", "gate", "step", "status", "download"))
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--mode", choices=("poc", "full", "resume"))
    parser.add_argument("--variant", choices=("A", "B", "A+B"), default="B")
    parser.add_argument("--index", type=int)
    parser.add_argument("--exclusive-gpu-reservation", action="store_true")
    parser.add_argument("--output-base", type=Path, default=ROOT / "reports/kaggle_batch_runs")
    parser.add_argument("--pinned-root", type=Path)
    args = parser.parse_args()
    try:
        if args.variant != "B":
            raise SafeStop("Variant A/A+B require a separate approved experiment; D2 POC/full is B")
        plan, rows, prompt = load_plan(args.experiment_id, args.mode)
        if args.pinned_root:
            verify_pinned_inputs(plan, args.pinned_root)
        elif args.command in ("gate", "step"):
            raise SafeStop("Pinned input checkout is required before any live action")
        if args.command == "approval":
            print(plan["approved_commit"])
            return
        if args.command == "gate":
            if not args.exclusive_gpu_reservation:
                raise SafeStop("GPU reservation not confirmed")
            print(plan["approved_commit"])
            return
        gateway = KaggleCLI()
        if args.command == "step":
            if args.index is None:
                raise SafeStop("Batch index required")
            result = step(plan, rows, prompt, args.index, gateway, args.exclusive_gpu_reservation,
                          allow_retry=args.mode == "resume")
        elif args.command == "status":
            result = local_status(plan, rows, prompt, gateway)
        else:
            result = download_verified(plan, rows, prompt, gateway, args.output_base)
        if args.command == "step" and result.get("quality") == "needs_review":
            raise SafeStop("Batch output preserved on Kaggle but needs review")
        print(json.dumps(result, ensure_ascii=False))
    except SafeStop as error:
        parser.exit(2, f"D2 safe stop: {error}\n")


if __name__ == "__main__":
    main()
