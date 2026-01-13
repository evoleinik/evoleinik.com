---
title: "The Best Agent Architecture Is Already in Your Terminal"
date: 2026-01-12
slug: filesystem-agent-context
tags:
  - ai
  - agents
  - claude
  - developer-tools
  - architecture
---

# The Best Agent Architecture Is Already in Your Terminal

My project's CLAUDE.md file had grown to 55KB—242 learnings crammed into one massive file.

The problem? Claude prepends this file to every single prompt. A 55KB context file means less room for thinking and acting. Sessions hit context limits faster. Compaction happens sooner.

I noticed the degradation: sessions became noticeably shorter, context compaction triggered more frequently, and the agent seemed to lose track of longer conversations.

Here's the kicker: Claude Code's system prompt actually tells Claude not to take CLAUDE.md too seriously if it's too large. The system is designed to deprioritize oversized context files. So not only was I wasting context space—the agent was being instructed to partially ignore my carefully curated learnings anyway.

The fix took about an hour: split into a `learnings/` folder with one file per tool. Simple navigation:

```bash
ls learnings/                        # List available files
grep -r "webhook" learnings/         # Search all learnings
cat learnings/stripe.md              # Read specific tool
```

Then Vercel published an article that validated exactly this approach: [How to build agents with filesystems and bash](https://vercel.com/blog/how-to-build-agents-with-filesystems-and-bash).

## The Key Insight

LLMs have been trained on massive amounts of code. They've spent countless hours navigating directories, grepping through files, and managing state across complex codebases.

**If agents excel at filesystem operations for code, they'll excel at filesystem operations for anything.**

Vercel's sales call summarization agent went from ~$1.00 to ~$0.25 per call by replacing custom tooling with filesystem + bash. Quality improved too.

## Why This Works for Project Context

The typical approach is stuffing everything into the prompt. But every byte in your CLAUDE.md is a byte the model can't use for reasoning.

Filesystems offer:
- **On-demand loading.** Agent reads only what it needs, when it needs it.
- **Precise retrieval.** `grep -r "webhook" learnings/` returns exact matches.
- **Structure that matches your domain.** Learnings have natural hierarchies by tool.

## My New Structure

```
learnings/
  README.md           # Index + navigation guide
  stripe.md           # Webhooks, CLI, subscriptions
  vercel.md           # Deploys, env vars, cron
  prisma.md           # CRITICAL column drops, migrations
  clerk.md            # Auth, users, organizations
  axiom.md            # Logging, monitors, alerts
  nextjs.md           # Routing, caching, layouts
  playwright.md       # E2E testing, selectors
  ai-providers.md     # OpenAI, Gemini quirks
  database.md         # PostgreSQL, psql patterns
  git.md              # Hooks, GitHub Actions
  neon-setup.md       # Database branching setup
  misc.md             # Everything else
```

CLAUDE.md: 55KB → 24KB. All 251 learnings preserved and searchable. More headroom for actual work.

## The Pattern

1. **Keep always-loaded context minimal.** Only critical gotchas in CLAUDE.md.
2. **Structure knowledge as files.** One file per domain/tool.
3. **Let the agent navigate.** `ls`, `grep`, `cat` are native skills.

The agent treats your knowledge base like a codebase—searching for patterns, reading sections, building context just like debugging code.

As Vercel puts it: "The future of agents might be surprisingly simple. Maybe the best architecture is almost no architecture at all. Just filesystems and bash."
