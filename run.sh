#!/usr/bin/env bash
set -euo pipefail

VENV=".venv"
REQUIREMENTS="requirements.txt"
APP_MODULE="src.app:app"

if [[ ! -d "$VENV" ]]; then
  echo "Creating virtual environment in $VENV..."
  python3 -m venv "$VENV"
fi

source "$VENV/bin/activate"

pip install --upgrade pip
pip install -r "$REQUIREMENTS"

echo "Starting FastAPI app..."
exec "$VENV/bin/uvicorn" "$APP_MODULE" --reload
