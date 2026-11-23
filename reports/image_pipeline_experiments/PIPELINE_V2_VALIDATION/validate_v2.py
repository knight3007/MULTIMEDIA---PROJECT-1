"""Run prompt v2 (local Qwen) on the 100 benchmark words and score routes against the frozen expectations.

Each run is saved as runs/iterNN.json (never overwritten). No search, no SigLIP.
"""
import csv
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "collect data script"))
import visual_query_policy as policy  # noqa: E402
from query_generator import DEFAULT_QWEN_MODEL, QueryGenerationError, QwenQueryGenerator  # noqa: E402


def main():
    criteria = json.loads((HERE / "acceptance_criteria.json").read_text(encoding="utf-8"))
    expected_path = HERE / "expected_routes.csv"
    if hashlib.sha256(expected_path.read_bytes()).hexdigest() != criteria["expected_routes_sha256"]:
        raise SystemExit("expected_routes.csv changed after freeze")
    with expected_path.open(encoding="utf-8", newline="") as file:
        expected = list(csv.DictReader(file))
    runs = HERE / "runs"
    runs.mkdir(exist_ok=True)
    iteration = len(list(runs.glob("iter*.json"))) + 1
    if iteration > criteria["max_prompt_iterations"]:
        raise SystemExit("prompt iteration budget exhausted")
    generator = QwenQueryGenerator(DEFAULT_QWEN_MODEL, batch_size=4)
    started = time.perf_counter()
    rows = []
    try:
        generator._load()
        for row in expected:
            try:
                typed = policy.classify_words([row["english"]], generator)[0]
                rows.append({**row, "word_type": typed.word_type, "route": typed.route, "query": typed.query, "error": None})
            except QueryGenerationError as error:
                rows.append({**row, "word_type": None, "route": None, "query": None, "error": str(error)})
    finally:
        generator.close()

    def share(kind, ok):
        group = [r for r in rows if r["expected_route"] == kind]
        hits = [r for r in group if ok(r)]
        return len(hits), len(group), [r["english"] for r in group if not ok(r)]

    photo = share("PHOTO", lambda r: r["route"] == "PHOTO")
    non_photo = share("NON_PHOTO", lambda r: r["route"] in {"ICON", "SCENE", "CURATE"})
    curate = share("CURATE", lambda r: r["route"] == "CURATE")
    valid = sum(r["error"] is None for r in rows)
    c = criteria["criteria"]
    passed = (photo[0] / photo[1] >= c["PHOTO_kept_concrete_min"] and non_photo[0] / non_photo[1] >= c["NON_PHOTO_routed_away_min"]
              and curate[0] == curate[1] and valid == len(rows))
    result = {"iteration": iteration, "run_at_utc": datetime.now(timezone.utc).isoformat(), "model": DEFAULT_QWEN_MODEL,
              "prompt_sha256": hashlib.sha256(policy.TYPED_PROMPT.encode("utf-8")).hexdigest(),
              "policy_version": policy.POLICY_VERSION, "seconds": round(time.perf_counter() - started, 1),
              "metrics": {"PHOTO_kept": photo[:2], "PHOTO_misses": photo[2],
                          "NON_PHOTO_routed_away": non_photo[:2], "NON_PHOTO_misses": non_photo[2],
                          "CURATE": curate[:2], "valid_queries": [valid, len(rows)],
                          "route_counts": {k: sum(r["route"] == k for r in rows) for k in ("PHOTO", "ICON", "SCENE", "CURATE", None)}},
              "passed": passed, "rows": rows}
    out = runs / f"iter{iteration:02d}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
