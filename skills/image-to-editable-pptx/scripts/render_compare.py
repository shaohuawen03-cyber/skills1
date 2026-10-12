#!/usr/bin/env python3
"""Render the first slide and compare it with a source image at source resolution."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def executable(*names: str) -> str:
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    raise RuntimeError(f"Missing executable: {' or '.join(names)}")


def render_first_slide(pptx: Path, out_png: Path) -> None:
    soffice = executable("soffice", "libreoffice")
    pdftoppm = executable("pdftoppm")
    with tempfile.TemporaryDirectory(prefix="pptx-render-") as tmp:
        tmp_path = Path(tmp)
        proc = subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(tmp_path), str(pptx)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=120,
        )
        pdf = tmp_path / f"{pptx.stem}.pdf"
        if proc.returncode != 0 or not pdf.exists():
            raise RuntimeError(f"LibreOffice export failed: {proc.stdout}")
        prefix = tmp_path / "slide"
        proc = subprocess.run(
            [pdftoppm, "-f", "1", "-singlefile", "-png", "-r", "150", str(pdf), str(prefix)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=120,
        )
        rendered = prefix.with_suffix(".png")
        if proc.returncode != 0 or not rendered.exists():
            raise RuntimeError(f"pdftoppm failed: {proc.stdout}")
        shutil.copy2(rendered, out_png)


def edge_f1(a: np.ndarray, b: np.ndarray) -> float:
    ga = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
    gb = cv2.cvtColor(b, cv2.COLOR_RGB2GRAY)
    ea = cv2.Canny(ga, 80, 180) > 0
    eb = cv2.Canny(gb, 80, 180) > 0
    tp = np.logical_and(ea, eb).sum()
    fp = np.logical_and(~ea, eb).sum()
    fn = np.logical_and(ea, ~eb).sum()
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    return float(2 * precision * recall / max(precision + recall, 1e-12))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_image")
    parser.add_argument("pptx")
    parser.add_argument("--outdir", default="quality")
    args = parser.parse_args()

    source_path = Path(args.source_image)
    pptx_path = Path(args.pptx)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    rendered_path = outdir / "rendered.png"
    render_first_slide(pptx_path, rendered_path)

    source = np.array(Image.open(source_path).convert("RGB"))
    rendered = np.array(Image.open(rendered_path).convert("RGB").resize((source.shape[1], source.shape[0]), Image.Resampling.LANCZOS))
    diff = cv2.absdiff(source, rendered)
    Image.fromarray(diff).save(outdir / "diff.png")
    Image.fromarray(rendered).save(outdir / "rendered_resized.png")

    metrics = {
        "source_width": int(source.shape[1]),
        "source_height": int(source.shape[0]),
        "normalized_mae": float(np.mean(diff) / 255.0),
        "edge_f1": edge_f1(source, rendered),
        "note": "Use these metrics as review signals; renderer and font differences can change pixel scores.",
    }
    (outdir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
