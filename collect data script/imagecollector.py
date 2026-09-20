from __future__ import annotations

import argparse
import json
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from collector_common import (
    PROJECT_ROOT, CollectionError, add_common_arguments, load_vocabulary, load_vocabulary_pairs,
    resolve_project_path, run_cli, validate_common_arguments,
)

VOCABULARY_PATH = PROJECT_ROOT / "data" / "vocabulary" / "en.txt"
QUERY_PATH = PROJECT_ROOT / "collect data script" / "key.txt"
IMAGE_DIR = PROJECT_ROOT / "data" / "image" / "en"
METADATA_DIR = IMAGE_DIR / "_metadata"
CANDIDATE_CACHE_DIR = IMAGE_DIR / "_candidates"
OPENVERSE_IMAGES_ENDPOINT = "https://api.openverse.org/v1/images/"
USER_AGENT = "MultimediaVocabularyCollector/1.0"
DEFAULT_PAGE_SIZE = 7
DEFAULT_SIGLIP_MODEL = "google/siglip2-so400m-patch16-384"
JPEG_SIGNATURES = (b"\xff\xd8\xff",)
SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.'()-]*$")


@dataclass
class ImageResult:
    ok: bool
    word: str
    query_text: str
    status: str
    reason: str | None = None
    selected_image: str | None = None
    siglip_score: float | None = None
    candidate_count: int = 0


@dataclass
class Summary:
    total: int = 0
    success: int = 0
    failed: list[tuple[str, str]] = field(default_factory=list)
    results: list[ImageResult] = field(default_factory=list)

    def add(self, result: ImageResult) -> None:
        self.total += 1
        self.results.append(result)
        if result.ok:
            self.success += 1
        else:
            self.failed.append((result.word, result.reason or "unknown error"))


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
    CANDIDATE_CACHE_DIR.mkdir(parents=True, exist_ok=True)


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


def build_openverse_search_url(query_text: str, page_size: int) -> str:
    query = urlencode(
        {
            "q": query_text,
            "page_size": page_size,
            "mature": "false",
            "filter_dead": "true",
            "extension": "jpg,jpeg",
        }
    )
    return f"{OPENVERSE_IMAGES_ENDPOINT}?{query}"


