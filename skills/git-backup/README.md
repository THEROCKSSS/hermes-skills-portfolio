# git-backup

> A Hermes skill that gives the agent everything it needs to set up **automatic,
> verifiable, restorable backups** of your git repositories to an offsite remote.

Part of the [Hermes Skills Portfolio](https://github.com/MonicaAmano/hermes-skills-portfolio)
by Monica Amano.

---

## Why

A local repo is one spilled coffee away from gone. `git-backup` turns "I should
really push that" into a scheduled, hands-off job that you can prove works.

Backups are only real when they are **automatic**, **verified**, and
**restorable**. This skill is built around all three.

## What it does

- **Three strategies**, matched to your setup:
  - **Mirror clone** — compact bare mirror of every ref, ready to push to a host.
  - **Bundle** — one self-contained `.bundle` file for cold/portable storage.
  - **Bundle + push** — both, for a 3-2-1-grade safety net.
- **Scheduling** out of the box: `cron` or a `systemd` timer (Windows via Task
  Scheduler / WSL).
- **Any remote**: GitHub, Forgejo/Gitea, GitLab, or S3-compatible object storage
  (incl. Backblaze B2, Wasabi, MinIO via `rclone`).
- **Verification** built in: `git bundle verify`, `git fsck`, push exit codes,
  and a weekly spot-restore check plus a heartbeat alert.
- **Restore** in three lines, from mirror, bundle, or bucket.

## Install

Point Hermes at the skill file:

```
https://github.com/MonicaAmano/hermes-skills-portfolio/blob/main/skills/git-backup/SKILL.md
```

Or copy the `git-backup` folder into your Hermes skills directory.

## Quick start

Tell the agent:

> "Back up my `~/code` repos to a private GitHub repo every night, and also drop
> a weekly bundle in my S3 bucket. Verify each backup and warn me if one fails."

The agent will pick the mirror + bundle strategy, wire up a `systemd` timer (or
`cron`), add verification + a heartbeat, and hand you the restore commands.

## Example

```bash
# One self-contained, verified snapshot
git bundle create repo-2026-07-20.bundle --all
git bundle verify repo-2026-07-20.bundle

# Restore it anywhere
git clone repo-2026-07-20.bundle restored-repo
```

## License

MIT — use it, fork it, ship it.
