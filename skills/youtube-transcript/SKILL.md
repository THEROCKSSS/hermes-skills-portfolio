---
name: youtube-transcript
description: "Extract transcripts from YouTube videos — agent + this skill = user gets the text of any YouTube video."
version: 1.0.0
---

# youtube-transcript

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

## Pitfalls

- **No captions available** — Not all videos have captions. `get_transcript` raises `NoTranscriptFound`. Check with `list_transcripts` first.
- **Auto-generated captions** — YouTube auto-generates captions for many videos. They're less accurate than manual captions but usually available.
- **Rate limiting** — YouTube may rate-limit frequent requests. Add delays between multiple video fetches.
- **Video is private or deleted** — Private or deleted videos have no transcript. The API raises `VideoUnavailable`.
- **Language not available** — If the requested language isn't available, try `list_transcripts` to see what languages exist. Many videos have auto-translated tracks.
- **HTML entities in text** — Transcript text may contain HTML entities (`&amp;`, `&#39;`). Use `html.unescape()` to clean them.
