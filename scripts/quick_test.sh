#!/bin/bash

set -e

cd "$(dirname "$0")/.."

WORKLOAD="workloads/workload_insert_heavy"
THREADS=16
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="results/quick_test_${TIMESTAMP}"

mkdir -p $RESULTS_DIR

echo "Quick test with 16 threads, single repetition"

echo "Installing YCSB..."
bash scripts/install_ycsb.sh

echo ""
echo "Testing CockroachDB..."
bash scripts/setup_cockroachdb.sh

mkdir -p "${RESULTS_DIR}/cockroachdb"
bash scripts/run_ycsb_cockroach.sh $WORKLOAD $THREADS "${RESULTS_DIR}/cockroachdb/ycsb_output.txt"

bash scripts/stop_cockroachdb.sh

echo ""
echo "Testing ScyllaDB (ONE)..."
bash scripts/setup_scylladb.sh

mkdir -p "${RESULTS_DIR}/scylladb_ONE"
bash scripts/run_ycsb_scylla.sh $WORKLOAD $THREADS "ONE" "${RESULTS_DIR}/scylladb_ONE/ycsb_output.txt"

bash scripts/stop_scylladb.sh

echo ""
echo "Quick test completed! Results in: $RESULTS_DIR"
