import json
import math
import os
import sys
from unittest.mock import MagicMock, patch

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ops.benchmark_apiv3_coldstart import (  # noqa: E402  # pyre-ignore[21]
    BenchmarkResult,
    compute_stats,
    DEFAULT_SUITE,
    format_import_time_table,
    format_results_table,
    format_suite_table,
    ImportTimeEntry,
    IterationMetrics,
    MetricSummary,
    parse_args,
    parse_import_time,
    run_benchmark,
)


def test_compute_stats_empty() -> None:
    stats = compute_stats("test", [])
    assert stats.name == "test"
    assert stats.mean == 0.0
    assert stats.median == 0.0
    assert stats.std_dev == 0.0
    assert stats.min_val == 0.0
    assert stats.max_val == 0.0


def test_compute_stats_single_value() -> None:
    stats = compute_stats("single", [42.0])
    assert stats.name == "single"
    assert stats.mean == 42.0
    assert stats.median == 42.0
    assert stats.std_dev == 0.0
    assert stats.min_val == 42.0
    assert stats.max_val == 42.0


def test_compute_stats_odd_values() -> None:
    values = [10.0, 20.0, 30.0]
    stats = compute_stats("odd", values)
    assert stats.mean == 20.0
    assert stats.median == 20.0
    assert stats.min_val == 10.0
    assert stats.max_val == 30.0
    # Sample variance: ((10-20)^2 + (20-20)^2 + (30-20)^2) / 2 = 200 / 2 = 100
    assert math.isclose(stats.std_dev, 10.0)


def test_compute_stats_even_values() -> None:
    values = [10.0, 20.0, 30.0, 40.0]
    stats = compute_stats("even", values)
    assert stats.mean == 25.0
    assert stats.median == 25.0
    assert stats.min_val == 10.0
    assert stats.max_val == 40.0


def test_parse_import_time() -> None:
    sample_output = (
        "import time: self [us] | cumulative | imported package\n"
        "import time:       100 |        100 |   _io\n"
        "import time:       350 |        600 | _frozen_importlib_external\n"
        "import time:      1500 |       3000 |   backend.api.main\n"
    )
    entries = parse_import_time(sample_output)
    assert len(entries) == 3

    assert entries[0].module == "_io"
    assert entries[0].self_time_ms == 0.1
    assert entries[0].cumulative_time_ms == 0.1

    assert entries[1].module == "_frozen_importlib_external"
    assert entries[1].self_time_ms == 0.35
    assert entries[1].cumulative_time_ms == 0.6

    assert entries[2].module == "backend.api.main"
    assert entries[2].self_time_ms == 1.5
    assert entries[2].cumulative_time_ms == 3.0


def test_parse_args_defaults() -> None:
    args = parse_args([])
    assert args.iterations == 5
    assert args.endpoint == "/api/v3/status"
    assert args.auth_key is None
    assert args.mock_auth is True
    assert args.warm_requests == 3
    assert args.profile is False
    assert args.import_time is False
    assert args.json is False


def test_parse_args_custom() -> None:
    args = parse_args(
        [
            "-n",
            "10",
            "--endpoint",
            "/api/v3/team/frc254",
            "--no-mock-auth",
            "--auth-key",
            "custom_key",
            "--profile",
            "--json",
            "--warm-requests",
            "5",
        ]
    )
    assert args.iterations == 10
    assert args.endpoint == "/api/v3/team/frc254"
    assert args.mock_auth is False
    assert args.auth_key == "custom_key"
    assert args.profile is True
    assert args.json is True
    assert args.warm_requests == 5


def test_format_results_table() -> None:
    metrics = IterationMetrics(
        iteration=1,
        subprocess_wall_time_s=0.5,
        interpreter_baseline_s=0.03,
        import_time_s=0.35,
        client_init_s=0.02,
        cold_request_s=0.08,
        warm_request_times_s=[0.005, 0.004],
        warm_request_mean_s=0.0045,
        total_cold_start_s=0.48,
        cold_overhead_s=0.0755,
        response_status=200,
        response_size_bytes=1024,
    )
    summaries = {
        "subprocess_wall_time": MetricSummary(
            "Subprocess Wall Time", 0.5, 0.5, 0.0, 0.5, 0.5
        ),
        "interpreter_baseline": MetricSummary(
            "Interpreter Baseline", 0.03, 0.03, 0.0, 0.03, 0.03
        ),
        "import_time": MetricSummary("Module Import Time", 0.35, 0.35, 0.0, 0.35, 0.35),
        "client_init": MetricSummary("WSGI Init Time", 0.02, 0.02, 0.0, 0.02, 0.02),
        "cold_request": MetricSummary("Cold Request", 0.08, 0.08, 0.0, 0.08, 0.08),
        "warm_request": MetricSummary(
            "Warm Request", 0.0045, 0.0045, 0.0, 0.0045, 0.0045
        ),
        "cold_overhead": MetricSummary(
            "Cold Overhead", 0.0755, 0.0755, 0.0, 0.0755, 0.0755
        ),
        "total_cold_start": MetricSummary(
            "Total Cold Start", 0.48, 0.48, 0.0, 0.48, 0.48
        ),
    }
    result = BenchmarkResult(
        endpoint="/api/v3/status",
        iterations=1,
        warm_requests_per_iteration=2,
        metrics_by_iteration=[metrics],
        summaries=summaries,
    )
    table = format_results_table(result)
    assert "/api/v3/status" in table
    assert "200" in table
    assert "Subprocess Wall Time" in table
    assert "Cold Request Overhead" in table


