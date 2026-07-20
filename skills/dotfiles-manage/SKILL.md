---
name: dotfiles-manage
description: "Version and sync your dotfiles across machines — agent + this skill = user gets their config files in git and deployable to any new machine."
version: 1.0.0
---

# dotfiles-manage

Set up dotfiles management — version control for your configuration files (shell config, editor config, git config, etc.) with the ability to deploy them to any new machine in one command.

## When to Use

- The user wants their config files versioned and backed up.
- The user is setting up a new machine and wants their configs deployed automatically.
- The user wants to sync configs across multiple machines.
- The user says "set up dotfiles", "version my configs", or "I want my settings on my new laptop".

## Strategies

Four approaches, ranked by simplicity:

| Strategy | How it works | Best for |
|---|---|---|
| **Git bare repo** | A bare git repo stores dotfiles; alias manages add/commit | Minimalists, no extra tools |
| **GNU Stow** | Symlinks from a directory to your home dir | Organized by package, standard tool |
| **chezmoi** | Templated dotfiles with encryption and machine-specific values | Multiple machines with different needs |
| **yadm** | Yet Another Dotfiles Manager — git wrapper for home dir | Git-familiar users who want extras |

## Strategy 1: Git Bare Repo (simplest)

No extra software needed — just git.

### Setup

```bash
# Create a bare repo
git init --bare $HOME/.cfg

# Add an alias to your shell config
echo "alias config='/usr/bin/git --git-dir=\$HOME/.cfg/ --work-tree=\$HOME'" >> ~/.bashrc
source ~/.bashrc

# Ignore untracked files in your home dir
config config --local status.showUntrackedFiles no
```

### Add files

```bash
config add .bashrc .vimrc .gitconfig .tmux.conf
config commit -m "Initial dotfiles"
config remote add origin git@github.com:youruser/dotfiles.git
config push -u origin main
```

### Deploy on a new machine

```bash
# Clone as bare repo
git clone --bare git@github.com:youruser/dotfiles.git $HOME/.cfg

# Add the alias
echo "alias config='/usr/bin/git --git-dir=\$HOME/.cfg/ --work-tree=\$HOME'" >> ~/.bashrc
source ~/.bashrc

# Checkout the files
config checkout

# If it fails because files already exist, back them up first:
mkdir -p .config-backup
config checkout 2>&1 | grep "\t" | awk {'print $1'} | xargs -I{} mv {} .config-backup/{}
config checkout

# Set ignore
config config --local status.showUntrackedFiles no
```

## Strategy 2: GNU Stow

Organizes dotfiles into "packages" and symlinks them into your home directory.

### Setup

```bash
# Install stow
# Linux: apt install stow / pacman -S stow
# macOS: brew install stow

# Create a dotfiles directory
mkdir ~/dotfiles
cd ~/dotfiles

# Organize by package (each package is a directory)
mkdir -p bash vim git tmux

# Move configs into the package directories
mv ~/.bashrc ~/dotfiles/bash/.bashrc
mv ~/.vimrc ~/dotfiles/vim/.vimrc
mv ~/.gitconfig ~/dotfiles/git/.gitconfig

# Stow (create symlinks)
stow bash vim git

# Verify
ls -la ~/.bashrc  # → ~/dotfiles/bash/.bashrc
```

### Deploy on a new machine

```bash
git clone git@github.com:youruser/dotfiles.git ~/dotfiles
cd ~/dotfiles
stow bash vim git tmux
```

### Remove a package

```bash
stow -D vim  # removes the symlinks for the vim package
```

## Strategy 3: chezmoi (for multiple machines with differences)

chezmoi handles machine-specific values, templating, and secrets.

### Setup

```bash
# Install
# Linux: snap install chezmoi --classic / or download
# macOS: brew install chezmoi

# Initialize
chezmoi init

# Add a file
chezmoi add ~/.bashrc
chezmoi add ~/.gitconfig

# Edit managed files
chezmoi edit ~/.bashrc

# Apply changes to your home dir
chezmoi apply

# Push to git
chezmoi cd
git add -A
git commit -m "Initial dotfiles"
git remote add origin git@github.com:youruser/dotfiles.git
git push -u origin main
```

### Deploy on a new machine

```bash
chezmoi init git@github.com:youruser/dotfiles.git
chezmoi apply
```

### Machine-specific values

```bash
# Template file (chezmoi edit ~/.gitconfig)
[user]
    name = {{ .name }}
    email = {{ .email }}

# Set values per machine
chezmoi data --format json  # see current values
# Edit config:
chezmoi edit-config
# Add:
# data:
#   name: "Your Name"
#   email: "your@email.com"
```

## Managing Different OSes

For configs that differ between Linux and macOS:

**chezmoi:**
```bash
# OS-specific files are named with .linux_ or .darwin_ prefix
# chezmoi automatically picks the right one
```

**Git bare repo / Stow:**
```bash
# Use conditionals in your shell config:
if [ "$(uname)" = "Darwin" ]; then
    # macOS-specific settings
elif [ "$(uname)" = "Linux" ]; then
    # Linux-specific settings
fi
```

## Secrets in Dotfiles

Never commit plaintext secrets (API keys, tokens, passwords).

| Method | How |
|---|---|
| **chezmoi encryption** | `chezmoi add --encrypt ~/.config/secrets` — encrypts with age or gpg |
| **Env vars** | Store secrets in a file that's gitignored, load via shell config |
| **Password manager** | Reference secrets from `pass`, `1password-cli`, or `bitwarden-cli` in config |

```bash
# Example: load API key from password manager in .bashrc
export OPENAI_API_KEY=$(pass openai/api-key)
```

## Pitfalls

- **Committing secrets** — Before pushing, check for API keys, tokens, and passwords in your dotfiles. Use `git log -p` to review history. If secrets are already pushed, rotate them immediately — git history is forever.
- **Symlink loops with Stow** — If you stow a directory that contains a symlink pointing back to your home dir, you'll create a loop. Stow will warn you, but check manually.
- **Bare repo checkout fails** — If files already exist in your home dir, `config checkout` fails. Back up the conflicting files first (the deploy script above handles this).
- **Different paths on different OSes** — A config that works on Linux (`~/.config/`) may need a different path on macOS (`~/Library/Application Support/`). Use chezmoi for cross-OS setups, or conditional logic in shell configs.
- **Forgetting to stow/restow** — After adding a new file to a Stow package, you need to re-run `stow <package>` to create the symlink. It's not automatic.
- **Machine-specific values in git** — If you hardcode a machine-specific value (hostname, IP, path) in a dotfile, it breaks on other machines. Use templates (chezmoi) or conditionals.
