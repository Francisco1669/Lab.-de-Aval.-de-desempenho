#!/usr/bin/env python3

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark_lib import WorkloadManager

def main():
    wm = WorkloadManager()

    print("="*80)
    print("AVAILABLE WORKLOADS")
    print("="*80)
    print()

    for workload_name in wm.list_workloads():
        print(wm.get_workload_info(workload_name))
        print()
        print("-"*80)
        print()

    print("\n" + "="*80)
    print("TEST CONFIGURATIONS")
    print("="*80)
    print()

    for config_name in wm.list_test_configurations():
        config = wm.get_test_configuration(config_name)
        print(f"Configuration: {config_name}")
        print(f"Description: {config['description']}")
        print(f"Threads: {config['threads']}")
        print(f"Repetitions: {config['repetitions']}")
        print(f"Databases: {', '.join(config['databases'])}")
        print()

        for db in config['databases']:
            levels = config['consistency_levels'].get(db, ['default'])
            print(f"  {db}: {', '.join(levels)}")

        print()
        print("-"*80)
        print()

if __name__ == '__main__':
    main()
