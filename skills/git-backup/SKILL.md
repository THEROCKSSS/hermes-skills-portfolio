---
name: git-backup
description: Automate offsite backups of local git repositories to a remote. Covers mirror clones, bundles, scheduled jobs (cron / systemd), remote targets (GitHub, Forgejo, GitLab, S3), verification, and restore. Use when a user wants a hands-off, repeatable backup of one or many git repos.
version: 1.0.0
---

# git-backup

Give an agent this skill and it will set up an automated, verifiable backup of
the user's git repositories to a remote destination — with no manual `git push`
required and no data lost when a laptop dies.

Backups are only useful if they are (a) automatic, (b) verified, and
(c) restorable. This skill optimizes for all three.

## When to Use

- The user says "back up my repos", "I don't want to lose my code", or "set up
  automatic repo backups".
- The user has local git repos (work, personal, dotfiles) that are not pushed
  anywhere, or are pushed only to one provider and want a second copy.
- The user wants a 3-2-1-style strategy: 3 copies, 2 media, 1 offsite.
- Suitable for any OS where `git` runs (Linux, macOS, Windows/WSL, MSYS).

Do **not** use this skill for:
- Non-git directories — use a file-level tool (rsync, restic, borg).
- One-off manual pushes the user will do by hand.
- Large binary/asset stores — consider Git LFS or object storage instead.

## Backup Strategies

Pick one based on how many repos, how much automation, and how "portable" the
backup must be.

### 1. Mirror clone (recommended for live remotes)

A bare mirror keeps **all** refs (branches, tags, notes) and is what remote
hosts expect.

```bash
# One-time setup
git clone --mirror https://github.com/user/repo.git /backups/repo.git

# Each run (idempotent)
cd /backups/repo.git
git remote update --prune
```

Mirror clones are compact (bare, no working tree) and push cleanly to a fresh
remote later. Good when the destination is another git host.

### 2. Bundle (recommended for cold/portable storage)

A bundle is a **single self-contained file** containing the entire repo — perfect
for S3, NAS, USB drives, or emailing to yourself.

```bash
# Full snapshot into one file
git bundle create /backups/repo-$(date +%F).bundle --all

# Incremental after a known base (smaller files over time)
git bundle create /backups/repo-inc.bundle --since=1.week --all
```

Verify a bundle before trusting it:

```bash
git bundle verify /backups/repo-2026-07-20.bundle
```

### 3. Bundle + push (belt and suspenders)

Combine both: keep a live mirror on a git host **and** ship a dated bundle to
object storage. This survives both "host went down" and "account locked".

```bash
git clone --mirror /src/repo /backups/repo.git && \
  (cd /backups/repo.git && git remote update --prune) && \
  git -C /src/repo bundle create /backups/bundles/repo-$(date +%F).bundle --all && \
  aws s3 cp /backups/bundles/repo-$(date +%F).bundle s3://my-bucket/git/
```

## Scheduling

### cron (Linux/macOS/WSL)

Edit the user's crontab; never run backups as root unless the repos require it.

```bash
crontab -e
# Daily at 03:15, log to a file, silence on success
15 3 * * * /usr/bin/bash /home/user/bin/git-backup.sh >> /var/log/git-backup.log 2>&1
```

Stagger multiple repos so they don't all hit the network at once:

```bash
15 3 * * * /home/user/bin/git-backup.sh work      >> /var/log/gb-work.log 2>&1
30 3 * * * /home/user/bin/git-backup.sh personal  >> /var/log/gb-personal.log 2>&1
```

### systemd timer (preferred on modern Linux)

Timers survive sleep, log to the journal, and recover missed runs.

```ini
# ~/.config/systemd/user/git-backup.service
[Unit]
Description=Git backup

[Service]
Type=oneshot
ExecStart=/home/user/bin/git-backup.sh
```

