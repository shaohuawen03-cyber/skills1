import sys
path, out = sys.argv[1], sys.argv[2]
text = None
try:
    import fitz  # PyMuPDF
    doc = fitz.open(path)
    text = "\n\n".join(page.get_text() for page in doc)
except Exception:
    try:
        from pypdf import PdfReader
        text = "\n\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
    except Exception as e:
        print("no PDF text library: " + str(e))
if text is not None:
    open(out, "w", encoding="utf-8").write(text)
    print("text chars: %d" % len(text))
