---
name: watchlist-sync
description: Use when adding per-profile watchlists, watch statuses, continue-watching, or resume-position tracking to a media catalogue app — or when designing the Postgres/PostgREST schema, profile switching, PIN/password gates, or a watch-stats page behind one. Also use when a stats number looks plausible but wrong, when a login endpoint has no brute-force limit, or when a preference needs to be per-device rather than per-account.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [watchlist, postgrest, postgres, profiles, auth, playback-progress]
    related_skills: [movie-catalogue-site, streaming-provider-embeds, movie-night-calendar, tmdb-metadata]
---

# watchlist-sync

## Overview

Per-profile watchlists, statuses, continue-watching, and resume points for a catalogue app — on Postgres plus a REST layer generated from the schema (PostgREST/Supabase), with **no bespoke API server** to write or maintain.

The persistence itself is easy. What makes this skill worth having is the three places it goes quietly wrong: a credential table that is one `GRANT` away from being public, an auth function that is an unlimited guessing oracle, and a resume-position column that produces confidently wrong statistics when summed.

## When to Use

- Adding a watchlist, watch statuses, ratings, or notes to a catalogue app.
- Adding "Continue Watching" or resume-where-you-left-off.
- Designing profiles, profile switching, or a PIN/password gate.
- Building a watch-stats page.
- Reviewing an existing PostgREST schema for exposure.

Do not use it for playback event capture itself (`streaming-provider-embeds`) or for the browse/detail UI (`movie-catalogue-site`).

## Workflow

1. **Write migration 001** — profiles, a shared titles cache, watchlist (see Schema). Numbered, forward-only SQL applied in order.
2. **Expose a view, never the credential table** (see Never Expose the Credential Table).
3. **Put credential comparison inside the database** as `SECURITY DEFINER` functions (see Auth as Database Functions).
4. **Rate-limit those functions before shipping them**, not after (see Rate-Limit the Oracle). A grant of EXECUTE to an anonymous role is an unlimited guessing oracle otherwise.
5. **Validate every value that reaches a PostgREST query string** at the client boundary (see Filter-Param Injection).
6. **Add progress columns** and be explicit about what they mean (see The Resume-Point Trap).
7. **Decide per-setting whether it is per-account or per-device**, and say which in the UI (see Per-Device vs Per-Account).
8. **Ship the app tolerant of an unapplied migration** (see Migrations).
9. **State the perimeter honestly** in the README (see Be Honest About the Perimeter).

## Schema

```sql
CREATE TABLE profiles (
  id            SERIAL PRIMARY KEY,
  slug          TEXT UNIQUE NOT NULL,
  display_name  TEXT NOT NULL,
  username      TEXT UNIQUE,
  password_hash TEXT,
  pin_hash      TEXT,
  avatar_color  TEXT DEFAULT '#8a7cff',
  is_default    BOOLEAN NOT NULL DEFAULT FALSE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Shared cache: anything ever added to any watchlist gets one row here.
CREATE TABLE titles (
  id           SERIAL PRIMARY KEY,
  external_id  INTEGER NOT NULL,                 -- TMDB id
  media_type   TEXT NOT NULL DEFAULT 'movie',    -- 'movie' | 'tv'
  title        TEXT NOT NULL,
  image        TEXT DEFAULT '',
  release_date TEXT DEFAULT '',
  rating       NUMERIC(3,1) DEFAULT 0,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (external_id, media_type)
);

CREATE TABLE watchlist (
  id                    SERIAL PRIMARY KEY,
  profile_id            INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  title_id              INTEGER NOT NULL REFERENCES titles(id)   ON DELETE CASCADE,
  status                TEXT NOT NULL DEFAULT 'not_watched',
  rating                INTEGER NOT NULL DEFAULT 0,
  notes                 TEXT DEFAULT '',
  sort_order            INTEGER,                 -- NULL = never manually placed
  added_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_watched_at       TIMESTAMPTZ,
  last_season           INTEGER,
  last_episode          INTEGER,
  last_position_seconds INTEGER,
  last_duration_seconds INTEGER,
  UNIQUE (profile_id, title_id)
);
```

`status` is a small closed set: `not_watched`, `planning`, `watching`, `watched`, `dropped`. Validate it client-side against the same list before it is written — a garbage status persists silently and then renders as an unmatched, uncountable filter.

