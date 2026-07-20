# dotfiles-manage

Version and sync your configuration files across machines with git — deploy to any new machine in one command.

## What it does

The agent sets up a dotfiles management system using one of four strategies (git bare repo, GNU Stow, chezmoi, or yadm). Your config files get versioned in a git repo, and you can deploy them to any new machine by cloning and running one command. No more manually copying `.bashrc` to a new laptop.

## Install

```bash
hermes skills install https://github.com/THEROCKSSS/hermes-skills-portfolio/blob/main/skills/dotfiles-manage/SKILL.md
```

## How to use

```
"Set up dotfiles management for my shell, vim, and git configs"
```

The agent:
1. Recommends a strategy based on your needs (bare repo for simplicity, chezmoi for multiple machines)
2. Sets up the repo structure
3. Adds your config files
4. Pushes to a git remote
5. Shows you the one-command deploy for new machines

## Strategies

| Strategy | Needs | Best for |
|---|---|---|
| Git bare repo | Just git | Minimalists |
| GNU Stow | stow installed | Organized by package |
| chezmoi | chezmoi installed | Multiple machines, templated configs |
| yadm | yadm installed | Git-familiar, wants extras |

## Example

```
User: "I just got a new laptop. I want my configs from my old machine."

Agent:
  1. On old machine: sets up git bare repo at ~/.cfg
  2. Adds: .bashrc, .vimrc, .gitconfig, .tmux.conf
  3. Pushes to github.com/youruser/dotfiles
  4. On new machine: git clone --bare ... ~/.cfg
  5. Runs: config checkout
  6. Returns: "Your configs are now on the new machine."
```
