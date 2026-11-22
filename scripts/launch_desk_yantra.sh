#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
NEXT_DIR="${ROOT_DIR}/next"

PORT="${DESK_YANTRA_PORT:-8799}"
DATA_DIR="${DESK_YANTRA_DATA_DIR:-${HOME}/.desk-yantra}"

SERVER_ARGS=()
while [ "$#" -gt 0 ]; do
  if [ "$1" = "--local-workspace" ]; then
    if [ "$#" -lt 2 ] || [ ! -d "$2" ]; then
      echo "--local-workspace requires an existing directory" >&2
      exit 2
    fi
    export DESK_YANTRA_LOCAL_WORKSPACE="$(realpath "$2")"
    shift 2
  else
    SERVER_ARGS+=("$1")
    shift
  fi
done

mkdir -p "${DATA_DIR}"

echo "Starting Desk Yantra on http://127.0.0.1:${PORT}..."
echo "Data directory: ${DATA_DIR}"
if [ -n "${DESK_YANTRA_LOCAL_WORKSPACE:-}" ]; then
  echo "Shared local workspace: ${DESK_YANTRA_LOCAL_WORKSPACE}"
fi

export OMB_DATA_DIR="${DATA_DIR}"
export OMB_PORT="${PORT}"
export OMB_CLI_PREFIX="desk-yantra"

cd "${NEXT_DIR}"

# If running with special flags (like --help or --version), execute directly
if [ "${#SERVER_ARGS[@]}" -gt 0 ] && [[ "${SERVER_ARGS[0]}" == "--help" || "${SERVER_ARGS[0]}" == "-h" || "${SERVER_ARGS[0]}" == "--version" || "${SERVER_ARGS[0]}" == "-v" ]]; then
  if [[ "${SERVER_ARGS[0]}" == "--help" || "${SERVER_ARGS[0]}" == "-h" ]]; then
    echo "Launcher option: --local-workspace DIR shares DIR with bots for scoped file and command tools."
  fi
  exec node --experimental-strip-types server/openmausbot.ts "${SERVER_ARGS[@]}"
fi

if (echo > /dev/tcp/127.0.0.1/"${PORT}") 2>/dev/null; then
  echo "Port ${PORT} is already in use. Stop the running Desk Yantra server before starting this launcher." >&2
  exit 2
fi

# Start server in background
node --experimental-strip-types server/openmausbot.ts serve --port "${PORT}" --data-dir "${DATA_DIR}" "${SERVER_ARGS[@]}" &
SERVER_PID=$!

trap 'kill -TERM "${SERVER_PID}" 2>/dev/null || true' INT TERM EXIT

# Wait up to 10s for server to start listening
READY=0
for i in $(seq 1 20); do
  if (echo > /dev/tcp/127.0.0.1/"${PORT}") 2>/dev/null; then
    READY=1
    break
  fi
  if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
    break
  fi
  sleep 0.5
done

if [ "${READY}" -ne 1 ]; then
  echo "Desk Yantra did not start on port ${PORT}." >&2
  wait "${SERVER_PID}" || true
  exit 1
fi

# Mint pairing link for local browser
echo ""
echo "================================================================="
echo "  ◈ Desk Yantra is ready!"
echo "================================================================="
node --experimental-strip-types server/openmausbot.ts pair --port "${PORT}" 2>/dev/null || true
echo "================================================================="
echo ""

wait "${SERVER_PID}"

