---
name: tmdb-metadata
description: Use when wiring TMDB (and OMDb) into an app — browse rails, search, title detail, posters/backdrops, cast, episodes, certifications, streaming availability, IMDb/Rotten Tomatoes/Metacritic ratings — or when a TMDB-backed feature misbehaves, such as a filter that appears to do nothing, an empty search that should have matched, a genre chip that renders blank, a missing runtime, or a poster that taints a canvas.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [tmdb, omdb, movie-metadata, api-integration, posters, ratings]
    related_skills: [movie-catalogue-site, streaming-provider-embeds, media-id-mapping, http-api-tester]
---

# tmdb-metadata

## Overview

Wire TMDB as the metadata spine of a catalogue app — titles, artwork, cast, genres, episodes, certifications, streaming availability — with OMDb as the secondary source for IMDb / Rotten Tomatoes / Metacritic ratings. A free TMDB v3 key is the only credential the browse half of such an app strictly needs.

TMDB is well-behaved but has three sharp edges that fail *silently*: two different response shapes for the same field, filter parameters that are accepted and ignored on the wrong endpoint, and community-maintained data with real holes. Each one renders a plausible-looking wrong page rather than an error.

## When to Use

- Adding browse rails, search, a detail page, an episode list, or a cast list to an app.
- Adding ratings from IMDb/RT/Metacritic (that's OMDb, keyed by IMDb id, which comes from TMDB).
- Adding "where can I watch this" availability.
- Debugging: a filter that changes nothing, a search returning too few results, blank genre chips, `runtime: null`, a `SecurityError` from a canvas read of a poster.

Do not use it for playback (`streaming-provider-embeds`) or for anime/MAL id bridging (`media-id-mapping`).

## Workflow

1. **Get a free v3 API key** at <https://www.themoviedb.org/settings/api>. Put it in `.env` as `VITE_TMDB_API_KEY` (or your framework's equivalent) and throw at module load if it is absent.
2. **Write one fetch wrapper** and route every call through it (see Fetch Wrapper). Nothing else in the app builds a TMDB URL.
3. **Build browse rails** from the list endpoints, then **search**, then **detail** — in that order, each proven against a live response before the next.
4. **Normalise the genre shape at the boundary** the first time you render a genre, not later (see Two Response Shapes).
5. **Use `/discover` for browsing-by-criteria and `/search` for browsing-by-name.** They are not interchangeable — see Search Ignores Filters.
6. **Add OMDb only after `external_ids` is landing an `imdb_id`.** OMDb is keyed on IMDb id; without one there is nothing to ask.
7. **Render every absence deliberately.** Missing data is normal here; substituting a plausible value is the failure mode.

## Endpoint Set

| Purpose | Endpoint | Notes |
|---|---|---|
| Rails / browse | `/trending/{all,movie,tv}/{day,week}`, `/movie/popular`, `/movie/top_rated`, `/tv/popular`, `/tv/top_rated`, `/tv/airing_today` | list shape — carries `genre_ids`, not `genres` |
| Search | `/search/multi` | mixed movie + tv + person; filter to the types you want |
| Filtered browse | `/discover/{movie,tv}` | the only endpoints that honour filter params |
| Detail | `/{movie,tv}/{id}` | full shape — `genres`, `runtime`, and `external_ids` when appended |
| Episodes | `/tv/{id}/season/{n}` | per-season episode list with per-episode runtimes |
| Cast + crew | `/{movie,tv}/{id}/credits` | |
| Filmography | `/person/{id}/combined_credits` | |
| Certification | `/movie/{id}/release_dates`, `/tv/{id}/content_ratings` | region-scoped, different shapes per type |
| Availability | `/{movie,tv}/{id}/watch/providers` | keyed by region code |
| Service catalogue | `/watch/providers/{movie,tv}?watch_region=XX` | for a "filter by service" picker |

Append `?append_to_response=external_ids,credits` to a detail request to collapse three round-trips into one.

## Fetch Wrapper

```js
const BASE = 'https://api.themoviedb.org/3';

async function tmdbFetch(path, params = {}) {
  const url = new URL(BASE + path);
  url.searchParams.set('api_key', TMDB_API_KEY);
  url.searchParams.set('language', 'en-US');
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v);
  });
  const res = await fetch(url);
  if (!res.ok) throw new Error(`TMDB ${path} failed: ${res.status}`);
  return res.json();
}
```

Dropping empty-string params matters: `with_genres=` is not "no filter", it is a malformed filter.

## Two Response Shapes, One Field Difference

List endpoints return `genre_ids: [28, 12]`. Detail endpoints return `genres: [{id, name}]`. Code that reads one silently renders nothing on the other — no error, just an absent row.

```js
export function genreNames(item, limit = 3) {
  if (!item) return [];
  const fromDetail = Array.isArray(item.genres) ? item.genres.map((g) => g?.id) : null;
  const ids = fromDetail || (Array.isArray(item.genre_ids) ? item.genre_ids : []);
  const out = [];
  for (const id of ids) {
    const name = GENRE_NAMES[id];
    if (name && !out.includes(name)) out.push(name);   // unknown ids dropped, not printed as "18"
    if (out.length >= limit) break;
  }
  return out;
}
```

Genre ids are stable and few enough to hold as a static map rather than fetching `/genre/*/list` every session. Movie-only and TV-only ids share one namespace and do not collide, so a single lookup covers both — TV adds `10759 Action & Adventure`, `10762 Kids`, `10763 News`, `10764 Reality`, `10765 Sci-Fi & Fantasy`, `10766 Soap`, `10767 Talk`, `10768 War & Politics` alongside the movie set.

Derive any picker options from the same map rather than typing a second literal; two literals drift the day one is edited.

## Search Ignores Filters

The trap that costs a day: `with_watch_providers`, `with_genres` and friends are **accepted and ignored** by `/search/*`. No error, no warning.

Measured live against the API (2026-07-30, one reference implementation): `/search/multi?query=Rick and Morty` returned `total_results: 2` both with and without `with_watch_providers`, while the same parameter on `/discover/tv` moved `228,046 → 3,449`.

Consequences:

- **Filter search results client-side.** Fetch, then narrow in the browser.
- **Use `/discover` when the user browses by criteria** rather than by name. That is what it is for, and it filters server-side.
- **A page is 20 results.** Offer several filters against a 20-row pool and two selections empty it — which reads as "nothing matches" but means "we didn't ask for enough". Fetch two or three pages and merge, cap deliberately, treat later pages as best-effort, and de-duplicate on `type:id` (the index shifts between requests and repeats rows).

## Images

```
https://image.tmdb.org/t/p/{size}{path}
```

Poster sizes `w185 w342 w500`; backdrop sizes `w780 w1280 original`. Request the size you will display — a `w1280` backdrop in a 185px rail is pure waste. Return `null` for a null path so callers can omit the element rather than render a broken image.

`image.tmdb.org` sends `Access-Control-Allow-Origin: *`, so canvas pixel reads work **with** `crossOrigin="anonymous"` and throw `SecurityError` from `getImageData` without it. If you derive an accent colour from the poster, handle the block path: one `SecurityError` should set a session flag that skips the decode for every later title, so a CDN policy change degrades to your default accent rather than a half-applied palette.

## OMDb for IMDb / RT / Metacritic

TMDB does not carry Rotten Tomatoes or Metacritic. OMDb does, keyed by IMDb id — which TMDB gives you in `external_ids`.

```js
export async function fetchOmdbByImdbId(imdbId) {
  if (!imdbId) return null;
  const url = new URL('https://www.omdbapi.com/');
  url.searchParams.set('apikey', OMDB_API_KEY);
  url.searchParams.set('i', imdbId);
  url.searchParams.set('plot', 'short');
  const res = await fetch(url);
  const data = await res.json();
  return data.Response === 'True' ? data : null;   // OMDb signals failure in the body, not the status
}

export function parseRatings(omdb) {
  if (!omdb) return { imdb: null, rt: null, metacritic: null };
  const ratings = omdb.Ratings || [];
  return {
    imdb: omdb.imdbRating && omdb.imdbRating !== 'N/A' ? omdb.imdbRating : null,
    rt: ratings.find((r) => r.Source === 'Rotten Tomatoes')?.Value || null,
    metacritic: (ratings.find((r) => r.Source === 'Metacritic')?.Value || omdb.Metascore) ?? null,
  };
}
```

Three OMDb facts worth knowing before you rely on it:

- **It reports failure in the body.** `Response: "False"` arrives with HTTP 200. Checking `res.ok` alone treats an error as data.
- **`"N/A"` is a real value it returns.** Filter it explicitly or it renders as a rating.
- **The free tier is 1,000 requests/day**, and `thewdb` is OMDb's shared public demo key — it works, but it is rate-limited across every project using it, and a 401 silently removes your ratings row. Get your own.

## Availability (`/watch/providers`)

Returns a map keyed by **region code**, each holding tiers: `flatrate` (subscription), `free`, `ads`, `rent`, `buy` — plus a `link` to an aggregator page for that title in that region.

- **Label the region you are reporting.** The same title is subscription in one country and purchase-only in another. An unlabelled availability row is a claim about the wrong country for most visitors.
- **No prices. Ever.** The payload carries services, not amounts. "Cheapest" is not derivable. If you want a primary call-to-action, order by *tier* — free, ads, subscription, rent, buy — and say in the interface that this is a ranking by kind of offer, not a price comparison.
- **The `link` is not a deep link to the service.** It opens the aggregator's page for the title. Say so rather than implying otherwise.
- **Filtering a grid by service is client-side** (see Search Ignores Filters), which means one request per row. So: fetch nothing until the filter is engaged; narrow on type/year/genre/rating first (those are free — already in the response you hold); cache per `type:id:region` for the session; bound concurrency to about five at a time; and treat a failed lookup as **unknown, not unavailable** — silently dropping it shrinks the result set for a reason the viewer cannot see.
- For a service picker, `/watch/providers/{movie,tv}?watch_region=XX` returns the region's catalogue with `display_priorities[region]`. Sort by that rather than hand-writing a per-country list, and cap the picker — the raw list runs to hundreds of entries per region, mostly regional channel add-ons.

## Keys and Exposure

A browse-only metadata key in a client bundle is readable by anyone with devtools. That is the normal arrangement for this API tier and is not a leak — but:

- **Never put a write-scoped or account key in the client.** Read-only only.
- Rate limits are per key, so a public deployment shares yours.
- Write access (rating a title as a user) belongs behind your own backend, not in the bundle.

## Missing Data Is Normal

TMDB is community-maintained. Expect routinely: `runtime: null` on individual episodes even when the series carries an average; no `backdrop_path`; a poster and nothing else; no availability for a valid region; an obscure title with zero votes.

**Render the absence deliberately.** Do not substitute the series average for a missing episode runtime — that prints a confident number the data never said. Show the episode without a duration instead.

## Common Pitfalls

1. **Reading `genre_ids` on a detail response** (or `genres` on a list response). Silent blank.
2. **Passing filters to `/search/*`** and concluding the filter is broken. Wrong endpoint.
3. **Trusting `res.ok` on OMDb.** Failure is in the body.
4. **Rendering `"N/A"`** from OMDb as a score.
5. **Canvas reads without `crossOrigin="anonymous"`** — `SecurityError`, and the whole tint feature dies on the first poster.
6. **Fetching `/genre/*/list` per session** to restate a list that changes about never.
7. **One availability request per row on page load.** Gate it behind the filter actually being used.
8. **Assuming a certification exists.** Region-scoped, frequently absent, and shaped differently for movie (`release_dates`) vs TV (`content_ratings`).
9. **Empty-string params.** `with_genres=` is malformed, not absent — drop empty values in the wrapper.

## Limitations

This skill does **not**:

- Supply an API key, negotiate rate limits, or cover TMDB's v4 account/write endpoints.
- Cover playback or embed providers — see `streaming-provider-embeds`.
- Bridge TMDB ids to MyAnimeList/AniList/Kitsu — see `media-id-mapping`.
- Cache server-side. Everything here is session-scoped, client-side caching; a Redis/edge layer is a separate design.
- Guarantee any measured figure quoted above still holds. Those are dated observations against a live third-party API, not contract.
- Provide legal streaming rights of any kind. `/watch/providers` reports where a title is licensed; it does not license anything to you.

## Verification Checklist

- [ ] A rail, a search, and a detail page all render from live responses
- [ ] Genre chips render on **both** a list card and a detail page (proves the shape normalisation)
- [ ] A `/discover` filter visibly changes `total_results`; the same param on `/search` visibly does not (control case in the same run)
- [ ] A title with no backdrop and an episode with `runtime: null` both render without an invented value
- [ ] OMDb returns a rating for a title with an `imdb_id`, and a title without one skips the request entirely rather than sending `i=undefined`
- [ ] Availability is labelled with the region it describes, shows no prices, and says "no listed way to watch" rather than rendering an empty row
- [ ] Missing `TMDB_API_KEY` throws a named error at boot instead of producing an empty catalogue
