#!/usr/bin/env bash
set -euo pipefail

branch="$(git branch --show-current)"

if [[ "$branch" == "main" ]]; then
  echo "ERROR: Refusing to work on main." >&2
  exit 1
fi

if [[ ! "$branch" =~ ^issue-[0-9]+-.+ ]]; then
  echo "ERROR: Branch must look like issue-147-short-name" >&2
  echo "Current branch: $branch" >&2
  exit 1
fi

echo "OK branch: $branch"
