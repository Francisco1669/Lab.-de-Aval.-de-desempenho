#!/usr/bin/env python3

import sys
import csv
import statistics

def calculate_resource_metrics(filename):
    cpu_values = []
    mem_values = []

    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                cpu_values.append(float(row['cpu_percent']))
                mem_values.append(float(row['memory_mb']))
            except (ValueError, KeyError):
                continue

    if not cpu_values or not mem_values:
        return {'cpu_avg': 0, 'cpu_max': 0, 'mem_avg': 0, 'mem_max': 0}

    return {
        'cpu_avg': statistics.mean(cpu_values),
        'cpu_max': max(cpu_values),
        'mem_avg': statistics.mean(mem_values),
        'mem_max': max(mem_values)
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: calculate_metrics.py <metrics_csv_file>")
        sys.exit(1)

    import json
    results = calculate_resource_metrics(sys.argv[1])
    print(json.dumps(results, indent=2))
