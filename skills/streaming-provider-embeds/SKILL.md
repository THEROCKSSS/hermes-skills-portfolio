---
name: streaming-provider-embeds
description: Use when integrating, switching, or debugging a third-party video embed in a catalogue app — the iframe shows a black box, plays nothing, hangs on a spinner, refuses to play with a sandbox attribute, or reports no progress; or when onboarding a new embed host and you need its URL pattern, postMessage contract, and failure signals captured rather than guessed.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [iframe-embed, video-player, csp, postmessage, black-box-debugging]
    related_skills: [movie-catalogue-site, media-id-mapping, tmdb-metadata, watchlist-sync]
---

# streaming-provider-embeds

## Overview

Integrate third-party embed hosts that serve a player for a title id. You do not control them, cannot read inside their frame, and they change without notice — so every contract you hold is **captured on a date**, not documentation.

The whole domain is one problem wearing different hats: **a wrong answer here does not error.** A blocked iframe renders a plain black rectangle. A refusing host returns HTTP 200 with an error page. A wrong id plays a *different show* at full quality with no warning. An unavailable dub plays nothing, identical to the provider being down.

So the discipline throughout is: **make failure observable, or refuse to act.**

### Before you integrate anything — the honest framing

Third-party embed hosts are not licensed sources and this skill does not pretend otherwise. They aggregate streams whose provenance you cannot verify, they are frequently blocked by DNS/ISP/hosting providers, they serve popup and redirect ads, they change or disappear without notice, and embedding one may breach the terms of your host, your CDN, or your jurisdiction's copyright law. If your goal is "where can I legally watch this", the answer is the metadata API's availability endpoint (see `tmdb-metadata`), not an embed. Integrate an embed only with that understood, and never describe such a source in your UI as licensed, official, or authorised.

## When to Use

- Adding a player to a catalogue app, or adding a second/third source with a switcher.
- An embed shows a black box, an endless spinner, or plays nothing.
- Progress/resume tracking doesn't fire, or saves `undefined`/`0`.
- Onboarding a host with thin, wrong, or client-rendered documentation.
- Deciding whether a documented parameter is actually consumed.

## Workflow

1. **Control probe the host before writing any app code** (see The Control Probe). Establish what a hit and a miss each look like.
2. **Check the host's own framing policy** — `X-Frame-Options`, its own CSP — and follow redirects, recording every host in the chain.
3. **Allowlist every host in that chain in your proxy's `frame-src`, in the same change as the code.** Not a follow-up commit.
4. **Build the embed URL in one module**, next to the trusted-origin allowlist (see URL Construction).
5. **Capture the postMessage contract live** for a full session before parsing anything (see postMessage Capture).
6. **Add the origin to the allowlist only if it sends something worth parsing.**
7. **Add explicit failure detection** — an error event if published, plus a conservative silence watchdog (see Detecting Failure).
8. **Sweep a sample of real ids to measure coverage** and report the number with its sample size.
9. **Confirm a real video plays in a real browser.** An iframe whose `src` resolves is not a video that plays.

## The Control Probe

Before concluding anything about a host, request **two** things: an id you believe is real, and one that certainly is not (`99999999`).

If both responses look the same, your probe is broken and every measurement after it is meaningless. This catches, in one step: being blocked before you reach the routing layer, an SPA shell that returns 200 for everything, and your own malformed request.

**Worked example from a real integration.** A bare `curl` of one host returned an identical 3,545-byte body for a real id, a second real id, and a bogus one. That looked like a dead provider. It was a `410` error page: the host refuses requests without an embed-shaped `Referer`. With the headers added, real ids returned a real player and the bogus id returned a distinguishable `404`.

```bash
curl -sS -o /dev/null -w '%{http_code} %{size_download}\n' \
  -H "Referer: https://localhost/" \
  -H "Sec-Fetch-Dest: iframe" \
  -H "Sec-Fetch-Mode: navigate" \
  -H "Sec-Fetch-Site: cross-site" \
  -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36" \
  "https://provider.example.com/embed/550"
```

A `410`/`403` from a bare curl means **your request was malformed**, not that the title is missing. Do not record it as a coverage miss. Note that hosts typically check only that a plausible cross-site `Referer` is *present*, not which origin it names — so keep it configurable (`PROBE_REFERER`) and default it to something neutral rather than baking your deployment's hostname into a file that may go public.

## The Five Traps

