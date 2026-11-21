#!/usr/bin/env python3
"""Benchmark coldstart loading time and endpoint latency for TBA services.

Usage:
    uv run python3 ops/benchmark_coldstart.py
    uv run python3 ops/benchmark_coldstart.py --iterations 5
    uv run python3 ops/benchmark_coldstart.py --imports-only
    uv run python3 ops/benchmark_coldstart.py --service web
"""

import argparse
import json
import os
import statistics
import subprocess
import sys
from typing import Any, Dict, List, Tuple

DEFAULT_ENDPOINTS = [
    "/_ah/warmup",
    "/api/v3/status",
    "/api/v3/event/2026casac",
    "/api/v3/event/2026casac/matches",
    "/api/v3/event/2026casac/teams/simple",
    "/api/v3/team/frc177",
    "/api/v3/team/frc177/events/2003",
    "/api/v3/team/frc177/awards/2003",
    "/api/v3/match/2026casac_qm1",
    "/api/v3/districts/2026",
]

SERVICE_MODULES = {
    "api": "backend.api.main",
    "web": "backend.web.main",
    "tasks_io": "backend.tasks_io.main",
    "tasks_cpu": "backend.tasks_cpu.main",
}


def _get_project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _run_subprocess(args: List[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    root = _get_project_root()
    env["PYTHONPATH"] = os.path.join(root, "src")
    env["AUTH_NETLOC"] = "false"
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        env=env,
        cwd=root,
    )


def measure_import_profile(module: str, top_n: int = 10) -> Dict[str, Any]:
    """Measure module loading times using Python's -X importtime profiler."""
    cmd = [sys.executable, "-X", "importtime", "-c", f"import {module}"]
    result = _run_subprocess(cmd)

    lines = [
        line for line in result.stderr.splitlines() if line.startswith("import time:")
    ]
    records: List[Tuple[float, float, str]] = []

    for line in lines:
        parts = line.replace("import time:", "").split("|")
        if len(parts) == 3:
            try:
                self_us = int(parts[0].strip())
                cum_us = int(parts[1].strip())
                mod_name = parts[2].strip()
                records.append((self_us / 1000.0, cum_us / 1000.0, mod_name))
            except ValueError:
                continue

    slowest_self = sorted(records, key=lambda x: x[0], reverse=True)[:top_n]
    slowest_cum = sorted(records, key=lambda x: x[1], reverse=True)[:top_n]

    # Cumulative time of target module is the last entry matching the module name
    target_records = [r for r in records if r[2] == module]
    total_cum_ms = target_records[-1][1] if target_records else 0.0

    return {
        "module": module,
        "total_modules_loaded": len(records),
        "cumulative_import_ms": total_cum_ms,
        "slowest_by_self_time": [
            {"module": m, "self_ms": round(s, 2), "cum_ms": round(c, 2)}
            for s, c, m in slowest_self
        ],
        "slowest_by_cum_time": [
            {"module": m, "self_ms": round(s, 2), "cum_ms": round(c, 2)}
            for s, c, m in slowest_cum
        ],
    }


def measure_startup_latency(module: str, iterations: int = 3) -> Dict[str, Any]:
    """Measure fresh process startup time for importing the target service module."""
    code = f"""
import sys, time
t0 = time.time()
import {module}
t1 = time.time()
print(f"{{(t1-t0)*1000:.2f}},{{len(sys.modules)}}")
"""
    times: List[float] = []
    modules: List[int] = []

    for _ in range(iterations):
        res = _run_subprocess([sys.executable, "-c", code])
        for line in res.stdout.splitlines():
            line = line.strip()
            if "," in line and not line.startswith("INFO"):
                try:
                    t_str, m_str = line.split(",")
                    times.append(float(t_str))
                    modules.append(int(m_str))
                except ValueError:
                    pass

    return {
        "module": module,
        "iterations": iterations,
        "median_ms": round(statistics.median(times), 2) if times else 0.0,
        "mean_ms": round(statistics.mean(times), 2) if times else 0.0,
        "min_ms": round(min(times), 2) if times else 0.0,
        "max_ms": round(max(times), 2) if times else 0.0,
        "modules_in_sys_modules": int(statistics.median(modules)) if modules else 0,
    }


def measure_endpoint_coldstart(endpoint: str, iterations: int = 3) -> Dict[str, Any]:
    """Measure coldstart request latency in a fresh subprocess."""
    code = f"""
import sys, time, os
os.environ['AUTH_NETLOC'] = 'false'
t0 = time.time()
from backend.api.main import app
t_import = time.time() - t0
client = app.test_client()
t1 = time.time()
resp = client.get('{endpoint}', headers={{'X-TBA-Auth-Key': 'test_key'}})
t_req = time.time() - t1
t_total = time.time() - t0
print(f"{{t_total*1000:.2f}},{{t_import*1000:.2f}},{{t_req*1000:.2f}},{{resp.status_code}}")
"""
    totals: List[float] = []
    imports: List[float] = []
    reqs: List[float] = []
    status = ""

    for _ in range(iterations):
        res = _run_subprocess([sys.executable, "-c", code])
        for line in res.stdout.splitlines():
            line = line.strip()
            if "," in line and not line.startswith("INFO"):
                parts = line.split(",")
                if len(parts) == 4:
                    try:
                        totals.append(float(parts[0]))
                        imports.append(float(parts[1]))
                        reqs.append(float(parts[2]))
                        status = parts[3]
                    except ValueError:
                        pass

    return {
        "endpoint": endpoint,
        "status_code": status,
        "median_total_ms": round(statistics.median(totals), 2) if totals else 0.0,
        "median_import_ms": round(statistics.median(imports), 2) if imports else 0.0,
        "median_req_ms": round(statistics.median(reqs), 2) if reqs else 0.0,
        "min_total_ms": round(min(totals), 2) if totals else 0.0,
        "max_total_ms": round(max(totals), 2) if totals else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark startup time and coldstart latency for TBA services."
    )
    parser.add_argument(
        "--service",
        choices=list(SERVICE_MODULES.keys()),
        default="api",
        help="Service module to benchmark (default: api).",
    )
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=3,
        help="Number of iterations for benchmark runs (default: 3).",
    )
    parser.add_argument(
        "--top-imports",
        type=int,
        default=10,
        help="Number of top slowest imports to display (default: 10).",
    )
    parser.add_argument(
        "--imports-only",
        action="store_true",
        help="Only benchmark import time without running endpoint coldstarts.",
    )
    parser.add_argument(
        "--endpoints",
        nargs="*",
        default=DEFAULT_ENDPOINTS,
        help="Custom endpoints to benchmark.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output benchmark results as JSON.",
    )
    args = parser.parse_args()

    module = SERVICE_MODULES[args.service]

    if not args.json:
        print("=" * 80)
        print(f"TBA Coldstart Benchmark — Service: {args.service} ({module})")
        print("=" * 80)
        print(f"Measuring startup across {args.iterations} iterations...\n")

    # 1. Startup Latency
    startup_res = measure_startup_latency(module, iterations=args.iterations)

    # 2. Import Profile (-X importtime)
    profile_res = measure_import_profile(module, top_n=args.top_imports)

    # 3. Endpoint Coldstart (API only)
    endpoint_results: List[Dict[str, Any]] = []
    if not args.imports_only and args.service == "api":
        if not args.json:
            print("Measuring fresh process coldstart for common endpoints...")
        for ep in args.endpoints:
            endpoint_results.append(
                measure_endpoint_coldstart(ep, iterations=args.iterations)
            )

    if args.json:
        output = {
            "startup": startup_res,
            "profile": profile_res,
            "endpoints": endpoint_results,
        }
        print(json.dumps(output, indent=2))
        return

    # Print Formatted Results
    print("\n--- 1. Process Startup & Import Timing ---")
    print(f"  Median Startup Time : {startup_res['median_ms']:.2f} ms")
    print(f"  Mean Startup Time   : {startup_res['mean_ms']:.2f} ms")
    print(
        f"  Range (min / max)   : {startup_res['min_ms']:.2f} ms / {startup_res['max_ms']:.2f} ms"
    )
    print(f"  Modules in sys.modules : {startup_res['modules_in_sys_modules']}")
    print(f"  Total Import Records   : {profile_res['total_modules_loaded']}")
    print(f"  Cumulative Import Time : {profile_res['cumulative_import_ms']:.2f} ms")

    print(f"\n--- 2. Top {args.top_imports} Slowest Imports by Self Time ---")
    print(f"  {'Module':<45} | {'Self Time':<10} | {'Cumulative':<10}")
    print("  " + "-" * 71)
    for entry in profile_res["slowest_by_self_time"]:
        print(
            f"  {entry['module']:<45} | {entry['self_ms']:7.2f} ms | {entry['cum_ms']:7.2f} ms"
        )

    if endpoint_results:
        print("\n--- 3. Fresh Process Endpoint Coldstart Latency ---")
        print(
            f"  {'Endpoint':<36} | {'Total':<10} | {'Import':<9} | {'Req':<8} | {'Status':<6}"
        )
        print("  " + "-" * 77)
        for ep_res in endpoint_results:
            print(
                f"  {ep_res['endpoint']:<36} | "
                f"{ep_res['median_total_ms']:7.2f} ms | "
                f"{ep_res['median_import_ms']:6.2f} ms | "
                f"{ep_res['median_req_ms']:5.2f} ms | "
                f"{ep_res['status_code']:<6}"
            )

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
