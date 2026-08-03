---
name: movie-night-calendar
description: Use when a media catalogue app needs shared scheduling — a movie-night calendar, watch-party planner, a month grid of events with a host and a title attached, an upcoming-event badge, or a "who's picking this Friday" feature. Also use when calendar dates render one day off, when past events need distinguishing from upcoming, or when deciding who may delete an event.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [calendar, scheduling, movie-night, watch-party, postgrest]
    related_skills: [watchlist-sync, movie-catalogue-site, tmdb-metadata]
---

# movie-night-calendar

## Overview

A shared calendar bolted onto a catalogue app: a month grid, one row per scheduled screening, each carrying a host profile, a real title picked from the metadata API, a date and optional time, a description, and an optional chat/voice link. Plus the small things that make it feel finished — a day panel, a past/upcoming distinction, and an "there's something coming up" badge in the nav.

It is a small feature with two disproportionate traps: **JavaScript date parsing that silently shifts the day**, and **permissions on a table anyone can reach**.

## When to Use

- A catalogue app needs "movie night on Friday" scheduling shared between profiles.
- A watch-party planner, screening schedule, or club calendar over an existing title catalogue.
- Debugging a calendar that renders events one day early or late.
- Deciding who may create, edit, or delete an event.

Do not use it for personal reminders with no shared audience (a `notes` field on the watchlist row is enough), or for release-date calendars sourced from the metadata API — those are a `/discover` query with date filters, not stored events.

## Workflow

1. **Add the table and its grants** (see Schema). One migration, following the same exposed-view discipline as `watchlist-sync`.
2. **Load the month's events once**, ordered by date, and render the grid from that array — not one request per cell.
3. **Build the month grid** with the leading blanks maths (see Rendering the Month).
4. **Parse every date string with an explicit local-midnight suffix** (see The Off-By-One-Day Trap). Do this before anything else, or you will chase a rendering bug that is a parsing bug.
5. **Add the day panel**: click a cell, see that day's events, create from there with the date pre-filled.
6. **Attach a real title** by searching the metadata API in the create form and storing the id and poster alongside the free-text title (see Attaching a Title).
7. **Decide and enforce who can delete** (see Permissions), and say the rule in the UI.
8. **Add the upcoming badge** as a bounded range query (see Upcoming Badge).

## Schema

```sql
CREATE TABLE movie_nights (
  id              SERIAL PRIMARY KEY,
  host_profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  title           TEXT NOT NULL,          -- denormalised on purpose, see below
  external_id     INTEGER,                -- TMDB id, nullable: not every night is a catalogued title
  media_type      TEXT CHECK (media_type IN ('movie','tv')),
  poster_url      TEXT DEFAULT '',
  event_date      DATE NOT NULL,
  event_time      TEXT DEFAULT '',        -- free text; see the timezone note
  description     TEXT DEFAULT '',
  chat_url        TEXT DEFAULT '',        -- Discord/Matrix/Jitsi invite
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX movie_nights_date_idx ON movie_nights (event_date);
ALTER TABLE movie_nights ENABLE ROW LEVEL SECURITY;
NOTIFY pgrst, 'reload schema';
```

Three deliberate choices:

- **`title` and `poster_url` are denormalised.** An event must still read correctly when the catalogue row is gone, and a scheduled night is a historical record — it should not silently retitle itself if the metadata changes.
- **`event_date` is a `DATE`, not a `TIMESTAMPTZ`.** A movie night is a calendar day, not an instant. Storing an instant forces a timezone decision on a value that doesn't have one and reintroduces the off-by-one below at the database layer.
- **`event_time` is free text.** Storing `"8pm-ish"` honestly beats storing `20:00:00+00` and then rendering it in a timezone nobody agreed on. If you need a real instant, add a separate nullable `starts_at TIMESTAMPTZ` and say in the UI which timezone it is displayed in.

## The Off-By-One-Day Trap

This is the bug this skill exists for.

```js
new Date('2026-08-02')             // parsed as UTC midnight → renders as Aug 1 west of UTC
new Date('2026-08-02T00:00:00')    // parsed as LOCAL midnight → correct
```

A bare `YYYY-MM-DD` string is parsed by the ECMAScript spec as **UTC**, while a date-time string without an offset is parsed as **local**. So every event silently shifts a day for anyone in a negative-offset timezone — and looks perfect on the developer's machine if they happen to be east of UTC.

Two rules, applied everywhere:

```js
// Read: always append the time component.
const dateObj = new Date(dateStr + 'T00:00:00');

// Write: never use toISOString().slice(0,10) — that converts to UTC first
// and shifts the day back for anyone in a negative offset.
function fmtDate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}
```

Compare against a *normalised* today, or every event dated today counts as past from 00:00:01 onward:

```js
const today = new Date();
today.setHours(0, 0, 0, 0);
const isPast = new Date(dateStr + 'T00:00:00') < today;
```

## Rendering the Month

Fetch once, filter in memory:

```js
const events = await api('/movie_nights?order=event_date.asc');
```

Then the grid maths, which is three lines and easy to get subtly wrong:

```js
const firstDay    = new Date(year, month, 1).getDay();      // 0=Sun leading blanks
const daysInMonth = new Date(year, month + 1, 0).getDate(); // day 0 of next month = last of this
```

