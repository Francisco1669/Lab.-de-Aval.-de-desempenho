#!/bin/bash
# Experimento de Custo da Consistência - ScyllaDB Cluster (3 nós, RF=3)

YCSB_HOME="/home/epaim/Lab.-de-Aval.-de-desempenho/ycsb-0.17.0"
WORKLOAD="/home/epaim/Lab.-de-Aval.-de-desempenho/workloads/workload_consistency_test"
RESULTS_DIR="/home/epaim/Lab.-de-Aval.-de-desempenho/results"
OUTPUT_FILE="$RESULTS_DIR/consistency_cluster_results.csv"

# Parâmetros
THREADS=(16 32)
CONSISTENCY_LEVELS=("ONE" "QUORUM" "ALL")
REPETITIONS=3

# Criar cabeçalho do CSV
echo "database,threads,consistency,repetition,throughput,latency_avg,latency_p99,latency_p95,timestamp" > $OUTPUT_FILE

run_test() {
    local threads=$1
    local consistency=$2
    local rep=$3
    
    echo "========================================"
    echo "Teste: $threads threads | $consistency | Rep $rep"
    echo "========================================"
    
    # Limpar tabela
    docker exec scylla-node1 cqlsh 172.20.0.2 -e "TRUNCATE ycsb.usertable" 2>/dev/null
    sleep 2
    
    # Executar YCSB
    output=$($YCSB_HOME/bin/ycsb.sh run cassandra-cql \
        -P $WORKLOAD \
        -p hosts=localhost \
        -p port=9042 \
        -p cassandra.writeconsistencylevel=$consistency \
        -p cassandra.readconsistencylevel=$consistency \
        -threads $threads \
        -s 2>&1)
    
    # Extrair métricas
    throughput=$(echo "$output" | grep "\[OVERALL\], Throughput" | awk -F', ' '{print $3}')
    latency_avg=$(echo "$output" | grep "\[INSERT\], AverageLatency" | awk -F', ' '{print $3}')
    latency_p99=$(echo "$output" | grep "\[INSERT\], 99thPercentileLatency" | awk -F', ' '{print $3}')
    latency_p95=$(echo "$output" | grep "\[INSERT\], 95thPercentileLatency" | awk -F', ' '{print $3}')
    timestamp=$(date -Iseconds)
    
    # Converter latência de us para ms
    latency_avg_ms=$(echo "scale=3; $latency_avg / 1000" | bc)
    latency_p99_ms=$(echo "scale=3; $latency_p99 / 1000" | bc)
    latency_p95_ms=$(echo "scale=3; $latency_p95 / 1000" | bc)
    
    echo "  Throughput: $throughput ops/sec"
    echo "  Latency P99: $latency_p99_ms ms"
    
    # Salvar resultado
    echo "ScyllaDB-Cluster,$threads,$consistency,$rep,$throughput,$latency_avg_ms,$latency_p99_ms,$latency_p95_ms,$timestamp" >> $OUTPUT_FILE
    
    sleep 3
}

echo "============================================"
echo "EXPERIMENTO: CUSTO DA CONSISTÊNCIA"
echo "Cluster: 3 nós | RF=3"
echo "============================================"

total=$((${#THREADS[@]} * ${#CONSISTENCY_LEVELS[@]} * REPETITIONS))
current=0

for threads in "${THREADS[@]}"; do
    for consistency in "${CONSISTENCY_LEVELS[@]}"; do
        for rep in $(seq 1 $REPETITIONS); do
            current=$((current + 1))
            echo ""
            echo ">>> Progresso: $current / $total"
            run_test $threads $consistency $rep
        done
    done
done

echo ""
echo "============================================"
echo "EXPERIMENTO CONCLUÍDO!"
echo "Resultados: $OUTPUT_FILE"
echo "============================================"
cat $OUTPUT_FILE
