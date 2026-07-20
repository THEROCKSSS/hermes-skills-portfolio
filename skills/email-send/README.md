# email-send

Send email programmatically via SMTP or a transactional email API.

## What it does

The agent configures an email provider (SMTP, Resend, SendGrid, Mailgun, or AWS SES), writes the sending code in your language, and tests the connection. You get a working email function for your app, scripts, or agent tasks — notifications, alerts, reports, or transactional emails.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/email-send/SKILL.md
```

## How to use

```
"Set up email notifications for my app using Resend"
```

The agent:
1. Helps you create a Resend account and get an API key
2. Writes the sending code in Python or Node.js
3. Tests by sending a test email to your address
4. Integrates into your app or script

## Providers

| Provider | Free tier | Best for |
|---|---|---|
| SMTP (Gmail) | 500/day | Personal scripts |
| Resend | 3k/month | Modern apps |
| SendGrid | 100/day | High volume |
| AWS SES | 62k (from EC2) | Cheapest at scale |
| Mailgun | 5k/month (3mo) | EU hosting |

## Example

```
User: "Send me an email when my cron job fails"

Agent:
  1. Sets up Resend with your API key
  2. Writes: send_email("you@example.com", "Job Failed", "<p>Backup failed at 3AM</p>")
  3. Tests: sends a test email → you receive it
  4. Adds the call to your cron job's error handler
```
