# telegram-bot-build

Turn a BotFather token into a bot you can actually talk to — slash commands and inline keyboard menus included. The agent writes the code, registers the handlers, and runs the bot so it answers in chat, not just compiles.

## What it does

Builds a working Telegram bot in Python (`python-telegram-bot`) or Node (`telegraf`). Covers the full path: getting the token, wiring up the library, registering commands, building inline keyboard buttons, and choosing polling vs webhook. You end up with a runnable bot, not a skeleton with TODOs.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/telegram-bot-build/SKILL.md
```

## How to use

```
"Build a Telegram bot that echoes text and shows a menu of buttons"
```

The agent will:
- Get you a BotFather token if you don't have one (or load it from `.env`).
- Scaffold the bot in your language of choice, with commands registered.
- Add an inline keyboard example so you see buttons working.
- Run it and confirm it responds to `/start` in your chat.

## What you get

A minimal but real bot:

```python
async def start(update, context):
    await update.message.reply_text("Bot is alive. Send /help.")

async def menu(update, context):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    kb = [[InlineKeyboardButton("Weather", callback_data="weather")]]
    await update.message.reply_text("Choose:", reply_markup=InlineKeyboardMarkup(kb))
```

plus the polling run loop and a `.env` for the token.

## What it covers

- **Commands** — one handler each; parameters parsed from the message.
- **Inline keyboards** — buttons under a message, each firing a `callback_data` you route on.
- **Polling vs webhook** — polling for dev and behind NAT; webhook for production behind HTTPS.
- **Pitfalls** — token safety, the `query.answer()` spinner trap, callback-data length limits.

## Limitations

- It builds a bot user (Bot API), not a Telegram client account — no reading others' chats, no MTProto automation.
- Scaling to many groups needs rate-limit handling and a proper deploy; this skill gets you to a correct single-bot baseline.
- Group admin/moderation tooling is out of scope unless you ask for it specifically.
