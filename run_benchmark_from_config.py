#!/usr/bin/env python3

import sys
import json
from pathlib import Path
from datetime import datetime
from benchmark_lib import (
    WorkloadManager,
    CockroachDBController,
    ScyllaDBController,
    BenchmarkRunner,
    ResultsAnalyzer
)

def run_test_configuration(config_name: str, output_dir: str):
    wm = WorkloadManager()
    config = wm.get_test_configuration(config_name)

    print(f"Running test configuration: {config_name}")
    print(f"Description: {config['description']}")
    print(f"Threads: {config['threads']}")
    print(f"Repetitions: {config['repetitions']}")
    print()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path(output_dir) / config_name / timestamp
    results_dir.mkdir(parents=True, exist_ok=True)

    runner = BenchmarkRunner()

    for db_name in config['databases']:
        consistency_levels = config['consistency_levels'].get(db_name, ['default'])

        for consistency in consistency_levels:
            for threads in config['threads']:
                for rep in range(1, config['repetitions'] + 1):
                    print(f"Testing {db_name} - consistency: {consistency}, threads: {threads}, rep: {rep}")

                    test_dir = results_dir / f"{db_name}_{consistency}" / f"threads_{threads}" / f"rep_{rep}"
                    test_dir.mkdir(parents=True, exist_ok=True)

                    if db_name == "cockroachdb":
                        db = CockroachDBController()
                        db.start()
                        db.create_database()

                        success = runner.run_cockroachdb_benchmark(
                            workload_file="workloads/workload_insert_heavy",
                            threads=threads,
                            output_file=str(test_dir / "ycsb_output.txt")
                        )

                        db.stop()

                    elif db_name == "scylladb":
                        db = ScyllaDBController()
                        db.start()

                        success = runner.run_scylladb_benchmark(
                            workload_file="workloads/workload_insert_heavy",
                            threads=threads,
                            consistency_level=consistency,
                            output_file=str(test_dir / "ycsb_output.txt")
                        )

                        db.stop()

                    if success:
                        ycsb_results = ResultsAnalyzer.parse_ycsb_output(str(test_dir / "ycsb_output.txt"))

                        summary = {
                            'database': db_name,
                            'consistency': consistency,
                            'threads': threads,
                            'repetition': rep,
                            'throughput': ycsb_results['throughput'],
                            'latency_p99': ycsb_results['latency_p99'],
                            'timestamp': timestamp
                        }

                        with open(test_dir / "summary.json", 'w') as f:
                            json.dump(summary, f, indent=2)

                        print(f"  Success! Throughput: {ycsb_results['throughput']:.2f} ops/sec, P99: {ycsb_results['latency_p99']:.2f} ms")
                    else:
                        print(f"  Failed!")

    print(f"\nAll tests completed! Results saved to: {results_dir}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        wm = WorkloadManager()
        print("Usage: run_benchmark_from_config.py <test_config_name> [output_dir]")
        print("\nAvailable test configurations:")
        for config_name in wm.list_test_configurations():
            config = wm.get_test_configuration(config_name)
            print(f"  - {config_name}: {config['description']}")
        sys.exit(1)

    config_name = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "results"

    run_test_configuration(config_name, output_dir)
