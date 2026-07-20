# ntfy-notifier

Send push notifications to your phone and desktop via simple HTTP requests — no SDK, no Firebase, no APNS.

## What it does

The agent sets up ntfy push notifications for your scripts, cron jobs, or agent tasks. You install the ntfy app on your phone, subscribe to a topic, and then any HTTP POST to that topic URL appears as a push notification. No mobile SDK integration, no certificate management, no per-platform setup.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/ntfy-notifier/SKILL.md
```

## How to use

```
"Send me a notification when my build finishes"
```

The agent:
1. Picks a unique topic name (or uses one you specify)
2. Tells you to install the ntfy app and subscribe to the topic
3. Adds a curl call to your script: `curl -d "Build complete" ntfy.sh/your-topic`
4. Tests it — you get a notification on your phone

## Example

```
User: "Alert my phone if the backup script fails"

Agent:
  1. Topic: backup-alerts-x7k2m9
  2. Instructs: install ntfy app, subscribe to "backup-alerts-x7k2m9"
  3. Adds to backup script:
     curl -H "Priority: high" -H "Title: Backup Failed" \
       -d "Backup failed at $(date)" ntfy.sh/backup-alerts-x7k2m9
  4. Tests: curl -d "Test alert" ntfy.sh/backup-alerts-x7k2m9
  5. Returns: "You should see a test notification on your phone."
```

## Sending a notification

```bash
# Basic
curl -d "Hello" ntfy.sh/your-topic

# With title and priority
curl -H "Title: Alert" -H "Priority: high" -d "Server down" ntfy.sh/your-topic
```

The notification appears instantly on any device subscribed to the topic.
