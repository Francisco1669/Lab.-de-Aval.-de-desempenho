import json
import csv
import re
import statistics
from pathlib import Path
from typing import Dict, List, Optional

class ResultsAnalyzer:
    @staticmethod
    def parse_ycsb_output(output_file: str) -> Dict:
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

        with open(output_file, 'r') as f:
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

    @staticmethod
    def calculate_resource_metrics(metrics_file: str) -> Dict:
        cpu_values = []
        mem_values = []

        with open(metrics_file, 'r') as f:
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
            'cpu_stdev': statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0,
            'mem_avg': statistics.mean(mem_values),
            'mem_max': max(mem_values),
            'mem_stdev': statistics.stdev(mem_values) if len(mem_values) > 1 else 0
        }

    @staticmethod
    def create_summary(
        ycsb_results: Dict,
        resource_metrics: Dict,
        database: str,
        consistency: str,
        threads: int,
        repetition: int,
        timestamp: str
    ) -> Dict:
        return {
            'database': database,
            'consistency': consistency,
            'threads': threads,
            'repetition': repetition,
            'throughput': ycsb_results['throughput'],
            'latency_p99': ycsb_results['latency_p99'],
            'latency_avg': ycsb_results['latency_avg'],
            'latency_p95': ycsb_results['latency_p95'],
            'cpu_avg': resource_metrics['cpu_avg'],
            'cpu_max': resource_metrics['cpu_max'],
            'mem_avg': resource_metrics['mem_avg'],
            'mem_max': resource_metrics['mem_max'],
            'timestamp': timestamp
        }

    @staticmethod
    def aggregate_results(results_dir: str) -> List[Dict]:
        results_path = Path(results_dir)
        all_results = []

        for result_file in results_path.glob('**/summary.json'):
            with open(result_file, 'r') as f:
                data = json.load(f)
                all_results.append(data)

        return all_results

    @staticmethod
    def calculate_statistics(results: List[Dict], group_by: List[str]) -> Dict:
        from collections import defaultdict

        grouped = defaultdict(list)

        for result in results:
            key = tuple(result[field] for field in group_by)
            grouped[key].append(result)

        stats = {}
        for key, group_results in grouped.items():
            throughputs = [r['throughput'] for r in group_results]
            latencies = [r['latency_p99'] for r in group_results]

            stats[key] = {
                'count': len(group_results),
                'throughput_mean': statistics.mean(throughputs),
                'throughput_stdev': statistics.stdev(throughputs) if len(throughputs) > 1 else 0,
                'latency_p99_mean': statistics.mean(latencies),
                'latency_p99_stdev': statistics.stdev(latencies) if len(latencies) > 1 else 0
            }

        return stats
