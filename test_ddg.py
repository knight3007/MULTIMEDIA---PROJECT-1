from io import BytesIO
from pathlib import Path

import requests
from ddgs import DDGS
from PIL import Image


MAX_IMAGE_SIZE = (1024, 1024)
JPEG_QUALITY = 90

OUTPUT_DIR = Path("test_images")


def search_images(keyword: str, max_results: int = 10) -> list[str]:
    keyword = keyword.strip()

    if not keyword:
        raise ValueError("Keyword cannot be empty.")

    results = DDGS().images(
        query=keyword,
        safesearch="moderate",
        max_results=max_results,
    )

    return [
        result["image"]
        for result in results
        if result.get("image")
    ]


def download_and_normalize_image(
    url: str,
    output_path: Path,
) -> None:
    """
    Download an image and normalize it for flashcard usage.

    Rules:
    - Do not crop.
    - Preserve aspect ratio.
    - Do not upscale small images.
    - Resize only if the image exceeds 1024x1024.
    - Convert to RGB JPEG.
    """

    response = requests.get(
        url,
        timeout=15,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        },
    )

    response.raise_for_status()

    image = Image.open(BytesIO(response.content))

    # Normalize orientation from EXIF metadata if needed.
    from PIL import ImageOps
    image = ImageOps.exif_transpose(image)

    # Convert PNG/WebP/RGBA/etc. into standard RGB.
    image = image.convert("RGB")

    original_size = image.size

    # Resize while preserving aspect ratio.
    # thumbnail() never enlarges an image.
    image.thumbnail(
        MAX_IMAGE_SIZE,
        Image.Resampling.LANCZOS,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    image.save(
        output_path,
        format="JPEG",
        quality=JPEG_QUALITY,
        optimize=True,
    )

    print(
        f"    Original: {original_size[0]}x{original_size[1]} "
        f"-> Saved: {image.width}x{image.height}"
    )


if __name__ == "__main__":
    keyword = input("Search keyword: ").strip()

    try:
        urls = search_images(
            keyword,
            max_results=10,
        )

        print(
            f"\nFound {len(urls)} images "
            f"for: {keyword}\n"
        )

        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        downloaded = 0

        for index, url in enumerate(
            urls,
            start=1,
        ):
            print(f"{index:02d}. {url}")

            output_path = (
                OUTPUT_DIR
                / f"{index:02d}.jpg"
            )

            try:
                download_and_normalize_image(
                    url=url,
                    output_path=output_path,
                )

                print(
                    f"    Saved: {output_path}\n"
                )

                downloaded += 1

            except Exception as exc:
                print(
                    f"    Failed: {exc}\n"
                )

        print(
            f"Finished: "
            f"{downloaded}/{len(urls)} "
            f"images downloaded."
        )

    except Exception as exc:
        print(
            f"Search failed: {exc}"
        )
