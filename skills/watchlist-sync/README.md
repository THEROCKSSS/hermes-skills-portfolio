# watchlist-sync

Per-profile watchlists, watch statuses, continue-watching, and resume points for a media catalogue app — on Postgres plus a generated REST layer, with no bespoke API server.

## What it does

The agent designs and ships the persistence half of a catalogue app: schema, profile switching, a PIN/password gate that lives inside the database, and progress tracking.

The storage itself is the easy part. This skill exists for the three places it goes quietly wrong:

- a credential table one `GRANT` away from being public,
- an auth function that is an unlimited guessing oracle,
- a resume-position column that produces confidently wrong statistics when summed.

## Install

```bash
hermes skills install https://raw.githubusercontent.com/THEROCKSSS/hermes-skills-portfolio/main/skills/watchlist-sync/SKILL.md
```

## Schema

```sql
profiles      id, slug, display_name, username, password_hash, pin_hash, avatar_color, is_default
titles        id, external_id, media_type, title, image, release_date, rating   -- UNIQUE(external_id, media_type)
watchlist     id, profile_id, title_id, status, rating, notes, sort_order, added_at,
              last_watched_at, last_season, last_episode,
              last_position_seconds, last_duration_seconds                       -- UNIQUE(profile_id, title_id)
auth_attempts scope, identity, failed_count, first_failed_at, locked_until       -- no anon grants, ever
```

`status` is a closed set: `not_watched`, `planning`, `watching`, `watched`, `dropped`. `UNIQUE(external_id, media_type)` matters — movie 1399 and TV 1399 are different titles.

`sort_order` with `ORDER BY sort_order ASC NULLS LAST, added_at DESC` makes manual ordering additive: rows never dragged keep their newest-first order as a group, so an untouched list looks exactly as it did before the column existed.

## Never expose the credential table

```sql
CREATE VIEW profiles_public AS
  SELECT id, slug, display_name, avatar_color, is_default, created_at FROM profiles;
GRANT SELECT ON profiles_public TO anon;
REVOKE SELECT ON profiles FROM anon;
```

A Postgres view runs with its owner's privileges, which is exactly what lets `anon` read the view without holding `SELECT` on the table underneath.

**A new column on an exposed table inherits that table's grants.** Convenient — and precisely how a sensitive field gets published by accident.

## Auth inside the database

```sql
CREATE OR REPLACE FUNCTION verify_login(p_username TEXT, p_password TEXT)
RETURNS TABLE (id INT, display_name TEXT)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  RETURN QUERY SELECT p.id, p.display_name FROM profiles p
   WHERE p.username = lower(trim(p_username))
     AND p.password_hash IS NOT NULL
     AND p.password_hash = crypt(p_password, p.password_hash);
END; $$;
```

`SECURITY DEFINER` lets the function read a table the caller cannot — the hash never leaves the database. `SET search_path = public` is not optional.

## Rate-limit it, or it's a guessing oracle

A four-digit PIN is 10,000 combinations and profile ids are enumerable through the public view. Five design points, each load-bearing:

1. **Evaluate the lock first and short-circuit.** While locked, the response is a constant function of the submitted credential — a right PIN and a wrong PIN are byte-identical. Check the credential first and the oracle stays fully intact.
2. **Count failures against the identity as supplied**, resolved or not, so "locked" never reveals whether a profile exists.
3. **"Locked" may safely differ from "wrong credential"** — it tells the attacker only that they just failed five times, which they know. A silent lock lies to the legitimate user.
4. **Run exactly one bcrypt on every path.** Short-circuiting in the `WHERE` clause makes "no such user" measurably faster than "wrong password" — existence by timing. Split lookup from comparison; adding a dummy hash *after* comparing makes the gap worse.
5. **Time-based, self-clearing locks, scoped separately** for PIN and login, so a locked PIN never locks the owner out entirely.

Raise SQLSTATE `PT429` so PostgREST returns HTTP 429 with a JSON message the client already renders.

