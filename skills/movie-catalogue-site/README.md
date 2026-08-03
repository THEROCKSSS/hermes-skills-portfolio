# movie-catalogue-site

Build the browsable half of a movie/TV catalogue — home rails, search, category browse, title detail, watchlist — as a small, debuggable SPA over a metadata API.

## What it does

The agent scaffolds and structures the app: module boundaries that put each external contract in exactly one file, routes including a real 404, filter state encoded in the URL, honest loading/empty/error states, and a deploy shape where a reverse proxy owns the security headers.

It deliberately keeps the stack small — Vite + React, plain JS, no component library, no state manager, no CSS framework, no bespoke API server. Every layer removed is one that can't break between you and a rendered page.

The metadata API, the player, and the watchlist each have their own skill. This one is the shell they plug into.

## Install

```bash
hermes skills install https://raw.githubusercontent.com/THEROCKSSS/hermes-skills-portfolio/main/skills/movie-catalogue-site/SKILL.md
```

## What you get

```
src/
  main.jsx / App.jsx       chrome + auth context + routes
  lib/
    config.js              env reading; throws on a missing required key
    tmdb.js                every metadata call, and nothing else
    supabase.js            every persistence call
    providers.js           embed URLs + trusted-origin allowlist (one file, never two)
    watchProviders.js      streaming availability (different thing — see below)
  pages/                   Home, Search, Category, TitleDetail, Watchlist, Profiles, NotFound
  components/              MovieCard, Rail, FilterBar, EpisodePicker, Player
deploy/
  nginx.conf               SPA fallback + CSP (the CSP lives here, not in the app)
  docker-compose.yml
```

## Routes

```
/                        home — hero + rails
/search?q=&genre=&year=  results; every filter in the query string
/category/:key           full paginated list for one rail
/title/:mediaType/:id    detail + player + episode picker
/person/:id              filmography
/watchlist               the list, with status facets
/profiles                switch / log in
*                        a real 404
```

## Two things called "providers"

This domain overloads the word, and mixing them up costs an afternoon:

| File | Means | Example |
|---|---|---|
| `lib/providers.js` | **playback embed sources** — where the iframe points | the player host serving `/embed/movie/550` |
| `lib/watchProviders.js` | **watch providers** — which services legitimately carry a title | Netflix, Hulu, Disney+ from `/watch/providers` |

Put a header comment on each pointing at the other.

## Fail loudly on missing config

```js
function required(name) {
  const value = import.meta.env[name];
  if (!value) {
    throw new Error(`${name} is not set. Copy .env.example to .env and fill it in, ` +
                    `then restart the dev server (Vite only reads .env at startup).`);
  }
  return value;
}
export const TMDB_API_KEY = required('VITE_TMDB_API_KEY');
```

Without this, a missing key produces 401s that the fetch layer reports as "no results" — and a search that says "no matches" when it means "no credentials" is a lie that hides for days.

Ship a tracked `.env.example`, gitignore `.env`, and say in the example that Vite inlines every `VITE_*` value into the bundle: those keys are public on the deployed site. Fine for a browse-only metadata key, never for a database credential.

## Filter state in the URL

Encode every active filter as a query parameter — shareable, bookmarkable, and back/forward works with no history code. Three rules:

- Scope sticky persistence per page type (a search filter must not leak into category browse).
- Persist only deliberate changes — a filter that arrived in someone else's shared link is not a preference.
- Write filters with `replace`, not `push`, or four selects bury the page you came from.

## Deploy: the proxy owns the CSP

```nginx
location /app/assets/ { try_files $uri =404; }              # assets 404 properly
location /app/        { try_files $uri $uri/ /app/index.html; }  # SPA fallback
location = /          { return 301 $real_scheme://$http_host/app/; }
```

Four load-bearing details:

- **`add_header` is not inherited into a location that declares its own** — the child list replaces the parent list entirely, and your security headers vanish for that location.
- **`always`**, or headers are dropped on 301s and 404s.
- **Assets block before the SPA fallback**, or a missing favicon serves the app shell with a 200.
- **`return 301 $real_scheme://$http_host/…`** — the bare `return 301 /app/;` form builds `Location` from `$scheme://$host`, drops the port, and bounces every visitor to whatever the config says instead of the domain they used.

Bind-mount the build output instead of baking it into an image: a rebuild goes live without rebuilding a container.

## Pitfalls

- **Route params reaching a query string unvalidated.** `:mediaType` off the URL in a PostgREST filter is filter-param injection — extra filters, operators, or `select=` columns. Validate against a closed list; coerce ids with `Number.isInteger(n) && n > 0`.
- **Adding a player without touching the CSP.** Black box, no catchable error, and your own failure detection blames the title. Code and CSP ship together.
- **Two response shapes.** List endpoints give `genre_ids`, detail endpoints give `genres`. Normalise at the boundary.
- **Hardcoded API origin.** Breaks under HTTPS (mixed content) and under any tunnel forwarding one port. Use a same-origin path the gate proxies.
- **Cross-origin fetch without `credentials: 'include'`.** The gate cookie is dropped and every write 401s in production only.
- **`page.screenshot({ fullPage: true })` for reveal-on-scroll content.** It expands the viewport virtually rather than scrolling, so `IntersectionObserver` never fires and working content photographs blank.

## Honest limitations

- It does not host, transcode, or serve video. It builds a catalogue that links out or embeds third parties.
- Metadata contracts, player integration, and persistence each live in their own skill (`tmdb-metadata`, `streaming-provider-embeds`, `watchlist-sync`).
- It provides structure and state rules, not a visual design system.
- Anything you embed from a third-party host is that host's content under that host's terms. This skill takes no position on, and grants no rights to, what those hosts serve.

## Part of

[Hermes Skills Portfolio](https://github.com/THEROCKSSS/hermes-skills-portfolio) — empowering skills for the Hermes agent.
