from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VOCABULARY_PATH = PROJECT_ROOT / "data" / "vocabulary" / "en.txt"
QUERY_PATH = PROJECT_ROOT / "collect data script" / "key.txt"
IMAGE_DIR = PROJECT_ROOT / "data" / "image" / "en"
METADATA_DIR = IMAGE_DIR / "_metadata"

OPENVERSE_IMAGES_ENDPOINT = "https://api.openverse.org/v1/images/"
USER_AGENT = "MultimediaVocabularyCollector/1.0"

DEFAULT_LIMIT = 10
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_RETRIES = 2
DEFAULT_RETRY_DELAY_SECONDS = 2.0
DEFAULT_RATE_LIMIT_DELAY_SECONDS = 1.0
DEFAULT_PAGE_SIZE = 20

JPEG_SIGNATURES = (b"\xff\xd8\xff",)
SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.'()-]*$")


@dataclass
class ImageResult:
    ok: bool
    word: str
    status: str
    reason: str | None = None


@dataclass
class Summary:
    total: int = 0
    success: int = 0
    failed: list[tuple[str, str]] = field(default_factory=list)

    def add(self, result: ImageResult) -> None:
        self.total += 1
        if result.ok:
            self.success += 1
        else:
            self.failed.append((result.word, result.reason or "unknown error"))


class CollectionError(Exception):
    pass


def load_vocabulary(path: Path) -> list[str]:
    if not path.exists():
        raise CollectionError(f"Vocabulary file not found: {path}")

    words = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    words = [word for word in words if word]

    duplicates = sorted({word for word in words if words.count(word) > 1})
    if duplicates:
        duplicate_list = ", ".join(duplicates)
        raise CollectionError(f"Duplicate vocabulary found: {duplicate_list}")

    return words


def load_query_file(path: Path, expected_count: int) -> list[str]:
    if not path.exists():
        raise CollectionError(f"Query file not found: {path}")

    queries = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    queries = [query for query in queries if query]

    if len(queries) != expected_count:
        raise CollectionError(
            f"Query file count mismatch: expected {expected_count}, found {len(queries)}"
        )

    return queries


def sanitize_filename(word: str) -> str:
    if word in {".", ".."} or "/" in word or "\\" in word or ":" in word:
        raise CollectionError("unsafe vocabulary for filename")
    if not SAFE_FILENAME_RE.match(word):
        raise CollectionError("vocabulary contains unsupported filename characters")
    return word


def ensure_directories() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)


def is_valid_jpeg(path: Path) -> bool:
    if not path.exists() or not path.is_file() or path.stat().st_size == 0:
        return False
    with path.open("rb") as file:
        header = file.read(3)
    return any(header.startswith(signature) for signature in JPEG_SIGNATURES)


def request_with_retry(
    url: str,
    *,
    timeout: int,
    retries: int,
    retry_delay: float,
) -> tuple[bytes, dict[str, str], int]:
    last_error: Exception | None = None

    for attempt in range(retries + 1):
        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=timeout) as response:
                status = response.getcode()
                headers = {key.lower(): value for key, value in response.headers.items()}
                body = response.read()
                if 200 <= status < 300:
                    return body, headers, status
                last_error = CollectionError(f"HTTP {status}")
        except HTTPError as error:
            last_error = error
            if error.code in {400, 401, 403, 404}:
                break
        except (TimeoutError, URLError) as error:
            last_error = error

        if attempt < retries:
            time.sleep(retry_delay * (attempt + 1))

    raise CollectionError(str(last_error) if last_error else "request failed")


def http_get_json(url: str, *, timeout: int, retries: int, retry_delay: float) -> dict[str, Any]:
    body, headers, status = request_with_retry(
        url,
        timeout=timeout,
        retries=retries,
        retry_delay=retry_delay,
    )
    content_type = headers.get("content-type", "")
    if "application/json" not in content_type:
        raise CollectionError(f"expected JSON response, got {content_type or 'unknown'}")
    try:
        return json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as error:
        raise CollectionError(f"invalid JSON response after HTTP {status}: {error}") from error


def build_openverse_search_url(query_text: str) -> str:
    query = urlencode(
        {
            "q": query_text,
            "page_size": DEFAULT_PAGE_SIZE,
            "mature": "false",
            "filter_dead": "true",
            "extension": "jpg,jpeg",
        }
    )
    return f"{OPENVERSE_IMAGES_ENDPOINT}?{query}"


def search_image(query_text: str, *, timeout: int, retries: int, retry_delay: float) -> list[dict[str, Any]]:
    data = http_get_json(
        build_openverse_search_url(query_text),
        timeout=timeout,
        retries=retries,
        retry_delay=retry_delay,
    )
    results = data.get("results")
    if not isinstance(results, list):
        raise CollectionError("Openverse response missing results list")
    return results


def score_image_result(word: str, result: dict[str, Any]) -> int:
    needle = word.lower()
    title = str(result.get("title") or "").lower()
    tags = result.get("tags") or []
    tag_names = [
        str(tag.get("name") or "").lower()
        for tag in tags
        if isinstance(tag, dict)
    ]
    filetype = str(result.get("filetype") or "").lower()
    url = str(result.get("url") or "").lower()

    score = 0
    if title == needle:
        score += 60
    elif re.search(rf"\b{re.escape(needle)}\b", title):
        score += 35
    if needle in tag_names:
        score += 30
    if filetype in {"jpg", "jpeg"}:
        score += 20
    if url.endswith((".jpg", ".jpeg")):
        score += 10
    if result.get("foreign_landing_url"):
        score += 5
    return score


