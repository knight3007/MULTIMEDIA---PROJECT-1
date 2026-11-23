"""Validate B-001 Vocabulary XLSX files and persist isolated import records."""

import argparse
import hashlib
import json
import re
import sys
import unicodedata
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile


MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
FIELDS = ("english", "japanese", "vietnamese", "target_sense")
REQUIRED = FIELDS[:3]
WHITE_SPACE = "\t\n\v\f\r \u0085\u00a0\u1680" + "".join(chr(n) for n in range(0x2000, 0x200b)) + "\u2028\u2029\u202f\u205f\u3000"
CELL_REF = re.compile(r"^([A-Z]+)([1-9][0-9]*)$")


def tag(name):
    return f"{{{MAIN}}}{name}"


def diagnostic(code, severity="error", row=None, column=None, message="", related_row=None, sheet="Vocabulary"):
    return dict(code=code, severity=severity, sheet=sheet, row=row, column=column,
                message=message, related_row=related_row)


def parse_xml(data):
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ValueError("DTD/entity content is unsupported")
    return ET.fromstring(data)


def column_number(letters):
    number = 0
    for letter in letters:
        number = number * 26 + ord(letter) - 64
    return number


def read_workbook(path):
    """Return header cells, data cells, merged ranges; fail closed on unsupported OOXML."""
    if path.suffix.lower() != ".xlsx":
        raise ValueError("Only .xlsx workbooks are supported")
    with ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or any(n.startswith("/") or ".." in PurePosixPath(n).parts for n in names):
            raise ValueError("Unsafe or repeated ZIP member")
        if any(n.startswith(("xl/externalLinks/", "xl/embeddings/", "xl/activeX/", "xl/drawings/"))
               or "vbaProject" in n or n.startswith("xl/media/") for n in names):
            raise ValueError("External links, embedded objects, drawings and macros are unsupported")
        content = parse_xml(archive.read("[Content_Types].xml"))
        types = [x.get("ContentType", "") for x in content]
        if any("macroEnabled" in t or "externalLink" in t or "oleObject" in t or "vbaProject" in t for t in types):
            raise ValueError("Macro or external workbook content is unsupported")
        workbook = parse_xml(archive.read("xl/workbook.xml"))
        sheets = workbook.findall(f"{tag('sheets')}/{tag('sheet')}")
        if len(sheets) != 1 or sheets[0].get("name") != "Vocabulary" or sheets[0].get("state", "visible") != "visible":
            raise LookupError("Workbook must have exactly one visible worksheet named Vocabulary")
        relationships = parse_xml(archive.read("xl/_rels/workbook.xml.rels"))
        by_id = {x.get("Id"): x for x in relationships}
        if any(x.get("TargetMode") == "External" or x.get("Type", "").endswith("/externalLink") for x in relationships):
            raise ValueError("External workbook relationships are unsupported")
        sheet_rel = by_id[sheets[0].get(f"{{{REL}}}id")]
        if not sheet_rel.get("Type", "").endswith("/worksheet"):
            raise ValueError("Invalid worksheet relationship")
        target = sheet_rel.get("Target", "")
        sheet_name = str(PurePosixPath(target.lstrip("/") if target.startswith("/") else "xl/" + target))
        if not sheet_name.startswith("xl/worksheets/") or ".." in PurePosixPath(sheet_name).parts:
            raise ValueError("Invalid worksheet path")
        sheet = parse_xml(archive.read(sheet_name))
        if any(n.startswith("xl/worksheets/_rels/") and n.endswith(".rels") for n in names):
            rel_name = "xl/worksheets/_rels/" + PurePosixPath(sheet_name).name + ".rels"
            if rel_name in names:
                rels = parse_xml(archive.read(rel_name))
                if any(x.get("TargetMode") == "External" for x in rels):
                    raise ValueError("External worksheet relationships are unsupported")
        shared = []
        if "xl/sharedStrings.xml" in names:
            strings = parse_xml(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(n.text or "" for n in si.iter(tag("t"))) for si in strings.findall(tag("si"))]
        cells = {}
        for row in sheet.findall(f"{tag('sheetData')}/{tag('row')}"):
            for cell in row.findall(tag("c")):
                reference = cell.get("r", "")
                match = CELL_REF.fullmatch(reference)
                if not match or reference in cells or int(match[2]) != int(row.get("r", "0")):
                    raise ValueError("Invalid or repeated cell reference")
                kind = cell.get("t", "n")
                if cell.find(tag("f")) is not None:
                    value = ("formula", None)
                elif kind == "e":
                    value = ("error", None)
                elif kind == "s":
                    index = int(cell.findtext(tag("v")))
                    value = ("text", shared[index])
                elif kind == "inlineStr":
                    value = ("text", "".join(n.text or "" for n in cell.iter(tag("t"))))
                elif kind == "str":
                    value = ("text", cell.findtext(tag("v")) or "")
                elif kind in ("n", "b", "d"):
                    raw = cell.findtext(tag("v"))
                    value = ("blank", None) if raw is None else ("unsupported", raw)
                else:
                    value = ("unsupported", None)
                cells[(int(match[2]), column_number(match[1]))] = value
        merges = [x.get("ref", "") for x in sheet.findall(f"{tag('mergeCells')}/{tag('mergeCell')}")]
        return cells, merges


