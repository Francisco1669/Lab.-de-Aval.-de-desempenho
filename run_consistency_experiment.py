#!/usr/bin/env python3
"""
Experimento: Custo da Consistência em ScyllaDB Cluster (3 nós, RF=3)
Objetivo: Medir o impacto real dos níveis ONE, QUORUM e ALL
"""

import subprocess
import time
import csv
import json
import re
import os
from datetime import datetime
from pathlib import Path

# Configuração
YCSB_HOME = Path(__file__).parent / "ycsb-0.17.0"
WORKLOAD = Path(__file__).parent / "workloads" / "workload_insert_heavy"
RESULTS_DIR = Path(__file__).parent / "results"
DOCKER_COMPOSE = Path(__file__).parent / "docker" / "docker-compose-scylladb-cluster.yml"

# Parâmetros do experimento
THREAD_COUNTS = [16, 32, 64]  # Removido 128 para evitar sobrecarga
CONSISTENCY_LEVELS = ["ONE", "QUORUM", "ALL"]
REPETITIONS = 3

# ScyllaDB cluster connection
SCYLLA_HOST = "localhost"
SCYLLA_PORT = 9042

def run_command(cmd, check=True, capture=True):
    """Executa comando shell"""
    print(f"  $ {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(
        cmd, shell=isinstance(cmd, str), 
        capture_output=capture, text=True, check=False
    )
    if check and result.returncode != 0:
        print(f"  ERRO: {result.stderr}")
    return result

def start_cluster():
    """Inicia o cluster ScyllaDB de 3 nós"""
    print("\n" + "="*60)
    print("INICIANDO CLUSTER ScyllaDB (3 nós)")
    print("="*60)
    
    # Parar containers antigos
    run_command(f"docker compose -f {DOCKER_COMPOSE} down -v", check=False)
    time.sleep(5)
    
    # Iniciar cluster
    run_command(f"docker compose -f {DOCKER_COMPOSE} up -d")
    
    print("\nAguardando cluster inicializar (pode levar 2-3 minutos)...")
    
    # Aguardar todos os nós estarem prontos
    max_wait = 300  # 5 minutos
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        result = run_command(
            "docker exec scylla-node1 nodetool status 2>/dev/null | grep -c '^UN'",
            check=False
        )
        try:
            nodes_up = int(result.stdout.strip())
            print(f"  Nós ativos: {nodes_up}/3")
            if nodes_up >= 3:
                print("  ✓ Cluster pronto!")
                break
        except:
            pass
        time.sleep(10)
    else:
        print("  ⚠ Timeout aguardando cluster. Continuando mesmo assim...")
    
    # Mostrar status do cluster
    run_command("docker exec scylla-node1 nodetool status", check=False)
    
    return True

def setup_keyspace():
    """Cria keyspace com RF=3"""
    print("\n" + "="*60)
    print("CONFIGURANDO KEYSPACE (RF=3)")
    print("="*60)
    
    cql_commands = """
    DROP KEYSPACE IF EXISTS ycsb;
    CREATE KEYSPACE ycsb WITH replication = {
        'class': 'SimpleStrategy',
        'replication_factor': 3
    };
    USE ycsb;
    CREATE TABLE usertable (
        y_id varchar PRIMARY KEY,
        field0 varchar, field1 varchar, field2 varchar,
        field3 varchar, field4 varchar, field5 varchar,
        field6 varchar, field7 varchar, field8 varchar, field9 varchar
    );
    """
    
    # Executar via cqlsh no container
    result = run_command(
        f'docker exec scylla-node1 cqlsh -e "{cql_commands}"',
        check=False
    )
    
    if result.returncode == 0:
        print("  ✓ Keyspace criado com RF=3")
    else:
        print(f"  ⚠ Erro ao criar keyspace: {result.stderr}")
    
    # Verificar replicação
    run_command(
        'docker exec scylla-node1 cqlsh -e "DESCRIBE KEYSPACE ycsb"',
        check=False
    )
    
    return True