`UNIQUE (external_id, media_type)` matters: TMDB movie 1399 and TV 1399 are different titles.

`sort_order` with `ORDER BY sort_order ASC NULLS LAST, added_at DESC` makes manual ordering **additive** — rows never dragged keep their existing newest-first order as a group, so an untouched list looks exactly as it did before the column existed. Persist a reorder by writing the whole ordered list's indices, not by patching the moved row: positions are only meaningful relative to neighbours, and one-row writes leave gaps and ties that compound with every drag.

## Never Expose the Credential Table

The raw `profiles` row holds hashes. Expose a **view** with only public columns, grant the anonymous role access to that, and revoke it on the table.

```sql
CREATE VIEW profiles_public AS
  SELECT id, slug, display_name, avatar_color, is_default, created_at FROM profiles;

GRANT SELECT ON profiles_public TO anon;
REVOKE SELECT ON profiles FROM anon;
```

A Postgres view runs with its owner's privileges by default, which is exactly what lets `anon` read the view without ever holding `SELECT` on the table underneath.

Every later table that grows a sensitive column follows the same pattern. **A new column on an exposed table inherits that table's grants** — convenient, and precisely how a sensitive field gets published by accident. Check what a new column is exposed to before adding it.

The same split works for write-only feedback tables (e.g. "report a broken source"): grant `INSERT` to `anon`, give it no `SELECT` policy at all, and expose only aggregate views that omit `profile_id`. Send `Prefer: return=minimal` on the insert so PostgREST never needs a SELECT grant just to echo the row back.

## Auth as Database Functions

Compare hashes **in the database**, never in the client:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION verify_login(p_username TEXT, p_password TEXT)
RETURNS TABLE (id INT, slug TEXT, display_name TEXT, avatar_color TEXT)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  RETURN QUERY
  SELECT p.id, p.slug, p.display_name, p.avatar_color
  FROM profiles p
  WHERE p.username = lower(trim(p_username))
    AND p.password_hash IS NOT NULL
    AND p.password_hash = crypt(p_password, p.password_hash);
END;
$$;

GRANT EXECUTE ON FUNCTION verify_login(TEXT, TEXT) TO anon;
```

`SECURITY DEFINER` lets the function read a table the caller cannot; the hash never leaves the database. `SET search_path = public` is not optional — without it a caller-controlled search path can shadow the objects the function references.

## Rate-Limit the Oracle

A four-digit PIN is 10,000 combinations, and profile ids are enumerable through the public view. An unmetered `verify_pin` grant to `anon` is a complete takeover in minutes. Add a failure counter and **evaluate the lock before touching a hash**.

```sql
CREATE TABLE auth_attempts (
  scope           TEXT        NOT NULL CHECK (scope IN ('pin','login')),
  identity        TEXT        NOT NULL,          -- truncate to 128 chars at the caller
  failed_count    INTEGER     NOT NULL DEFAULT 0,
  first_failed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  locked_until    TIMESTAMPTZ,
  PRIMARY KEY (scope, identity)
);
-- No grants to anon. RLS on. service_role policy only. No view over it.
```

Five design points, each load-bearing:

1. **The lock is evaluated first and short-circuits.** While locked, the response is a constant function of the submitted credential — a right PIN and a wrong PIN produce byte-identical responses, so a locked request carries zero bits about the secret. Check the credential first and the lock second and the oracle stays fully intact.
2. **Count failures against the identity *as supplied*, resolved or not.** A username that never existed locks out exactly like a real one, so "locked" is not an existence oracle.
3. **"Locked" may safely be distinguishable from "wrong credential."** It tells the attacker only that they just made five failed attempts — a fact they already hold. A silent lock lies to the legitimate user staring at a PIN box that stopped working.
4. **Run exactly one bcrypt on every path** — the real comparison when the identity resolves, a throwaway hash when it doesn't. Short-circuiting inside the `WHERE` clause means "no such username" skips hashing and returns measurably faster than "wrong password", leaking existence by timing. Split the lookup from the comparison; adding a dummy hash *after* comparing gives the resolving path two hashes and makes the gap worse.
5. **Time-based, self-clearing locks.** Account lockout is inherently a denial-of-service lever; a permanent lock hands that lever to anyone. Track PIN and login scopes separately so a locked PIN never locks the owner out of full login.

Raise a distinct SQLSTATE (`PT429`) so PostgREST maps it to HTTP 429 with a JSON `message` the client already renders.

**Do not bolt the same counter onto signup.** There is no secret to guess there, the counter has no stable key (every abusive signup uses a fresh username), and a per-username lock lets anyone pre-lock a name a real person is about to register. Signup abuse is a *volume* problem — fix it with a reverse-proxy rate limit.

## Filter-Param Injection

Every value interpolated into a PostgREST **query string** needs validation at the client boundary. This is not SQL injection — PostgREST parameterises the SQL it generates — but an unvalidated value injects extra PostgREST filter syntax: additional `&` params, `or=(...)`, a different operator than `eq.`, extra `select=` columns.

```js
export const MEDIA_TYPES = Object.freeze(['movie', 'tv']);

