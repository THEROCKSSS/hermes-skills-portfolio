# tmdb-metadata

Wire TMDB into an app as the metadata spine — titles, artwork, cast, genres, episodes, certifications, availability — with OMDb for IMDb / Rotten Tomatoes / Metacritic ratings.

## What it does

The agent builds the metadata layer: one fetch wrapper, the endpoint set that actually covers a catalogue app, and the boundary normalisation that keeps TMDB's two response shapes from silently rendering nothing.

It exists mostly because of three sharp edges that fail *quietly*: the same field arrives under two different names depending on the endpoint, filter parameters are accepted and ignored on `/search/*`, and the data is community-maintained with real holes. All three produce a plausible-looking wrong page rather than an error.

## Install

```bash
hermes skills install https://raw.githubusercontent.com/THEROCKSSS/hermes-skills-portfolio/main/skills/tmdb-metadata/SKILL.md
```

## Endpoints that cover a catalogue app

| Purpose | Endpoint |
|---|---|
| Rails / browse | `/trending/{all,movie,tv}/{day,week}`, `/movie/popular`, `/tv/top_rated`, `/tv/airing_today` |
| Search | `/search/multi` |
| Filtered browse | `/discover/{movie,tv}` — the only endpoints that honour filter params |
| Detail | `/{movie,tv}/{id}?append_to_response=external_ids,credits` |
| Episodes | `/tv/{id}/season/{n}` |
| Cast + crew | `/{movie,tv}/{id}/credits` |
| Certification | `/movie/{id}/release_dates`, `/tv/{id}/content_ratings` |
| Availability | `/{movie,tv}/{id}/watch/providers` |
| Service catalogue | `/watch/providers/{movie,tv}?watch_region=XX` |

Keys: free TMDB v3 key from <https://www.themoviedb.org/settings/api>, free OMDb key from <https://www.omdbapi.com/apikey.aspx>. Both go in `.env` as `VITE_TMDB_API_KEY` / `VITE_OMDB_API_KEY` (or your framework's equivalent).

## The three silent failures

### 1. Two response shapes

List endpoints return `genre_ids: [28, 12]`. Detail endpoints return `genres: [{id, name}]`. Read the wrong one and the row renders blank with no error.

```js
const ids = Array.isArray(item.genres) ? item.genres.map((g) => g?.id) : item.genre_ids;
```

Normalise at the boundary the first time you render a genre. Hold the id→name map statically — genre ids are stable and small, and movie/TV ids share one non-colliding namespace.

### 2. `/search/*` accepts and ignores filters

Measured live (2026-07-30, one reference implementation): `/search/multi?query=Rick and Morty` returned `total_results: 2` with and without `with_watch_providers`, while the same param on `/discover/tv` moved `228,046 → 3,449`.

So: `/discover` when the user browses **by criteria**, `/search` when they browse **by name**, and any filtering of search results happens client-side. A page is 20 results — offer several filters against that pool and two selections empty it, which reads as "nothing matches" but means "we didn't ask for enough". Fetch a couple of pages, merge, de-duplicate on `type:id`.

### 3. Missing data is normal

`runtime: null` on individual episodes, no `backdrop_path`, no availability for a valid region, zero votes on obscure titles. Render the absence — do not substitute the series average for a missing episode runtime. That prints a confident number the data never said.

## OMDb notes

```js
const res = await fetch(url);
const data = await res.json();
return data.Response === 'True' ? data : null;   // failure arrives with HTTP 200
```

- OMDb reports failure **in the body**, not the status. `res.ok` alone treats an error as data.
- `"N/A"` is a real value it returns — filter it or it renders as a score.
- Free tier is 1,000 requests/day. `thewdb` is OMDb's shared public demo key: it works, it is rate-limited across every project using it, and a 401 silently drops your ratings row. Get your own.

## Images

```
https://image.tmdb.org/t/p/{size}{path}
```

Posters `w185 w342 w500`, backdrops `w780 w1280 original`. Request the size you display. `image.tmdb.org` sends `Access-Control-Allow-Origin: *`, so canvas pixel reads work with `crossOrigin="anonymous"` — and throw `SecurityError` without it. If you derive a poster accent colour, make one `SecurityError` set a session flag that skips the decode for every later title, so a CDN policy change degrades to a default rather than a half-applied palette.

## Availability, honestly

`/watch/providers` returns tiers per region: `flatrate`, `free`, `ads`, `rent`, `buy`, plus a `link` to an aggregator page.

- **Label the region.** The same title is subscription in one country and purchase-only in another.
- **No prices.** The payload has services, not amounts — "cheapest" is not derivable. Rank by tier and say that's what you're doing.
- **The `link` is not a deep link into the service.** It opens the aggregator's title page.
- **Filtering a grid by service is client-side**, so: nothing fetched until the filter is engaged, narrow on free fields first, cache per `type:id:region`, cap concurrency around five, and treat a failed lookup as **unknown, not unavailable**.

## Key exposure

A browse-only key in a client bundle is readable by anyone with devtools. That's normal for this tier and not a leak — but never put a write-scoped or account key there, and remember rate limits are per key, so a public deployment shares yours.

## Honest limitations

- Does not supply keys, raise rate limits, or cover TMDB v4 account/write endpoints.
- Does not cover playback or embed providers (`streaming-provider-embeds`) or MAL/AniList id bridging (`media-id-mapping`).
- Caching described here is session-scoped and client-side; a server/edge cache is a separate design.
- The measured figures quoted above are dated observations against a live third-party API, not a contract — re-measure before relying on them.
- `/watch/providers` reports where a title is licensed. It licenses nothing to you.

## Part of

[Hermes Skills Portfolio](https://github.com/THEROCKSSS/hermes-skills-portfolio) — empowering skills for the Hermes agent.
