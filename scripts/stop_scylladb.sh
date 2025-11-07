#!/bin/bash

cd "$(dirname "$0")/.."

echo "Stopping ScyllaDB..."
docker-compose -f docker/docker-compose-scylladb.yml down -v

echo "ScyllaDB stopped and volumes removed."
