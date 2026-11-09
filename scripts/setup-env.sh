#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${AQUA3_VENV:-${ROOT_DIR}/.venv}"

find_python() {
  local candidate
  for candidate in "${AQUA3_PYTHON:-}" python3.11 python3 python; do
    if [[ -n "${candidate}" ]] && command -v "${candidate}" >/dev/null 2>&1; then
      if "${candidate}" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
        printf '%s\n' "${candidate}"
        return 0
      fi
    fi
  done
  return 1
}

PYTHON="$(find_python || true)"
if [[ -z "${PYTHON}" ]]; then
  echo "AQuA3 requires Python 3.10 or newer." >&2
  echo "Install Python 3.11, or set AQUA3_PYTHON to a compatible interpreter." >&2
  exit 1
fi

echo "Creating AQuA3 environment at ${VENV_DIR} using ${PYTHON}"
"${PYTHON}" -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/python" -m pip install -e "${ROOT_DIR}[dev]"
"${VENV_DIR}/bin/python" -m aqua3 --check

cat <<EOF

AQuA3 is ready.

Activate it with:
  source "${VENV_DIR}/bin/activate"

Then launch the GUI with:
  aqua3
EOF
