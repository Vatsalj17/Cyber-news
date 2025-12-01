#!/bin/bash

# --- CONFIGURATION ---
VENV_DIR=".venv"
LOG_DIR="logs"
mkdir -p "$LOG_DIR"

# Colors for pretty output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Ensure cleanup happens on exit (kills all background jobs started by this script)
trap "kill 0" EXIT

echo -e "${BLUE}--- Starting Cyber-News Platform ---${NC}"

# 1. Automatic Virtual Environment Check
if [[ -z "$VIRTUAL_ENV" ]]; then
    if [[ -d "$VENV_DIR" ]]; then
        echo -e "${YELLOW}[INFO] Activating virtual environment...${NC}"
        source "$VENV_DIR/bin/activate"
    else
        echo -e "${RED}[ERROR] Virtual environment not found. Please run ./setup.sh first.${NC}"
        exit 1
    fi
fi

# Function to check if a port is in use (requires lsof or netstat, but python is safer here)
check_port() {
    python3 -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); result = s.connect_ex(('localhost', $1)); s.close(); exit(0 if result == 0 else 1)"
}

# Function to wait for a service to start
wait_for_service() {
    local port=$1
    local name=$2
    local retries=30
    echo -n "   Waiting for $name (Port $port)..."
    while ! check_port $port; do
        sleep 1
        ((retries--))
        if [[ $retries -eq 0 ]]; then
            echo -e " ${RED}[FAILED]${NC}"
            echo -e "${RED}[!] $name failed to start. Check logs in $LOG_DIR/${name}.log${NC}"
            exit 1
        fi
    done
    echo -e " ${GREEN}[OK]${NC}"
}

# 2. Start the Producer (Data Scraper)
echo -e "${BLUE}[LAUNCH] Starting Producer...${NC}"
python3 -u ./producer.py > "$LOG_DIR/producer.log" 2>&1 &
PRODUCER_PID=$!
# Quick check to ensure it didn't die immediately
sleep 1
if ! kill -0 $PRODUCER_PID 2>/dev/null; then
    echo -e "${RED}[!] Producer crashed immediately. Check logs.${NC}"
    exit 1
fi

# 3. Start the Pathway Pipeline (RAG Server)
echo -e "${BLUE}[LAUNCH] Starting Pathway Pipeline & RAG Server...${NC}"
python3 -u ./pipeline.py > "$LOG_DIR/pipeline.log" 2>&1 &
wait_for_service 9000 "RAG API"

# 4. Start the Web Dashboard (Flask App)
echo -e "${BLUE}[LAUNCH] Starting Web Dashboard...${NC}"
python3 -u ./dashboard_web.py > "$LOG_DIR/dashboard_web.log" 2>&1 &
wait_for_service 5001 "Web UI"

# Announce completion
echo ""
echo "------------------------------------------"
echo -e "✅ ${GREEN}All services are online.${NC}"
echo "------------------------------------------"
echo -e "🖥️  Web UI:  ${BLUE}http://localhost:5001${NC}"
echo -e "🤖 RAG API: ${BLUE}http://localhost:9000${NC}"
echo "------------------------------------------"
echo ""
echo -e "🚀 Launching Interactive CLI..."
echo ""

# 5. Start the CLI Dashboard in the foreground
python3 dashboard_cli.py

# Final message on exit
echo -e "\n${BLUE}--- Cyber-News Platform Shutting Down ---${NC}"