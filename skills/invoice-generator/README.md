# invoice-generator

A public [Hermes](https://github.com/NousResearch/hermes) skill that turns
structured line items into a clean, professional **PDF invoice** — with client
details, itemized rows, tax, totals, and multi-currency support.

> "Agent + skill = the user gets a branded invoice PDF without touching a
> spreadsheet."

## Why

Invoicing is repetitive, error-prone, and easy to get wrong on tax and totals.
This skill standardizes the input, validates the math, and renders a
print-ready document every time.

## Install

Point Hermes at the skill file:

```
https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/invoice-generator/SKILL.md
```

Or copy the `invoice-generator/` folder into your Hermes skills directory.

The PDF engine uses [`fpdf2`](https://pypi.org/project/fpdf2/) (pure Python):

```bash
pip install fpdf2
```

## Usage

Tell the agent what you sold. Provide the details as a YAML block, or just
describe the job and let the agent assemble it:

```yaml
invoice:
  number: INV-2026-0042
  issue_date: 2026-07-20
  currency: USD
  tax_rate: 0.20
  sender:
    name: Monica Amano
    company: Amano Studio LLC
    email: billing@amano.studio
  client:
    name: Jordan Reeves
    company: Reeves & Co.
    email: accounts@reeves.co
  items:
    - description: "Brand identity design"
      quantity: 1
      unit_price: 2400.00
    - description: "Logo suite"
      quantity: 2
      unit_price: 350.00
```

The agent returns a saved `invoice.pdf` path.

## Features

- **Clean template** — header, From/Bill-To blocks, itemized table, totals.
- **Tax handling** — subtotal × rate, shown as its own line; exempt-aware.
- **Numbering** — explicit or auto `INV-<YYYY>-<seq>`.
- **Multi-currency** — ISO 4217 codes, correct symbols, JPY/KRW zero-decimal.
- **Safe math** — precise accumulation, rounding only at display.

## What it is not

Quotes/estimates, cash receipts, and timesheets without a billing step are
out of scope — adapt the title and status if you reuse it for those.

## License

MIT — free to use, fork, and ship in your own portfolio.

---

Part of the [hermes-skills-portfolio](https://github.com/THEROCKSSS/hermes-skills-portfolio)
by Monica Amano.
