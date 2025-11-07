#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark_lib import WorkloadManager

def generate_all_workloads():
    wm = WorkloadManager()

    print("Generating YCSB workload files from workloads.json...")

    for workload_name in wm.list_workloads():
        workload = wm.get_workload(workload_name)
        output_path = workload['file']

        wm.generate_ycsb_file(workload_name, output_path)
        print(f"Generated: {output_path}")

    print(f"\nTotal workloads generated: {len(wm.list_workloads())}")

if __name__ == '__main__':
    generate_all_workloads()
