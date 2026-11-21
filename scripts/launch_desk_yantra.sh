#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
NEXT_DIR="${ROOT_DIR}/next"

PORT="${DESK_YANTRA_PORT:-8799}"
DATA_DIR="${DESK_YANTRA_DATA_DIR:-${HOME}/.desk-yantra}"

mkdir -p "${DATA_DIR}"

echo "Starting Desk Yantra on http://127.0.0.1:${PORT}..."
echo "Data directory: ${DATA_DIR}"

export OMB_DATA_DIR="${DATA_DIR}"
export OMB_PORT="${PORT}"
export OMB_CLI_PREFIX="desk-yantra"

cd "${NEXT_DIR}"

# If running with special flags (like --help or --version), execute directly
if [ "$#" -gt 0 ] && [[ "$1" == "--help" || "$1" == "-h" || "$1" == "--version" || "$1" == "-v" ]]; then
  exec node --experimental-strip-types server/openmausbot.ts "$@"
fi

# Start server in background
node --experimental-strip-types server/openmausbot.ts serve --port "${PORT}" --data-dir "${DATA_DIR}" "$@" &
SERVER_PID=$!

trap 'kill -TERM "${SERVER_PID}" 2>/dev/null || true' INT TERM EXIT

# Wait up to 10s for server to start listening
for i in $(seq 1 20); do
  if (echo > /dev/tcp/127.0.0.1/"${PORT}") 2>/dev/null; then
    break
  fi
  sleep 0.5
done

# Mint pairing link for local browser
echo ""
echo "================================================================="
echo "  ◈ Desk Yantra is ready!"
echo "================================================================="
node --experimental-strip-types server/openmausbot.ts pair --port "${PORT}" 2>/dev/null || true
echo "================================================================="
echo ""

wait "${SERVER_PID}"

