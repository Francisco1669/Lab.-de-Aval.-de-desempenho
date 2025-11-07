#!/bin/bash

set -e

if [ $# -lt 3 ]; then
    echo "Usage: $0 <workload_file> <threads> <output_file>"
    exit 1
fi

WORKLOAD=$1
THREADS=$2
OUTPUT=$3

cd "$(dirname "$0")/.."

source config/cockroachdb_config.sh

YCSB_DIR="ycsb-0.17.0"

if [ ! -d "$YCSB_DIR" ]; then
    echo "YCSB not found. Please run install_ycsb.sh first."
    exit 1
fi

echo "Loading data into CockroachDB..."
$YCSB_DIR/bin/ycsb load jdbc -P $WORKLOAD \
    -p db.driver=org.postgresql.Driver \
    -p db.url="jdbc:postgresql://${COCKROACH_HOST}:${COCKROACH_PORT}/${COCKROACH_DATABASE}?sslmode=disable" \
    -p db.user=$COCKROACH_USER \
    -p jdbc.fetchsize=10 \
    -p jdbc.autocommit=true \
    -p db.batchsize=1000 \
    -threads $THREADS > /dev/null 2>&1

echo "Running benchmark on CockroachDB..."
$YCSB_DIR/bin/ycsb run jdbc -P $WORKLOAD \
    -p db.driver=org.postgresql.Driver \
    -p db.url="jdbc:postgresql://${COCKROACH_HOST}:${COCKROACH_PORT}/${COCKROACH_DATABASE}?sslmode=disable" \
    -p db.user=$COCKROACH_USER \
    -p jdbc.fetchsize=10 \
    -p jdbc.autocommit=true \
    -p db.batchsize=1000 \
    -threads $THREADS > $OUTPUT

echo "Benchmark completed. Results saved to $OUTPUT"