Do **not** bolt the same counter onto signup: there's no secret to guess, the counter has no stable key, and a per-username lock lets anyone pre-lock a name someone is about to register. Signup abuse is a volume problem — fix it at the proxy.

## Filter-param injection

Values interpolated into a PostgREST **query string** need validation at the boundary. Not SQL injection — PostgREST parameterises — but an unvalidated value injects extra filters, operators, or `select=` columns.

```js
function safeId(v, label) {
  const n = Number(v);
  if (!Number.isInteger(n) || n <= 0) throw new Error(`Invalid ${label}: ${JSON.stringify(v)}`);
  return n;
}
```

`mediaType` comes straight off `/title/:mediaType/:id`, so it's fully attacker-controlled. Validate in the data module so every caller inherits it. And send `credentials: 'include'` on cross-origin fetches or the gate's session cookie is silently dropped.

## The resume-point trap

`last_position_seconds` is a **resume point for the most recent play**, overwritten on every update. It is not a total, and not even a bound: seek back to minute 5 after watching 40 and it stores 5; skip to the credits and it stores the credits.

A "hours watched" statistic summed from it is **wrong** — not approximate, wrong, and confidently so. It also looks plausible, which is why it survives review.

Either derive only what the data supports (titles marked watched, distinct days with recorded playback, longest streak, ratings given) and label each number with what it counts — or add an append-only playback log, which is the schema change that makes duration answerable. Don't quietly ship the sum.

## Continue Watching and auto-tidy

Scope the rail to `status = 'watching'`, ordered `last_watched_at.desc.nullslast,added_at.desc`. Anything carrying a timestamp without being `watching` has since been marked watched or dropped, and resurfacing it is wrong.

Auto-tidying stale `watching` rows into `dropped` is fine if:

- **reading never writes** (Home is a page anyone can land on while viewing another profile — filter the display there, write only on the page that owns the list),
- **a failed PATCH is not reported as a success**,
- **undo has a column** — an opt-out flag plus a fired-at timestamp, or the row is stale forever and the rule re-drops it next visit.

## Per-device vs per-account

Playback source defaults, themes, rail arrangement, thresholds — `localStorage` is a legitimate home if every surface offering the setting says so. Key by profile inside one map-shaped key (with `'guest'` for none), and wrap access in try/catch: locked-down browsers throw, and private-mode quota failures must not take the page down.

Where there's no admin auth, per-device is often the *more honest* option — a server-side setting with no auth is one anyone who reaches the API changes for everybody.

## Migrations

Numbered, forward-only. End every one with `NOTIFY pgrst, 'reload schema';` or PostgREST keeps serving the old cache and your new column 404s for no visible reason.

Ship the app tolerant of an unapplied migration: probe for the column once per session, memoise a 400/404 as a permanent answer, drop the memo on anything transient. Then a deploy that lands ahead of its migration is a missing feature, not a broken page.

## Be honest about the perimeter

If `anon` holds broad write grants — the usual arrangement for a generated REST layer — profile login is a **UI gate, not server-enforced authorisation**. Anyone who can reach the API directly can write.

That's a legitimate design for a self-hosted personal site, but only if you say so. The real perimeter is a single shared gate in front of the app *and* the API, with neither publishing a host port of its own. An unlinked admin route is obscurity — if you ship one, say that on the page.

## Honest limitations

- No real row-level authorisation. It deliberately doesn't fake per-profile server-enforced RLS with JWTs.
- No cross-device conflict resolution, offline queue, or CRDT.
- No Trakt / Letterboxd / MAL / Simkl import or export.
- Cannot answer "how many hours have I watched" from this schema — it names the playback-log change that would.
- Playback event capture belongs to `streaming-provider-embeds`.
- Not a guide to Supabase Auth, OAuth, or magic links.

## Part of

[Hermes Skills Portfolio](https://github.com/THEROCKSSS/hermes-skills-portfolio) — empowering skills for the Hermes agent.
