# PageIR schema

PageIR is the only page-specific construction input. Keep geometry in source pixels so the source image remains the canonical coordinate system.

## Top level

```json
{
  "schema_version": "1.0",
  "pages": []
}
```

Each page must contain:

```json
{
  "id": "slide-1",
  "width_px": 1600,
  "height_px": 900,
  "background": "#FFFFFF",
  "objects": []
}
```

All pages in one deck must have the same aspect ratio within 0.1%.

## Common object fields

Every object needs a unique `id` and a `type`. Objects with a rectangular extent use:

```json
"bbox": [x, y, width, height]
```

Coordinates are source pixels, with origin at the source image's top-left corner.

Optional `z` controls back-to-front order. Lower values render first.

## Text

```json
{
  "id": "title",
  "type": "text",
  "bbox": [54, 36, 1150, 92],
  "text": "Editable title",
  "style": {
    "font_face": "Microsoft YaHei",
    "font_size_pt": 30,
    "bold": true,
    "color": "#111111",
    "align": "left",
    "valign": "top",
    "margin_pt": 0
  }
}
```

Supported alignments are `left`, `center`, `right`. Supported vertical alignments are `top`, `mid`, `bottom`.

## Native shape

Use `rect`, `round_rect`, `ellipse`, `triangle`, or `chevron`.

```json
{
  "id": "panel",
  "type": "round_rect",
  "bbox": [100, 220, 360, 180],
  "style": {
    "fill": "#FFF4EF",
    "line": "#F05A28",
    "line_width_pt": 1.5
  }
}
```

Set `fill` to `null` for no fill and `line` to `null` for no outline.

## Line or arrow

```json
{
  "id": "arrow-1",
  "type": "line",
  "points": [510, 300, 690, 300],
  "style": {
    "color": "#F05A28",
    "width_pt": 2.0,
    "dash": "solid",
    "start_arrow": "none",
    "end_arrow": "triangle"
  }
}
```

Supported dash values are `solid`, `dash`, `dot`, and `dash_dot`.

## Image asset

Use image assets only for visual content that is not reliable as PowerPoint primitives.

```json
{
  "id": "illustration-1",
  "type": "image",
  "bbox": [1200, 160, 210, 210],
  "path": "assets/illustration-1.png"
}
```

The compiler places the image into the exact PageIR frame. Prepare the PNG canvas so its aspect ratio matches the intended source rectangle.

## Layering

Sort objects by `z` when overlap matters. Use this common order:

1. large background panels;
2. separators and connectors;
3. images and icons;
4. text.

Avoid duplicate objects that visually own the same source content.
