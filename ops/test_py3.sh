#!/bin/bash

run_inline_tests() {
    local -a test_targets=()
    local -a pytest_args=("$@")
    local -A seen_targets=()
    local staged_src_python_count=0
    local file filename dirname base candidate

    while IFS= read -r file; do
        [ -n "$file" ] || continue

        if [[ "$file" != src/* ]]; then
            continue
        fi

        ((staged_src_python_count += 1))
        filename=$(basename "$file")

        if [[ "$file" == *_test.py || "$filename" == test_*.py ]]; then
            if [ -f "$file" ] && [ -z "${seen_targets[$file]+x}" ]; then
                seen_targets["$file"]=1
                test_targets+=("$file")
            fi
            continue
        fi

        dirname=$(dirname "$file")
        base=$(basename "$file" .py)

        candidate="${dirname}/tests/${base}_test.py"
        if [ -f "$candidate" ] && [ -z "${seen_targets[$candidate]+x}" ]; then
            seen_targets["$candidate"]=1
            test_targets+=("$candidate")
        fi

        candidate="${dirname}/tests/test_${base}.py"
        if [ -f "$candidate" ] && [ -z "${seen_targets[$candidate]+x}" ]; then
            seen_targets["$candidate"]=1
            test_targets+=("$candidate")
        fi
    done < <(git diff --cached --name-only --diff-filter=ACMR -- "*.py")

    if [ "$staged_src_python_count" -eq 0 ]; then
        echo "No staged Python files under src/ found; skipping pytest."
        return 0
    fi

    if [ "${#test_targets[@]}" -eq 0 ]; then
        echo "No staged test files or directly related tests found; skipping pytest."
        return 0
    fi

    pytest "${test_targets[@]}" "${pytest_args[@]}"
}

if [ "${1:-}" == "--inline" ]; then
    shift
    run_inline_tests "$@"
elif [ "${1:-}" == "--relevant" ]; then
    shift
    pytest --testmon --suppress-no-test-exit-code src "$@"
elif [ "$#" -ge 1 ]; then
    pytest "$@"
else
    pytest src --cov-report=xml --cov=src
fi
