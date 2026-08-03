# streaming-provider-embeds

Integrate and debug third-party video embeds in a catalogue app — the URL contract, the CSP that makes or breaks them, the postMessage capture, and the failure modes that render as a black box instead of an error.

## What it does

The agent onboards an embed host the way you'd onboard any undocumented third party: probe it with a control case, capture its real contract live, allowlist exactly what you need, and build explicit failure detection — because in this domain a wrong answer never throws. It renders a black rectangle, or plays a different show at full quality.

It also covers the five traps that make a working embed look dead (and a dead one look working), and the capability table that stops you shipping a seek button on a host that never reports position.

## Read this before integrating anything

Third-party embed hosts are **not licensed sources** and this skill does not pretend otherwise. They aggregate streams whose provenance you cannot verify, they're frequently blocked at DNS/ISP/hosting level, they serve popup and redirect ads, they change or vanish without notice, and embedding one may breach your host's terms, your CDN's terms, or your jurisdiction's copyright law.

If the question is "where can I legally watch this", the answer is the metadata API's availability endpoint (see `tmdb-metadata`), not an embed. Integrate one only with that understood — and never label such a source in your UI as licensed, official, or authorised.

## Install

```bash
hermes skills install https://raw.githubusercontent.com/THEROCKSSS/hermes-skills-portfolio/main/skills/streaming-provider-embeds/SKILL.md
```

## The control probe — do this first

Request an id you believe is real **and** one that certainly isn't (`99999999`). If both look the same, your probe is broken and every measurement after it is meaningless.

```bash
curl -sS -o /dev/null -w '%{http_code} %{size_download}\n' \
  -H "Referer: https://localhost/" \
  -H "Sec-Fetch-Dest: iframe" -H "Sec-Fetch-Mode: navigate" -H "Sec-Fetch-Site: cross-site" \
  -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0 Safari/537.36" \
  "https://provider.example.com/embed/550"
```

Real case: a bare `curl` returned an identical 3,545-byte body for a real id, a second real id, and a bogus one — which looked like a dead provider. It was a `410`: the host refuses requests without an embed-shaped `Referer`. With headers, real ids returned a player and the bogus id returned a distinguishable 404.

A `410`/`403` from a bare curl means **your request was malformed**, not that the title is missing.

## The five traps

| # | Trap | Symptom | Fix |
|---|---|---|---|
| 1 | Missing `frame-src` entry | **Plain black box**, console-only CSP error | CSP entry and provider list are one change, never two |
| 2 | Direct access disabled | Error page for every id, real or not | Send embed-shaped headers when probing |
| 3 | Host sets `X-Frame-Options` | "Refused to display … 'sameorigin'" | Nothing on your side fixes it — check before integrating |
| 4 | CSP re-checks after redirects | Console names a host you never wrote | Follow redirects; allowlist every host in the chain |
| 5 | `sandbox` attribute detected | "Sandbox Detected" error, or an endless spinner | Use a click-catch overlay instead |

Trap 1 is the expensive one: a blocked frame is indistinguishable from a dead provider, so your own failure detection reports the *title* as unavailable — a lie that sends you debugging the wrong layer.

Trap 5's mitigation, which works:

```jsx
<iframe key={src} src={src} allow="autoplay; fullscreen; encrypted-media; picture-in-picture" allowFullScreen />
{overlayActive && (
  <button className="player__click-catch" onClick={() => setOverlayActive(false)}>Tap again to play</button>
)}
```

A transparent layer absorbs the first click so a click-triggered popup fires on your overlay, not inside the frame. Re-arm it on every new `src`.

## Origin allowlisting

```js
export const TRUSTED_EMBED_ORIGINS = Object.freeze(['https://alpha.example.com']);
export const isTrustedEmbedOrigin = (o) => typeof o === 'string' && TRUSTED_EMBED_ORIGINS.includes(o);
```

`Array.includes` is exact element matching — correct. A **string** `includes` is not: `origin.includes('alpha.example.com')` accepts `https://alpha.example.com.attacker.com`. This has been a real vulnerability in a shipped app.

Keep the allowlist in the same file that builds the embed URLs, or the two drift and you get trap 1. And only allowlist an origin you gain something from — one that emits nothing but analytics widens your trust boundary for free.

## Capture the contract, don't trust the docs

```js
window.addEventListener('message', (e) => {
  let d = e.data;
  if (typeof d === 'string') { try { d = JSON.parse(d); } catch {} }
  console.log(e.origin, d);
});
```

In one measured comparison, one host published a full lifecycle contract and delivered it; another's docs implied events, and a live capture of 76 messages across a full session found every one to be third-party analytics chatter with no playback field at all — so that origin was deliberately left out of the allowlist.

Shapes that bite: position arrives as `time` **or** `currentTime` (read the wrong one and you save `undefined`), the payload may be a JSON *string*, and the real event may be nested at `data.data.event`. Handle all three.

Also: mark a title "watching" on **frame load**, not on the first message. Some hosts only message on specific interactions, so a viewer who presses play and walks away would never register at all.

## Detecting failure you cannot see

You can't read a cross-origin frame and CORS blocks pre-probing. Two signals remain: an explicit error event, and **silence**.

A host's error page is static HTML with no scripts, so it posts nothing. A working player posts *something* — even chrome chatter — long before playback starts. Measured on one host: real id → 1 message before playback, bogus id → 0. That difference is the whole signal.

```js
sawAnyMessageRef.current = true;   // set BEFORE parsing — the useful evidence is often a message your parser discards

const timer = setTimeout(() => {
  if (!sawAnyMessageRef.current) onSourceError('silent');
}, 20_000);                         // must cover iframe load + player boot on a slow connection
```

Key it on recognised *playback* events instead and it fires whenever playback simply hasn't started — autoplay blocked, buffering, paused — yanking a working video away from the viewer.

## Capability table

```js
const PROVIDER_CAPABILITIES = Object.freeze({
  alpha: { reportsPosition: true,  canSeekByUrl: false },
  beta:  { reportsPosition: false, canSeekByUrl: true  },
});
```

Two abilities, kept apart so you can see which half is missing: does it tell you where playback is, and can it be told to start at an offset? Record the evidence for each entry in a comment — a wrong flag ships a button that silently does nothing. Derive UI copy from the table, never from a hardcoded string.

## Manual switching, remembered

A cross-origin iframe can't be probed for "does this host carry this title", so let the viewer pick and remember it: per title, with a per-profile default underneath. Precedence goes one way — an explicit per-title choice always outranks the default, and changing the default never retroactively moves a title someone already chose for.

## Coverage sweeps

Sample real ids from your own catalogue, make the sample deterministic (seeded shuffle), bound concurrency, keep the script in the repo. Report `103/140 (73.6%)` — useful and checkable. "Good coverage" is neither, and "we carry everything" is a claim you'll be held to.

## Honest limitations

- Names no specific hosts — they change, disappear, and get blocked. The method transfers; a host list wouldn't.
- Endorses and licenses nothing. See the framing note above.
- Cannot make playback verifiable in headless CI: headless browsers lack the codecs. You can verify the URL built, the response returned, and the messages posted — a person has to watch a video play.
- Cannot bypass a host's `X-Frame-Options`.
- Does not cover DRM, HLS/DASH, or serving your own streams.
- Does not handle id mapping to MAL/AniList — see `media-id-mapping`.

## Part of

[Hermes Skills Portfolio](https://github.com/THEROCKSSS/hermes-skills-portfolio) — empowering skills for the Hermes agent.
