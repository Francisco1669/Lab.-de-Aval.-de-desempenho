#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
Script Principal de Benchmark: CockroachDB vs ScyllaDB
=============================================================================
Este script orquestra o experimento completo de benchmark comparativo
entre CockroachDB (NewSQL/ACID) e ScyllaDB (NoSQL/BASE) usando YCSB.

Foco: Ingestão Massiva de Dados (Insert Heavy)

Autor: Gerado automaticamente para experimento de avaliação de desempenho
Compatibilidade: Linux (Ubuntu/Arch), Windows (WSL/PowerShell com Python)

Uso:
    python main.py [--quick-test] [--databases cockroach,scylla] [--threads 16,32]

Para customização, veja a seção CONFIGURAÇÕES DO EXPERIMENTO abaixo.
=============================================================================
"""

import os
import sys
import subprocess
import time
import csv
import re
import json
import argparse
import platform
import threading
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from concurrent.futures import ThreadPoolExecutor

# =============================================================================
# CONFIGURAÇÕES DO EXPERIMENTO
# =============================================================================
# Altere aqui os parâmetros do experimento conforme necessário

@dataclass
class ExperimentConfig:
    """Configurações centralizadas do experimento."""
    
    # ===== BANCOS DE DADOS =====
    databases: List[str] = field(default_factory=lambda: ["cockroach", "scylla"])
    
    # ===== NÍVEIS DE CONCORRÊNCIA (THREADS) =====
    # Altere esta lista para testar diferentes níveis de concorrência
    thread_counts: List[int] = field(default_factory=lambda: [16, 32, 64, 128])
    
    # ===== NÍVEIS DE CONSISTÊNCIA (ScyllaDB apenas) =====
    # ONE: Apenas 1 réplica confirma (mais rápido, menor consistência)
    # QUORUM: Maioria das réplicas confirma (balanceado)
    # ALL: Todas as réplicas confirmam (mais lento, maior consistência)
    scylla_consistency_levels: List[str] = field(default_factory=lambda: ["ONE", "QUORUM", "ALL"])
    
    # ===== REPETIÇÕES =====
    # Número de repetições para cada configuração (para significância estatística)
    repetitions: int = 3
    
    # ===== PATHS =====
    ycsb_dir: str = "ycsb-0.17.0"
    workload_file: str = "workloads/workload_insert_heavy"
    results_dir: str = "results"
    docker_dir: str = "docker"
    
    # ===== TIMEOUTS (segundos) =====
    db_startup_timeout: int = 120
    db_health_check_interval: int = 5
    ycsb_timeout: int = 3600  # 1 hora
    
    # ===== MÉTRICAS =====
    metrics_collection_interval: float = 1.0  # segundos


# =============================================================================
# CLASSES DE SUPORTE
# =============================================================================

@dataclass
class BenchmarkResult:
    """Resultado de uma execução de benchmark."""
    database: str
    threads: int
    consistency: str
    repetition: int
    throughput: float
    latency_avg: float
    latency_p99: float
    latency_p95: float
    latency_min: float
    latency_max: float
    cpu_avg: float
    memory_avg: float
    duration_seconds: float
    timestamp: str
    success: bool
    error_message: str = ""


class MetricsCollector:
    """Coletor de métricas de containers Docker em background."""
    
    def __init__(self, container_name: str, interval: float = 1.0):
        self.container_name = container_name
        self.interval = interval
        self.running = False
        self.metrics: List[Dict] = []
        self._thread: Optional[threading.Thread] = None
    
    def start(self):
        """Inicia a coleta de métricas em background."""
        self.running = True
        self.metrics = []
        self._thread = threading.Thread(target=self._collect_loop, daemon=True)
        self._thread.start()
    
    def stop(self) -> Tuple[float, float]:
        """Para a coleta e retorna médias de CPU e memória."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        
        if not self.metrics:
            return 0.0, 0.0
        
        cpu_values = [m['cpu'] for m in self.metrics if m['cpu'] is not None]
        mem_values = [m['memory'] for m in self.metrics if m['memory'] is not None]
        
        cpu_avg = sum(cpu_values) / len(cpu_values) if cpu_values else 0.0
        mem_avg = sum(mem_values) / len(mem_values) if mem_values else 0.0
        
        return cpu_avg, mem_avg
    
    def _collect_loop(self):
        """Loop de coleta de métricas."""
        while self.running:
            try:
                cmd = f'docker stats --no-stream --format "{{{{.CPUPerc}}}},{{{{.MemUsage}}}}" {self.container_name}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0 and result.stdout.strip():
                    parts = result.stdout.strip().split(',')
                    cpu = float(parts[0].rstrip('%'))
                    
                    mem_str = parts[1].split('/')[0].strip()
                    if 'GiB' in mem_str:
                        memory = float(mem_str.replace('GiB', '').strip()) * 1024
                    elif 'MiB' in mem_str:
                        memory = float(mem_str.replace('MiB', '').strip())
                    else:
                        memory = 0.0
                    
                    self.metrics.append({'cpu': cpu, 'memory': memory})
            except Exception:
                pass
            
            time.sleep(self.interval)


