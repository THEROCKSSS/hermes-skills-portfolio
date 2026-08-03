---
name: gif-search
description: "Use when the user wants a GIF for a message or reaction — including a specific reaction GIF (facepalm, thumbs up, celebration) — found and downloaded via the Tenor API."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [tenor-api, gif-search, reaction-gif, media-download]
    related_skills: [discord-bot-build, telegram-bot-build]
---

# gif-search

## Overview

Search and download animated GIFs from Tenor's API. The agent finds GIFs by keyword, previews results, and downloads the selected GIF to a local file.

## When to Use

- The user wants a GIF for a message or reaction.
- The user wants to find a specific reaction GIF (facepalm, thumbs up, celebration).
- The user says "find me a GIF", "search for a GIF", or "I need a reaction GIF".

## Prerequisites

A Tenor API key. Get one free at https://developers.google.com/tenor/guides/quickstart

```bash
# Store the key as an environment variable
export TENOR_API_KEY="your_key_here"
```

## Search for GIFs

```python
import requests
import os

def search_gifs(query: str, limit: int = 10, pos: str = "") -> list:
    """Search Tenor for GIFs matching the query."""
    api_key = os.environ.get("TENOR_API_KEY", "")
    params = {
        "q": query,
        "key": api_key,
        "limit": limit,
        "media_filter": "gif",
        "contentfilter": "medium",
    }
    if pos:
        params["pos"] = pos

    resp = requests.get("https://tenor.googleapis.com/v2/search", params=params)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("results", []):
        gif_url = None
        for media in item.get("media_formats", []):
            if media.get("gif"):
                gif_url = media["gif"]["url"]
                break
        if gif_url:
            results.append({
                "id": item.get("id"),
                "title": item.get("title", ""),
                "url": gif_url,
                "preview": item.get("media_formats", [{}])[0].get("tinygif", {}).get("url", ""),
            })
    return results
```

## Download a GIF

```python
def download_gif(url: str, output_path: str) -> str:
    """Download a GIF to a local file."""
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return output_path
```

## Full Workflow

```python
# 1. Search for GIFs
results = search_gifs("facepalm", limit=5)

# 2. Show options to the user
for i, r in enumerate(results):
    print(f"{i}: {r['title']} — {r['url']}")

# 3. User picks one
choice = 2
selected = results[choice]

# 4. Download
path = download_gif(selected["url"], "facepalm.gif")
print(f"Downloaded to {path}")
```

## Trending GIFs

```python
def trending_gifs(limit: int = 10) -> list:
    """Get currently trending GIFs."""
    api_key = os.environ.get("TENOR_API_KEY", "")
    params = {"key": api_key, "limit": limit, "media_filter": "gif"}
    resp = requests.get("https://tenor.googleapis.com/v2/featured", params=params)
    resp.raise_for_status()
    # Same parsing as search_gifs
    ...
```

## Categories

```python
def categories() -> list:
    """Get available GIF categories."""
    api_key = os.environ.get("TENOR_API_KEY", "")
    params = {"key": api_key, "type": "featured"}
    resp = requests.get("https://tenor.googleapis.com/v2/categories", params=params)
    return resp.json().get("tags", [])
```

## Workflow

1. Get the search query from the user
2. Search Tenor with the query
3. Present top 5-10 results (title + URL) to the user
4. User picks one
5. Download the selected GIF to a local file
6. Return the file path

## Common Pitfalls

1. **No API key** — Without a Tenor API key, all requests fail. Get one at https://developers.google.com/tenor/guides/quickstart (free).
2. **Content filter** — Tenor returns NSFW content by default if no filter is set. Use `contentfilter=medium` or `contentfilter=high` to keep results safe.
3. **Rate limits** — Tenor's free tier allows ~100 requests per minute. For normal use this is plenty.
4. **GIF size** — Full GIFs can be 5-20 MB. If you need smaller files, use the `tinygif` or `nanogif` media format instead of `gif`.
5. **API version** — Tenor has v1 and v2 APIs. v2 is current. v1 is deprecated but still works. Always use `tenor.googleapis.com/v2/`.
6. **Attribution** — Tenor doesn't require attribution, but linking back to the Tenor page is good practice.

## Verification Checklist

- [ ] `TENOR_API_KEY` is set and a test search returns results, not an auth error
- [ ] `contentfilter` set to `medium` or `high` before showing results to the user
- [ ] Downloaded file is a valid, non-zero-size GIF at the expected path
- [ ] Media format chosen (`gif` vs `tinygif`/`nanogif`) matches the size constraint the use case needs