def test_format_import_time_table() -> None:
    entries = [
        ImportTimeEntry(module="flask", self_time_ms=12.5, cumulative_time_ms=50.0),
        ImportTimeEntry(module="werkzeug", self_time_ms=8.0, cumulative_time_ms=20.0),
    ]
    table = format_import_time_table(entries, top_n=10)
    assert "flask" in table
    assert "werkzeug" in table
    assert "12.50 ms" in table


def test_run_benchmark_mocked_worker() -> None:
    mock_worker_json = json.dumps(
        {
            "import_time_s": 0.3,
            "client_init_s": 0.01,
            "cold_request_s": 0.05,
            "warm_request_times_s": [0.003],
            "warm_request_mean_s": 0.003,
            "total_cold_start_s": 0.36,
            "response_status": 200,
            "response_size_bytes": 500,
        }
    )

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = f"some logs\n{mock_worker_json}\n"
    mock_proc.stderr = ""

    with patch("subprocess.run", return_value=mock_proc):
        with patch(
            "ops.benchmark_apiv3_coldstart.measure_interpreter_baseline",
            return_value=0.02,
        ):
            result = run_benchmark(
                endpoint="/api/v3/status",
                iterations=2,
                warm_requests=1,
                mock_auth=True,
            )

    assert result.iterations == 2
    assert len(result.metrics_by_iteration) == 2
    assert result.summaries["cold_request"].mean == 0.05
    assert result.summaries["warm_request"].mean == 0.003
    assert math.isclose(result.summaries["cold_overhead"].mean, 0.047)


def test_default_suite_contains_endpoints() -> None:
    assert len(DEFAULT_SUITE) >= 10
    assert "/api/v3/status" in DEFAULT_SUITE
    assert "/api/v3/team/frc254" in DEFAULT_SUITE
    assert "/api/v3/event/2024casj" in DEFAULT_SUITE
    assert "/api/v3/match/2024casj_qm1" in DEFAULT_SUITE
    assert "/api/v3/district/2024ne/events" in DEFAULT_SUITE


def test_parse_args_suite_and_endpoints() -> None:
    args_suite = parse_args(["--suite"])
    assert args_suite.suite is True
    assert args_suite.endpoints is None

    args_eps = parse_args(["--endpoints", "/api/v3/status", "/api/v3/team/frc254"])
    assert args_eps.suite is False
    assert args_eps.endpoints == ["/api/v3/status", "/api/v3/team/frc254"]


def test_format_suite_table() -> None:
    metrics = IterationMetrics(
        iteration=1,
        subprocess_wall_time_s=0.5,
        interpreter_baseline_s=0.03,
        import_time_s=0.35,
        client_init_s=0.02,
        cold_request_s=0.08,
        warm_request_times_s=[0.005],
        warm_request_mean_s=0.005,
        total_cold_start_s=0.48,
        cold_overhead_s=0.075,
        response_status=200,
        response_size_bytes=1024,
    )
    summaries = {
        "subprocess_wall_time": MetricSummary(
            "Subprocess Wall Time", 0.5, 0.5, 0.0, 0.5, 0.5
        ),
        "interpreter_baseline": MetricSummary(
            "Interpreter Baseline", 0.03, 0.03, 0.0, 0.03, 0.03
        ),
        "import_time": MetricSummary("Module Import Time", 0.35, 0.35, 0.0, 0.35, 0.35),
        "client_init": MetricSummary("WSGI Init Time", 0.02, 0.02, 0.0, 0.02, 0.02),
        "cold_request": MetricSummary("Cold Request", 0.08, 0.08, 0.0, 0.08, 0.08),
        "warm_request": MetricSummary("Warm Request", 0.005, 0.005, 0.0, 0.005, 0.005),
        "cold_overhead": MetricSummary(
            "Cold Overhead", 0.075, 0.075, 0.0, 0.075, 0.075
        ),
        "total_cold_start": MetricSummary(
            "Total Cold Start", 0.48, 0.48, 0.0, 0.48, 0.48
        ),
    }
    result = BenchmarkResult(
        endpoint="/api/v3/status",
        iterations=1,
        warm_requests_per_iteration=1,
        metrics_by_iteration=[metrics],
        summaries=summaries,
    )
    table = format_suite_table([result])
    assert "APIv3 Multi-Endpoint Coldstart Summary" in table
    assert "/api/v3/status" in table
    assert "200" in table
