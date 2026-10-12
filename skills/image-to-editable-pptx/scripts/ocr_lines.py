#!/usr/bin/env python3
"""Extract candidate OCR lines and source-pixel boxes with Tesseract."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from PIL import Image
import pytesseract
from pytesseract import Output


CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def join_tokens(tokens: list[str]) -> str:
    result = ""
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        if not result:
            result = token
            continue
        if CJK_RE.search(result[-1]) and CJK_RE.search(token[0]):
            result += token
        elif token[0] in ",.;:!?%)]}，。；：！？％）】》":
            result += token
        elif result[-1] in "([{（【《":
            result += token
        else:
            result += " " + token
    return result


def extract(image_path: Path, lang: str, min_conf: float) -> dict:
    image = Image.open(image_path).convert("RGB")
    data = pytesseract.image_to_data(image, lang=lang, output_type=Output.DICT, config="--psm 6")
    groups: dict[tuple[int, int, int, int], list[int]] = defaultdict(list)
    count = len(data["text"])
    for i in range(count):
        text = str(data["text"][i]).strip()
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            conf = -1.0
        if not text or conf < min_conf:
            continue
        key = (
            int(data["page_num"][i]),
            int(data["block_num"][i]),
            int(data["par_num"][i]),
            int(data["line_num"][i]),
        )
        groups[key].append(i)

    lines = []
    for line_index, (_, indexes) in enumerate(sorted(groups.items()), start=1):
        left = min(int(data["left"][i]) for i in indexes)
        top = min(int(data["top"][i]) for i in indexes)
        right = max(int(data["left"][i]) + int(data["width"][i]) for i in indexes)
        bottom = max(int(data["top"][i]) + int(data["height"][i]) for i in indexes)
        tokens = [str(data["text"][i]).strip() for i in indexes]
        confidences = [float(data["conf"][i]) for i in indexes]
        lines.append(
            {
                "id": f"ocr-line-{line_index}",
                "text": join_tokens(tokens),
                "bbox": [left, top, right - left, bottom - top],
                "confidence": round(sum(confidences) / len(confidences), 2),
                "tokens": tokens,
            }
        )
    return {"image": str(image_path), "width_px": image.width, "height_px": image.height, "lang": lang, "lines": lines}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--lang", default="eng")
    parser.add_argument("--min-conf", type=float, default=55.0)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    payload = extract(Path(args.image), args.lang, args.min_conf)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
