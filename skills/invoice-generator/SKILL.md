---
name: invoice-generator
description: Generate professional PDF invoices from structured line items. Use when a user wants a clean, branded invoice (client details, itemized line items, tax, totals, currency) produced as a downloadable PDF.
version: 1.0.0
---

# invoice-generator

Turn structured line items into a polished, print-ready PDF invoice. The agent
collects client and item details, validates the math, and renders a professional
document the user can send to a customer or file for accounting.

## When to Use

- A user asks to "make an invoice", "bill my client", or "generate an invoice PDF".
- A user provides services/products sold and wants a formal document with totals.
- A user needs recurring or one-off invoices with consistent branding.
- A user wants tax (VAT/GST/sales tax) applied and shown as its own line.
- A user works across currencies and needs symbols + formatting handled correctly.

Do **not** use this skill for: quotes/estimates (no tax committed yet — still fine
to adapt, but name it clearly), receipts for already-paid cash sales, or timesheets
without a billing step. For those, adjust the document title and clarify status.

## Input Format

Collect the invoice as a single YAML block. Keep field names stable so the
generator script can parse them without guessing.

```yaml
invoice:
  number: INV-2026-0042
  issue_date: 2026-07-20
  due_date: 2026-08-19
  currency: USD
  tax_rate: 0.20          # 20% VAT/GST; 0 if tax-exempt
  notes: "Payment due within 30 days. Bank transfer preferred."
  sender:
    name: Monica Amano
    company: Amano Studio LLC
    email: billing@amano.studio
    address: "12 Birch Lane, Suite 4\nPortland, OR 97201"
    tax_id: "US-EIN 84-1234567"
  client:
    name: Jordan Reeves
    company: Reeves & Co.
    email: accounts@reeves.co
    address: "88 Market Street\nLondon EC2M 1AP, UK"
  items:
    - description: "Brand identity design"
      quantity: 1
      unit_price: 2400.00
    - description: "Logo suite (primary + secondary)"
      quantity: 2
      unit_price: 350.00
    - description: "Business card layout"
      quantity: 3
      unit_price: 90.00
```

### Field rules

- `currency`: ISO 4217 code (`USD`, `EUR`, `GBP`, `JPY`, ...). Drives the symbol.
- `tax_rate`: decimal fraction (0.20 = 20%). Multiply after subtotal.
- `quantity` × `unit_price` = line total. All money values are decimals.
- `address` may contain `\n` for line breaks.
- Missing `due_date` → default to `issue_date` + 30 days.
- Missing `number` → fall back to `INV-<YYYY>-<seq>` (see Numbering).

## Template

A clean, professional invoice has a clear visual hierarchy:

1. **Header row** — Sender name/logo on the left, "INVOICE" title + number on the right.
2. **Party block** — "From" (sender) and "Bill To" (client) side by side.
3. **Meta row** — Issue date, due date, currency, tax ID.
4. **Line-item table** — columns: Description | Qty | Unit Price | Line Total.
5. **Totals block** — Subtotal, Tax, **Total Due** (right-aligned, emphasized).
6. **Footer** — notes, payment terms, thank-you line.

Design cues that read as "professional":
- One accent color (deep navy or slate), generous whitespace, 10–11pt body text.
- Right-align all numeric columns; use thousands separators.
- Bold the Total Due and separate it with a thin rule.
- Avoid clip-art, gradients, and decorative fonts.

## PDF Generation

Use `fpdf2` (pure Python, no system libraries) so the skill runs anywhere Python does.

Install once:

```bash
pip install fpdf2
```

