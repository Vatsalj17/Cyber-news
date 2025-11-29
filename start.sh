#!/bin/bash

# Ensure cleanup happens on exit
trap "pkill -P $$" EXIT

echo "--- Starting Cyber-News Platform ---"

# 1. Start the Producer (Data Scraper)
echo "[LAUNCH] Starting Producer..."
python3 producer.py &
sleep 2

# 2. Start the Pathway Pipeline (RAG Server)
echo "[LAUNCH] Starting Pathway Pipeline & RAG Server..."
python3 pipeline.py &
sleep 5 # Give it a moment to initialize

# 3. Start the Web Dashboard (Flask App)
echo "[LAUNCH] Starting Web Dashboard on port 5001..."
python3 dashboard_web.py &
sleep 2

# Announce completion
echo ""
echo "------------------------------------------"
echo "✅ All services are running in background."
echo "------------------------------------------"
echo "🖥️  Web UI: http://localhost:5001"
echo "🤖 RAG API: http://localhost:9000"
echo "------------------------------------------"
echo ""
echo "🚀 Launching Interactive CLI..."
echo ""

# 4. Start the CLI Dashboard in the foreground
python3 dashboard_cli.py

# Final message on exit
echo "--- Cyber-News Platform Shutting Down ---"