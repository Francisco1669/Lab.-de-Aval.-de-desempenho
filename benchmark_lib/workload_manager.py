import json
from pathlib import Path
from typing import Dict, List, Optional

class WorkloadManager:
    def __init__(self, config_file: str = "workloads.json"):
        self.config_file = Path(config_file)
        self.workloads = {}
        self.test_configurations = {}
        self._load_config()

    def _load_config(self):
        if not self.config_file.exists():
            raise FileNotFoundError(f"Configuration file {self.config_file} not found")

        with open(self.config_file, 'r') as f:
            config = json.load(f)

        self.workloads = {w['name']: w for w in config['workloads']}
        self.test_configurations = {t['name']: t for t in config['test_configurations']}

    def get_workload(self, name: str) -> Dict:
        if name not in self.workloads:
            raise ValueError(f"Workload {name} not found")
        return self.workloads[name]

    def get_test_configuration(self, name: str) -> Dict:
        if name not in self.test_configurations:
            raise ValueError(f"Test configuration {name} not found")
        return self.test_configurations[name]

    def list_workloads(self) -> List[str]:
        return list(self.workloads.keys())

    def list_test_configurations(self) -> List[str]:
        return list(self.test_configurations.keys())

    def generate_ycsb_file(self, workload_name: str, output_path: str):
        workload = self.get_workload(workload_name)
        params = workload['parameters']

        lines = [
            f"recordcount={params['recordcount']}",
            f"operationcount={params['operationcount']}",
            "workload=site.ycsb.workloads.CoreWorkload",
            "",
            "readallfields=true",
            "",
            f"readproportion={params['readproportion']}",
            f"updateproportion={params['updateproportion']}",
            f"scanproportion={params['scanproportion']}",
            f"insertproportion={params['insertproportion']}",
            "",
            f"requestdistribution={params['requestdistribution']}"
        ]

        if 'maxscanlength' in params:
            lines.append(f"maxscanlength={params['maxscanlength']}")

        with open(output_path, 'w') as f:
            f.write('\n'.join(lines) + '\n')

    def get_workload_info(self, name: str) -> str:
        workload = self.get_workload(name)
        info = [
            f"Workload: {name}",
            f"Description: {workload['description']}",
            f"File: {workload['file']}",
            "Parameters:",
        ]

        for key, value in workload['parameters'].items():
            info.append(f"  {key}: {value}")

        if 'use_cases' in workload:
            info.append("Use Cases:")
            for uc in workload['use_cases']:
                info.append(f"  - {uc}")

        return '\n'.join(info)
