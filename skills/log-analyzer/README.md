# log-analyzer

Parse log files to find errors, count error types, detect spikes, and extract stack traces.

## What it does

The agent reads a log file and produces a structured analysis: total lines, error count, error types categorized (connection failures, timeouts, auth errors, etc.), errors by hour to find spikes, and full stack trace extraction. You get a summary of what went wrong without manually scrolling through thousands of log lines.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/log-analyzer/SKILL.md
```

## How to use

```
"Check app.log for errors and tell me what went wrong"
```

The agent:
1. Runs a log summary (total lines, errors, warnings)
2. Categorizes errors by type
3. Shows errors by hour to find spikes
4. Extracts the most recent stack traces
5. Reports: "23 errors, mostly timeouts between 2-4 AM"

## Example

```
User: "Why did my service crash last night?"

Agent:
  1. Analyzes service.log (450k lines)
  2. Finds 15 ERROR lines, 3 FATAL
  3. Error types: 8 timeouts, 4 connection refused, 3 OOM
  4. Spikes at 3:00-3:15 AM
  5. Extracts traceback: "OutOfMemoryError: heap space"
  6. Returns: "Service ran out of memory at 3 AM. 8 timeouts cascaded from the OOM event."
```
