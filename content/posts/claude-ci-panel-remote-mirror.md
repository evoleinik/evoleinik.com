---
title: "The Path Has To Exist: Fixing Claude's CI Panel for Remote Dev Sessions"
date: 2026-06-01
tags: [claude-code, macos, fuse, sshfs, remote-development, devtools]
summary: "Claude's desktop CI/PR panel kept showing 'CI checks unavailable' for my remote dev sessions. The reason was dumber than it looked: it shells out to local gh in the session's working directory — a Linux path that doesn't exist on my Mac. Here's how I fixed the premise instead of the app, by mirroring the remote repo at its real path with a read-only FUSE-T sshfs mount, plus the three FUSE gotchas that cost me an afternoon."
---

My code lives on a Linux box. I drive it from a Mac with Claude Code running in the Claude desktop app, pointed at the box over SSH — so the session's working directory is a remote path. Everything works — except the desktop app's CI/PR panel, which shows "CI checks unavailable" for every pull request.

The reason is dumber than it looks. The panel doesn't subscribe to GitHub webhooks. It shells out to your local `gh` CLI, in the **session's working directory**, on the Mac. For a remote session that directory is a Linux path — `/home/eo/src/airshelf/...` — which doesn't exist on the Mac. `gh` spawns, hits `ENOENT`, and the panel goes dark.

So I stopped trying to "fix the app" and fixed the premise instead: **make that exact path exist on the Mac, with a real `.git`.** Then the local `gh` resolves the repo and the panel lights up — no patching, survives every app update.

The clean way to do that in 2026 is FUSE-T + sshfs.

## What I ruled out first

**Webhooks into the panel.** They don't exist. The only event-driven GitHub integration Claude ships is Routines — cloud agents that spin up a *fresh* session on a PR or Release event. Useful, but it's not the local panel, and it can't wake the session you're sitting in.

**NFS.** My first instinct. It died twice: macOS `autofs` owns `/home`, so `mkdir /home/eo` returns "Operation not supported"; and an NFS export can't filter per-file, so exporting `/home/eo` would hand the network my SSH keys and `.env` files. Wrong tool.

## The build

The whole fix is one mount and a keep-alive. Three things make it safe and boring:

**Scope the mount to the subtree you need.** Not all of `/home/eo` — just `box:/home/eo/src`. SSH keys and shell dotfiles live one level up and never get mounted.

**Read-only.** A read-write mount means Finder and Spotlight will scatter `.DS_Store` files into your live working tree on the server. `-o ro` and the problem disappears.

**FUSE-T, not macFUSE.** FUSE-T is kext-less — it runs a local NFS v4 server instead of a kernel extension. On modern, locked-down macOS that means no Recovery-mode kext approval and no security downgrade. (`brew install --cask fuse-t fuse-t-sshfs`.)

Making `/home/eo/src` exist on a read-only macOS root is the fiddly part. On my machine `/home` was already a symlink to the writable data volume, so I only had to evict `autofs`:

```bash
sudo sed -i '' 's|^/home|#/home|' /etc/auto_master   # free /home from autofs
sudo automount -vc                                    # no reboot needed
sudo mkdir -p /home/eo/src && sudo chown "$(id -un)":staff /home/eo /home/eo/src
sshfs box:/home/eo/src /home/eo/src -o ro -o reconnect -o volname=airshelf-src
```

(If `/home` isn't already a symlink, `/etc/synthetic.conf` creates the root-level entry — that one needs a reboot.)

A LaunchAgent re-runs an idempotent mount script every 60 seconds so reboots and network blips self-heal.

## The FUSE gotchas that actually cost me time

The mount was the easy 20%. The other 80% was three non-obvious traps — the kind of thing worth writing down so nobody (including me) burns an afternoon on them again.

**1. The mount must be created from a GUI login session — not headless SSH.** I scripted the whole thing over `ssh mac '...'` and every access returned "Operation not permitted," while the *identical* command run in the Mac's own Terminal worked perfectly. A FUSE-T mount born in a non-GUI SSH session has no TCC/GUI context and serves nothing. The LaunchAgent solves this for free: it runs in the user's `gui/$UID` domain, which is the right context.

**2. Don't trust the `mount` table for "is it mounted?"** FUSE-T lists a single mount as *two* identical lines, and leaves stale lines behind after an unmount. My first idempotency check grepped `mount` — so it both double-mounted and, later, *skipped* a real mount because a stale line fooled it. The robust check is a **liveness probe**: `test -e /home/eo/src/<repo>/.git`. If the path you actually need doesn't resolve, remount. The mount table is theater.

**3. Kill the `sshfs` process *before* you unmount.** Force-unmounting while the process is still alive produces a half-dead mount: the entry lingers, the proc lingers, and every access throws "Operation not permitted" — and a fresh mount on the same point fails with `fuse: mount failed with error: -1`. The clean recovery is `pkill -9 -f sshfs` first; the stale entry then clears itself, and the point is mountable again. I learned this by doing the opposite, repeatedly.

## Takeaway

When a tool integration breaks across a machine boundary, check whether it's secretly assuming a local path. Claude's CI panel was — it just runs `gh` where it thinks the repo is. You don't need the vendor to ship a feature; you need the path to exist. A scoped, read-only FUSE-T mount makes the remote repo present at its real path on the Mac, and the "broken" feature was never broken — it was looking in the right place on the wrong filesystem.
