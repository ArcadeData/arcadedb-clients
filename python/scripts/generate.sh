#!/usr/bin/env bash
#
# Regenerates the HTTP client from the committed OpenAPI contract.
#
# --meta none emits the package body only (api/, models/, client.py, errors.py,
# types.py) with no project scaffolding of its own. The generated modules import
# each other RELATIVELY, which is what lets the tree nest inside an existing
# package without rewriting a single import.
#
# The contract is located by resolve-openapi-contract.sh rather than by a glob:
# two contracts/arcadedb-openapi-*.json would otherwise generate from whichever
# the glob yields first, which is lexical, not version, order.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$PYTHON_DIR/.." && pwd)"

SPEC="$("$REPO_ROOT/scripts/resolve-openapi-contract.sh")"
OUT="$PYTHON_DIR/packages/driver/src/arcadedb_driver/_generated"

cd "$PYTHON_DIR"
uv run openapi-python-client generate \
  --path "$SPEC" \
  --meta none \
  --overwrite \
  --output-path "$OUT"

# The generator leaves its own ruff cache inside the output directory, which the
# drift gate reads with `git status --porcelain`.
rm -rf "$OUT/.ruff_cache"