```ini
# ~/.config/systemd/user/git-backup.timer
[Unit]
Description=Daily git backup

[Timer]
OnCalendar=*-*-* 03:15:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now git-backup.timer
systemctl --user status git-backup.timer
```

On Windows use Task Scheduler to call a `.bat`/`.ps1` wrapper around the same
script, or run the script under WSL.

## Remote Options

### GitHub
Create a private repo, then push the mirror:
```bash
cd /backups/repo.git
git remote add github https://github.com/user/backup-repo.git
git push --mirror github
```

### Forgejo / Gitea
Same flow, different URL:
```bash
git remote add forge https://forgejo.example.com/user/backup-repo.git
git push --mirror forge
```

### GitLab
```bash
git remote add gitlab https://gitlab.com/user/backup-repo.git
git push --mirror gitlab
```

### S3 (or any S3-compatible bucket)
Bundles are the natural fit here — they're immutable files:
```bash
aws s3 cp repo-$(date +%F).bundle s3://my-backup-bucket/git/
# rclone also works for Backblaze B2, Wasabi, MinIO, etc.
rclone copy repo-$(date +%F).bundle remote:bucket/git/
```
Set lifecycle rules to expire very old bundles after N copies exist.

## Verification

A backup you never check is a hope, not a backup. After every run:

1. **Mirror:** `git fsck --connectivity-only` inside the mirror, and confirm the
   remote's ref list matches the source.
2. **Bundle:** always run `git bundle verify <file>` in the backup script and
   abort on non-zero exit.
3. **Remote push:** check `git push --mirror` exit code; alert on failure.
4. **Spot restore (weekly):** clone the mirror or unbundle into a temp dir and
   confirm `git log -1` works.

Add a heartbeat: a tiny `echo "$(date) OK" >> /var/log/gb-heartbeat` line, and
alert if the file is older than 26h.

## Restore

From a mirror:
```bash
git clone /backups/repo.git restored-repo
```

From a bundle:
```bash
git clone /backups/repo-2026-07-20.bundle restored-repo
```

From S3:
```bash
aws s3 cp s3://my-backup-bucket/git/repo-2026-07-20.bundle ./
git clone repo-2026-07-20.bundle restored-repo
```

Then re-point remotes to the live host and push normally. If the original host
is gone, the mirror/bundle *is* the source of truth.

## Pitfalls

- **`git push` (not `--mirror`) loses tags/branches.** Always use `--mirror` for
  full-fidelity copies, or `git push --tags` plus every branch explicitly.
- **Non-bare mirrors drift.** Use `git clone --mirror` (bare) or `remote update
  --prune`; a normal clone accumulates conflicts on repeated fetches.
- **Credentials expire.** Use SSH keys or a token stored in the OS keychain, not
  inline in scripts. On CI, use scoped deploy keys.
- **Unverified bundles rot silently.** A truncated bundle fails only on clone —
  always `git bundle verify` immediately after creation.
- **Clock skew / timezones** in dated filenames cause confusing overwrites;
  use UTC (`date -u +%FT%TZ`) for filenames.
- **Huge repos + daily full bundles** waste space; switch to incremental
  bundles (`--since`) or keep only the mirror for those.
- **Silent failures.** If the script has no alert path, a broken backup looks
  identical to a working one. Always log + heartbeat + alert.
- **Symlinks / submodules.** `git bundle` does not follow submodules; back them
  up separately or use `git submodule` foreach.

## Minimal script skeleton (`git-backup.sh`)

```bash
#!/usr/bin/env bash
set -euo pipefail
SRC="$1"; NAME=$(basename "$SRC"); STAMP=$(date -u +%F)
BAK="/backups"; mkdir -p "$BAK/bundles"
git -C "$SRC" bundle create "$BAK/bundles/$NAME-$STAMP.bundle" --all
git bundle verify "$BAK/bundles/$NAME-$STAMP.bundle"
echo "$(date -u) $NAME OK" >> /var/log/gb-heartbeat
```
