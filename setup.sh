#!/usr/bin/env bash

# Colors for pretty output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}[+] Initializing Cyber-News Setup...${NC}"

# 1. Check Python Version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[!] Python 3 is not installed.${NC}"
    exit 1
fi

# 2. Create Virtual Environment (if not exists)
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}[+] Creating Python Virtual Environment (.venv)...${NC}"
    python3 -m venv .venv
fi

# Activate Venv
source .venv/bin/activate

# 3. Create Lighter Requirements File (If missing)
# We use the lighter list to avoid downloading 3GB of unnecessary Nvidia/Torch libs for the reviewer
if [ ! -f "requirements.local.txt" ]; then
    echo -e "${BLUE}[+] Generating optimized requirements list...${NC}"
    cat <<EOF > requirements.local.txt
requests
beautifulsoup4
playwright
pathway
sentence-transformers
textual
ollama
lxml
pdf2image
unstructured
pathway[xpack-llm-docs]
EOF
fi

# 4. Install Dependencies
echo -e "${BLUE}[+] Installing Python Dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.local.txt

# 5. Install Playwright Browsers
echo -e "${BLUE}[+] Installing Headless Browsers...${NC}"
playwright install chromium

# 6. Check/Install Ollama
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}[!] Ollama is not found.${NC}"
    echo -e "${BLUE}[+] Attempting to install Ollama (Requires Sudo)...${NC}"
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo -e "${GREEN}[OK] Ollama is detected.${NC}"
fi

# 7. Pull the AI Model
echo -e "${BLUE}[+] Checking AI Model (Phi-3)...${NC}"
# Start ollama in background just to pull, then kill it? 
# Better to ask user to ensure it's running, or try to check API.
if systemctl is-active --quiet ollama; then
    ollama pull phi3
else
    echo -e "${RED}[!] Ollama service is not running.${NC}"
    echo "    Please run 'ollama serve' in a separate terminal, then run this script again."
    echo "    Or proceed if you know what you are doing."
fi

echo -e "${GREEN}[SUCCESS] Setup Complete!${NC}"
echo -e "To run the project locally:"
echo -e "  1. ${BLUE}source .venv/bin/activate${NC}"
echo -e "  2. ${BLUE}./start.sh${NC}"
