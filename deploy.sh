#!/usr/bin/env bash

set -euo pipefail

REMOTE_HOST="${1:-root@65.49.233.137}"
REMOTE_PATH="${2:-/opt/binance-copy-trading}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_NAME="${VENV_NAME:-venv}"

echo "Deploying Binance Copy Trading to ${REMOTE_HOST}:${REMOTE_PATH}"

if ! command -v rsync >/dev/null 2>&1; then
  echo "Error: rsync is required on the local machine." >&2
  exit 1
fi

ssh "${REMOTE_HOST}" "mkdir -p '${REMOTE_PATH}'"

RSYNC_EXCLUDES=(
  "--exclude=.git/"
  "--exclude=__pycache__/"
  "--exclude=.pytest_cache/"
  "--exclude=.mypy_cache/"
  "--exclude=${VENV_NAME}/"
  "--exclude=.venv/"
  "--exclude=logs/"
  "--exclude=web/frontend/node_modules/"
)

echo "Syncing project files..."
rsync -az --delete "${RSYNC_EXCLUDES[@]}" ./ "${REMOTE_HOST}:${REMOTE_PATH}/"

echo "Preparing remote environment..."
ssh "${REMOTE_HOST}" bash <<EOF
set -euo pipefail

APP_DIR="${REMOTE_PATH}"
VENV_DIR="\${APP_DIR}/${VENV_NAME}"

if ! command -v ${PYTHON_BIN} >/dev/null 2>&1; then
  echo "Error: ${PYTHON_BIN} is not available on the remote host." >&2
  exit 1
fi

cd "\${APP_DIR}"
${PYTHON_BIN} -m venv "\${VENV_DIR}"
source "\${VENV_DIR}/bin/activate"
pip install --upgrade pip setuptools wheel

pip install -r requirements.txt
if [ -f requirements-web.txt ]; then
  pip install -r requirements-web.txt
fi

alembic upgrade head

if [ ! -f config.yaml ]; then
  if [ -f config.example.yaml ]; then
    cp config.example.yaml config.yaml
    echo "INFO: Created config.yaml from config.example.yaml"
  else
    cat > config.yaml <<'CFG'
base_url: "https://testnet.binancefuture.com"
master:
  api_key: ""
  api_secret: ""
followers: []
trading:
  leverage: 10
  margin_type: "CROSSED"
  position_mode: "one_way"
CFG
    echo "INFO: Generated placeholder config.yaml"
  fi
fi

mkdir -p logs
touch logs/api.log

deactivate
EOF

echo "Deployment complete."
echo ""
echo "Next steps:"
echo "1. ssh ${REMOTE_HOST}"
echo "2. cd ${REMOTE_PATH}"
echo "3. Edit config.futures.yaml with your API keys"
echo "4. Start the web server:"
echo "   source ${VENV_NAME}/bin/activate"
echo "   python web_server.py"
echo ""
echo "Or use Docker:"
echo "   docker-compose up -d"
echo ""
echo "Access the dashboard at: http://${REMOTE_HOST}:8000"
