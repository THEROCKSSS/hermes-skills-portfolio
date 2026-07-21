#!/usr/bin/env python3
"""Enrich skills-index.json with provenance (source_attribution) for all skills.

Provenance rules:
- source=new: author=Owen, origin_type=internal, origin_url="", note="Originally authored for the Hermes Skills Portfolio."
- source=generalized: trace to internal origin (from the skill's README/CONTEXT), origin_type=internal,
  origin_url="", note="Generalized from the internal <name> skill."
- source=adapted: (none currently, but if added, requires origin_type=external + origin_url)

Also fixes:
- portfolio.owner: "Alex" -> "Owen" (consistency)
- portfolio.total_skills: ensure matches skills array length
"""

import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(REPO, "skills-index.json")

# Known generalized skill origins (from CONTEXT.md and skill analysis)
GENERALIZED_ORIGINS = {
    "hallmark-readme": "Generalized from the internal hallmark frontend skill's README anti-slop rules.",
    "generate-dockerfile": "Generalized from the internal generate-dockerfile skill used in the agentsoul profile.",
    "forgejo-self-host": "Generalized from the internal soul-forgejo-access and forgejo skills used in the agentsoul profile.",
    "frontend-design-toolkit": "Generalized from the internal frontend-design-library, hallmark, and frontend-design-craft skills.",
    "docker-umbrella": "Generalized from the internal personal-docker-umbrella and docker-pages-umbrella skills.",
    "api-test-suite": "Generalized from the internal api-test-suite skill used in the agentsoul profile.",
    "skill-registry-catalog": "Generalized from the internal skill-registry-catalog skill used in the agentsoul profile.",
}


def enrich():
    with open(INDEX, "r", encoding="utf-8") as f:
        index = json.load(f)

    # Fix owner inconsistency
    if index.get("portfolio", {}).get("owner") != "Owen":
        index["portfolio"]["owner"] = "Owen"

    # Fix total_skills
    index["portfolio"]["total_skills"] = len(index["skills"])

    for skill in index["skills"]:
        name = skill["name"]
        source = skill.get("source", "new")

        # Skip if already has a populated source_attribution (object with origin_type)
        sa = skill.get("source_attribution")
        if isinstance(sa, dict) and sa.get("origin_type"):
            continue

        if source == "new":
            skill["source_attribution"] = {
                "author": "Owen",
                "origin_type": "internal",
                "origin_repo": "",
                "origin_url": "",
                "origin_note": "Originally authored for the Hermes Skills Portfolio.",
                "license": "MIT",
                "derived": False,
            }
        elif source == "generalized":
            note = GENERALIZED_ORIGINS.get(name, f"Generalized from an internal Hermes skill.")
            skill["source_attribution"] = {
                "author": "Owen",
                "origin_type": "internal",
                "origin_repo": "",
                "origin_url": "",
                "origin_note": note,
                "license": "MIT",
                "derived": True,
            }
        elif source == "adapted":
            # Adapted skills need external origin_url — but none exist yet
            # If one is added, this will flag it for manual completion
            skill["source_attribution"] = {
                "author": "",
                "origin_type": "external",
                "origin_repo": "",
                "origin_url": "",
                "origin_note": "Adapted from an external source — fill in origin_url.",
                "license": "MIT",
                "derived": True,
            }

    with open(INDEX, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    # Also copy to docs/
    import shutil
    shutil.copy2(INDEX, os.path.join(REPO, "docs", "skills-index.json"))

    print(f"Enriched {len(index['skills'])} skills with provenance")
    print(f"Fixed portfolio.owner -> Owen")
    print(f"Fixed portfolio.total_skills -> {len(index['skills'])}")


if __name__ == "__main__":
    enrich()