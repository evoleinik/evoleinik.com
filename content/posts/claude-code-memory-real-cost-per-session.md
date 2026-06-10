---
title: "The Real Cost of a Claude Code Session Is the Language Server, Not Claude"
date: 2026-06-10
tags: [observability, memory, llm-agents, linux, typescript]
summary: "Summing RSS says 26 Claude Code sessions eat 50GB. Measuring PSS/USS says 32.5GB — and the entire swing is the TypeScript language server, not Claude."
---

`top` said my dev box was at 45GB used. Summing RSS across the roughly 1000 `node`/`bun` processes from ~26 concurrent Claude Code sessions said 49.8GB. Both numbers are wrong about what's actually costing me memory. The real figure is 32.5GB, the `claude` process itself is a rounding error, and the entire difference between a cheap session and an expensive one is the TypeScript language server.

Here's the investigation, with every number measured from `/proc`.

## RSS is lying to you (by 53%)

The setup: a Linux box, 62GB RAM, ~26 Claude Code sessions open against one large TypeScript monorepo. Naive accounting:

| Metric | Total | What it counts |
|--------|-------|----------------|
| Σ RSS (all node/bun) | 49.8 GB | Every page each process maps, **including shared pages counted once per process** |
| Σ PSS (true) | 32.5 GB | Each process's *proportional* share of shared pages + its private pages |

That 17.3GB gap — a 53% overcount — is the shared V8/Node binary and shared libraries. With ~1000 Node processes alive, every one of them maps the same interpreter and the same `.so` files. RSS counts that binary ~1000 times. It's mapped once in physical RAM.

Three numbers matter when you measure process memory on Linux:

- **RSS** — Resident Set Size. Every resident page the process maps. Shared pages are counted in full for *every* sharer. Sums to nonsense.
- **PSS** — Proportional Set Size. A shared page mapped by *N* processes contributes `1/N` of its size to each. Sum of PSS across all processes equals actual physical RAM used. This is the honest total.
- **USS** — Unique Set Size = `Private_Clean + Private_Dirty`. Strictly private, unshareable pages. This is what you reclaim if you kill the process *and nothing else was sharing its pages*.

All three are readable per-process from `/proc/PID/smaps_rollup`.

## I assumed closing sessions wouldn't help. I was wrong.

My first instinct: most of this is the shared Node binary, so closing a few idle sessions buys me nothing — the pages stay mapped by the others. Reasonable theory. It's also false, and measuring USS is what proved it.

Per session, PSS ≈ USS — equal to one decimal place. That seems to contradict Finding 1 (17GB of shared pages!) until you do the division. The shared binary and libs are split across ~1000 processes, so any single process's *proportional* share of shared memory is negligible. What's left, and what dominates each process's PSS, is its **private heap**.

Practical consequence: closing a session reclaims essentially its full footprint. The shared-pages story is real in aggregate and irrelevant per session. If you remember one thing about reading `smaps`: shared memory matters for the *grand total*, private memory matters for *what you can free*.

## Where the memory actually goes

Two sessions, same MCP config, measured by PSS.

**Light session** (chatting, not editing code) — ~0.9GB, fully reclaimable:

| Component | PSS | Procs |
|-----------|-----|-------|
| chrome-devtools-mcp | 289 MB | 4 |
| claude (main) | 193 MB | 1 |
| playwright-mcp | 121 MB | 4 |
| context7 | 77 MB | 3 |
| in-house MCP servers | ~190 MB | several |

**Heavy session** (editing the monorepo) — ~4.8GB:

| Component | PSS | Procs |
|-----------|-----|-------|
| TypeScript `tsserver` (LSP) | 3,919 MB | 2 |
| the same MCP fleet as above | ~700–900 MB | many |

The MCP fleet is identical in both. The `claude` process barely moves. The only thing that changed is one component went from absent to nearly 4GB: the language server.

## Four things this proves

**(a) `claude` itself is cheap.** ~190MB. The "Claude Code uses 50GB" headline is an RSS artifact — the shared Node binary counted ~1000 times. The agent's own cost is trivial. The cost is in what it *spawns*.

**(b) There's a fixed ~700MB "MCP tax" per session.** Identical whether you're coding or just chatting, because Claude Code spawns your *entire* configured MCP fleet fresh for every session over stdio. No sharing between sessions, no lazy start. Twenty-six sessions = twenty-six full copies of your MCP fleet.

