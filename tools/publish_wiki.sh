#!/usr/bin/env bash
# Publish the generated Genia function reference to the GitHub Wiki.
#
# The mkdocs site (docs/reference/**) is the source of truth; this mirrors the
# same generated pages into the project wiki as flat pages. Run in CI after a
# push to main, or locally with push credentials.
#
#   tools/publish_wiki.sh                 # regenerate + push to the default wiki remote
#   WIKI_REMOTE=<url> tools/publish_wiki.sh
#
set -euo pipefail
cd "$(dirname "$0")/.."

# 1. Regenerate the wiki mirror from source @doc/@meta.
python tools/gen_function_docs.py >/dev/null

WIKI_SRC=".tmp/wiki"
WIKI_REMOTE="${WIKI_REMOTE:-https://github.com/m0smith/genia-2026.wiki.git}"

if [ ! -d "$WIKI_SRC" ] || [ -z "$(ls -A "$WIKI_SRC"/*.md 2>/dev/null)" ]; then
  echo "No generated wiki pages in $WIKI_SRC" >&2
  exit 1
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
git clone --depth 1 "$WIKI_REMOTE" "$WORK"

# Mirror generated pages (Function-Reference.md, _Sidebar.md, <function>.md).
# Hand-written wiki pages (e.g. Home.md) are left untouched.
cp "$WIKI_SRC"/*.md "$WORK"/

cd "$WORK"
git add -A
if git diff --cached --quiet; then
  echo "Wiki already up to date."
  exit 0
fi
git -c user.name="genia-docs-bot" -c user.email="docs@genia.local" \
    commit -m "docs: sync generated function reference"
git push
echo "Wiki updated: $(ls *.md | wc -l) pages."
