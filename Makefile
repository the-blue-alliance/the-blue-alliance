.PHONY: test lint typecheck help

# Default target
help:
	@echo "Available targets:"
	@echo "  make test              - Run all tests"
	@echo "  make test ARGS='...'   - Run tests with custom arguments"
	@echo "  make lint              - Check code formatting (black + flake8)"
	@echo "  make lint ARGS='--fix' - Auto-fix formatting with black, then run flake8"
	@echo "  make typecheck         - Run ty type checker"
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
	@docker compose build tba
	docker compose run --rm lint $(ARGS)

# Run ty type checker
typecheck:
	./ops/typecheck_py3.sh
