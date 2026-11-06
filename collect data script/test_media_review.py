"""Offline checks for exact-byte image review records."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from media_review import promotion_eligible, validate_reviews


class MediaReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run_id = "review-run"
        self.relative = f"baseline/media-staging/images/{self.run_id}/chicken.jpg"
        image_path = self.root / self.relative
        image_path.parent.mkdir(parents=True)
        image_path.write_bytes(b"candidate bytes")
        self.digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
        manifest = {"schema_version": 1, "run_id": self.run_id, "targets": [
            {"vocab_id": "vocab-000009", "target_sense": "chicken meat",
             "effective_query": "chicken meat", "status": "staged",
             "staged_image_path": self.relative,
             "selected_result": {"image_url": "https://example.test/chicken.jpg",
                                 "source_page_url": "https://example.test/file"}}]}
        (image_path.parent / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        self.review = {"vocab_id": "vocab-000009", "asset_type": "image",
                       "staging_run_id": self.run_id, "candidate_path": self.relative,
                       "sha256": self.digest, "target_sense": "chicken meat",
                       "target_sense_approval": "owner_approved",
                       "visual_review": {"semantic_match": True,
                                         "production_suitability": "suitable"},
                       "license_status": "verified_permitted",
                       "source_evidence": {"image_url": "https://example.test/chicken.jpg",
                                           "source_page_url": "https://example.test/file",
                                           "license_url": "https://example.test/license",
                                           "author": "Example", "attribution": "none"},
                       "owner_promotion_approval": "pending", "notes": "reviewed"}

    def test_valid_record_binds_exact_asset_and_does_not_grant_approval(self):
        validate_reviews(self.root, {"schema_version": 1, "reviews": [self.review]})
        self.assertFalse(promotion_eligible(self.review))

    def test_changed_bytes_or_wrong_run_are_rejected(self):
        (self.root / self.relative).write_bytes(b"different bytes")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            validate_reviews(self.root, {"schema_version": 1, "reviews": [self.review]})
        (self.root / self.relative).write_bytes(b"candidate bytes")
        self.review["staging_run_id"] = "other-run"
        with self.assertRaises(ValueError):
            validate_reviews(self.root, {"schema_version": 1, "reviews": [self.review]})

    def test_verified_license_requires_source_and_license_evidence(self):
        self.review["source_evidence"]["license_url"] = None
        with self.assertRaisesRegex(ValueError, "license"):
            validate_reviews(self.root, {"schema_version": 1, "reviews": [self.review]})

    def test_source_evidence_must_match_staged_selection(self):
        self.review["source_evidence"]["image_url"] = "https://example.test/other.jpg"
        with self.assertRaisesRegex(ValueError, "source"):
            validate_reviews(self.root, {"schema_version": 1, "reviews": [self.review]})

    def test_watermarked_candidate_is_ineligible_even_with_license_and_owner(self):
        self.review["visual_review"]["production_suitability"] = "blocked_watermark"
        self.review["owner_promotion_approval"] = "approved"
        self.assertFalse(promotion_eligible(self.review))

    def test_unknown_license_and_pending_owner_are_ineligible(self):
        self.review["license_status"] = "unknown"
        self.review["source_evidence"]["license_url"] = None
        validate_reviews(self.root, {"schema_version": 1, "reviews": [self.review]})
        self.assertFalse(promotion_eligible(self.review))


if __name__ == "__main__":
    unittest.main()
