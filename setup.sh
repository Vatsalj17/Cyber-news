#!/usr/bin/env bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}[+] Initializing Cyber-News Setup...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[!] Python 3 is not installed.${NC}"
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo -e "${BLUE}[+] Creating Python Virtual Environment (.venv)...${NC}"
    python3 -m venv .venv
fi

source .venv/bin/activate

echo -e "${BLUE}[+] Installing Python Dependencies...${NC}"
pip install -r requirements.txt

echo -e "${BLUE}[+] Installing Headless Browsers...${NC}"
playwright install chromium

if ! command -v ollama &> /dev/null; then
    echo -e "${RED}[!] Ollama is not found.${NC}"
    echo -e "${BLUE}[+] Attempting to install Ollama (Requires Sudo)...${NC}"
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo -e "${GREEN}[OK] Ollama is detected.${NC}"
fi

echo -e "${BLUE}[+] Checking AI Model (Phi-3)...${NC}"
if systemctl is-active --quiet ollama; then
    ollama pull phi3
else
    echo -e "${RED}[!] Ollama service is not running.${NC}"
    echo "    Please run 'ollama serve' in a separate terminal, then run this script again."
    echo "    Or proceed if you know what you are doing."
fi

echo -e "${GREEN}[SUCCESS] Setup Complete!${NC}"
echo -e "To run the project locally: ${BLUE}./start.sh${NC}"
