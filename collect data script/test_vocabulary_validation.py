"""Offline structural checks for the three source vocabulary files."""

import tempfile
import unittest
from pathlib import Path

from validate_vocabulary import validate_sources


class VocabularyValidationTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def sources(self, en: str, jp: str, vn: str):
        paths = {}
        for language, content in (("en", en), ("jp", jp), ("vn", vn)):
            path = self.root / f"{language}.txt"
            path.write_text(content, encoding="utf-8")
            paths[language] = path
        return paths

    def test_valid_rows_preserve_physical_order(self):
        rows, issues = validate_sources(
            self.sources("apple\nbanana\n", "りんご\nバナナ\n", "táo\nchuối\n"),
            expected_count=2,
        )
        self.assertEqual(issues, [])
        self.assertEqual(rows[1], ("banana", "バナナ", "chuối"))

    def test_empty_row_retains_line_number_and_count_mismatch_is_reported(self):
        rows, issues = validate_sources(
            self.sources("apple\n\nbanana\n", "りんご\nバナナ\n", "táo\nchuối\n"),
            expected_count=3,
        )
        self.assertEqual(rows[1], ("", "バナナ", "chuối"))
        self.assertTrue(any("en: line 2: empty" in issue for issue in issues))
        self.assertTrue(any("jp: expected 3 lines, found 2" in issue for issue in issues))

    def test_duplicate_after_trim_and_trailing_space_are_reported(self):
        _, issues = validate_sources(
            self.sources("apple\napple  \n", "りんご\nバナナ\n", "táo\nchuối\n"),
            expected_count=2,
        )
        self.assertTrue(any("en: line 2: surrounding whitespace" in issue for issue in issues))
        self.assertTrue(any("en: line 2: duplicate of line 1" in issue for issue in issues))

    def test_invalid_utf8_is_reported(self):
        paths = self.sources("apple\n", "りんご\n", "táo\n")
        paths["jp"].write_bytes(b"\xff")
        _, issues = validate_sources(paths, expected_count=1)
        self.assertTrue(any("jp: invalid UTF-8" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
