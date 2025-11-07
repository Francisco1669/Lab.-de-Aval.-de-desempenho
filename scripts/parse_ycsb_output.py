#!/usr/bin/env python3

import sys
import re
import json

def parse_ycsb_output(filename):
    results = {
        'throughput': 0,
        'latency_avg': 0,
        'latency_p50': 0,
        'latency_p95': 0,
        'latency_p99': 0,
        'latency_p999': 0,
        'latency_min': 0,
        'latency_max': 0
    }

    with open(filename, 'r') as f:
        content = f.read()

        throughput_match = re.search(r'\[OVERALL\],\s*Throughput\(ops/sec\),\s*([\d.]+)', content)
        if throughput_match:
            results['throughput'] = float(throughput_match.group(1))

        patterns = {
            'latency_avg': r'\[INSERT\],\s*AverageLatency\(us\),\s*([\d.]+)',
            'latency_min': r'\[INSERT\],\s*MinLatency\(us\),\s*([\d.]+)',
            'latency_max': r'\[INSERT\],\s*MaxLatency\(us\),\s*([\d.]+)',
            'latency_p50': r'\[INSERT\],\s*50thPercentileLatency\(us\),\s*([\d.]+)',
            'latency_p95': r'\[INSERT\],\s*95thPercentileLatency\(us\),\s*([\d.]+)',
            'latency_p99': r'\[INSERT\],\s*99thPercentileLatency\(us\),\s*([\d.]+)',
            'latency_p999': r'\[INSERT\],\s*99\.9thPercentileLatency\(us\),\s*([\d.]+)'
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                results[key] = float(match.group(1)) / 1000.0

    return results

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: parse_ycsb_output.py <ycsb_output_file>")
        sys.exit(1)

    results = parse_ycsb_output(sys.argv[1])
    print(json.dumps(results, indent=2))
