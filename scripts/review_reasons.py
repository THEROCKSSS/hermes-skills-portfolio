#!/usr/bin/env python3
"""Decline reasons for skill submissions, and the guidance each one carries.

Why this exists
---------------
A bare "rejected" label tells a contributor nothing. It doesn't say what was
wrong, whether it is fixable, or whether they should try again. That reads as
arbitrary, and it is the fastest way to lose the next contribution.

So a decline is always TWO labels: `rejected` plus exactly one `decline:<reason>`.
This module turns that reason into a specific explanation, a concrete "what
would change the answer", and an honest statement of whether resubmitting is
worth their time. Both the issue path and the pull-request path render from
here, so the wording can't drift between them.

Nothing here invents a judgement — the maintainer picks the reason label; this
only expands it into something actionable.
"""

from __future__ import annotations

LABEL_PREFIX = "decline:"

# reason -> (headline, why it happens, what would change the answer, resubmit?)
REASONS: dict[str, dict[str, object]] = {
    "duplicate": {
        "headline": "The catalog already covers this",
        "explain": (
            "An existing skill already does this job. Two skills that overlap "
            "make the catalog harder to search, and an agent loading both wastes "
            "context deciding between them."
        ),
        "changes_it": [
            "Show a case the existing skill genuinely cannot handle.",
            "Propose it as an improvement to the existing skill instead — open "
            "an issue against that skill, or a PR editing its `SKILL.md`.",
        ],
        "resubmit": True,
    },
    "out-of-scope": {
        "headline": "Not something an agent skill should do",
        "explain": (
            "A skill teaches an agent to do a job on the user's behalf. This "
            "proposal reads as something else — a library, a hosted service, a "
            "one-off script, or a task with no agent-shaped decision in it."
        ),
        "changes_it": [
            "Reframe it around what the *agent* decides and does, not what a "
            "tool does.",
            "If it's really a library or CLI, publishing it on its own and then "
            "proposing a thin skill that drives it is usually the better split.",
        ],
        "resubmit": True,
    },
    "too-narrow": {
        "headline": "Too specific to one setup",
        "explain": (
            "As written this only works for one person's hostnames, paths, "
            "accounts, or hardware. Someone else installing it would have to "
            "rewrite it before it did anything."
        ),
        "changes_it": [
            "Replace environment-specific values with named configuration and "
            "say where each one comes from.",
            "Describe the general job first, and keep your own setup as one "
            "worked example.",
        ],
        "resubmit": True,
    },
    "quality": {
        "headline": "The idea works, the submission doesn't yet",
        "explain": (
            "The underlying idea is fine, but the text isn't usable as-is — "
            "vague triggers, no real workflow steps, no way to tell whether it "
            "worked, or claims with nothing behind them."
        ),
        "changes_it": [
            "Make `description` state concrete trigger conditions — when should "
            "an agent reach for this, and when should it not?",
            "Give the workflow real, ordered steps with actual commands.",
            "Add a verification section: how does the agent know it succeeded?",
            "Remove any figure you cannot source. Invented metrics are the one "
            "thing this catalog refuses outright.",
        ],
        "resubmit": True,
    },
    "licensing": {
        "headline": "Licensing or attribution can't be resolved",
        "explain": (
            "This appears to be adapted from someone else's work, and the "
            "licence either forbids redistribution here or the origin can't be "
            "established. The catalog is MIT and every adapted skill has to name "
            "a real, checkable source."
        ),
        "changes_it": [
            "Supply the origin URL and its licence.",
            "If the licence is incompatible, rewriting the skill from your own "
            "understanding — not from their text — is a legitimate path.",
        ],
        "resubmit": True,
    },
    "unverifiable": {
        "headline": "Nothing here can be checked",
        "explain": (
            "The skill depends on a private endpoint, a dead link, an account "
            "nobody else can create, or a service that no longer exists. A skill "
            "nobody can run is a skill nobody can maintain."
        ),
        "changes_it": [
            "Point at something publicly reachable, or document exactly what a "
            "reader has to stand up first.",
            "Replace dead links — the weekly quality job checks every URL in "
            "the catalog and will flag them again.",
        ],
        "resubmit": True,
    },
}


def reason_from_labels(labels) -> str | None:
    """Return the reason slug from a list of label names, if exactly one is set."""
    found = [
        str(name)[len(LABEL_PREFIX):]
        for name in labels
        if str(name).startswith(LABEL_PREFIX)
    ]
    known = [r for r in found if r in REASONS]
    return known[0] if len(known) == 1 else None


def render(reason: str | None, *, subject: str = "this submission") -> str:
    """Render the markdown explanation for a decline reason.

    An unknown or missing reason yields an honest fallback rather than a
    fabricated justification — the maintainer simply didn't record one.
    """
    if reason is None or reason not in REASONS:
        return (
            "**No specific reason label was set.**\n\n"
            "A maintainer declined this without recording a `decline:<reason>` "
            "label, so there's no detail to expand here. If you'd like to know "
            "what would change the answer, reply on this thread and ask — that "
            "is a fair question and it will get an answer.\n"
        )

    r = REASONS[reason]
    out = [f"**{r['headline']}**", "", str(r["explain"]), "", "**What would change the answer**", ""]
    for item in r["changes_it"]:
        out.append(f"- {item}")
    out.append("")
    if r["resubmit"]:
        out.append(
            f"You're welcome to open a new proposal for {subject} once that's "
            "addressed — a decline is about this submission as written, not "
            "about you or the idea permanently."
        )
    return "\n".join(out) + "\n"


def all_reason_labels() -> list[str]:
    return [f"{LABEL_PREFIX}{r}" for r in sorted(REASONS)]


if __name__ == "__main__":  # tiny CLI so the workflow can shell out to it
    import argparse

    ap = argparse.ArgumentParser(description="Render a decline reason as markdown.")
    ap.add_argument("--labels", nargs="*", default=[], help="label names on the issue/PR")
    ap.add_argument("--reason", default=None, help="reason slug, bypassing label lookup")
    ap.add_argument("--subject", default="this submission")
    ap.add_argument("--list", action="store_true", help="print every reason label")
    args = ap.parse_args()

    if args.list:
        print("\n".join(all_reason_labels()))
    else:
        print(render(args.reason or reason_from_labels(args.labels), subject=args.subject))
