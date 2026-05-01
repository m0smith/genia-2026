#!/usr/bin/env bash

set -euo pipefail

SLUG="${1:-}"

if [[ -z "$SLUG" ]]; then
  echo "Usage: genia-clean <change-slug>"
  exit 1
fi

HANDOFF_DIR=".genia/process/tmp/handoffs/$SLUG"

echo "== Genia Clean: $SLUG =="

# --- Check directory exists
if [[ ! -d "$HANDOFF_DIR" ]]; then
  echo "❌ Handoff directory not found:"
  echo "   $HANDOFF_DIR"
  exit 1
fi

# --- Check required files
DISTILL_FILE="$HANDOFF_DIR/08-distillation.md"
AUDIT_FILE="$HANDOFF_DIR/07-audit.md"

if [[ ! -f "$DISTILL_FILE" ]]; then
  echo "❌ Missing distillation file:"
  echo "   $DISTILL_FILE"
  echo "Run distillation before cleaning."
  exit 1
fi

echo "✔ Found distillation file"

# --- Check audit result (non-blocking warning)
if [[ -f "$AUDIT_FILE" ]]; then
  if grep -q "FAIL" "$AUDIT_FILE"; then
    echo "⚠️  Audit indicates FAIL"
    echo "   Review before deleting handoffs"
  else
    echo "✔ Audit does not indicate failure"
  fi
else
  echo "⚠️  No audit file found"
fi

# --- Confirm deletion
echo
read -p "Delete handoff directory $HANDOFF_DIR ? [y/N] " CONFIRM

if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
  echo "Aborted."
  exit 0
fi

# --- Delete
rm -rf "$HANDOFF_DIR"

echo "🧹 Handoff directory removed"
echo "Done."