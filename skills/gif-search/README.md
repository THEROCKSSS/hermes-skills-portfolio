# gif-search

Search and download GIFs from Tenor by keyword.

## What it does

The agent searches Tenor's GIF library by keyword, shows you the top results, and downloads the one you pick. Useful for finding reaction GIFs for messages, social media, or documentation.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/gif-search/SKILL.md
```

## How to use

```
"Find me a celebration GIF"
```

The agent:
1. Searches Tenor for "celebration"
2. Shows you 5-10 results with titles and preview URLs
3. You pick one
4. Downloads it to a local file

## Prerequisites

- A free Tenor API key from https://tenor.com/developer/keyregistration
- Set as `TENOR_API_KEY` environment variable

## Example

```
User: "I need a facepalm GIF"

Agent:
  1. Searches Tenor: search_gifs("facepalm", limit=5)
  2. Returns:
     0: Facepalm Reaction — https://media.tenor.com/...
     1: Picard Facepalm — https://media.tenor.com/...
     2: Animated Facepalm — https://media.tenor.com/...
  3. User picks: 1
  4. Downloads to facepalm.gif
  5. Returns: "Saved to facepalm.gif"
```
