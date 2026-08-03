---
name: movie-catalogue-site
description: Use when the user wants to build a browsable movie/TV catalogue — a "Netflix-like" front-end, a media dashboard, a personal streaming site, a watchlist app with browse/search/detail pages — or says "build me a movie site", "a page to browse films and shows", "my own TV catalogue". Covers the app shell, routes, rails, filter state, empty states, and the deploy shape that owns the CSP. Not for the metadata API itself (tmdb-metadata) or the player (streaming-provider-embeds).
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [movie-catalogue, streaming-site, spa, react, vite, watchlist]
    related_skills: [tmdb-metadata, streaming-provider-embeds, watchlist-sync, media-id-mapping, movie-night-calendar]
---

# movie-catalogue-site

## Overview

Build the browsable half of a movie/TV catalogue: an app shell with home rails, search, category browse, a title detail page, and a watchlist route — on top of a metadata API and (optionally) third-party embed providers. This skill owns the **application structure**: module boundaries, routing, filter state, loading/empty states, and the deploy shape. The metadata contracts live in `tmdb-metadata`, the player in `streaming-provider-embeds`, persistence in `watchlist-sync`.

The stack that works and stays debuggable: a plain Vite + React SPA (no TypeScript, no component library, no state manager, no CSS framework), a generated REST layer over Postgres (PostgREST/Supabase) instead of a bespoke API server, and a reverse proxy that owns the security headers. Every layer you remove is one that can't break between you and a rendered page.

## When to Use

- The user wants a browsable catalogue of films/shows with posters, detail pages, and search.
- An existing catalogue needs a new route, rail, or browse surface.
- Playback, watchlist, or metadata work needs a place to live and the app shell doesn't exist yet.
- The user asks for "a personal Netflix", "a media browser", "a site for my movie list".

