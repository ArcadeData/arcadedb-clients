#!/usr/bin/env bash
#
# Prints the path of the single contracts/arcadedb-openapi-*.json, or fails.
#
# `generate:http` used to hand the glob straight to openapi-typescript:
#
#     openapi-typescript ../contracts/arcadedb-openapi-*.json -o .../schema.ts
#
# openapi-typescript takes ONE input. Given two matching files it does not warn,
# error, or mention the second - it generates from whichever the shell's glob
# yields first, which is lexical order, not version order. That is not a
# hypothetical: with 26.9.1-SNAPSHOT and 26.9.2-SNAPSHOT side by side it
# generates from 26.9.1, the STALE one. Typecheck, tests and the drift gate all
# stay green, because the committed output does match the contract it was
# generated from - just not the current one.
#
# Two contracts is exactly what a version bump produces, since fetch-contract.sh
# names each file after its version and writes the new one beside the old. The
# gRPC half of the pipeline is protected twice over (buf fails loudly on the
# duplicate symbol, and ci.yml counts contracts/*.proto); this is the OpenAPI
# half's missing guard.
#
# Prints the path on stdout so a caller can substitute it; every diagnostic goes
# to stderr.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTRACTS_DIR="${1:-$(cd "$SCRIPT_DIR/.." && pwd)/contracts}"

shopt -s nullglob
SPECS=("$CONTRACTS_DIR"/arcadedb-openapi-*.json)
shopt -u nullglob

if [[ "${#SPECS[@]}" -eq 0 ]]; then
  echo "ERROR: no $CONTRACTS_DIR/arcadedb-openapi-*.json found." >&2
  echo "Run scripts/fetch-contract.sh --release <tag> or --image <image> first." >&2
  exit 1
fi

if [[ "${#SPECS[@]}" -ne 1 ]]; then
  echo "ERROR: expected exactly one $CONTRACTS_DIR/arcadedb-openapi-*.json, found ${#SPECS[@]}:" >&2
  printf '  %s\n' "${SPECS[@]}" >&2
  echo "Generating from a glob would silently pick one by lexical order - for 26.9.1 beside" >&2
  echo "26.9.2 that is the OLDER file. Retire the superseded contract first:" >&2
  echo "  scripts/adopt-contract-version.sh <version>" >&2
  exit 1
fi

printf '%s\n' "${SPECS[0]}"
