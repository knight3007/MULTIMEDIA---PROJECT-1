from __future__ import annotations

import argparse
import ipaddress
import io
import json
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from PIL import Image, ImageOps, UnidentifiedImageError

from collector_common import (
    PROJECT_ROOT, CollectionError, add_common_arguments, load_vocabulary,
    resolve_project_path, run_cli, validate_common_arguments,
)

VOCABULARY_PATH = PROJECT_ROOT / "data" / "vocabulary" / "en.txt"
IMAGE_DIR = PROJECT_ROOT / "data" / "image" / "en"
METADATA_DIR = IMAGE_DIR / "_metadata"
CANDIDATE_CACHE_DIR = IMAGE_DIR / "_candidates"
IMAGE_PROVIDER = "duckduckgo"
DDG_REGION = "wt-wt"
DDG_SAFESEARCH = "moderate"
USER_AGENT = "MultimediaVocabularyCollector/1.0"
DEFAULT_PAGE_SIZE = 7
DEFAULT_SIGLIP_MODEL = "google/siglip2-so400m-patch16-384"
MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
MAX_IMAGE_SIZE = (1024, 1024)
JPEG_QUALITY = 90
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
    search_result_count: int = 0
    valid_candidate_count: int = 0
    search_seconds: float = 0.0
    download_seconds: float = 0.0
    scoring_seconds: float = 0.0
    total_seconds: float = 0.0


@dataclass(frozen=True)
class ImageSearchBatch:
    candidates: list[dict[str, Any]]
    raw_count: int
    duration_seconds: float


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


def normalize_remote_url(url: str) -> str:
    if not is_supported_remote_url(url):
        raise CollectionError("unsupported or unsafe image URL")
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname.encode("idna").decode("ascii")
        port = parsed.port
        if ":" in hostname:
            hostname = f"[{hostname}]"
        netloc = hostname if port is None else f"{hostname}:{port}"
        return urlunsplit((
            parsed.scheme.lower(),
            netloc,
            quote(parsed.path, safe="/%:@!$&'()*+,;=-._~"),
            quote(parsed.query, safe="=&?/:;+,%@-._~"),
            "",
        ))
    except (UnicodeError, ValueError) as error:
        raise CollectionError(f"invalid image URL: {error}") from error


def request_with_retry(
    url: str,
    *,
    timeout: int,
    retries: int,
    retry_delay: float,
) -> tuple[bytes, dict[str, str], int]:
    url = normalize_remote_url(url)
    last_error: Exception | None = None

    for attempt in range(retries + 1):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=timeout) as response:
                status = response.getcode()
                headers = {key.lower(): value for key, value in response.headers.items()}
                try:
                    content_length = int(headers.get("content-length", "0"))
                except ValueError:
                    content_length = 0
                if content_length > MAX_IMAGE_BYTES:
                    raise CollectionError(f"image payload exceeds {MAX_IMAGE_BYTES} bytes")
                body = response.read(MAX_IMAGE_BYTES + 1)
                if len(body) > MAX_IMAGE_BYTES:
                    raise CollectionError(f"image payload exceeds {MAX_IMAGE_BYTES} bytes")
                if 200 <= status < 300:
                    return body, headers, status
                last_error = CollectionError(f"HTTP {status}")
        except HTTPError as error:
            last_error = error
            if error.code in {400, 401, 403, 404}:
                break
        except (TimeoutError, URLError) as error:
            last_error = error
        except (UnicodeError, ValueError) as error:
            last_error = error
            break

        if attempt < retries:
            time.sleep(retry_delay * (attempt + 1))

    raise CollectionError(str(last_error) if last_error else "request failed")