Do **not** use it for: a media *server* that transcodes and serves your own files (that's Jellyfin/Plex territory), or a plain flat list with no metadata lookups.

## Workflow

Build in this order. Each step's output is the next step's input; skipping ahead means debugging two unknowns at once.

1. **Scaffold and prove one API call.** `npm create vite@latest -- --template react`, add `react-router-dom`, put the metadata key in `.env` as `VITE_TMDB_API_KEY`, and render one rail of real posters. Nothing else — no player, no database. Done when a live response paints artwork.
2. **Fail loudly on missing config.** Throw at module load if a required key is absent (see Config below). A missing key otherwise produces 401s that the fetch layer reports as "no results", and an empty search that says "no matches" is a lie.
3. **Draw the module boundaries** (see Module Layout). One file per external boundary, so a third-party contract change lands in exactly one place.
4. **Add the routes** (see Routes). Include a real 404 — not the shell over an empty body.
5. **Build the title detail page.** One request with `append_to_response` rather than three. Cast, runtime, genres, certification, availability. This is the page every other surface links into, so it is the one worth over-building.
6. **Add search and category browse**, with every active filter encoded in the query string (see Filter State).
7. **Add the player** — `streaming-provider-embeds`. Add its origin to the proxy CSP in the *same change*, never a follow-up.
8. **Add persistence** — `watchlist-sync`. Profiles, statuses, resume points.
9. **Deploy behind a proxy that owns the CSP** (see Deploy). Bind-mount the build output so a rebuild is live without rebuilding a container.
10. **Verify in a real browser**, not on a clean build. See Verification Checklist.

## Module Layout

```
src/
  main.jsx                 mounts App
  App.jsx                  chrome (nav, footer) + AuthContext + ToastProvider + <Routes>
  lib/
    config.js              env reading; throws on a missing required key
    tmdb.js                every metadata API call, and nothing else
    omdb.js                the secondary ratings source
    supabase.js            every persistence call (PostgREST fetches)
    providers.js           embed URL construction + the trusted-origin allowlist
    idMapping.js           cross-system ID resolution
    watchProviders.js      streaming *availability* (not playback — see the naming note)
  context/
    AuthContext.jsx        which profile is active, and whether it may be edited
  components/              MovieCard, Rail, FilterBar, EpisodePicker, Player, …
  pages/                   Home, Search, Category, TitleDetail, Watchlist, Profiles, NotFound
```

**Keep the origin allowlist in the same file that builds the embed URLs.** Split them and they drift: you add a provider in one and forget the other, which is the black-box failure in `streaming-provider-embeds`.

**Naming trap worth heading off in a comment.** "Providers" means two unrelated things in this domain — *playback embed sources* (where the iframe points) and *watch providers* (which streaming services carry a title, from the metadata API). The reference implementation keeps them in `lib/providers.js` and `lib/watchProviders.js` with a header comment on each pointing at the other. Do the same or you will spend an afternoon reading the wrong file.

## Routes

```
/                        home — hero + rails (trending, popular, top rated, continue watching)
/search?q=&genre=&year=  results; every filter in the query string
/category/:key           browse one rail's full list, paginated
/title/:mediaType/:id    detail + player + episode picker
/person/:id              filmography
/watchlist               the list, with status facets
/profiles                switch / log in
*                        a real 404
```

`:mediaType` is attacker-controlled (it comes straight off the URL). Validate it against `['movie','tv']` at the boundary before it reaches any fetch — see Common Pitfalls.

## Config

```js
// src/lib/config.js
function required(name) {
  const value = import.meta.env[name];
  if (!value) {
    throw new Error(
      `${name} is not set. Copy .env.example to .env and fill it in, then ` +
      `restart the dev server (Vite only reads .env at startup).`,
    );
  }
  return value;
}

export const TMDB_API_KEY = required('VITE_TMDB_API_KEY');
export const OMDB_API_KEY = required('VITE_OMDB_API_KEY');

// Same-origin relative path, proxied to the REST layer by the front gate.
// NOT a hardcoded `http://host:8124` — that breaks under HTTPS (mixed content)
// and under any access path that only forwards one port.
export const API_URL = '/api';
```

Ship a tracked `.env.example` and gitignore `.env`. State plainly in the example file that Vite inlines every `VITE_*` value into the bundle at build time, so those keys are readable by anyone with devtools. That is normal for a browse-only metadata key and is *not* a leak — but a write-scoped or database credential must never go there.

## Filter State Belongs in the URL

Encode every active filter as a query parameter. Shareable and bookmarkable views come free, and the browser's own back/forward restores them with no history code. Three rules that make it behave:

- **Scope sticky persistence per page type.** A filter set on search must not leak into category browse even when the parameter names match.
- **Persist only deliberate changes.** A filter that merely arrived in a shared URL should not become that visitor's sticky default.
- **Use `replace`, not `push`, when writing filters.** Otherwise adjusting four selects buries the page you came from under four history entries.

## Loading, Empty, and Error States

Three states look identical if you collapse them into one nullable variable: *haven't asked yet*, *asked and the answer is nothing*, *asked and it failed*. Carry a separate `loaded` flag. Collapsing 1 and 2 is exactly why catalogue pages flash "nothing available" on every load before data arrives.

- Skeleton cards while loading, sized like the real card so nothing reflows.
- "No listed way to watch this in your region" is a real answer. An empty row is a bug report waiting to happen.
- Never render a dead affordance. If a button can't work here, say why in one line next to it rather than greying it out silently.

## Deploy

Static build behind a reverse proxy, plus the REST layer, plus one shared auth gate in front of both. Neither the static site nor the API publishes a host port of its own — every path goes through the gate.

```nginx
server {
  listen 80;
  root /usr/share/nginx/html;

  add_header X-Content-Type-Options "nosniff" always;
  add_header Referrer-Policy "strict-origin-when-cross-origin" always;
  add_header Content-Security-Policy "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'self'; form-action 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://images.metadata.example.com; connect-src 'self' https://api.metadata.example.com https://images.metadata.example.com https://ratings.example.com; media-src 'self' blob:; worker-src 'self' blob:; frame-src https://player.example.com https://*.player.example.com" always;

  location /app/assets/ { try_files $uri =404; }        # real assets 404 properly
  location /app/        { try_files $uri $uri/ /app/index.html; }   # SPA fallback

  location = / { return 301 $real_scheme://$http_host/app/; }
}
```

Substitute the real hosts for the placeholders. In a TMDB-backed app they are `api.themoviedb.org` (connect), `image.tmdb.org` (img + connect if you read poster pixels), `www.omdbapi.com` (connect), and whichever embed hosts you integrated (frame) — see `tmdb-metadata` and `streaming-provider-embeds`.

Four things in that block are load-bearing and each has cost someone an afternoon:

- **`add_header` is not inherited into a location that declares its own.** The child list replaces the parent list entirely. Add one `add_header` inside a `location` and all the security headers silently vanish *for that location*.
- **`always`**, or the headers are dropped on 301s and 404s.
- **Assets location before the SPA fallback**, or a missing favicon silently serves the app shell with a 200.
- **`return 301 $real_scheme://$http_host/…`**, not a bare `return 301 /app/;`. nginx builds the bare form's `Location` from `$scheme://$host`, which drops the port and ignores the Host the client actually used — so every visitor gets bounced to `http://localhost/...` regardless of the domain they typed. Map `$http_x_forwarded_proto` to `$real_scheme` with a `$scheme` fallback.

**Bind-mount the build output** rather than baking it into an image. A rebuild is then live without rebuilding any container, and only proxy config changes need a restart. It removes an entire class of "why is my fix not deployed".

## Common Pitfalls

1. **Route params reaching a query string unvalidated.** `:mediaType` off the URL interpolated into a PostgREST filter is *filter-param injection* — not SQL injection (PostgREST parameterises), but an attacker can inject extra filters, operators, or `select=` columns. Validate against a closed list, and coerce every id with `Number.isInteger(n) && n > 0`.
2. **Adding a provider without touching the proxy CSP.** Renders a black box with no catchable error, and your own failure detection then reports the *title* as unavailable — a lie that sends you debugging the wrong layer. Code change and CSP change ship together, always.
3. **Two response shapes from one API.** List endpoints return `genre_ids: [28,12]`; detail endpoints return `genres: [{id,name}]`. Code that reads one silently renders nothing on the other. Normalise at the boundary — see `tmdb-metadata`.
4. **A hardcoded API origin.** Breaks the moment the site is reached over HTTPS, a tunnel, or a different port. Use a same-origin relative path the gate proxies.
5. **Cross-origin fetch without `credentials: 'include'`.** The gate's session cookie is silently not sent, and every API call 401s only in production.
6. **Building stats from a resume-point column.** `last_position_seconds` is overwritten on every progress update — see `watchlist-sync` for why summing it produces a confidently wrong number.
7. **`fullPage: true` screenshots for scroll-reveal content.** The capture expands the viewport virtually rather than scrolling, so `IntersectionObserver` reveals never fire and working content looks blank. Scroll in increments before asserting.

## Limitations

This skill does **not**:

- Host, transcode, or serve video files. It builds a catalogue that *links out* or embeds third parties.
- Supply the metadata API contracts — that is `tmdb-metadata`.
- Integrate or debug an embed provider — that is `streaming-provider-embeds`.
- Define the persistence schema or auth — that is `watchlist-sync`.
- Provide a design system. It states structure and state rules only; pair it with a design skill for the visual layer.
- Grant you any right to redistribute content. See the note in `streaming-provider-embeds`.

## Verification Checklist

- [ ] Home, search, a category, a title detail, and a bogus URL all render — the last as a real 404, not the shell over an empty body
- [ ] A deep link (`/title/tv/1396`) works on a hard refresh, not just via in-app navigation
- [ ] Missing `.env` throws a named error at boot instead of rendering an empty catalogue
- [ ] Every filter is in the query string and survives back/forward
- [ ] Loading, empty, and error states are visually distinct on at least one slow/failing route
- [ ] The deployed CSP is applied in the verification run (re-attach it via route interception — `vite preview` sends none) and the console shows zero CSP violations
- [ ] Security headers are present on a 404 and on the root 301, not just on 200s
- [ ] A real browser loaded the page; a `curl` 200 does not prove it renders
