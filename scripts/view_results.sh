#!/bin/bash

if [ $# -lt 1 ]; then
    echo "Usage: $0 <results_directory>"
    exit 1
fi

RESULTS_DIR=$1

echo "=========================================="
echo "Summary of Results"
echo "=========================================="
echo ""

for summary in $(find $RESULTS_DIR -name "summary.json" | sort); do
    echo "File: $summary"
    cat $summary | python3 -m json.tool
    echo ""
done

if [ -f "${RESULTS_DIR}/all_results.csv" ]; then
    echo "=========================================="
    echo "Aggregated Results (CSV)"
    echo "=========================================="
    column -t -s',' "${RESULTS_DIR}/all_results.csv"
fi