def search_image(
    query_text: str,
    *,
    page_size: int,
    timeout: int,
    retries: int,
    retry_delay: float,
) -> list[dict[str, Any]]:
    data = http_get_json(
        build_openverse_search_url(query_text, page_size),
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


def usable_image_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [result for result in results if isinstance(result, dict) and result.get("url")]


def candidate_cache_path(word: str, index: int) -> Path:
    return CANDIDATE_CACHE_DIR / sanitize_filename(word) / f"{index:02d}.jpg"


def candidate_cache_dir(word: str) -> Path:
    return CANDIDATE_CACHE_DIR / sanitize_filename(word)


def cleanup_candidate_cache(word: str) -> None:
    shutil.rmtree(candidate_cache_dir(word), ignore_errors=True)


def download_candidate_images(
    word: str,
    results: list[dict[str, Any]],
    *,
    timeout: int,
    retries: int,
    retry_delay: float,
) -> list[tuple[dict[str, Any], Path]]:
    candidates: list[tuple[dict[str, Any], Path]] = []
    candidate_dir = candidate_cache_dir(word)
    candidate_dir.mkdir(parents=True, exist_ok=True)

    for index, result in enumerate(usable_image_results(results), start=1):
        image_url = str(result["url"])
        cache_path = candidate_cache_path(word, index)
        try:
            if is_valid_jpeg(cache_path):
                candidates.append((result, cache_path))
                continue
            download_jpeg(
                image_url,
                cache_path,
                timeout=timeout,
                retries=retries,
                retry_delay=retry_delay,
            )
            candidates.append((result, cache_path))
        except (CollectionError, OSError) as error:
            cache_path.unlink(missing_ok=True)
            print(f"  SKIP candidate {index}: {image_url}")
            print(f"    reason: {error}")

    return candidates


def choose_image_result_with_siglip(
    word: str,
    query_text: str,
    results: list[dict[str, Any]],
    scorer: Any,
    *,
    timeout: int,
    retries: int,
    retry_delay: float,
) -> tuple[dict[str, Any] | None, float | None, int]:
    from image_scorer import ImageScoringError

    old_selected = choose_image_result(query_text, results)
    candidates = download_candidate_images(
        word,
        results,
        timeout=timeout,
        retries=retries,
        retry_delay=retry_delay,
    )
    print("=" * 40)
    print(f"KEY: {word}")
    print(f"QUERY: {query_text}")
    print(f"CANDIDATES: {len(candidates)}")
    if old_selected:
        print(f"OLD SELECTED: {old_selected.get('url')}")

    if not candidates:
        return None, None, 0

    try:
        score_results = scorer.score_batch(query_text, [path for _result, path in candidates])
    except ImageScoringError as error:
        raise CollectionError(str(error)) from error

    scored_candidates = sorted(
        zip(candidates, score_results),
        key=lambda item: item[1].score,
        reverse=True,
    )

    for rank, ((result, _path), score_result) in enumerate(scored_candidates, start=1):
        print(f"{rank}. {result.get('url')}")
        print(f"   score={score_result.score:.4f}")

    (best_result, best_path), best_score = scored_candidates[0]
    print("SELECTED:")
    print(best_result.get("url"))
    print(f"score={best_score.score:.4f}")
    print("=" * 40)
    best_result["_siglip_candidate_path"] = str(best_path)
    return best_result, best_score.score, len(candidates)


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


def metadata_from_result(
    word: str,
    query_text: str,
    result: dict[str, Any],
    image_selection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = {
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
    if image_selection:
        metadata["image_selection"] = image_selection
    return metadata


def save_metadata(
    word: str,
    query_text: str,
    result: dict[str, Any],
    image_selection: dict[str, Any] | None = None,
) -> None:
    metadata_path = METADATA_DIR / f"{sanitize_filename(word)}.json"
    metadata_path.write_text(
        json.dumps(
            metadata_from_result(word, query_text, result, image_selection),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def process_word(
    word: str,
    query_text: str,
    *,
    timeout: int,
    retries: int,
    retry_delay: float,
    page_size: int,
    scorer: Any | None = None,
    siglip_model: str = DEFAULT_SIGLIP_MODEL,
) -> ImageResult:
    try:
        filename = sanitize_filename(word)
        image_path = IMAGE_DIR / f"{filename}.jpg"
        metadata_path = METADATA_DIR / f"{filename}.json"

        if is_valid_jpeg(image_path) and metadata_path.exists():
            print(f"[IMAGE] {word} -> SUCCESS: cached")
            return ImageResult(ok=True, word=word, query_text=query_text, status="cached")

        if image_path.exists() and not is_valid_jpeg(image_path):
            raise CollectionError("existing image file is not a valid JPEG")

        results = search_image(
            query_text,
            page_size=page_size,
            timeout=timeout,
            retries=retries,
            retry_delay=retry_delay,
        )
        siglip_score = None
        candidate_count = 0
        if scorer:
            chosen, siglip_score, candidate_count = choose_image_result_with_siglip(
                word,
                query_text,
                results,
                scorer,
                timeout=timeout,
                retries=retries,
                retry_delay=retry_delay,
            )
        else:
            chosen = choose_image_result(query_text, results)
        if not chosen:
            raise CollectionError("no usable Openverse image result")

        candidate_path = chosen.get("_siglip_candidate_path")
        if candidate_path:
            shutil.copyfile(candidate_path, image_path)
        else:
            download_jpeg(
                str(chosen["url"]),
                image_path,
                timeout=timeout,
                retries=retries,
                retry_delay=retry_delay,
            )
        image_selection = None
        if siglip_score is not None:
            image_selection = {
                "method": "siglip2",
                "model": siglip_model,
                "score": siglip_score,
            }
        save_metadata(word, query_text, chosen, image_selection)
        if candidate_path:
            cleanup_candidate_cache(word)

        print(f"[IMAGE] {word} ({query_text}) -> SUCCESS")
        return ImageResult(
            ok=True,
            word=word,
            query_text=query_text,
            status="downloaded",
            selected_image=str(chosen.get("url")),
            siglip_score=siglip_score,
            candidate_count=candidate_count,
        )
    except (CollectionError, OSError) as error:
        print(f"[IMAGE] {word} -> FAILED: {error}")
        return ImageResult(ok=False, word=word, query_text=query_text, status="failed", reason=str(error))


def print_summary(summary: Summary) -> None:
    failed_count = len(summary.failed)
    print()
    print(f"Total: {summary.total}")
    print(f"Success: {summary.success}")
    print(f"Failed: {failed_count}")
    scored_results = [result for result in summary.results if result.siglip_score is not None]
    if scored_results:
        scores = [result.siglip_score for result in scored_results if result.siglip_score is not None]
        print()
        print("SigLIP selections:")
        for index, result in enumerate(summary.results, start=1):
            if result.siglip_score is None:
                continue
            print(
                f"{index}. {result.word} | query={result.query_text} | "
                f"candidates={result.candidate_count} | "
                f"score={result.siglip_score:.4f} | image={result.selected_image}"
            )
        print()
        print(f"Average score: {sum(scores) / len(scores):.4f}")
        print(f"Min score: {min(scores):.4f}")
        print(f"Max score: {max(scores):.4f}")
    if summary.failed:
        print()
        print("Failed words:")
        for word, reason in summary.failed:
            print(f"- {word}: {reason}")


class LazySiglipScorer:
    """Load the model once, only when uncached images need ranking."""

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.scorer = None

    def score_batch(self, text: str, paths: list[Path]):
        from image_scorer import ImageScoringError, SiglipImageScorer

        if self.scorer is None:
            args = self.args
            print(f"[SIGLIP] loading model={args.siglip_model} device={args.siglip_device} dtype={args.siglip_dtype}")
            try:
                self.scorer = SiglipImageScorer(args.siglip_model, device=args.siglip_device, dtype=args.siglip_dtype)
            except (OSError, ValueError, RuntimeError) as error:
                raise ImageScoringError(str(error)) from error
            print(f"[SIGLIP] ready resolved_model={self.scorer.model_path} device={self.scorer.device} dtype={self.scorer.dtype}")
        return self.scorer.score_batch(text, paths)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
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
        help="Legacy search-query file, ignored with --qwen-queries. Must match vocabulary count.",
    )
    parser.add_argument("--qwen-queries", action="store_true",
                        help="Prepare Qwen queries from aligned English/Vietnamese vocabulary before image collection.")
    parser.add_argument("--vn-vocabulary", type=Path,
                        default=PROJECT_ROOT / "data" / "vocabulary" / "vn.txt",
                        help="Vietnamese meanings aligned by line with --vocabulary (Qwen mode only).")
    # Resolve generator defaults inside the Qwen branch, keeping legacy imports light.
    parser.add_argument("--qwen-model", help="Qwen model name or path; defaults to query_generator.DEFAULT_QWEN_MODEL.")
    parser.add_argument("--qwen-batch-size", type=int,
                        help="Generation batch size; defaults to query_generator.DEFAULT_BATCH_SIZE.")
    parser.add_argument("--qwen-cache", type=Path,
                        help="Query cache JSON; defaults to query_generator.DEFAULT_QUERY_CACHE.")
    parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help="Number of Openverse image candidates to request per word.",
    )
    parser.add_argument(
        "--no-siglip",
        action="store_true",
        help="Use the old Openverse metadata heuristic instead of SigLIP ranking.",
    )
    parser.add_argument(
        "--siglip-model",
        default=DEFAULT_SIGLIP_MODEL,
        help="SigLIP model name or local snapshot path.",
    )
    parser.add_argument(
        "--siglip-device",
        default="auto",
        choices=("auto", "cpu", "cuda"),
        help="Device for SigLIP inference.",
    )
    parser.add_argument(
        "--siglip-dtype",
        default="auto",
        choices=("auto", "float16", "bfloat16", "float32"),
        help="Torch dtype for SigLIP model weights.",
    )
    add_common_arguments(parser)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    validate_common_arguments(args)
    if args.page_size < 1:
        raise CollectionError("--page-size must be at least 1")

    vocabulary_path = resolve_project_path(args.vocabulary)
    if args.qwen_queries:
        from query_generator import (
            DEFAULT_BATCH_SIZE, DEFAULT_QUERY_CACHE, DEFAULT_QWEN_MODEL, prepare_queries,
        )

        batch_size = DEFAULT_BATCH_SIZE if args.qwen_batch_size is None else args.qwen_batch_size
        if batch_size < 1:
            raise CollectionError("--qwen-batch-size must be at least 1")
        pairs = load_vocabulary_pairs(vocabulary_path, resolve_project_path(args.vn_vocabulary))
        words_to_process = [word for word, _meaning in pairs[: args.limit]]
        # Phase A completes (including Qwen release) before any image/scorer work.
        queries_to_process = prepare_queries(
            pairs, limit=args.limit,
            model_name=args.qwen_model if args.qwen_model is not None else DEFAULT_QWEN_MODEL,
            batch_size=batch_size,
            cache_path=resolve_project_path(args.qwen_cache if args.qwen_cache is not None else DEFAULT_QUERY_CACHE),
        )
        if len(queries_to_process) != len(words_to_process):
            raise CollectionError(
                f"Qwen query count mismatch: expected {len(words_to_process)}, found {len(queries_to_process)}"
            )
        ensure_directories()
    else:
        query_path = resolve_project_path(args.query_file)
        ensure_directories()
        words = load_vocabulary(vocabulary_path)
        queries = load_query_file(query_path, len(words)) if query_path else words
        words_to_process = words[: args.limit]
        queries_to_process = queries[: args.limit]

    # Phase B: existing search, candidate download, and SigLIP selection.
    scorer = None
    if not args.no_siglip:
        scorer = LazySiglipScorer(args)

    summary = Summary()
    for index, (word, query_text) in enumerate(zip(words_to_process, queries_to_process)):
        result = process_word(
            word,
            query_text,
            timeout=args.timeout,
            retries=args.retries,
            retry_delay=args.retry_delay,
            page_size=args.page_size,
            scorer=scorer,
            siglip_model=args.siglip_model,
        )
        summary.add(result)
        if result.status != "cached" and index < len(words_to_process) - 1:
            time.sleep(args.rate_limit_delay)

    print_summary(summary)
    return 0 if not summary.failed else 1


if __name__ == "__main__":
    run_cli(main)
