#!/usr/bin/env bash
#
# Files what the daily contract watch found: one tracking issue, and - when a
# refresh can fix it - one pull request that does.
#
# Everything here is IDEMPOTENT against a single label and a single branch. The
# job runs every day; a script that created an issue per run would produce thirty
# a month, and a feed nobody reads is indistinguishable from no feed at all. So a
# second consecutive finding updates the existing issue instead of opening
# another, and only comments when the situation actually moved.
#
# Consumes, from the environment: STATE, VERSION, IMAGE, VERIFY, RUN_URL,
# TRACKING_LABEL, REFRESH_BRANCH, GH_TOKEN.
set -euo pipefail

: "${STATE:?}" "${VERSION:?}" "${IMAGE:?}" "${VERIFY:?}" "${RUN_URL:?}"
: "${TRACKING_LABEL:=contract-drift}" "${REFRESH_BRANCH:=chore/contract-refresh}"

REPO="${GITHUB_REPOSITORY:-ArcadeData/arcadedb-clients}"

verify_line() {
  if [[ "$VERIFY" == "success" ]]; then
    echo "The client builds and its full suite passes against \`$IMAGE\`."
  else
    echo "**The client's suite FAILS against \`$IMAGE\`.** See the run for which stage."
  fi
}

changed_files="$(git status --porcelain -- contracts typescript || true)"

build_body() {
  echo "<!-- contract-watch:$STATE -->"
  echo
  case "$STATE" in
    contract-changed)
      cat <<MD
The contract served by \`$IMAGE\` no longer matches the one committed here.

$(verify_line)

Files affected by the refresh:

\`\`\`
${changed_files:-(none)}
\`\`\`

A pull request from \`$REFRESH_BRANCH\` carries the refreshed contracts, the
regenerated output and the version adoption, so the change is reviewable as a
diff rather than as a description of one.

Reviewing it is the point of this issue: a contract change is a decision about
what the client promises, and the only moment that decision is cheap is now,
while it is one day old and attributable to a known set of commits.
MD
      ;;
    behaviour-regression)
      cat <<MD
The contract is **byte-identical** to the one committed here, and the client's
suite still fails against \`$IMAGE\`.

That combination is the interesting one. The server's behaviour moved under a
contract that did not, so nothing in this repository can fix it and there is no
refresh PR to open - the contract is already current. Either the server changed
behaviour without changing its contract, or the contract does not describe the
behaviour it should.

MD
      ;;
    *)
      echo "Unrecognised contract-watch state: \`$STATE\`."
      ;;
  esac
  echo
  echo "Snapshot version: \`$VERSION\` · [workflow run]($RUN_URL)"
  echo
  echo "_Maintained by \`.github/workflows/contract-watch.yml\`. This issue is updated in place;"
  echo "it closes when a run finds the contract current and the suite green._"
}

# The label is the identity of the tracking issue, so it has to exist before it
# can be searched for.
gh label create "$TRACKING_LABEL" \
  --repo "$REPO" \
  --color d93f0b \
  --description "Contract drift or behaviour regression found by the daily contract watch" \
  2>/dev/null || true

title="Contract watch: $STATE against $VERSION"
body="$(build_body)"

existing="$(gh issue list --repo "$REPO" --label "$TRACKING_LABEL" --state open \
  --limit 1 --json number --jq '.[0].number // empty')"

if [[ -z "$existing" ]]; then
  issue_url="$(gh issue create --repo "$REPO" --title "$title" --label "$TRACKING_LABEL" --body "$body")"
  issue="${issue_url##*/}"
  echo "Opened issue #$issue" >&2
else
  issue="$existing"
  previous="$(gh issue view "$issue" --repo "$REPO" --json body --jq .body)"
  if [[ "$previous" == "$body" ]]; then
    # Same finding as yesterday, unchanged in every detail. Updating the issue
    # would be a no-op and commenting would be noise.
    echo "Issue #$issue already describes this exact finding; leaving it alone." >&2
  else
    gh issue edit "$issue" --repo "$REPO" --title "$title" --body "$body"
    gh issue comment "$issue" --repo "$REPO" --body \
      "The finding changed as of [this run]($RUN_URL). The description above has been updated."
    echo "Updated issue #$issue" >&2
  fi
fi

if [[ "$STATE" != "contract-changed" ]]; then
  exit 0
fi

# The refresh PR. A fixed branch, force-pushed, so consecutive days update one
# pull request rather than stacking near-identical ones.
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

git checkout -b "$REFRESH_BRANCH"
git add contracts typescript
git commit -m "chore: refresh the contract to $VERSION

Opened by the daily contract watch. Regenerated from $IMAGE, with the previous
version retired by scripts/adopt-contract-version.sh.

Refs #$issue"
git push --force origin "$REFRESH_BRANCH"

open_pr="$(gh pr list --repo "$REPO" --head "$REFRESH_BRANCH" --state open \
  --limit 1 --json number --jq '.[0].number // empty')"

pr_body="$(cat <<MD
Refreshes the committed contract to \`$VERSION\`, regenerates both clients, and
retires the previous version's artifacts and references.

$(verify_line)

Closes #$issue

_Opened automatically by \`.github/workflows/contract-watch.yml\`, force-pushed
in place each day the contract moves._
MD
)"

if [[ -z "$open_pr" ]]; then
  gh pr create --repo "$REPO" --base main --head "$REFRESH_BRANCH" \
    --title "chore: refresh the contract to $VERSION" --body "$pr_body"
else
  gh pr edit "$open_pr" --repo "$REPO" \
    --title "chore: refresh the contract to $VERSION" --body "$pr_body"
  echo "Updated PR #$open_pr" >&2
fi
