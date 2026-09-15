# toolbox-container

A single Docker image packaging five genuine, everyday CLI utilities -
demonstrating the **utility container** pattern: a container built not to
run as a persistent service, but to be invoked on demand, do one job, and
exit.

```
docker run --rm -v "$(pwd)/sample-data:/data" toolbox-container hash-files /data/csv
```

## Utility container vs. service container

| | Service container (e.g. a web server) | Utility container (this project) |
|---|---|---|
| Lifetime | Runs indefinitely (`docker run -d`) | Runs for the duration of one task, then exits |
| Typical flag | `-d` (detached, long-running) | `--rm` (remove immediately on exit) |
| `ENTRYPOINT`/`CMD` | Starts a server process that never returns | Runs a command that returns an exit code |
| Health signal | `HEALTHCHECK` polling a live port | The process's own exit code |
| Ports | `EXPOSE`, `-p` | None - there's nothing to connect to |
| Analogy | A daemon | A CLI binary, distributed as an image |

This image deliberately has **no `EXPOSE`, no `CMD`, no `HEALTHCHECK`** -
there is nothing running until you invoke it, and nothing left running
after.

## Project structure

```
toolbox-container/
├── toolbox/                   # The CLI package
│   ├── cli.py                  # argparse entrypoint, wires up subcommands
│   ├── exit_codes.py           # Shared, documented exit code constants
│   ├── logging_utils.py        # Structured JSON-lines logging to stdout
│   ├── convert_csv_json.py     # CSV <-> JSON
│   ├── resize_image.py         # Batch image resize (Pillow)
│   ├── hash_files.py           # SHA-256 manifest generation
│   ├── wait_for.py             # TCP host:port readiness gate
│   └── lint_json.py            # JSON Schema validation (jsonschema)
├── tests/                     # pytest unit tests for every subcommand
├── sample-data/               # Ready-to-run sample inputs (see below)
├── example-api/               # Concrete demo of wait-for as an orchestration gate
│   ├── Dockerfile               # FROM toolbox-container:latest
│   ├── app.py                    # Trivial stdlib HTTP server
│   └── entrypoint.sh              # Runs `toolbox wait-for db:5432` before starting
├── .github/workflows/ci.yml   # Build + real functional tests against sample data
├── Dockerfile                 # builder -> test -> runtime
├── docker-compose.yml          # toolbox (profiled) + db + api
├── pyproject.toml               # Declares the `toolbox` console script
├── requirements.txt / requirements-dev.txt
├── .dockerignore
└── .gitignore
```

## Sample data (runnable out of the box, no setup)

| Path | Purpose |
|---|---|
| `sample-data/csv/sample.csv` | Input for `convert-csv-json` |
| `sample-data/json/valid.json` | Passes `lint-json` |
| `sample-data/json/invalid.json` | **Intentionally** fails `lint-json` (wrong type, empty string, missing field) |
| `sample-data/json-schema.json` | The schema `lint-json` validates against |
| `sample-data/images/*.png` | Input for `resize-image` |

## Build

```bash
docker build -t toolbox-container:latest .
```

This builds the default `runtime` target. To also run the test suite as
part of the build (fails the build if tests fail):

```bash
docker build --target test -t toolbox-container:test .
```

## Command reference

Every subcommand accepts `--help` for the full, current list of flags.

### `convert-csv-json`

Converts CSV to JSON, or a JSON array of objects back to CSV. Direction is
inferred from file extensions.

```bash
docker run --rm -v "$(pwd)/sample-data:/data" toolbox-container:latest \
  convert-csv-json /data/csv/sample.csv /data/csv/sample.json
```

### `resize-image`

Batch-resizes every image in `--in-dir`, preserving aspect ratio, capped at
`--max-dimension` pixels.

```bash
docker run --rm -v "$(pwd)/sample-data:/data" toolbox-container:latest \
  resize-image --in-dir /data/images --out-dir /data/images-out --max-dimension 200
```

### `hash-files`

Recursively SHA-256-hashes every file in a directory and writes a
`checksums.txt` manifest.

```bash
docker run --rm -v "$(pwd)/sample-data:/data" toolbox-container:latest \
  hash-files /data/csv
```

### `wait-for`

