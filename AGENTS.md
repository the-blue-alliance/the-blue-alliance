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
- **Linting**: flake8, black (formatting), ty (type checking)

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
- **All Python code must be well-typed** - use type hints and pass `ty`
- **Tests must accompany every change** - no code changes without corresponding tests
- Use manipulators for all database writes
- Use queries for database reads
- Models in `common/models/` are NDB entities
- Async work via `defer()` to task queues (see docs/common/Queues-and-defer.md)
- **NEVER** modify data directly without manipulators
- Configuration via `tba_dev_config.json` for local dev

## Development Setup
**Recommended**: Use devcontainers or docker-compose for local development.

See docs/Setup/Setup-Guide-Beta.md for docker-compose or docs/Setup/Setup-Guide.md for vagrant setup.

```bash
# Start dev environment with docker-compose
docker-compose up

# Access shell in container
docker-compose exec tba bash

# Or use convenience script
./ops/shell/run_local_shell.sh
```

## Testing & Linting
Run tests via make:

```bash
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

## Notes
- The PWA (Progressive Web App) is a separate project in `pwa/` with its own AGENTS.md
- GAE deployment via `ops/deploy/` scripts (maintainers only)
- Production data can be seeded locally (see docs/Developing/Development-Runbook.md)
- [tba-cli](https://github.com/the-blue-alliance/tba-cli) is a CLI tool for accessing TBA data via the API, useful when agents need to look at data from TBA

