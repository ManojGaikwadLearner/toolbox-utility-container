#!/bin/bash
# This is the concrete, runnable version of the pattern described in the
# README: an app's own entrypoint blocks on `toolbox wait-for` before
# starting its real server, instead of relying on Compose's `depends_on`
# (which only waits for the `db` container to *start*, not for Postgres
# inside it to actually be accepting connections).
set -euo pipefail

echo "[example-api] Waiting for the database to become reachable..."
toolbox wait-for db:5432 --timeout 60 --interval 2

echo "[example-api] Database is up - starting the API server on :5000"
exec python app.py
