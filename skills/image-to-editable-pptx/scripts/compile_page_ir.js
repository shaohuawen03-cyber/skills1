#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const PptxGenJS = require('pptxgenjs');

function fail(message) {
  console.error(message);
  process.exit(2);
}

function hex(value, fallback) {
  if (value === null || value === undefined) return fallback;
  return String(value).replace(/^#/, '').toUpperCase();
}

function pxBoxToInches(bbox, sx, sy) {
  return { x: bbox[0] * sx, y: bbox[1] * sy, w: bbox[2] * sx, h: bbox[3] * sy };
}

function mapShapeType(pptx, type) {
  const mapping = {
    rect: 'rect',
    round_rect: 'roundRect',
    ellipse: 'ellipse',
    triangle: 'triangle',
    chevron: 'chevron',
  };
  const key = mapping[type];
  if (!key || !pptx.ShapeType[key]) fail(`Unsupported shape type: ${type}`);
  return pptx.ShapeType[key];
}

function mapDash(value) {
  const mapping = { solid: 'solid', dash: 'dash', dot: 'dot', dash_dot: 'dashDot' };
  return mapping[value || 'solid'] || 'solid';
}

function mapArrow(value) {
  return value === 'triangle' ? 'triangle' : 'none';
}

function addObject(slide, pptx, obj, sx, sy, baseDir) {
  const style = obj.style || {};
  if (obj.type === 'text') {
    const box = pxBoxToInches(obj.bbox, sx, sy);
    const opts = {
      ...box,
      fontFace: style.font_face || 'Arial',
      fontSize: Number(style.font_size_pt || 18),
      bold: Boolean(style.bold),
      italic: Boolean(style.italic),
      color: hex(style.color, '111111'),
      align: style.align || 'left',
      valign: style.valign || 'top',
      margin: Number(style.margin_pt || 0) / 72,
      breakLine: false,
      paraSpaceAfterPt: 0,
      lineSpacingMultiple: 1.0,
      isTextBox: true,
    };
    slide.addText(obj.text || '', opts);
    return;
  }

  if (obj.type === 'line') {
    const [x1, y1, x2, y2] = obj.points;
    const line = {
      color: hex(style.color, '111111'),
      width: Number(style.width_pt || 1),
      dash: mapDash(style.dash),
      beginArrowType: mapArrow(style.start_arrow),
      endArrowType: mapArrow(style.end_arrow),
    };
    slide.addShape(pptx.ShapeType.line, {
      x: x1 * sx,
      y: y1 * sy,
      w: (x2 - x1) * sx,
      h: (y2 - y1) * sy,
      line,
    });
    return;
  }

  if (obj.type === 'image') {
    const box = pxBoxToInches(obj.bbox, sx, sy);
    const imagePath = path.isAbsolute(obj.path) ? obj.path : path.resolve(baseDir, obj.path);
    slide.addImage({ path: imagePath, ...box });
    return;
  }

  const box = pxBoxToInches(obj.bbox, sx, sy);
  const shapeOpts = { ...box };
  if (style.fill === null) shapeOpts.fill = { color: 'FFFFFF', transparency: 100 };
  else shapeOpts.fill = { color: hex(style.fill, 'FFFFFF'), transparency: Number(style.fill_transparency || 0) };
  if (style.line === null) shapeOpts.line = { color: 'FFFFFF', transparency: 100, width: 0 };
  else shapeOpts.line = { color: hex(style.line, '111111'), width: Number(style.line_width_pt || 1) };
  slide.addShape(mapShapeType(pptx, obj.type), shapeOpts);
}

async function main() {
  const [, , irPathArg, outputPathArg] = process.argv;
  if (!irPathArg || !outputPathArg) fail('Usage: node scripts/compile_page_ir.js page_ir.json output.pptx');
  const irPath = path.resolve(irPathArg);
  const outputPath = path.resolve(outputPathArg);
  const payload = JSON.parse(fs.readFileSync(irPath, 'utf8'));
  if (!payload.pages || payload.pages.length === 0) fail('PageIR contains no pages');

  const first = payload.pages[0];
  const aspect = Number(first.width_px) / Number(first.height_px);
  if (!Number.isFinite(aspect) || aspect <= 0) fail('Invalid page dimensions');
  const pptx = new PptxGenJS();
  const slideWidth = 13.333333;
  const slideHeight = slideWidth / aspect;
  pptx.defineLayout({ name: 'SOURCE_RATIO', width: slideWidth, height: slideHeight });
  pptx.layout = 'SOURCE_RATIO';
  pptx.author = 'image-to-editable-pptx';
  pptx.subject = 'Editable reconstruction from PageIR';
  pptx.title = 'Editable PowerPoint reconstruction';
  pptx.company = '';
  pptx.lang = 'zh-CN';
  pptx.theme = {
    headFontFace: 'Arial',
    bodyFontFace: 'Arial',
    lang: 'zh-CN',
  };

  const baseDir = path.dirname(irPath);
  for (const page of payload.pages) {
    const currentAspect = Number(page.width_px) / Number(page.height_px);
    if (Math.abs(currentAspect - aspect) / aspect > 0.001) fail('All pages must share the same aspect ratio');
    const slide = pptx.addSlide();
    slide.background = { color: hex(page.background || '#FFFFFF', 'FFFFFF') };
    const sx = slideWidth / Number(page.width_px);
    const sy = slideHeight / Number(page.height_px);
    const objects = [...(page.objects || [])].sort((a, b) => Number(a.z || 0) - Number(b.z || 0));
    for (const obj of objects) addObject(slide, pptx, obj, sx, sy, baseDir);
  }

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  await pptx.writeFile({ fileName: outputPath });
  console.log(JSON.stringify({ output: outputPath, slides: payload.pages.length, width_in: slideWidth, height_in: slideHeight }));
}

main().catch((err) => {
  console.error(err && err.stack ? err.stack : String(err));
  process.exit(1);
});