def is_supported_remote_url(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    hostname = parsed.hostname
    if parsed.scheme not in {"http", "https"} or not hostname or parsed.username or parsed.password:
        return False
    if hostname.lower() == "localhost" or hostname.lower().endswith(".localhost"):
        return False
    try:
        return ipaddress.ip_address(hostname).is_global
    except ValueError:
        return True


def normalize_ddg_results(raw_results: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_results, list):
        return []
    normalized = []
    seen_images: set[str] = set()
    seen_pages: set[str] = set()
    for raw in raw_results:
        if not isinstance(raw, dict) or not is_supported_remote_url(raw.get("image")):
            continue
        image_url = raw["image"]
        source_page_url = raw.get("url") if is_supported_remote_url(raw.get("url")) else None
        if image_url in seen_images or source_page_url and source_page_url in seen_pages:
            continue
        seen_images.add(image_url)
        if source_page_url:
            seen_pages.add(source_page_url)
        normalized.append({
            "provider": IMAGE_PROVIDER,
            "title": raw.get("title") if isinstance(raw.get("title"), str) else None,
            "image_url": image_url,
            "thumbnail_url": raw.get("thumbnail") if is_supported_remote_url(raw.get("thumbnail")) else None,
            "source_page_url": source_page_url,
            "width": raw.get("width") if isinstance(raw.get("width"), int) else None,
            "height": raw.get("height") if isinstance(raw.get("height"), int) else None,
            "source": raw.get("source") if isinstance(raw.get("source"), str) else None,
        })
    return normalized


def search_images(
    query_text: str,
    *,
    page_size: int,
    timeout: int,
    retries: int,
    retry_delay: float,
) -> ImageSearchBatch:
    from ddgs import DDGS
    from ddgs.exceptions import DDGSException

    started = time.perf_counter()
    last_error = "request failed"
    for attempt in range(retries + 1):
        try:
            raw_results = DDGS(timeout=timeout).images(
                query=query_text,
                region=DDG_REGION,
                safesearch=DDG_SAFESEARCH,
                max_results=page_size,
            )
            if not raw_results:
                raise CollectionError("no image results")
            candidates = normalize_ddg_results(raw_results)
            if not candidates:
                raise CollectionError("no valid image candidates")
            return ImageSearchBatch(candidates, len(raw_results), time.perf_counter() - started)
        except (CollectionError, DDGSException) as error:
            last_error = str(error)
        if attempt < retries:
            time.sleep(retry_delay * (attempt + 1))
    raise CollectionError(f"DuckDuckGo image search failed: {last_error}")


def choose_image_result(word: str, results: list[dict[str, Any]]) -> dict[str, Any] | None:
    usable = usable_image_results(results)
    return usable[0] if usable else None


def usable_image_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [result for result in results if isinstance(result, dict) and result.get("image_url")]


def candidate_cache_path(word: str, index: int) -> Path:
    return CANDIDATE_CACHE_DIR / sanitize_filename(word) / f"{index:02d}.img"


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
    cleanup_candidate_cache(word)
    candidate_dir.mkdir(parents=True, exist_ok=True)

    for index, result in enumerate(usable_image_results(results), start=1):
        image_url = str(result["image_url"])
        cache_path = candidate_cache_path(word, index)
        try:
            download_candidate_image(
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
) -> tuple[dict[str, Any] | None, float | None, int, float, float]:
    from image_scorer import ImageScoringError

    download_started = time.perf_counter()
    candidates = download_candidate_images(
        word,
        results,
        timeout=timeout,
        retries=retries,
        retry_delay=retry_delay,
    )
    download_seconds = time.perf_counter() - download_started
    print("=" * 40)
    print(f"KEY: {word}")
    print(f"QUERY: {query_text}")
    print(f"CANDIDATES: {len(candidates)}")
    if not candidates:
        return None, None, 0, download_seconds, 0.0

    scoring_started = time.perf_counter()
    try:
        score_results = scorer.score_batch(query_text, [path for _result, path in candidates])
    except ImageScoringError as error:
        raise CollectionError(str(error)) from error
    scoring_seconds = time.perf_counter() - scoring_started

    scored_candidates = sorted(
        zip(candidates, score_results),
        key=lambda item: item[1].score,
        reverse=True,
    )

    for rank, ((result, _path), score_result) in enumerate(scored_candidates, start=1):
        print(f"{rank}. {result.get('image_url')}")
        print(f"   score={score_result.score:.4f}")

    (best_result, best_path), best_score = scored_candidates[0]
    print("SELECTED:")
    print(best_result.get("image_url"))
    print(f"score={best_score.score:.4f}")
    print("=" * 40)
    best_result["_siglip_candidate_path"] = str(best_path)
    return best_result, best_score.score, len(candidates), download_seconds, scoring_seconds


def validate_image_bytes(body: bytes) -> None:
    try:
        with Image.open(io.BytesIO(body)) as downloaded:
            width, height = downloaded.size
            if width < 1 or height < 1 or width * height > MAX_IMAGE_PIXELS:
                raise CollectionError(f"unsupported image dimensions: {width}x{height}")
            downloaded.verify()
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as error:
        raise CollectionError(f"downloaded payload is not a usable image: {error}") from error


def download_candidate_image(
    image_url: str,
    destination: Path,
    *,
    timeout: int,
    retries: int,
    retry_delay: float,
) -> None:
    body, _headers, _status = request_with_retry(
        image_url,
        timeout=timeout,
        retries=retries,
        retry_delay=retry_delay,
    )
    validate_image_bytes(body)
    temporary_path = destination.with_suffix(destination.suffix + ".tmp")
    try:
        temporary_path.write_bytes(body)
        temporary_path.replace(destination)
    except OSError:
        temporary_path.unlink(missing_ok=True)
        raise


def normalize_image_to_jpeg(source: Any, destination: Path) -> None:
    temporary_path = destination.with_suffix(".jpg.tmp")
    try:
        with Image.open(source) as downloaded:
            width, height = downloaded.size
            if width < 1 or height < 1 or width * height > MAX_IMAGE_PIXELS:
                raise CollectionError(f"unsupported image dimensions: {width}x{height}")
            normalized = ImageOps.exif_transpose(downloaded).convert("RGB")
            normalized.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
            normalized.save(
                temporary_path,
                format="JPEG",
                quality=JPEG_QUALITY,
                optimize=True,
            )
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as error:
        temporary_path.unlink(missing_ok=True)
        raise CollectionError(f"downloaded payload is not a usable image: {error}") from error
    if not is_valid_jpeg(temporary_path):
        temporary_path.unlink(missing_ok=True)
        raise CollectionError("saved file failed JPEG validation")
    temporary_path.replace(destination)


def download_image_as_jpeg(
    image_url: str,
    destination: Path,
    *,
    timeout: int,
    retries: int,
    retry_delay: float,
) -> None:
    body, _headers, _status = request_with_retry(
        image_url,
        timeout=timeout,
        retries=retries,
        retry_delay=retry_delay,
    )
    normalize_image_to_jpeg(io.BytesIO(body), destination)


def metadata_from_result(
    word: str,
    query_text: str,
    result: dict[str, Any],
    image_selection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = {
        "word": word,
        "search_query": query_text,
        "provider": result.get("provider"),
        "image_url": result.get("image_url"),
        "thumbnail_url": result.get("thumbnail_url"),
        "source_page_url": result.get("source_page_url"),
        "title": result.get("title"),
        "width": result.get("width"),
        "height": result.get("height"),
        "source": IMAGE_PROVIDER,
        "result_source": result.get("source"),
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


def is_valid_image_cache(image_path: Path, metadata_path: Path, query_text: str) -> bool:
    if not is_valid_jpeg(image_path) or not metadata_path.exists():
        return False
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    return (
        isinstance(metadata, dict)
        and metadata.get("provider") == IMAGE_PROVIDER
        and metadata.get("search_query") == query_text
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
    started = time.perf_counter()
    try:
        filename = sanitize_filename(word)
        image_path = IMAGE_DIR / f"{filename}.jpg"
        metadata_path = METADATA_DIR / f"{filename}.json"

        if is_valid_image_cache(image_path, metadata_path, query_text):
            print(f"[IMAGE] {word} -> SUCCESS: cached")
            return ImageResult(
                ok=True, word=word, query_text=query_text, status="cached",
                total_seconds=time.perf_counter() - started,
            )

        if image_path.exists() and not is_valid_jpeg(image_path):
            raise CollectionError("existing image file is not a valid JPEG")

        search_batch = search_images(
            query_text,
            page_size=page_size,
            timeout=timeout,
            retries=retries,
            retry_delay=retry_delay,
        )
        siglip_score = None
        candidate_count = 0
        download_seconds = 0.0
        scoring_seconds = 0.0
        if scorer:
            chosen, siglip_score, candidate_count, download_seconds, scoring_seconds = \
                choose_image_result_with_siglip(
                word,
                query_text,
                search_batch.candidates,
                scorer,
                timeout=timeout,
                retries=retries,
                retry_delay=retry_delay,
            )
        else:
            chosen = choose_image_result(query_text, search_batch.candidates)
        if not chosen:
            raise CollectionError("all DuckDuckGo candidate downloads failed")

        candidate_path = chosen.get("_siglip_candidate_path")
        if candidate_path:
            normalize_image_to_jpeg(candidate_path, image_path)
        else:
            download_started = time.perf_counter()
            download_image_as_jpeg(
                str(chosen["image_url"]),
                image_path,
                timeout=timeout,
                retries=retries,
                retry_delay=retry_delay,
            )
            download_seconds = time.perf_counter() - download_started
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

        total_seconds = time.perf_counter() - started
        print(
            f"[IMAGE] {word} ({query_text}) -> SUCCESS | raw={search_batch.raw_count} "
            f"valid={len(search_batch.candidates)} downloaded={candidate_count or 1} "
            f"search={search_batch.duration_seconds:.3f}s download={download_seconds:.3f}s "
            f"siglip={scoring_seconds:.3f}s total={total_seconds:.3f}s"
        )
        return ImageResult(
            ok=True,
            word=word,
            query_text=query_text,
            status="downloaded",
            selected_image=str(chosen.get("image_url")),
            siglip_score=siglip_score,
            candidate_count=candidate_count or 1,
            search_result_count=search_batch.raw_count,
            valid_candidate_count=len(search_batch.candidates),
            search_seconds=search_batch.duration_seconds,
            download_seconds=download_seconds,
            scoring_seconds=scoring_seconds,
            total_seconds=total_seconds,
        )
    except (CollectionError, OSError) as error:
        print(f"[IMAGE] {word} -> FAILED: {error}")
        return ImageResult(
            ok=False, word=word, query_text=query_text, status="failed", reason=str(error),
            total_seconds=time.perf_counter() - started,
        )


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
                f"raw={result.search_result_count} | valid={result.valid_candidate_count} | "
                f"downloaded={result.candidate_count} | score={result.siglip_score:.4f} | "
                f"search={result.search_seconds:.3f}s | download={result.download_seconds:.3f}s | "
                f"siglip={result.scoring_seconds:.3f}s | total={result.total_seconds:.3f}s | "
                f"image={result.selected_image}"
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
    parser = argparse.ArgumentParser(description="Collect English vocabulary images using DuckDuckGo and SigLIP.")
    parser.add_argument(
        "--vocabulary",
        type=Path,
        default=VOCABULARY_PATH,
        help="Path to canonical vocabulary file used for output filenames.",
    )
    # Resolve generator defaults in main, keeping argument parsing imports light.
    parser.add_argument("--qwen-model", help="Qwen model name or path; defaults to query_generator.DEFAULT_QWEN_MODEL.")
    parser.add_argument("--qwen-batch-size", type=int,
                        help="Generation batch size; defaults to query_generator.DEFAULT_BATCH_SIZE.")
    parser.add_argument("--qwen-cache", type=Path,
                        help="Query cache JSON; defaults to query_generator.DEFAULT_QUERY_CACHE.")
    parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help="Number of DuckDuckGo image candidates to request per word.",
    )
    parser.add_argument(
        "--no-siglip",
        action="store_true",
        help="Skip SigLIP and use the first valid DuckDuckGo result.",
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
    from query_generator import (
        DEFAULT_BATCH_SIZE, DEFAULT_QUERY_CACHE, DEFAULT_QWEN_MODEL, prepare_queries,
    )

    batch_size = DEFAULT_BATCH_SIZE if args.qwen_batch_size is None else args.qwen_batch_size
    if batch_size < 1:
        raise CollectionError("--qwen-batch-size must be at least 1")
    words = load_vocabulary(vocabulary_path)
    words_to_process = words[: args.limit]
    # Phase A completes (including Qwen release) before any image/scorer work.
    query_started = time.perf_counter()
    queries_to_process = prepare_queries(
        words, limit=args.limit,
        model_name=args.qwen_model if args.qwen_model is not None else DEFAULT_QWEN_MODEL,
        batch_size=batch_size,
        cache_path=resolve_project_path(args.qwen_cache if args.qwen_cache is not None else DEFAULT_QUERY_CACHE),
    )
    print(f"[QWEN] query preparation: {time.perf_counter() - query_started:.3f}s")
    if len(queries_to_process) != len(words_to_process):
        raise CollectionError(
            f"Qwen query count mismatch: expected {len(words_to_process)}, found {len(queries_to_process)}"
        )
    ensure_directories()

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
