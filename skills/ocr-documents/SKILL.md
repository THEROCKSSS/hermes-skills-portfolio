---
name: ocr-documents
description: "Extract text from images and scanned documents using OCR — agent + this skill = user gets editable text from any image or scan."
version: 1.0.0
---

# ocr-documents

Extract text from images, screenshots, and scanned documents using Tesseract OCR and EasyOCR. The agent handles image preprocessing, OCR execution, and text cleanup.

## When to Use

- The user has a screenshot or image containing text they want to extract.
- The user has a scanned document that needs to be converted to editable text.
- The user says "read the text in this image", "OCR this scan", or "extract text from screenshot".

## Prerequisites

```bash
# Tesseract (recommended for most use cases)
pip install pytesseract pillow
# System package:
# Linux: apt install tesseract-ocr
# macOS: brew install tesseract
# Windows: https://github.com/UB-Mannheim/tesseract/wiki

# EasyOCR (alternative, better for handwriting/complex layouts)
pip install easyocr
```

## Basic OCR

### Tesseract (fast, reliable for printed text)

```python
import pytesseract
from PIL import Image

def ocr_image(image_path: str, lang: str = "eng") -> str:
    img = Image.open(image_path)
    return pytesseract.image_to_string(img, lang=lang)
```

### EasyOCR (better for complex layouts, handwriting)

```python
import easyocr

reader = easyocr.Reader(['en'])

def ocr_image_easyocr(image_path: str) -> str:
    results = reader.readtext(image_path)
    return "\n".join([r[1] for r in results])
```

## Image Preprocessing

OCR accuracy depends heavily on image quality. Preprocess for better results:

```python
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

def ocr_with_preprocessing(image_path: str) -> str:
    img = Image.open(image_path)

    # Convert to grayscale
    img = img.convert('L')

    # Increase contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)

    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)

    # Upscale small images
    if img.width < 1000:
        ratio = 1000 / img.width
        img = img.resize((int(img.width * ratio), int(img.height * ratio)))

    return pytesseract.image_to_string(img)
```

## OCR with Bounding Boxes

```python
import pytesseract
from PIL import Image, ImageDraw

def ocr_with_boxes(image_path: str, output_path: str = "annotated.png"):
    img = Image.open(image_path)
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    draw = ImageDraw.Draw(img)
    for i in range(len(data["text"])):
        if int(data["conf"][i]) > 60:  # confidence threshold
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            draw.rectangle([x, y, x + w, y + h], outline="red", width=2)

    img.save(output_path)
    return [data["text"][i] for i in range(len(data["text"])) if int(data["conf"][i]) > 60]
```

## PDF Page OCR

```python
import fitz  # pymupdf
import pytesseract
from PIL import Image
import io

def ocr_pdf_page(pdf_path: str, page_num: int = 0, dpi: int = 300) -> str:
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    pix = page.get_pixmap(dpi=dpi)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    return pytesseract.image_to_string(img)
```

## Multi-language OCR

```python
# Install language packs:
# Linux: apt install tesseract-ocr-fra tesseract-ocr-deu tesseract-ocr-spa
# Then:
text = pytesseract.image_to_string(img, lang='eng+fra+deu')
```

## Workflow

1. Identify the image or document to OCR
2. Check image quality — if low resolution or poor contrast, preprocess
3. Run Tesseract for printed text, EasyOCR for handwriting/complex layouts
4. Clean up the output (remove stray characters, fix common OCR errors)
5. Return the extracted text

## Common OCR Errors and Fixes

| Error | Cause | Fix |
|---|---|---|
| Empty output | Image too small | Upscale to 1000px+ width |
| Garbled text | Low contrast | Convert to grayscale + enhance contrast |
| Missing text | Dark background | Invert colors: `ImageOps.invert(img)` |
| Wrong characters | Similar-looking chars (0/O, 1/l) | Post-process with regex replacements |
| Slow processing | High DPI | Use 300 DPI (sufficient for most text) |

## Pitfalls

- **Tesseract path not found** — On Windows, set the tesseract path: `pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'`
- **Handwriting recognition** — Tesseract is poor at handwriting. Use EasyOCR or TrOCR for handwritten text.
- **Rotated text** — Tesseract expects horizontal text. Detect and rotate first: `pytesseract.image_to_osd(img)` returns rotation angle.
- **Multi-column layouts** — Tesseract reads left-to-right, top-to-bottom. Multi-column documents get jumbled. Use `image_to_data` with bounding boxes and sort by column.
- **Low confidence results** — Filter by confidence score. `image_to_data` returns confidence per word. Anything below 50 is unreliable.
- **Large images** — Images over 5000px take significant time. Resize to 2000-3000px width before OCR.
