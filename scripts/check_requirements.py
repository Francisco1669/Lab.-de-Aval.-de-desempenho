#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
Script de Verificação de Pré-requisitos
=============================================================================
Verifica se todas as dependências estão instaladas antes de rodar o benchmark.

Uso:
    python scripts/check_requirements.py
=============================================================================
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def check_command(command: str, name: str) -> bool:
    """Verifica se um comando está disponível."""
    path = shutil.which(command)
    if path:
        print(f"  ✅ {name}: {path}")
        return True
    else:
        print(f"  ❌ {name}: NÃO ENCONTRADO")
        return False


def check_docker() -> bool:
    """Verifica Docker e Docker Compose."""
    print("\n📦 Verificando Docker...")
    
    docker_ok = check_command("docker", "Docker")
    
    # Docker Compose pode ser 'docker-compose' ou 'docker compose'
    compose_ok = check_command("docker-compose", "Docker Compose")
    if not compose_ok:
        # Tentar 'docker compose' (v2)
        try:
            result = subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                print(f"  ✅ Docker Compose (v2): disponível")
                compose_ok = True
        except:
            pass
    
    if docker_ok:
        # Verificar se Docker daemon está rodando
        try:
            result = subprocess.run(
                ["docker", "info"], capture_output=True, timeout=10
            )
            if result.returncode != 0:
                print("  ⚠️  Docker daemon não está rodando!")
                print("     Execute: sudo systemctl start docker")
                return False
        except:
            print("  ⚠️  Não foi possível verificar Docker daemon")
    
    return docker_ok and compose_ok


def check_python() -> bool:
    """Verifica Python e dependências."""
    print("\n🐍 Verificando Python...")
    
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(f"  ✅ Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"  ❌ Python 3.8+ necessário, encontrado: {python_version.major}.{python_version.minor}")
        return False
    
    # Verificar pacotes essenciais
    packages = {
        'pandas': 'pandas',
        'matplotlib': 'matplotlib',
        'numpy': 'numpy',
        'seaborn': 'seaborn'
    }
    
    all_ok = True
    for display_name, import_name in packages.items():
        try:
            __import__(import_name)
            print(f"  ✅ {display_name}: instalado")
        except ImportError:
            print(f"  ❌ {display_name}: não instalado")
            all_ok = False
    
    if not all_ok:
        print("\n  💡 Execute: pip install -r requirements.txt")
    
    return all_ok


def check_java() -> bool:
    """Verifica instalação do Java."""
    print("\n☕ Verificando Java...")
    
    java_ok = check_command("java", "Java")
    
    if java_ok:
        try:
            result = subprocess.run(
                ["java", "-version"], capture_output=True, text=True, timeout=5
            )
            # Java imprime versão no stderr
            version_output = result.stderr or result.stdout
            version_line = version_output.split('\n')[0]
            print(f"     Versão: {version_line}")
        except:
            pass
    else:
        print("  💡 Instale Java 8+:")
        print("     Ubuntu: sudo apt install openjdk-11-jdk")
        print("     Arch: sudo pacman -S jdk11-openjdk")
    
    return java_ok


def check_ycsb() -> bool:
    """Verifica instalação do YCSB."""
    print("\n📊 Verificando YCSB...")
    
    project_root = Path(__file__).parent.parent.absolute()
    ycsb_dir = project_root / "ycsb-0.17.0"
    ycsb_bin = ycsb_dir / "bin" / "ycsb"
    
    if ycsb_dir.exists() and ycsb_bin.exists():
        print(f"  ✅ YCSB 0.17.0: {ycsb_dir}")
        return True
    else:
        print(f"  ❌ YCSB: não encontrado em {ycsb_dir}")
        print("  💡 Execute: ./scripts/install_ycsb.sh")
        print("     ou: python scripts/install_ycsb.py")
        return False


def check_ports() -> bool:
    """Verifica se portas necessárias estão disponíveis."""
    print("\n🔌 Verificando portas...")
    
    import socket
    
    ports = {
        26257: "CockroachDB SQL",
        8080: "CockroachDB Admin",
        9042: "ScyllaDB CQL",
        9160: "ScyllaDB Thrift",
        10000: "ScyllaDB REST"
    }
    
    all_ok = True
    for port, service in ports.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"  ⚠️  Porta {port} ({service}): EM USO")
            all_ok = False
        else:
            print(f"  ✅ Porta {port} ({service}): disponível")
    
    return all_ok


def main():
    print("\n" + "=" * 60)
    print("  VERIFICAÇÃO DE PRÉ-REQUISITOS")
    print("  Benchmark CockroachDB vs ScyllaDB")
    print("=" * 60)
    
    checks = {
        'Docker': check_docker(),
        'Python': check_python(),
        'Java': check_java(),
        'YCSB': check_ycsb(),
        'Portas': check_ports()
    }
    
    print("\n" + "=" * 60)
    print("  RESUMO")
    print("=" * 60)
    
    all_ok = True
    for name, status in checks.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {name}")
        if not status:
            all_ok = False
    
    print("\n" + "=" * 60)
    
    if all_ok:
        print("  ✅ TUDO PRONTO! Pode executar: python main.py")
    else:
        print("  ⚠️  Corrija os problemas acima antes de continuar.")
    
    print("=" * 60 + "\n")
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
