#!/usr/bin/env bash
# Run the CDWC Talent Recommendation Engine locally.
# Usage: bash scripts/run_local.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Starting CDWC Talent Recommendation Engine on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
echo ""

python app/main.py
