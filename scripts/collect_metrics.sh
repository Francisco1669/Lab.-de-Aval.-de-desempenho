#!/bin/bash

if [ $# -lt 2 ]; then
    echo "Usage: $0 <container_name> <output_file>"
    exit 1
fi

CONTAINER=$1
OUTPUT=$2

echo "timestamp,cpu_percent,memory_mb" > $OUTPUT

while docker ps | grep -q $CONTAINER; do
    STATS=$(docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}}" $CONTAINER 2>/dev/null)

    if [ -n "$STATS" ]; then
        CPU=$(echo $STATS | cut -d',' -f1 | sed 's/%//')
        MEM_FULL=$(echo $STATS | cut -d',' -f2)
        MEM=$(echo $MEM_FULL | cut -d'/' -f1 | sed 's/MiB//' | sed 's/GiB/*1024/' | bc 2>/dev/null || echo "0")

        TIMESTAMP=$(date +%s)
        echo "$TIMESTAMP,$CPU,$MEM" >> $OUTPUT
    fi

    sleep 1
done