### 1. CSP `frame-src` renders a black box

The most expensive failure in this domain. Adding a provider to your code without adding its origin to `frame-src` means the browser refuses to load the frame. The result is **a plain black rectangle** — no exception, no `onerror`, nothing your app can observe. Your own failure detection then reports the *title* as unavailable, which is false and sends you debugging the wrong layer entirely.

```
frame-src https://provider.example.com https://*.provider.example.com;
```

Console-only symptom:

```
Refused to frame 'https://provider.example.com/' because it violates the following
Content Security Policy directive: "frame-src ..."
```

**Rule: the CSP entry and the provider list are one change, never two.** Put a comment in the proxy config naming the module the list mirrors.

### 2. Direct access is often disabled

Several hosts serve embeds only when the request looks like an iframe navigation from a site. A plain fetch gets an error page regardless of whether the title exists. Use the header set from the control probe above.

### 3. The host refuses framing outright

Some hosts set their own `X-Frame-Options: sameorigin`. No CSP change on your side helps — the provider has decided.

```bash
curl -sS -D - -o /dev/null "https://provider.example.com/embed/550" \
  | grep -iE "^(x-frame|content-security|location)"
```

Verify against a policy-free page before blaming your own CSP. A real observed case: a host answered its own embed with `X-Frame-Options: sameorigin`, producing `Refused to display '…' in a frame because it set 'X-Frame-Options' to 'sameorigin'` — nothing in the app could fix it.

### 4. CSP re-checks after every redirect

A host may 301 to a different origin, and CSP evaluates the **final** URL. Allowlisting only the URL you wrote still fails.

Found live, not theoretically: an embed URL answered with a 301 to a different host, and listing only the first host blocked playback with `Framing 'https://other-host/' violates … "frame-src …"`. Both hosts had to be listed. `curl -L -o /dev/null -w '%{num_redirects} %{url_effective}\n'` tells you what to allowlist.

### 5. `sandbox` is detectable

Adding a `sandbox` attribute as an ad mitigation is detected by some hosts *by the attribute's mere presence*, regardless of which tokens you grant. They then refuse to play — one observed host showed an explicit "Iframe Sandbox Detected" error, another hung on a spinner forever. A never-loading player is worse than the popup you were preventing.

The workable mitigation is a **click-catch overlay**: a transparent layer over the frame that absorbs the first interaction and shows a "tap to play" affordance, so a click-triggered popup fires on your overlay instead of inside the frame. It costs one extra tap, touches nothing about the iframe, and re-arms on every new `src`.

```jsx
<div className="player">
  <iframe
    key={src}
    src={src}
    title="Player"
    allow="autoplay; fullscreen; encrypted-media; picture-in-picture"
    allowFullScreen
    loading="lazy"
  />
  {overlayActive && (
    <button className="player__click-catch" onClick={() => setOverlayActive(false)}>
      Tap again to play
    </button>
  )}
</div>
```

`key={src}` is deliberate: changing the key remounts the frame, which is the only way to make a URL-parameter seek take effect.

## URL Construction and the Origin Allowlist

One module owns both, so they cannot drift:

```js
export const PROVIDERS = [
  { key: 'alpha', label: 'Alpha' },
  { key: 'beta',  label: 'Beta' },
  { key: 'gamma', label: 'Gamma', animeOnly: true },  // no plain movie/TV route at all
];

export function buildEmbedUrl(provider, { mediaType, tmdbId, season, episode, startAtSeconds }) {
  if (provider === 'gamma') {
    // Anime-only host keyed on a foreign id system. Without a *resolved*
    // mapping there is nothing to build — return null so the caller can show
    // an honest "no source" panel instead of mounting a frame that can only 404.
    if (!isResolvedMapping(arguments[1].anime)) return null;
    ...
  }
  return mediaType === 'tv'
    ? `https://beta.example.com/tv/${tmdbId}/${season}/${episode}`
    : `https://beta.example.com/movie/${tmdbId}`;
}

// Full origins (scheme + host + port) exactly as `event.origin` reports them.
export const TRUSTED_EMBED_ORIGINS = Object.freeze([
  'https://alpha.example.com',
  'https://beta.example.com',
]);

export function isTrustedEmbedOrigin(origin) {
  return typeof origin === 'string' && TRUSTED_EMBED_ORIGINS.includes(origin);
}
```

`Array.includes` is exact element matching — correct. A **string** `includes` is not: `origin.includes('beta.example.com')` accepts `https://beta.example.com.attacker.com` and `https://evil.example.com/?beta.example.com`. This has been a real vulnerability in a shipped app; keep the array form.

