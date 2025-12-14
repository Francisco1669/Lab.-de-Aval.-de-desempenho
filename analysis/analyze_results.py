#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
Script de Análise e Geração de Gráficos
=============================================================================
Gera visualizações a partir dos resultados do benchmark.

Uso:
    python analysis/analyze_results.py [--results-dir results]
=============================================================================
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats


def load_results(results_dir: Path) -> pd.DataFrame:
    """Carrega resultados do CSV."""
    csv_file = results_dir / "results.csv"
    
    if not csv_file.exists():
        print(f"❌ Arquivo não encontrado: {csv_file}")
        sys.exit(1)
    
    df = pd.read_csv(csv_file)
    # Filtrar apenas testes bem-sucedidos
    df = df[df['success'] == True]
    return df


def create_throughput_comparison(df: pd.DataFrame, output_dir: Path):
    """Gráfico de comparação de throughput."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Agrupar por banco, consistência e threads
    grouped = df.groupby(['database', 'consistency', 'threads']).agg({
        'throughput': ['mean', 'std']
    }).reset_index()
    grouped.columns = ['database', 'consistency', 'threads', 'throughput_mean', 'throughput_std']
    
    # Criar label combinada
    grouped['label'] = grouped['database'] + ' (' + grouped['consistency'] + ')'
    
    # Plotar
    labels = grouped['label'].unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(labels)))
    
    for i, label in enumerate(labels):
        data = grouped[grouped['label'] == label].sort_values('threads')
        ax.errorbar(
            data['threads'], data['throughput_mean'], 
            yerr=data['throughput_std'],
            marker='o', label=label, linewidth=2, capsize=5,
            color=colors[i]
        )
    
    ax.set_xlabel('Número de Threads', fontsize=12)
    ax.set_ylabel('Throughput (ops/sec)', fontsize=12)
    ax.set_title('Throughput vs Concorrência', fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log', base=2)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'throughput_comparison.png', dpi=300)
    plt.close()
    print(f"✅ Gráfico salvo: throughput_comparison.png")


def create_latency_comparison(df: pd.DataFrame, output_dir: Path):
    """Gráfico de comparação de latência P99."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    grouped = df.groupby(['database', 'consistency', 'threads']).agg({
        'latency_p99': ['mean', 'std']
    }).reset_index()
    grouped.columns = ['database', 'consistency', 'threads', 'latency_mean', 'latency_std']
    grouped['label'] = grouped['database'] + ' (' + grouped['consistency'] + ')'
    
    labels = grouped['label'].unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(labels)))
    
    for i, label in enumerate(labels):
        data = grouped[grouped['label'] == label].sort_values('threads')
        ax.errorbar(
            data['threads'], data['latency_mean'],
            yerr=data['latency_std'],
            marker='s', label=label, linewidth=2, capsize=5,
            color=colors[i]
        )
    
    ax.set_xlabel('Número de Threads', fontsize=12)
    ax.set_ylabel('Latência P99 (ms)', fontsize=12)
    ax.set_title('Latência P99 vs Concorrência', fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log', base=2)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'latency_comparison.png', dpi=300)
    plt.close()
    print(f"✅ Gráfico salvo: latency_comparison.png")


def create_resource_usage_plot(df: pd.DataFrame, output_dir: Path):
    """Gráfico de uso de recursos (CPU e Memória)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    grouped = df.groupby(['database', 'consistency', 'threads']).agg({
        'cpu_avg': 'mean',
        'memory_avg': 'mean'
    }).reset_index()
    grouped['label'] = grouped['database'] + ' (' + grouped['consistency'] + ')'
    
    labels = grouped['label'].unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(labels)))
    
    # CPU
    for i, label in enumerate(labels):
        data = grouped[grouped['label'] == label].sort_values('threads')
        ax1.plot(data['threads'], data['cpu_avg'], marker='o', 
                 label=label, linewidth=2, color=colors[i])
    
    ax1.set_xlabel('Número de Threads', fontsize=12)
    ax1.set_ylabel('CPU Médio (%)', fontsize=12)
    ax1.set_title('Uso de CPU vs Concorrência', fontsize=14)
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log', base=2)
    
    # Memória
    for i, label in enumerate(labels):
        data = grouped[grouped['label'] == label].sort_values('threads')
        ax2.plot(data['threads'], data['memory_avg'], marker='s',
                 label=label, linewidth=2, color=colors[i])
    
    ax2.set_xlabel('Número de Threads', fontsize=12)
    ax2.set_ylabel('Memória Média (MB)', fontsize=12)
    ax2.set_title('Uso de Memória vs Concorrência', fontsize=14)
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log', base=2)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'resource_usage.png', dpi=300)
    plt.close()
    print(f"✅ Gráfico salvo: resource_usage.png")


def create_consistency_impact_plot(df: pd.DataFrame, output_dir: Path):
    """Gráfico de impacto da consistência no ScyllaDB."""
    scylla_df = df[df['database'] == 'ScyllaDB']
    
    if scylla_df.empty:
        print("⚠️ Sem dados do ScyllaDB para análise de consistência")
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Throughput por nível de consistência
    grouped = scylla_df.groupby(['consistency', 'threads']).agg({
        'throughput': 'mean',
        'latency_p99': 'mean'
    }).reset_index()
    
    consistency_order = ['ONE', 'QUORUM', 'ALL']
    colors = {'ONE': 'green', 'QUORUM': 'orange', 'ALL': 'red'}
    
    for consistency in consistency_order:
        if consistency in grouped['consistency'].values:
            data = grouped[grouped['consistency'] == consistency].sort_values('threads')
            ax1.plot(data['threads'], data['throughput'], marker='o',
                     label=consistency, linewidth=2, color=colors[consistency])
            ax2.plot(data['threads'], data['latency_p99'], marker='s',
                     label=consistency, linewidth=2, color=colors[consistency])
    
    ax1.set_xlabel('Número de Threads', fontsize=12)
    ax1.set_ylabel('Throughput (ops/sec)', fontsize=12)
    ax1.set_title('Impacto da Consistência no Throughput', fontsize=14)
    ax1.legend(title='Consistência', loc='best')
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log', base=2)
    
    ax2.set_xlabel('Número de Threads', fontsize=12)
    ax2.set_ylabel('Latência P99 (ms)', fontsize=12)
    ax2.set_title('Impacto da Consistência na Latência', fontsize=14)
    ax2.legend(title='Consistência', loc='best')
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log', base=2)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'consistency_impact.png', dpi=300)
    plt.close()
    print(f"✅ Gráfico salvo: consistency_impact.png")


def create_box_plots(df: pd.DataFrame, output_dir: Path):
    """Box plots para visualizar distribuição."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    df['label'] = df['database'] + '\n(' + df['consistency'] + ')'
    
    # Throughput
    sns.boxplot(data=df, x='label', y='throughput', ax=ax1, palette='Set2')
    ax1.set_xlabel('')
    ax1.set_ylabel('Throughput (ops/sec)', fontsize=12)
    ax1.set_title('Distribuição do Throughput', fontsize=14)
    ax1.tick_params(axis='x', rotation=45)
    
    # Latência
    sns.boxplot(data=df, x='label', y='latency_p99', ax=ax2, palette='Set2')
    ax2.set_xlabel('')
    ax2.set_ylabel('Latência P99 (ms)', fontsize=12)
    ax2.set_title('Distribuição da Latência P99', fontsize=14)
    ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'distribution_boxplots.png', dpi=300)
    plt.close()
    print(f"✅ Gráfico salvo: distribution_boxplots.png")


