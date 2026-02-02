---
title: "How We Make Claude Remember: Learnings Over Skills"
date: 2026-02-02
tags: ["ai", "agents", "claude-code", "skills", "productivity"]
summary: "Skills don't reliably auto-invoke. We built a three-layer system: searchable learnings files, a curation skill, and a post-commit hook that reminds you to document."
---

## Background

Claude Code reads a CLAUDE.md file at project root for context. "Skills" are reusable prompt templates Claude can invoke. But Claude itself resets between sessions - it doesn't remember what it learned yesterday.

## The Problem

We created 10+ skills to teach Claude project-specific knowledge. But skills don't reliably auto-invoke.

Concrete example: I had an `airshelf-vercel` skill with explicit instructions: "Don't run `vercel --prod` - push to git instead." I asked Claude to deploy. It ran `vercel --prod`. Repeatedly. The skill existed. Claude never loaded it.

**"Why not just use Skills?"** I've seen this feedback. We tried. Skills work great for workflows you explicitly invoke (`/commit`, `/review-pr`). But for factual knowledge Claude needs mid-task? Skills require Claude to remember which of 10 skills to invoke. It often doesn't. Learnings require one generic pattern: `grep -r "keyword" learnings/`.

## The Solution

A three-layer system:

**1. learnings/ folder** - Topic-specific files (database.md, stripe.md, vercel.md) for facts and gotchas. CLAUDE.md tells Claude these exist and how to search them. Not auto-loaded, but always discoverable.

**2. curate-docs skill** - A structured process for capturing knowledge after features. Why a skill and not a script? Because curation requires judgment - deciding what goes where:
- Critical gotchas → CLAUDE.md (1-liners, always loaded)
- Detailed knowledge → learnings/ (searchable on demand)
- Repeatable workflows → skills (explicitly invoked)

**3. Post-commit hook** - Claude Code supports hooks that run after specific tool calls. Ours fires after `git commit`, but only on feature branches with commits ahead of main:

```
"Feature branch 'feat/auth' has 3 commits. Consider running /curate-docs."
```

Targeted reminder, not noise. Without it, I forgot to document. With it, I don't.

## Does It Work?

**When it works:** I hit a Prisma migration error, searched `grep -r "Neon branch" learnings/`, found the exact workaround I'd documented weeks earlier.

**When it fails:** When Claude doesn't think to search. This still happens - roughly 1 in 5 times. Prompting helps ("check learnings/ for this error"). But it works far more often than skills Claude had to remember to invoke.

## Get It

The curate-docs skill and hook: [github.com/evoleinik/curate-docs](https://github.com/evoleinik/curate-docs)

```bash
npx skills add evoleinik/curate-docs
```

## Takeaway

Skills = workflows you invoke. Learnings = facts Claude searches. Don't rely on skills alone for persistent knowledge. Use searchable learnings files combined with a hook that reminds you to curate.
