# Benchmark Library

Biblioteca Python modular para execução programática de benchmarks de bancos de dados distribuídos.

## Módulos

### WorkloadManager
Gerencia workloads definidos em `workloads.json`.

```python
from benchmark_lib import WorkloadManager

wm = WorkloadManager()
workloads = wm.list_workloads()
config = wm.get_test_configuration('quick_comparison')
```

### DatabaseController
Controla ciclo de vida de bancos de dados via Docker.

```python
from benchmark_lib import CockroachDBController, ScyllaDBController

cockroach = CockroachDBController()
cockroach.start()
cockroach.create_database()
cockroach.stop()

scylla = ScyllaDBController()
scylla.start()
scylla.stop()
```

### BenchmarkRunner
Executa benchmarks YCSB.

```python
from benchmark_lib import BenchmarkRunner

runner = BenchmarkRunner()

runner.run_cockroachdb_benchmark(
    workload_file="workloads/workload_insert_heavy",
    threads=32,
    output_file="results/output.txt"
)

runner.run_scylladb_benchmark(
    workload_file="workloads/workload_insert_heavy",
    threads=32,
    consistency_level="QUORUM",
    output_file="results/output.txt"
)
```

### MetricsCollector
Coleta métricas de CPU e memória em tempo real.

```python
from benchmark_lib import MetricsCollector

collector = MetricsCollector("cockroachdb", "metrics.csv")
collector.collect_metrics_continuous()
```

### ResultsAnalyzer
Analisa resultados de benchmarks.

```python
from benchmark_lib import ResultsAnalyzer

ycsb_results = ResultsAnalyzer.parse_ycsb_output("output.txt")
resource_metrics = ResultsAnalyzer.calculate_resource_metrics("metrics.csv")

all_results = ResultsAnalyzer.aggregate_results("results/20250107_120000")
stats = ResultsAnalyzer.calculate_statistics(all_results, ['database', 'threads'])
```

## Uso

### Exemplo Básico

```python
from benchmark_lib import (
    CockroachDBController,
    BenchmarkRunner,
    ResultsAnalyzer
)

db = CockroachDBController()
db.start()
db.create_database()

runner = BenchmarkRunner()
runner.run_cockroachdb_benchmark(
    workload_file="workloads/workload_insert_heavy",
    threads=32,
    output_file="results/test.txt"
)

results = ResultsAnalyzer.parse_ycsb_output("results/test.txt")
print(f"Throughput: {results['throughput']} ops/sec")

db.stop()
```

### Executar Configuração de Teste

```python
python3 run_benchmark_from_config.py quick_comparison
```

## Scripts de Exemplo

- `example_usage.py`: Exemplos de uso da biblioteca
- `run_benchmark_from_config.py`: Executa testes baseados em configurações JSON
- `scripts/list_workloads.py`: Lista workloads e configurações disponíveis
- `scripts/generate_workloads_from_json.py`: Gera arquivos YCSB a partir do JSON
