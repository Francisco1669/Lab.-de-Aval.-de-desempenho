# =============================================================================
# Makefile - Benchmark CockroachDB vs ScyllaDB
# =============================================================================
# Comandos disponíveis:
#   make install      - Instala dependências e YCSB
#   make run          - Executa experimento completo
#   make quick-test   - Executa teste rápido de validação
#   make analyze      - Gera gráficos e análises
#   make clean        - Limpa resultados e containers
# =============================================================================

.PHONY: all install setup run quick-test analyze clean help \
        start-cockroach stop-cockroach start-scylla stop-scylla stop-all

# Comando padrão
all: help

# Instalação completa
install:
	@echo "📦 Instalando dependências Python..."
	pip install -r requirements.txt
	@echo ""
	@echo "📥 Instalando YCSB..."
	chmod +x scripts/*.sh scripts/*.py analysis/*.py 2>/dev/null || true
	bash scripts/install_ycsb.sh || python3 scripts/install_ycsb.py
	@echo ""
	@echo "✅ Instalação concluída!"

# Executar experimento completo
run:
	@echo "🔬 Iniciando experimento completo..."
	python3 main.py

# Teste rápido de validação
quick-test:
	@echo "⚡ Executando teste rápido..."
	python3 main.py --quick-test

# Teste apenas CockroachDB
test-cockroach:
	@echo "🐓 Testando apenas CockroachDB..."
	python3 main.py --databases cockroach --threads 16 --repetitions 1

# Teste apenas ScyllaDB
test-scylla:
	@echo "🦂 Testando apenas ScyllaDB..."
	python3 main.py --databases scylla --threads 16 --repetitions 1 --consistency ONE

# Análise de resultados
analyze:
	@echo "📊 Gerando análises e gráficos..."
	python3 analysis/analyze_results.py

# Gerenciamento de containers
start-cockroach:
	@echo "🚀 Iniciando CockroachDB..."
	docker-compose -f docker/docker-compose-cockroachdb.yml up -d

stop-cockroach:
	@echo "🛑 Parando CockroachDB..."
	docker-compose -f docker/docker-compose-cockroachdb.yml down -v

start-scylla:
	@echo "🚀 Iniciando ScyllaDB..."
	docker-compose -f docker/docker-compose-scylladb.yml up -d

stop-scylla:
	@echo "🛑 Parando ScyllaDB..."
	docker-compose -f docker/docker-compose-scylladb.yml down -v

stop-all:
	@echo "🛑 Parando todos os containers..."
	docker-compose -f docker/docker-compose-cockroachdb.yml down -v 2>/dev/null || true
	docker-compose -f docker/docker-compose-scylladb.yml down -v 2>/dev/null || true

# Limpeza
clean:
	@echo "🧹 Limpando resultados e cache..."
	rm -rf results/
	rm -rf benchmark_lib/__pycache__/
	rm -rf analysis/__pycache__/
	rm -rf scripts/__pycache__/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -delete
	@echo "✅ Limpeza concluída!"

clean-all: clean stop-all
	@echo "🧹 Removendo YCSB..."
	rm -rf ycsb-*
	@echo "✅ Limpeza completa!"

# Ajuda
help:
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════╗"
	@echo "║     Benchmark CockroachDB vs ScyllaDB - Comandos Make        ║"
	@echo "╠══════════════════════════════════════════════════════════════╣"
	@echo "║                                                              ║"
	@echo "║  INSTALAÇÃO:                                                 ║"
	@echo "║    make install        Instala dependências e YCSB           ║"
	@echo "║                                                              ║"
	@echo "║  EXECUÇÃO:                                                   ║"
	@echo "║    make run            Experimento completo                  ║"
	@echo "║    make quick-test     Teste rápido de validação             ║"
	@echo "║    make test-cockroach Testar apenas CockroachDB             ║"
	@echo "║    make test-scylla    Testar apenas ScyllaDB                ║"
	@echo "║                                                              ║"
	@echo "║  ANÁLISE:                                                    ║"
	@echo "║    make analyze        Gerar gráficos e estatísticas         ║"
	@echo "║                                                              ║"
	@echo "║  CONTAINERS:                                                 ║"
	@echo "║    make start-cockroach   Iniciar CockroachDB                ║"
	@echo "║    make stop-cockroach    Parar CockroachDB                  ║"
	@echo "║    make start-scylla      Iniciar ScyllaDB                   ║"
	@echo "║    make stop-scylla       Parar ScyllaDB                     ║"
	@echo "║    make stop-all          Parar todos os containers          ║"
	@echo "║                                                              ║"
	@echo "║  LIMPEZA:                                                    ║"
	@echo "║    make clean          Limpar resultados e cache             ║"
	@echo "║    make clean-all      Limpeza completa (inclui YCSB)        ║"
	@echo "║                                                              ║"
	@echo "╚══════════════════════════════════════════════════════════════╝"
	@echo ""
