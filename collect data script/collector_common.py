from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LIMIT = 10
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_RETRIES = 2
DEFAULT_RETRY_DELAY_SECONDS = 2.0
DEFAULT_RATE_LIMIT_DELAY_SECONDS = 1.0


class CollectionError(Exception):
    pass


def load_vocabulary(path: Path) -> list[str]:
    if not path.exists():
        raise CollectionError(f"Vocabulary file not found: {path}")

    words = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    words = [word for word in words if word]

    duplicates = sorted(word for word, count in Counter(words).items() if count > 1)
    if duplicates:
        duplicate_list = ", ".join(duplicates)
        raise CollectionError(f"Duplicate vocabulary found: {duplicate_list}")

    return words


def configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def load_vocabulary_pairs(english_path: Path, vietnamese_path: Path) -> list[tuple[str, str]]:
    """Preserve physical line alignment; reject blank records rather than shifting them."""
    lists = []
    for label, path in (("English", english_path), ("Vietnamese", vietnamese_path)):
        try:
            lines = [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines()]
        except (OSError, UnicodeError) as error:
            raise CollectionError(f"Cannot read {label} vocabulary {path}: {error}") from error
        if not lines:
            raise CollectionError(f"{label} vocabulary is empty: {path}")
        for index, line in enumerate(lines, start=1):
            if not line:
                raise CollectionError(f"Blank {label} vocabulary at line {index}: {path}")
        lists.append(lines)
    words, meanings = lists
    if len(words) != len(meanings):
        raise CollectionError(
            f"EN/VN line count mismatch: English={len(words)}, Vietnamese={len(meanings)}"
        )
    duplicates = sorted(word for word, count in Counter(words).items() if count > 1)
    if duplicates:
        raise CollectionError(f"Duplicate vocabulary found: {', '.join(duplicates)}")
    return list(zip(words, meanings))


def resolve_project_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Number of words to process.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="Timeout per operation in seconds.")
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES, help="Retry count per operation.")
    parser.add_argument("--retry-delay", type=float, default=DEFAULT_RETRY_DELAY_SECONDS, help="Base delay between retries in seconds.")
    parser.add_argument("--rate-limit-delay", type=float, default=DEFAULT_RATE_LIMIT_DELAY_SECONDS, help="Delay between uncached words in seconds.")


def validate_common_arguments(args: argparse.Namespace) -> None:
    for name in ("limit", "timeout"):
        if getattr(args, name) < 1:
            raise CollectionError(f"--{name} must be at least 1")
    for name in ("retries", "retry_delay", "rate_limit_delay"):
        value = getattr(args, name)
        if not 0 <= value < float("inf"):
            raise CollectionError(f"--{name.replace('_', '-')} must be finite and nonnegative")


def run_cli(main) -> None:
    configure_console()
    try:
        raise SystemExit(main())
    except (CollectionError, OSError) as error:
        print(f"ERROR: {error}")
        raise SystemExit(1)
