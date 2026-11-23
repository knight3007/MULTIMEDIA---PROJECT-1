"""Offline contract tests for the isolated B-002 importer."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/b001"
MODULE = Path(__file__).with_name("excel_vocabulary_importer.py")
spec = importlib.util.spec_from_file_location("excel_vocabulary_importer", MODULE)
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)


def change_zip(source, destination, replacements):
    with ZipFile(source) as original, ZipFile(destination, "w") as target:
        for entry in original.infolist():
            data = original.read(entry.filename)
            for old, new in replacements.get(entry.filename, []):
                assert old in data
                data = data.replace(old, new)
            target.writestr(entry, data)


class ExcelImporterTests(unittest.TestCase):
    def test_authored_fixtures(self):
        expected = json.loads((FIXTURES / "expected.json").read_text(encoding="utf-8"))["cases"]
        for name, case in expected.items():
            with self.subTest(name=name):
                result = importer.validate(FIXTURES / name)
                self.assertEqual([x["code"] for x in result["diagnostics"] if x["severity"] == "error"],
                                 [x["code"] for x in case["errors"]])
                self.assertEqual([x["source_row"] for x in result["rows"]] if result["valid"] else [], case["accepted_rows"])
                self.assertEqual([x["row"] for x in result["diagnostics"] if x["code"] == "EMPTY_ROW"], case["empty_rows"])
                if "normalized_row" in case:
                    self.assertEqual([result["rows"][0][field] for field in importer.FIELDS], case["normalized_row"])
                if name == "excel_duplicate.xlsx":
                    self.assertEqual(result["diagnostics"][0]["related_row"], 2)

    def test_accept_retry_ids_and_isolation(self):
        benchmark = ROOT / "data/vocabulary/unified_dataset_v1.json"
        before = hashlib.sha256(benchmark.read_bytes()).hexdigest()
        source = FIXTURES / "excel_valid.xlsx"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "private_import.json"
            first = importer.accept(source, output)
            self.assertEqual(importer.accept(source, resume=output, import_id=first["import_id"]), first)
            self.assertEqual(first["rows"][0]["source_row"], 2)
            self.assertEqual(len(first["rows"]), 3)
            self.assertTrue(first["import_id"].startswith("imp-"))
            self.assertTrue(first["pack_id"].startswith("pack-"))
            self.assertEqual(len({x["item_id"] for x in first["rows"]}), 3)
            self.assertTrue(all(x["item_id"].startswith("item-") for x in first["rows"]))
            self.assertEqual(first["normalized_payload_sha256"], importer.payload_hash(first["rows"]))
            with self.assertRaises(FileExistsError):
                importer.accept(source, output)
            another = importer.accept(source, Path(directory) / "another.json")
            self.assertNotEqual(first["import_id"], another["import_id"])
            with self.assertRaisesRegex(ValueError, "conflict"):
                importer.accept(FIXTURES / "excel_unicode.xlsx", resume=output, import_id=first["import_id"])
            with self.assertRaisesRegex(ValueError, "conflict"):
                importer.accept(source, resume=output, import_id="imp-wrong")
        self.assertEqual(hashlib.sha256(benchmark.read_bytes()).hexdigest(), before)

    def test_errors_and_preview_determinism(self):
        source = FIXTURES / "excel_valid.xlsx"
        self.assertEqual(importer.validate(source), importer.validate(source))
        self.assertEqual(importer.validate(source)["normalized_payload_sha256"],
                         "d7efbaf23abac2e23c637c8e8f24089763dc12a45d0547f9884154a77a20eaaf")
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            self.assertEqual(importer.validate(directory / "missing.xlsx")["diagnostics"][0]["code"], "INVALID_WORKBOOK")
            bad = directory / "bad.xlsx"
            bad.write_bytes(b"not a workbook")
            self.assertEqual(importer.validate(bad)["diagnostics"][0]["code"], "INVALID_WORKBOOK")
            self.assertEqual(importer.validate(source.with_suffix(".xls"))["diagnostics"][0]["code"], "INVALID_WORKBOOK")

    def test_unsupported_cells_and_required_values(self):
        source = FIXTURES / "excel_valid.xlsx"
        with ZipFile(source) as archive:
            sheet = archive.read("xl/worksheets/sheet1.xml")
        self.assertIn(b'<x:c r="A2"', sheet)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.xlsx"
            change_zip(source, path, {"xl/worksheets/sheet1.xml": [
                (b'<x:c r="A2" s="1" t="str"><x:v>apple</x:v></x:c>', b'<x:c r="A2"><x:f>1+1</x:f><x:v>2</x:v></x:c>'),
                (b'<x:c r="A3" s="1" t="str"><x:v>cat</x:v></x:c>', b'<x:c r="A3" s="1" />')]})
            result = importer.validate(path)
            self.assertFalse(result["valid"])
            self.assertTrue(any(x["code"] == "UNSUPPORTED_CELL" and x["row"] == 2 and x["column"] == "english" for x in result["diagnostics"]))
            self.assertTrue(any(x["code"] == "REQUIRED_VALUE" and x["row"] == 3 and x["column"] == "english" for x in result["diagnostics"]))

    def test_more_than_100_rows(self):
        source = FIXTURES / "excel_valid.xlsx"
        with ZipFile(source) as archive:
            sheet = archive.read("xl/worksheets/sheet1.xml")
        end = b"</x:sheetData>"
        self.assertIn(end, sheet)
        rows = b"".join(
            f'<x:row r="{n}"><x:c r="A{n}" t="inlineStr"><x:is><x:t>word {n}</x:t></x:is></x:c>'
            f'<x:c r="B{n}" t="inlineStr"><x:is><x:t>\u3042</x:t></x:is></x:c>'
            f'<x:c r="C{n}" t="inlineStr"><x:is><x:t>ngh\u0129a {n}</x:t></x:is></x:c></x:row>'.encode("utf-8")
            for n in range(5, 104))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "large.xlsx"
            change_zip(source, path, {"xl/worksheets/sheet1.xml": [(end, rows + end)]})
            result = importer.validate(path)
            self.assertTrue(result["valid"], result["diagnostics"])
            self.assertEqual(len(result["rows"]), 102)
            self.assertEqual(result["rows"][-1]["source_row"], 103)

    def test_unsupported_sheet_merge_and_control_text(self):
        source = FIXTURES / "excel_valid.xlsx"
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            wrong_sheet = directory / "wrong_sheet.xlsx"
            change_zip(source, wrong_sheet, {"xl/workbook.xml": [(b'name="Vocabulary"', b'name="Words"')]})
            self.assertEqual(importer.validate(wrong_sheet)["diagnostics"][0]["code"], "INVALID_SHEET")
            merged = directory / "merged.xlsx"
            change_zip(source, merged, {"xl/worksheets/sheet1.xml": [
                (b"</x:sheetData>", b'</x:sheetData><x:mergeCells><x:mergeCell ref="A2:B2" /></x:mergeCells>')]})
            self.assertEqual(importer.validate(merged)["diagnostics"][0]["code"], "INVALID_WORKBOOK")
            newline = directory / "newline.xlsx"
            change_zip(source, newline, {"xl/worksheets/sheet1.xml": [
                (b'<x:v>apple</x:v>', b'<x:v>apple&#10;</x:v>')]})
            issues = importer.validate(newline)["diagnostics"]
            self.assertTrue(any(x["code"] == "INVALID_TEXT" and x["row"] == 2 and x["column"] == "english" for x in issues))


if __name__ == "__main__":
    unittest.main()
