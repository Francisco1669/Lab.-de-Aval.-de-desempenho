# Benchmark CockroachDB vs ScyllaDB - Ingestão Massiva de Dados

[![Status](https://img.shields.io/badge/Status-Concluído-brightgreen)]()
[![YCSB](https://img.shields.io/badge/YCSB-0.17.0-blue)]()
[![Docker](https://img.shields.io/badge/Docker-29.1.2-blue)]()

## 🎯 Objetivo

Framework de benchmark automatizado para comparação experimental entre **CockroachDB (NewSQL/ACID)** e **ScyllaDB (NoSQL/BASE)**, utilizando o Yahoo! Cloud Serving Benchmark (YCSB).

O foco principal é avaliar a **Ingestão Massiva de Dados (Insert Heavy)**, quantificando:
- Throughput (operações/segundo)
- Latência (P99, média)
- Utilização de recursos (CPU, memória)
- **Custo da consistência** (ONE vs QUORUM vs ALL)

**Autores**: Antonio Zubiaurre, Eduardo Paim, Felipe Dresch, Vinicius Santa Catarina  
**Instituição**: Universidade Federal do Pampa (UNIPAMPA)  
**Disciplina**: Laboratório de Avaliação de Desempenho

---

## 📊 Resultados Principais

### Experimento 1: Single-Node

| SGBD | Threads | Throughput (ops/s) | Status |
|------|---------|-------------------|--------|
| CockroachDB | 32 | 8.807 ± 215 | **Ponto Ótimo** |
| CockroachDB | 128 | 0 (Timeout) | ❌ FALHA |
| ScyllaDB | 32 | 13.993 ± 229 | ✅ OK |
| ScyllaDB | 128 | 13.982 ± 111 | ✅ OK |

**Conclusão**: ScyllaDB ~2x mais rápido, CockroachDB falha em alta concorrência.

### Experimento 2: Custo da Consistência (Cluster 3 nós)

| Consistência | Throughput (16t) | Impacto |
|--------------|------------------|---------|
| ONE | 7.391 ops/s | - |
| QUORUM | 6.315 ops/s | -14,6% |
| ALL | 6.347 ops/s | -14,1% |

**Conclusão**: ~15% de custo para garantir consistência forte.

---

## 📋 Pré-requisitos

### Software Necessário
- **Docker** e **Docker Compose** (versão 2.0+)
- **Python 3.8+**
- **Java 8+** (para YCSB)

### Verificação de Instalação
```bash
# Verificar Docker
docker --version
docker-compose --version

# Verificar Python
python3 --version

# Verificar Java
java -version
```

### Instalação de Dependências (Linux)
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y docker.io docker-compose python3 python3-pip openjdk-11-jdk

# Arch Linux
sudo pacman -S docker docker-compose python python-pip jdk11-openjdk
```

---

## 🚀 Início Rápido

### 1. Clonar e Preparar
```bash
# Clonar repositório
git clone <url-do-repositorio>
cd Lab.-de-Aval.-de-desempenho

# Instalar dependências Python
pip install -r requirements.txt

# Instalar YCSB (versão 0.17.0)
./scripts/install_ycsb.sh
# ou para Windows/compatibilidade:
python scripts/install_ycsb.py
```

### 2. Executar Experimento Completo
```bash
# Experimento completo (pode demorar horas)
python main.py

# Teste rápido (validação do setup)
python main.py --quick-test
```

### 3. Analisar Resultados
```bash
# Gerar gráficos e estatísticas
python analysis/analyze_results.py
```

---

## ⚙️ Configuração do Experimento

### Parâmetros Principais (em `main.py`)

```python
@dataclass
class ExperimentConfig:
    # Bancos de dados a testar
    databases: List[str] = ["cockroach", "scylla"]
    
    # Níveis de concorrência (threads)
    # ALTERE AQUI para modificar os níveis de paralelismo
    thread_counts: List[int] = [16, 32, 64, 128]
    
    # Níveis de consistência ScyllaDB
    # ONE: Menor latência, menor consistência
    # QUORUM: Balanceado
    # ALL: Maior consistência, maior latência
    scylla_consistency_levels: List[str] = ["ONE", "QUORUM", "ALL"]
    
    # Repetições para significância estatística
    repetitions: int = 3
```

### Workload (em `workloads/workload_insert_heavy`)

```properties
# Número de registros a inserir (1 milhão)
# ALTERE AQUI para modificar o volume de dados
recordcount=1000000

# 100% operações de INSERT
insertproportion=1
```

---

## � Estrutura do Projeto

```
.
├── main.py                              # 🎯 Script principal do experimento
├── requirements.txt                      # Dependências Python
├── docker/
│   ├── docker-compose-cockroachdb.yml    # CockroachDB single-node
│   ├── docker-compose-scylladb.yml       # ScyllaDB single-node
│   └── docker-compose-scylladb-cluster.yml # ScyllaDB cluster 3 nós (RF=3)
├── workloads/
│   ├── workload_insert_heavy             # 1M registros, 100% INSERT
│   └── workload_consistency_test         # 100K registros para cluster
├── analysis/
│   ├── full_statistical_analysis.py      # t-test, ANOVA, Cohen's d
│   └── analyze_consistency_experiment.py # Análise do custo de consistência
├── results/
│   ├── results.csv                       # Dados Experimento 1 (48 testes)
│   ├── consistency_cluster_results.csv   # Dados Experimento 2 (30 testes)
│   └── plots/                            # 7 gráficos gerados
└── benchmark_lib/                        # Biblioteca de suporte
```

---

## 🔧 Configurações de Infraestrutura

### CockroachDB (docker-compose-cockroachdb.yml)
```yaml
# In-memory store (2GiB) - elimina I/O de disco
command: start-single-node --insecure --store=type=mem,size=2GiB
ports:
  - "26257:26257"  # SQL
  - "8080:8080"    # Admin UI
```

### ScyllaDB (docker-compose-scylladb.yml)
```yaml
# Configuração otimizada para containers
command: --smp 2 --memory 2G --overprovisioned 1
ports:
  - "9042:9042"   # CQL
  - "9160:9160"   # Thrift
  - "10000:10000" # REST
```

---

## 📈 Resultados

Após a execução, os resultados são salvos em:

| Arquivo | Descrição |
|---------|-----------|
| `results/results.csv` | Todos os dados coletados (detalhado) |
| `results/benchmark_summary.csv` | Resumo com médias |
| `results/plots/` | Gráficos de comparação |

### Métricas Coletadas
- **Throughput**: Operações por segundo
- **Latência P99/P95/Avg**: Em milissegundos
- **CPU Avg**: Uso médio de CPU (%)
- **Memory Avg**: Uso médio de memória (MB)

---

## 🖥️ Comandos Úteis

### Execução do Benchmark
```bash
# Experimento completo
python main.py

# Apenas CockroachDB
python main.py --databases cockroach

# Apenas ScyllaDB
python main.py --databases scylla

# Threads específicas
python main.py --threads 16,32

# Menos repetições
python main.py --repetitions 1

# Consistência específica
python main.py --consistency ONE,QUORUM
```

### Gerenciamento de Containers
```bash
# Ver containers rodando
docker ps

# Ver logs do CockroachDB
docker logs cockroachdb

# Ver logs do ScyllaDB
docker logs scylladb

# Parar todos os containers
docker-compose -f docker/docker-compose-cockroachdb.yml down -v
docker-compose -f docker/docker-compose-scylladb.yml down -v
```

### Análise
```bash
# Gerar todos os gráficos
python analysis/analyze_results.py

# Especificar diretório de resultados
python analysis/analyze_results.py --results-dir results
```

---

## 🔍 Design do Experimento

### Experimento 1: Single-Node (Comparação de Desempenho)

| Fator | Níveis |
|-------|--------|
| Banco de Dados | CockroachDB, ScyllaDB |
| Threads | 16, 32, 64, 128 |
| Consistência | ONE, QUORUM, ALL (ScyllaDB) / ACID (CockroachDB) |
| Repetições | 3 |

**Total**: 48 testes (12 CockroachDB + 36 ScyllaDB)

### Experimento 2: Cluster (Custo da Consistência)

| Fator | Níveis |
|-------|--------|
| Cluster | ScyllaDB 3 nós (RF=3) |
| Threads | 16, 32 |
| Consistência | ONE, QUORUM, ALL |
| Repetições | 5 |

**Total**: 30 testes

---

## ⚠️ Solução de Problemas

### YCSB não encontrado
```bash
# Instalar YCSB
./scripts/install_ycsb.sh
# Verificar instalação
ls ycsb-0.17.0/bin/ycsb
```

### Erro de conexão com banco
```bash
# Verificar se container está rodando
docker ps | grep -E "cockroach|scylla"

# Verificar logs
docker logs cockroachdb
docker logs scylladb
```

### Memória insuficiente
```yaml
# Reduzir memória em docker-compose
# CockroachDB: --store=type=mem,size=1GiB
# ScyllaDB: --memory 1G
```

### Java não encontrado
```bash
# Ubuntu/Debian
sudo apt install openjdk-11-jdk

# Arch
sudo pacman -S jdk11-openjdk
```

---

## 📚 Referências

- [YCSB - Yahoo! Cloud Serving Benchmark](https://github.com/brianfrankcooper/YCSB)
- [CockroachDB Documentation](https://www.cockroachlabs.com/docs/)
- [ScyllaDB Documentation](https://docs.scylladb.com/)
- [Docker Documentation](https://docs.docker.com/)
- Cooper, B. F. et al. (2010). Benchmarking cloud serving systems with YCSB. ACM SoCC.
- Kleppmann, M. (2017). Designing Data-Intensive Applications. O'Reilly Media.

---

## 🖥️ Hardware Utilizado

| Componente | Especificação |
|------------|---------------|
| CPU | AMD Ryzen 5 4500 (6 cores, 12 threads) |
| RAM | 16 GB DDR4 |
| Armazenamento | Lexar NQ100 SSD 960GB |
| SO | Arch Linux (Kernel 6.12.62-1-lts) |
| Docker | 29.1.2 com cgroups v2 |

---

## 📝 Licença

Este projeto é parte de um trabalho acadêmico da disciplina Laboratório de Avaliação de Desempenho.
Universidade Federal do Pampa (UNIPAMPA) - 2025.
