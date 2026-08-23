#!/usr/bin/env bash
#
# Tests for scripts/resolve-openapi-contract.sh and scripts/adopt-contract-version.sh.
#
# Both scripts exist because of failures that were INVISIBLE while they happened:
# generating a client from a stale contract, and a half-applied version bump that
# leaves the build green while every import points at a retired descriptor. So the
# tests assert the specific silent outcome, not merely that the scripts run.
#
# Each check is bounds-checked before it is asserted. An unguarded index or a
# missing file under `set -e` aborts the harness, which prints no FAIL line and
# silently skips every later check - a green-looking run that tested nothing.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

PASS=0
FAIL=0

ok()   { echo "  PASS: $1"; PASS=$((PASS + 1)); }
bad()  { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }
check() { if [[ "$1" == "$2" ]]; then ok "$3"; else bad "$3 (expected '$2', got '$1')"; fi; }

# A throwaway repository laid out like the real one, so the scripts resolve their
# own REPO_ROOT naturally and no test-only hook is needed in production code.
make_fixture() {
  local version="$1"
  local root
  root="$(mktemp -d)"
  mkdir -p "$root/scripts" "$root/contracts" \
           "$root/typescript/packages/client-grpc/src/gen" \
           "$root/typescript/packages/client-grpc/test" \
           "$root/typescript/packages/client"
  cp "$SCRIPTS_DIR/resolve-openapi-contract.sh" "$SCRIPTS_DIR/adopt-contract-version.sh" "$root/scripts/"
  echo '{}' > "$root/contracts/arcadedb-openapi-${version}.json"
  echo 'syntax = "proto3";' > "$root/contracts/arcadedb-server-${version}.proto"
  echo '// generated' > "$root/typescript/packages/client-grpc/src/gen/arcadedb-server-${version}_pb.ts"
  cat > "$root/typescript/packages/client-grpc/src/index.ts" <<TS
import { ArcadeDbService } from "./gen/arcadedb-server-${version}_pb.js";
export * from "./gen/arcadedb-server-${version}_pb.js";
TS
  cat > "$root/typescript/packages/client-grpc/test/stream.test.ts" <<TS
import { GrpcRecordSchema } from "../src/gen/arcadedb-server-${version}_pb.js";
// The contract this client is generated from is ${version}, in prose.
TS
  cat > "$root/typescript/packages/client-grpc/README.md" <<MD
This package was generated from \`contracts/arcadedb-server-${version}.proto\`.

Generate your own against \`contracts/arcadedb-server-<version>.proto\` if you prefer.

    "serverVersion": "${version}"

| Package | Server contract |
| --- | --- |
| 0.1.0 | ${version} |
MD
  printf '{\n  "name": "@arcadedb/client-grpc",\n  "arcadedb": {\n    "serverVersion": "%s"\n  }\n}\n' "$version" \
    > "$root/typescript/packages/client-grpc/package.json"
  printf '{\n  "name": "@arcadedb/client",\n  "arcadedb": {\n    "serverVersion": "%s"\n  }\n}\n' "$version" \
    > "$root/typescript/packages/client/package.json"
  echo "$root"
}

echo "resolve-openapi-contract.sh"

FIX="$(make_fixture 26.9.1-SNAPSHOT)"
out="$("$FIX/scripts/resolve-openapi-contract.sh" "$FIX/contracts" 2>/dev/null)"; rc=$?
check "$rc" "0" "exits 0 with exactly one contract"
check "$(basename "${out:-<none>}")" "arcadedb-openapi-26.9.1-SNAPSHOT.json" "prints the single contract path"

# The defect this script exists for: openapi-typescript takes the FIRST glob
# match, and 26.9.1 sorts before 26.9.2, so a bump would silently generate from
# the OLD contract. Refusing is the whole point.
echo '{}' > "$FIX/contracts/arcadedb-openapi-26.9.2-SNAPSHOT.json"
out="$("$FIX/scripts/resolve-openapi-contract.sh" "$FIX/contracts" 2>&1)"; rc=$?
check "$rc" "1" "refuses two contracts instead of silently picking the older one"
case "$out" in *"expected exactly one"*) ok "explains what it found" ;; *) bad "explains what it found (got: $out)" ;; esac
rm -f "$FIX/contracts/arcadedb-openapi-26.9.2-SNAPSHOT.json"

rm -f "$FIX/contracts/arcadedb-openapi-26.9.1-SNAPSHOT.json"
"$FIX/scripts/resolve-openapi-contract.sh" "$FIX/contracts" >/dev/null 2>&1; rc=$?
check "$rc" "1" "refuses when no contract is present"
rm -rf "$FIX"

echo "adopt-contract-version.sh"

FIX="$(make_fixture 26.9.1-SNAPSHOT)"
# A bump: both new contracts land beside the old ones, as fetch-contract.sh leaves them.
echo '{}' > "$FIX/contracts/arcadedb-openapi-26.10.1-SNAPSHOT.json"
echo 'syntax = "proto3";' > "$FIX/contracts/arcadedb-server-26.10.1-SNAPSHOT.proto"
"$FIX/scripts/adopt-contract-version.sh" 26.10.1-SNAPSHOT >/dev/null 2>&1; rc=$?
check "$rc" "0" "adopts a new version"

check "$(find "$FIX/contracts" -maxdepth 1 -name 'arcadedb-openapi-*.json' | wc -l | tr -d '[:space:]')" "1" "retires the superseded OpenAPI contract"
check "$(find "$FIX/contracts" -maxdepth 1 -name 'arcadedb-server-*.proto' | wc -l | tr -d '[:space:]')" "1" "retires the superseded proto"
check "$(find "$FIX/typescript/packages/client-grpc/src/gen" -maxdepth 1 -name '*_pb.ts' | wc -l | tr -d '[:space:]')" "0" "retires the orphaned generated module"

src="$FIX/typescript/packages/client-grpc/src/index.ts"
if [[ -f "$src" ]] && ! grep -q "26.9.1-SNAPSHOT" "$src" && grep -q "arcadedb-server-26.10.1-SNAPSHOT_pb.js" "$src"; then
  ok "repoints src imports at the new generated module"
else
  bad "repoints src imports at the new generated module"
fi

tst="$FIX/typescript/packages/client-grpc/test/stream.test.ts"
if [[ -f "$tst" ]] && grep -q "arcadedb-server-26.10.1-SNAPSHOT_pb.js" "$tst"; then
  ok "repoints test imports too (tests import the generated module as well)"
else
  bad "repoints test imports too"
fi

for pkg in client client-grpc; do
  f="$FIX/typescript/packages/$pkg/package.json"
  got="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['arcadedb']['serverVersion'])" "$f" 2>/dev/null)"
  check "${got:-<unreadable>}" "26.10.1-SNAPSHOT" "records the new serverVersion in $pkg/package.json"
done

readme="$FIX/typescript/packages/client-grpc/README.md"
# shellcheck disable=SC2016  # the backticks are literal markdown, not a subshell
if [[ -f "$readme" ]] && grep -q 'generated from `contracts/arcadedb-server-26.10.1-SNAPSHOT.proto`' "$readme"; then
  ok "updates the README's 'generated from' line"
else
  bad "updates the README's 'generated from' line"
fi

# A bare mention of the outgoing version in a comment or a sentence must be
# repointed too. Filename patterns alone miss these, so before this was handled a
# bump left every such line stale - stating a contract version the client no
# longer used, in the one place a reader would trust.
if [[ -f "$tst" ]] && grep -q "generated from is 26.10.1-SNAPSHOT, in prose" "$tst"; then
  ok "repoints a bare version mentioned in prose"
else
  bad "repoints a bare version mentioned in prose"
fi

# A generic placeholder is instructions, not a value. Rewriting
# `arcadedb-server-<version>.proto` into a concrete version turns a general
# instruction into a claim about one release - a documentation regression that
# looks like an update. This happened on a real run before the patterns required
# the version segment to start with a digit.
if [[ -f "$readme" ]] && grep -q 'arcadedb-server-<version>.proto' "$readme"; then
  ok "leaves a generic <version> placeholder alone"
else
  bad "leaves a generic <version> placeholder alone"
fi

# The compatibility table is a historical record: 0.1.0 really was generated from
# 26.9.1-SNAPSHOT. Rewriting that row would replace a fact with a falsehood, and
# the literal repointing above is broad enough to do exactly that if unguarded.
if [[ -f "$readme" ]] && grep -qE '^\| 0\.1\.0 \| 26\.9\.1-SNAPSHOT \|' "$readme"; then
  ok "leaves the historical compatibility table row untouched"
else
  bad "leaves the historical compatibility table row untouched"
fi

# Idempotence: re-adopting the version already in force must be a clean no-op.
before="$(find "$FIX" -type f -exec shasum {} + | sort | shasum)"
"$FIX/scripts/adopt-contract-version.sh" 26.10.1-SNAPSHOT >/dev/null 2>&1; rc=$?
after="$(find "$FIX" -type f -exec shasum {} + | sort | shasum)"
check "$rc" "0" "re-adopting the current version exits 0"
check "$after" "$before" "re-adopting the current version changes nothing"

"$FIX/scripts/adopt-contract-version.sh" 99.9.9-NOPE >/dev/null 2>&1; rc=$?
check "$rc" "1" "refuses a version whose contracts were never fetched"
rm -rf "$FIX"

echo
echo "passed: $PASS   failed: $FAIL"
[[ "$FAIL" -eq 0 ]]
