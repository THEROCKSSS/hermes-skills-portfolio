---
name: discord-bot-build
description: Use when the user wants a Discord bot for their server, wants to automate moderation/announcements/custom commands, or says "build a Discord bot", "make a bot for my server", or "I need a Discord mod bot".
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [discord-bot, discordjs, slash-commands, moderation-bot, gateway-intents]
    related_skills: [telegram-bot-build, env-config-manager]
---

# discord-bot-build

## Overview

Build a Discord bot with slash commands, event handlers, and moderation capabilities using discord.js. The bot runs as a Node.js process and connects to Discord via the Gateway.

## When to Use

- The user wants a Discord bot for their server.
- The user wants to automate moderation, send announcements, or add custom commands.
- The user says "build a Discord bot", "make a bot for my server", or "I need a Discord mod bot".

## Prerequisites

1. **Node.js 18+** — check with `node --version`
2. **A Discord bot token** — create a bot at https://discord.com/developers/applications
3. **Privileged Gateway Intents** — enable in the Developer Portal:
   - Presence Intent (if you need online/offline tracking)
   - Server Members Intent (if you need member lists)
   - Message Content Intent (required for reading message text)

## Bot Setup

### Step 1: Create the application

1. Go to https://discord.com/developers/applications
2. Click "New Application" → name it → go to the "Bot" tab
3. Click "Add Bot" → copy the **token** (keep it secret)
4. Under "Privileged Gateway Intents", enable Message Content Intent
5. Under "OAuth2 → URL Generator", select `bot` + `applications.commands` scopes and the permissions you need
6. Open the generated URL to invite the bot to your server

### Step 2: Initialize the project

```bash
mkdir my-bot && cd my-bot
npm init -y
npm install discord.js dotenv
```

### Step 3: Create the bot file

```javascript
// index.js
const { Client, GatewayIntentBits, SlashCommandBuilder, Events } = require('discord.js');
require('dotenv').config();

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.GuildMembers,
    ],
});

client.once(Events.ClientReady, c => {
    console.log(`Logged in as ${c.user.tag}`);
});

// Register slash commands
client.on(Events.InteractionCreate, async interaction => {
    if (!interaction.isChatInputCommand()) return;

    if (interaction.commandName === 'ping') {
        await interaction.reply('Pong!');
    }

    if (interaction.commandName === 'kick') {
        const target = interaction.options.getUser('user');
        const reason = interaction.options.getString('reason') ?? 'No reason provided';
        if (!interaction.memberPermissions.has('KickMembers')) {
            await interaction.reply('You do not have permission to kick members.');
            return;
        }
        try {
            await interaction.guild.members.kick(target, reason);
            await interaction.reply(`Kicked ${target.tag} for: ${reason}`);
        } catch (error) {
            await interaction.reply(`Failed to kick: ${error.message}`);
        }
    }
});

client.login(process.env.DISCORD_TOKEN);
```

### Step 4: Create .env

```
DISCORD_TOKEN=your_bot_token_here
```

### Step 5: Register slash commands

```javascript
// deploy-commands.js
const { REST, Routes, SlashCommandBuilder } = require('discord.js');
require('dotenv').config();

const commands = [
    new SlashCommandBuilder()
        .setName('ping')
        .setDescription('Replies with pong'),
    new SlashCommandBuilder()
        .setName('kick')
        .setDescription('Kick a member')
        .addUserOption(opt => opt.setName('user').setDescription('The user to kick').setRequired(true))
        .addStringOption(opt => opt.setName('reason').setDescription('Reason for kicking')),
].map(cmd => cmd.toJSON());

const rest = new REST().setToken(process.env.DISCORD_TOKEN);

(async () => {
    try {
        await rest.put(Routes.applicationCommands(process.env.CLIENT_ID), { body: commands });
        console.log('Slash commands registered.');
    } catch (error) {
        console.error(error);
    }
})();
```

