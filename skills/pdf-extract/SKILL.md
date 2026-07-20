---
name: pdf-extract
description: "Extract text, images, and tables from PDFs — agent + this skill = user gets structured content from any PDF file."
version: 1.0.0
---

# pdf-extract

Extract text, images, and tables from PDF files using open-source Python libraries. The agent handles PDF parsing, OCR fallback for scanned documents, and structured output.

## When to Use

- The user wants to extract text from a PDF.
- The user has a scanned PDF that needs OCR.
- The user wants to pull tables or images out of a PDF.
- The user says "read this PDF", "extract text from PDF", or "what's in this PDF".

## Prerequisites

```bash
pip install pymupdf pdfplumber pillow
# For OCR fallback:
pip install pytesseract
# Also install tesseract-ocr system package:
# Linux: apt install tesseract-ocr
# macOS: brew install tesseract
# Windows: download from https://github.com/UB-Mannheim/tesseract/wiki
```

## Text Extraction

### Basic text extraction (pymupdf)

```python
import fitz  # pymupdf

def extract_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    text = []
    for page in doc:
        text.append(page.get_text())
    return "\n".join(text)
```

### With page numbers

```python
def extract_text_with_pages(pdf_path: str) -> list[dict]:
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        pages.append({
            "page": i + 1,
            "text": page.get_text()
        })
    return pages
```

## Table Extraction

```python
import pdfplumber

def extract_tables(pdf_path: str) -> list:
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_tables = page.extract_tables()
            for table in page_tables:
                tables.append({"page": i + 1, "rows": table})
    return tables
```

## Image Extraction

```python
import fitz
import os

def extract_images(pdf_path: str, output_dir: str = "./extracted_images"):
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    images = []
    for page_num, page in enumerate(doc):
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]
            filename = f"{output_dir}/page{page_num+1}_img{img_index+1}.{ext}"
            with open(filename, "wb") as f:
                f.write(image_bytes)
            images.append(filename)
    return images
```

## OCR Fallback (for scanned PDFs)

If `get_text()` returns empty or near-empty, the PDF is likely scanned images. Use OCR:

```python
import fitz
import pytesseract
from PIL import Image
import io

def extract_with_ocr(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    text = []
    for page in doc:
        # Render page to image at 300 DPI
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        page_text = pytesseract.image_to_string(img)
        text.append(page_text)
    return "\n".join(text)
```

## Auto-detect: text vs scanned

```python
def extract_pdf(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    # Try direct text extraction
    total_text = "".join(page.get_text() for page in doc)
    # If less than 50 chars per page on average, use OCR
    if len(total_text) / len(doc) < 50:
        return extract_with_ocr(pdf_path)
    return total_text
```

## Workflow

1. Identify the PDF file path
2. Try direct text extraction with pymupdf
3. If text is sparse (< 50 chars/page average), fall back to OCR
4. If the user needs tables, use pdfplumber
5. If the user needs images, extract with pymupdf's image API
6. Return structured output (text, tables, or image paths)

## Pitfalls

- **Scanned PDFs return empty text** — `get_text()` returns "" for image-only PDFs. Always check text length and fall back to OCR.
- **OCR is slow** — Rendering at 300 DPI and running tesseract takes 2-5 seconds per page. For large PDFs, warn the user.
- **Encrypted PDFs** — `fitz.open()` will fail on password-protected PDFs. Use `doc.authenticate("password")` if the password is known.
- **Table extraction quality varies** — pdfplumber works well for bordered tables but struggles with borderless tables. Check the output.
- **Large PDFs use lots of memory** — A 500-page PDF loaded with pymupdf uses significant RAM. Process pages one at a time if memory is constrained.
- **Tesseract language packs** — For non-English PDFs, install the appropriate language pack: `tesseract-ocr-fra` for French, etc. Pass `lang='fra'` to `image_to_string`.
