---
name: pdf-extract
description: Use when the user wants to extract text, tables, or images from a PDF file — including scanned/image-only PDFs needing OCR — or asks to "read this PDF", "extract text from PDF", "what's in this PDF", or to pull tables/images out of one.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [pdf, ocr, text-extraction, table-extraction, pymupdf, tesseract]
    related_skills: [ocr-documents, markdown-to-pdf, csv-toolkit]
---

# pdf-extract

## Overview

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

## Common Pitfalls

1. **Scanned PDFs return empty text.** `get_text()` returns `""` for image-only PDFs — always check text length and fall back to OCR.
2. **OCR is slow.** Rendering at 300 DPI and running tesseract takes 2-5 seconds per page — warn the user before running it on large PDFs.
3. **Encrypted PDFs fail to open.** `fitz.open()` raises on password-protected PDFs — call `doc.authenticate("password")` first if the password is known.
4. **Table extraction quality varies.** pdfplumber handles bordered tables well but struggles with borderless ones — check the output before trusting it.
5. **Large PDFs exhaust memory.** A 500-page PDF loaded whole with pymupdf can use significant RAM — process pages one at a time if memory is constrained.
6. **Missing Tesseract language packs.** Non-English PDFs need the matching pack (e.g. `tesseract-ocr-fra`) installed and `lang='fra'` passed to `image_to_string`, or OCR silently produces garbage text.

## Verification Checklist

- [ ] Checked average chars/page before deciding text-extraction vs. OCR
- [ ] Extracted text/table/image count is consistent with the source PDF's page count
- [ ] OCR output spot-checked for garbled text when a scanned PDF was processed
- [ ] Correct Tesseract language pack used for non-English documents
- [ ] Password-protected PDFs authenticated successfully before extraction was attempted
- [ ] Output files (images, extracted text/tables) saved where the user expects them
