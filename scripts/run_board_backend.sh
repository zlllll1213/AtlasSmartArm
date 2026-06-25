#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="python3"
PIP_INSTALL_ARGS=()

if [ -x ".venv/bin/python" ] && .venv/bin/python -m pip --version >/dev/null 2>&1; then
  PYTHON_BIN=".venv/bin/python"
elif python3 -m venv .venv >/dev/null 2>&1 && .venv/bin/python -m pip --version >/dev/null 2>&1; then
  PYTHON_BIN=".venv/bin/python"
else
  echo "python3-venv or venv pip is unavailable; using python3 with existing packages." >&2
  PIP_INSTALL_ARGS=(--user)
fi

if "${PYTHON_BIN}" -m pip --version >/dev/null 2>&1; then
  "${PYTHON_BIN}" -m pip install "${PIP_INSTALL_ARGS[@]}" -r requirements.txt
else
  echo "pip is unavailable for ${PYTHON_BIN}; skipping dependency install." >&2
fi

if ! "${PYTHON_BIN}" -c "import uvicorn" >/dev/null 2>&1; then
  echo "uvicorn is not available for ${PYTHON_BIN}; install requirements before starting." >&2
  exit 1
fi

export PROGRAM_MODE="${PROGRAM_MODE:-board}"
export ROBOT_ARM_ROOT="${ROBOT_ARM_ROOT:-/home/HwHiAiUser/E2ESamples/src/E2E-Sample/ros2_robot_arm}"

"${PYTHON_BIN}" -m uvicorn src.backend.main:app --host 0.0.0.0 --port "${APP_PORT:-8080}"
