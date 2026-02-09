.PHONY: test lint lint-bash help

# Default target
help:
	@echo "Available targets:"
	@echo "  make test                       - Run all tests"
	@echo "  make test ARGS='...'            - Run tests with custom arguments"
	@echo "  make lint                       - Check code formatting (black + flake8)"
	@echo "  make lint ARGS='--fix'          - Auto-fix formatting with black, then run flake8"
# 	@echo "  make typecheck                  - Run pyre type checker"
	@echo "  make lint-bash                  - Check bash script formatting (shellcheck + shfmt)"
	@echo "  make lint-bash ARGS='--fix'     - Auto-fix bash formatting with shfmt"
	@echo ""
	@echo "Examples:"
	@echo "  make test"
	@echo "  make test ARGS='src/backend/common/helpers/tests/tbans_helper_test.py'"
	@echo "  make test ARGS='src/backend/common/helpers/tests/tbans_helper_test.py::TestTBANSHelper'"
	@echo "  make test ARGS='src/ -k test_ping'"

# Run tests - pass ARGS for custom pytest arguments
# Examples:
#   make test
#   make test ARGS='src/backend/common/helpers/tests/tbans_helper_test.py'
#   make test ARGS='src/backend/common/helpers/tests/tbans_helper_test.py::TestTBANSHelper'
#   make test ARGS='src/backend/common/helpers/tests/tbans_helper_test.py::TestTBANSHelper::test_ping_webhook'
#   make test ARGS='src/ -k "test_ping"'
test:
	@docker compose build tba
ifdef ARGS
	docker compose run --rm test $(ARGS)
else
	docker compose run --rm test
endif

# Run linter (black + flake8)
# Use ARGS='--fix' to auto-fix formatting issues
lint:
	docker compose run --rm lint $(ARGS)

# Run bash linter (shellcheck + shfmt)
# Use ARGS='--fix' to auto-fix formatting issues
lint-bash:
	docker compose run --rm lint-bash $(ARGS)

# Run pyre type checker
# typecheck:
# 	docker compose run --rm typecheck
