# discord-bot-build

Build a working Discord bot with slash commands, event handlers, and moderation tools.

## What it does

The agent creates a Discord bot using discord.js — sets up the project, registers slash commands, implements event handlers, and adds moderation commands (kick, ban, mute, purge). The bot connects to your server and responds to commands in real time.

## Install

```bash
hermes skills install https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/discord-bot-build/SKILL.md
```

## How to use

```
"Build a Discord bot for my server with kick, ban, and a ping command"
```

The agent:
1. Initializes a Node.js project with discord.js
2. Creates the bot file with slash commands and event handlers
3. Creates the command deployment script
4. Shows you how to invite the bot and start it

## Prerequisites

- Node.js 18+
- A Discord bot token from https://discord.com/developers/applications
- Message Content Intent enabled in the Developer Portal

## Example

```
User: "I need a Discord bot that welcomes new members and has a /purge command"

Agent:
  1. npm init + npm install discord.js dotenv
  2. Creates index.js:
     - GuildMemberAdd event → sends welcome message
     - /purge command → deletes N messages (requires ManageMessages)
  3. Creates deploy-commands.js
  4. Returns: "Run `node deploy-commands.js` to register commands, then `node index.js` to start the bot."
```

## Commands included

| Command | Action | Permission |
|---|---|---|
| `/ping` | Replies "Pong!" | None |
| `/kick @user [reason]` | Kicks a member | KickMembers |
| `/ban @user [reason]` | Bans a member | BanMembers |
| `/purge <count>` | Deletes recent messages | ManageMessages |
