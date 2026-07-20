# pdf-extract

Extract text, tables, and images from PDF files — with OCR fallback for scanned documents.

## What it does

The agent reads a PDF and extracts its content as structured text. For normal PDFs, it uses direct text extraction (fast). For scanned PDFs (image-only), it falls back to OCR with tesseract. It can also extract tables as structured rows and pull embedded images.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/pdf-extract/SKILL.md
```

## How to use

```
"Extract the text from report.pdf"
```

The agent:
1. Opens the PDF with pymupdf
2. Tries direct text extraction
3. If text is sparse (scanned PDF), falls back to OCR
4. Returns the extracted text

## What you get

| Output | Method | Notes |
|---|---|---|
| Text | pymupdf `get_text()` | Fast, works on text-based PDFs |
| Tables | pdfplumber `extract_tables()` | Bordered tables work best |
| Images | pymupdf `extract_image()` | Saves to disk |
| OCR text | tesseract via PIL | Fallback for scanned PDFs |

## Example

```
User: "Pull the tables out of financial_report.pdf"

Agent:
  1. Uses pdfplumber to extract tables
  2. Finds 3 tables across 5 pages
  3. Returns: [{"page": 2, "rows": [["Q1", "$1.2M"], ...]}, ...]
  4. Optionally exports to CSV
```
