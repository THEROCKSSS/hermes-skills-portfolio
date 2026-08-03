# movie-night-calendar

A shared scheduling calendar for a media catalogue app — a month grid of screenings, each with a host, a real title from the metadata API, a date, and a chat link.

## What it does

The agent adds the table, the month grid, the day panel, the create flow that searches your metadata API for a real title, the past/upcoming distinction, and the "something's coming up" badge in the nav.

It is a small feature with two disproportionate traps: **JavaScript date parsing that silently shifts the day**, and **permissions on a table anyone can reach**. Most of this skill is those two.

## Install

```bash
hermes skills install https://raw.githubusercontent.com/THEROCKSSS/hermes-skills-portfolio/main/skills/movie-night-calendar/SKILL.md
```

## Schema

```sql
CREATE TABLE movie_nights (
  id              SERIAL PRIMARY KEY,
  host_profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  title           TEXT NOT NULL,       -- denormalised: an event must read correctly forever
  external_id     INTEGER,             -- nullable: not every night is a catalogued title
  media_type      TEXT CHECK (media_type IN ('movie','tv')),
  poster_url      TEXT DEFAULT '',
  event_date      DATE NOT NULL,       -- a calendar day, NOT a timestamptz
  event_time      TEXT DEFAULT '',     -- free text; "8pm-ish" beats a fake instant
  description     TEXT DEFAULT '',
  chat_url        TEXT DEFAULT '',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX movie_nights_date_idx ON movie_nights (event_date);
NOTIFY pgrst, 'reload schema';
```

`event_date` is a `DATE` on purpose. A movie night is a calendar day, not an instant — storing a timestamp forces a timezone decision on a value that doesn't have one, and drags the off-by-one below into the database layer too.

## The off-by-one-day trap

```js
new Date('2026-08-02')             // parsed as UTC midnight → renders as Aug 1 west of UTC
new Date('2026-08-02T00:00:00')    // parsed as LOCAL midnight → correct
```

Per spec, a bare `YYYY-MM-DD` is UTC and a date-time without an offset is local. So every event silently shifts a day for anyone in a negative-offset timezone — and looks perfect on a developer's machine east of UTC.

```js
// Read: always append the time component.
const d = new Date(dateStr + 'T00:00:00');

// Write: never toISOString().slice(0,10) — it converts to UTC first.
function fmtDate(d) {
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}

// Compare against a normalised today, or today's events read as past all afternoon.
const today = new Date(); today.setHours(0,0,0,0);
```

## Month grid maths

```js
const firstDay    = new Date(year, month, 1).getDay();       // leading blank cells
const daysInMonth = new Date(year, month + 1, 0).getDate();  // day 0 of next month
```

`new Date(y, m+1, 0)` handles leap years for free. Fetch the month's events **once** and filter in memory — never one request per cell.

Per cell: the day number, up to ~3 event rows (title + a dot in the host's avatar colour), a `+N more` line, `today`/`past` classes, and a click handler opening the day panel. Cap the rows or one busy day stretches the grid.

Escape everything — these are user-authored strings going into `innerHTML`:

```js
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
```

And render `chat_url` with `target="_blank" rel="noopener"`. A user-supplied URL opened without `noopener` hands the opened page a reference to your window.

## Attaching a title

The create form searches your metadata API and stores three things together: the **id** (so the event deep-links into your own title page), the **title** (so it reads correctly without a lookup), and the **poster** (so the grid renders without a request per event).

Keep the id nullable. "Board games" or "whatever we feel like" is a legitimate entry, and `NOT NULL` turns that into a blocked flow.

## Permissions

Decide explicitly rather than inheriting whatever `anon` was granted:

- host may delete their own event,
- an admin/editor may delete any,
- nobody else sees a delete button.

If `anon` holds a broad `DELETE` grant, **say in the README that this is a UI gate**, not enforcement — anyone reaching the API directly can delete anything. Legitimate for a self-hosted site behind one shared front door; not legitimate to leave unstated. To make it real, move the delete behind a `SECURITY DEFINER` function that checks the caller, or behind RLS with a JWT.

Past dates: hide create, keep delete. A calendar you can't clean up fills with dead weeks.

## Upcoming badge

```js
const rows = await api(`/movie_nights?event_date=gte.${fmtDate(today)}&event_date=lte.${fmtDate(week)}`);
badge.hidden = !(rows && rows.length);
```

A bounded range query, refreshed after every create and delete — otherwise the badge disagrees with the calendar until the next reload. A failure hides the badge; it must not break the nav.

## Empty states

A month with no events says so in words, and only offers "create one from any day" when the viewer can actually create. A day panel with no events says "No movie nights planned". A failed load is visually distinct from an empty month — same three-state rule as everywhere: haven't asked, asked and empty, asked and failed.

## Honest limitations

- Sends no invitations, reminders, emails, or push notifications. It stores a link; delivery is a separate system.
- No recurrence, RSVPs, attendance, or voting on what to watch — each is its own schema.
- No iCal/Google Calendar export: a calendar day plus free-text time isn't a precise enough instant for an `.ics`.
- No synchronised playback. Watch-party sync is a different problem, and the embed hosts in `streaming-provider-embeds` publish no seek command you can rely on.
- Does not enforce permissions server-side by itself — it describes the UI gate honestly and names the two ways to make it real.
- Does not solve timezones for a distributed group; it stores a calendar day and free text rather than pretending to.

## Part of

[Hermes Skills Portfolio](https://github.com/THEROCKSSS/hermes-skills-portfolio) — empowering skills for the Hermes agent.
