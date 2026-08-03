---
name: media-id-mapping
description: Use when a feature needs a title's id in a system other than the one you hold — TMDB to IMDb, TVDB, MyAnimeList, AniList or Kitsu — typically because an anime player or a ratings API speaks a different id system. Also use when a mapped title plays the wrong show, when a title "is supported" but plays nothing, or when season/episode numbers don't line up between two catalogues.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [id-mapping, tmdb, imdb, myanimelist, anilist, anime]
    related_skills: [streaming-provider-embeds, tmdb-metadata, movie-catalogue-site]
---

# media-id-mapping

## Overview

Bridge a title's identity across catalogues: TMDB ↔ IMDb ↔ TVDB ↔ MyAnimeList ↔ AniList ↔ Kitsu. You need this the moment a consumer speaks a different id system than your metadata spine — an anime embed host keyed on MAL ids, a ratings API keyed on IMDb ids, a tracker keyed on AniList ids.

This is where **silent failure** does its worst work. A wrong id does not 404. It plays a completely different show, at full quality, with no warning, and the viewer blames your site. The hard part is not even the id — it is the **episode number**, which does not carry over between systems and cannot be computed arithmetically.

## The Invariant

**Never guess an id.** Every ambiguous or partial case resolves to `null`, and the caller falls back to a route that does not need the mapping — or says plainly that it cannot play this title.

A fallback is always available. A wrong show is not recoverable.

## When to Use

- An embed host, tracker, or API needs MAL/AniList/Kitsu/TVDB/IMDb ids and you hold TMDB ids.
- A mapped title plays the wrong show, or plays nothing while appearing supported.
- Season/episode numbers disagree between two catalogues.
- You're choosing a mapping dataset and need to know which ones actually bridge what.
- You're about to ship a derived/inferred id and need a way to prove it is right.

## Workflow

1. **Get the free ids first.** TMDB's `/{movie,tv}/{id}?append_to_response=external_ids` already returns `imdb_id` and `tvdb_id`. No dataset needed for those — see The Easy Half.
2. **Pick a dataset that carries *your* spine's ids** (see Where Mapping Data Comes From). An excellent anime database that omits TMDB ids cannot bridge TMDB to anything.
3. **Snapshot it at build time**, trimmed to the fields you need (see Build-Time, Not Runtime).
4. **Write the resolver as a pure function** over an already-loaded snapshot, so it can be exercised with no async plumbing.
5. **Handle the cour/offset problem explicitly** (see Episode Numbering).
6. **Derive only where the data admits exactly one reading**, never where two are possible (see Derive, Then Verify).
7. **Verify derived rows against the live consumer** and compare their hit rate to your existing baseline. Ship the verifier alongside the builder.
8. **Track availability separately from existence** (see Availability Is Not Existence).
9. **Return `null` loudly** — the caller must render an honest dead end, not an empty frame.

## The Easy Half: IMDb and TVDB

TMDB gives you these directly; there is no dataset, no matching, and no ambiguity:

```js
const details = await tmdbFetch(`/${mediaType}/${id}`, {
  append_to_response: 'external_ids,credits',
});
const imdbId = details.external_ids?.imdb_id;   // "tt0137523"
const tvdbId = details.external_ids?.tvdb_id;   // 81189
```

IMDb ids are what OMDb keys on for Rotten Tomatoes / Metacritic ratings (see `tmdb-metadata`). TVDB ids matter here for a second reason: they are a **secondary bridge** into anime datasets, because a meaningful minority of series carry a TVDB id in those datasets but no TMDB id.

Movies have `imdb_id` on the detail response. TV series have it under `external_ids`, and individual *episodes* have their own — don't reuse the series id for an episode lookup.

## Where Mapping Data Comes From

Datasets differ in what they bridge, and picking the wrong one wastes a day:

| Dataset kind | Bridges | Use for |
|---|---|---|
| Cross-id list carrying your metadata API's ids | TMDB/TVDB ↔ MAL/AniList/Kitsu, with `season` + `episode_offset` | **the actual bridge** |
| Anime-only aggregators | MAL ↔ AniList ↔ Kitsu ↔ AniDB | enriching, not bridging |
| Id caches / existence lists | which ids exist at all | validation only |

The publicly maintained cross-id lists (e.g. the `Fribb/anime-lists` family, which the reference implementation snapshots from `anime-list-mini.json`) are the first category — they carry `mal_id`, `anilist_id`, `kitsu_id`, `anidb_id`, `themoviedb_id`, `thetvdb_id`, plus **`season`** and **`episode_offset`**, which are the two fields that actually matter.

**Check the dataset carries your spine's ids before adopting it.** This is the single most common wasted afternoon in this domain.

## Episode Numbering Does Not Carry Over

