"""Create a labeled Excel test input from the exact canonical EN/JP/VN text rows."""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

from collector_common import PROJECT_ROOT
from excel_vocabulary_importer import MAIN, validate


def create(output: Path):
    source = PROJECT_ROOT / "data" / "vocabulary"
    columns = [(source / f"{code}.txt").read_text(encoding="utf-8-sig").splitlines() for code in ("en", "jp", "vn")]
    if len({len(x) for x in columns}) != 1 or not columns[0]:
        raise ValueError("Canonical vocabulary columns differ in length")
    rows = [("english", "japanese", "vietnamese"), *zip(*columns)]
    ns = f"{{{MAIN}}}"
    strings = ET.Element(ns + "sst", {"count": str(len(rows) * 3), "uniqueCount": str(len(rows) * 3)})
    sheet = ET.Element(ns + "worksheet")
    data = ET.SubElement(sheet, ns + "sheetData")
    for number, values in enumerate(rows, 1):
        row = ET.SubElement(data, ns + "row", {"r": str(number)})
        for col, value in zip("ABC", values):
            index = (number - 1) * 3 + "ABC".index(col)
            ET.SubElement(ET.SubElement(strings, ns + "si"), ns + "t").text = value
            ET.SubElement(ET.SubElement(row, ns + "c", {"r": f"{col}{number}", "t": "s"}), ns + "v").text = str(index)
    template = PROJECT_ROOT / "tests" / "fixtures" / "b001" / "excel_valid.xlsx"
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(template) as old, ZipFile(output, "x") as new:
        for entry in old.infolist():
            payload = (ET.tostring(strings, encoding="utf-8", xml_declaration=True) if entry.filename == "xl/sharedStrings.xml"
                       else ET.tostring(sheet, encoding="utf-8", xml_declaration=True) if entry.filename == "xl/worksheets/sheet1.xml"
                       else old.read(entry.filename))
            new.writestr(entry, payload)
    result = validate(output)
    if not result["valid"] or len(result["rows"]) != len(columns[0]):
        raise ValueError("Reconstructed workbook failed B-002 validation")
    evidence = {"label": "RECONSTRUCTED_FIXTURE_NOT_OWNER_ORIGINAL", "row_count": len(result["rows"]),
                "workbook_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "source_sha256": {f"{code}.txt": hashlib.sha256((source / f"{code}.txt").read_bytes()).hexdigest() for code in ("en", "jp", "vn")}}
    (output.parent / (output.stem + ".provenance.json")).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    print(json.dumps(create(parser.parse_args().output)))
