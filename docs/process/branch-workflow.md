# Branch Workflow (Genia)

## Purpose

Ensure all work is isolated, traceable, and aligned with the Genia 5-prompt pipeline.

---

## Core Rule

> No work is ever done on `main`.

---

## Workflow Integration

Pipeline:

1. Pre-flight  
2. Branch (automatic)  
3. Spec  
4. Design
5. Test (TDD)  
6. Implementation  
7. Docs  
8. Audit  
9. Merge → main  

---

## Branch Naming

Format:

    <type>/<short-kebab-name>

Types:

- feature/
- fix/
- refactor/
- docs/
- exp/

Examples:

    feature/refinement-templates
    fix/parser-rest-pattern
    docs/value-template-overview

---

## Branch Creation Rules

- Branch must be created before Spec
- Branch must match Pre-flight CHANGE NAME
- One branch per change
- No mixed-purpose branches

---

## Automation Contract

Every prompt MUST:

1. Check current branch
2. If on `main` → create new branch
3. If not on `main` → verify correct branch
4. Fail if mismatch

---

## Shell Automation

```bash
CURRENT_BRANCH="$(git branch --show-current)"

CHANGE_TYPE="${CHANGE_TYPE:-feature}"
CHANGE_SLUG="${CHANGE_SLUG:-replace-me}"

TARGET_BRANCH="${CHANGE_TYPE}/${CHANGE_SLUG}"

if [ "$CURRENT_BRANCH" = "main" ]; then
  git checkout -b "$TARGET_BRANCH"
elif [ "$CURRENT_BRANCH" != "$TARGET_BRANCH" ]; then
  echo "❌ Branch mismatch"
  echo "Current: $CURRENT_BRANCH"
  echo "Expected: $TARGET_BRANCH"
  exit 1
fi

echo "✅ Branch: $(git branch --show-current)"

Merge Rules
Must pass Audit
Must not introduce drift
Must keep main releasable
Prefer small, focused PRs
Anti-Patterns (Forbidden)
committing directly to main
long-lived mega branches
mixing multiple features in one branch
renaming branch mid-change
Philosophy

Branching is not optional.

It enforces:

isolation
clarity
auditability
correctness

Without it, the pipeline breaks.


---

# 🔧 Update: Pre-flight Template

Add this block **at the top**:

```md
--------------------------------
0. BRANCH
--------------------------------

Branch required:
YES

Branch type:
[ ] feature
[ ] fix
[ ] refactor
[ ] docs
[ ] exp

Branch slug:
<short-kebab-name>

Expected branch:
<branch-type>/<branch-slug>

Rules:
- Must not work on main
- Branch must be created before spec