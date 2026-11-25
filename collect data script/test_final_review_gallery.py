"""Focused checks for the final review gallery's real Content Pack data."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_final_review_gallery as gallery

RUN = HERE.parent / "reports" / "EXCEL_FULL_PIPELINE_FINAL" / "run-88c4196d-dc59-497e-a389-76a564615483"


class FinalGalleryTests(unittest.TestCase):
    def test_real_pack_counts_and_language_mapping(self):
        cards, summary = gallery.load_review_data(RUN)
        self.assertEqual(len(cards), 100)
        self.assertEqual(len({card["id"] for card in cards}), 100)
        self.assertEqual(summary, {"items": 100, "images": 99, "missing_images": 1,
                                   "english_audio": 100, "japanese_audio": 100,
                                   "needs_review": 99, "errors": 1})
        self.assertTrue(all(card["english"] and card["japanese"] and card["vietnamese"] for card in cards))
        self.assertTrue(all(card["audio_en"]["text"] == card["english"] and card["audio_en"]["locale"] == "en"
                            and card["audio_ja"]["text"] == card["japanese"] and card["audio_ja"]["locale"] == "ja" for card in cards))
        self.assertEqual([card["image_status"] for card in cards if card["english"] == "sometimes"], ["NO_SUITABLE_IMAGE"])
        self.assertTrue(all((RUN / card["image"]["path"]).is_file() for card in cards if card["image"]))

    def test_embedded_json_cannot_close_script(self):
        encoded = gallery.embed_json([{"english": '</script><script>alert("x")</script>', "japanese": "りんご"}])
        self.assertNotIn("<script", encoded)
        self.assertNotIn("</script", encoded)
        self.assertIn("りんご", encoded)


if __name__ == "__main__":
    unittest.main()