**Only allowlist an origin you gain something from.** An origin that publishes no player events buys you nothing and widens what you trust.

**Return `null`, never a guessed URL.** A `null` src is what lets the caller render "no source for this title, here's why, pick another" instead of an empty black box that looks like a player loading forever.

## Capability Table, Not Boolean Soup

Two abilities are separate and no host has both by accident. Collapsing them into one `supportsSkipIntro` flag hides which half is missing.

```js
const PROVIDER_CAPABILITIES = Object.freeze({
  alpha: { reportsPosition: true,  canSeekByUrl: false },
  beta:  { reportsPosition: false, canSeekByUrl: true  },
  gamma: { reportsPosition: true,  canSeekByUrl: true  },
});
```

- `reportsPosition` — does the embed tell you where playback is? Without it you cannot know whether the viewer is inside the intro, and you must refuse to guess.
- `canSeekByUrl` — can it be told to *start* at an offset, so remounting the frame is a real skip rather than a restart?

Record the **evidence** for every entry in a comment. A wrong flag here ships a button that silently does nothing. Derive any UI copy about which sources support a feature from this table, never from a hardcoded string that goes stale the day a host gains a parameter.

## postMessage Capture

Player events are how you get real progress and end-of-playback. Never assume a documented contract exists — watch for it:

```js
window.addEventListener('message', (e) => {
  let d = e.data;
  if (typeof d === 'string') { try { d = JSON.parse(d); } catch { /* keep raw */ } }
  console.log(e.origin, d);
});
```

Load a real embed, let it run, and record what actually arrives. **Documentation is a hypothesis.** In one measured comparison, one host published a full lifecycle contract and delivered it; another's docs implied events, and a live capture of 76 messages across a full session found every one to be third-party analytics chatter with no playback field at all — so that origin was deliberately left *out* of the allowlist, and the app degraded to a runtime timer instead.

Payload shapes differ in ways that bite:

- Position may be `time` **or** `currentTime`. Reading the wrong field silently saves a resume point of `undefined` or `0`.
- The payload may be a JSON *string*, not an object.
- The real event may be nested (`data.data.event`).

Handle every shape defensively:

```js
function handleMessage(event) {
  if (!isTrustedEmbedOrigin(event.origin)) return;
  sawAnyMessageRef.current = true;         // set BEFORE parsing — see below
  let data = event.data;
  if (typeof data === 'string') { try { data = JSON.parse(data); } catch { return; } }
  if (!data || typeof data !== 'object') return;
  const inner = data.data && typeof data.data === 'object' ? data.data : data;
  const evt = inner.event ?? data.event;
  const position = typeof inner.time === 'number' ? inner.time : inner.currentTime ?? data.currentTime;
  ...
}
```

Throttle progress writes to roughly once every 15 seconds, and flush unthrottled on `visibilitychange` and `pagehide` — that last save is the one that makes resume feel right.

Also: **fire "mark as watching" on frame load, not on the first postMessage.** Some hosts only message on specific interactions, so a viewer who presses play and walks away would otherwise never register as watching at all.

## Detecting Failure You Cannot See

Same-origin policy means you cannot read the frame, and CORS usually blocks pre-probing the URL from the browser. Two signals remain.

**An explicit error event**, if the host publishes one. Cheap and exact.

**Silence.** A host's error page is typically static HTML with no scripts, so it posts *nothing*. A working player loads scripts that post *something* — even chrome chatter — long before playback starts. Measured on one host: a real id produced 1 message before playback began (a fullscreen-bridge call); a bogus id produced 0. That difference is the entire signal.

So the watchdog is **any message from the trusted origin proves the player loaded** — set the flag before parsing, because the useful evidence is often a message your parser would discard. Key it on recognised *playback* events instead and it fires whenever playback simply hasn't started (autoplay blocked, buffering, paused), yanking a working video away from the viewer.

```js
const SILENT_FAILURE_MS = 20 * 1000;   // must cover iframe load + player boot on a slow connection

useEffect(() => {
  if (!src || !onSourceError) return undefined;
  const timer = setTimeout(() => {
    if (!sawAnyMessageRef.current) onSourceError('silent');
  }, SILENT_FAILURE_MS);
  return () => clearTimeout(timer);
}, [src, onSourceError]);
```