function safeMediaType(v) {
  if (v !== 'movie' && v !== 'tv') throw new Error(`Invalid media type: ${JSON.stringify(v)}`);
  return v;
}

function safeId(v, label) {
  const n = Number(v);
  if (!Number.isInteger(n) || n <= 0) throw new Error(`Invalid ${label}: ${JSON.stringify(v)}`);
  return n;
}
```

`mediaType` comes straight off a `/title/:mediaType/:id` route, so it is fully attacker-controlled via a crafted URL. Impact may be low *today* if `anon` already holds those grants — but the moment real server-enforced auth lands, an injectable filter param silently undermines it. Validate in the data module, not in the page, so every caller inherits it.

Cross-origin fetches need `credentials: 'include'` or the browser silently drops your gate's session cookie on every API call.

## The Resume-Point Trap

`last_position_seconds` is a **resume point for the most recent play**, overwritten on every progress update.

It is *not* a running total, and not even a bound in either direction: seek back to minute 5 after watching 40 and it stores 5; skip to the credits and it stores the credits.

So a "hours watched" statistic summed from that column is **wrong** — not approximate, wrong, and confidently so. It will also look plausible, which is why it survives review.

If you build a stats page, either:

- derive only what the data honestly supports — titles marked watched, distinct calendar days with recorded playback, longest streak, ratings given — and **label each number with what it actually counts**; or
- add a per-session playback log (append-only start/stop rows), which is the schema change that makes duration answerable.

Do not quietly ship the sum. State the absence and name the fix; a page that explains what it cannot tell you is more trustworthy than one that guesses.

Related honesty: a status column records *what* happened, not *who* or *why*. "On this profile's list" is not "this person added it" when the edit PIN is shareable, and "dropped" does not distinguish a deliberate choice from an automatic tidy-up. If you want to show either, store it.

## Continue Watching and Auto-Tidy

Scope the Continue Watching rail to `status = 'watching'`, not to "anything with a `last_watched_at`". The only rows carrying a timestamp without being `watching` are ones since marked `watched` or `dropped`, and resurfacing a finished or abandoned title as "continue watching" is wrong. Rows marked `watching` by hand but never played (`last_watched_at IS NULL`) still belong — sorted to the back:

```
order=last_watched_at.desc.nullslast,added_at.desc
```

A title left in `watching` with no activity for a long time can be auto-treated as dropped. Three rules keep that honest:

- **Reading must never write.** Home is a surface anyone can land on while viewing another profile; filter stale rows out of the *display* there, and only write on the page that owns the list.
- **A failed write is not a success.** Only rows whose PATCH actually resolved may be recoloured and announced. Swallowing a rejection and still showing the row as dropped survives while the change is silent — it does not survive a banner announcing it by name.
- **"Undo" needs a column.** Store an opt-out flag (and a timestamp of when the rule fired), or the row is stale by the clock forever and the rule re-drops it on the very next visit. Both halves are needed to claim "auto-tidied": the timestamp alone keeps claiming it after the owner restored and re-dropped by hand; `status = 'dropped'` alone is the manual/automatic ambiguity the feature exists to remove.

Define derived facets by what the columns actually say. "In progress" means the row carries something you could resume from — a position greater than zero, or a stored season/episode — which cuts across statuses. Print the criterion next to the chip so it is never read as a synonym for "Watching". A position of `0` does not count: that's what an embed reports before playback has moved at all.

## Per-Device vs Per-Account

Some settings genuinely have nowhere durable to live yet — a playback source default, a theme, a rail arrangement, a stale-watching threshold. `localStorage` is a legitimate home for them **if every surface that offers the setting says so out loud**.

Key by profile inside one storage key holding a map, with `'guest'` for "no profile selected", so two people sharing a browser don't overwrite each other and the whole preference set can be inspected or cleared in one operation:

```js
const LS_PREFS = 'app_profile_prefs';   // { "3": { provider: "alpha" }, "guest": {...} }
```

Wrap reads and writes in try/catch — a locked-down browser throws on `localStorage` access, and private-mode quota failures must not take the page down; the choice just doesn't survive the reload.

Where a setting has no admin authentication to protect it, per-device is often the *more honest* option: a server-side threshold with no auth is a setting anyone who can reach the API changes for everybody, and the sentence "one person tuned this for the whole install" would be false the moment a second person opened the URL.

## Migrations

Numbered, forward-only SQL files applied in order. Two habits pay off:

**Ship the app tolerant of an unapplied migration.** Probe for the column and degrade — hide the feature, or fall back to local storage and say so in the interface:

```js
// One tiny probe per session, memoised. A 400/404 means PostgREST parsed the
// request and there is no such column — a permanent answer worth caching.
// Anything else (offline, 500, proxy hiccup) is transient: drop the memo so
// the next caller asks again rather than downgrading the schema for the whole
// page's life over one bad request.
```

Then a deploy that lands ahead of its migration is a missing feature, not a broken page.

**`NOTIFY pgrst, 'reload schema';`** at the end of every migration, or PostgREST keeps serving the old schema cache and your new column 404s for no visible reason.

## Be Honest About the Perimeter

If the anonymous role holds broad write grants — the usual arrangement for a generated REST layer — then profile login is a **UI-level gate, not server-enforced authorisation**. Anyone who can reach the API directly can write.

That is a legitimate design for a self-hosted personal site, but only if you say so, in the README and in the code comments. The real perimeter is whatever fronts the whole deployment: put a single shared gate in front of the app *and* the API so every access path — local, tunnel, public domain — passes the same check, and neither service publishes a host port of its own.

An unlinked admin route is obscurity, not a gate. If you ship one, say that on the page itself.

## Common Pitfalls

1. **Granting `SELECT` on the table that holds hashes.** One line, total exposure.
2. **Comparing credentials in the client.** The hash has to travel to do that.
3. **Unmetered auth RPCs.** 10,000 PINs fall in minutes.
4. **Checking the credential before the lock.** Leaves the oracle intact.
5. **Summing `last_position_seconds`.** Confidently wrong hours-watched.
6. **Unvalidated route params in a PostgREST filter.** Filter-param injection.
7. **Forgetting `credentials: 'include'`.** Works locally, 401s behind the gate.
8. **Forgetting `NOTIFY pgrst`.** New column invisible until a restart.
9. **A new column on an exposed table.** Inherits the table's grants silently.
10. **Reading a list mutating it.** Anyone viewing another profile's page triggers writes they didn't ask for.

## Limitations

This skill does **not**:

- Provide real row-level authorisation. The described arrangement is a UI gate plus a shared front-door; per-profile server-enforced RLS with JWTs is a larger design it deliberately doesn't fake.
- Sync across devices beyond what the database itself gives you — there is no conflict resolution, no offline queue, no CRDT.
- Import or export to Trakt, Letterboxd, MAL, or Simkl.
- Answer "how many hours have I watched" from the schema above. That needs the playback-log change it names.
- Capture playback events — that is `streaming-provider-embeds`.
- Cover Supabase Auth, OAuth, or magic links; the auth here is deliberately a small in-database password/PIN check.

## Verification Checklist

- [ ] `GET /profiles` as the anon role is refused; `GET /profiles_public` returns no hash columns
- [ ] A wrong password and a right password are both exercised **in the same test run** — a verify function that accepted everything would also pass the happy path
- [ ] Six consecutive wrong PINs return 429, and the correct PIN also returns 429 while locked (proves the lock is evaluated first)
- [ ] A locked PIN does not block username+password login for the same profile
- [ ] A crafted `mediaType` in the URL throws at the data-module boundary instead of reaching a query string
- [ ] A status change survives a reload, and a second profile cannot see the first's credentials
- [ ] Continue Watching excludes titles marked watched or dropped
- [ ] Any stats number is labelled with what it counts, and nothing is summed from `last_position_seconds`
- [ ] The app still renders with the newest migration unapplied
