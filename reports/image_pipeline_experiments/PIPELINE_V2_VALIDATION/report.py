"""Summarize all prompt v2 iterations and write validation_report.md + freeze_manifest.json."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FROZEN = ["collect data script/visual_query_policy.py", "collect data script/image_pipeline_v2.py",
          "collect data script/test_image_pipeline_v2.py", "collect data script/imagecollector.py",
          "collect data script/image_scorer.py", "collect data script/query_generator.py",
          "data/vocabulary/approved_images_v1.json", "docs/IMAGE_PIPELINE_V2.md"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    criteria = json.loads((HERE / "acceptance_criteria.json").read_text(encoding="utf-8"))
    runs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((HERE / "runs").glob("iter*.json"))]
    final = runs[-1]
    lines = ["# Pipeline v2 validation (prompt v2 word-type routing)", "",
             f"Frozen expectations: `expected_routes.csv` SHA `{criteria['expected_routes_sha256'][:16]}…`, derived from the owner-approved final selection before any inference. "
             f"Counts: {criteria['counts']}. Criteria: PHOTO kept ≥ {criteria['criteria']['PHOTO_kept_concrete_min']:.0%}, "
             f"NON_PHOTO routed away ≥ {criteria['criteria']['NON_PHOTO_routed_away_min']:.0%}, CURATE exact, 100% valid queries. "
             f"Budget: {criteria['max_prompt_iterations']} prompt iterations. Model Qwen3-1.7B, greedy, local.", "",
             "| Iteration | PHOTO kept | NON_PHOTO away | CURATE | Valid | Passed | Prompt SHA |", "|---|---|---|---|---|---|---|"]
    for r in runs:
        m = r["metrics"]
        lines.append(f"| {r['iteration']} | {m['PHOTO_kept'][0]}/{m['PHOTO_kept'][1]} | {m['NON_PHOTO_routed_away'][0]}/{m['NON_PHOTO_routed_away'][1]} | "
                     f"{m['CURATE'][0]}/{m['CURATE'][1]} | {m['valid_queries'][0]}/{m['valid_queries'][1]} | {r['passed']} | `{r['prompt_sha256'][:12]}` |")
    m = final["metrics"]
    lines += ["", f"Final iteration misses — PHOTO: {m['PHOTO_misses'] or 'none'}; NON_PHOTO: {m['NON_PHOTO_misses'] or 'none'}.",
              f"Invalid outputs: {[r['english'] for r in final['rows'] if r['error']] or 'none'}.", "",
              "Changes between iterations: (1→2) prompt states that persons, places, institutions, meals and drinks are CONCRETE; "
              "replaced examples that Qwen copied (idea light bulb, night sky); TIME uses calendar/clock; collision tokens are stripped instead of fatal. "
              "(2→3) code rejects CONCRETE answers with a non-physical class (action, activity, abstract, organization…) so the corrective retry reroutes them; "
              "digits, apostrophes and meta words are stripped; question-word, action and frequency examples added; 'a verb is never CONCRETE'.", "",
              "## Final iteration, all 100 words", "", "| Word | Expected | Type | Route | Query | Owner-approved query |", "|---|---|---|---|---|---|"]
    for r in final["rows"]:
        lines.append(f"| {r['english']} | {r['expected_route']} | {r['word_type'] or '—'} | {r['route'] or 'ERROR'} | "
                     f"{r['query'] or (r['error'] or '')[:80]} | {r['approved_query']} |")
    (HERE / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    (HERE / "freeze_manifest.json").write_text(json.dumps({
        "policy_version": "image-pipeline-v2", "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_git_head": head, "validation_passed": final["passed"], "final_iteration": final["iteration"],
        "final_prompt_sha256": final["prompt_sha256"], "files": {p: sha(ROOT / p) for p in FROZEN}},
        indent=2) + "\n", encoding="utf-8")
    print("passed" if final["passed"] else "NOT passed", m)


if __name__ == "__main__":
    main()
