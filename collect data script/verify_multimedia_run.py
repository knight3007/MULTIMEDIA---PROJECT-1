"""Check a completed private run's pack and gallery references without a browser."""
import argparse
import json
import re
from pathlib import Path

from content_pack_builder import validate_pack


def verify(root: Path):
    report = json.loads((root / "execution_report.json").read_text(encoding="utf-8"))
    pack_root = root / report["active_content_pack"]
    pack = json.loads((pack_root / "content_pack.json").read_text(encoding="utf-8"))
    validation = validate_pack(pack, pack_root)
    page = (root / "review_gallery.html").read_text(encoding="utf-8")
    match = re.search(r"const items=(\[.*?\]);let index", page)
    if not match:
        raise ValueError("Gallery item data missing")
    cards = json.loads(match.group(1))
    if not validation["valid"] or len(cards) != len(pack["items"]):
        raise ValueError("Pack invalid or gallery count mismatch")
    if not all(x in page for x in ('value="en"', 'value="ja"', 'id="search"', 'id="filter"', 'id="prev"', 'id="next"')):
        raise ValueError("Gallery mode, search, filter or navigation missing")
    for card, item in zip(cards, pack["items"]):
        if (card["id"], card["english"], card["japanese"], card["vietnamese"]) != tuple(item[k] for k in ("item_id", "english", "japanese", "vietnamese")):
            raise ValueError("Gallery vocabulary identity mismatch")
        for gallery_key, pack_key in (("image", "image"), ("en", "audio_english"), ("ja", "audio_japanese")):
            asset = item.get(pack_key)
            expected = f"{pack_root.name}/{asset['path']}" if asset else None
            if card[gallery_key] != expected or expected and not (root / expected).is_file():
                raise ValueError(f"Gallery {gallery_key} reference mismatch: {item['item_id']}")
    return {"valid": True, "cards": len(cards), "images": sum(bool(x["image"]) for x in cards),
            "english_audio": sum(bool(x["en"]) for x in cards), "japanese_audio": sum(bool(x["ja"]) for x in cards),
            "browser_checked": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    print(json.dumps(verify(parser.parse_args().run_dir)))