def normalize(value):
    return unicodedata.normalize("NFC", value.strip(WHITE_SPACE))


def valid_text(value):
    return not any(ord(c) < 32 or 127 <= ord(c) <= 159 or 0xD800 <= ord(c) <= 0xDFFF for c in value)


def payload_hash(rows):
    values = [[row[field] for field in FIELDS] for row in rows]
    compact = json.dumps(values, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(compact.encode("utf-8")).hexdigest()


def validate(path):
    """Return a deterministic preview. Errors make acceptance impossible."""
    path = Path(path)
    result = {"contract_version": 1, "valid": False, "rows": [], "diagnostics": [], "normalized_payload_sha256": None}
    try:
        cells, merges = read_workbook(path)
    except FileNotFoundError:
        result["diagnostics"].append(diagnostic("INVALID_WORKBOOK", message="Workbook file does not exist.", sheet=None))
        return result
    except LookupError:
        result["diagnostics"].append(diagnostic("INVALID_SHEET", message="Exactly one visible Vocabulary worksheet is required.", sheet=None))
        return result
    except (BadZipFile, KeyError, IndexError, ET.ParseError, ValueError, TypeError, OSError, OverflowError):
        result["diagnostics"].append(diagnostic("INVALID_WORKBOOK", message="Workbook is invalid or contains unsupported structure.", sheet=None))
        return result
    issues = result["diagnostics"]
    header = {col: value for (row, col), value in cells.items() if row == 1 and value[0] != "blank"}
    columns = {}
    for col, (kind, raw) in sorted(header.items()):
        if kind != "text" or normalize(raw) not in FIELDS or raw != normalize(raw):
            issues.append(diagnostic("INVALID_HEADER", row=1, message="Header must be a supported lowercase field name."))
        elif raw in columns:
            issues.append(diagnostic("INVALID_HEADER", row=1, column=raw, message="Repeated header."))
        else:
            columns[raw] = col
    for name in REQUIRED:
        if name not in columns:
            issues.append(diagnostic("INVALID_HEADER", row=1, column=name, message=f"Required {name} header is missing."))
    if any(i["severity"] == "error" for i in issues):
        return result
    for (row, col), (kind, raw) in cells.items():
        if row > 1 and col not in columns.values() and kind != "blank" and (kind != "text" or normalize(raw)):
            issues.append(diagnostic("INVALID_HEADER", row=1, message="Populated column has no header."))
            break
    table_max = max((r for r, _ in cells if r > 1), default=1)
    for merged in merges:
        ends = merged.split(":")
        if len(ends) != 2 or not all(CELL_REF.fullmatch(x) for x in ends):
            issues.append(diagnostic("INVALID_WORKBOOK", message="Invalid merged-cell range."))
            continue
        a, b = (CELL_REF.fullmatch(x) for x in ends)
        if int(a[2]) <= table_max and int(b[2]) >= 1 and column_number(a[1]) <= max(columns.values()):
            issues.append(diagnostic("INVALID_WORKBOOK", message="Merged cells in the vocabulary table are unsupported."))
    seen = {}
    for row in range(2, table_max + 1):
        extracted = {}
        present = False
        row_errors = False
        for name in FIELDS:
            if name not in columns:
                extracted[name] = None
                continue
            kind, raw = cells.get((row, columns[name]), ("blank", None))
            if kind not in ("text", "blank"):
                issues.append(diagnostic("UNSUPPORTED_CELL", row=row, column=name, message="Text cell required; formulas, errors, numbers, booleans and dates are unsupported."))
                row_errors = True
                extracted[name] = None
                present = True
                continue
            if kind == "text" and not valid_text(raw):
                issues.append(diagnostic("INVALID_TEXT", row=row, column=name, message="Text contains a control character or invalid Unicode."))
                row_errors = True
            value = normalize(raw) if kind == "text" else ""
            if value:
                present = True
                if value != raw:
                    issues.append(diagnostic("NORMALIZED_TEXT", "warning", row, name, "Text was trimmed or normalized to NFC."))
            extracted[name] = value or None
        if not present:
            issues.append(diagnostic("EMPTY_ROW", "warning", row, message="Empty row skipped."))
            continue
        for name in REQUIRED:
            if not extracted[name] and cells.get((row, columns[name]), ("blank",))[0] in ("text", "blank"):
                issues.append(diagnostic("REQUIRED_VALUE", row=row, column=name, message=f"{name.capitalize()} text is required."))
                row_errors = True
        if row_errors:
            continue
        key = (extracted["english"].casefold(), extracted["japanese"], extracted["vietnamese"].casefold(),
               extracted["target_sense"].casefold() if extracted["target_sense"] else None)
        if key in seen:
            issues.append(diagnostic("DUPLICATE_ROW", row=row, message="Duplicate normalized vocabulary record.", related_row=seen[key]))
        else:
            seen[key] = row
            result["rows"].append({"source_row": row, **extracted})
    if not result["rows"] and not any(x["severity"] == "error" for x in issues):
        issues.append(diagnostic("NO_DATA", message="Workbook has no vocabulary data."))
    issues.sort(key=lambda x: (x["row"] is not None, x["row"] or 0, FIELDS.index(x["column"]) if x["column"] in FIELDS else -1, x["code"]))
    result["valid"] = not any(x["severity"] == "error" for x in issues)
    result["normalized_payload_sha256"] = payload_hash(result["rows"]) if result["valid"] else None
    return result


def accept(path, output=None, resume=None, import_id=None):
    """Accept a validated preview into a private import record; never overwrite."""
    preview = validate(path)
    if not preview["valid"]:
        raise ValueError("Workbook validation failed; inspect preview diagnostics.")
    if resume is not None:
        record = json.loads(Path(resume).read_text(encoding="utf-8"))
        if (not import_id or record.get("import_id") != import_id or record.get("contract_version") != 1
                or record.get("normalized_payload_sha256") != preview["normalized_payload_sha256"]):
            raise ValueError("Import conflict: normalized payload differs from accepted import.")
        return record
    if import_id is not None or output is None:
        raise ValueError("A new import needs an output path; import_id applies only to resume.")
    used = set()
    def new_id(prefix):
        while True:
            value = prefix + str(uuid.uuid4())
            if value not in used:
                used.add(value)
                return value
    record = {"contract_version": 1, "import_id": new_id("imp-"), "pack_id": new_id("pack-"),
              "workbook_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
              "normalized_payload_sha256": preview["normalized_payload_sha256"],
              "rows": [{"item_id": new_id("item-"), **row} for row in preview["rows"]],
              "warnings": [x for x in preview["diagnostics"] if x["severity"] == "warning"]}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return record


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--output", type=Path, help="Accept valid workbook and create private import JSON (exclusive)")
    parser.add_argument("--resume", type=Path, help="Verify payload against an existing private import JSON")
    parser.add_argument("--import-id", help="Accepted import ID required with --resume")
    args = parser.parse_args()
    if args.output and args.resume:
        parser.error("--output and --resume are separate operations")
    if bool(args.resume) != bool(args.import_id):
        parser.error("--resume and --import-id must be supplied together")
    preview = validate(args.workbook)
    if (args.output or args.resume) and preview["valid"]:
        try:
            record = accept(args.workbook, args.output, args.resume, args.import_id)
        except (ValueError, OSError, json.JSONDecodeError) as error:
            parser.exit(2, str(error) + "\n")
        print(json.dumps({"import_id": record["import_id"], "pack_id": record["pack_id"],
                          "item_count": len(record["rows"]), "normalized_payload_sha256": record["normalized_payload_sha256"]}, ensure_ascii=False))
    else:
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        if not preview["valid"]:
            parser.exit(1)


if __name__ == "__main__":
    main()
