---
title: "Agent Experience (AX): 10 Principles for CLI Tools AI Agents Can Actually Use"
date: 2026-02-27
tags: [cli, vercel, ai-agents, agent-experience, bun, developer-tools]
summary: "We have UX. We have DX. But AI agents are now the primary users of developer tools, and nobody's designing for them. Here are 10 principles from watching real agent behavior through usage telemetry."
---

We have UX. We have DX. But AI agents are now the primary users of developer tools, and nobody's designing for them.

I run a startup where Claude Code is the primary CI/CD operator — it deploys, checks logs, reads env vars, searches session history. The Vercel CLI was the first tool it had to use, and it was a disaster. `vercel logs` hangs for 5 minutes then times out. `vercel env pull` silently overwrites `.env.local`. `vercel link` rewires your project config without asking. No `--json` on most commands. Every feature designed to help humans was actively breaking the agent.

So I rebuilt it. And then I rebuilt a second tool. And the pattern became obvious: the features developers love most — interactive wizards, spinners, guided flows, colorful output — are the exact things that break agents.

I'm calling the discipline **Agent Experience (AX)** — ten principles I landed on after watching real agent behavior through usage telemetry.

## The ten principles

**1. Minimize output — every token costs context.** An agent's context window is its short-term memory. Every separator line, every padding character, every decoration pushes useful information out. I removed dash separator lines from table output after realizing they served zero purpose for agents and wasted tokens for humans too.

**2. Structured output by default.** `--json` on every command. JSON preserves the structure the code already has internally. Telemetry confirmed this: 38% of all agent calls use `--json`. They strongly prefer structured output when it's available.

**3. stdout for data, stderr for noise.** Results to stdout, diagnostics to stderr. Piping works, agents get clean data.

**4. No interactive prompts.** Agents can't type "Y" at a confirmation prompt. Every operation must be fully specified by arguments.

**5. Fail fast and loud.** Configurable `--timeout`. Clear error message. Non-zero exit code. The agent detects failure and tries something else.

**6. Never mutate implicitly.** Read-only by default. Silent side effects corrupt state in ways agents can't detect or recover from.

**7. Read existing state, don't create new state.** Reuse auth tokens and config files from existing tools. Zero setup if the user already has the original tool installed.

**8. Instant startup.** Agents call tools 40-60 times per session. Startup latency compounds. Compile to a binary. Sub-100ms or it's too slow.

**9. Guide on failure — empty results are the worst UX.** When a tool returns nothing, the agent has zero signal. Was the query wrong? The scope too narrow? I watched agents get empty results and blindly retry with progressively broader queries — three retries on average. I added one line to stderr: `no matches for "deploy" (19 files, 7 days, current project) — try: -d 30, -a, -s`. Retry chains dropped immediately. The agent now knows what was searched and what to try differently.

**10. Log usage for yourself — close the feedback loop.** Append one JSONL line per invocation — command, flags, result count, latency. Add a `--usage` command to aggregate it. Not for dashboards — for you, the tool author. Here's what the telemetry actually taught me:

- Agents write flags after the argument (`tool "pattern" -n 5`) because that's how grep works. My flag parser silently ignored those flags. Telemetry caught 4 instances in one session — I added argument reordering and the issue vanished.
- Agents retry the same command within 2 minutes after errors. Detecting these retry chains showed me which error messages weren't actionable enough.
- Every other principle on this list was discovered or validated by reading the usage log.

## The AX checklist

If you're building a CLI tool and want it to work with AI agents:

- Minimize output tokens (context window is finite)
- `--json` on every command
- stdout = data, stderr = logs
- No interactive prompts
- Deterministic exit codes
- `--timeout` on network operations
- Clear, parseable error messages
- Read-only by default
- Idempotent operations
- Fast startup (sub-100ms)
- Guide on empty results (print scope + suggestions to stderr)
- Log usage locally (you can't improve what you can't observe)

## AX is mostly Unix, rediscovered

When I stepped back and looked at these ten principles, I realized most of them aren't new. They're the Unix philosophy, written in 1978, applied to a user that didn't exist yet.

| AX Principle | Unix Origin |
|---|---|
| Minimize output | Rule of Silence — "say nothing unless you have something surprising to report" |
| stdout/stderr separation | Unix invented this |
| No interactive prompts | Pipe-friendly by design — tools that prompt break pipelines |
| Fail fast and loud | Rule of Repair — "fail noisily and as soon as possible" |
| Read existing state | Shared config: `/etc/`, env vars, dotfiles |
| Instant startup | Small, focused tools that do one thing |
| Never mutate implicitly | Principle of least surprise |

The Unix designers solved most of these problems 50 years ago. Then we forgot them. We added spinners, wizards, interactive flows, colored output — because we were designing for humans sitting at terminals.

Now the user is an AI agent, and we're back to needing exactly what Unix always wanted: small tools, text streams, clean interfaces, no surprises.

**What's different — same principles, different costs:**

- **JSON over plain text.** Not because agents need "richer structure" — agents parse text fine. The problem is **determinism**. `ls -la` output varies by OS, locale, terminal width, ANSI escape codes. JSON doesn't. Unix said "write programs to handle text streams" because text was universal. JSON is the new universal — for machine consumers, unambiguous beats human-readable.
- **Guide on failure.** Agents can read man pages. But loading a man page costs context window tokens. An inline hint is a man page compressed to one line — same information, 100x cheaper. It's the same tradeoff Unix made with terse error messages over verbose help, just with a different cost function.
- **Usage telemetry.** Genuinely new. Unix tools don't self-instrument. Watching how agents actually use your tool — what flags they pass, where they retry, what returns empty — is a feedback loop Unix never had.
- **Output has a cost — again.** Unix designers knew output had a cost: slow terminals, paper tape, 300 baud modems. That's why they wrote the Rule of Silence. We forgot because modern terminals are instant. Now output costs again — every token is real money when an LLM reads it. Same principle, different price tag.

The meta-insight: good AX is boring. Predictable, structured, silent, deterministic. Not a new idea — a very old idea, rediscovered because the cost of output became real again.
