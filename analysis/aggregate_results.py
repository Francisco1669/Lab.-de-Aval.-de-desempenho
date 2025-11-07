#!/usr/bin/env python3

import json
import sys
import csv
from pathlib import Path

def aggregate_results(results_dir):
    results_path = Path(results_dir)
    all_results = []

    for result_file in results_path.glob('**/summary.json'):
        with open(result_file, 'r') as f:
            data = json.load(f)
            all_results.append(data)

    return all_results

def save_to_csv(results, output_file):
    if not results:
        return

    fieldnames = list(results[0].keys())

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)

def main():
    if len(sys.argv) != 3:
        print("Usage: aggregate_results.py <results_directory> <output_csv>")
        sys.exit(1)

    results_dir = sys.argv[1]
    output_csv = sys.argv[2]

    results = aggregate_results(results_dir)

    if not results:
        print("No results found.")
        sys.exit(1)

    save_to_csv(results, output_csv)
    print(f"Aggregated {len(results)} results to {output_csv}")

if __name__ == '__main__':
    main()