`new Date(y, m + 1, 0)` is the idiomatic "days in month" and handles leap years for free. Emit `firstDay` empty cells before day 1, then one cell per day carrying:

- the day number,
- up to ~3 event rows (title plus a dot in the host's avatar colour), then a `+N more` line,
- `today` and `past` classes,
- a `data-date` attribute and a click handler opening the day panel.

Cap the events shown per cell. A day with nine events must not stretch the row and break the grid.

**Escape every interpolated string.** These are user-authored titles and descriptions going into `innerHTML`. The one-liner that actually works:

```js
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
```

And render `chat_url` links with `target="_blank" rel="noopener"` — a user-supplied URL opened without `noopener` hands the opened page a reference to your window.

## Attaching a Title

The create form searches the metadata API (see `tmdb-metadata`) and stores the chosen result's id, display title, and poster path together. Store all three:

- the **id** so the event can deep-link into your own title page,
- the **title** so the event reads correctly without a lookup,
- the **poster** so the grid and day panel render without a metadata request per event.

Keep `external_id` nullable. Not every movie night is a catalogued title — "board games" or "whatever we feel like" is a legitimate entry, and a `NOT NULL` id turns that into a lie or a blocked flow.

Pre-fill the date from whichever day cell was clicked, and default it to today when the panel was opened without one.

## Permissions

A generated REST layer over Postgres gives `anon` whatever you grant, so decide this explicitly rather than inheriting it:

- **Host may delete their own event.** Compare `event.host_profile_id` against the active profile.
- **An admin/editor may delete any.** Whatever your app's edit gate is.
- **Nobody else sees a delete button.**

Be honest that this is a **UI-level gate** if `anon` holds a broad `DELETE` grant — anyone reaching the API directly can delete anything. That's a legitimate design for a self-hosted site behind a single shared front door (see `watchlist-sync`), but the README has to say so. If you want it enforced, the delete has to move behind a `SECURITY DEFINER` function that checks the caller, or behind real RLS with a JWT.

Past events are worth treating differently: hide "create" and edit affordances on a past date, but keep delete available for tidy-up. A calendar you cannot clean up fills with dead weeks.

## Upcoming Badge

A bounded range query, not a full table scan on every page load:

```js
const today = new Date(); today.setHours(0, 0, 0, 0);
const week  = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
const rows  = await api(`/movie_nights?event_date=gte.${fmtDate(today)}&event_date=lte.${fmtDate(week)}`);
badge.hidden = !(rows && rows.length);
```

Refresh it after any create or delete, or the badge disagrees with the calendar until the next reload.

Failure must hide the badge, not break the nav — wrap it and swallow.

## Empty States

- **A month with no events** says so in words ("No movie nights this month" — plus "create one from any day" only when the viewer can actually create). Never a blank grid area.
- **A day panel with no events** says "No movie nights planned", not an empty list.
- **A failed load** is distinct from an empty month. Same three-state rule as everywhere else: haven't asked, asked and empty, asked and failed.

## Common Pitfalls

1. **`new Date('2026-08-02')`.** UTC-parsed; shifts a day west of UTC. The single most likely bug in this feature.
2. **`toISOString().slice(0,10)` to write a date.** Same bug, other direction.
3. **Comparing against an unnormalised `new Date()`.** Today's events read as past all afternoon.
4. **`getMonth()` off-by-one.** It is 0-indexed; `getDate()` is not.
5. **Unbounded events per cell.** One busy day breaks the grid.
6. **Unescaped titles/descriptions in `innerHTML`.** User-authored strings.
7. **`target="_blank"` without `rel="noopener"`** on a user-supplied chat URL.
8. **A stale badge** after create/delete.
9. **`NOT NULL` on the title id.** Blocks legitimate non-catalogue nights.
10. **Storing a time as a UTC timestamp** and rendering it without saying which timezone.

## Limitations

This skill does **not**:

- Send invitations, reminders, emails, or push notifications. It stores a link; delivery is a separate system.
- Do recurrence (every Friday), RSVPs, attendance tracking, or voting on what to watch. Each is a real feature with its own schema; this is a single-row event.
- Export to iCal/Google Calendar. `event_date` + `event_time` as stored is not a precise enough instant for an `.ics` without the `starts_at` addition it names.
- Sync playback between viewers. A watch-*party* with synchronised players is a different problem entirely, and the embed hosts in `streaming-provider-embeds` publish no seek command you can rely on.
- Enforce permissions server-side by itself. It describes the UI gate honestly and names the two ways to make it real.
- Handle timezones for a distributed group. It deliberately stores a calendar day and free-text time rather than pretending to.

## Verification Checklist

- [ ] An event created for today renders on today's cell with the machine's timezone set to something **west of UTC** (this is the test that catches the parsing bug)
- [ ] Month navigation across a year boundary and into February of a leap year both render the right number of days
- [ ] A day with more than three events shows `+N more` and does not stretch the row
- [ ] A title containing `<script>` renders as text
- [ ] The delete button appears only for the host and the editor, and the rule is stated in the UI
- [ ] Creating and deleting an event both update the upcoming badge without a reload
- [ ] An empty month and a failed load render differently
- [ ] A past date offers delete but not create
