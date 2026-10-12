#!/usr/bin/env python3
"""Validate the compact PageIR used by the public image-to-editable-PPTX skill."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


ALLOWED_TYPES = {"text", "rect", "round_rect", "ellipse", "triangle", "chevron", "line", "image"}
ALLOWED_ALIGN = {"left", "center", "right"}
ALLOWED_VALIGN = {"top", "mid", "bottom"}
ALLOWED_DASH = {"solid", "dash", "dot", "dash_dot"}
ALLOWED_ARROW = {"none", "triangle"}


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def validate_bbox(bbox: Any, page_w: float, page_h: float, path: str, errors: list[str]) -> None:
    if not isinstance(bbox, list) or len(bbox) != 4 or not all(is_number(v) for v in bbox):
        errors.append(f"{path}.bbox must be [x,y,width,height]")
        return
    x, y, w, h = [float(v) for v in bbox]
    if w <= 0 or h <= 0:
        errors.append(f"{path}.bbox width/height must be positive")
    tolerance = 1.0
    if x < -tolerance or y < -tolerance or x + w > page_w + tolerance or y + h > page_h + tolerance:
        errors.append(f"{path}.bbox is outside the page")


def validate_page_ir(payload: Any, base_dir: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["PageIR root must be an object"]
    if payload.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")
    pages = payload.get("pages")
    if not isinstance(pages, list) or not pages:
        errors.append("pages must be a non-empty array")
        return errors

    ratios: list[float] = []
    page_ids: set[str] = set()
    for p_idx, page in enumerate(pages):
        ppath = f"pages[{p_idx}]"
        if not isinstance(page, dict):
            errors.append(f"{ppath} must be an object")
            continue
        page_id = page.get("id")
        if not isinstance(page_id, str) or not page_id.strip():
            errors.append(f"{ppath}.id must be a non-empty string")
        elif page_id in page_ids:
            errors.append(f"duplicate page id: {page_id}")
        else:
            page_ids.add(page_id)

        page_w = page.get("width_px")
        page_h = page.get("height_px")
        if not is_number(page_w) or float(page_w) <= 0 or not is_number(page_h) or float(page_h) <= 0:
            errors.append(f"{ppath}.width_px and height_px must be positive numbers")
            continue
        page_w = float(page_w)
        page_h = float(page_h)
        ratios.append(page_w / page_h)

        bg = page.get("background", "#FFFFFF")
        if not isinstance(bg, str) or not bg.startswith("#") or len(bg) not in (4, 7):
            errors.append(f"{ppath}.background must be a hex color")

        objects = page.get("objects")
        if not isinstance(objects, list):
            errors.append(f"{ppath}.objects must be an array")
            continue
        object_ids: set[str] = set()
        for o_idx, obj in enumerate(objects):
            opath = f"{ppath}.objects[{o_idx}]"
            if not isinstance(obj, dict):
                errors.append(f"{opath} must be an object")
                continue
            obj_id = obj.get("id")
            if not isinstance(obj_id, str) or not obj_id.strip():
                errors.append(f"{opath}.id must be a non-empty string")
            elif obj_id in object_ids:
                errors.append(f"duplicate object id on {page_id}: {obj_id}")
            else:
                object_ids.add(obj_id)
            obj_type = obj.get("type")
            if obj_type not in ALLOWED_TYPES:
                errors.append(f"{opath}.type must be one of {sorted(ALLOWED_TYPES)}")
                continue

            if obj_type == "line":
                points = obj.get("points")
                if not isinstance(points, list) or len(points) != 4 or not all(is_number(v) for v in points):
                    errors.append(f"{opath}.points must be [x1,y1,x2,y2]")
                else:
                    x1, y1, x2, y2 = [float(v) for v in points]
                    if min(x1, x2) < -1 or min(y1, y2) < -1 or max(x1, x2) > page_w + 1 or max(y1, y2) > page_h + 1:
                        errors.append(f"{opath}.points are outside the page")
                style = obj.get("style", {})
                if style.get("dash", "solid") not in ALLOWED_DASH:
                    errors.append(f"{opath}.style.dash is invalid")
                if style.get("start_arrow", "none") not in ALLOWED_ARROW or style.get("end_arrow", "none") not in ALLOWED_ARROW:
                    errors.append(f"{opath}.style arrow type is invalid")
                continue

            validate_bbox(obj.get("bbox"), page_w, page_h, opath, errors)

            if obj_type == "text":
                if not isinstance(obj.get("text"), str):
                    errors.append(f"{opath}.text must be a string")
                style = obj.get("style", {})
                if style.get("align", "left") not in ALLOWED_ALIGN:
                    errors.append(f"{opath}.style.align is invalid")
                if style.get("valign", "top") not in ALLOWED_VALIGN:
                    errors.append(f"{opath}.style.valign is invalid")
            elif obj_type == "image":
                rel = obj.get("path")
                if not isinstance(rel, str) or not rel.strip():
                    errors.append(f"{opath}.path must be a non-empty string")
                else:
                    image_path = (base_dir / rel).resolve() if not Path(rel).is_absolute() else Path(rel)
                    if not image_path.exists():
                        errors.append(f"{opath}.path does not exist: {rel}")

    if ratios:
        base = ratios[0]
        for idx, ratio in enumerate(ratios[1:], start=1):
            if abs(ratio - base) / base > 0.001:
                errors.append(f"pages[{idx}] aspect ratio differs by more than 0.1%")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("page_ir")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    path = Path(args.page_ir)
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_page_ir(payload, path.resolve().parent)
    result = {"valid": not errors, "errors": errors}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif errors:
        print("PageIR validation failed:")
        for item in errors:
            print(f"- {item}")
    else:
        print("PageIR validation passed")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
