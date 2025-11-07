#!/usr/bin/env python3

import json
import sys
import statistics
from pathlib import Path
from collections import defaultdict

def load_results(results_dir):
    results_path = Path(results_dir)
    grouped_results = defaultdict(list)

    for result_file in results_path.glob('**/summary.json'):
        with open(result_file, 'r') as f:
            data = json.load(f)
            key = (data['database'], data.get('consistency', 'ACID'), data['threads'])
            grouped_results[key].append(data)

    return grouped_results

def calculate_statistics(values):
    if not values:
        return {'mean': 0, 'stdev': 0, 'min': 0, 'max': 0}

    return {
        'mean': statistics.mean(values),
        'stdev': statistics.stdev(values) if len(values) > 1 else 0,
        'min': min(values),
        'max': max(values)
    }

def analyze_results(grouped_results):
    analysis = {}

    for key, results in grouped_results.items():
        db_name, consistency, threads = key

        throughputs = [r['throughput'] for r in results]
        latencies = [r['latency_p99'] for r in results]
        cpus = [r['cpu_avg'] for r in results]
        mems = [r['mem_avg'] for r in results]

        analysis[key] = {
            'database': db_name,
            'consistency': consistency,
            'threads': threads,
            'num_samples': len(results),
            'throughput': calculate_statistics(throughputs),
            'latency_p99': calculate_statistics(latencies),
            'cpu_avg': calculate_statistics(cpus),
            'mem_avg': calculate_statistics(mems)
        }

    return analysis

def print_analysis(analysis):
    print("=" * 80)
    print("STATISTICAL ANALYSIS OF BENCHMARK RESULTS")
    print("=" * 80)
    print()

    sorted_keys = sorted(analysis.keys(), key=lambda x: (x[0], x[1], x[2]))

    for key in sorted_keys:
        stats = analysis[key]
        print(f"Database: {stats['database']} ({stats['consistency']})")
        print(f"Threads: {stats['threads']}")
        print(f"Samples: {stats['num_samples']}")
        print()

        print("  Throughput (ops/sec):")
        print(f"    Mean: {stats['throughput']['mean']:.2f}")
        print(f"    StdDev: {stats['throughput']['stdev']:.2f}")
        print(f"    Min: {stats['throughput']['min']:.2f}")
        print(f"    Max: {stats['throughput']['max']:.2f}")
        print()

        print("  Latency P99 (ms):")
        print(f"    Mean: {stats['latency_p99']['mean']:.2f}")
        print(f"    StdDev: {stats['latency_p99']['stdev']:.2f}")
        print(f"    Min: {stats['latency_p99']['min']:.2f}")
        print(f"    Max: {stats['latency_p99']['max']:.2f}")
        print()

        print("  CPU Usage (%):")
        print(f"    Mean: {stats['cpu_avg']['mean']:.2f}")
        print(f"    StdDev: {stats['cpu_avg']['stdev']:.2f}")
        print()

        print("  Memory Usage (MB):")
        print(f"    Mean: {stats['mem_avg']['mean']:.2f}")
        print(f"    StdDev: {stats['mem_avg']['stdev']:.2f}")
        print()

        print("-" * 80)
        print()

def main():
    if len(sys.argv) != 2:
        print("Usage: statistical_analysis.py <results_directory>")
        sys.exit(1)

    results_dir = sys.argv[1]
    grouped_results = load_results(results_dir)

    if not grouped_results:
        print("No results found.")
        sys.exit(1)

    analysis = analyze_results(grouped_results)
    print_analysis(analysis)

    output_file = Path(results_dir) / 'statistical_analysis.json'
    with open(output_file, 'w') as f:
        json.dump({str(k): v for k, v in analysis.items()}, f, indent=2)

    print(f"Analysis saved to: {output_file}")

if __name__ == '__main__':
    main()
