---
title: "Reading WhatsApp from an AI Agent Without Giving SSH Full Disk Access"
date: 2026-10-31
tags: [macos, security, ai-agents, ssh, cli]
summary: "The usual advice for reading protected Mac data over SSH is to give sshd Full Disk Access. That hands every SSH login your Mail, Messages and Safari history. A 154-line launcher gives the grant to one fixed program instead."
---

I wanted Claude Code, running on my Linux dev box, to read my WhatsApp. WhatsApp for Mac already keeps the whole chat history in a plain SQLite file on my Mac, so the reader was the easy part. The hard part was macOS, and the standard fix for it turned out to be much worse than the problem.

## The easy part

WhatsApp for Mac stores everything in `~/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite`. I wrote [`wa`](https://github.com/evoleinik/wa), one Python file with no dependencies. It opens that database read-only and answers `wa chats --unread`, `wa read alice --since 7d`, `wa search invoice` and `wa media <id>`, with `--json` everywhere. From another machine it runs over SSH, so the database never leaves the Mac. (If you want an archive rather than live reads, [wacrawl](https://github.com/openclaw/wacrawl) reads the same file and is the more complete tool.)

The first call over SSH failed:

```
ls: .../group.net.whatsapp.WhatsApp.shared: Operation not permitted
```

macOS protects other apps' data with TCC, and a program needs Full Disk Access to read it.

## The fix everyone uses, and why it is bad

Search for this error and every answer says the same thing. Add `/usr/libexec/sshd-keygen-wrapper` to Full Disk Access. I did, and `wa` worked.

Then I thought about what I had granted. TCC decides by the *responsible process*. For anything started over SSH, that is `sshd-keygen-wrapper`. So the grant does not cover one command. It covers every SSH login, with any key, running anything. Every SSH session could now read Mail, Messages, Safari history, Desktop, Documents and every other app's container.

My dev box runs AI agents all day. They read web pages, email and, now, WhatsApp messages written by other people. Any of that text can carry a prompt injection. With that grant in place, one injected instruction plus `ssh mac` reaches everything on the Mac.

## How TCC decides

Three facts set the shape of the fix:

1. TCC checks the responsible process, and child processes inherit it.
2. A process started over SSH has `sshd-keygen-wrapper` as its responsible process. Granting Full Disk Access to some other binary does nothing when that binary is started from SSH.
3. A process can give up that inherited responsibility. `responsibility_spawnattrs_setdisclaim` is a spawn attribute that libsystem exports and Apple does not document. A process spawned with it becomes its own responsible process, and TCC checks *its* grant. iTerm2, the .NET macOS tooling and [tcc-venv](https://pypi.org/project/tcc-venv/) all use it.

So the grant can go on one small program that does one fixed job, and SSH itself keeps nothing.

## The launcher

`wa-launch` is 154 lines of C. Over SSH, `wa` now runs `ssh mac /usr/local/libexec/wa/wa-launch chats --unread` instead of piping itself to Python.

1. `wa-launch` re-executes itself in place (`POSIX_SPAWN_SETEXEC`) with responsibility disclaimed. Now it is its own responsible process.
2. It starts Python, which inherits that responsibility. TCC checks `wa-launch`'s grant, and `wa-launch` is the only binary on the list.
3. Python runs one fixed, root-owned copy of `wa`, with `-I -S` and an empty environment.

Before it runs anything, it checks that the Python binary, its standard library and the `wa` script are owned by root. It checks every folder above them as well, and refuses if any of them is writable by anyone else or is a symlink. Code you can edit gives nothing, because anything running as you could edit it too. That check is what makes the grant narrow.

The result, measured from the dev box:

```
$ ssh mac ls ~/Library/Mail
ls: /Users/me/Library/Mail: Operation not permitted
$ wa status
ok: 95320 messages, 288 chats, latest 2026-10-31T16:19:23+09:00, 132.5 MB
```

Plain SSH can't read protected data anymore, and `wa` can. Calls take about half a second over a shared SSH connection.

## What the security review caught

I ran an automated security review on the first commit. It found two holes, and both were real.

**The launched process could still write a file.** I had refused `-o`, so `wa media` could not save to a path the caller chose. Plain `wa media` still saved to `~/.cache/wa/media` under the grant, though. A symlink placed there could aim that write into a folder macOS protects. Now `wa-launch` sets `WA_LAUNCHED=1`, and `wa` refuses every command that writes. Media goes back over SSH as data and is saved on the machine that asked.

**`/usr/bin/python3` is not one fixed program.** It is a stub that follows `xcode-select`. If Xcode was installed by dragging it into Applications, the user usually owns it. Then the Python files that run under the grant are editable by anyone running as you. The install script now pins the Command Line Tools Python, which Apple's installer puts under root. It checks that every file in its standard library is owned by root and builds both paths in. `wa-launch` checks them again on every run.

Each of these checks has a test, and I watched each test fail when I deleted its check. The full test needs a root-owned folder, and GitHub's macOS runners have passwordless `sudo`, so CI runs it on every push.

## The hole wasn't SSH

After removing the sshd grant, I looked at the rest of the Full Disk Access list. No terminal app was on it. One app was, and it runs user scripts. Its scripts lived in a folder that syncs from the same dev box, so anything on the box that could write that folder could plant a script. It would then run with full access the next time I used the app, with no SSH involved.

That path was wider than the sshd grant ever was. Moving that app's settings to a local folder closed it.

If you give Full Disk Access to anything that runs scripts (launchers, automation tools, file watchers), check where those scripts come from.

## What this does not fix

- The disclaim call is undocumented. If a macOS update breaks it, `wa-launch` loses access and `wa` exits 3. It fails closed and never ends up reading more.
- TCC only guards data. My dev box can still SSH into the Mac and run code as me. This change removes the reach into protected folders, not code execution. Limiting that SSH key is a separate job.
- Anything running as me on the Mac can call `wa-launch` and read WhatsApp. That is exactly the access I meant to grant, and nothing more.

## Try it

```bash
git clone https://github.com/evoleinik/wa && ./wa/launcher/install.sh
```

Then add `/usr/local/libexec/wa/wa-launch` to Full Disk Access, set `WA_HOST` and `WA_LAUNCHER` on the machine you read from, and remove `sshd-keygen-wrapper` from the list if you added it. The [design notes](https://github.com/evoleinik/wa/blob/main/docs/plans/2026-10-31-ssh-without-full-disk-access.md) compare this with three other options, including a launchd socket job that uses only documented behavior.

The pattern works for any protected data an agent should read over SSH. Give the grant to one small program that does one job, and make sure root owns everything it runs.
