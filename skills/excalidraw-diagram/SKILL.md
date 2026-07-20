---
name: excalidraw-diagram
description: "Generate hand-drawn style diagrams as Excalidraw JSON — agent + this skill = user gets architecture and flow diagrams that look hand-drawn."
version: 1.0.0
---

# excalidraw-diagram

Generate Excalidraw-compatible JSON diagrams in a hand-drawn style. The agent creates architecture diagrams, flow charts, sequence diagrams, and mind maps as Excalidraw files that can be opened in the Excalidraw editor or exported as PNG/SVG.

## When to Use

- The user wants a diagram for documentation or a presentation.
- The user wants a hand-drawn style diagram (not polished/corporate).
- The user wants an architecture, flow, or sequence diagram.
- The user says "draw a diagram", "make an architecture diagram", or "visualize this flow".

## Excalidraw JSON Format

Excalidraw files are JSON with an `elements` array. Each element is a shape (rectangle, ellipse, arrow, line, text).

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "hermes",
  "elements": [
    {
      "type": "rectangle",
      "x": 100, "y": 100,
      "width": 200, "height": 80,
      "strokeColor": "#1e88e5",
      "backgroundColor": "transparent",
      "fillStyle": "hachure",
      "strokeWidth": 2,
      "roughness": 1,
      "id": "rect-1"
    },
    {
      "type": "text",
      "x": 120, "y": 130,
      "text": "API Server",
      "fontSize": 20,
      "fontFamily": 1,
      "id": "text-1"
    }
  ],
  "appState": { "viewBackgroundColor": "#ffffff" }
}
```

## Helper Functions

### Rectangle with label

```python
import json, uuid

def box(x, y, w, h, label, color="#1e88e5"):
    """Create a labeled rectangle element."""
    rect_id = str(uuid.uuid4())
    text_id = str(uuid.uuid4())
    return [
        {
            "type": "rectangle", "x": x, "y": y, "width": w, "height": h,
            "strokeColor": color, "backgroundColor": "transparent",
            "fillStyle": "hachure", "strokeWidth": 2, "roughness": 1,
            "id": rect_id, "seed": 1
        },
        {
            "type": "text", "x": x + 10, "y": y + h/2 - 10,
            "text": label, "fontSize": 20, "fontFamily": 1,
            "textAlign": "center", "id": text_id, "seed": 2
        }
    ]

def arrow(x1, y1, x2, y2, label="", color="#1e88e5"):
    """Create an arrow element between two points."""
    elements = [{
        "type": "arrow", "x": x1, "y": y1,
        "width": x2 - x1, "height": y2 - y1,
        "points": [[0, 0], [x2 - x1, y2 - y1]],
        "strokeColor": color, "strokeWidth": 2, "roughness": 1,
        "id": str(uuid.uuid4()), "seed": 3
    }]
    if label:
        elements.append({
            "type": "text",
            "x": (x1 + x2) / 2, "y": (y1 + y2) / 2 - 15,
            "text": label, "fontSize": 16, "fontFamily": 1,
            "id": str(uuid.uuid4()), "seed": 4
        })
    return elements

def circle(x, y, r, label, color="#e91e63"):
    """Create a labeled circle."""
    return [
        {"type": "ellipse", "x": x, "y": y, "width": r*2, "height": r*2,
         "strokeColor": color, "backgroundColor": "transparent",
         "fillStyle": "hachure", "strokeWidth": 2, "roughness": 1,
         "id": str(uuid.uuid4()), "seed": 5},
        {"type": "text", "x": x + r - len(label)*5, "y": y + r - 10,
         "text": label, "fontSize": 18, "fontFamily": 1,
         "id": str(uuid.uuid4()), "seed": 6}
    ]

def build_diagram(elements_list, filepath="diagram.excalidraw"):
    """Assemble elements into an Excalidraw file."""
    elements = []
    for el_list in elements_list:
        elements.extend(el_list)
    diagram = {
        "type": "excalidraw", "version": 2, "source": "hermes",
        "elements": elements,
        "appState": {"viewBackgroundColor": "#ffffff"}
    }
    with open(filepath, "w") as f:
        json.dump(diagram, f, indent=2)
    return filepath
```

## Architecture Diagram Example

```python
# Client → API → Database
elements = [
    box(100, 100, 200, 80, "Web Client"),
    box(400, 100, 200, 80, "API Server"),
    box(700, 100, 200, 80, "PostgreSQL"),
    arrow(300, 140, 400, 140, "HTTP"),
    arrow(600, 140, 700, 140, "SQL"),
]

build_diagram(elements, "architecture.excalidraw")
```

## Flow Chart Example

```python
# Start → Decision → (Yes: Action, No: End)
elements = [
    circle(200, 50, 40, "Start"),
    box(150, 150, 200, 80, "Process Data"),
    box(150, 300, 200, 80, "Valid?"),
    box(400, 300, 200, 80, "Save Result"),
    circle(200, 450, 40, "End"),
    arrow(200, 90, 200, 150, ""),
    arrow(200, 230, 200, 300, ""),
    arrow(350, 340, 400, 340, "Yes"),
    arrow(200, 380, 200, 450, "No"),
    arrow(500, 300, 500, 200, ""),  # loop back
]

build_diagram(elements, "flowchart.excalidraw")
```

## Opening the Diagram

- Open `https://excalidraw.com` in a browser
- File → Open → select the `.excalidraw` file
- Or drag and drop the file onto the Excalidraw window

## Pitfalls

- **Coordinate system** — Excalidraw uses a top-left origin, y increases downward. Plan your layout before generating elements.
- **Text positioning** — Text elements need manual x/y positioning. Center text by offsetting from the box: `x + width/2 - len(label) * fontSize/4`.
- **Arrow endpoints** — Arrows use `points` relative to the start position `x, y`. `points: [[0, 0], [dx, dy]]` draws from (x, y) to (x+dx, y+dy).
- **Roughness** — `roughness: 0` = clean, `roughness: 1` = hand-drawn, `roughness: 2.5` = very sketchy. Default to 1 for the hand-drawn aesthetic.
- **Font family** — `1` = Virgil (hand-drawn), `2` = Helvetica, `3` = Cascadia (mono). Use 1 for the Excalidraw look.
- **File size** — Large diagrams with many elements produce large JSON. Keep diagrams to under 50 elements for readability.
