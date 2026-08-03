# How submissions are reviewed

Every skill proposal gets a decision and a reason. This file says what the bar
is before you spend time on a submission, and what each outcome means.

A decline is about **a submission as written**. It is not a permanent no, and
every decline path in this repo tells you what would change the answer.

## The states

| Label | What it means | Does the thread close? |
|---|---|---|
| `skill-request` | Received. Waiting on a maintainer. | No |
| `needs-info` | Can't decide yet — something specific is missing. | No |
| `changes-requested` | Close. Specific changes needed, then it goes in. | No |
| `approved` | Accepted. A draft PR is scaffolded automatically. | Closes as converted |
| `rejected` | Declined, always with a `decline:<reason>` label. | Yes |

`needs-info` and `changes-requested` deliberately leave the thread open. They
are requests, not verdicts — push to the same branch or reply in place.

## Decline reasons

A `rejected` label is always paired with exactly one of these. The bot expands
the reason into specific guidance; the full text lives in
[`scripts/review_reasons.py`](scripts/review_reasons.py).

| Label | Short version |
|---|---|
| `decline:duplicate` | An existing skill already covers this job. |
| `decline:out-of-scope` | Not a job an agent skill should do. |
| `decline:too-narrow` | Only works for one person's setup. |
| `decline:quality` | Good idea, submission needs substantial rework. |
| `decline:licensing` | Licensing or attribution can't be resolved. |
| `decline:unverifiable` | Depends on something nobody else can check. |

If a decline arrives with no reason label, the bot says so plainly rather than
inventing a justification — ask on the thread and you'll get a real answer.

## The bar

A skill is accepted when it is:

- **Empowering** — the agent plus the skill delivers a real outcome, not a
  description of one.
- **Self-contained** — no dependency on private infrastructure, or on tools
  only the author has.
- **Runnable** — the instructions produce a working result. A tutorial, a
  reference sheet, or a list of links does not qualify.
- **Honest** — no invented metrics, no fabricated examples, no testimonials.
  This one is enforced by CI, not just by review.
- **Attributed** — adapted work names its origin and licence.

## What happens mechanically

1. You open a proposal with the **Skill request** issue form.
2. A maintainer reads it and applies one of the labels above.
3. On `approved`, [`skill-submission.yml`](.github/workflows/skill-submission.yml)
   scaffolds `skills/<name>/`, adds the index entry, regenerates the derived
   files, runs the same checks CI runs, and opens a **draft** PR for a human to
   finish. It never pushes to `main`.
4. On `rejected`, the same workflow posts the decline (issues) — or
   [`skill-review.yml`](.github/workflows/skill-review.yml) does (pull requests)
   — naming the reason and the closest existing skills.

Both workflows only ever run when a maintainer with write access applies a
label. There is no push, schedule, or comment trigger, so a submission can
never approve itself. The scaffolder fills your own words into the description
and when-to-use sections, and leaves `TODO(maintainer)` markers everywhere it
would otherwise have to invent content.

## Disagreeing

Reply on the thread. A decline is a judgement call, and judgement calls can be
argued with — particularly `decline:duplicate`, where the useful counter-argument
is a concrete task the existing skill fails at.