Blocks until `host:port` accepts a TCP connection, or exits `1` after
`--timeout` seconds. See [Using `wait-for` as an orchestration gate](#using-wait-for-as-an-orchestration-gate)
below for the realistic Compose example.

```bash
docker run --rm toolbox-container:latest wait-for db:5432 --timeout 30
```

### `lint-json`

Validates every `.json` file in a directory against a JSON Schema; exits
non-zero if any file is invalid, so it can act as a CI quality gate.

```bash
docker run --rm -v "$(pwd)/sample-data:/data" toolbox-container:latest \
  lint-json /data/json --schema /data/json-schema.json
# exits 5, because sample-data/json/invalid.json is intentionally invalid
```

## Exit codes

| Code | Name | Meaning |
|---|---|---|
| 0 | `SUCCESS` | The command completed successfully |
| 1 | `TIMEOUT` / `GENERIC_ERROR` | `wait-for` timed out, or an unclassified failure elsewhere |
| 2 | `INPUT_NOT_FOUND` | A required file/directory argument doesn't exist |
| 3 | `PARSE_ERROR` | Input exists but couldn't be parsed/converted |
| 4 | `PARTIAL_FAILURE` | A batch operation succeeded for some items, failed for others |
| 5 | `VALIDATION_FAILED` | `lint-json`: one or more files failed schema validation |

This is what makes the image usable as a real pipeline component: a CI step
or shell script can branch on `$?` instead of scraping log text.

## Using `wait-for` as an orchestration gate

`docker-compose.yml` includes a realistic `db` + `api` pair. `api`'s own
image is built `FROM toolbox-container:latest` (see `example-api/Dockerfile`)
specifically so its entrypoint can call the CLI directly:

```bash
# example-api/entrypoint.sh
echo "Waiting for the database to become reachable..."
toolbox wait-for db:5432 --timeout 60 --interval 2

echo "Database is up - starting the API server on :5000"
exec python app.py
```

This solves a real orchestration problem: Compose's `depends_on` only waits
for the `db` **container** to start, not for Postgres **inside** it to
actually be accepting connections. `wait-for` closes that gap without
needing a separate init-container or a sleep hack.

Because `example-api`'s Dockerfile is `FROM toolbox-container:latest`, build
the toolbox image first:

```bash
docker compose build toolbox
docker compose build api
docker compose up -d db api
docker compose logs -f api
# -> "Waiting for the database to become reachable..."
# -> "Target is reachable" (once Postgres finishes starting)
# -> "Database is up - starting the API server on :5000"

curl http://localhost:5000
```

## Using the toolbox via Docker Compose

The `toolbox` service is in the `tools` profile, so a plain `docker compose up`
does **not** start it - it only runs as a one-off job:

```bash
docker compose build toolbox
docker compose run --rm toolbox hash-files /data/csv
docker compose run --rm toolbox lint-json /data/json --schema /data/json-schema.json
docker compose run --rm toolbox convert-csv-json /data/csv/sample.csv /data/csv/sample.json
docker compose run --rm toolbox resize-image --in-dir /data/images --out-dir /data/images-out
```

This is the point being demonstrated: the same utility image sits alongside
a real multi-service stack (`db` + `api`) without becoming part of the
running topology - it's summoned for a task and then gone.

## Running tests

**Locally:**

```bash
pip install -e .
pip install -r requirements-dev.txt
pytest tests/ -v
```

Tests for `lint-json` and `resize-image` are skipped automatically
(`pytest.importorskip`) if `jsonschema` / `Pillow` aren't installed in your
environment - they run fully once you've done the `pip install` above, and
always run inside Docker (see below).

**Inside Docker**, via the dedicated `test` build stage:

```bash
docker build --target test -t toolbox-container:test .
```

## CI/CD

`.github/workflows/ci.yml` runs on every push/PR to `main`:

1. Installs the package and runs `pytest` directly on the GitHub Actions
   runner.
2. Runs `docker build --target test` - the same test suite again, this time
   inside the actual container environment.
3. Builds the production `runtime` image.
4. **Actually invokes every subcommand** against `sample-data/` as real
   functional tests - not just "does it build":
   - `hash-files` produces a manifest
   - `convert-csv-json` produces JSON output
   - `resize-image` produces resized files
   - `lint-json` is asserted to **fail with exit code 5** because
     `invalid.json` is present
   - `wait-for` is asserted to return **0** against a reachable target and
     **1** against an unreachable one
5. Builds `example-api`, proving the toolbox image works as a base image for
   another service.

## What this demonstrates

A quick map from "concept" to "where it lives in this repo" - useful for
walking through this project in an interview.

- **Ephemeral execution** - no `CMD`, no `EXPOSE`, no `HEALTHCHECK`; the
  image does nothing until invoked and leaves nothing running afterward
  (`Dockerfile`, runtime stage).
- **`--rm` and container lifecycle hygiene** - every example uses `--rm`;
  nothing accumulates in `docker ps -a` after normal use.
- **Volumes as the only legitimate I/O channel** - every file-touching
  subcommand reads from and writes to mounted paths (`-v $(pwd)/sample-data:/data`);
  nothing is baked into the image, and the image never assumes a particular
  host path.
- **Meaningful, documented exit codes for pipeline integration** -
  `toolbox/exit_codes.py`, exercised directly by `.github/workflows/ci.yml`
  (`lint-json` → 5, `wait-for` → 0 or 1).
- **`ENTRYPOINT` as a binary, not a shell** - `pyproject.toml`'s
  `console_scripts` entry point plus `ENTRYPOINT ["toolbox"]` means
  `docker run toolbox-container <subcommand>` behaves exactly like a native
  CLI tool.
- **`wait-for` as an orchestration primitive** - `example-api/entrypoint.sh`
  is a real, runnable case of a utility container solving a real startup-race
  problem, not just a toy example in prose.
- **Multi-stage builds separating build/test/runtime concerns** -
  `builder` → `test` → `runtime` stages, each with a distinct, single
  responsibility.

## License

MIT - use this freely as a template or reference.
