#!/usr/bin/env bash
#
# Fetches the ArcadeDB OpenAPI contract and writes a jq -S normalised copy into
# contracts/. Every generated client, in every language this repository will
# ever host, derives from the file this script writes.
#
# Two modes:
#   --release <tag>   Downloads arcadedb-openapi-<tag>.json from the matching
#                      GitHub release and verifies it against the published
#                      .sha256 checksum.
#   --image <docker-tag>
#                      Starts the given arcadedata/arcadedb Docker image on an
#                      ephemeral host port, waits for /api/v1/ready, and fetches
#                      /api/v1/openapi.json using a root password the script
#                      sets on the container itself.
#
# In both modes, the resulting spec is refused unless it is structurally
# provably post-M0: the /api/v1/begin/{database} 204 response must carry the
# arcadedb-session-id header. A version string proves nothing about content;
# this marker cannot be true of any pre-M0 spec.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONTRACTS_DIR="$REPO_ROOT/contracts"
GITHUB_REPO="ArcadeData/arcadedb"

usage() {
  echo "Usage: $0 --release <tag>" >&2
  echo "       $0 --image <docker-tag>" >&2
  exit 1
}

MODE=""
TARGET=""

if [[ $# -ne 2 ]]; then
  usage
fi

case "$1" in
  --release)
    MODE="release"
    ;;
  --image)
    MODE="image"
    ;;
  *)
    usage
    ;;
esac
TARGET="$2"

mkdir -p "$CONTRACTS_DIR"

CLEANUP_TMP_DIR=""
CLEANUP_CONTAINER=""

cleanup() {
  if [[ -n "$CLEANUP_CONTAINER" ]]; then
    docker rm -f "$CLEANUP_CONTAINER" > /dev/null 2>&1 || true
  fi
  if [[ -n "$CLEANUP_TMP_DIR" ]]; then
    rm -rf "$CLEANUP_TMP_DIR"
  fi
}
trap cleanup EXIT

RAW_SPEC=""
VERSION_TAG=""

if [[ "$MODE" == "release" ]]; then
  VERSION_TAG="$TARGET"
  ASSET_NAME="arcadedb-openapi-${VERSION_TAG}.json"

  TMP_DIR="$(mktemp -d)"
  CLEANUP_TMP_DIR="$TMP_DIR"

  echo "Downloading ${ASSET_NAME} from release ${VERSION_TAG}..." >&2
  gh release download "$VERSION_TAG" \
    --repo "$GITHUB_REPO" \
    --pattern "$ASSET_NAME" \
    --pattern "${ASSET_NAME}.sha256" \
    --dir "$TMP_DIR"

  echo "Verifying checksum..." >&2
  (cd "$TMP_DIR" && shasum -a 256 -c "${ASSET_NAME}.sha256")

  RAW_SPEC="$TMP_DIR/$ASSET_NAME"

elif [[ "$MODE" == "image" ]]; then
  IMAGE="$TARGET"
  VERSION_TAG="${IMAGE##*:}"

  CONTAINER_NAME="arcadedb-contract-fetch-$$"
  ROOT_PASSWORD="contract-fetch-$$-$(date +%s)"
  CLEANUP_CONTAINER="$CONTAINER_NAME"

  echo "Starting ${IMAGE} as ${CONTAINER_NAME} on an ephemeral host port..." >&2
  # Bind to an ephemeral host port (never 2480: a developer machine may
  # already have ArcadeDB listening there).
  docker run -d \
    --name "$CONTAINER_NAME" \
    -p 127.0.0.1::2480 \
    -e JAVA_OPTS="-Darcadedb.server.rootPassword=${ROOT_PASSWORD}" \
    "$IMAGE" > /dev/null

  HOST_PORT="$(docker inspect \
    --format='{{(index (index .NetworkSettings.Ports "2480/tcp") 0).HostPort}}' \
    "$CONTAINER_NAME")"
  BASE_URL="http://127.0.0.1:${HOST_PORT}"

  echo "Waiting for ${IMAGE} to become ready on ${BASE_URL}..." >&2
  ATTEMPTS=0
  MAX_ATTEMPTS=90
  until [[ "$(curl -s -o /dev/null -w '%{http_code}' "${BASE_URL}/api/v1/ready" || true)" == "204" ]]; do
    ATTEMPTS=$((ATTEMPTS + 1))
    if [[ "$ATTEMPTS" -ge "$MAX_ATTEMPTS" ]]; then
      echo "ERROR: ${IMAGE} did not become ready within $((MAX_ATTEMPTS * 2))s" >&2
      docker logs "$CONTAINER_NAME" >&2 || true
      exit 1
    fi
    sleep 2
  done

  TMP_DIR="$(mktemp -d)"
  CLEANUP_TMP_DIR="$TMP_DIR"
  RAW_SPEC="$TMP_DIR/openapi.json"

  echo "Fetching /api/v1/openapi.json..." >&2
  # The spec endpoint requires authentication (GetOpenApiHandler.isRequireAuthentication()
  # returns true), so use the root password this script just set on the container.
  curl --fail -s -u "root:${ROOT_PASSWORD}" "${BASE_URL}/api/v1/openapi.json" -o "$RAW_SPEC"
fi

OUT="$CONTRACTS_DIR/arcadedb-openapi-${VERSION_TAG}.json"
jq -S . "$RAW_SPEC" > "$OUT"

# Refuse a contract we cannot confirm is post-M0. Structural check, not a
# version-string comparison: M0 both moved begin's success response to 204
# and attached the session header to it, so the presence of that header
# under the 204 key cannot be true of any pre-M0 spec.
if ! jq -e '.paths."/api/v1/begin/{database}".post.responses."204".headers."arcadedb-session-id"' \
     "$OUT" > /dev/null; then
  echo "REFUSING: this spec predates the M0 contract fixes." >&2
  echo "It lacks the arcadedb-session-id response header on beginTransaction, which means it also" >&2
  echo "declares 200 where the server sends 204 and leaves PromQL results untyped." >&2
  echo "A client generated from it cannot use transactions. Use a server at or after fa599b7516." >&2
  rm -f "$OUT"
  exit 1
fi

echo "Wrote $OUT" >&2