MAL files a long-running series as **one entry per cour** (a quarter-season broadcast block). So "season 3, episode 13" of a series may be a *different MAL entry starting again at episode 1* — not entry X at episode 38, and not entry Y at episode 13. Neither conversion is arithmetic; both come from the dataset's `season` and `episode_offset` fields.

Given rows shaped `[foreignId, season, episodeOffset, type]`:

```js
function pickSeriesRow(rows, season, episode) {
  if (!Array.isArray(rows)) return null;
  let best = null;
  for (const row of rows) {
    if (row[1] !== season) continue;
    // A cour's offset is how many episodes of this season came BEFORE it, so it
    // must be strictly below the episode asked for. Among the cours that
    // qualify, the latest-starting one contains this episode.
    if (row[2] >= episode) continue;
    if (!best || row[2] > best[2]) best = row;
  }
  return best;
}

const absoluteEpisode = episode - row[2];
if (!Number.isInteger(absoluteEpisode) || absoluteEpisode <= 0) return null;
```

### Verify the model, don't inherit it

Consumers map foreign ids onto **their own** catalogue's grouping, which usually matches the source's cour splits but not always.

A worked case: one series appeared to prove a host merged cours — its season-3 entry served 22 episodes (both cours) while the second cour's entry did not exist at all. That looks like a rule. Tested across 16 multi-cour seasons where the two models disagree, the **per-cour model won 10–0**. The merged case was a genuine per-title exception, not an arithmetic rule.

Had that been "fixed" as a rule it would have broken every correctly-mapped multi-cour series. **Test a model against a sample before adopting it**, and leave per-title exceptions to the runtime fallback rather than special-casing them in the resolver.

## Snapshot Strictness Rules

Each of these exists to prevent a silent mis-play. Enforce them in the builder, and log how many rows each one dropped:

1. **Never cross-read numbering systems.** TMDB-keyed rows read `season.tmdb` / `episode_offset.tmdb` only; TVDB-keyed rows read the `tvdb` variants only. These genuinely disagree in real datasets — in one snapshot, 38 rows had differing season numbers and 7 had differing offsets. Cross-reading mis-maps exactly those rows.
2. **A row with an offset object but no value for your route is dropped, not defaulted to 0.** Defaulting turns "S3E13 → episode 1" into "→ episode 13".
3. **A `(series, season, offset)` slot claimed by several different foreign ids is dropped entirely.** There is no non-guessing way to choose.
4. **A row enters the TVDB index only when it carries no TMDB id of its own**, and the resolver consults that index only when the TMDB route found nothing — so the TMDB route always wins and the two indexes can never contradict each other.
5. Movies are a separate, simpler index: one entry, episode 1.

## Derive, Then Verify

Source datasets have holes. Some rows carry your spine's series id but omit the season number, and a strict builder drops them — silently.

Worked example: a major long-running series had its two *films* mapped and its **entire 148-episode run unmapped**, because its row omitted a season. The title looked supported and played nothing — the worst failure shape available, because it invites you to debug the player.

**Recovery rule.** Derive a season only where the data admits exactly one reading: the series has *exactly one* non-film row in the whole dataset. One entry with no cour split means season 1, offset 0 is the only arrangement the data can describe. Two or more rows are genuinely ambiguous and stay dropped.

That is a derivation, not a guess — and the difference is testable:

```
recovered rows:        47/63 resolve (74.6%)
existing map baseline:            73.6%
```

Matching the baseline is the evidence. Derived ids that were *wrong* would resolve at a visibly different rate — near zero if the rule were broken, suspiciously high if it were selecting only easy cases. A distribution matching the population says the rule found real rows, not plausible noise.

**Ship a repeatable verifier alongside the builder** so the next dataset refresh is re-checked rather than re-argued:

```
node scripts/verify-map.mjs              # deterministic sample of N entries
node scripts/verify-map.mjs --id 11061   # one specific id
node scripts/verify-map.mjs --n 200      # bigger sample
```

The verifier probes the **live consumer** — the thing that will actually serve these ids — with the embed-shaped headers that consumer requires (see `streaming-provider-embeds`), and it must use a control probe: a real id and a bogus one, so a total-failure result can't be mistaken for a coverage number. Keep the referer configurable (`PROBE_REFERER`) rather than baking a deployment hostname into a file that may go public.

## Availability Is Not Existence

"We carry this show" and "we carry it dubbed" are different facts. Conflating them makes a track selector dishonest: it offers every track on every mapped title and plays nothing for the ones that exist in only one.

Measured on one catalogue: of 8,732 titles, **5,155 were sub-only** — 59% of the titles where a dub button was being offered.

If the consumer's catalogue publishes per-track counts, harvest them during a walk you are already doing and store `[subCount, dubCount]` per id.

