#!/bin/bash

set -e

cd "$(dirname "$0")/.."

echo "Starting ScyllaDB..."
docker-compose -f docker/docker-compose-scylladb.yml up -d

echo "Waiting for ScyllaDB to be ready..."
for i in {1..60}; do
    if docker exec scylladb cqlsh -e "DESCRIBE KEYSPACES;" > /dev/null 2>&1; then
        echo "ScyllaDB is ready!"
        break
    fi
    echo "Waiting... ($i/60)"
    sleep 2
done

echo "ScyllaDB setup completed!"
