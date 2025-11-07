#!/bin/bash

cd "$(dirname "$0")/.."

echo "Stopping CockroachDB..."
docker-compose -f docker/docker-compose-cockroachdb.yml down -v

echo "CockroachDB stopped and volumes removed."
