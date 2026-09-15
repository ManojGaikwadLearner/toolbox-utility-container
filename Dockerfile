# syntax=docker/dockerfile:1

# =============================================================================
# Stage 1: builder
# Installs the toolbox package (and its dependencies) into an isolated user
# site-packages directory, which the final stage copies wholesale - leaving
# compilers and build tools behind.
# =============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY toolbox/ ./toolbox/

# Installs the package AND its console_scripts entry point (`toolbox`) into
# /root/.local/bin - this is what lets the final image's ENTRYPOINT be the
# CLI binary itself, not a Python invocation.
RUN pip install --no-cache-dir --user .


# =============================================================================
# Stage 2: test (optional - used by CI, not part of the shipped image)
# Installs dev/test dependencies on top of the builder stage and actually
# runs the test suite against the sample data. If tests fail, this build
# stage fails - a real CI gate, not just "does it build".
# =============================================================================
FROM builder AS test

COPY requirements-dev.txt ./
RUN pip install --no-cache-dir --user -r requirements-dev.txt

COPY tests/ ./tests/
COPY sample-data/ ./sample-data/

ENV PATH=/root/.local/bin:$PATH

RUN python -m pytest tests/ -v


# =============================================================================
# Stage 3: runtime (the final, shipped image)
# No server, no CMD, no EXPOSE, no HEALTHCHECK - by design. This image does
# nothing until invoked, and leaves nothing running once it's done.
# =============================================================================
FROM python:3.12-slim AS runtime

LABEL maintainer="you@example.com" \
      org.opencontainers.image.title="toolbox-container" \
      org.opencontainers.image.description="Ephemeral multi-purpose CLI utility container: CSV/JSON conversion, image resizing, file hashing, TCP wait-for, and JSON Schema linting" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/<your-username>/toolbox-container"

RUN groupadd --gid 1000 toolbox \
    && useradd --uid 1000 --gid toolbox --shell /bin/bash --create-home toolbox

WORKDIR /app

# Only the installed package + its dependencies - no compilers, no pip cache,
# no test files, no source downloads.
COPY --from=builder /root/.local /home/toolbox/.local

ENV PATH=/home/toolbox/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

RUN chown -R toolbox:toolbox /home/toolbox/.local

USER toolbox

# The image IS the CLI. `docker run --rm toolbox-container hash-files /data`
# runs exactly as if `toolbox` were installed natively on the host.
ENTRYPOINT ["toolbox"]
