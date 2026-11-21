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

cd "${NEXT_DIR}"
exec node --experimental-strip-types server/openmausbot.ts serve --port "${PORT}" --data-dir "${DATA_DIR}" "$@"

