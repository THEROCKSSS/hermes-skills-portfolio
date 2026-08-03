# media-id-mapping

Bridge a title's identity across catalogues — TMDB ↔ IMDb ↔ TVDB ↔ MyAnimeList ↔ AniList ↔ Kitsu — without ever guessing an id.

## What it does

You need this the moment a consumer speaks a different id system than your metadata spine: an anime embed host keyed on MAL ids, a ratings API keyed on IMDb ids, a tracker keyed on AniList ids.

The agent picks a dataset that actually bridges what you hold, snapshots it at build time under strict rules, writes a pure resolver, and — crucially — verifies derived rows against the live consumer instead of reasoning about them.

## The invariant

**Never guess an id.** Every ambiguous or partial case resolves to `null` and the caller falls back to a route that doesn't need the mapping, or says plainly that it can't play this title.

A wrong id does not 404. It plays a completely different show, at full quality, with no warning. A fallback is always available; a wrong show is not recoverable.

## Install

```bash
hermes skills install https://raw.githubusercontent.com/THEROCKSSS/hermes-skills-portfolio/main/skills/media-id-mapping/SKILL.md
```

## The easy half — no dataset needed

```js
const details = await tmdbFetch(`/${mediaType}/${id}`, { append_to_response: 'external_ids' });
details.external_ids?.imdb_id   // "tt0137523"  → OMDb ratings
details.external_ids?.tvdb_id   // 81189        → secondary bridge into anime datasets
```

TVDB matters for a second reason: a meaningful minority of series carry a TVDB id in anime datasets but no TMDB id, so it's a real fallback route.

## Picking a dataset

| Kind | Bridges | Use for |
|---|---|---|
| Cross-id list carrying your API's ids | TMDB/TVDB ↔ MAL/AniList/Kitsu, with `season` + `episode_offset` | **the actual bridge** |
| Anime-only aggregators | MAL ↔ AniList ↔ Kitsu ↔ AniDB | enriching, not bridging |
| Id existence caches | which ids exist | validation only |

**Check the dataset carries your spine's ids before adopting it.** An excellent anime database that omits TMDB ids cannot bridge TMDB to anything, however complete it is otherwise. This is the most common wasted afternoon in this domain.

## The hard part is the episode number

MAL files a long-running series as **one entry per cour**. "Season 3, episode 13" may be a different entry starting again at episode 1 — not entry X at episode 38, and not entry Y at episode 13. Neither conversion is arithmetic.

```js
function pickSeriesRow(rows, season, episode) {
  let best = null;
  for (const row of rows || []) {
    if (row[1] !== season) continue;
    if (row[2] >= episode) continue;              // offset must be strictly below
    if (!best || row[2] > best[2]) best = row;    // latest-starting qualifying cour
  }
  return best;
}
const absoluteEpisode = episode - row[2];
```

**Verify the model, don't inherit it.** One series looked like proof that a host merged cours — season 3 served 22 episodes while the second cour's entry didn't exist. Tested across 16 multi-cour seasons where the two models disagree, the per-cour model won **10–0**. That one case was a per-title exception, not a rule; "fixing" it as a rule would have broken every correctly-mapped series.

## Snapshot strictness rules

Each prevents a silent mis-play. Log how many rows each drops:

1. **Never cross-read numbering systems** — TMDB rows read the `tmdb` season/offset, TVDB rows read the `tvdb` ones. In one real snapshot 38 rows had differing seasons and 7 differing offsets.
2. **A missing offset is dropped, not defaulted to 0.** Defaulting turns "S3E13 → ep 1" into "→ ep 13".
3. **A slot claimed by several foreign ids is dropped entirely.** No non-guessing way to choose.
4. **TVDB index is consulted only when the TMDB route found nothing**, so the two can never contradict.

## Derive, then verify

Datasets have holes. One real case: a major long-running series had its two *films* mapped and its **entire 148-episode run unmapped** because the row omitted a season. The title looked supported and played nothing — the worst failure shape available, because it invites you to debug the player.

Recovery rule: derive a season only where the data admits exactly one reading — the series has *exactly one* non-film row. Two or more rows are genuinely ambiguous and stay dropped.

Then prove it:

```
recovered rows:        47/63 resolve (74.6%)
existing map baseline:            73.6%
```

Matching the baseline is the evidence. Wrong ids would resolve at a visibly different rate — near zero if the rule were broken, suspiciously high if it were cherry-picking easy cases.

Ship the verifier next to the builder so the next refresh is re-checked rather than re-argued, and give it a control probe (real id vs bogus id) so a total failure can't be mistaken for a coverage number.

## Availability is not existence

"We carry this show" and "we carry it dubbed" are different facts. Measured on one catalogue: of 8,732 titles, **5,155 were sub-only** — 59% of the titles where a dub button was being offered.

```js
if (!Array.isArray(row)) return null;   // null = UNKNOWN, not unavailable
```

Unknown must leave every track enabled. Disabling on absent data removes a working option on a guess — the same sin as guessing an id, pointed the other way.

## Build-time, not runtime

Mapping datasets are large (~5.7 MB in the reference case) and their hosts rarely send CORS headers. Snapshot at build time, trimmed to per-id buckets — that got to ~190 kB, small enough to commit and lazily load.

- **Bundled import** → the build *fails* if the file is missing. Right for data the app can't work without. (Bundlers resolve dynamic imports at build time, so even `import()` in a try/catch hard-fails.)
- **Runtime `fetch` from a static path** → a missing file degrades to "no mapping" and the app still runs. Right for anything optional.

Getting this backwards means an optional enrichment file breaks your build. Memoise both the parsed result and the in-flight promise; clear the promise on failure so a retry is possible.

Refresh is manual, and that's the safe direction — a stale snapshot means a new show fails to resolve and falls back, not that it plays the wrong thing. Record `meta.generated` in the output.

## Is it even anime?

TMDB has no flag. The working heuristic is genre 16 (Animation) **combined with** Japanese original language — genre alone pulls in every Western animated film. Use it only to decide whether "no mapping for this title" is worth saying out loud.

## Honest limitations

- Ships no dataset. The data is someone else's, with their coverage and their licence.
- Maps by id only — no title matching, fuzzy matching, or fingerprinting.
- Coverage is partial by nature. The reference snapshot resolved roughly 4,100 TV series and 1,300 films; everything else legitimately doesn't map.
- The embed/player side of using these ids belongs to `streaming-provider-embeds`.
- No MAL/AniList *account* integration (OAuth, list sync) — this is id resolution only.
- All measured figures here are dated observations from one reference implementation, not guarantees. Re-measure.

## Part of

[Hermes Skills Portfolio](https://github.com/THEROCKSSS/hermes-skills-portfolio) — empowering skills for the Hermes agent.
