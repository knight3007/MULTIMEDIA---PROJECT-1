"""Focused checks for Docker's gallery orchestration and resume guard."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import docker_pipeline


class DockerPipelineTests(unittest.TestCase):
    def test_builds_final_gallery_from_active_pack(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "execution_report.json").write_text(
                json.dumps({"active_content_pack": "content_pack_v46", "images": {}, "audio": {}}), encoding="utf-8")
            with patch.object(docker_pipeline, "ensure_siglip_for_new_images"), \
                    patch.object(docker_pipeline, "execute", return_value=root) as execute, \
                    patch.object(docker_pipeline, "build", return_value={"valid": True}) as build:
                self.assertEqual(docker_pipeline.run(Path("words.xlsx")), root)
            execute.assert_called_once()
            build.assert_called_once_with(root, "content_pack_v46")

    def test_resume_refuses_gallery_for_changed_pack(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pack = root / "content_pack_v46"
            pack.mkdir()
            (pack / "content_pack.json").write_bytes(b"new pack")
            (root / "execution_report.json").write_text(
                json.dumps({"active_content_pack": pack.name, "images": {}, "audio": {}}), encoding="utf-8")
            (root / "final_review_gallery.html").write_text("old gallery", encoding="utf-8")
            (root / "final_gallery_validation_report.json").write_text(json.dumps({
                "source_content_pack": f"{pack.name}/content_pack.json",
                "source_sha256": hashlib.sha256(b"old pack").hexdigest(),
            }), encoding="utf-8")
            with patch.object(docker_pipeline, "ensure_siglip_for_new_images"), \
                    patch.object(docker_pipeline, "execute", return_value=root), \
                    patch.object(docker_pipeline, "build") as build:
                with self.assertRaises(FileExistsError):
                    docker_pipeline.run(Path("words.xlsx"), root)
            build.assert_not_called()
            self.assertEqual((root / "final_review_gallery.html").read_text(), "old gallery")

    def test_reports_failed_stage_as_command_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "execution_report.json").write_text(json.dumps({
                "active_content_pack": "content_pack", "images": {"QUERY_FAILED": 15}, "audio": {},
            }), encoding="utf-8")
            with patch.object(docker_pipeline, "ensure_siglip_for_new_images"), \
                    patch.object(docker_pipeline, "execute", return_value=root), \
                    patch.object(docker_pipeline, "build", return_value={"valid": True}):
                with self.assertRaisesRegex(RuntimeError, "QUERY_FAILED"):
                    docker_pipeline.run(Path("words.xlsx"))


if __name__ == "__main__":
    unittest.main()
