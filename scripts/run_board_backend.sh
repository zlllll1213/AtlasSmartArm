#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="python3"
PIP_INSTALL_ARGS=()

if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
elif python3 -m venv .venv >/dev/null 2>&1; then
  PYTHON_BIN=".venv/bin/python"
else
  echo "python3-venv is unavailable; falling back to python3 --user packages." >&2
  PIP_INSTALL_ARGS=(--user)
fi

"${PYTHON_BIN}" -m pip install "${PIP_INSTALL_ARGS[@]}" -r requirements.txt

export PROGRAM_MODE="${PROGRAM_MODE:-board}"
export ROBOT_ARM_ROOT="${ROBOT_ARM_ROOT:-/home/HwHiAiUser/E2ESamples/src/E2E-Sample/ros2_robot_arm}"

"${PYTHON_BIN}" -m uvicorn src.backend.main:app --host 0.0.0.0 --port "${APP_PORT:-8080}"
