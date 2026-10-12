---
name: harness-anything-wps
description: "Control local WPS Office (Writer / Calc / Impress) or Microsoft Office via COM CLI (cli-anything-wps) to batch-generate and edit native .docx, .xlsx, .pptx, and .pdf files. Ideal for 学科课件0到1变现SOP (courseware PPTX & teaching plans) and AI代做商业计划书 (Word BP + Pitch Deck PPTX)."
---

# harness-anything-wps (cli-anything-wps)

Let AI agents control Windows WPS Office (`KWPS.Application`, `KET.Application`, `KWPP.Application`) or MS Office via 47 CLI commands (`cli-anything-wps`), producing 100% native editable `.docx`, `.xlsx`, `.pptx`, and `.pdf` deliverables.

## Quick Start

See [`README_CN.md`](./README_CN.md) and [`WPS.md`](./WPS.md) for the complete command reference.

```bash
# Writer (.docx)
cli-anything-wps document new --type writer --name "report" -o report.json
cli-anything-wps --project report.json writer add-heading -t "一、项目概述" -l 1
cli-anything-wps --project report.json writer add-paragraph -t "正文内容..."
cli-anything-wps --project report.json export render report.docx -p docx

# Impress (.pptx)
cli-anything-wps document new --type impress --name "slides" -o slides.json
cli-anything-wps --project slides.json impress add-slide -t "封面标题" -c "副标题"
cli-anything-wps --project slides.json export render slides.pptx -p pptx
```
