#!/usr/bin/env bash

set -euo pipefail

cleanup() {
	echo "Performing cleanup..."
	[[ -n "${PRODUCER_PID:-}" ]] && kill "$PRODUCER_PID" 2>/dev/null || true
	[[ -n "${PIPELINE_PID:-}" ]] && kill "$PIPELINE_PID" 2>/dev/null || true
	# pkill -9 "ollama" || true
	echo "Cleanup complete."
}

# Trap Ctrl+C, SIGTERM, ERR
trap "echo 'Interrupted!'; cleanup; exit 1" SIGINT SIGTERM
trap "echo 'Error detected!'; cleanup; exit 1" ERR

echo "[1/3] Starting Producer..."
python3 -u ./producer.py >producer.log 2>&1 &
PRODUCER_PID=$!
sleep 1

# Check if producer died immediately
if ! kill -0 "$PRODUCER_PID" 2>/dev/null; then
	echo "Producer FAILED to start. Exiting."
	cleanup
	exit 1
fi
echo "      Producer PID: $PRODUCER_PID"

echo "[2/3] Starting Pipeline (RAG Engine)..."
python3 -u ./pipeline.py >pipeline.log 2>&1 &
PIPELINE_PID=$!
sleep 1

# Check if pipeline died immediately
if ! kill -0 "$PIPELINE_PID" 2>/dev/null; then
	echo "Pipeline FAILED to start. Exiting."
	cleanup
	exit 1
fi
echo "      Pipeline PID: $PIPELINE_PID"

echo "Waiting for Pipeline to open port 9000..."
ready=0
for i in {1..30}; do
	if ss -lnt | grep -q ":9000"; then
		ready=1
		break
	fi

	# pipeline may have crashed while waiting
	if ! kill -0 "$PIPELINE_PID" 2>/dev/null; then
		echo "Pipeline CRASHED while initializing. Exiting."
		cleanup
		exit 1
	fi

	sleep 1
done

if [[ $ready -ne 1 ]]; then
	echo "Pipeline FAILED to start within timeout."
	cleanup
	exit 1
fi

echo "Pipeline is Ready!"

echo "[3/3] Launching Dashboard..."
python3 ./dashboard.py || true

# After dashboard closes → cleanup
cleanup
exit 0