Run once: `node deploy-commands.js`

### Step 6: Start the bot

```bash
node index.js
```

## Command Registration

Commands must be registered before they appear in Discord. Two scopes:

| Scope | Where it appears | Registration |
|---|---|---|
| Global | All servers the bot is in | Up to 1 hour to propagate |
| Guild | One specific server | Instant |

For development, use guild commands (instant). For production, use global commands.

```javascript
// Guild command (instant, for testing)
await rest.put(
    Routes.applicationGuildCommands(clientId, guildId),
    { body: commands }
);

// Global command (production, up to 1hr delay)
await rest.put(
    Routes.applicationCommands(clientId),
    { body: commands }
);
```

## Event Handling

```javascript
// Member joined
client.on(Events.GuildMemberAdd, member => {
    const channel = member.guild.systemChannel;
    if (channel) channel.send(`Welcome ${member} to the server!`);
});

// Message deleted
client.on(Events.MessageDelete, message => {
    console.log(`Message deleted in #${message.channel.name}: ${message.content}`);
});

// Reaction added
client.on(Events.MessageReactionAdd, (reaction, user) => {
    if (reaction.emoji.name === '📌') {
        // Pin the message
        reaction.message.pin();
    }
});
```

## Moderation Commands

| Command | What it does | Required permission |
|---|---|---|
| `/kick @user [reason]` | Remove a member | KickMembers |
| `/ban @user [reason]` | Ban a member | BanMembers |
| `/mute @user [duration]` | Timeout a member | ModerateMembers |
| `/purge <count>` | Delete recent messages | ManageMessages |
| `/warn @user <reason>` | Issue a warning | ModerateMembers |

## Keeping the Bot Running

**With PM2 (recommended):**
```bash
npm install -g pm2
pm2 start index.js --name my-bot
pm2 save
pm2 startup  # auto-restart on reboot
```

**With Docker:**
```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
CMD ["node", "index.js"]
```

## Common Pitfalls

1. **Message Content Intent not enabled.** The bot can't read message text without this. Enable it in the Developer Portal under "Privileged Gateway Intents" — without it, `message.content` is always empty even though the event still fires.
2. **Token committed or leaked.** Never commit the `.env` file — add it to `.gitignore`. If the token leaks, regenerate it immediately in the Developer Portal; a leaked token gives full control of the bot.
3. **Commands not appearing after deploy.** Global commands take up to 1 hour to propagate. Use guild commands (`applicationGuildCommands`) for testing since they're instant. Also re-run `deploy-commands.js` after adding or changing any command definition — editing `index.js` alone doesn't re-register them.
4. **Bot can't kick/ban despite having the permission.** The bot's role must sit higher in the role hierarchy than the target user's highest role, in addition to having the Kick/Ban permission — Discord enforces hierarchy regardless of permission flags.
5. **Rate limits on bulk operations.** Discord enforces per-route rate limits. Bulk operations (mass ban, mass delete) should use `bulkDelete` and expect the library's automatic rate-limit handling to introduce delays — don't assume every call completes instantly.
6. **No error handling crashes the whole bot.** An unhandled exception inside an interaction handler can crash the process if not caught. Always wrap command logic in try/catch and reply with the error so the user gets feedback instead of a silently dead bot.

## Verification Checklist

- [ ] `node index.js` logs "Logged in as ..." with no uncaught errors on startup
- [ ] `deploy-commands.js` was run and slash commands appear in Discord (guild commands show instantly; confirm before assuming global propagation)
- [ ] Message Content Intent is enabled in the Developer Portal if any command reads `message.content`
- [ ] `.env` is listed in `.gitignore` and the token was never committed
- [ ] Moderation commands (`/kick`, `/ban`, etc.) were tested against a low-permission test account, confirming both the permission check and the Discord role-hierarchy behavior
- [ ] Every interaction handler has a try/catch that replies with an error message instead of leaving the interaction unanswered
