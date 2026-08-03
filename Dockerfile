# Hermes Skills Portfolio — containerised static site.
#
# Two stages on purpose. The build stage regenerates every derived artefact and
# then runs the same gates CI runs, so an image can only be produced from a
# tree that is internally consistent. A plain `COPY docs/ /usr/share/nginx/html`
# would happily ship a docs/ that had drifted from skills-index.json — which is
# exactly the class of bug this repo already had once.

# ---------- stage 1: regenerate + verify ----------
FROM python:3.12-slim AS build
WORKDIR /src

# PyYAML is optional for the quality checker (it has a stdlib fallback), but
# installing it exercises the same path CI uses.
RUN pip install --no-cache-dir --quiet pyyaml pytest

COPY . .

RUN set -eu; \
    python scripts/generate_skill_pages.py; \
    python scripts/generate_sitemap.py; \
    python scripts/generate_feed.py; \
    python scripts/sync_site.py; \
    echo "--- gates ---"; \
    python -m pytest tests/ -q; \
    python scripts/check_content_quality.py frontmatter; \
    python scripts/check_content_quality.py metrics; \
    python scripts/check_content_quality.py tiers; \
    python scripts/normalize_install_urls.py --check; \
    python scripts/refresh_content_cache.py --check; \
    python scripts/generate_sitemap.py --check; \
    python scripts/generate_feed.py --check; \
    echo "--- site/docs parity ---"; \
    diff -r -x 'skills' site docs; \
    echo "build verified"

# ---------- stage 2: serve ----------
FROM nginx:1.27-alpine AS serve

# docs/ is what GitHub Pages publishes, so the container serves byte-identical
# bytes to production rather than a second, subtly different copy.
COPY --from=build /src/docs /usr/share/nginx/html
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf

# Two traps here, both of which report "unhealthy" while nginx serves perfectly:
#   1. This is BusyBox wget, not GNU wget — `-q --spider` is the portable form.
#   2. Use 127.0.0.1, NOT localhost. nginx listens on IPv4 (`listen 80`), while
#      `localhost` resolves to ::1 first inside the container, so the probe gets
#      "connection refused" from IPv6 and the container is restart-looped by any
#      orchestrator that trusts the healthcheck.
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -q --spider http://127.0.0.1/ || exit 1

EXPOSE 80
