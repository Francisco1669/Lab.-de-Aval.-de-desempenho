.PHONY: all install setup-cockroach setup-scylla stop-cockroach stop-scylla run clean

all: install run

install:
	pip install -r requirements.txt
	chmod +x run_benchmark.sh scripts/*.sh scripts/*.py analysis/*.py
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

clean:
	rm -rf results/
	rm -rf ycsb-*
	docker-compose -f docker/docker-compose-cockroachdb.yml down -v 2>/dev/null || true
	docker-compose -f docker/docker-compose-scylladb.yml down -v 2>/dev/null || true
