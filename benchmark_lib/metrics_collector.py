import subprocess
import csv
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

class MetricsCollector:
    def __init__(self, container_name: str, output_file: str):
        self.container_name = container_name
        self.output_file = Path(output_file)
        self.running = False
        self.interval = 1

    def is_container_running(self) -> bool:
        cmd = f"docker ps --filter name={self.container_name} --format '{{{{.Names}}}}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return self.container_name in result.stdout

    def collect_single_metric(self) -> Optional[dict]:
        if not self.is_container_running():
            return None

        cmd = f'docker stats --no-stream --format "{{{{.CPUPerc}}}},{{{{.MemUsage}}}}" {self.container_name}'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            return None

        try:
            parts = result.stdout.strip().split(',')
            cpu_percent = float(parts[0].rstrip('%'))

            mem_str = parts[1].split('/')[0].strip()
            if 'GiB' in mem_str:
                mem_mb = float(mem_str.replace('GiB', '')) * 1024
            else:
                mem_mb = float(mem_str.replace('MiB', ''))

            return {
                'timestamp': int(time.time()),
                'cpu_percent': cpu_percent,
                'memory_mb': mem_mb
            }
        except (ValueError, IndexError):
            return None

    def collect_metrics_continuous(self):
        self.running = True

        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'cpu_percent', 'memory_mb'])
            writer.writeheader()

            while self.running and self.is_container_running():
                metric = self.collect_single_metric()
                if metric:
                    writer.writerow(metric)
                    f.flush()
                time.sleep(self.interval)

    def stop(self):
        self.running = False
