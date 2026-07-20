# excalidraw-diagram

Generate hand-drawn style diagrams as Excalidraw JSON — architecture, flow, and sequence diagrams.

## What it does

The agent creates Excalidraw-compatible JSON files containing boxes, arrows, circles, and labels arranged as architecture diagrams, flow charts, or sequence diagrams. Open the file in the Excalidraw editor (excalidraw.com) to view, edit, or export as PNG/SVG. The hand-drawn aesthetic makes diagrams look approachable, not corporate.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/excalidraw-diagram/SKILL.md
```

## How to use

```
"Draw an architecture diagram: Client → API → Database → Cache"
```

The agent:
1. Plans the layout (positions, sizes)
2. Generates Excalidraw JSON with boxes and arrows
3. Saves as a `.excalidraw` file
4. You open it at excalidraw.com

## Example

```
User: "Make a flow chart for user registration: Sign up → Validate → Create account → Send email"

Agent:
  1. Plans 4 boxes in a vertical flow with arrows
  2. Generates diagram.excalidraw
  3. Returns: "Open diagram.excalidraw at https://excalidraw.com"
```
