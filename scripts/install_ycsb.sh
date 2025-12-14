#!/bin/bash
# =============================================================================
# Script de Instalação do YCSB
# =============================================================================
# Este script baixa e configura o Yahoo! Cloud Serving Benchmark (YCSB)
# Compatível com: Linux (Ubuntu, Arch), macOS, Windows (WSL/Git Bash)
#
# Uso: ./scripts/install_ycsb.sh
# =============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configurações
YCSB_VERSION="0.17.0"
YCSB_DIR="ycsb-${YCSB_VERSION}"
YCSB_URL="https://github.com/brianfrankcooper/YCSB/releases/download/${YCSB_VERSION}/ycsb-${YCSB_VERSION}.tar.gz"

# Ir para o diretório raiz do projeto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Instalação do YCSB ${YCSB_VERSION}${NC}"
echo -e "${YELLOW}========================================${NC}"

# Verificar se já existe
if [ -d "$YCSB_DIR" ]; then
    echo -e "${GREEN}✅ YCSB já está instalado em ${YCSB_DIR}${NC}"
    echo "   Para reinstalar, remova o diretório primeiro:"
    echo "   rm -rf ${YCSB_DIR}"
    exit 0
fi

# Verificar dependências
echo -e "\n${YELLOW}📋 Verificando dependências...${NC}"

# Verificar Java
if ! command -v java &> /dev/null; then
    echo -e "${RED}❌ Java não encontrado!${NC}"
    echo "   Instale o Java 8 ou superior:"
    echo "   - Ubuntu/Debian: sudo apt install openjdk-11-jdk"
    echo "   - Arch: sudo pacman -S jdk11-openjdk"
    echo "   - macOS: brew install openjdk@11"
    exit 1
fi

JAVA_VERSION=$(java -version 2>&1 | head -n 1)
echo -e "${GREEN}✅ Java encontrado: ${JAVA_VERSION}${NC}"

# Verificar curl ou wget
if command -v curl &> /dev/null; then
    DOWNLOADER="curl"
elif command -v wget &> /dev/null; then
    DOWNLOADER="wget"
else
    echo -e "${RED}❌ curl ou wget não encontrado!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Downloader: ${DOWNLOADER}${NC}"

# Baixar YCSB
echo -e "\n${YELLOW}📥 Baixando YCSB ${YCSB_VERSION}...${NC}"
TARFILE="ycsb-${YCSB_VERSION}.tar.gz"

if [ "$DOWNLOADER" = "curl" ]; then
    curl -L -o "$TARFILE" "$YCSB_URL"
else
    wget -O "$TARFILE" "$YCSB_URL"
fi

# Extrair
echo -e "\n${YELLOW}📦 Extraindo YCSB...${NC}"
tar xzf "$TARFILE"

# Limpar arquivo tar
rm -f "$TARFILE"

# Verificar instalação
if [ -d "$YCSB_DIR" ] && [ -f "$YCSB_DIR/bin/ycsb" ]; then
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ YCSB instalado com sucesso!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "   Diretório: ${PROJECT_ROOT}/${YCSB_DIR}"
    echo -e "   Binário: ${YCSB_DIR}/bin/ycsb"
    echo ""
    echo -e "   ${YELLOW}Bindings disponíveis:${NC}"
    ls -1 "$YCSB_DIR" | grep -E "^(jdbc|cassandra|scylla)" | head -5 || echo "   (verificar diretório)"
else
    echo -e "${RED}❌ Erro na instalação do YCSB${NC}"
    exit 1
fi

# Tornar executável
chmod +x "$YCSB_DIR/bin/ycsb"
chmod +x "$YCSB_DIR/bin/ycsb.sh" 2>/dev/null || true

# Baixar driver PostgreSQL JDBC (necessário para CockroachDB)
echo -e "\n${YELLOW}📥 Baixando driver PostgreSQL JDBC...${NC}"
POSTGRES_DRIVER_URL="https://jdbc.postgresql.org/download/postgresql-42.6.0.jar"
POSTGRES_DRIVER_PATH="$YCSB_DIR/jdbc-binding/lib/postgresql-42.6.0.jar"

if [ "$DOWNLOADER" = "curl" ]; then
    curl -L -o "$POSTGRES_DRIVER_PATH" "$POSTGRES_DRIVER_URL"
else
    wget -O "$POSTGRES_DRIVER_PATH" "$POSTGRES_DRIVER_URL"
fi

if [ -f "$POSTGRES_DRIVER_PATH" ]; then
    echo -e "${GREEN}✅ Driver PostgreSQL JDBC instalado${NC}"
else
    echo -e "${RED}⚠️  Falha ao baixar driver PostgreSQL${NC}"
fi

echo -e "\n${GREEN}Pronto para executar benchmarks!${NC}"
