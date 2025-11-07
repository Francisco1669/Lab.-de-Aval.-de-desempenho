#!/bin/bash

set -e

if [ $# -lt 4 ]; then
    echo "Usage: $0 <workload_file> <threads> <consistency_level> <output_file>"
    exit 1
fi

WORKLOAD=$1
THREADS=$2
CONSISTENCY=$3
OUTPUT=$4

cd "$(dirname "$0")/.."

source config/scylladb_config.sh

YCSB_DIR="ycsb-0.17.0"

if [ ! -d "$YCSB_DIR" ]; then
    echo "YCSB not found. Please run install_ycsb.sh first."
    exit 1
fi

echo "Loading data into ScyllaDB with consistency level: $CONSISTENCY..."
$YCSB_DIR/bin/ycsb load cassandra-cql -P $WORKLOAD \
    -p hosts=$SCYLLA_HOST \
    -p port=$SCYLLA_PORT \
    -p cassandra.readconsistencylevel=$CONSISTENCY \
    -p cassandra.writeconsistencylevel=$CONSISTENCY \
    -threads $THREADS > /dev/null 2>&1

echo "Running benchmark on ScyllaDB..."
$YCSB_DIR/bin/ycsb run cassandra-cql -P $WORKLOAD \
    -p hosts=$SCYLLA_HOST \
    -p port=$SCYLLA_PORT \
    -p cassandra.readconsistencylevel=$CONSISTENCY \
    -p cassandra.writeconsistencylevel=$CONSISTENCY \
    -threads $THREADS > $OUTPUT

echo "Benchmark completed. Results saved to $OUTPUT"
