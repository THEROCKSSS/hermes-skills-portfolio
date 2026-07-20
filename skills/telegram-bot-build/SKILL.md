---
name: telegram-bot-build
description: "Build a working Telegram bot with slash commands and inline keyboards, in Python (python-telegram-bot) or Node (telegraf). Agent + this skill = user gets a runnable bot they can talk to, not a skeleton."
version: 1.0.0
---

# telegram-bot-build

Build a runnable Telegram bot that responds to slash commands and presents inline keyboard menus. The agent wires up the library, registers handlers, defines the keyboard markup, and runs the bot so the user can open a chat and see it work. Reference libraries: **python-telegram-bot** (v20+, async) and **telegraf** (Node).

## When to Use

- The user says "build a Telegram bot", "make a bot that does X", or "I have a BotFather token, now what".
- A project needs chat-based interaction: alerts, a menu-driven tool, a support front-end, a command wrapper around an API.
- You are extending an existing bot with new commands or interactive menus.
- The user wants inline keyboards (buttons under a message) rather than free-text replies.

Do **not** use it for:
- Long-polling over a web framework you already own for a different purpose — still valid, but the bot library handles this natively.
- Anything that needs raw MTProto (telethon/Pyrogram) — that is client/account automation, a different skill.
- Group moderation at scale — possible, but confirm the user wants admin tooling before adding it.

## Prerequisites

The bot needs a token from BotFather. If the user does not have one, the first step is to get it:

