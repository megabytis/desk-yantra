#!/usr/bin/env bash
set -euo pipefail

PORT="${DESK_YANTRA_PORT:-8799}"
DATA_DIR="${DESK_YANTRA_DATA_DIR:-${HOME}/.desk-yantra}"
APP_DIR="/usr/lib/desk-yantra"

mkdir -p "${DATA_DIR}"

export OMB_DATA_DIR="${DATA_DIR}"
export OMB_PORT="${PORT}"
export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=4096}"

if [ -d "${APP_DIR}" ]; then
    cd "${APP_DIR}"
    exec node --experimental-strip-types server/openmausbot.ts "$@"
else
    # Fallback to local repo execution if not globally installed
    REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/next"
    cd "${REPO_DIR}"
    exec node --experimental-strip-types server/openmausbot.ts "$@"
fi

