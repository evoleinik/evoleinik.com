---
title: "Zero-Friction Database Branching with Neon, Git Hooks, and Claude Code"
date: 2026-01-07
tags: ["postgres", "neon", "devtools", "ai-development", "claude-code", "git"]
---

# Zero-Friction Database Branching with Neon, Git Hooks, and Claude Code

I've been refining my Neon database branching setup over the past few months. Here's the current state: fully automated branch lifecycle with zero manual cleanup.

## The Goal

When I `git checkout -b feat/x`:
1. Neon database branch created automatically
2. `.env.local` updated with the new connection string
3. Vercel preview deployment uses the same isolated database

When I merge and delete the branch:
1. Orphaned Neon branches cleaned up automatically
2. No manual intervention needed

## The Stack

- **Neon** - Serverless Postgres with instant copy-on-write branching
- **neonctl** - Neon's CLI (much cleaner than curl API calls)
- **Git hooks** - post-checkout and pre-push automation
- **Claude Code** - AI assistant that follows the "never work on main" rule

## Environment Mapping

```
Git Branch    │  Neon Branch    │  Vercel
──────────────┼─────────────────┼──────────────
main          │  production     │  Production
feat/*        │  feat/*         │  Preview
```

## The Setup

### 1. Install neonctl

```bash
npm install -g neonctl
```

Authentication uses the `NEON_API_KEY` environment variable - no browser login needed for headless servers.

### 2. Post-Checkout Hook (Branch Creation + Auto-Cleanup)

```bash
#!/bin/bash
# .githooks/post-checkout

[ "$3" == "0" ] && exit 0  # Skip file checkouts

BRANCH_NAME=$(git symbolic-ref --short HEAD 2>/dev/null) || exit 0

source .env.local 2>/dev/null || exit 0
[ -z "$NEON_PROJECT_ID" ] && exit 0
[ -z "$NEON_API_KEY" ] && exit 0
export NEON_API_KEY

update_env() {
  local uri="$1"
  local escaped_uri="${uri//&/\\&}"  # Escape & for sed
  sed -i "s|^DATABASE_URL=.*|DATABASE_URL=\"$escaped_uri\"|" .env.local
  sed -i "s|^DIRECT_DATABASE_URL=.*|DIRECT_DATABASE_URL=\"$escaped_uri\"|" .env.local
}

# Protected branches → production database
if [[ "$BRANCH_NAME" =~ ^(main|master)$ ]]; then
  PROD_URI=$(neonctl connection-string production --project-id "$NEON_PROJECT_ID")
  update_env "$PROD_URI"
  echo "neon: $BRANCH_NAME → production"

  # Auto-cleanup orphaned Neon branches
  NEON_BRANCHES=$(neonctl branches list --project-id "$NEON_PROJECT_ID" -o json | \
    jq -r '.[].name | select(. != "production")')

  for neon_branch in $NEON_BRANCHES; do
    if ! git branch -a | grep -qE "(^[* +] +|/)${neon_branch}$"; then
      neonctl branches delete "$neon_branch" --project-id "$NEON_PROJECT_ID" && \
        echo "neon: deleted orphan $neon_branch"
    fi
  done
  exit 0
fi

# Feature branch → get or create Neon branch
CONNECTION_URI=$(neonctl connection-string "$BRANCH_NAME" --project-id "$NEON_PROJECT_ID" 2>/dev/null)

if [ -n "$CONNECTION_URI" ]; then
  update_env "$CONNECTION_URI"
  echo "neon: $BRANCH_NAME → existing branch"
else
  neonctl branches create --project-id "$NEON_PROJECT_ID" --name "$BRANCH_NAME" --parent production
  CONNECTION_URI=$(neonctl connection-string "$BRANCH_NAME" --project-id "$NEON_PROJECT_ID")
  update_env "$CONNECTION_URI"
  echo "neon: created $BRANCH_NAME"
fi
```

The magic is in the cleanup section: when you checkout `main`, the hook scans for Neon branches that no longer have a matching git branch and deletes them.

### 3. Pre-Push Hook (Vercel Sync + Parallel Checks)

```bash
#!/bin/sh
# .githooks/pre-push

BRANCH=$(git symbolic-ref --short HEAD)

# Sync DATABASE_URL to Vercel preview (background)
(
  case "$BRANCH" in
    main|master) ;;
    *)
      DB_URL=$(grep '^DATABASE_URL=' .env.local | sed 's/^DATABASE_URL=//' | tr -d '"')
      if [ -n "$DB_URL" ]; then
        printf "%s" "$DB_URL" | vercel env add --force DATABASE_URL preview "$BRANCH"
        echo "vercel: synced DATABASE_URL for preview/$BRANCH"
      fi
      ;;
  esac
) &

# Run checks in parallel
npm test &
PID_TEST=$!
npm run lint &
PID_LINT=$!

wait $PID_TEST || exit 1
wait $PID_LINT || exit 1

echo "All checks passed!"
```

### 4. Status Command

See which git branches have corresponding Neon branches:

```bash
$ git neon-status

Branch                              Git   Neon
──────────────────────────────────────────────────
main                                 ✓    (production)
feat/new-api                         ✓    ✓
feat/old-branch                      ✓      ← no DB
orphan-neon-branch                        ✓  ← orphan
```

Add the alias:
```bash
git config --global alias.neon-status '!./scripts/neon-status.sh'
```

## The Workflow

```bash
# Start feature
git checkout -b feat/new-api
# "neon: created feat/new-api"

# Work freely - isolated database
npm run dev

# Push for review
git push -u origin feat/new-api
# "vercel: synced DATABASE_URL for preview/feat/new-api"
# Preview at feat-new-api.vercel.app uses YOUR database

# Merge PR, delete branch
git checkout main
git branch -d feat/new-api
# "neon: deleted orphan feat/new-api"  ← automatic!
```

No manual cleanup. The orphaned Neon branch is deleted next time you checkout main.

## Claude Code Integration

The key rule in my `CLAUDE.md`:

```markdown
RULES:
- NEVER work directly on main branch - always create a feature branch first
- Main is for merging and deploying only, not development
```

This ensures Claude always runs `git checkout -b feat/...` before making changes. Combined with Neon branching:
- AI experiments on isolated database
- Production is never touched
- Mistakes are contained to the feature branch

## Why This Matters

With AI assistants writing code, they often need to:
- Run migrations
- Seed test data
- Execute queries to verify changes

On a shared database, this is terrifying. With Neon branching + the "always branch" rule:
- Every feature gets an isolated database copy
- AI can freely experiment
- Production stays clean
- Cleanup is automatic

## Quick Reference

| Command | What Happens |
|---------|--------------|
| `git checkout -b feat/x` | Creates Neon branch, updates .env.local |
| `git push` | Syncs DB URL to Vercel preview |
| `git checkout main` | Switches to prod DB, cleans orphans |
| `git neon-status` | Shows branch mapping |
| `git nuke feat/x` | Deletes git + Neon branch (manual) |

## neonctl Cheatsheet

```bash
# List branches
neonctl branches list --project-id "$NEON_PROJECT_ID"

# Get connection string
neonctl connection-string "branch-name" --project-id "$NEON_PROJECT_ID"

# Create branch
neonctl branches create --name "branch-name" --parent production --project-id "$NEON_PROJECT_ID"

# Delete branch
neonctl branches delete "branch-name" --project-id "$NEON_PROJECT_ID"
```

---

The full setup is in my dotfiles. The combination of Neon's instant branching, git hooks for automation, and Claude's "always branch" rule gives me confidence to let AI assistants work on my codebase without fear of production accidents.
