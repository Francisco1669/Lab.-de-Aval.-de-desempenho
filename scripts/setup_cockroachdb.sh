#!/bin/bash

set -e

cd "$(dirname "$0")/.."

echo "Starting CockroachDB..."
docker-compose -f docker/docker-compose-cockroachdb.yml up -d

echo "Waiting for CockroachDB to be ready..."
for i in {1..30}; do
    if docker exec cockroachdb ./cockroach sql --insecure --execute="SELECT 1;" > /dev/null 2>&1; then
        echo "CockroachDB is ready!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

echo "Creating database..."
docker exec cockroachdb ./cockroach sql --insecure --execute="CREATE DATABASE IF NOT EXISTS ycsb;"

echo "CockroachDB setup completed!"