def create_heatmap(df: pd.DataFrame, output_dir: Path):
    """Heatmap de throughput por configuração."""
    pivot = df.pivot_table(
        values='throughput',
        index=['database', 'consistency'],
        columns='threads',
        aggfunc='mean'
    )
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(pivot, annot=True, fmt='.0f', cmap='YlOrRd', ax=ax)
    ax.set_title('Heatmap de Throughput (ops/sec)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Threads', fontsize=12)
    ax.set_ylabel('')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'throughput_heatmap.png', dpi=300)
    plt.close()
    print(f"✅ Gráfico salvo: throughput_heatmap.png")


def generate_statistical_summary(df: pd.DataFrame, output_dir: Path):
    """Gera resumo estatístico dos resultados."""
    summary_file = output_dir / 'statistical_summary.txt'
    
    with open(summary_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("RESUMO ESTATÍSTICO DO BENCHMARK\n")
        f.write("=" * 80 + "\n\n")
        
        grouped = df.groupby(['database', 'consistency', 'threads']).agg({
            'throughput': ['mean', 'std', 'min', 'max', 'count'],
            'latency_p99': ['mean', 'std', 'min', 'max'],
            'latency_avg': ['mean', 'std'],
            'cpu_avg': ['mean', 'std'],
            'memory_avg': ['mean', 'std']
        })
        
        for idx, row in grouped.iterrows():
            db, cons, threads = idx
            f.write(f"\n{'='*60}\n")
            f.write(f"Database: {db} | Consistência: {cons} | Threads: {threads}\n")
            f.write(f"{'='*60}\n")
            f.write(f"Amostras: {int(row[('throughput', 'count')])}\n\n")
            
            f.write("Throughput (ops/sec):\n")
            f.write(f"  Média: {row[('throughput', 'mean')]:.2f}\n")
            f.write(f"  Desvio Padrão: {row[('throughput', 'std')]:.2f}\n")
            f.write(f"  Mín/Máx: {row[('throughput', 'min')]:.2f} / {row[('throughput', 'max')]:.2f}\n\n")
            
            f.write("Latência P99 (ms):\n")
            f.write(f"  Média: {row[('latency_p99', 'mean')]:.2f}\n")
            f.write(f"  Desvio Padrão: {row[('latency_p99', 'std')]:.2f}\n\n")
            
            f.write("Uso de Recursos:\n")
            f.write(f"  CPU Médio: {row[('cpu_avg', 'mean')]:.2f}%\n")
            f.write(f"  Memória Média: {row[('memory_avg', 'mean')]:.2f} MB\n")
        
        # Comparação geral
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("COMPARAÇÃO GERAL\n")
        f.write("=" * 80 + "\n\n")
        
        for db in df['database'].unique():
            db_data = df[df['database'] == db]
            f.write(f"\n{db}:\n")
            f.write(f"  Throughput médio geral: {db_data['throughput'].mean():.2f} ops/sec\n")
            f.write(f"  Latência P99 média geral: {db_data['latency_p99'].mean():.2f} ms\n")
            f.write(f"  Melhor throughput: {db_data['throughput'].max():.2f} ops/sec\n")
    
    print(f"✅ Resumo salvo: statistical_summary.txt")


def main():
    parser = argparse.ArgumentParser(
        description='Análise e visualização dos resultados do benchmark'
    )
    parser.add_argument(
        '--results-dir', type=str, default='results',
        help='Diretório com os resultados'
    )
    
    args = parser.parse_args()
    results_dir = Path(args.results_dir)
    
    print("\n" + "=" * 50)
    print("📊 ANÁLISE DE RESULTADOS DO BENCHMARK")
    print("=" * 50 + "\n")
    
    # Carregar dados
    print("📁 Carregando resultados...")
    df = load_results(results_dir)
    print(f"   {len(df)} registros carregados\n")
    
    # Criar diretório para plots
    plots_dir = results_dir / 'plots'
    plots_dir.mkdir(exist_ok=True)
    
    # Gerar visualizações
    print("📈 Gerando gráficos...")
    
    try:
        create_throughput_comparison(df, plots_dir)
        create_latency_comparison(df, plots_dir)
        create_resource_usage_plot(df, plots_dir)
        create_consistency_impact_plot(df, plots_dir)
        create_box_plots(df, plots_dir)
        create_heatmap(df, plots_dir)
        generate_statistical_summary(df, plots_dir)
    except Exception as e:
        print(f"⚠️ Erro ao gerar gráficos: {e}")
    
    print(f"\n✅ Análise completa! Gráficos em: {plots_dir}")


if __name__ == "__main__":
    main()