**Unknown is not unavailable.** A title absent from the catalogue may still play via the id route, so missing data must leave every track enabled. Disabling on absent data removes a working option on a guess — the same sin as guessing an id, pointed the other way.

```js
export function availabilityFromMap(avail, id) {
  const row = avail?.[id];
  if (!Array.isArray(row)) return null;          // null = unknown, NOT unavailable
  const sub = Number(row[0]) || 0;
  const dub = Number(row[1]) || 0;
  return { sub, dub, hasSub: sub > 0, hasDub: dub > 0 };
}
```

## Build-Time, Not Runtime

Mapping datasets are large (the upstream file in the reference case is ~5.7 MB of JSON) and their hosts rarely send CORS headers, so the browser cannot fetch them directly. Snapshot at build time, trimmed: drop every field the consumer doesn't need, drop every row without a foreign id, and re-shape into per-id buckets. That took ~5.7 MB to roughly 190 kB in the reference implementation — small enough to commit and lazily load.

Two placements, and the difference matters:

- **Bundled import** (`import('../data/map.json')`) — the build *fails* if the file is missing. Right for data the app cannot work without. Bundlers resolve dynamic imports at build time, so even `import()` inside a `try/catch` hard-fails a missing file.
- **Fetched from a static path at runtime** (`fetch(\`${import.meta.env.BASE_URL}map.json\`)`) — a missing file degrades to "no mapping" and the app still runs. Right for anything optional.

Getting this backwards means an optional enrichment file can break your build.

Memoise both the parsed result **and the in-flight promise**, so two components mounting at once share one request. On failure, clear the promise (so a later attempt can retry) and let the caller treat it exactly like an unmapped title.

**Refresh is manual and that is the safe direction.** A stale snapshot means a genuinely new show fails to resolve and the caller falls back — not that it plays the wrong thing. Record a `meta.generated` timestamp in the output so "why won't this new show resolve" has a one-line answer.

## Deciding When a Mapping Is Even Wanted

Only mention an *absent* mapping when it would make sense to have one. TMDB has no "is this anime" flag; the working heuristic — genre 16 (Animation) **combined with** Japanese original language — is the same filter `/discover` uses to build an anime rail:

```js
export function looksLikeAnime(details) {
  const isAnimation = (details?.genres || []).some((g) => g.id === 16);
  return isAnimation && details?.original_language === 'ja';
}
```

Genre alone pulls in every Western animated film. Use both, always, and use this only to decide whether "no mapping for this title" is worth saying out loud — a live-action film shouldn't be told it has no anime mapping.

## Common Pitfalls

1. **Guessing an id from a title-string match.** Join on ids alone. Title matching across catalogues produces confident wrong answers on every remake, sequel, and localised title.
2. **Treating episode numbering as arithmetic.** `episode - 12` is not a cour offset; the dataset's field is.
3. **Adopting a dataset that doesn't carry your spine's ids.** It cannot bridge, however complete it is.
4. **Defaulting a missing offset to 0.** Silently shifts an entire season.
5. **Special-casing a per-title exception as a rule.** Breaks every correctly-mapped series.
6. **Shipping a derived id without a hit-rate comparison.** The comparison is the only evidence you have.
7. **Disabling a track on unknown availability.** Removes a working option on a guess.
8. **Bundling an optional file with a static import.** A missing optional artifact fails the build.
9. **Probing the consumer without embed headers.** Everything looks like a miss (see `streaming-provider-embeds`).
10. **No control case in the sweep.** A total failure and a coverage number are indistinguishable without one.

## Limitations

This skill does **not**:

- Ship or maintain a mapping dataset. It tells you which kind to pick and how to snapshot it; the data is someone else's, with their coverage and their licence.
- Map anything by title, fuzzy match, or fingerprint. Ids only.
- Cover per-episode ids beyond what the cour/offset model gives you.
- Guarantee coverage. Real mappings are partial by nature — roughly 4,100 TV series and 1,300 films resolved in the reference snapshot, and everything else legitimately doesn't.
- Handle the embed/player side of using these ids — see `streaming-provider-embeds`.
- Provide MAL/AniList *account* integration (OAuth, list sync). This is id resolution only.

## Verification Checklist

- [ ] The chosen dataset demonstrably carries your metadata API's ids (grep one known title)
- [ ] The resolver is a pure function over a loaded snapshot and is exercised without network
- [ ] A multi-cour series resolves to the right entry **and** the right episode number, checked by hand against the catalogue
- [ ] An ambiguous/absent row returns `null`, and the caller renders an honest dead end
- [ ] Derived rows verified against the live consumer, with their hit rate compared to the baseline and both numbers recorded
- [ ] The verifier run includes a control probe (real id vs bogus id) that visibly differ
- [ ] Unknown availability leaves every track enabled
- [ ] The build still succeeds with the optional artifact deleted
- [ ] `meta.generated` is present in the snapshot output
