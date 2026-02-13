.PHONY: test lint lint-bash typecheck sync freeze help

# Default target
help:
	@echo "Available targets:"
	@echo "  make test                       - Run all tests"
	@echo "  make test ARGS='...'            - Run tests with custom arguments"
	@echo "  make lint                       - Check code formatting (black + flake8)"
	@echo "  make lint ARGS='--fix'          - Auto-fix formatting with black, then run flake8"
	@echo "  make typecheck                  - Run pyre type checker"
	@echo "  make lint-bash                  - Check bash script formatting (shellcheck + shfmt)"
	@echo "  make lint-bash ARGS='--fix'     - Auto-fix bash formatting with shfmt"
	@echo "  make sync                       - Sync all dev dependencies via uv"
	@echo "  make freeze                     - Generate src/requirements.txt from pyproject.toml"
	@echo ""
	@echo "Examples:"
	@echo "  make test"
	@echo "  make test ARGS='src/backend/common/helpers/tests/tbans_helper_test.py'"
	@echo "  make test ARGS='src/backend/common/helpers/tests/tbans_helper_test.py::TestTBANSHelper'"
	@echo "  make test ARGS='src/ -k test_ping'"

# Sync all dev dependencies
sync:
	uv sync --group dev

# Run tests - pass ARGS for custom pytest arguments
# Examples:
#   make test
#   make test ARGS='src/backend/common/helpers/tests/tbans_helper_test.py'
#   make test ARGS='src/backend/common/helpers/tests/tbans_helper_test.py::TestTBANSHelper'
#   make test ARGS='src/backend/common/helpers/tests/tbans_helper_test.py::TestTBANSHelper::test_ping_webhook'
#   make test ARGS='src/ -k "test_ping"'
test:
ifdef ARGS
	uv run --group test ./ops/test_py3.sh $(ARGS)
else
	uv run --group test ./ops/test_py3.sh
endif

# Run linter (black + flake8)
# Use ARGS='--fix' to auto-fix formatting issues
lint:
	uv run --group lint ./ops/lint_py3.sh $(ARGS)

# Run bash linter (shellcheck + shfmt)
# Use ARGS='--fix' to auto-fix formatting issues
lint-bash:
	docker compose run --rm lint-bash $(ARGS)

# Run pyre type checker
typecheck:
	uv run --group typecheck ./ops/typecheck_py3.sh

# Generate src/requirements.txt from pyproject.toml for GAE deploys
freeze:
	uv export --no-dev --no-hashes --frozen -o src/requirements.txt
