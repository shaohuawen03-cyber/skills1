---
name: image-to-editable-pptx
description: Rebuild flattened slide images, screenshots, scanned presentation pages, or image-based PPTX pages into source-faithful editable PowerPoint files. Use when ChatGPT needs to recreate slide text as editable text, rebuild simple lines/panels/arrows as native PowerPoint shapes, preserve the original page ratio and layout, optionally force a pure white background, and validate the rendered result against the source image before delivery.
---

# Image to Editable PPTX

Reconstruct the visible content of a flattened slide into an editable `.pptx` without redesigning it. Preserve source wording, hierarchy, geometry, and visual rhythm; do not claim recovery of hidden vectors, original chart data, masters, animations, or inaccessible source content.

## Core rules

- Treat the supplied raster or image-based slide as the visual source of truth.
- Recreate readable text as editable text boxes.
- Recreate simple panels, borders, separators, arrows, and geometric icons as native PowerPoint shapes.
- Use raster assets only for complex visuals that cannot be reproduced reliably with native shapes.
- Never use the entire source image as the visible slide background when the user asks for an editable reconstruction.
- Never replace an icon with an emoji, font glyph, or unrelated symbol.
- Preserve the source aspect ratio and use source-pixel coordinates as the canonical geometry space.
- Use a pure white background when the user explicitly asks for white/clean background; otherwise preserve the visible source background.
- Keep uncertain OCR or visual interpretation explicit and review it against the source before delivery.

## Workflow

1. Run a runtime check when code execution is available:

```bash
python3 scripts/runtime_check.py --ocr-lang chi_sim+eng
```

2. Inspect the source image visually. Record the source width and height.
3. Extract candidate text if useful:

```bash
python3 scripts/ocr_lines.py source.png --lang chi_sim+eng --out analysis/ocr_lines.json
```

Treat OCR only as evidence. Correct wording, punctuation, spacing, and line breaks against the source.

4. Build a PageIR JSON file using `references/pageir-schema.md`. Represent each visible object once.
5. Validate the PageIR:

```bash
python3 scripts/validate_page_ir.py page_ir.json
```

6. Compile the PageIR into PowerPoint:

```bash
node scripts/compile_page_ir.js page_ir.json output.pptx
```

7. Inspect the compiled deck for canvas overflow and full-slide image shortcuts:

```bash
python3 scripts/inspect_pptx.py output.pptx
```

8. Render and compare the result when LibreOffice and Poppler are available:

```bash
python3 scripts/render_compare.py source.png output.pptx --outdir quality
```

9. Review the source, rendered slide, and difference image. Repair PageIR geometry or styling rather than hiding differences with a full-slide screenshot.
10. Re-run validation and comparison after every material repair.
11. Deliver only the final editable `.pptx` and disclose any unresolved model-inferred text or visual approximation.

## Representation decisions

Use these default mappings:

- `text`: titles, labels, captions, body copy, numbers, badges, table text.
- `rect`, `round_rect`, `ellipse`, `triangle`, `chevron`: simple native geometry.
- `line`: separators, connectors, arrows, underlines, simple strokes.
- `image`: complex logos, illustrations, textured graphics, photos, or dense pictorial icons.

For a complex image object, use an asset with transparent or white-safe margins and place it in the exact source-pixel rectangle. Avoid crop/stretch behavior unless the source itself is visibly stretched.

## Text fidelity

- Use one text object per visible source line for titles, short labels, captions, and badges.
- Preserve visible line breaks.
- Do not auto-rewrite wording.
- Prefer explicit font size and box geometry over shrink-to-fit.
- Match boldness, alignment, color, and approximate font family.
- If the exact font is unavailable, choose the nearest metric-compatible font and re-check the render.

## White-background requests

When the user asks for a pure white background:

- Set `page.background` to `#FFFFFF`.
- Rebuild all foreground boxes and separators independently.
- Do not retain scanned paper tint, screenshot shadows, or watermarks as background texture.
- Do not remove foreground content that is genuinely part of the design.

## Quality gates

Before delivery, require all of the following:

- Source and output aspect ratios match within 0.1%.
- All readable source text intended to remain text is editable.
- No text box or shape is outside the slide canvas.
- No unintended object overlap or clipping is visible.
- No full-slide raster shortcut is visible in the final deck.
- Background matches the user request.
- Major anchors, columns, rows, arrows, and separators align with the source.
- Rendered differences are reviewed at full-slide and local-object level.

Use `references/quality-checks.md` for the detailed review checklist.

## Output contract

Use a concise final response and link the generated `.pptx`. If a machine or visual gate cannot be completed, state the exact limitation instead of claiming strict fidelity.

## References

- Read `references/pageir-schema.md` when authoring or repairing PageIR.
- Read `references/workflow.md` for the full reconstruction and repair runbook.
- Read `references/quality-checks.md` before final delivery.
