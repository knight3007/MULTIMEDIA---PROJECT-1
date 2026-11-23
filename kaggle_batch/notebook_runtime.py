"""Self-contained source pasted into a private Kaggle notebook by driver.py.

The rendered notebook defines CONFIG before this source. This module is never
imported by the CPU driver, so offline tests cannot accidentally load Qwen.
"""
import hashlib
import json
import platform
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("/kaggle/working")
TYPES = {"concrete_object", "food", "animal", "person_role", "place", "action",
         "emotion_state", "physical_attribute", "time_weather", "abstract_concept",
         "function_word", "educational_visual"}


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def put(name, document):
    blob = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    (OUT / name).write_bytes(blob)
    return {"file": name, "sha256": digest(blob), "bytes": len(blob)}


def parse(raw, ended):
    if not ended:
        return None, "generation reached token limit without EOS"
    try:
        obj = json.loads(raw)
        keys = {"visual_type", "search_query", "visual_description", "negative_constraints", "reason"}
        if not isinstance(obj, dict) or set(obj) != keys:
            raise ValueError("JSON must contain exactly the five required fields")
        if obj["visual_type"] not in TYPES:
            raise ValueError("unsupported visual_type")
        for key in ("search_query", "visual_description", "reason"):
            if not isinstance(obj[key], str) or not obj[key].strip():
                raise ValueError(f"{key} must be nonempty text")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9 ,'-]*", obj["search_query"]):
            raise ValueError("search_query must be an English search phrase")
        negatives = obj["negative_constraints"]
        if (not isinstance(negatives, list) or len(negatives) > 8
                or any(not isinstance(x, str) or not x.strip() for x in negatives)):
            raise ValueError("negative_constraints must be an array of at most eight nonempty strings")
        return obj, None
    except (ValueError, TypeError) as error:
        return None, str(error)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    manifest = {"schema_version": 1, "input": CONFIG, "started_utc": now(),
                "model": "Qwen/Qwen3-4B", "model_revision": None,
                "records": [], "files": [], "generation_started": 0,
                "generation_completed": 0, "collection": "incomplete",
                "quality": "not_evaluated", "completion_reason": "incomplete",
                "timings_seconds": {}}
    event_log = []
    phase = "environment_setup"
    phase_start = time.monotonic()
    try:
        if CONFIG["variant"] != "B" or len(CONFIG["rows"]) > CONFIG["generation_limit"]:
            raise ValueError("D2 notebook has invalid variant or generation budget")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet",
                               "transformers>=4.51,<5", "accelerate", "huggingface_hub"])
        import torch
        import transformers
        from huggingface_hub import model_info, snapshot_download
        from transformers import AutoModelForCausalLM, AutoTokenizer
        if not torch.cuda.is_available():
            raise RuntimeError("GPU unavailable")
        manifest["environment"] = {"python": platform.python_version(),
                                   "torch": torch.__version__,
                                   "transformers": transformers.__version__,
                                   "cuda": torch.version.cuda,
                                   "gpu": torch.cuda.get_device_name(0)}
        manifest["timings_seconds"][phase] = time.monotonic() - phase_start
        phase = "model_download"
        phase_start = time.monotonic()
        required = CONFIG["model_revision"]
        revision = model_info("Qwen/Qwen3-4B", revision=required).sha
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise RuntimeError("Hugging Face model commit is not verifiable")
        if required != "main" and required != revision:
            raise RuntimeError("Pinned model revision changed")
        model_path = snapshot_download("Qwen/Qwen3-4B", revision=revision)
        if revision not in str(model_path):
            raise RuntimeError("Downloaded model path does not identify expected commit")
        manifest["model_revision"] = revision
        manifest["timings_seconds"][phase] = time.monotonic() - phase_start
        phase = "model_loading"
        phase_start = time.monotonic()
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16,
                                                     device_map={"": 0}).eval()
        manifest["timings_seconds"][phase] = time.monotonic() - phase_start
        phase = "inference"
        phase_start = time.monotonic()
        for row in CONFIG["rows"]:
            if time.monotonic() - started >= CONFIG["inference_cutoff_seconds"]:
                manifest["completion_reason"] = "timeout"
                break
            if manifest["generation_started"] >= CONFIG["generation_limit"]:
                raise RuntimeError("Generation budget exhausted")
            messages = [{"role": "system", "content": CONFIG["system_prompt"]},
                        {"role": "user", "content": row["user_prompt"]}]
            rendered = tokenizer.apply_chat_template(messages, tokenize=False,
                                                      add_generation_prompt=True,
                                                      enable_thinking=False)
            batch = tokenizer([rendered], return_tensors="pt").to("cuda:0")
            input_count = int(batch.input_ids.shape[1])
            if input_count > 2048:
                raise ValueError("Input exceeds 2048 tokens")
            manifest["generation_started"] += 1
            t0 = time.monotonic()
            with torch.inference_mode():
                output = model.generate(**batch, max_new_tokens=256, do_sample=False,
                                        pad_token_id=tokenizer.eos_token_id)
            latency = time.monotonic() - t0
            new_tokens = output[0, input_count:]
            eos = model.generation_config.eos_token_id or tokenizer.eos_token_id
            eos_ids = eos if isinstance(eos, list) else [eos]
            ended = int(new_tokens[-1]) in eos_ids if len(new_tokens) else False
            raw = tokenizer.decode(new_tokens, skip_special_tokens=True)
            parsed, error = parse(raw, ended)
            ident = f"{row['source_row_index']:03d}"
            raw_file = put(f"raw_{ident}.json", {"id": ident, "raw": raw,
                "raw_sha256": digest(raw.encode("utf-8")), "input_tokens": input_count,
                "output_tokens": len(new_tokens), "latency_seconds": latency,
                "ended_with_eos": ended})
            parsed_file = put(f"parsed_{ident}.json", {"id": ident, "parsed": parsed,
                            "error": error, "validation_status": "valid" if error is None else "invalid"})
            manifest["files"].extend([raw_file, parsed_file])
            manifest["records"].append({"id": ident, "vocab_id": row["vocab_id"],
                                         "raw_sha256": digest(raw.encode("utf-8")),
                                         "parse_valid": error is None})
            manifest["generation_completed"] += 1
        manifest["timings_seconds"][phase] = time.monotonic() - phase_start
        if len(manifest["records"]) == len(CONFIG["rows"]):
            manifest["collection"] = "complete"
            manifest["quality"] = ("parse_valid" if all(r["parse_valid"] for r in manifest["records"])
                                   else "needs_review")
            manifest["completion_reason"] = "complete"
        elif manifest["completion_reason"] != "timeout":
            manifest["completion_reason"] = "incomplete"
    except Exception as error:
        event_log.append({"at": now(), "phase": phase, "error_type": type(error).__name__,
                          "message": str(error)[:500]})
        manifest["completion_reason"] = "incomplete"
    finally:
        if phase not in manifest["timings_seconds"]:
            manifest["timings_seconds"][phase] = time.monotonic() - phase_start
        final_started = time.monotonic()
        manifest["finished_utc"] = now()
        manifest["elapsed_seconds"] = time.monotonic() - started
        manifest["files"].append(put("events.json", event_log))
        manifest["timings_seconds"]["output_finalization"] = time.monotonic() - final_started
        if CONFIG["mode"] == "poc" and time.monotonic() - started >= 3600:
            manifest["completion_reason"] = "timeout"
        put("manifest.json", manifest)
    if manifest["completion_reason"] != "complete":
        raise RuntimeError("Batch incomplete; inspect Kaggle version output")


