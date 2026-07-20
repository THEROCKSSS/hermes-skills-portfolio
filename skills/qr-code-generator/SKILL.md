---
name: qr-code-generator
description: "Generate QR codes for URLs, text, WiFi, and more — agent + this skill = user gets a scannable QR code for any content."
version: 1.0.0
---

# qr-code-generator

Generate QR codes as PNG or SVG images. The agent creates QR codes for URLs, plain text, WiFi credentials, vCards, and custom content with customizable size, color, and error correction.

## When to Use

- The user wants a QR code for a URL.
- The user wants to share WiFi credentials via QR.
- The user wants a QR code for contact info (vCard).
- The user says "make a QR code", "generate a QR", or "create a scannable code".

## Prerequisites

```bash
pip install qrcode[pil]
```

## Basic QR Code

```python
import qrcode

def make_qr(data: str, output: str = "qr.png", size: int = 10, border: int = 4):
    """Generate a QR code PNG from any string data."""
    qr = qrcode.QRCode(
        version=None,  # auto-detect minimum size
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output)
    return output
```

## Custom Colors

```python
def make_colored_qr(data: str, output: str, fill: str = "#1a1a2e", back: str = "#ffffff"):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill, back_color=back)
    img.save(output)
    return output
```

## SVG Output

```python
import qrcode.svg

def make_svg_qr(data: str, output: str = "qr.svg"):
    factory = qrcode.svg.SvgPathImage
    qr = qrcode.QRCode(image_factory=factory)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image()
    img.save(output)
    return output
```

## WiFi QR Code

```python
def wifi_qr(ssid: str, password: str, security: str = "WPA", hidden: bool = False, output: str = "wifi.png"):
    """Generate a QR code that auto-configures WiFi on phones."""
    data = f"WIFI:T:{security};S:{ssid};P:{password};H:{'true' if hidden else 'false'};;"
    return make_qr(data, output)
```

## vCard QR Code

```python
def vcard_qr(name: str, phone: str, email: str, org: str = "", output: str = "contact.png"):
    """Generate a QR code with contact info."""
    data = f"BEGIN:VCARD\nVERSION:3.0\nFN:{name}\nTEL:{phone}\nEMAIL:{email}\nORG:{org}\nEND:VCARD"
    return make_qr(data, output)
```

## URL QR Code

```python
def url_qr(url: str, output: str = "url.png"):
    """Generate a QR code for a URL."""
    return make_qr(url, output)
```

## Error Correction Levels

| Level | Recovery | Use case |
|---|---|---|
| L | 7% | High-density, clean environment |
| M | 15% | Default, general use |
| Q | 25% | Some risk of damage |
| H | 30% | Logos overlay, dirty environments |

```python
# High error correction (allows logo overlay in center)
qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
```

## With Logo Overlay

```python
from PIL import Image

def qr_with_logo(data: str, logo_path: str, output: str = "qr_logo.png"):
    """Generate a QR code with a logo in the center."""
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    logo = Image.open(logo_path).convert("RGBA")
    # Scale logo to ~20% of QR size
    qr_size = qr_img.size[0]
    logo_size = int(qr_size * 0.2)
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

    pos = ((qr_size - logo_size) // 2, (qr_size - logo_size) // 2)
    qr_img.paste(logo, pos, logo)
    qr_img.save(output)
    return output
```

## Workflow

1. Determine the content type (URL, text, WiFi, vCard)
2. Choose format (PNG for images, SVG for print/web)
3. Pick error correction level (M default, H for logos)
4. Generate the QR code
5. Return the file path

## Pitfalls

- **Too much data** — QR codes have capacity limits. A v1 QR holds 17 alphanumeric chars; v40 holds 4,296. Long URLs produce large, dense codes that are hard to scan. Use a URL shortener first.
- **Dark on dark** — QR codes need high contrast. Dark fill on dark background won't scan. Always use dark fill on light background.
- **Logo too large** — A logo covering more than 30% of the QR code will make it unscannable. Keep logos to 20% max and use error correction H.
- **PNG vs SVG** — PNG is for screen and print at fixed size. SVG is scalable (good for large prints). Use SVG for billboards or large displays.
- **WiFi QR format** — The format must be exactly `WIFI:T:WPA;S:SSID;P:PASSWORD;;` — note the double semicolon at the end. Missing it breaks the QR.
- **Special characters** — Escape semicolons and colons in WiFi SSIDs/passwords: `\\:` and `\\;`.
