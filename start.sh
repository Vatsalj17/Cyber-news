#!/usr/bin/env bash

set -euo pipefail

cleanup() {
	echo "Performing cleanup..."
	[[ -n "${PRODUCER_PID:-}" ]] && kill "$PRODUCER_PID" 2>/dev/null || true
	[[ -n "${PIPELINE_PID:-}" ]] && kill "$PIPELINE_PID" 2>/dev/null || true
	echo "Cleanup complete."
}

trap "echo 'Interrupted!'; cleanup; exit 1" SIGINT SIGTERM
trap "echo 'Error detected!'; cleanup; exit 1" ERR

# --- 1. Start Producer ---
echo "[1/3] Starting Producer..."
python3 -u ./producer.py >producer.log 2>&1 &
PRODUCER_PID=$!
sleep 1
if ! kill -0 "$PRODUCER_PID" 2>/dev/null; then
	echo "Producer FAILED to start. Exiting."
	cleanup; exit 1
fi
echo "      Producer PID: $PRODUCER_PID"

# --- 2. Start Pipeline ---
echo "[2/3] Starting Pipeline (RAG Engine)..."
python3 -u ./pipeline.py >pipeline.log 2>&1 &
PIPELINE_PID=$!
sleep 1
if ! kill -0 "$PIPELINE_PID" 2>/dev/null; then
	echo "Pipeline FAILED to start. Exiting."
	cleanup; exit 1
fi
echo "      Pipeline PID: $PIPELINE_PID"

# --- 3. Wait for Services ---
echo "Waiting for Pipeline (Port 9000)..."
ready=0
for i in {1..30}; do
	if ss -lnt | grep -q ":9000"; then
		ready=1
		break
	fi
	if ! kill -0 "$PIPELINE_PID" 2>/dev/null; then
		echo "Pipeline CRASHED. Check pipeline.log"
		cleanup; exit 1
	fi
	sleep 1
done

if [[ $ready -ne 1 ]]; then
	echo "Pipeline Timeout."
	cleanup; exit 1
fi

# Optional: Wait for Ollama (Prevent dashboard crash on first run)
echo "Checking AI Link..."
# If OLLAMA_HOST is set, use it, else default localhost
HOST=${OLLAMA_HOST:-http://localhost:11434}
# We don't exit on failure here, just warn, because Dashboard handles offline mode
if curl -s "$HOST" > /dev/null; then
    echo "AI Brain Connected ($HOST)."
else
    echo "Warning: AI Host unreachable ($HOST). Dashboard will run in reduced mode."
fi

# --- 4. Launch Dashboard ---
echo "[3/3] Launching Dashboard..."
python3 ./dashboard.py || true

cleanup
exit 0