Minimal generation function (embed/call this from the agent's runtime):

```python
from fpdf import FPDF
from datetime import date, timedelta

SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CAD": "C$", "AUD": "A$"}

def money(value, currency):
    sym = SYMBOLS.get(currency, f"{currency} ")
    # JPY has no decimal places by convention
    dec = 0 if currency == "JPY" else 2
    return f"{sym}{value:,.{dec}f}"

def build_invoice(data, out_path="invoice.pdf"):
    inv = data["invoice"]
    cur = inv.get("currency", "USD")
    tax_rate = float(inv.get("tax_rate", 0) or 0)
    items = inv.get("items", [])

    subtotal = sum(float(i["quantity"]) * float(i["unit_price"]) for i in items)
    tax = subtotal * tax_rate
    total = subtotal + tax

    pdf = FPDF(format="A4", unit="mm")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(15, 15, 15)

    # Header
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 10, inv["sender"]["name"], ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, inv["sender"].get("company", ""), ln=True)
    pdf.ln(2)

    pdf.set_xy(140, 15)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "INVOICE", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(140)
    pdf.cell(0, 6, f"Number: {inv.get('number', 'N/A')}", ln=True)
    pdf.set_x(140)
    pdf.cell(0, 6, f"Issue: {inv.get('issue_date', date.today().isoformat())}", ln=True)

    pdf.ln(6)

    # Parties
    y = pdf.get_y()
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(90, 6, "From", ln=0)
    pdf.cell(90, 6, "Bill To", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for key in ("name", "company", "email", "address"):
        s = str(inv["sender"].get(key, "")).replace("\n", "  |  ")
        c = str(inv["client"].get(key, "")).replace("\n", "  |  ")
        pdf.cell(90, 6, s[:48], ln=0)
        pdf.cell(90, 6, c[:48], ln=True)

    pdf.ln(4)

    # Items table
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(230, 232, 240)
    pdf.cell(100, 8, "Description", border=1, fill=True)
    pdf.cell(20, 8, "Qty", border=1, fill=True, align="R")
    pdf.cell(35, 8, "Unit Price", border=1, fill=True, align="R")
    pdf.cell(35, 8, "Total", border=1, fill=True, align="R", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for i in items:
        lt = float(i["quantity"]) * float(i["unit_price"])
        pdf.cell(100, 8, str(i["description"])[:60], border=1)
        pdf.cell(20, 8, str(i["quantity"]), border=1, align="R")
        pdf.cell(35, 8, money(float(i["unit_price"]), cur), border=1, align="R")
        pdf.cell(35, 8, money(lt, cur), border=1, align="R", ln=True)

    # Totals
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(155, 8, "Subtotal", align="R")
    pdf.cell(35, 8, money(subtotal, cur), align="R", ln=True)
    if tax_rate:
        pdf.cell(155, 8, f"Tax ({int(tax_rate*100)}%)", align="R")
        pdf.cell(35, 8, money(tax, cur), align="R", ln=True)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(155, 9, "Total Due", align="R")
    pdf.cell(35, 9, money(total, cur), align="R", ln=True)

    # Notes
    if inv.get("notes"):
        pdf.ln(6)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, inv["notes"])

    pdf.output(out_path)
    return out_path
```

The agent should:
1. Parse the YAML the user provided (or assemble it from a conversation).
2. Call `build_invoice(data, "invoice.pdf")`.
3. Return the saved PDF path to the user.

## Numbering

- Prefer an explicit `number` from the user (e.g. `INV-2026-0042`).
- If absent, generate `INV-<YYYY>-<seq>` where `<seq>` is a zero-padded sequence
  based on the year (start at 0001, increment per invoice).
- Keep numbers unique and sequential; do not reuse or skip ranges silently.
- For drafts, prefix with `DRAFT-` and strip it on finalization.

## Tax Calculation

- `tax = subtotal × tax_rate`. Apply **after** the subtotal, never per line, unless
  the jurisdiction requires line-level tax (then sum line taxes).
- Show tax as its own line with the rate in parentheses: `Tax (20%)`.
- `total = subtotal + tax`. Never round the subtotal before computing tax if the
  jurisdiction rounds tax on the gross — when in doubt, compute tax on the exact
  subtotal and round only the displayed value.
- Tax-exempt? Set `tax_rate: 0` and omit the tax line (or label it `Tax (0% — exempt)`).
- If the client is in another tax jurisdiction, surface that to the user before
  assuming a rate — reverse-charge rules may apply.

## Multi-currency

- Always store ISO 4217 codes. Map to display symbols via the `SYMBOLS` dict above;
  extend it as needed.
- **JPY, KRW** conventionally show **no decimals** — handle `dec = 0`.
- Format with thousands separators (`1,234.56`) and right-align in tables.
- If the invoice is in a non-sender currency, note the exchange basis in `notes`
  (e.g. "Converted at 1 EUR = 1.08 USD on 2026-07-20").
- Never mix currencies within one invoice; convert first, then bill in one currency.

## Pitfalls

- **Float rounding**: money math in floats is fine for display, but round only at
  presentation. Accumulate subtotal as a precise sum.
- **Missing client address** breaks the layout — default to the email if address
  is absent, and warn the user.
- **Long descriptions** overflow the cell — truncate to ~60 chars or use
  `multi_cell` for wrapping.
- **Page breaks**: set `auto_page_break` (done above) so long item lists don't clip.
- **Special characters** (€, é, &) — `fpdf2` core fonts are latin-1; for full
  Unicode, add a TTF font via `pdf.add_font(...)` or sanitize to ASCII.
- **Date formats**: store ISO `YYYY-MM-DD`; format for display per locale only at
  render time, never in the source data.
- **Duplicate numbers**: check before assigning a generated number.
- **Not saved where the user expects**: return the absolute output path and confirm
  the filename so the user can find the PDF.

## Install / Source

Public portfolio (Monica Amano):
https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/invoice-generator/SKILL.md
