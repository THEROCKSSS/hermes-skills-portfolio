# markdown-to-pdf

Convert markdown to a styled PDF with syntax highlighting, tables, and custom themes.

## What it does

The agent converts a markdown file to PDF using weasyprint, puppeteer, or pandoc. It applies CSS styling (default, dark, or print-friendly), renders code blocks with syntax highlighting, and handles tables, images, and blockquotes. You get a professional PDF from any markdown document.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/markdown-to-pdf/SKILL.md
```

## How to use

```
"Convert README.md to PDF"
```

The agent:
1. Reads the markdown
2. Renders to HTML with syntax highlighting
3. Applies CSS styling
4. Generates the PDF
5. Returns the file path

## Conversion methods

| Method | Language | Best for |
|---|---|---|
| weasyprint | Python | Pure Python, no browser needed |
| puppeteer | Node.js | Best rendering, handles CSS/JS |
| pandoc | System | Simplest, many format options |

## Example

```
User: "Convert my documentation to a dark-themed PDF"

Agent:
  1. Reads docs.md
  2. Applies DARK_CSS theme
  3. Runs: md_to_pdf("docs.md", "docs.pdf", css=DARK_CSS)
  4. Returns: "PDF saved to docs.pdf"
```
