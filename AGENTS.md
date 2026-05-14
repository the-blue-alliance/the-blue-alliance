# The Blue Alliance Agent Guide

## Overview
The Blue Alliance (TBA) is a FIRST Robotics Competition (FRC) data archive and scouting tool. Teams use TBA to scout for competitions, track team performance, view match results, and relive events. Built on Google App Engine with Python 3.

## Tech Stack
- **Platform**: Google App Engine (serverless, auto-scaling)
- **Framework**: Flask (web framework)
- **Templates**: Jinja2
- **Database**: Google Cloud Datastore (NoSQL)
- **Cache**: Google Cloud Memorystore (Redis)
- **Tasks**: Google Cloud Tasks (async execution)
- **Data Source**: FRC Events API
- **Testing**: pytest, pytest-cov
- **Linting**: flake8, black (formatting), pyre-check (type checking)

## Project Structure
```
src/backend/
  ├── api/              # APIv3 endpoints and handlers
  ├── web/              # Web service (user-facing pages)
  ├── tasks_io/         # I/O-bound async tasks (data fetching)
  ├── tasks_cpu/        # CPU-bound async tasks (calculations)
  ├── default/          # Default service
  └── common/
      ├── models/       # Database models
      ├── queries/      # Database query helpers
      ├── helpers/      # Business logic and utilities
      ├── manipulators/ # Database write operations
      ├── sitevars/     # Database-backed config
      ├── consts/       # Constants and enums
      └── cache/        # Caching infrastructure
docs/                   # Architecture and setup guides
ops/                    # Build, deploy, and dev scripts
```

## Architecture
- **Frontend** (web/api services): Handle HTTP requests, read from Datastore, render HTML/JSON responses
- **Backend** (tasks services): Cron-triggered jobs that fetch upstream data, compute statistics, and write to Datastore
- Services share a common Datastore database
- Aggressive caching at multiple levels (see docs/Architecture/Architecture-Caching.md)

## Key Conventions
- Python 3 (migrated from Python 2, see docs/Developing/Py2ToPy3.md)
- **All Python code must be well-typed** - use type hints and pass `pyre-check`
- **Tests must accompany every change** - no code changes without corresponding tests
- Use manipulators for all database writes
- Use queries for database reads
- Models in `common/models/` are NDB entities
- Async work via `defer()` to task queues (see docs/common/Queues-and-defer.md)
- **NEVER** modify data directly without manipulators
- Configuration via `tba_dev_config.json` for local dev

## Development Setup
**Recommended**: Use docker compose for the local dev server, and `uv` for Python tooling (tests, linting).

See docs/Setup/Setup-Guide.md for setup instructions.

```bash
# Start dev environment with docker compose (always use --build)
docker compose up --build

# Access shell in container
docker compose exec tba bash

# View logs
docker compose logs -f tba
docker compose logs -f webpack
```

## Running Python Commands
All Python dependencies are managed by `uv` and isolated in a virtual environment. Use one of these approaches:

### Via `uv run` (preferred for one-off commands)
`uv run` executes a command within the managed virtual environment, automatically syncing dependencies first if needed.

```bash
# Run a Python script with all dev dependencies available
uv run --group dev python3 script.py

# Run with a specific dependency group
uv run --group test python3 -c "import pytest; print(pytest.__version__)"
uv run --group typecheck pyre check
```

### Via `uv shell` (preferred for interactive sessions)
Activate a shell with the virtual environment so all subsequent commands use the managed Python.

```bash
# Activate the uv-managed virtual environment
source .venv/bin/activate

# Now python3 and all installed packages are available directly
python3 script.py
pytest src/backend/common/models/tests/event_test.py
```

If the `.venv` doesn't exist yet, run `make sync` first to create it and install all dependencies.

### Via `make` targets (preferred for standard workflows)
The Makefile wraps `uv run` with the correct dependency groups. Use these for all standard dev tasks:

```bash
make test               # Run all tests
make lint               # Run Python linters
make typecheck          # Run pyre type checker
make sync               # Sync/install all dev dependencies
make freeze             # Generate src/requirements.txt for GAE deploy
```

## Testing & Linting
Tests and linting use `uv` for dependency management. Dependencies are synced automatically on first `make` invocation.

**Run commands inside Docker when the container is running, otherwise run locally.** Check with `docker compose ps tba` — if the `tba` service is up, prefix commands with `docker compose exec tba`. Example:

```bash
# Container running
docker compose exec tba make test ARGS='src/backend/...'

# Container not running
make test ARGS='src/backend/...'
```

