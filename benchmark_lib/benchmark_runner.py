import subprocess
import threading
from pathlib import Path
from typing import Optional, Dict
from .database_controller import DatabaseController
from .metrics_collector import MetricsCollector

class BenchmarkRunner:
    def __init__(self, ycsb_dir: str = "ycsb-0.17.0"):
        self.ycsb_dir = Path(ycsb_dir)
        if not self.ycsb_dir.exists():
            raise FileNotFoundError(f"YCSB directory {ycsb_dir} not found. Run install_ycsb.sh first.")
        self.ycsb_bin = self.ycsb_dir / "bin" / "ycsb"

    def run_cockroachdb_benchmark(
        self,
        workload_file: str,
        threads: int,
        output_file: str,
        host: str = "localhost",
        port: int = 26257,
        database: str = "ycsb",
        user: str = "root"
    ) -> bool:
        jdbc_url = f"jdbc:postgresql://{host}:{port}/{database}?sslmode=disable"

        load_cmd = [
            str(self.ycsb_bin), "load", "jdbc",
            "-P", workload_file,
            "-p", "db.driver=org.postgresql.Driver",
            "-p", f"db.url={jdbc_url}",
            "-p", f"db.user={user}",
            "-p", "jdbc.fetchsize=10",
            "-p", "jdbc.autocommit=true",
            "-p", "db.batchsize=1000",
            "-threads", str(threads)
        ]

        result = subprocess.run(load_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return False

        run_cmd = [
            str(self.ycsb_bin), "run", "jdbc",
            "-P", workload_file,
            "-p", "db.driver=org.postgresql.Driver",
            "-p", f"db.url={jdbc_url}",
            "-p", f"db.user={user}",
            "-p", "jdbc.fetchsize=10",
            "-p", "jdbc.autocommit=true",
            "-p", "db.batchsize=1000",
            "-threads", str(threads)
        ]

        with open(output_file, 'w') as f:
            result = subprocess.run(run_cmd, stdout=f, stderr=subprocess.PIPE, text=True)

        return result.returncode == 0

    def run_scylladb_benchmark(
        self,
        workload_file: str,
        threads: int,
        consistency_level: str,
        output_file: str,
        host: str = "localhost",
        port: int = 9042
    ) -> bool:
        load_cmd = [
            str(self.ycsb_bin), "load", "cassandra-cql",
            "-P", workload_file,
            "-p", f"hosts={host}",
            "-p", f"port={port}",
            "-p", f"cassandra.readconsistencylevel={consistency_level}",
            "-p", f"cassandra.writeconsistencylevel={consistency_level}",
            "-threads", str(threads)
        ]

        result = subprocess.run(load_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return False

        run_cmd = [
            str(self.ycsb_bin), "run", "cassandra-cql",
            "-P", workload_file,
            "-p", f"hosts={host}",
            "-p", f"port={port}",
            "-p", f"cassandra.readconsistencylevel={consistency_level}",
            "-p", f"cassandra.writeconsistencylevel={consistency_level}",
            "-threads", str(threads)
        ]

        with open(output_file, 'w') as f:
            result = subprocess.run(run_cmd, stdout=f, stderr=subprocess.PIPE, text=True)

        return result.returncode == 0

    def run_benchmark_with_metrics(
        self,
        db_controller: DatabaseController,
        container_name: str,
        metrics_output: str,
        benchmark_func,
        **benchmark_kwargs
    ) -> Dict:
        collector = MetricsCollector(container_name, metrics_output)

        metrics_thread = threading.Thread(target=collector.collect_metrics_continuous)
        metrics_thread.daemon = True
        metrics_thread.start()

        success = benchmark_func(**benchmark_kwargs)

        collector.stop()
        metrics_thread.join(timeout=5)

        return {
            'success': success,
            'metrics_file': metrics_output
        }
