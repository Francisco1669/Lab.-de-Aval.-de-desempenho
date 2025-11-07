.PHONY: all install setup-cockroach setup-scylla stop-cockroach stop-scylla run clean list-workloads generate-workloads example quick-test

all: install run

install:
	pip install -r requirements.txt
	chmod +x run_benchmark.sh scripts/*.sh scripts/*.py analysis/*.py
	chmod +x run_benchmark_from_config.py example_usage.py
	bash scripts/install_ycsb.sh

setup-cockroach:
	bash scripts/setup_cockroachdb.sh

setup-scylla:
	bash scripts/setup_scylladb.sh

stop-cockroach:
	bash scripts/stop_cockroachdb.sh

stop-scylla:
	bash scripts/stop_scylladb.sh

run:
	./run_benchmark.sh

quick-test:
	bash scripts/quick_test.sh

list-workloads:
	python3 scripts/list_workloads.py

generate-workloads:
	python3 scripts/generate_workloads_from_json.py

example:
	python3 example_usage.py

clean:
	rm -rf results/
	rm -rf ycsb-*
	rm -rf benchmark_lib/__pycache__/
	find . -name "*.pyc" -delete
	docker-compose -f docker/docker-compose-cockroachdb.yml down -v 2>/dev/null || true
	docker-compose -f docker/docker-compose-scylladb.yml down -v 2>/dev/null || true