1. Open a chat with [@BotFather](https://t.me/BotFather) in Telegram.
2. Send `/newbot`, pick a display name, then a username ending in `bot` (e.g. `weather_poller_bot`).
3. BotFather replies with a token like `123456789:AAE...longstring`. Treat it as a secret.
4. Send `/setcommands` to BotFather to register the command list users see in the autocomplete menu.

Store the token in an environment variable, never in source:

```bash
# .env  (gitignored)
TELEGRAM_BOT_TOKEN=123456789:AAE...
```

Then load it in code from the environment. If it is missing, the bot must fail with a clear message, not a cryptic stack trace.

## Bot Setup

**Python (python-telegram-bot v20+):**

```bash
pip install python-telegram-bot python-dotenv
```

```python
# bot.py
import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

load_dotenv()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise SystemExit("TELEGRAM_BOT_TOKEN is not set. Add it to .env")

async def start(update, context):
    await update.message.reply_text("Bot is alive. Send /help.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    # run_polling blocks; the bot is live after this returns nothing
    app.run_polling()

if __name__ == "__main__":
    main()
```

**Node (telegraf):**

```bash
npm init -y && npm install telegraf dotenv
```

```js
// bot.js
import { Telegraf } from "telegraf";
import "dotenv/config";

const token = process.env.TELEGRAM_BOT_TOKEN;
if (!token) throw new Error("TELEGRAM_BOT_TOKEN is not set. Add it to .env");

const bot = new Telegraf(token);
bot.command("start", (ctx) => ctx.reply("Bot is alive. Send /help."));
bot.launch();
process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));
```

Run it: `python bot.py` or `node bot.js`. Open the chat with your bot and send `/start`.

## Command Handling

Register one handler per command. Keep each handler small and pure where possible so logic is testable without Telegram.

**Python:**

```python
from telegram.ext import CommandHandler

async def help_command(update, context):
    await update.message.reply_text(
        "Commands:\n/start - wake up\n/echo <text> - repeat\n/menu - show buttons"
    )

async def echo(update, context):
    # context.args holds everything after the command
    text = " ".join(context.args) or "nothing to echo"
    await update.message.reply_text(text)

app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("echo", echo))
```

**Node:**

```js
bot.command("help", (ctx) =>
  ctx.reply("Commands:\n/start - wake up\n/echo <text> - repeat\n/menu - show buttons")
);

bot.command("echo", (ctx) => {
  const text = ctx.message.text.replace(/^\/echo(@\S+)?\s*/, "") || "nothing to echo";
  return ctx.reply(text);
});
```

Rules:
- Command names are lowercase, letters/numbers/underscore only, max 32 chars.
- Register them with `/setcommands` in BotFather so they autocomplete.
- Unknown commands should get a friendly fallback, not silence.
- Use `context.args` (Python) / parse `ctx.message.text` (Node) for parameters; do not assume order.

## Inline Keyboards

Inline keyboards put buttons *under* a message. Each button carries a `callback_data` string (1–64 bytes) that comes back to a callback handler — no text is typed by the user.

**Python:**

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler

async def menu(update, context):
    keyboard = [
        [InlineKeyboardButton("Get weather", callback_data="weather")],
        [InlineKeyboardButton("Set city", callback_data="set_city")],
        [InlineKeyboardButton("Open site", url="https://example.com")],
    ]
    await update.message.reply_text(
        "Choose:", reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update, context):
    query = update.callback_query
    await query.answer()  # REQUIRED: clears the loading state on the button
    await query.edit_message_text(f"You picked: {query.data}")

app.add_handler(CommandHandler("menu", menu))
app.add_handler(CallbackQueryHandler(button))
```

**Node:**

```js
bot.command("menu", (ctx) =>
  ctx.reply("Choose:", {
    reply_markup: {
      inline_keyboard: [
        [{ text: "Get weather", callback_data: "weather" }],
        [{ text: "Set city", callback_data: "set_city" }],
        [{ text: "Open site", url: "https://example.com" }],
      ],
    },
  })
);

bot.on("callback_query", async (ctx) => {
  await ctx.answerCbQuery();  // REQUIRED
  await ctx.editMessageText(`You picked: ${ctx.callbackQuery.data}`);
});
```

Rules:
- Always call `query.answer()` / `ctx.answerCbQuery()` — without it the button spins forever on the user's screen.
- Keep `callback_data` short and stable; it is what your router switches on. Encode intent, not state.
- `url` buttons open a link and do **not** fire a callback.
- You can edit the message text on click (`edit_message_text`) to reflect the choice instead of sending a new bubble.

## Webhook vs Polling

**Polling** (default, `run_polling` / `bot.launch()` in long-poll mode) is simplest: the bot opens HTTPS long-poll requests to Telegram. No public server, no certificates, no port forwarding. Use it for development and for bots behind a home network or behind a tunnel.

**Webhook** is for production behind a public HTTPS endpoint. Telegram pushes updates to your URL. You must:
- Serve HTTPS on port 443 (or use a reverse proxy / serverless function that terminates TLS).
- Set the webhook once: `curl https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://your.domain/bot<TOKEN>`.
- Match the path to the token, and delete the old webhook (`deleteWebhook`) before switching back to polling — a bot cannot poll and webhook at once.

Guidance:
- Start with polling. Move to webhook only when you have a stable public HTTPS URL and need push (lower latency, fewer requests, required by some hosts).
- If deploying serverless (Cloud Functions, Workers, Lambda), webhook is the natural fit — `app.post("/webhook", ...)` + `setWebhook`.
- Never hardcode the webhook URL; read it from env so staging vs prod differs by config.

## Pitfalls

- **Token in source / committed to git.** Load from env. A leaked token lets anyone drive your bot; revoke via BotFather `/revoke`.
- **Forgetting `query.answer()`.** The button shows a perpetual spinner. Every callback handler must answer the query.
- **callback_data over 64 bytes.** Telegram rejects it silently with an API error. Encode an opaque id, look up the payload server-side.
- **Polling and webhook simultaneously.** You cannot do both. Switching modes requires deleting the webhook first or updates will never arrive on the other.
- **Not handling `/setcommands`.** Without it, commands don't autocomplete and the bot feels broken even though it works.
- **Replying to callback queries with `reply_text` instead of `edit_message_text`.** That sends a *new* message bubble, not an update to the button's message. Use edit for in-place changes.
- **Crashing on every update.** A single unhandled exception in a handler can kill polling in older setups; wrap external calls (API/DB) in try/except and send a graceful error. python-telegram-bot v20 uses async error handlers (`app.add_error_handler`).
- **Localized command names.** Commands must be ASCII; don't localize the `/command` itself, localize the reply text.
- **Long-running work blocking the loop.** Heavy jobs (image gen, API calls) should run in a task/queue, not inline in the handler, or updates back up.
- **Testing with the real token in CI.** Use a throwaway test bot or mock the update objects; never poll the production bot from a test run.