```bash
# Sync all dev dependencies explicitly
make sync

# Run all tests
make test

# Run a specific test file
make test ARGS='src/backend/common/helpers/tests/tbans_helper_test.py'

# Run a specific test class
make test ARGS='src/backend/common/helpers/tests/tbans_helper_test.py::TestTBANSHelper'

# Run a specific test method
make test ARGS='src/backend/common/helpers/tests/tbans_helper_test.py::TestTBANSHelper::test_ping_webhook'

# Run tests matching a name pattern
make test ARGS='src/ -k "test_ping"'

# Lint Python (black --check + flake8)
make lint

# Auto-fix formatting with black, then run flake8
make lint ARGS='--fix'

# Type check
make typecheck
```

## File Organization
- `*.yaml` files in `src/` define GAE services (api.yaml, web.yaml, tasks_*.yaml, cron.yaml, queue.yaml, etc.)
- Each service has a `main.py` entrypoint
- Shared code lives in `src/backend/common/`
- Legacy Python 2 code in `old_py2/` (deprecated, do not modify)

## Key Documentation
- [Architecture Overview](docs/Architecture/Architecture-Overview.md)
- [Data Model](docs/Architecture/Architecture-Data-Model.md)
- [Development Runbook](docs/Developing/Development-Runbook.md)
- [Contributing Guidelines](docs/Setup/Contributing.md)
- [Sitevars](docs/common/Sitevars.md)
- [Queues and Tasks](docs/common/Queues-and-defer.md)

## Common Workflows
- **Add new model**: Create in `common/models/`, add manipulator, add queries
- **Add API endpoint**: Create handler in `api/handlers/`, add route in `api/main.py`, update OpenAPI spec
- **Add web page**: Create handler in `web/handlers/`, template in `web/templates/`, route in `web/main.py`
- **Add async task**: Use `defer()` to enqueue, create handler in `tasks_io/` or `tasks_cpu/`
- **Add configuration**: Use Sitevar (see docs/common/Sitevars.md)
- **Update API/models**: Reflect changes in `src/backend/web/static/swagger/*.json` OpenAPI specs (api_v3.json, api_trusted_v1.json, client_v9.json), then regenerate PWA client by running `cd pwa && ./generate-api.sh`

## Tournament Structures

### FIRST Championship
At the FIRST Championship, teams are split into 8 divisions. Each division runs a full tournament to crown division Champions. Those 8 division Champions then compete in the **Championship Playoffs** on the **Einstein fields** (event type `CMP_FINALS`) to determine the overall Championship Winners.

### District Championships
Some district championships have grown large enough to split into multiple divisions (either 2 or 4, depending on the district). These divisions feed into a finals field that mirrors the Einstein structure, though it is not officially called Einstein. Not all district championships use this format — smaller ones run as a single standard tournament.

### Standard Tournament Format (pre-2023 vs. 2023+)
See [Data Idiosyncrasies](#data-idiosyncrasies) for notes on the elimination bracket format change (single-elimination BO3 before 2023, Double Elimination from 2023 onward).

### Game Manual
The 2026 FIRST Game Manual (authoritative source for tournament rules and structure) is available at:
https://firstfrc.blob.core.windows.net/frc2026/Manual/2026GameManual.pdf

If unsure about tournament structure details, consult this manual.

## Data Idiosyncrasies
FRC data has several quirks that are important to understand when working with historical records:

- **Award renames**: The Chairman's Award was renamed to the Impact Award in fall of 2022 — they are the same award. The Dean's List Award was renamed to the FIRST Leadership Award in fall of 2025 — they are the same award.
- **Award types**: FIRST has added and removed many award types over the years. Most `AwardType` values are not in active use today, but they still appear in historical records.
- **Score breakdowns**: Match score breakdowns only became available in 2015. Finer details such as foul points are unavailable for prior years.
- **Data completeness varies by era**: Event data may be fully populated, partially populated, or entirely missing. The further back in history, the less reliable the data. Rankings, alliances, match results, award data, and team lists may be partially or entirely absent on older events.
- **Reliability by year**: Data becomes more reliable around 2010. Prior to 2006, data is uncommon.
- **Elimination format**: FIRST implemented Double Elimination brackets starting in the 2023 season. Prior seasons used a single-elimination best-of-three bracket.

## Notes
- The PWA (Progressive Web App) is a separate project in `pwa/` with its own AGENTS.md
- GAE deployment via `ops/deploy/` scripts (maintainers only)
- Production data can be seeded locally (see docs/Developing/Development-Runbook.md)
- [tba-cli](https://github.com/the-blue-alliance/tba-cli) is a CLI tool for accessing TBA data via the API, useful when agents need to look at data from TBA

