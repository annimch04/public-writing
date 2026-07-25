#!/bin/sh
set -eu

REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$REPO_ROOT"

find_node() {
  if [ -n "${FIELDLIGHT_NODE:-}" ] && [ -x "$FIELDLIGHT_NODE" ]; then
    printf '%s\n' "$FIELDLIGHT_NODE"
    return
  fi

  if command -v node >/dev/null 2>&1; then
    command -v node
    return
  fi

  codex_node="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
  if [ -x "$codex_node" ]; then
    printf '%s\n' "$codex_node"
    return
  fi

  printf '%s\n' "Node.js was not found. Install Node 20+ or set FIELDLIGHT_NODE." >&2
  exit 1
}

find_python() {
  if [ -n "${FIELDLIGHT_PYTHON:-}" ] && [ -x "$FIELDLIGHT_PYTHON" ]; then
    printf '%s\n' "$FIELDLIGHT_PYTHON"
    return
  fi

  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi

  codex_python="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
  if [ -x "$codex_python" ]; then
    printf '%s\n' "$codex_python"
    return
  fi

  printf '%s\n' "Python 3 was not found. Install Python 3.11+ or set FIELDLIGHT_PYTHON." >&2
  exit 1
}

NODE_BIN=$(find_node)
COMMAND=${1:-scrape}
if [ "$#" -gt 0 ]; then
  shift
fi
if [ "$COMMAND" != "scrape" ]; then
  printf '%s\n' "Usage: ./tools/x_scrape.sh scrape [options]" >&2
  exit 2
fi

PYTHON_BIN=$(find_python)
exec "$PYTHON_BIN" tools/twitter_sync.py scrape --node "$NODE_BIN" "$@"