def choose_image_result(word: str, results: list[dict[str, Any]]) -> dict[str, Any] | None:
    usable = [result for result in results if isinstance(result, dict) and result.get("url")]
    if not usable:
        return None
    return max(usable, key=lambda result: score_image_result(word, result))


def download_jpeg(
    image_url: str,
    destination: Path,
    *,
    timeout: int,
    retries: int,
    retry_delay: float,
) -> None:
    body, headers, _status = request_with_retry(
        image_url,
        timeout=timeout,
        retries=retries,
        retry_delay=retry_delay,
    )
    content_type = headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type not in {"image/jpeg", "image/jpg"}:
        raise CollectionError(f"expected JPEG content-type, got {content_type or 'unknown'}")
    if not any(body.startswith(signature) for signature in JPEG_SIGNATURES):
        raise CollectionError("downloaded file does not have a JPEG signature")

    temporary_path = destination.with_suffix(".jpg.tmp")
    temporary_path.write_bytes(body)
    if not is_valid_jpeg(temporary_path):
        temporary_path.unlink(missing_ok=True)
        raise CollectionError("saved file failed JPEG validation")
    temporary_path.replace(destination)


def metadata_from_result(word: str, query_text: str, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "word": word,
        "search_query": query_text,
        "source": result.get("source"),
        "source_url": result.get("source_url"),
        "image_url": result.get("url"),
        "title": result.get("title"),
        "creator": result.get("creator"),
        "creator_url": result.get("creator_url"),
        "license": result.get("license"),
        "license_url": result.get("license_url"),
        "foreign_landing_url": result.get("foreign_landing_url"),
    }


def save_metadata(word: str, query_text: str, result: dict[str, Any]) -> None:
    metadata_path = METADATA_DIR / f"{sanitize_filename(word)}.json"
    metadata_path.write_text(
        json.dumps(metadata_from_result(word, query_text, result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def process_word(
    word: str,
    query_text: str,
    *,
    timeout: int,
    retries: int,
    retry_delay: float,
) -> ImageResult:
    try:
        filename = sanitize_filename(word)
        image_path = IMAGE_DIR / f"{filename}.jpg"
        metadata_path = METADATA_DIR / f"{filename}.json"

        if is_valid_jpeg(image_path) and metadata_path.exists():
            print(f"[IMAGE] {word} -> SUCCESS: cached")
            return ImageResult(ok=True, word=word, status="cached")

        if image_path.exists() and not is_valid_jpeg(image_path):
            raise CollectionError("existing image file is not a valid JPEG")

        results = search_image(query_text, timeout=timeout, retries=retries, retry_delay=retry_delay)
        chosen = choose_image_result(query_text, results)
        if not chosen:
            raise CollectionError("no usable Openverse image result")

        download_jpeg(
            str(chosen["url"]),
            image_path,
            timeout=timeout,
            retries=retries,
            retry_delay=retry_delay,
        )
        save_metadata(word, query_text, chosen)

        print(f"[IMAGE] {word} ({query_text}) -> SUCCESS")
        return ImageResult(ok=True, word=word, status="downloaded")
    except CollectionError as error:
        print(f"[IMAGE] {word} -> FAILED: {error}")
        return ImageResult(ok=False, word=word, status="failed", reason=str(error))


def print_summary(summary: Summary) -> None:
    failed_count = len(summary.failed)
    print()
    print(f"Total: {summary.total}")
    print(f"Success: {summary.success}")
    print(f"Failed: {failed_count}")
    if summary.failed:
        print()
        print("Failed words:")
        for word, reason in summary.failed:
            print(f"- {word}: {reason}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect English vocabulary images from Openverse.")
    parser.add_argument(
        "--vocabulary",
        type=Path,
        default=VOCABULARY_PATH,
        help="Path to canonical vocabulary file used for output filenames.",
    )
    parser.add_argument(
        "--query-file",
        type=Path,
        default=QUERY_PATH,
        help="Path to search-query file. Must have the same number of lines as vocabulary.",
    )
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Number of words to process.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="HTTP timeout in seconds.")
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES, help="Retry count per request.")
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=DEFAULT_RETRY_DELAY_SECONDS,
        help="Base delay between retries in seconds.",
    )
    parser.add_argument(
        "--rate-limit-delay",
        type=float,
        default=DEFAULT_RATE_LIMIT_DELAY_SECONDS,
        help="Delay between words in seconds.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit < 1:
        raise CollectionError("--limit must be at least 1")

    vocabulary_path = args.vocabulary
    if not vocabulary_path.is_absolute():
        vocabulary_path = PROJECT_ROOT / vocabulary_path

    query_path = args.query_file
    if query_path is not None and not query_path.is_absolute():
        query_path = PROJECT_ROOT / query_path

    ensure_directories()
    words = load_vocabulary(vocabulary_path)
    queries = load_query_file(query_path, len(words)) if query_path else words
    words_to_process = words[: args.limit]
    queries_to_process = queries[: args.limit]

    summary = Summary()
    for index, (word, query_text) in enumerate(zip(words_to_process, queries_to_process)):
        result = process_word(
            word,
            query_text,
            timeout=args.timeout,
            retries=args.retries,
            retry_delay=args.retry_delay,
        )
        summary.add(result)
        if index < len(words_to_process) - 1:
            time.sleep(args.rate_limit_delay)

    print_summary(summary)
    return 0 if not summary.failed else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CollectionError as error:
        print(f"ERROR: {error}")
        raise SystemExit(1)
