#!/usr/bin/env python3

import json
import sys
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def load_results(results_dir):
    results = []
    results_path = Path(results_dir)

    for result_file in results_path.glob('**/summary.json'):
        with open(result_file, 'r') as f:
            data = json.load(f)
            results.append(data)

    return results

def plot_throughput_vs_threads(results, output_file):
    dbs = {}
    for result in results:
        db_name = result['database']
        consistency = result.get('consistency', 'ACID')
        key = f"{db_name} ({consistency})"

        if key not in dbs:
            dbs[key] = {'threads': [], 'throughput': []}

        dbs[key]['threads'].append(result['threads'])
        dbs[key]['throughput'].append(result['throughput'])

    plt.figure(figsize=(10, 6))

    for db_name, data in dbs.items():
        sorted_data = sorted(zip(data['threads'], data['throughput']))
        threads, throughput = zip(*sorted_data)
        plt.plot(threads, throughput, marker='o', label=db_name, linewidth=2)

    plt.xlabel('Number of Threads', fontsize=12)
    plt.ylabel('Throughput (ops/sec)', fontsize=12)
    plt.title('Throughput vs Number of Threads', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()

def plot_latency_p99_vs_threads(results, output_file):
    dbs = {}
    for result in results:
        db_name = result['database']
        consistency = result.get('consistency', 'ACID')
        key = f"{db_name} ({consistency})"

        if key not in dbs:
            dbs[key] = {'threads': [], 'latency': []}

        dbs[key]['threads'].append(result['threads'])
        dbs[key]['latency'].append(result['latency_p99'])

    plt.figure(figsize=(10, 6))

    for db_name, data in dbs.items():
        sorted_data = sorted(zip(data['threads'], data['latency']))
        threads, latency = zip(*sorted_data)
        plt.plot(threads, latency, marker='o', label=db_name, linewidth=2)

    plt.xlabel('Number of Threads', fontsize=12)
    plt.ylabel('P99 Latency (ms)', fontsize=12)
    plt.title('P99 Latency vs Number of Threads', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()

def plot_resource_usage(results, output_file):
    dbs = {}
    for result in results:
        db_name = result['database']
        consistency = result.get('consistency', 'ACID')
        key = f"{db_name} ({consistency})"

        if key not in dbs:
            dbs[key] = {'cpu': [], 'memory': [], 'threads': []}

        dbs[key]['cpu'].append(result['cpu_avg'])
        dbs[key]['memory'].append(result['mem_avg'])
        dbs[key]['threads'].append(result['threads'])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    for db_name, data in dbs.items():
        sorted_data = sorted(zip(data['threads'], data['cpu']))
        threads, cpu = zip(*sorted_data)
        ax1.plot(threads, cpu, marker='o', label=db_name, linewidth=2)

    ax1.set_xlabel('Number of Threads', fontsize=12)
    ax1.set_ylabel('Average CPU Usage (%)', fontsize=12)
    ax1.set_title('CPU Usage vs Number of Threads', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    for db_name, data in dbs.items():
        sorted_data = sorted(zip(data['threads'], data['memory']))
        threads, memory = zip(*sorted_data)
        ax2.plot(threads, memory, marker='o', label=db_name, linewidth=2)

    ax2.set_xlabel('Number of Threads', fontsize=12)
    ax2.set_ylabel('Average Memory Usage (MB)', fontsize=12)
    ax2.set_title('Memory Usage vs Number of Threads', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()

def plot_comparison_table(results, output_file):
    dbs = {}
    for result in results:
        db_name = result['database']
        consistency = result.get('consistency', 'ACID')
        key = f"{db_name} ({consistency})"

        if key not in dbs:
            dbs[key] = {
                'max_throughput': 0,
                'min_latency_p99': float('inf'),
                'avg_cpu': [],
                'avg_memory': []
            }

        if result['throughput'] > dbs[key]['max_throughput']:
            dbs[key]['max_throughput'] = result['throughput']

        if result['latency_p99'] < dbs[key]['min_latency_p99']:
            dbs[key]['min_latency_p99'] = result['latency_p99']

        dbs[key]['avg_cpu'].append(result['cpu_avg'])
        dbs[key]['avg_memory'].append(result['mem_avg'])

    fig, ax = plt.subplots(figsize=(12, len(dbs) * 0.8 + 1))
    ax.axis('tight')
    ax.axis('off')

    table_data = []
    headers = ['Database', 'Max Throughput\n(ops/sec)', 'Min P99 Latency\n(ms)', 'Avg CPU\n(%)', 'Avg Memory\n(MB)']

    for db_name, data in sorted(dbs.items()):
        avg_cpu = np.mean(data['avg_cpu'])
        avg_memory = np.mean(data['avg_memory'])
        table_data.append([
            db_name,
            f"{data['max_throughput']:.2f}",
            f"{data['min_latency_p99']:.2f}",
            f"{avg_cpu:.2f}",
            f"{avg_memory:.2f}"
        ])

    table = ax.table(cellText=table_data, colLabels=headers, cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)

    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')

    plt.title('Performance Comparison Summary', fontsize=14, fontweight='bold', pad=20)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    if len(sys.argv) != 2:
        print("Usage: generate_plots.py <results_directory>")
        sys.exit(1)

    results_dir = sys.argv[1]
    results = load_results(results_dir)

    if not results:
        print("No results found in the specified directory.")
        sys.exit(1)

    output_dir = Path(results_dir) / 'plots'
    output_dir.mkdir(exist_ok=True)

    print(f"Generating plots from {len(results)} result files...")

    plot_throughput_vs_threads(results, output_dir / 'throughput_vs_threads.png')
    print("Generated: throughput_vs_threads.png")

    plot_latency_p99_vs_threads(results, output_dir / 'latency_p99_vs_threads.png')
    print("Generated: latency_p99_vs_threads.png")

    plot_resource_usage(results, output_dir / 'resource_usage.png')
    print("Generated: resource_usage.png")

    plot_comparison_table(results, output_dir / 'comparison_table.png')
    print("Generated: comparison_table.png")

    print(f"All plots saved to {output_dir}")

if __name__ == '__main__':
    main()
