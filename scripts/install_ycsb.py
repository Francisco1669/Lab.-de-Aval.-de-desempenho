#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
Script de Instalação do YCSB (Cross-Platform)
=============================================================================
Alternativa Python ao script shell para compatibilidade Windows/Linux.

Uso:
    python scripts/install_ycsb.py
=============================================================================
"""

import os
import sys
import tarfile
import urllib.request
import shutil
from pathlib import Path

# Configurações
YCSB_VERSION = "0.17.0"
YCSB_DIR = f"ycsb-{YCSB_VERSION}"
YCSB_URL = f"https://github.com/brianfrankcooper/YCSB/releases/download/{YCSB_VERSION}/ycsb-{YCSB_VERSION}.tar.gz"


def main():
    print("=" * 50)
    print(f"  Instalação do YCSB {YCSB_VERSION}")
    print("=" * 50)
    
    # Diretório do projeto
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    os.chdir(project_root)
    
    ycsb_path = project_root / YCSB_DIR
    
    # Verificar se já existe
    if ycsb_path.exists():
        print(f"\n✅ YCSB já está instalado em {ycsb_path}")
        print("   Para reinstalar, remova o diretório primeiro.")
        return 0
    
    # Verificar Java
    print("\n📋 Verificando Java...")
    java_check = os.system("java -version")
    if java_check != 0:
        print("\n❌ Java não encontrado!")
        print("   Instale o Java 8 ou superior.")
        return 1
    
    # Baixar YCSB
    print(f"\n📥 Baixando YCSB {YCSB_VERSION}...")
    tarfile_name = f"ycsb-{YCSB_VERSION}.tar.gz"
    
    try:
        urllib.request.urlretrieve(YCSB_URL, tarfile_name, reporthook=download_progress)
        print()  # Nova linha após progress
    except Exception as e:
        print(f"\n❌ Erro ao baixar: {e}")
        return 1
    
    # Extrair
    print("\n📦 Extraindo YCSB...")
    try:
        with tarfile.open(tarfile_name, "r:gz") as tar:
            tar.extractall()
    except Exception as e:
        print(f"❌ Erro ao extrair: {e}")
        return 1
    
    # Limpar
    os.remove(tarfile_name)
    
    # Verificar
    if ycsb_path.exists() and (ycsb_path / "bin" / "ycsb").exists():
        print("\n" + "=" * 50)
        print("✅ YCSB instalado com sucesso!")
        print("=" * 50)
        print(f"   Diretório: {ycsb_path}")
        return 0
    else:
        print("❌ Erro na instalação do YCSB")
        return 1


def download_progress(block_num, block_size, total_size):
    """Callback para mostrar progresso do download."""
    downloaded = block_num * block_size
    percent = min(100, downloaded * 100 / total_size)
    bar_len = 40
    filled = int(bar_len * percent / 100)
    bar = '█' * filled + '░' * (bar_len - filled)
    sys.stdout.write(f'\r   [{bar}] {percent:.1f}%')
    sys.stdout.flush()


if __name__ == "__main__":
    sys.exit(main())