**(c) chrome-devtools-mcp costs more than `claude` does.** 289MB across 4 helper processes — the single priciest MCP, beating the agent process itself. Most people have it in their global config and have no idea it's the most expensive thing they spawn per session.

**(d) The TypeScript language server is the entire swing.** 0 or ~3.9GB, depending purely on whether the session opened TS files. One `tsserver` per session/worktree, never shared. The math is brutal:

```
4 heavy sessions:   4 × ~4.1GB  = 16.3 GB
22 light sessions: 22 × ~0.67GB = 14.7 GB
```

Four coding sessions outweigh all twenty-two idle ones combined. Your language server, multiplied by your session count, *is* the memory story.

## Aggregate by role

Summing PSS by component across all 26 sessions:

| Role | PSS | Procs |
|------|-----|-------|
| tsserver (LSP) | 13.1 GB | 8 |
| Claude Code main | 5.3 GB | 26 |
| chrome-devtools-mcp | 4.9 GB | 80 |
| playwright-mcp | 2.2 GB | 84 |
| context7 | 1.3 GB | 60 |
| in-house MCP (combined) | ~2.9 GB | many |
| bun-based MCP | 1.0 GB | many |

That's ~32.5GB of process PSS. Add ~8GB of tmpfs/shm plus kernel overhead and you reconcile cleanly with the 45GB `free` reported. The 49.8GB RSS sum never reconciled with anything, because it was never real.

Note `tsserver` runs only 8 processes (4 sessions × 2 — the full server plus a `partialSemantic` instance) yet tops the table at 13.1GB. chrome-devtools-mcp runs 80 processes for 4.9GB. Process count is not cost.

## Reproduce it yourself

The whole investigation is just reading `smaps_rollup` per PID and bucketing by what the process is. `smaps_rollup` gives you pre-summed `Pss`, `Private_Clean`, `Private_Dirty`, and `Swap` in one cheap read — no need to parse the full `smaps`.

```python
import os, glob

def category(pid):
    try:
        cmd = open(f"/proc/{pid}/cmdline").read().replace("\0", " ")
    except OSError:
        return None
    if "tsserver" in cmd:                 return "tsserver"
    if "chrome-devtools-mcp" in cmd:      return "chrome-devtools-mcp"
    if "playwright" in cmd:               return "playwright-mcp"
    if "context7" in cmd:                 return "context7"
    if "claude" in cmd:                   return "claude-main"
    if "node" in cmd or "bun" in cmd:     return "other-mcp"
    return None

def field(rollup, key):
    for line in rollup.splitlines():
        if line.startswith(key + ":"):
            return int(line.split()[1])  # kB
    return 0

totals = {}
for p in glob.glob("/proc/[0-9]*/smaps_rollup"):
    pid = p.split("/")[2]
    cat = category(pid)
    if not cat:
        continue
    try:
        r = open(p).read()
    except OSError:
        continue
    pss = field(r, "Pss")
    uss = field(r, "Private_Clean") + field(r, "Private_Dirty")
    t = totals.setdefault(cat, [0, 0, 0])
    t[0] += pss; t[1] += uss; t[2] += 1

for cat, (pss, uss, n) in sorted(totals.items(), key=lambda x: -x[1][0]):
    print(f"{cat:24} PSS {pss/1e6:6.2f}GB  USS {uss/1e6:6.2f}GB  ({n} procs)")
```

Run it as root (or with `CAP_SYS_PTRACE`) so you can read other users' `smaps_rollup`. The PSS column is your honest total; compare it against PSS ≈ USS to confirm per-process memory is private. If you don't want to write code, `smem` does the same off the shelf and reports PSS/USS directly (`smem -t -k -c "name pss uss"`).

## The takeaway

If you run many agent sessions, you have exactly two memory levers, and neither of them is "use a lighter model" or "close the Claude window":

1. **Sessions touching the monorepo.** Each one that opens TS files spins up a fresh ~3–4GB language server, never shared across sessions or worktrees. This is your dominant, swingiest cost. Fewer concurrent *coding* sessions — or sharing a worktree — is the biggest win available.

2. **MCP fleet size.** Every session pays the full tax: spawn cost × session count, whether you use those tools or not. Trim your *global* MCP config to what you actually reach for. Dropping chrome-devtools-mcp alone saved ~290MB per session — ~7.5GB across 26 sessions. Move situational servers to per-project config so idle sessions don't pay for them.

The agent is cheap. The compiler tooling it wakes up is not. Measure PSS, not RSS — your `top` output has been blaming the wrong process this whole time.
