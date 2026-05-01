#!/usr/bin/env bash

set -euo pipefail

ISSUE="${1:-}"
SLUG="${2:-}"
TYPE="${3:-feature}"

if [[ -z "$ISSUE" || -z "$SLUG" ]]; then
  echo "Usage: scripts/genia-new.sh <issue-number> <short-slug> [branch-type]"
  echo
  echo "Example:"
  echo "  scripts/genia-new.sh 207 flow-normalization feature"
  exit 1
fi

CHANGE_SLUG="issue-${ISSUE}-${SLUG}"
BRANCH="${TYPE}/${CHANGE_SLUG}"
HANDOFF_DIR=".genia/process/tmp/handoffs/${CHANGE_SLUG}"

echo "== Genia New Change =="
echo "Issue:        #${ISSUE}"
echo "Slug:         ${CHANGE_SLUG}"
echo "Branch:       ${BRANCH}"
echo "Handoff dir:  ${HANDOFF_DIR}"
echo

CURRENT_BRANCH="$(git branch --show-current)"

if [[ "$CURRENT_BRANCH" == "main" ]]; then
  echo "Creating branch from main: ${BRANCH}"
  git switch -c "$BRANCH"
else
  echo "Current branch is: ${CURRENT_BRANCH}"
  read -p "Create/switch to ${BRANCH} from here? [y/N] " CONFIRM
  if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "Aborted."
    exit 0
  fi
  git switch -c "$BRANCH"
fi

mkdir -p "$HANDOFF_DIR"

cat > "$HANDOFF_DIR/README.md" <<EOF
# Genia Handoff: ${CHANGE_SLUG}

Temporary LLM handoff directory.

These files are not canonical documentation and must not be committed.

Pipeline files:
- 00-preflight.md
- 01-contract.md
- 02-design.md
- 03-failing-tests.md
- 04-implementation.md
- 05-test-verification.md
- 06-doc-sync.md
- 07-audit.md
- 08-distillation.md
EOF

touch \
  "$HANDOFF_DIR/00-preflight.md" \
  "$HANDOFF_DIR/01-contract.md" \
  "$HANDOFF_DIR/02-design.md" \
  "$HANDOFF_DIR/03-failing-tests.md" \
  "$HANDOFF_DIR/04-implementation.md" \
  "$HANDOFF_DIR/05-test-verification.md" \
  "$HANDOFF_DIR/06-doc-sync.md" \
  "$HANDOFF_DIR/07-audit.md" \
  "$HANDOFF_DIR/08-distillation.md"

echo
echo "Created handoff files."
echo
echo "Next prompt:"
echo
cat <<EOF
Follow docs/process/preflight-prompt.md.

CHANGE NAME: issue #${ISSUE} ${SLUG}
CHANGE SLUG: ${CHANGE_SLUG}

Handoff directory:
${HANDOFF_DIR}/

Output pre-flight to:
${HANDOFF_DIR}/00-preflight.md
EOF