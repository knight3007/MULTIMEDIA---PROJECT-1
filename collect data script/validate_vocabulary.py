"""Read-only structural validation of parallel EN/JP/VN vocabulary files."""

import argparse
from itertools import zip_longest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ("en", "jp", "vn")


def validate_sources(paths: dict[str, Path], expected_count: int = 100):
    """Return physical-line triples and deterministic structural issue messages."""
    columns = {}
    issues = []
    for language in LANGUAGES:
        path = paths[language]
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            issues.append(f"{language}: invalid UTF-8: {path}")
            lines = []
        except OSError as error:
            issues.append(f"{language}: cannot read {path}: {error.strerror or error}")
            lines = []
        columns[language] = lines
        if len(lines) != expected_count:
            issues.append(f"{language}: expected {expected_count} lines, found {len(lines)}")
        seen = {}
        for index, raw in enumerate(lines, start=1):
            value = raw.strip()
            if not value:
                issues.append(f"{language}: line {index}: empty")
                continue
            if value != raw:
                issues.append(f"{language}: line {index}: surrounding whitespace")
            key = value.casefold()
            if key in seen:
                issues.append(f"{language}: line {index}: duplicate of line {seen[key]}")
            else:
                seen[key] = index
    rows = list(zip_longest(*(columns[language] for language in LANGUAGES), fillvalue=""))
    return rows, issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for language in LANGUAGES:
        parser.add_argument(f"--{language}", type=Path,
                            default=PROJECT_ROOT / "data" / "vocabulary" / f"{language}.txt")
    args = parser.parse_args()
    rows, issues = validate_sources({language: getattr(args, language) for language in LANGUAGES})
    print(f"Physical rows: {len(rows)}")
    for issue in issues:
        print(issue)
    print(f"Structural issues: {len(issues)}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
