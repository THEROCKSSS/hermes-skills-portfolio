---
name: resume-builder
description: Generate a professional, print-ready resume in HTML and PDF from structured YAML/JSON data. Use when a user wants to turn their CV, work history, skills, and education into a polished single-page or multi-page resume with selectable templates and reliable PDF export.
version: 1.0.0
---

# resume-builder

Turn structured career data into a clean, professional resume rendered as HTML
and exported to PDF. The skill owns the data model, three visual templates, and
two PDF backends so the agent produces a consistent artifact regardless of the
user's environment.

## When to Use

- The user supplies (or asks the agent to draft) a resume from facts: jobs,
  education, skills, projects, certifications, contact info.
- The user has a YAML/JSON resume and wants a styled HTML page or a PDF.
- The user wants to re-theme an existing resume (minimal / modern / classic)
  without re-typing content.
- The user needs a portable, ATS-friendly document for job applications.

Do **not** use this skill for:
- Cover letters (single narrative prose) — that is a different artifact.
- Full CVs with publications/grants requiring a two-column academic layout
  (the classic template can approximate it, but flag the limitation).
- Free-form un-structured prompts with no data — first collect data (see
  Input Format), then render.

## Input Format

The skill consumes one structured document. Prefer YAML for hand-authoring;
accept JSON interchangeably. The canonical schema:

```yaml
basics:
  name: "Monica Amano"
  label: "Senior Software Engineer"
  email: "monica@example.com"
  phone: "+1 555 0100"
  url: "https://monica.example.com"
  location: "Berlin, Germany"
  summary: "Engineer focused on distributed systems and developer tooling."
sections:
  work:
    - company: "Acme Corp"
      position: "Staff Engineer"
      start: "2021-03"
      end: "2024-06"
      location: "Remote"
      highlights:
        - "Led migration of the billing service to event-driven architecture."
        - "Cut p99 latency 40% by introducing a read-through cache."
  education:
    - institution: "TU Berlin"
      area: "Computer Science"
      degree: "M.Sc."
      start: "2016"
      end: "2018"
  skills:
    - "Go"
    - "Kubernetes"
    - "Distributed Systems"
  projects:
    - name: "openmetrics-cli"
      description: "A tiny Prometheus exporter toolkit."
      url: "https://github.com/monica/openmetrics-cli"
  certifications:
    - name: "CKA"
      issuer: "CNCF"
      date: "2022"
```

Rules the agent must enforce:
- `basics.name` and at least one `sections.work` or `sections.education` entry
  are required; everything else is optional and omitted if absent.
- Dates use ISO `YYYY` or `YYYY-MM`. Render ranges as `2021-03 – 2024-06`;
  an open-ended role uses `Present` for a missing `end`.
- `highlights` are bullet points; keep each to one line, action-verb led.
- Unknown top-level keys are ignored, not erroring.

## Template Options

Three bundled, dependency-light CSS templates. The agent picks based on the
user's stated preference or defaults to `modern`.

- **minimal** — single column, generous whitespace, hairline rules, neutral
  sans-serif. Best for engineering and design roles; fastest to scan.
- **modern** — accent color header band, two-tone palette, subtle typographic
  scale. Good general-purpose default.
- **classic** — serif body, ruled section headers, traditional chronology.
  Best for finance, law, academia-adjacent roles.

Each template is a self-contained `<style>` block plus semantic HTML, so the
rendered page works offline and prints predictably. The agent sets the accent
color and font stack via CSS custom properties (see Customization).

## PDF Generation

Two backends; pick whichever the user's machine can run.

### weasyprint (recommended, headless-friendly)
```bash
pip install weasyprint
weasyprint resume.html resume.pdf
```
WeasyPrint renders HTML/CSS directly — no browser needed. It honors `@page`
size, margins, and `print-color-adjust: exact`, so colors survive to PDF.
Best when Chromium is unavailable.

### puppeteer (best fidelity to screen CSS)
```bash
npm install puppeteer
node -e "const p=require('puppeteer');(async()=>{const b=await p.launch();const pg=await b.newPage();await pg.goto('file://'+process.cwd()+'/resume.html',{waitUntil:'networkidle0'});await pg.pdf({path:'resume.pdf',format:'A4',printBackground:true});await b.close();})()"
```
Puppeteer gives pixel-accurate output and supports web fonts. Slower to install
and needs a Chromium download. Use when the user already has Node tooling.

Always generate the PDF from the final HTML with `printBackground: true`
(puppeteer) or `print-color-adjust: exact` (weasyprint) so the template's
background colors and rules appear.

## HTML Output

The agent writes a single `resume.html`:
- One root `<article class="resume template-<name>">`.
- `lang` attribute set from `basics` locale or default `en`.
- Inline `<style>` in `<head>`; no external requests (fonts fall back to
  system stacks) so the file is portable.
- Contact links use `mailto:`/`tel:` and `rel="noopener"` on external `url`.
- Section order: summary → work → education → projects → skills → certifications.
  Sections with no data are dropped; the order is fixed for ATS consistency.

## Customization

Drive appearance through CSS custom properties at `:root` so users restyle
without touching markup:

```css
:root{
  --accent:#2563eb;
  --ink:#111827;
  --paper:#ffffff;
  --font-sans: "Inter", system-ui, sans-serif;
  --font-serif: "Georgia", serif;
  --space: 0.75rem;
}
```

- Recolor: set `--accent`. For classic, also set `--font-body: var(--font-serif)`.
- Page size: override `@page { size: A4; margin: 14mm; }` (Letter for US users).
- Multi-page: templates are fluid; long resumes paginate automatically. Add
  `break-inside: avoid` on `.entry` to keep a role's block together.
- One-page coercion: if the user demands one page, shrink `--space` and font
  sizes, trim `summary`, and cap `highlights` to 3–4 per role rather than
  dropping sections.

## Pitfalls

- **Missing `end` date** → render `Present`, never leave a blank range.
- **WeasyPrint missing system libs** (Pango/cairo) on minimal Linux images →
  install `libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0` first, or
  fall back to puppeteer.
- **Fonts not embedded in PDF** → use system font stacks; web fonts loaded via
  `<link>` may not print. Inline `@font-face` only if the user supplies files.
- **Print background stripped** → without `printBackground:true` /
  `print-color-adjust:exact`, accent bands disappear. This is the #1 "my PDF
  looks blank" bug.
- **ATS parsing** → keep real text (no text-in-images, no columns-splitting
  names). The minimal/modern templates are ATS-safe; heavy two-column sidebars
  can confuse parsers.
- **Non-ISO dates** → normalize `Mar 2021` → `2021-03` before rendering.
- **Long URLs in `highlights`** → wrap or shorten; raw URLs break line layout.
- **Over-styling for one page** → don't shrink below 9pt; prefer content edits.
