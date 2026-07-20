---
name: markdown-to-pdf
description: "Convert markdown to PDF with styling — agent + this skill = user gets a styled PDF from any markdown file."
version: 1.0.0
---

# markdown-to-pdf

Convert markdown files to PDF with customizable styling. The agent handles markdown parsing, CSS styling, and PDF generation with options for themes, page size, and syntax highlighting.

## When to Use

- The user wants to convert a markdown document to PDF.
- The user wants a styled PDF report from markdown.
- The user says "convert this to PDF", "make a PDF from markdown", or "export as PDF".

## Prerequisites

```bash
# Option 1: weasyprint (recommended, pure Python)
pip install weasyprint markdown

# Option 2: puppeteer (Node.js, better rendering)
npm install puppeteer markdown-it

# Option 3: pandoc (system package)
# Linux: apt install pandoc
# macOS: brew install pandoc
```

## Using weasyprint (Python)

```python
import markdown
from weasyprint import HTML

def md_to_pdf(md_path: str, pdf_path: str, css: str = ""):
    """Convert markdown to PDF with optional CSS styling."""
    with open(md_path, 'r') as f:
        md_content = f.read()

    html_body = markdown.markdown(md_content, extensions=['codehilite', 'tables', 'fenced_code'])

    default_css = """
    body { font-family: 'Inter', sans-serif; max-width: 800px; margin: 40px auto; line-height: 1.6; color: #333; }
    h1 { font-size: 2em; border-bottom: 2px solid #eee; padding-bottom: 0.3em; }
    h2 { font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }
    code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: 'Fira Code', monospace; font-size: 0.9em; }
    pre { background: #f8f8f8; padding: 16px; border-radius: 5px; overflow-x: auto; }
    pre code { background: none; padding: 0; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
    th { background: #f4f4f4; font-weight: bold; }
    blockquote { border-left: 4px solid #ddd; margin-left: 0; padding-left: 16px; color: #666; }
    """

    html = f"""
    <html><head><style>{css or default_css}</style></head>
    <body>{html_body}</body></html>
    """

    HTML(string=html).write_pdf(pdf_path)
    return pdf_path
```

## Using pandoc (simplest)

```bash
# Basic conversion
pandoc input.md -o output.pdf

# With a template and table of contents
pandoc input.md -o output.pdf --toc --template=eisvogel

# With syntax highlighting
pandoc input.md -o output.pdf --highlight-style=tango
```

## Using puppeteer (best rendering)

```javascript
const markdownIt = require('markdown-it');
const puppeteer = require('puppeteer');
const fs = require('fs');

async function mdToPdf(mdPath, pdfPath) {
    const md = fs.readFileSync(mdPath, 'utf-8');
    const htmlBody = markdownIt({ html: true, highlight: true }).render(md);

    const html = `
    <html><head>
    <style>
        body { font-family: system-ui; max-width: 800px; margin: 40px auto; padding: 20px; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
        pre { background: #f8f8f8; padding: 16px; border-radius: 5px; overflow-x: auto; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; }
    </style>
    </head><body>${htmlBody}</body></html>
    `;

    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.setContent(html, { waitUntil: 'networkidle0' });
    await page.pdf({ path: pdfPath, format: 'A4', margin: { top: '1in', bottom: '1in' } });
    await browser.close();
    return pdfPath;
}
```

## Custom Themes

### Dark theme

```python
DARK_CSS = """
body { background: #1a1a2e; color: #e0e0e0; font-family: 'Inter', sans-serif; max-width: 800px; margin: 40px auto; }
h1, h2, h3 { color: #fff; border-bottom-color: #333; }
code { background: #16213e; color: #e94560; }
pre { background: #16213e; border: 1px solid #333; }
a { color: #e94560; }
table th { background: #16213e; }
table th, table td { border-color: #333; }
"""
```

### Print-friendly

```python
PRINT_CSS = """
body { font-family: 'Georgia', serif; max-width: none; margin: 0; font-size: 12pt; line-height: 1.5; }
h1 { font-size: 20pt; page-break-before: always; }
h1:first-of-type { page-break-before: avoid; }
h2 { font-size: 16pt; }
pre, code { font-family: 'Courier New', monospace; font-size: 10pt; }
table { font-size: 10pt; }
@page { margin: 1in; }
"""
```

## Workflow

1. Read the markdown file
2. Choose the conversion method (weasyprint for Python, puppeteer for best rendering, pandoc for simplicity)
3. Apply CSS styling (default, dark, or print-friendly)
4. Generate the PDF
5. Return the file path

## Pitfalls

- **Missing system dependencies** — weasyprint needs cairo, pango, and gdk-pixbuf system libraries. On Ubuntu: `apt install libpango-1.0-0 libpangoft2-1.0-0`. On macOS: `brew install pango`.
- **Code blocks not highlighted** — Without the `codehilite` extension (Python) or a highlight.js include (JS), code blocks are plain text. Install `pygments` for Python highlighting.
- **Images not rendering** — Local image paths must be absolute or relative to the HTML file. Use `file://` URLs or embed images as base64.
- **Page breaks in bad places** — Use CSS `page-break-before: always` on h1 elements to force chapter breaks. Add `page-break-inside: avoid` on tables and code blocks.
- **Emoji rendering** — weasyprint may not render emoji. Install a color emoji font (Noto Color Emoji) or replace emoji with text.
- **Large PDFs** — PDFs with many images can be large. Optimize images before embedding (resize to max 1000px width, use JPEG for photos).
