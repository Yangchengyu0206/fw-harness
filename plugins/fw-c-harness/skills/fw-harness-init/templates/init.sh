#!/bin/sh
# Thin wrapper around harness/scripts/init_check.py. It verifies the environment and installs nothing.
cd "$(dirname "$0")" || exit 1
. ./.githooks/_python.sh
PY=$(harness_python) || { echo "init: Python 3.9+ not found. Fix: install Python 3 (on Windows, the py launcher)" >&2; exit 1; }
exec $PY harness/scripts/init_check.py "$@"
