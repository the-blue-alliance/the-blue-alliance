#!/usr/bin/env python3
"""Benchmark and profile the coldstart time of the TBA APIv3 service.

In serverless environments (e.g. Google App Engine Python 3.13), a cold start
occurs when a new instance is spawned to handle incoming traffic. Because Python
caches imported modules in sys.modules, measuring true cold starts requires
spawning fresh, isolated child processes for each iteration.

This script measures:
  1. Subprocess wall-clock time (process spawn -> completion).
  2. Baseline interpreter startup time (python3 -c "pass").
  3. Module import time for backend.api.main and dependencies.
  4. Test client / WSGI setup time.
  5. First request (cold request) latency through the WSGI dispatch pipeline.
  6. Subsequent (warm request) latencies to quantify cold-start overhead.
  7. Detailed module import bottlenecks via python3 -X importtime (--import-time).
  8. CPU execution bottlenecks via cProfile (--profile).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

# Ensure src directory is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


@dataclass
class IterationMetrics:
    iteration: int
    subprocess_wall_time_s: float
    interpreter_baseline_s: float
    import_time_s: float
    client_init_s: float
    cold_request_s: float
    warm_request_times_s: List[float]
    warm_request_mean_s: float
    total_cold_start_s: float
    cold_overhead_s: float
    response_status: int
    response_size_bytes: int


@dataclass
class MetricSummary:
    name: str
    mean: float
    median: float
    std_dev: float
    min_val: float
    max_val: float


@dataclass
class ImportTimeEntry:
    module: str
    self_time_ms: float
    cumulative_time_ms: float


@dataclass
class BenchmarkResult:
    endpoint: str
    iterations: int
    warm_requests_per_iteration: int
    metrics_by_iteration: List[IterationMetrics]
    summaries: Dict[str, MetricSummary]
    top_imports: Optional[List[ImportTimeEntry]] = None


def compute_stats(name: str, values: List[float]) -> MetricSummary:
    """Compute mean, median, sample standard deviation, min, and max for a metric."""
    if not values:
        return MetricSummary(
            name=name, mean=0.0, median=0.0, std_dev=0.0, min_val=0.0, max_val=0.0
        )

    n = len(values)
    mean_val = sum(values) / n
    sorted_vals = sorted(values)

    if n % 2 == 1:
        median_val = sorted_vals[n // 2]
    else:
        median_val = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0

    min_val = sorted_vals[0]
    max_val = sorted_vals[-1]

    if n > 1:
        variance = sum((x - mean_val) ** 2 for x in values) / (n - 1)
        std_dev = math.sqrt(variance)
    else:
        std_dev = 0.0

    return MetricSummary(
        name=name,
        mean=mean_val,
        median=median_val,
        std_dev=std_dev,
        min_val=min_val,
        max_val=max_val,
    )


def parse_import_time(output: str) -> List[ImportTimeEntry]:
    """Parse output from python3 -X importtime into structured entries."""
    entries: List[ImportTimeEntry] = []
    # Lines match: "import time: self [us] | cumulative | imported package"
    # Example: "import time:       354 |        608 | _frozen_importlib_external"
    pattern = re.compile(r"^import time:\s+(\d+)\s+\|\s+(\d+)\s+\|\s+(.*)$")

    for line in output.splitlines():
        match = pattern.match(line)
        if match:
            self_us = int(match.group(1))
            cum_us = int(match.group(2))
            module_name = match.group(3).strip()
            entries.append(
                ImportTimeEntry(
                    module=module_name,
                    self_time_ms=self_us / 1000.0,
                    cumulative_time_ms=cum_us / 1000.0,
                )
            )

    return entries


def measure_interpreter_baseline(iterations: int = 3) -> float:
    """Measure the baseline startup time of the bare Python interpreter."""
    times: List[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        subprocess.run(
            [sys.executable, "-c", "pass"],
            capture_output=True,
            check=True,
        )
        times.append(time.perf_counter() - t0)
    return sum(times) / len(times) if times else 0.0


def run_worker(
    endpoint: str,
    auth_key: Optional[str],
    mock_auth: bool,
    warm_requests: int,
    profile: bool,
    profile_output: Optional[str],
) -> Dict[str, Any]:
    """Execute a single cold start iteration inside the worker process."""
    t_process_start = time.perf_counter()

    profiler = None
    if profile:
        import cProfile

        profiler = cProfile.Profile()
        profiler.enable()

    if mock_auth:
        from google.appengine.ext import testbed

        tb = testbed.Testbed()
        tb.activate()
        tb.init_datastore_v3_stub()
        tb.init_memcache_stub()
        tb.init_taskqueue_stub(root_path=SRC_DIR)

    # Measure import time for backend.api.main
    t_before_import = time.perf_counter()
    from backend.api.main import app

    t_after_import = time.perf_counter()
    import_time_s = t_after_import - t_before_import

    if mock_auth:
        from backend.common.consts.auth_type import AuthType
        from backend.common.consts.comp_level import CompLevel
        from backend.common.consts.event_type import EventType
        from backend.common.models.api_auth_access import ApiAuthAccess
        from backend.common.models.district import District
        from backend.common.models.district_team import DistrictTeam
        from backend.common.models.event import Event
        from backend.common.models.event_team import EventTeam
        from backend.common.models.match import Match
        from backend.common.models.team import Team

        if not auth_key:
            auth_key = "benchmark_coldstart_key"

        ApiAuthAccess(
            id=auth_key,
            auth_types_enum=[AuthType.READ_API],
        ).put()
        team = Team(
            id="frc254",
            team_number=254,
            nickname="The Cheesy Poofs",
            name="Team 254",
            city="San Jose",
            state_prov="CA",
            country="USA",
        )
        team.put()
        district = District(
            id="2024ne",
            year=2024,
            abbreviation="ne",
            display_name="New England",
        )
        district.put()
        event = Event(
            id="2024casj",
            year=2024,
            event_short="casj",
            name="Silicon Valley Regional",
            event_type_enum=EventType.REGIONAL,
            first_code="casj",
            district_key=district.key,
        )
        event.put()
        EventTeam(
            id="2024casj_frc254",
            event=event.key,
            team=team.key,
            year=2024,
        ).put()
        DistrictTeam(
            id="2024ne_frc254",
            district_key=district.key,
            team=team.key,
            year=2024,
        ).put()
        match_alliances = {
            "blue": {
                "score": 100,
                "teams": ["frc254", "frc1678", "frc971"],
                "surrogates": [],
                "dqs": [],
            },
            "red": {
                "score": 90,
                "teams": ["frc1323", "frc581", "frc973"],
                "surrogates": [],
                "dqs": [],
            },
        }
        Match(
            id="2024casj_qm1",
            year=2024,
            event=event.key,
            comp_level=CompLevel.QM,
            match_number=1,
            set_number=1,
            team_key_names=[
                "frc254",
                "frc1678",
                "frc971",
                "frc1323",
                "frc581",
                "frc973",
            ],
            alliances_json=json.dumps(match_alliances),
        ).put()

    # Measure test client setup
    t_before_client = time.perf_counter()
    client = app.test_client()
    t_after_client = time.perf_counter()
    client_init_s = t_after_client - t_before_client

    headers = {}
    if auth_key:
        headers["X-TBA-Auth-Key"] = auth_key

    # Measure cold request latency (first HTTP dispatch)
    t_before_cold = time.perf_counter()
    cold_resp = client.get(endpoint, headers=headers)
    t_after_cold = time.perf_counter()
    cold_request_s = t_after_cold - t_before_cold

    # Measure warm requests
    warm_times: List[float] = []
    for _ in range(warm_requests):
        t_before_warm = time.perf_counter()
        client.get(endpoint, headers=headers)
        t_after_warm = time.perf_counter()
        warm_times.append(t_after_warm - t_before_warm)

    total_cold_start_s = t_after_cold - t_process_start

    if profiler:
        import pstats

        profiler.disable()
        stats = pstats.Stats(profiler, stream=sys.stderr)
        stats.sort_stats("cumulative")
        print(
            "\n=== cProfile: Top 25 Functions by Cumulative Time ===", file=sys.stderr
        )
        stats.print_stats(25)
        print("\n=== cProfile: Top 25 Functions by Total Time ===", file=sys.stderr)
        stats.sort_stats("tottime")
        stats.print_stats(25)
        if profile_output:
            stats.dump_stats(profile_output)
            print(f"Saved profile stats to {profile_output}", file=sys.stderr)

    return {
        "import_time_s": import_time_s,
        "client_init_s": client_init_s,
        "cold_request_s": cold_request_s,
        "warm_request_times_s": warm_times,
        "warm_request_mean_s": (
            sum(warm_times) / len(warm_times) if warm_times else 0.0
        ),
        "total_cold_start_s": total_cold_start_s,
        "response_status": cold_resp.status_code,
        "response_size_bytes": len(cold_resp.data),
    }


def run_benchmark(
    endpoint: str = "/api/v3/status",
    iterations: int = 5,
    warm_requests: int = 3,
    auth_key: Optional[str] = None,
    mock_auth: bool = True,
    profile: bool = False,
    profile_output: Optional[str] = None,
    import_time: bool = False,
    verbose: bool = False,
) -> BenchmarkResult:
    """Run full benchmark across multiple isolated subprocess iterations."""
    script_path = os.path.abspath(__file__)
    baseline_s = measure_interpreter_baseline()

    metrics_list: List[IterationMetrics] = []

    for i in range(1, iterations + 1):
        if verbose:
            print(f"Running iteration {i}/{iterations}...", file=sys.stderr)

        cmd = [
            sys.executable,
            script_path,
            "--worker",
            f"--endpoint={endpoint}",
            f"--warm-requests={warm_requests}",
        ]
        if mock_auth:
            cmd.append("--mock-auth")
        if auth_key:
            cmd.append(f"--auth-key={auth_key}")
        if profile and i == 1:
            cmd.append("--profile")
            if profile_output:
                cmd.append(f"--profile-output={profile_output}")

        t0 = time.perf_counter()
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        wall_time_s = time.perf_counter() - t0

        if proc.returncode != 0:
            raise RuntimeError(
                f"Worker subprocess failed with returncode {proc.returncode}:\n"
                f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
            )

        if profile and i == 1 and proc.stderr:
            print(proc.stderr, file=sys.stderr)

        # Worker prints JSON on the last line of stdout
        raw_json = proc.stdout.strip().splitlines()[-1]
        data = json.loads(raw_json)

        cold_overhead = data["cold_request_s"] - data["warm_request_mean_s"]
        metrics = IterationMetrics(
            iteration=i,
            subprocess_wall_time_s=wall_time_s,
            interpreter_baseline_s=baseline_s,
            import_time_s=data["import_time_s"],
            client_init_s=data["client_init_s"],
            cold_request_s=data["cold_request_s"],
            warm_request_times_s=data["warm_request_times_s"],
            warm_request_mean_s=data["warm_request_mean_s"],
            total_cold_start_s=data["total_cold_start_s"],
            cold_overhead_s=cold_overhead,
            response_status=data["response_status"],
            response_size_bytes=data["response_size_bytes"],
        )
        metrics_list.append(metrics)

    # Compute statistical summaries
    summaries = {
        "subprocess_wall_time": compute_stats(
            "Subprocess Wall Time",
            [m.subprocess_wall_time_s for m in metrics_list],
        ),
        "interpreter_baseline": compute_stats(
            "Interpreter Startup Baseline",
            [m.interpreter_baseline_s for m in metrics_list],
        ),
        "import_time": compute_stats(
            "Module Import Time (backend.api.main)",
            [m.import_time_s for m in metrics_list],
        ),
        "client_init": compute_stats(
            "Test Client / WSGI Init Time",
            [m.client_init_s for m in metrics_list],
        ),
        "cold_request": compute_stats(
            "Cold Request Latency (1st Request)",
            [m.cold_request_s for m in metrics_list],
        ),
        "warm_request": compute_stats(
            "Warm Request Latency (Average)",
            [m.warm_request_mean_s for m in metrics_list],
        ),
        "cold_overhead": compute_stats(
            "Cold Request Overhead (Cold - Warm)",
            [m.cold_overhead_s for m in metrics_list],
        ),
        "total_cold_start": compute_stats(
            "Total In-Process Cold Start Time",
            [m.total_cold_start_s for m in metrics_list],
        ),
    }

    # Run import time analysis if requested
    top_imports = None
    if import_time:
        if verbose:
            print("Profiling module import breakdown...", file=sys.stderr)
        import_cmd = [
            sys.executable,
            "-X",
            "importtime",
            "-c",
            "import sys; sys.path.insert(0, 'src'); import backend.api.main",
        ]
        import_proc = subprocess.run(
            import_cmd,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        all_imports = parse_import_time(import_proc.stderr)
        # Sort by self_time_ms descending
        top_imports = sorted(all_imports, key=lambda x: x.self_time_ms, reverse=True)

    return BenchmarkResult(
        endpoint=endpoint,
        iterations=iterations,
        warm_requests_per_iteration=warm_requests,
        metrics_by_iteration=metrics_list,
        summaries=summaries,
        top_imports=top_imports,
    )


def format_ms(val_seconds: float) -> str:
    """Format seconds as milliseconds string."""
    return f"{val_seconds * 1000.0:8.2f} ms"


DEFAULT_SUITE: List[str] = [
    "/api/v3/status",
    "/api/v3/team/frc254",
    "/api/v3/team/frc254/simple",
    "/api/v3/team/frc254/years_participated",
    "/api/v3/team/frc254/events",
    "/api/v3/event/2024casj",
    "/api/v3/event/2024casj/simple",
    "/api/v3/event/2024casj/teams",
    "/api/v3/event/2024casj/matches",
    "/api/v3/match/2024casj_qm1",
    "/api/v3/match/2024casj_qm1/simple",
    "/api/v3/district/2024ne/events",
]


def format_suite_table(results: List[BenchmarkResult]) -> str:
    """Format benchmark results across multiple endpoints into a summary comparison table."""
    lines: List[str] = [
        "=" * 105,
        "                          APIv3 Multi-Endpoint Coldstart Summary",
        "=" * 105,
        f"{'Endpoint':<42} {'Status':>6} {'Cold Req':>11} {'Warm Req':>11} {'Cold Overhead':>15} {'Wall Time':>13}",
        "-" * 105,
    ]
    for res in results:
        status = res.metrics_by_iteration[0].response_status
        cold_mean = res.summaries["cold_request"].mean * 1000.0
        warm_mean = res.summaries["warm_request"].mean * 1000.0
        overhead_mean = res.summaries["cold_overhead"].mean * 1000.0
        wall_mean = res.summaries["subprocess_wall_time"].mean * 1000.0
        lines.append(
            f"{res.endpoint:<42} "
            f"{status:>6} "
            f"{cold_mean:>8.2f} ms "
            f"{warm_mean:>8.2f} ms "
            f"{overhead_mean:>12.2f} ms "
            f"{wall_mean:>10.2f} ms"
        )
    lines.append("=" * 105)
    return "\n".join(lines)


def format_results_table(result: BenchmarkResult) -> str:
    """Format benchmark results into a clean CLI table."""
    first_metric = result.metrics_by_iteration[0]
    lines: List[str] = [
        "=" * 84,
        "                     APIv3 Coldstart Benchmark Results",
        "=" * 84,
        f"Target Endpoint:       {result.endpoint}",
        f"Iterations:            {result.iterations} isolated process run(s)",
        f"Warm Requests / Run:   {result.warm_requests_per_iteration}",
        f"HTTP Response:         {first_metric.response_status} ({first_metric.response_size_bytes} bytes)",
        "-" * 84,
        f"{'Phase / Metric':<36} {'Mean':>10} {'Median':>10} {'Std Dev':>10} {'Min':>10} {'Max':>10}",
        "-" * 84,
    ]

    metric_keys = [
        ("Subprocess Wall Time", "subprocess_wall_time"),
        ("  - Interpreter Baseline", "interpreter_baseline"),
        ("  - Module & App Import", "import_time"),
        ("  - WSGI / Client Init", "client_init"),
        ("Cold Request Latency (1st)", "cold_request"),
        ("Warm Request Latency (Avg)", "warm_request"),
        ("Cold Request Overhead", "cold_overhead"),
        ("Total In-Process Cold Start", "total_cold_start"),
    ]

    for label, key in metric_keys:
        summary = result.summaries[key]
        lines.append(
            f"{label:<36} "
            f"{format_ms(summary.mean):>10} "
            f"{format_ms(summary.median):>10} "
            f"{format_ms(summary.std_dev):>10} "
            f"{format_ms(summary.min_val):>10} "
            f"{format_ms(summary.max_val):>10}"
        )

    lines.append("=" * 84)
    return "\n".join(lines)


def format_import_time_table(entries: List[ImportTimeEntry], top_n: int = 20) -> str:
    """Format top slowest imports into a table."""
    lines: List[str] = [
        "",
        "=" * 84,
        f"               Top {top_n} Slowest Module Imports (via -X importtime)",
        "=" * 84,
        f"{'Module Name':<50} {'Self Time':>15} {'Cumulative':>15}",
        "-" * 84,
    ]

    for entry in entries[:top_n]:
        lines.append(
            f"{entry.module:<50} "
            f"{entry.self_time_ms:12.2f} ms "
            f"{entry.cumulative_time_ms:12.2f} ms"
        )

    lines.append("=" * 84)
    return "\n".join(lines)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Benchmark and profile coldstart latency of the APIv3 service."
    )
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=5,
        help="Number of isolated cold start iterations to run (default: 5).",
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default="/api/v3/status",
        help="API endpoint path to benchmark (default: /api/v3/status).",
    )
    parser.add_argument(
        "--endpoints",
        nargs="+",
        default=None,
        help="List of API endpoints to benchmark.",
    )
    parser.add_argument(
        "--suite",
        action="store_true",
        help="Benchmark the representative suite of diverse APIv3 endpoints.",
    )
    parser.add_argument(
        "--auth-key",
        type=str,
        default=None,
        help="Auth key to pass in X-TBA-Auth-Key header.",
    )
    parser.add_argument(
        "--mock-auth",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable local App Engine stubs with a valid test auth key (default: true).",
    )
    parser.add_argument(
        "--warm-requests",
        type=int,
        default=3,
        help="Number of subsequent warm requests to measure per iteration (default: 3).",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Run cProfile on the cold start and display top function bottlenecks.",
    )
    parser.add_argument(
        "--profile-output",
        type=str,
        default=None,
        help="Path to save cProfile .prof binary stats.",
    )
    parser.add_argument(
        "--import-time",
        action="store_true",
        help="Profile module import time breakdown using python -X importtime.",
    )
    parser.add_argument(
        "--top-imports",
        type=int,
        default=20,
        help="Number of slowest imports to show when --import-time is enabled (default: 20).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format instead of human-readable text.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output.",
    )
    parser.add_argument(
        "--worker",
        action="store_true",
        help=argparse.SUPPRESS,  # Internal flag used for child worker execution
    )
    return parser.parse_args(argv)


def _serialize_benchmark_result(
    result: BenchmarkResult, top_imports_limit: int = 20
) -> Dict[str, Any]:
    return {
        "endpoint": result.endpoint,
        "iterations": result.iterations,
        "warm_requests_per_iteration": result.warm_requests_per_iteration,
        "metrics_by_iteration": [asdict(m) for m in result.metrics_by_iteration],
        "summaries": {k: asdict(v) for k, v in result.summaries.items()},
        "top_imports": (
            [asdict(entry) for entry in result.top_imports[:top_imports_limit]]
            if result.top_imports is not None
            else None
        ),
    }


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    if args.worker:
        worker_data = run_worker(
            endpoint=args.endpoint,
            auth_key=args.auth_key,
            mock_auth=args.mock_auth,
            warm_requests=args.warm_requests,
            profile=args.profile,
            profile_output=args.profile_output,
        )
        print(json.dumps(worker_data), flush=True)
        try:
            from google.appengine.api import apiproxy_rpc

            if hasattr(apiproxy_rpc, "_THREAD_POOL") and apiproxy_rpc._THREAD_POOL:
                apiproxy_rpc._THREAD_POOL.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)

    if args.iterations < 1:
        print("Error: --iterations must be at least 1.", file=sys.stderr)
        return 1

    if args.suite:
        endpoints_to_run = DEFAULT_SUITE
    elif args.endpoints:
        endpoints_to_run = args.endpoints
    else:
        endpoints_to_run = [args.endpoint]

    results: List[BenchmarkResult] = []
    for idx, ep in enumerate(endpoints_to_run):
        if args.verbose or len(endpoints_to_run) > 1:
            print(
                f"Benchmarking [{idx + 1}/{len(endpoints_to_run)}]: {ep}...",
                file=sys.stderr,
            )
        res = run_benchmark(
            endpoint=ep,
            iterations=args.iterations,
            warm_requests=args.warm_requests,
            auth_key=args.auth_key,
            mock_auth=args.mock_auth,
            profile=args.profile,
            profile_output=args.profile_output,
            import_time=(args.import_time and idx == 0),
            verbose=args.verbose,
        )
        results.append(res)

    if args.json:
        if len(results) == 1:
            output_dict = _serialize_benchmark_result(
                results[0], top_imports_limit=args.top_imports
            )
            print(json.dumps(output_dict, indent=2))
        else:
            output_list = [
                _serialize_benchmark_result(r, top_imports_limit=args.top_imports)
                for r in results
            ]
            print(json.dumps(output_list, indent=2))
    else:
        top_imports = results[0].top_imports
        if len(results) == 1:
            print(format_results_table(results[0]))
            if top_imports is not None:
                print(format_import_time_table(top_imports, top_n=args.top_imports))
        else:
            print(format_suite_table(results))
            if top_imports is not None:
                print(format_import_time_table(top_imports, top_n=args.top_imports))

    return 0


if __name__ == "__main__":
    sys.exit(main())
