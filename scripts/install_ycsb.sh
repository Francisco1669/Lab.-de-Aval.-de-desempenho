#!/bin/bash

set -e

cd "$(dirname "$0")/.."

YCSB_VERSION="0.17.0"
YCSB_DIR="ycsb-${YCSB_VERSION}"

if [ -d "$YCSB_DIR" ]; then
    echo "YCSB already installed at $YCSB_DIR"
    exit 0
fi

echo "Downloading YCSB ${YCSB_VERSION}..."
curl -O --location "https://github.com/brianfrankcooper/YCSB/releases/download/${YCSB_VERSION}/ycsb-${YCSB_VERSION}.tar.gz"

echo "Extracting YCSB..."
tar xfz "ycsb-${YCSB_VERSION}.tar.gz"

rm "ycsb-${YCSB_VERSION}.tar.gz"

echo "YCSB installation completed at $YCSB_DIR"
