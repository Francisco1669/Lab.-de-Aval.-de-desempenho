# Análise de Desempenho e Custo de Consistência em Sistemas de Banco de Dados Distribuídos

## Objetivo

Framework de benchmark automatizado para comparação experimental entre CockroachDB (NewSQL/ACID) e ScyllaDB (NoSQL/BASE), quantificando o impacto de diferentes níveis de consistência em métricas de desempenho (throughput, latência P99) e utilização de recursos (CPU, memória) sob cargas de trabalho variadas baseadas no YCSB.

**Autores**: Antonio Zubiaurre, Eduardo Paim, Felipe Dresch, Vinicius Santa Catarina

## Resumo Técnico

Este projeto realiza uma avaliação experimental comparando o desempenho de CockroachDB (NewSQL) e ScyllaDB (NoSQL) sob cargas de trabalho de inserção massiva, utilizando o benchmark YCSB. O framework permite:

- Executar testes automatizados com múltiplas configurações (threads, workloads, níveis de consistência)
- Coletar métricas em tempo real (throughput, latência, CPU, memória)
- Gerar análises estatísticas e visualizações comparativas
- Identificar o "knee capacity" de cada sistema
- Quantificar o "custo da consistência" no ScyllaDB (ONE vs QUORUM vs ALL)

## Estrutura do Projeto

```
.
├── analysis/
│   ├── generate_plots.py
│   └── aggregate_results.py
├── config/
│   ├── cockroachdb_config.sh
│   └── scylladb_config.sh
├── docker/
│   ├── docker-compose-cockroachdb.yml
│   └── docker-compose-scylladb.yml
├── scripts/
│   ├── setup_cockroachdb.sh
│   ├── setup_scylladb.sh
│   ├── stop_cockroachdb.sh
│   ├── stop_scylladb.sh
│   ├── install_ycsb.sh
│   ├── run_ycsb_cockroach.sh
│   ├── run_ycsb_scylla.sh
│   ├── collect_metrics.sh
│   ├── parse_ycsb_output.py
│   └── calculate_metrics.py
├── workloads/
│   ├── workload_insert_heavy
│   └── workload_mixed
├── results/
├── run_benchmark.sh
└── README.md
```

## Pré-requisitos

- Docker e Docker Compose
- Python 3.7+
- Bash
- Curl
- Git

## Instalação

### 1. Instalar Dependências Python

```bash
pip install -r requirements.txt
```

### 2. Dar Permissões de Execução aos Scripts

```bash
chmod +x run_benchmark.sh
chmod +x scripts/*.sh
chmod +x scripts/*.py
chmod +x analysis/*.py
```

## Execução dos Benchmarks

### Execução Completa Automatizada

Para executar todos os testes automaticamente:

```bash
./run_benchmark.sh
```

Este script irá:
1. Instalar o YCSB
2. Executar testes no CockroachDB com diferentes números de threads (16, 32, 64, 128)
3. Executar testes no ScyllaDB com consistência ONE
4. Executar testes no ScyllaDB com consistência QUORUM
5. Cada configuração é repetida 3 vezes
6. Gerar análises e gráficos dos resultados

### Execução Manual

#### Testar CockroachDB

```bash
bash scripts/setup_cockroachdb.sh

bash scripts/run_ycsb_cockroach.sh workloads/workload_insert_heavy 32 results/cockroach_test.txt

bash scripts/stop_cockroachdb.sh
```

#### Testar ScyllaDB

```bash
bash scripts/setup_scylladb.sh

bash scripts/run_ycsb_scylla.sh workloads/workload_insert_heavy 32 ONE results/scylla_test.txt

bash scripts/stop_scylladb.sh
```

## Análise dos Resultados

Os resultados são salvos em `results/TIMESTAMP/` com a seguinte estrutura:

```
results/TIMESTAMP/
├── cockroachdb/
│   └── threads_X/
│       └── rep_Y/
│           ├── ycsb_output.txt
│           ├── metrics.csv
│           ├── ycsb_results.json
│           ├── resource_metrics.json
│           └── summary.json
├── scylladb_ONE/
│   └── threads_X/
│       └── rep_Y/
│           └── ...
├── scylladb_QUORUM/
│   └── threads_X/
│       └── rep_Y/
│           └── ...
├── all_results.csv
└── plots/
    ├── throughput_vs_threads.png
    ├── latency_p99_vs_threads.png
    ├── resource_usage.png
    └── comparison_table.png
```

### Métricas Coletadas

- **Throughput**: Operações por segundo
- **Latência P99**: Tempo de resposta no 99º percentil (ms)
- **CPU Usage**: Utilização média da CPU (%)
- **Memory Usage**: Utilização média de memória (MB)

## Uso Programático (Biblioteca Python)

O projeto inclui uma biblioteca Python modular (`benchmark_lib/`) para execução programática de benchmarks.

### Listar Workloads Disponíveis

```bash
python3 scripts/list_workloads.py
```

### Executar Benchmark a partir de Configuração JSON

```bash
python3 run_benchmark_from_config.py quick_comparison
```

Configurações disponíveis em `workloads.json`:
- `scalability_test`: Testa escalabilidade com múltiplos threads
- `consistency_cost_test`: Quantifica custo da consistência
- `quick_comparison`: Comparação rápida entre sistemas

### Exemplo de Uso Programático

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

Ver mais exemplos em `example_usage.py` e documentação completa em `benchmark_lib/README.md`.

## Personalização

### Modificar Workloads

Edite `workloads.json` para definir novos workloads ou modifique os arquivos em `workloads/` diretamente:
- `recordcount`: Número de registros a carregar
- `operationcount`: Número de operações a executar
- Proporções de leitura/escrita/inserção

### Modificar Parâmetros de Teste

Edite `run_benchmark.sh` para ajustar:
- `THREADS_LIST`: Lista de threads a testar
- `REPETITIONS`: Número de repetições por teste
- `WORKLOAD`: Workload a utilizar

Ou modifique configurações de teste em `workloads.json`.

### Adicionar Novos Níveis de Consistência

Para ScyllaDB, modifique o script `run_benchmark.sh` ou `workloads.json` e adicione novos testes com diferentes níveis:
- ONE
- QUORUM
- ALL
- LOCAL_QUORUM

## Interpretação dos Resultados

### Gráficos Gerados

1. **throughput_vs_threads.png**: Mostra como a vazão escala com o número de threads
2. **latency_p99_vs_threads.png**: Mostra como a latência P99 varia com a carga
3. **resource_usage.png**: Mostra utilização de CPU e memória
4. **comparison_table.png**: Tabela resumo com métricas principais

### Análise do "Knee Capacity"

O ponto onde a latência começa a aumentar exponencialmente enquanto o throughput se estabiliza indica o knee capacity do sistema.

## Troubleshooting

### Porta já em uso

Se encontrar erro de porta já em uso:

```bash
docker ps
docker stop <container_id>
```

### YCSB não encontrado

```bash
bash scripts/install_ycsb.sh
```

### Permissões negadas

```bash
chmod +x run_benchmark.sh scripts/*.sh scripts/*.py analysis/*.py
```

## Autores

- Antonio Zubiaurre
- Eduardo Paim
- Felipe Dresch
- Vinicius Santa Catarina