class DatabaseManager:
    """Gerenciador de containers Docker dos bancos de dados."""
    
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.project_root = Path(__file__).parent.absolute()
    
    def _run_command(self, cmd: str, timeout: int = 60) -> Tuple[bool, str, str]:
        """Executa um comando shell e retorna (sucesso, stdout, stderr)."""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def start_cockroachdb(self) -> bool:
        """Inicia o container CockroachDB."""
        print("🚀 Iniciando CockroachDB...")
        compose_file = self.project_root / self.config.docker_dir / "docker-compose-cockroachdb.yml"
        
        success, _, stderr = self._run_command(
            f"docker-compose -f {compose_file} up -d"
        )
        
        if not success:
            print(f"❌ Erro ao iniciar CockroachDB: {stderr}")
            return False
        
        return self._wait_for_cockroachdb()
    
    def _wait_for_cockroachdb(self) -> bool:
        """Aguarda CockroachDB ficar pronto."""
        print("⏳ Aguardando CockroachDB ficar pronto...")
        
        for i in range(self.config.db_startup_timeout // self.config.db_health_check_interval):
            success, _, _ = self._run_command(
                'docker exec cockroachdb ./cockroach sql --insecure -e "SELECT 1"',
                timeout=10
            )
            if success:
                print("✅ CockroachDB está pronto!")
                return True
            time.sleep(self.config.db_health_check_interval)
            print(f"   Tentativa {i+1}...")
        
        print("❌ Timeout aguardando CockroachDB")
        return False
    
    def setup_cockroachdb(self) -> bool:
        """Configura o banco de dados YCSB no CockroachDB."""
        print("🔧 Configurando banco YCSB no CockroachDB...")
        
        # Criar banco de dados
        success, _, stderr = self._run_command(
            'docker exec cockroachdb ./cockroach sql --insecure -e "CREATE DATABASE IF NOT EXISTS ycsb;"'
        )
        if not success:
            print(f"❌ Erro ao criar database: {stderr}")
            return False
        
        # Criar tabela usertable (necessária para driver JDBC)
        create_table_sql = "CREATE TABLE IF NOT EXISTS ycsb.usertable (YCSB_KEY VARCHAR(255) PRIMARY KEY, FIELD0 TEXT, FIELD1 TEXT, FIELD2 TEXT, FIELD3 TEXT, FIELD4 TEXT, FIELD5 TEXT, FIELD6 TEXT, FIELD7 TEXT, FIELD8 TEXT, FIELD9 TEXT);"
        success, _, stderr = self._run_command(
            f"docker exec cockroachdb ./cockroach sql --insecure -e \"{create_table_sql}\""
        )
        if not success:
            print(f"❌ Erro ao criar tabela: {stderr}")
            return False
        
        print("✅ CockroachDB configurado!")
        return True
    
    def cleanup_cockroachdb(self) -> bool:
        """Limpa dados do CockroachDB para novo teste."""
        print("🧹 Limpando dados do CockroachDB...")
        success, _, _ = self._run_command(
            'docker exec cockroachdb ./cockroach sql --insecure -e "TRUNCATE TABLE ycsb.usertable;"'
        )
        return success
    
    def stop_cockroachdb(self) -> bool:
        """Para o container CockroachDB."""
        print("🛑 Parando CockroachDB...")
        compose_file = self.project_root / self.config.docker_dir / "docker-compose-cockroachdb.yml"
        success, _, _ = self._run_command(f"docker-compose -f {compose_file} down -v")
        return success
    
    def start_scylladb(self) -> bool:
        """Inicia o container ScyllaDB."""
        print("🚀 Iniciando ScyllaDB...")
        compose_file = self.project_root / self.config.docker_dir / "docker-compose-scylladb.yml"
        
        success, _, stderr = self._run_command(
            f"docker-compose -f {compose_file} up -d"
        )
        
        if not success:
            print(f"❌ Erro ao iniciar ScyllaDB: {stderr}")
            return False
        
        return self._wait_for_scylladb()
    
    def _wait_for_scylladb(self) -> bool:
        """Aguarda ScyllaDB ficar pronto."""
        print("⏳ Aguardando ScyllaDB ficar pronto (pode demorar ~60s)...")
        
        for i in range(self.config.db_startup_timeout // self.config.db_health_check_interval):
            success, _, _ = self._run_command(
                'docker exec scylladb cqlsh -e "DESCRIBE KEYSPACES"',
                timeout=10
            )
            if success:
                print("✅ ScyllaDB está pronto!")
                return True
            time.sleep(self.config.db_health_check_interval)
            print(f"   Tentativa {i+1}...")
        
        print("❌ Timeout aguardando ScyllaDB")
        return False
    
    def setup_scylladb(self) -> bool:
        """Configura o keyspace YCSB no ScyllaDB."""
        print("🔧 Configurando keyspace YCSB no ScyllaDB...")
        
        # Criar keyspace com replication_factor=1
        create_keyspace = "CREATE KEYSPACE IF NOT EXISTS ycsb WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};"
        success, _, stderr = self._run_command(
            f'docker exec scylladb cqlsh -e "{create_keyspace}"'
        )
        if not success:
            print(f"❌ Erro ao criar keyspace: {stderr}")
            return False
        
        # Criar tabela usertable
        create_table = "CREATE TABLE IF NOT EXISTS ycsb.usertable (y_id varchar PRIMARY KEY, field0 varchar, field1 varchar, field2 varchar, field3 varchar, field4 varchar, field5 varchar, field6 varchar, field7 varchar, field8 varchar, field9 varchar);"
        success, _, stderr = self._run_command(
            f"docker exec scylladb cqlsh -e \"{create_table}\""
        )
        if not success:
            print(f"❌ Erro ao criar tabela: {stderr}")
            return False
        
        print("✅ ScyllaDB configurado!")
        return True
    
    def cleanup_scylladb(self) -> bool:
        """Limpa dados do ScyllaDB para novo teste."""
        print("🧹 Limpando dados do ScyllaDB...")
        success, _, _ = self._run_command(
            'docker exec scylladb cqlsh -e "TRUNCATE ycsb.usertable;"'
        )
        return success
    
    def stop_scylladb(self) -> bool:
        """Para o container ScyllaDB."""
        print("🛑 Parando ScyllaDB...")
        compose_file = self.project_root / self.config.docker_dir / "docker-compose-scylladb.yml"
        success, _, _ = self._run_command(f"docker-compose -f {compose_file} down -v")
        return success


class YCSBRunner:
    """Executor do YCSB benchmark."""
    
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.project_root = Path(__file__).parent.absolute()
        
        # Usar ycsb.sh (script shell) para compatibilidade com Python 3
        # O script 'ycsb' (Python) requer Python 2
        self.ycsb_bin = self.project_root / config.ycsb_dir / "bin" / "ycsb.sh"
        
        # Fallback para o script Python se .sh não existir
        if not self.ycsb_bin.exists():
            self.ycsb_bin = self.project_root / config.ycsb_dir / "bin" / "ycsb"
    
    def check_ycsb_installed(self) -> bool:
        """Verifica se o YCSB está instalado."""
        ycsb_dir = self.project_root / self.config.ycsb_dir
        if not ycsb_dir.exists():
            print(f"❌ YCSB não encontrado em {ycsb_dir}")
            print("   Execute: ./scripts/install_ycsb.sh")
            return False
        return True
    
    def run_cockroach_load(self, threads: int) -> Tuple[bool, str]:
        """Executa fase de LOAD no CockroachDB."""
        workload = self.project_root / self.config.workload_file
        
        cmd = [
            str(self.ycsb_bin), "load", "jdbc",
            "-P", str(workload),
            "-p", "db.driver=org.postgresql.Driver",
            "-p", "db.url=jdbc:postgresql://localhost:26257/ycsb?sslmode=disable",
            "-p", "db.user=root",
            "-p", "db.passwd=",
            "-p", "jdbc.fetchsize=10",
            "-p", "jdbc.autocommit=true",
            "-p", "db.batchsize=1000",
            "-threads", str(threads),
            "-s"
        ]
        
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, 
                timeout=self.config.ycsb_timeout
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "YCSB timeout"
        except Exception as e:
            return False, str(e)
    
    def run_scylla_load(self, threads: int, consistency: str) -> Tuple[bool, str]:
        """Executa fase de LOAD no ScyllaDB."""
        workload = self.project_root / self.config.workload_file
        
        cmd = [
            str(self.ycsb_bin), "load", "cassandra-cql",
            "-P", str(workload),
            "-p", "hosts=localhost",
            "-p", "port=9042",
            "-p", f"cassandra.readconsistencylevel={consistency}",
            "-p", f"cassandra.writeconsistencylevel={consistency}",
            "-threads", str(threads),
            "-s"
        ]
        
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=self.config.ycsb_timeout
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "YCSB timeout"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def parse_ycsb_output(output: str) -> Dict:
        """Extrai métricas da saída do YCSB."""
        metrics = {
            'throughput': 0.0,
            'latency_avg': 0.0,
            'latency_p99': 0.0,
            'latency_p95': 0.0,
            'latency_min': 0.0,
            'latency_max': 0.0,
        }
        
        # Throughput (ops/sec)
        match = re.search(r'\[OVERALL\], Throughput\(ops/sec\), ([\d.]+)', output)
        if match:
            metrics['throughput'] = float(match.group(1))
        
        # Latência INSERT (foco do experimento)
        # Média
        match = re.search(r'\[INSERT\], AverageLatency\(us\), ([\d.]+)', output)
        if match:
            metrics['latency_avg'] = float(match.group(1)) / 1000  # us -> ms
        
        # P99
        match = re.search(r'\[INSERT\], 99thPercentileLatency\(us\), ([\d.]+)', output)
        if match:
            metrics['latency_p99'] = float(match.group(1)) / 1000
        
        # P95
        match = re.search(r'\[INSERT\], 95thPercentileLatency\(us\), ([\d.]+)', output)
        if match:
            metrics['latency_p95'] = float(match.group(1)) / 1000
        
        # Min
        match = re.search(r'\[INSERT\], MinLatency\(us\), ([\d.]+)', output)
        if match:
            metrics['latency_min'] = float(match.group(1)) / 1000
        
        # Max
        match = re.search(r'\[INSERT\], MaxLatency\(us\), ([\d.]+)', output)
        if match:
            metrics['latency_max'] = float(match.group(1)) / 1000
        
        return metrics


class ExperimentOrchestrator:
    """Orquestrador principal do experimento."""
    
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.db_manager = DatabaseManager(config)
        self.ycsb_runner = YCSBRunner(config)
        self.results: List[BenchmarkResult] = []
        self.project_root = Path(__file__).parent.absolute()
        
        # Criar diretório de resultados
        self.results_dir = self.project_root / config.results_dir
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def run_experiment(self):
        """Executa o experimento completo."""
        print("\n" + "=" * 70)
        print("🔬 EXPERIMENTO: CockroachDB vs ScyllaDB - Ingestão Massiva")
        print("=" * 70)
        print(f"📅 Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Bancos: {', '.join(self.config.databases)}")
        print(f"🧵 Threads: {self.config.thread_counts}")
        print(f"🔄 Repetições: {self.config.repetitions}")
        print("=" * 70 + "\n")
        
        # Verificar YCSB
        if not self.ycsb_runner.check_ycsb_installed():
            print("\n❌ YCSB não está instalado. Execute:")
            print("   ./scripts/install_ycsb.sh")
            return False
        
        total_tests = self._calculate_total_tests()
        current_test = 0
        
        # Executar testes para cada banco
        for database in self.config.databases:
            if database == "cockroach":
                current_test = self._run_cockroach_tests(current_test, total_tests)
            elif database == "scylla":
                current_test = self._run_scylla_tests(current_test, total_tests)
        
        # Salvar resultados
        self._save_results()
        
        print("\n" + "=" * 70)
        print("✅ EXPERIMENTO CONCLUÍDO!")
        print(f"📁 Resultados salvos em: {self.results_dir}")
        print("=" * 70)
        
        return True
    
    def _calculate_total_tests(self) -> int:
        """Calcula o número total de testes."""
        total = 0
        for db in self.config.databases:
            if db == "cockroach":
                total += len(self.config.thread_counts) * self.config.repetitions
            elif db == "scylla":
                total += (len(self.config.thread_counts) * 
                         len(self.config.scylla_consistency_levels) * 
                         self.config.repetitions)
        return total
    
    def _run_cockroach_tests(self, current_test: int, total_tests: int) -> int:
        """Executa todos os testes do CockroachDB."""
        print("\n" + "-" * 50)
        print("🐓 COCKROACHDB TESTS")
        print("-" * 50)
        
        # Iniciar banco
        if not self.db_manager.start_cockroachdb():
            print("❌ Falha ao iniciar CockroachDB")
            return current_test
        
        if not self.db_manager.setup_cockroachdb():
            self.db_manager.stop_cockroachdb()
            return current_test
        
        try:
            for threads in self.config.thread_counts:
                for rep in range(1, self.config.repetitions + 1):
                    current_test += 1
                    print(f"\n📊 Teste {current_test}/{total_tests}: "
                          f"CockroachDB | Threads={threads} | Rep={rep}")
                    
                    # Limpar dados
                    self.db_manager.cleanup_cockroachdb()
                    time.sleep(2)
                    
                    # Coletar métricas
                    collector = MetricsCollector(
                        "cockroachdb", 
                        self.config.metrics_collection_interval
                    )
                    collector.start()
                    
                    # Executar benchmark
                    start_time = time.time()
                    success, output = self.ycsb_runner.run_cockroach_load(threads)
                    duration = time.time() - start_time
                    
                    # Parar coleta de métricas
                    cpu_avg, mem_avg = collector.stop()
                    
                    # Parsear resultados
                    if success:
                        metrics = YCSBRunner.parse_ycsb_output(output)
                        result = BenchmarkResult(
                            database="CockroachDB",
                            threads=threads,
                            consistency="ACID",  # CockroachDB é sempre ACID
                            repetition=rep,
                            throughput=metrics['throughput'],
                            latency_avg=metrics['latency_avg'],
                            latency_p99=metrics['latency_p99'],
                            latency_p95=metrics['latency_p95'],
                            latency_min=metrics['latency_min'],
                            latency_max=metrics['latency_max'],
                            cpu_avg=cpu_avg,
                            memory_avg=mem_avg,
                            duration_seconds=duration,
                            timestamp=datetime.now().isoformat(),
                            success=True
                        )
                        print(f"   ✅ Throughput: {metrics['throughput']:.2f} ops/sec | "
                              f"P99: {metrics['latency_p99']:.2f} ms")
                    else:
                        result = BenchmarkResult(
                            database="CockroachDB",
                            threads=threads,
                            consistency="ACID",
                            repetition=rep,
                            throughput=0,
                            latency_avg=0,
                            latency_p99=0,
                            latency_p95=0,
                            latency_min=0,
                            latency_max=0,
                            cpu_avg=cpu_avg,
                            memory_avg=mem_avg,
                            duration_seconds=duration,
                            timestamp=datetime.now().isoformat(),
                            success=False,
                            error_message=output[:500]
                        )
                        print(f"   ❌ Falha no benchmark")
                    
                    self.results.append(result)
                    
                    # Salvar resultados parciais
                    self._save_results()
        
        finally:
            self.db_manager.stop_cockroachdb()
        
        return current_test
    
    def _run_scylla_tests(self, current_test: int, total_tests: int) -> int:
        """Executa todos os testes do ScyllaDB."""
        print("\n" + "-" * 50)
        print("🦂 SCYLLADB TESTS")
        print("-" * 50)
        
        # Iniciar banco
        if not self.db_manager.start_scylladb():
            print("❌ Falha ao iniciar ScyllaDB")
            return current_test
        
        if not self.db_manager.setup_scylladb():
            self.db_manager.stop_scylladb()
            return current_test
        
        try:
            for threads in self.config.thread_counts:
                for consistency in self.config.scylla_consistency_levels:
                    for rep in range(1, self.config.repetitions + 1):
                        current_test += 1
                        print(f"\n📊 Teste {current_test}/{total_tests}: "
                              f"ScyllaDB | Threads={threads} | "
                              f"Consistency={consistency} | Rep={rep}")
                        
                        # Limpar dados
                        self.db_manager.cleanup_scylladb()
                        time.sleep(2)
                        
                        # Coletar métricas
                        collector = MetricsCollector(
                            "scylladb",
                            self.config.metrics_collection_interval
                        )
                        collector.start()
                        
                        # Executar benchmark
                        start_time = time.time()
                        success, output = self.ycsb_runner.run_scylla_load(
                            threads, consistency
                        )
                        duration = time.time() - start_time
                        
                        # Parar coleta de métricas
                        cpu_avg, mem_avg = collector.stop()
                        
                        # Parsear resultados
                        if success:
                            metrics = YCSBRunner.parse_ycsb_output(output)
                            result = BenchmarkResult(
                                database="ScyllaDB",
                                threads=threads,
                                consistency=consistency,
                                repetition=rep,
                                throughput=metrics['throughput'],
                                latency_avg=metrics['latency_avg'],
                                latency_p99=metrics['latency_p99'],
                                latency_p95=metrics['latency_p95'],
                                latency_min=metrics['latency_min'],
                                latency_max=metrics['latency_max'],
                                cpu_avg=cpu_avg,
                                memory_avg=mem_avg,
                                duration_seconds=duration,
                                timestamp=datetime.now().isoformat(),
                                success=True
                            )
                            print(f"   ✅ Throughput: {metrics['throughput']:.2f} ops/sec | "
                                  f"P99: {metrics['latency_p99']:.2f} ms")
                        else:
                            result = BenchmarkResult(
                                database="ScyllaDB",
                                threads=threads,
                                consistency=consistency,
                                repetition=rep,
                                throughput=0,
                                latency_avg=0,
                                latency_p99=0,
                                latency_p95=0,
                                latency_min=0,
                                latency_max=0,
                                cpu_avg=cpu_avg,
                                memory_avg=mem_avg,
                                duration_seconds=duration,
                                timestamp=datetime.now().isoformat(),
                                success=False,
                                error_message=output[:500]
                            )
                            print(f"   ❌ Falha no benchmark")
                        
                        self.results.append(result)
                        
                        # Salvar resultados parciais
                        self._save_results()
        
        finally:
            self.db_manager.stop_scylladb()
        
        return current_test
    
    def _save_results(self):
        """Salva resultados em CSV e JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV
        csv_file = self.results_dir / "results.csv"
        with open(csv_file, 'w', newline='') as f:
            if self.results:
                writer = csv.DictWriter(f, fieldnames=asdict(self.results[0]).keys())
                writer.writeheader()
                for result in self.results:
                    writer.writerow(asdict(result))
        
        # JSON (backup completo)
        json_file = self.results_dir / f"results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump([asdict(r) for r in self.results], f, indent=2)
        
        # CSV simplificado (formato solicitado)
        simple_csv = self.results_dir / "benchmark_summary.csv"
        with open(simple_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Banco', 'Threads', 'Consistência', 'Throughput', 
                'Latencia_P99', 'CPU_Avg', 'Mem_Avg'
            ])
            for r in self.results:
                if r.success:
                    writer.writerow([
                        r.database, r.threads, r.consistency,
                        f"{r.throughput:.2f}", f"{r.latency_p99:.2f}",
                        f"{r.cpu_avg:.2f}", f"{r.memory_avg:.2f}"
                    ])


def parse_arguments():
    """Parse argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Benchmark CockroachDB vs ScyllaDB - Ingestão Massiva"
    )
    
    parser.add_argument(
        '--quick-test', 
        action='store_true',
        help='Executa teste rápido com menos repetições e threads'
    )
    
    parser.add_argument(
        '--databases',
        type=str,
        default='cockroach,scylla',
        help='Bancos a testar (cockroach,scylla ou apenas um)'
    )
    
    parser.add_argument(
        '--threads',
        type=str,
        default='16,32,64,128',
        help='Níveis de threads separados por vírgula'
    )
    
    parser.add_argument(
        '--repetitions',
        type=int,
        default=3,
        help='Número de repetições por configuração'
    )
    
    parser.add_argument(
        '--consistency',
        type=str,
        default='ONE,QUORUM,ALL',
        help='Níveis de consistência ScyllaDB separados por vírgula'
    )
    
    return parser.parse_args()


def main():
    """Função principal."""
    args = parse_arguments()
    
    # Criar configuração
    config = ExperimentConfig()
    
    # Aplicar argumentos
    config.databases = [db.strip() for db in args.databases.split(',')]
    config.thread_counts = [int(t.strip()) for t in args.threads.split(',')]
    config.repetitions = args.repetitions
    config.scylla_consistency_levels = [c.strip() for c in args.consistency.split(',')]
    
    # Modo quick-test
    if args.quick_test:
        print("⚡ Modo Quick Test ativado")
        config.thread_counts = [16]
        config.repetitions = 1
        config.scylla_consistency_levels = ["ONE"]
        config.workload_file = "workloads/workload_quick_test"  # Workload reduzido
    
    # Executar experimento
    orchestrator = ExperimentOrchestrator(config)
    
    try:
        success = orchestrator.run_experiment()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Experimento interrompido pelo usuário")
        print("   Salvando resultados parciais...")
        orchestrator._save_results()
        sys.exit(130)


if __name__ == "__main__":
    main()
