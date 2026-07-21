# resume-builder

> A Hermes skill that turns structured career data into a professional,
> print-ready resume — HTML and PDF, no design work required.

**Category:** utility · **Tier:** featured · **Version:** 1.0.0

---

## What it does

Give the agent your work history, education, skills, and contact details as
structured YAML or JSON. `resume-builder` renders a clean, ATS-friendly resume
in three visual styles and exports it to PDF with a single command.

No copy-pasting into Word. No fighting with margins. You describe the facts; the
skill handles the typography, pagination, and print fidelity.

## Templates

| Template  | Look                                    | Best for                  |
|-----------|-----------------------------------------|---------------------------|
| `minimal` | Single column, hairline rules, calm     | Engineering, design       |
| `modern`  | Accent header band, two-tone palette    | General-purpose default   |
| `classic` | Serif body, ruled headers, traditional  | Finance, law, academia    |

## Quick start

```yaml
# resume.yaml
basics:
  name: "Owen"
  label: "Senior Software Engineer"
  email: "monica@example.com"
  summary: "Engineer focused on distributed systems."
sections:
  work:
    - company: "Acme Corp"
      position: "Staff Engineer"
      start: "2021-03"
      end: "2024-06"
      highlights:
        - "Led a billing-service migration to event-driven architecture."
  education:
    - institution: "TU Berlin"
      area: "Computer Science"
      degree: "M.Sc."
      end: "2018"
  skills: ["Go", "Kubernetes", "Distributed Systems"]
```

Render and export:

```bash
# HTML (agent writes resume.html)
# PDF via WeasyPrint (no browser needed):
pip install weasyprint && weasyprint resume.html resume.pdf

# or PDF via Puppeteer (pixel-accurate):
npm install puppeteer && node export-pdf.js
```

## Why it's reliable

- **Print-safe by default** — background colors and rules survive to PDF via
  `printBackground: true` / `print-color-adjust: exact`.
- **ATS-friendly** — real text, predictable section order, no image-bound text.
- **Portable** — single self-contained HTML file, system font stacks, no
  external requests.
- **Customizable** — recolor and re-space through CSS custom properties; switch
  page size (A4 / Letter) with one `@page` rule.

## Install

Install this skill into Hermes from the public portfolio:

```
https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/resume-builder/SKILL.md
```

Then ask Hermes: *"Build my resume from resume.yaml using the modern template
and export a PDF."*

## License

MIT — use it, fork it, ship your own portfolio version.
