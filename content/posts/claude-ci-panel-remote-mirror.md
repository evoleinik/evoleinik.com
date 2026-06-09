---
title: "The Path Has To Exist: Fixing Claude Code's CI Panel for Remote Dev (Without Melting a CPU)"
date: 2026-06-09
tags: [claude-code, macos, fuse-t, sshfs, git-worktree, remote-development, devtools, open-source]
summary: "Claude Code's desktop CI panel shells out to local gh in the session's working directory — a remote path that doesn't exist on my Mac. I fixed the premise by making the path exist: first with a FUSE-T mount that pinned a CPU at 100%, then with a git-worktree mirror that doesn't. Plus the open-source tool that does it for you."
---

My code lives on a Linux box. I drive it from a Mac with Claude Code in the desktop app, pointed at the box over SSH — so each session's working directory is a remote path. Everything works except the desktop app's CI/PR panel, which shows "CI checks unavailable" for every pull request.

The reason is dumber than it looks. The panel doesn't subscribe to GitHub webhooks. It shells out to your local `gh`, in the **session's working directory**, on the Mac. For a remote session that directory is a Linux path — `/home/eo/src/app/...` — that doesn't exist on the Mac. `gh` runs somewhere with no repo, and the panel goes dark. (You can confirm this by reading the app bundle: the panel computes `available = repoSlugs > 0 && (githubAuth || ghCliAvailable)`, and `repoSlugs` comes from the git remote of the **local** folder at the session's path.)

So I stopped trying to fix the app and fixed the premise: **make that exact path exist on the Mac, with a real `.git`.** Then local `gh` resolves the repo and the panel lights up — no patching, survives every update.

I shipped that with a FUSE-T sshfs mount. I even wrote it up here. It was wrong.

## The mount that pinned a CPU at 100%

FUSE-T is the clean way to get a remote path onto a modern Mac — kext-less, it runs a local NFS server instead of a kernel extension. I mounted `box:/home/eo/src` read-only at the same path, a LaunchAgent kept it alive, the panel lit up. Done.

Then my fans spun up and stayed up. `go-nfsv4` — FUSE-T's userspace NFS server — sat at **100% CPU**, indefinitely.

The cause is a property of the whole category, not a bug I could patch. The desktop app watches the repo for changes. **NFS has no fsevents**, so a file-watcher over a network mount can't get push notifications — it falls back to *recursively polling*. And I'd mounted the entire `src` tree: every worktree, every `node_modules`, hundreds of thousands of files, walked over the network, forever. A network filesystem under a file-watcher is a polling bomb.

But the failure handed me the insight: **the panel doesn't need my files. It needs my `.git`.** `repoSlugs` comes from the remote URL; the checks come from `gh` hitting GitHub's API. The working tree — the expensive part to mirror — is irrelevant to the panel.

## The fix: mirror the git, not the filesystem

So I threw out the mount and built a mirror that produces *real local files the OS can watch natively*:

- Keep a blobless clone of the repo on the Mac at the identical path.
- Every 60 seconds, ask the box for its `git worktree list` and GitHub for my open PRs.
- For each remote worktree whose branch has an open PR, recreate it locally as a `git worktree` on the matching branch — a `git fetch`, kilobytes, no working-tree copy of `node_modules`.
- Prune the ones whose PRs closed.

Real local files → fsevents works → the watcher is cheap → `go-nfsv4` is gone and idle CPU is back to zero. The footprint is git metadata plus tracked source, scoped to the branches that actually have CI to show. A new PR appears within a minute; a closed one disappears.

A few macOS traps were worth the scar tissue:

- **You can't operate — or even read — the mount from a headless SSH session.** A FUSE-T mount (and, it turns out, launchd-owned git worktrees) live in the GUI `gui/$UID` domain; `git` run via `ssh mac '...'` returns "Operation not permitted." Do the work in launchd, verify in the GUI.
- **`/home` doesn't exist on macOS by default** (autofs owns it). If your remote path starts with `/home`, free it once with a one-line `auto_master` edit. Paths under `/Users` need nothing.
- **The `/System/Volumes/Data` firmlink** means `git worktree list` reports canonical paths; compare with that prefix stripped or your prune step churns every cycle.

## I packaged it

It's a single bash script — point it at your SSH host and the repo path; it clones, reconciles every 60s via a LaunchAgent, and stays out of the way. Open source, MIT:

**[github.com/evoleinik/claude-ci-mirror](https://github.com/evoleinik/claude-ci-mirror)**

```sh
printf 'REMOTE=box\nREMOTE_REPO=/home/you/src/app\n' > ~/.config/claude-ci-mirror/config
claude-ci-mirror doctor && claude-ci-mirror install
```

## Takeaway

When a tool integration breaks across a machine boundary, it's usually assuming a local path. Make the path exist — but give it *real local files*, not a network mount. The mount is the obvious move, and it works for about a minute, until a file-watcher starts polling it and eats a core. The panel was never broken; it was looking in the right place on the wrong filesystem. The real trick wasn't mounting the filesystem — it was noticing the panel only ever wanted the `.git`.