def run_ycsb_test(threads, consistency):
    """Executa teste YCSB"""
    print(f"\n  Executando: {threads} threads, {consistency}")
    
    ycsb_cmd = [
        str(YCSB_HOME / "bin" / "ycsb.sh"),
        "run", "cassandra-cql",
        "-P", str(WORKLOAD),
        "-p", f"hosts={SCYLLA_HOST}",
        "-p", f"port={SCYLLA_PORT}",
        "-p", f"cassandra.readconsistencylevel={consistency}",
        "-p", f"cassandra.writeconsistencylevel={consistency}",
        "-threads", str(threads),
        "-s"
    ]
    
    start_time = time.time()
    result = subprocess.run(ycsb_cmd, capture_output=True, text=True)
    duration = time.time() - start_time
    
    # Parse resultados
    output = result.stdout + result.stderr
    
    metrics = {
        'throughput': 0,
        'latency_avg': 0,
        'latency_p99': 0,
        'latency_p95': 0,
        'latency_min': 0,
        'latency_max': 0,
        'duration': duration,
        'success': result.returncode == 0
    }
    
    # Extrair métricas
    patterns = {
        'throughput': r'\[OVERALL\], Throughput\(ops/sec\), ([\d.]+)',
        'latency_avg': r'\[INSERT\], AverageLatency\(us\), ([\d.]+)',
        'latency_p99': r'\[INSERT\], 99thPercentileLatency\(us\), ([\d.]+)',
        'latency_p95': r'\[INSERT\], 95thPercentileLatency\(us\), ([\d.]+)',
        'latency_min': r'\[INSERT\], MinLatency\(us\), ([\d.]+)',
        'latency_max': r'\[INSERT\], MaxLatency\(us\), ([\d.]+)',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, output)
        if match:
            value = float(match.group(1))
            # Converter microsegundos para milissegundos
            if 'latency' in key:
                value = value / 1000
            metrics[key] = value
    
    print(f"    Throughput: {metrics['throughput']:.2f} ops/s, P99: {metrics['latency_p99']:.2f} ms")
    
    return metrics

def truncate_table():
    """Limpa tabela entre testes"""
    run_command(
        'docker exec scylla-node1 cqlsh -e "TRUNCATE ycsb.usertable"',
        check=False
    )
    time.sleep(2)

def stop_cluster():
    """Para o cluster"""
    print("\n" + "="*60)
    print("PARANDO CLUSTER")
    print("="*60)
    run_command(f"docker compose -f {DOCKER_COMPOSE} down", check=False)

def main():
    print("="*60)
    print("EXPERIMENTO: CUSTO DA CONSISTÊNCIA EM ScyllaDB")
    print("Cluster: 3 nós | RF=3 | Níveis: ONE, QUORUM, ALL")
    print("="*60)
    
    # Criar diretório de resultados
    RESULTS_DIR.mkdir(exist_ok=True)
    
    # Arquivo de resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = RESULTS_DIR / f"consistency_experiment_{timestamp}.csv"
    
    results = []
    
    try:
        # Iniciar cluster
        if not start_cluster():
            print("Falha ao iniciar cluster")
            return
        
        # Configurar keyspace
        setup_keyspace()
        time.sleep(10)  # Aguardar propagação
        
        # Calcular total de testes
        total_tests = len(THREAD_COUNTS) * len(CONSISTENCY_LEVELS) * REPETITIONS
        current_test = 0
        
        # Executar experimento
        for threads in THREAD_COUNTS:
            for consistency in CONSISTENCY_LEVELS:
                for rep in range(1, REPETITIONS + 1):
                    current_test += 1
                    print(f"\n{'='*60}")
                    print(f"TESTE {current_test}/{total_tests}")
                    print(f"Threads: {threads} | Consistência: {consistency} | Repetição: {rep}")
                    print(f"{'='*60}")
                    
                    # Limpar tabela
                    truncate_table()
                    
                    # Executar teste
                    metrics = run_ycsb_test(threads, consistency)
                    
                    # Registrar resultado
                    result = {
                        'database': 'ScyllaDB-Cluster',
                        'threads': threads,
                        'consistency': consistency,
                        'repetition': rep,
                        'throughput': metrics['throughput'],
                        'latency_avg': metrics['latency_avg'],
                        'latency_p99': metrics['latency_p99'],
                        'latency_p95': metrics['latency_p95'],
                        'latency_min': metrics['latency_min'],
                        'latency_max': metrics['latency_max'],
                        'duration_seconds': metrics['duration'],
                        'timestamp': datetime.now().isoformat(),
                        'success': metrics['success'],
                        'nodes': 3,
                        'replication_factor': 3
                    }
                    results.append(result)
                    
                    # Salvar incrementalmente
                    with open(csv_file, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=result.keys())
                        writer.writeheader()
                        writer.writerows(results)
                    
                    # Intervalo entre testes
                    time.sleep(5)
        
        print("\n" + "="*60)
        print("EXPERIMENTO CONCLUÍDO!")
        print(f"Resultados salvos em: {csv_file}")
        print("="*60)
        
    finally:
        # Perguntar se deve parar o cluster
        print("\n⚠ O cluster ScyllaDB ainda está rodando.")
        print("Para parar, execute:")
        print(f"  docker compose -f {DOCKER_COMPOSE} down -v")

if __name__ == '__main__':
    main()
