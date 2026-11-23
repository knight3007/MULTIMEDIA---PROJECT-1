"""Create A-001 versus A-004 top-image sheets for preliminary visual review."""
import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def draw_image(canvas, path, box):
    if not path or path == "MISSING_EVIDENCE":
        return
    with Image.open(ROOT / path) as source:
        picture = ImageOps.contain(source.convert("RGB"), (box[2] - box[0], box[3] - box[1]))
    x = box[0] + (box[2] - box[0] - picture.width) // 2
    y = box[1] + (box[3] - box[1] - picture.height) // 2
    canvas.paste(picture, (x, y))


def main():
    with (HERE / "frozen_vocabulary.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    retrieval = json.loads((HERE / "retrieval_results.json").read_text(encoding="utf-8"))
    font_path = Path("C:/Windows/Fonts/arial.ttf")
    font = ImageFont.truetype(str(font_path), 17) if font_path.is_file() else ImageFont.load_default()
    out = HERE / "contact_sheets"
    out.mkdir(exist_ok=True)
    for start in range(0, len(rows), 10):
        page = Image.new("RGB", (1200, 1250), "#f4f5f3")
        pen = ImageDraw.Draw(page)
        for offset, row in enumerate(rows[start:start + 10]):
            vid = row["vocab_id"]
            result = retrieval.get(vid, {})
            chosen = next((c for c in result.get("candidates", []) if c["candidate_id"] == result.get("proposed_candidate_id")), None)
            col, line = offset % 2, offset // 2
            x, y = col * 600, line * 250
            pen.rectangle((x + 5, y + 5, x + 595, y + 245), fill="white", outline="#bfcac6")
            pen.text((x + 15, y + 10), f'{vid[-3:]} {row["english"]} · {result.get("status", "NOT_RUN")}', fill="#152725", font=font)
            pen.text((x + 15, y + 36), "A-001", fill="#41514d", font=font)
            pen.text((x + 305, y + 36), "A-004 top-1", fill="#41514d", font=font)
            draw_image(page, row["previous_image_path"], (x + 12, y + 62, x + 285, y + 230))
            draw_image(page, chosen["jpeg_path"] if chosen else None, (x + 302, y + 62, x + 575, y + 230))
        page.save(out / f"top1_{start + 1:03d}_{start + len(rows[start:start + 10]):03d}.jpg", quality=88)
    print("contact sheets", len(list(out.glob("top1_*.jpg"))))


if __name__ == "__main__":
    main()
