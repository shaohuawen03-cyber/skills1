# Quality checks

Use this checklist before delivery.

## Text

- Exact visible wording is reproduced or explicitly marked as uncertain.
- Short labels do not wrap unexpectedly.
- Font size and weight match the source hierarchy.
- Text color, alignment, and baseline are visually consistent.
- Text boxes stay inside the slide and do not clip glyphs.

## Geometry

- Source aspect ratio is preserved.
- Major margins and anchors match.
- Repeated cards have consistent size and spacing.
- Separator lines and arrows meet the intended objects.
- Borders, corner radii, and stroke weights are visually close.

## Images

- Complex visual assets contain no neighboring text or structure.
- No asset is stretched unless the source is stretched.
- No full-page screenshot is used to fake fidelity.

## Background

- Pure white means `#FFFFFF`, with no scan tint or screenshot shadow.
- Preserve intentional colored panels and fills.
- Remove watermarks only when the user requests a clean reconstruction and the watermark is not part of the intended slide content.

## Render comparison

The provided comparison script reports normalized mean absolute error and edge F1. Treat these as review signals, not universal pass/fail thresholds. Fonts and renderer differences can change pixel metrics even when the slide is structurally correct.

Inspect the generated `rendered.png`, `diff.png`, and `metrics.json` before declaring strict fidelity.
