import subprocess
import time
from abc import ABC, abstractmethod
from typing import Optional

class DatabaseController(ABC):
    def __init__(self, name: str):
        self.name = name
        self.is_running = False

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        pass

    def wait_until_ready(self, timeout: int = 60, interval: int = 2) -> bool:
        elapsed = 0
        while elapsed < timeout:
            if self.is_ready():
                self.is_running = True
                return True
            time.sleep(interval)
            elapsed += interval
        return False

    def execute_command(self, command: str, shell: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(command, shell=shell, capture_output=True, text=True)

class CockroachDBController(DatabaseController):
    def __init__(self, compose_file: str = "docker/docker-compose-cockroachdb.yml"):
        super().__init__("CockroachDB")
        self.compose_file = compose_file
        self.container_name = "cockroachdb"

    def start(self):
        cmd = f"docker-compose -f {self.compose_file} up -d"
        result = self.execute_command(cmd)
        if result.returncode == 0:
            return self.wait_until_ready()
        return False

    def stop(self):
        cmd = f"docker-compose -f {self.compose_file} down -v"
        result = self.execute_command(cmd)
        self.is_running = False
        return result.returncode == 0

    def is_ready(self) -> bool:
        cmd = f'docker exec {self.container_name} ./cockroach sql --insecure --execute="SELECT 1;"'
        result = self.execute_command(cmd)
        return result.returncode == 0

    def create_database(self, db_name: str = "ycsb") -> bool:
        cmd = f'docker exec {self.container_name} ./cockroach sql --insecure --execute="CREATE DATABASE IF NOT EXISTS {db_name};"'
        result = self.execute_command(cmd)
        return result.returncode == 0

class ScyllaDBController(DatabaseController):
    def __init__(self, compose_file: str = "docker/docker-compose-scylladb.yml"):
        super().__init__("ScyllaDB")
        self.compose_file = compose_file
        self.container_name = "scylladb"

    def start(self):
        cmd = f"docker-compose -f {self.compose_file} up -d"
        result = self.execute_command(cmd)
        if result.returncode == 0:
            return self.wait_until_ready(timeout=120)
        return False

    def stop(self):
        cmd = f"docker-compose -f {self.compose_file} down -v"
        result = self.execute_command(cmd)
        self.is_running = False
        return result.returncode == 0

    def is_ready(self) -> bool:
        cmd = f'docker exec {self.container_name} cqlsh -e "DESCRIBE KEYSPACES;"'
        result = self.execute_command(cmd)
        return result.returncode == 0
