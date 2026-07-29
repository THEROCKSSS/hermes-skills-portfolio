---
name: youtube-transcript
description: Use when the user wants the text content of a YouTube video — the full transcript, timestamped segments, a search for a specific topic within the video, or a summary/quote — from a URL or bare video ID.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [youtube, transcript, captions, youtube-transcript-api, video-text-extraction]
    related_skills: [csv-toolkit]
---

# youtube-transcript

## Overview

Fetch transcripts from YouTube videos. The agent retrieves the video's caption track, cleans the text, and returns it as plain text or structured segments with timestamps.

## When to Use

- The user wants the text content of a YouTube video.
- The user wants to search for a specific topic within a video.
- The user wants to summarize or quote a video.
- The user says "get the transcript", "what does this video say", or "extract the captions".

## Prerequisites

```bash
pip install youtube-transcript-api
```

## Basic Transcript

```python
from youtube_transcript_api import YouTubeTranscriptApi

def get_transcript(video_id: str, lang: str = "en") -> str:
    """Get the full transcript as plain text."""
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
    return " ".join([snippet["text"] for snippet in transcript])
```

## With Timestamps

```python
def get_transcript_with_timestamps(video_id: str, lang: str = "en") -> list:
    """Get transcript as a list of {start, duration, text} dicts."""
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
    return [
        {
            "start": snippet["start"],
            "end": snippet["start"] + snippet["duration"],
            "text": snippet["text"]
        }
        for snippet in transcript
    ]
```

## Extract Video ID from URL

```python
import re

def extract_video_id(url: str) -> str:
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
        r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    # Maybe it's already just the ID
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url):
        return url
    raise ValueError(f"Could not extract video ID from: {url}")
```

## Full Workflow

```python
# 1. Get video ID from URL
video_id = extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

# 2. Get transcript
transcript = get_transcript(video_id)

# 3. Optionally save to file
with open("transcript.txt", "w") as f:
    f.write(transcript)
```

## Search Within Transcript

```python
def search_transcript(video_id: str, query: str, lang: str = "en") -> list:
    """Find segments containing a query string."""
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
    query_lower = query.lower()
    matches = []
    for snippet in transcript:
        if query_lower in snippet["text"].lower():
            matches.append({
                "timestamp": snippet["start"],
                "text": snippet["text"]
            })
    return matches
```

## Translate Non-English Transcripts

```python
from youtube_transcript_api import YouTubeTranscriptApi

def get_transcript_any_language(video_id: str) -> str:
    """Get transcript in any available language."""
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    for transcript in transcript_list:
        try:
            return " ".join([s["text"] for s in transcript.fetch()])
        except:
            continue
    raise ValueError("No transcript available in any language")
```

## Common Pitfalls

1. **Calling `get_transcript` without a fallback.** Not all videos have captions — it raises
   `NoTranscriptFound`. Call `list_transcripts` first to check what's actually available before
   assuming a fixed `lang`.
2. **Treating auto-generated captions as manual-quality.** YouTube auto-captions are usually
   available but less accurate (misheard words, no punctuation) — don't present them as a
   verbatim transcript without noting the source.
3. **Fetching many videos back-to-back with no delay.** YouTube rate-limits frequent requests;
   space out multiple fetches or batch jobs will start failing partway through.
4. **Assuming `VideoUnavailable` means a transient error.** It means the video is private or
   deleted — retrying won't help; report it as unavailable to the user.
5. **Hardcoding `languages=["en"]` for non-English content.** If the requested language isn't
   present, `get_transcript` raises rather than falling back — use `list_transcripts` to discover
   available (including auto-translated) languages first.
6. **Returning raw transcript text with HTML entities intact.** Segments can contain `&amp;`,
   `&#39;`, etc. — run `html.unescape()` before presenting the text.

## Verification Checklist

- [ ] `extract_video_id` correctly parses the actual URL format given (watch, youtu.be, embed, or
      shorts) before fetching.
- [ ] `list_transcripts` was checked when the first `get_transcript` call fails, rather than
      immediately reporting failure to the user.
- [ ] Returned text has no raw HTML entities (`&amp;`, `&#39;`) left unescaped.
- [ ] Timestamped output (if requested) has `start`/`end` values that increase monotonically and
      cover the video's actual duration.
