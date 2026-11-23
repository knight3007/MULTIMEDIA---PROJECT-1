"""Build an unverified A-001.1 baseline and owner review queue from saved A-001 evidence."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "evaluation_matrix.json"
STATS = HERE / "statistics.json"
AUDIO = HERE / "owner_audio_acceptance.json"
ALLOWED = {"PASS", "FAIL", "NEEDS_REVIEW", "UNKNOWN"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    items = data["items"]
    assert len(items) == 100
    assert [x["vocab_id"] for x in items] == [f"vocab-{n:06d}" for n in range(1, 101)]
    assert all(x["human_review"]["query"] == x["human_review"]["image"] == "NOT_REVIEWED" for x in items)
    assert all(x["audio_pronunciation_review"] == "PASS" for x in items)
    assert json.loads(STATS.read_text(encoding="utf-8"))["new_independent_query_image_labels"] == 0
    assert AUDIO.is_file()
    queue, baseline = [], []
    for x in items:
        query, image = x["query_overall"], x["image_learning_suitability"]
        relevance, visual = x["image_relevance"], x["image_visual_quality"]
        assert {query, image, relevance, visual} <= ALLOWED
        critical = (not x["image_path"] or "FAIL" in (query, image, relevance, visual, x["query_assessment"]["correct_meaning"]))
        uncertain = ("NEEDS_REVIEW" in (query, image, relevance, visual) or "UNKNOWN" in (query, image, relevance, visual))
        priority = "P1" if critical else "P2" if uncertain else "P3"
        issues = []
        if not x["image_path"]:
            issues.append("missing selected image")
        if x["query_assessment"]["correct_meaning"] == "FAIL":
            issues.append("query meaning mismatch (AI preliminary)")
        if query == "FAIL" and "query meaning mismatch (AI preliminary)" not in issues:
            issues.append("query overall FAIL (AI preliminary)")
        for label, value in (("image relevance", relevance), ("image visual quality", visual), ("image learning suitability", image)):
            if value == "FAIL":
                issues.append(f"{label} FAIL (AI preliminary)")
        if not issues:
            issues.append("ambiguous preliminary assessment" if uncertain else "verify preliminary PASS")
        classes = "; ".join(f"{a['classification']} [{a['certainty']}]" for a in x["error_attribution"])
        evidence = "; ".join(p for p in ("evaluation_matrix.json", x["query_evidence_path"], x["image_path"] or "MISSING_EVIDENCE: image", x["audio_path"]) if p)
        action = "Resolve intended sense and review query; inspect full image and label separately" if priority != "P3" else "Independently verify query and full image"
        common = {"vocab_id": x["vocab_id"], "english": x["english"], "japanese": x["japanese"], "vietnamese": x["vietnamese"]}
        queue.append({**common, "priority": priority, "ai_query_overall": query, "ai_image_relevance": relevance,
                      "ai_image_visual_quality": visual, "ai_image_learning_suitability": image,
                      "human_query": "NOT_REVIEWED", "human_image": "NOT_REVIEWED", "suspected_issue": "; ".join(issues),
                      "failure_category": classes, "evidence_reference": evidence, "recommended_review_action": action})
        baseline.append({**common,
            "expected_semantic_meaning": x["target_sense"] or "UNRESOLVED: infer only after owner checks EN/JP/VN context",
            "semantic_decision_status": (x["semantic_decision"] or {}).get("review_status", "NOT_RECORDED"),
            "original_qwen_query": x["parsed_qwen_query"], "effective_image_query": x["effective_image_query"],
            "query_model": x["query_model"], "query_prompt_version_evidence": x["prompt_version_evidence"],
            "query_model_revision": x["model_revision"], "ai_query_overall": query,
            "ai_query_correct_meaning": x["query_assessment"]["correct_meaning"], "ai_query_reason": x["query_reason"],
            "human_query": "NOT_REVIEWED", "selected_image_path": x["image_path"] or "MISSING_EVIDENCE",
            "selected_image_sha256": x["image_sha256"] or "MISSING_EVIDENCE",
            "image_technical": x["image_technical"]["status"], "ai_image_relevance": relevance,
            "ai_image_visual_quality": visual, "ai_image_learning_suitability": image,
            "image_observation": x["image_scene_observation"], "human_image": "NOT_REVIEWED",
            "audio_path": x["audio_path"], "audio_sha256": x["audio_sha256"],
            "audio_technical": x["audio_technical"]["status"], "audio_owner_acceptance": "PASS",
            "audio_acceptance_basis": x["audio_acceptance_basis"], "failure_category": classes,
            "evidence_references": evidence, "missing_evidence": "; ".join(x["missing_evidence"]),
            "reviewer": "", "reviewer_comments": ""})
    counts = Counter(row["priority"] for row in queue)
    write_csv(HERE / "review_priority_queue.csv", queue)
    write_csv(HERE / "preliminary_unverified_baseline_v1.csv", baseline)
    print(json.dumps({"run_id": data["run_id"], "source_sha256": sha(SOURCE), "priority_counts": dict(sorted(counts.items())),
                      "human_query_image_reviews": 0, "audio_owner_accepted": 100}, ensure_ascii=False))


if __name__ == "__main__":
    main()
