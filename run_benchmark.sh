#!/bin/bash

set -e

cd "$(dirname "$0")"

WORKLOAD="workloads/workload_insert_heavy"
THREADS_LIST=(16 32 64 128)
REPETITIONS=3
RESULTS_BASE="results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="${RESULTS_BASE}/${TIMESTAMP}"

mkdir -p $RESULTS_DIR

echo "=========================================="
echo "Starting Benchmark Suite"
echo "Timestamp: $TIMESTAMP"
echo "Workload: $WORKLOAD"
echo "Threads: ${THREADS_LIST[@]}"
echo "Repetitions: $REPETITIONS"
echo "=========================================="

test_cockroachdb() {
    local threads=$1
    local rep=$2
    local output_dir="${RESULTS_DIR}/cockroachdb/threads_${threads}/rep_${rep}"

    mkdir -p $output_dir

    echo "Starting CockroachDB test: threads=$threads, repetition=$rep"

    bash scripts/setup_cockroachdb.sh

    bash scripts/collect_metrics.sh cockroachdb "${output_dir}/metrics.csv" &
    METRICS_PID=$!

    bash scripts/run_ycsb_cockroach.sh $WORKLOAD $threads "${output_dir}/ycsb_output.txt"

    kill $METRICS_PID 2>/dev/null || true
    wait $METRICS_PID 2>/dev/null || true

    python3 scripts/parse_ycsb_output.py "${output_dir}/ycsb_output.txt" > "${output_dir}/ycsb_results.json"
    python3 scripts/calculate_metrics.py "${output_dir}/metrics.csv" > "${output_dir}/resource_metrics.json"

    YCSB_DATA=$(cat "${output_dir}/ycsb_results.json")
    RESOURCE_DATA=$(cat "${output_dir}/resource_metrics.json")

    THROUGHPUT=$(echo $YCSB_DATA | python3 -c "import sys, json; print(json.load(sys.stdin)['throughput'])")
    LATENCY_P99=$(echo $YCSB_DATA | python3 -c "import sys, json; print(json.load(sys.stdin)['latency_p99'])")
    CPU_AVG=$(echo $RESOURCE_DATA | python3 -c "import sys, json; print(json.load(sys.stdin)['cpu_avg'])")
    MEM_AVG=$(echo $RESOURCE_DATA | python3 -c "import sys, json; print(json.load(sys.stdin)['mem_avg'])")

    cat > "${output_dir}/summary.json" << EOF
{
  "database": "CockroachDB",
  "consistency": "ACID",
  "threads": $threads,
  "repetition": $rep,
  "throughput": $THROUGHPUT,
  "latency_p99": $LATENCY_P99,
  "cpu_avg": $CPU_AVG,
  "mem_avg": $MEM_AVG,
  "timestamp": "$TIMESTAMP"
}
EOF

    bash scripts/stop_cockroachdb.sh

    echo "CockroachDB test completed: threads=$threads, repetition=$rep"
    sleep 5
}

test_scylladb() {
    local threads=$1
    local consistency=$2
    local rep=$3
    local output_dir="${RESULTS_DIR}/scylladb_${consistency}/threads_${threads}/rep_${rep}"

    mkdir -p $output_dir

    echo "Starting ScyllaDB test: threads=$threads, consistency=$consistency, repetition=$rep"

    bash scripts/setup_scylladb.sh

    bash scripts/collect_metrics.sh scylladb "${output_dir}/metrics.csv" &
    METRICS_PID=$!

    bash scripts/run_ycsb_scylla.sh $WORKLOAD $threads $consistency "${output_dir}/ycsb_output.txt"

    kill $METRICS_PID 2>/dev/null || true
    wait $METRICS_PID 2>/dev/null || true

    python3 scripts/parse_ycsb_output.py "${output_dir}/ycsb_output.txt" > "${output_dir}/ycsb_results.json"
    python3 scripts/calculate_metrics.py "${output_dir}/metrics.csv" > "${output_dir}/resource_metrics.json"

    YCSB_DATA=$(cat "${output_dir}/ycsb_results.json")
    RESOURCE_DATA=$(cat "${output_dir}/resource_metrics.json")

    THROUGHPUT=$(echo $YCSB_DATA | python3 -c "import sys, json; print(json.load(sys.stdin)['throughput'])")
    LATENCY_P99=$(echo $YCSB_DATA | python3 -c "import sys, json; print(json.load(sys.stdin)['latency_p99'])")
    CPU_AVG=$(echo $RESOURCE_DATA | python3 -c "import sys, json; print(json.load(sys.stdin)['cpu_avg'])")
    MEM_AVG=$(echo $RESOURCE_DATA | python3 -c "import sys, json; print(json.load(sys.stdin)['mem_avg'])")

    cat > "${output_dir}/summary.json" << EOF
{
  "database": "ScyllaDB",
  "consistency": "$consistency",
  "threads": $threads,
  "repetition": $rep,
  "throughput": $THROUGHPUT,
  "latency_p99": $LATENCY_P99,
  "cpu_avg": $CPU_AVG,
  "mem_avg": $MEM_AVG,
  "timestamp": "$TIMESTAMP"
}
EOF

    bash scripts/stop_scylladb.sh

    echo "ScyllaDB test completed: threads=$threads, consistency=$consistency, repetition=$rep"
    sleep 5
}

echo "Installing YCSB..."
bash scripts/install_ycsb.sh

echo ""
echo "=========================================="
echo "Starting CockroachDB Tests"
echo "=========================================="

for threads in "${THREADS_LIST[@]}"; do
    for rep in $(seq 1 $REPETITIONS); do
        test_cockroachdb $threads $rep
    done
done

echo ""
echo "=========================================="
echo "Starting ScyllaDB Tests (ONE consistency)"
echo "=========================================="

for threads in "${THREADS_LIST[@]}"; do
    for rep in $(seq 1 $REPETITIONS); do
        test_scylladb $threads "ONE" $rep
    done
done

echo ""
echo "=========================================="
echo "Starting ScyllaDB Tests (QUORUM consistency)"
echo "=========================================="

for threads in "${THREADS_LIST[@]}"; do
    for rep in $(seq 1 $REPETITIONS); do
        test_scylladb $threads "QUORUM" $rep
    done
done

echo ""
echo "=========================================="
echo "Generating Analysis and Plots"
echo "=========================================="

python3 analysis/aggregate_results.py $RESULTS_DIR "${RESULTS_DIR}/all_results.csv"
python3 analysis/generate_plots.py $RESULTS_DIR

echo ""
echo "=========================================="
echo "Benchmark Suite Completed!"
echo "Results saved to: $RESULTS_DIR"
echo "=========================================="