Be conservative: fire at most once per source, use a generous window, and escalate to a fallback route rather than straight to an error.

## Manual Switching Beats Auto-Detection

A cross-origin iframe cannot be reliably probed for "does this host carry this title", so **let the viewer pick a source and remember the choice** — per title, with a per-profile default underneath it.

Precedence goes one way only: a source explicitly chosen *on this title* always beats the profile default. The default answers "where does a title I've never opened start"; the moment someone answers that for a specific title by hand, that is the more specific statement of intent and outranks the blanket preference forever. Changing the default must never retroactively move a title someone already chose a source for.

Exclude anime-only or otherwise partial hosts from being settable as a *global* default — as a starting point one would hand `buildEmbedUrl` a null URL on every ordinary title, and the honest "no source" panel would be the first thing anyone saw.

Announce an automatic switch only when one genuinely happened. Copy that claims a fallback the URL builder doesn't have is worse than silence.

## Coverage Sweeps

Measure rather than assume. Sample real ids drawn from your own catalogue or mapping so every row genuinely resolves, make the sample **deterministic** (seeded shuffle) so later runs are comparable, rate-limit and bound concurrency, and keep the sweep script in the repo so the next refresh is re-measurable rather than re-argued.

Report the number as measured, with the sample size: "103/140 (73.6%)" is useful and checkable; "good coverage" is neither, and "we carry everything" is a claim you will be held to.

## Common Pitfalls

1. **Provider added to the app, not to `frame-src`.** Black box. The single most expensive mistake here.
2. **Substring origin checks.** `origin.includes('alpha.example.com')` accepts `https://alpha.example.com.attacker.net`.
3. **Watchdog keyed on playback events.** Fires on a paused or buffering player and pulls a working video.
4. **Reading the wrong position field.** `time` vs `currentTime` — saves `undefined`, silently.
5. **Assuming a documented parameter is consumed.** Many are accepted and ignored. Confirm by diffing responses with and without it: a changed body size, a changed hash of an encrypted payload, or a different downstream request all count. No change means the parameter is decorative.
6. **Reading client-rendered docs with `curl`.** You get a "Loading…" shell. Open them in a real browser, and read the **raw HTML** — withdrawn parameters are often left commented out, invisible to a screenshot, and a clear signal not to use them.
7. **Adding `sandbox` to stop ads.** Detected by presence; kills playback.
8. **Trusting an origin that only emits analytics.** Widens your trust boundary for nothing.
9. **Shipping a seek/skip button on a host that never reports position.** A dead affordance the viewer can't diagnose.
10. **Letting the embed's own "next episode" control stay enabled** while your app also tracks episode state. The video advances inside the frame, your picker and progress badge don't, and everything downstream disagrees with what's playing. Pass the host's disable parameter explicitly rather than relying on its documented default.

## Limitations

This skill does **not**:

- Endorse, license, or vouch for any embed host, or grant any right to the content they serve. See the framing note at the top.
- Name specific hosts. They change, disappear, and get blocked; the *method* — control probe, capture live, allowlist the origin, detect failure explicitly — is what transfers.
- Make playback verifiable in headless CI. Headless browsers lack the codecs for most commercial streams; you can verify the URL built, the response returned, and the messages posted, but a person has to watch a video play.
- Bypass a host's `X-Frame-Options`. If they refuse framing, that is their decision.
- Cover DRM, HLS/DASH, or hosting your own streams — that is a media-server problem, not an embed problem.
- Handle id mapping to foreign systems (MAL/AniList) — see `media-id-mapping`.

## Verification Checklist

- [ ] Control probe run: a real id and a bogus id produce **visibly different** responses
- [ ] `X-Frame-Options` and any host-side CSP checked with `curl -D -`
- [ ] Redirect chain followed; every final host is in `frame-src`
- [ ] The CSP change shipped in the same commit as the provider code
- [ ] postMessage captured live for a full session; the parser matches what actually arrived, not the docs
- [ ] The origin allowlist uses exact array matching, and a deliberately wrong origin is ignored in a test
- [ ] A bogus/unmapped title renders an honest "no source" panel, not an empty frame
- [ ] The silence watchdog does **not** fire on a paused player (test it paused past the deadline)
- [ ] Coverage measured on a deterministic sample, reported as `n/N (x%)`
- [ ] A human confirmed a real video plays in a real browser
