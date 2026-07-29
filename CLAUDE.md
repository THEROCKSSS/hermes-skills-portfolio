# CLAUDE.md

Claude Code-specific operating notes for this repo. For the full picture, read in this order:
1. `design.md` — the locked visual system (theme, tokens, nav/footer, per-page macrostructure). Read before touching any page.
2. `ARCHITECTURE.md` — data flow, generator scripts, what's manual vs. automated.
3. `AGENTS.md` — contribution conventions for any AI agent (Claude, GPT, Hermes, Cursor).
4. `CONTEXT.md` — locked scope decisions and project vocabulary.

Don't duplicate those here — this file is only for things specific to working in *this tool*, on *this machine*.

## Environment specifics

- This is a Windows machine. Python lives in a hermes-agent venv, not on plain `PATH`:
  `C:\Users\User\AppData\Local\hermes\hermes-agent\venv\Scripts\python`
- Run the generator with that interpreter: `python scripts/generate_skill_pages.py` (from repo root).
- `python -m pytest tests/` uses the same venv.

## Local testing

No build step — just serve a directory:
```
python -m http.server <port> --directory site --bind 0.0.0.0
```
Bind `0.0.0.0` (not `127.0.0.1`) if you also want it reachable over Tailscale — check `tailscale status` for this machine's tailnet hostname and give that URL, not just localhost, when reporting a local link back.

Background server processes started via the Bash tool's `run_in_background` have been observed dying unexpectedly in this session (unrelated to disk space or the server itself — confirmed by checking scrollHeight/logs mid-request). If a backgrounded server keeps getting killed, launch it as a detached OS process instead (PowerShell `Start-Process -WindowStyle Hidden`), which survived where the harness-tracked background task didn't.

## Verifying UI changes — use a real browser, not just CSS reading

`npm install playwright && npx playwright install chromium` works in this environment and has been used successfully for real screenshot/DOM verification (no Camoufox/other browser MCP tool is registered here). Two real pitfalls hit and worth remembering:

1. **`page.screenshot({ fullPage: true })` does not really scroll the page.** It expands the viewport virtually to capture beyond the fold, which means any scroll-triggered `IntersectionObserver` reveal never fires during the capture — content can look "invisible/blank" in the screenshot even though it renders fine for a real visitor. To test reveal-on-scroll content, manually scroll in increments (`window.scrollTo` in a loop with waits) *before* asserting on it, or check `document.querySelectorAll('.reveal:not(.is-in)')` is empty after real incremental scrolling.
2. **`deviceScaleFactor` inflates PNG pixel dimensions**, not the page's real CSS height. If you set `deviceScaleFactor: 2` for retina-quality screenshots, divide the resulting PNG height by 2 before treating it as the page's actual scroll height — otherwise a normal-length page looks twice as long as it really is.

## Deploying

- `site/` is the working copy; `docs/` is what GitHub Pages serves from `main`. Sync manually (`cp site/<file> docs/<file>` per changed file — see `ARCHITECTURE.md`, there's no single sync script yet).
- After syncing, regenerate `CHANGELOG.md` and prepend a new entry to `changelog.js`'s `COMMITS` array with the real commit hash/date/subject once you've committed — don't invent a commit that hasn't happened yet.
- Push only after `python -m pytest tests/` passes and CI (GitHub Actions) is green — check with `gh run list --repo THEROCKSSS/hermes-skills-portfolio --limit 3`.
- After pushing, GitHub Pages takes ~10-30s to rebuild — poll `gh api repos/THEROCKSSS/hermes-skills-portfolio/pages --jq '.status'` until `built` before telling the user it's live.

## Safety

- Never commit or push without the user's explicit go-ahead for that specific action — this is a real public repo (github.com/THEROCKSSS/hermes-skills-portfolio) with GitHub Pages serving real traffic.
- Never merge or credit an entry from `pending-sources.json` into the live catalog without the user approving that specific entry — see `AGENTS.md`.
