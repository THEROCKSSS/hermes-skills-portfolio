# ocr-documents

Extract text from images, screenshots, and scanned documents using OCR.

## What it does

The agent runs OCR (Tesseract or EasyOCR) on an image or scanned document and returns the extracted text. For poor-quality images, it preprocesses first (grayscale, contrast enhancement, upscaling) to improve accuracy. For multi-language documents, it loads the appropriate language packs.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/ocr-documents/SKILL.md
```

## How to use

```
"Extract the text from this screenshot"
```

The agent:
1. Opens the image
2. Preprocesses if needed (grayscale, contrast, upscale)
3. Runs Tesseract OCR
4. Returns the text

## Prerequisites

- Tesseract OCR installed (system package)
- Python: `pip install pytesseract pillow`

## Example

```
User: "Read the text in this receipt photo"

Agent:
  1. Opens receipt.jpg (800px wide, low contrast)
  2. Preprocesses: grayscale + contrast x2 + upscale to 1000px
  3. Runs: pytesseract.image_to_string(img)
  4. Returns: "Coffee Shop\nLatte      $4.50\nMuffin     $3.25\nTotal      $7.75"
```
