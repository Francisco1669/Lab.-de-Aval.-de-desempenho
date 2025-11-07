#!/usr/bin/env python3

from benchmark_lib import (
    WorkloadManager,
    CockroachDBController,
    ScyllaDBController,
    BenchmarkRunner,
    ResultsAnalyzer
)

def example_1_list_workloads():
    print("="*60)
    print("Example 1: List all available workloads")
    print("="*60)

    wm = WorkloadManager()

    print("\nAvailable workloads:")
    for workload_name in wm.list_workloads():
        print(f"\n{workload_name}:")
        print(wm.get_workload_info(workload_name))

def example_2_single_test():
    print("\n" + "="*60)
    print("Example 2: Run a single benchmark test")
    print("="*60)

    print("\nStarting CockroachDB...")
    db = CockroachDBController()
    db.start()
    db.create_database()

    print("Running benchmark...")
    runner = BenchmarkRunner()
    success = runner.run_cockroachdb_benchmark(
        workload_file="workloads/workload_insert_heavy",
        threads=32,
        output_file="results/example_output.txt"
    )

    if success:
        print("Benchmark completed successfully!")

        results = ResultsAnalyzer.parse_ycsb_output("results/example_output.txt")
        print(f"\nResults:")
        print(f"  Throughput: {results['throughput']:.2f} ops/sec")
        print(f"  Latency P99: {results['latency_p99']:.2f} ms")
        print(f"  Latency Avg: {results['latency_avg']:.2f} ms")
    else:
        print("Benchmark failed!")

    print("\nStopping CockroachDB...")
    db.stop()

def example_3_compare_consistency():
    print("\n" + "="*60)
    print("Example 3: Compare ScyllaDB consistency levels")
    print("="*60)

    consistency_levels = ['ONE', 'QUORUM']
    results = {}

    for consistency in consistency_levels:
        print(f"\nTesting ScyllaDB with consistency: {consistency}")

        db = ScyllaDBController()
        db.start()

        runner = BenchmarkRunner()
        output_file = f"results/scylla_{consistency}.txt"

        success = runner.run_scylladb_benchmark(
            workload_file="workloads/workload_insert_heavy",
            threads=32,
            consistency_level=consistency,
            output_file=output_file
        )

        if success:
            results[consistency] = ResultsAnalyzer.parse_ycsb_output(output_file)

        db.stop()

    print("\n" + "="*60)
    print("Consistency Comparison Results")
    print("="*60)

    for consistency, result in results.items():
        print(f"\n{consistency}:")
        print(f"  Throughput: {result['throughput']:.2f} ops/sec")
        print(f"  Latency P99: {result['latency_p99']:.2f} ms")

    if len(results) == 2:
        one_throughput = results['ONE']['throughput']
        quorum_throughput = results['QUORUM']['throughput']
        overhead = ((one_throughput - quorum_throughput) / one_throughput) * 100

        print(f"\nConsistency Cost:")
        print(f"  Throughput overhead: {overhead:.2f}%")

def example_4_test_configurations():
    print("\n" + "="*60)
    print("Example 4: List test configurations")
    print("="*60)

    wm = WorkloadManager()

    print("\nAvailable test configurations:")
    for config_name in wm.list_test_configurations():
        config = wm.get_test_configuration(config_name)
        print(f"\n{config_name}:")
        print(f"  Description: {config['description']}")
        print(f"  Threads: {config['threads']}")
        print(f"  Repetitions: {config['repetitions']}")
        print(f"  Databases: {', '.join(config['databases'])}")

if __name__ == '__main__':
    print("Database Benchmark Framework - Usage Examples")
    print("=" * 60)

    example_1_list_workloads()

    print("\n\nTo run other examples, uncomment them in the code:")
    print("  - example_2_single_test(): Run a single benchmark")
    print("  - example_3_compare_consistency(): Compare consistency levels")
    print("  - example_4_test_configurations(): Show test configurations")
