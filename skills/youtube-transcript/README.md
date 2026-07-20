# youtube-transcript

Extract the transcript from any YouTube video that has captions.

## What it does

The agent fetches the caption track from a YouTube video and returns it as plain text or timestamped segments. Works with manual captions and auto-generated captions. You get the text content of a video without watching it.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/youtube-transcript/SKILL.md
```

## How to use

```
"Get the transcript from https://www.youtube.com/watch?v=..."
```

The agent:
1. Extracts the video ID from the URL
2. Fetches the transcript via the YouTube Transcript API
3. Returns the text (optionally with timestamps)

## Example

```
User: "What does this video say about machine learning? https://youtu.be/..."

Agent:
  1. Extracts video ID
  2. Gets transcript with timestamps
  3. Searches for "machine learning" in the text
  4. Returns: "At 3:42, the speaker says: 'Machine learning is...'"
```
