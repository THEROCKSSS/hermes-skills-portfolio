# qr-code-generator

Generate QR codes for URLs, WiFi, contact info, and any text — as PNG or SVG.

## What it does

The agent creates QR codes from any data: URLs, WiFi credentials, vCards, or plain text. Customizable colors, size, error correction, and optional logo overlay. Output as PNG for images or SVG for scalable print.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/qr-code-generator/SKILL.md
```

## How to use

```
"Make a QR code for https://example.com"
```

The agent generates a PNG QR code and returns the file path.

## QR types

| Type | Example |
|---|---|
| URL | `make_qr("https://example.com")` |
| WiFi | `wifi_qr(ssid="MyNet", password="pass123")` |
| vCard | `vcard_qr(name="Jane", phone="+1234", email="jane@x.com")` |
| Text | `make_qr("Any text content")` |

## Example

```
User: "Create a WiFi QR for my guest network"

Agent:
  1. Generates: WIFI:T:WPA;S:GuestNet;P:welcome2026;;
  2. Creates wifi_qr.png
  3. Returns: "Scan wifi_qr.png to auto-connect to GuestNet"
```
