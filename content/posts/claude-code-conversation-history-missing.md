---
title: "Claude Code conversation history missing: cleanupPeriodDays"
date: 2026-11-15
draft: false
tags: [claude-code, cleanupperioddays, rsync, backup]
summary: "Claude Code deletes session transcripts older than 30 days. Set cleanupPeriodDays in settings.json and archive them without rsync --delete."
---

Claude Code deletes session transcripts older than 30 days, and it does not tell you. To keep them, set `cleanupPeriodDays` to a large number such as `3650` in `~/.claude/settings.json`. Then copy `~/.claude/projects` to an archive with plain `rsync -a`, never with `--delete`.

I found this when old sessions were gone from `~/.claude/projects` on my build server. `claude --resume` could not find them, and nothing had warned me. Everything below was tested on Claude Code 2.1.318.

## Set cleanupPeriodDays in settings.json

```bash
f=~/.claude/settings.json
[ -f "$f" ] || echo '{}' > "$f"
jq '.cleanupPeriodDays = 3650' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
```

`3650` days is about ten years. The `jq` edit keeps every other key in the file. The second line creates the file if you never had one.

The [settings reference](https://code.claude.com/docs/en/settings-reference#cleanupperioddays) describes the key like this:

> Set how many days Claude Code keeps session transcripts and other application data before deleting them. Claude Code runs the deletion as a background sweep after a session starts, as long as it can safely determine the retention period. The sweep deletes transcripts without showing a message, so a session you haven't used for longer than the retention period no longer appears in the `/resume` picker.

The default is `30`. The minimum is `1`.

Do not set it to `0` to mean "never clean up". Claude Code rejects `0`, and then it ignores your whole settings file, hooks and permission rules included. On 2.1.318 a `claude -p` run printed this:

```text
These settings files did not load, so nothing in them is in effect, including hooks and permission rules. Each loads again once the problem listed for it is fixed:
  /home/you/.claude/settings.json (cleanupPeriodDays): Number must be greater than or equal to 0
```

The message says 0 is allowed, but it is not. The real minimum is 1. `claude doctor` explains why. Older versions treated `0` as "write no transcripts at all":

```text
Invalid settings
- /home/you/.claude/settings.json › cleanupPeriodDays: Number must be greater than or equal to 0
  Suggested fix: cleanupPeriodDays must be at least 1. To keep transcripts for a long time, set a large number (e.g. 3650 for ~10 years). [...] (0 is rejected because it previously silently disabled all transcript writes, which users setting it to mean "never clean up" did not expect.)
```

## Archive transcripts without rsync --delete

```bash
mkdir -p ~/claude-archive
rsync -a ~/.claude/projects/ ~/claude-archive/projects/
```

The `mkdir` matters. Without it the first run fails with this error:

```text
rsync: [Receiver] mkdir "/home/you/claude-archive/projects" failed: No such file or directory (2)
```

Plain `rsync -a` copies new transcripts and refreshes the ones that grew, because a live session keeps appending to its file. It never removes anything from the archive.

`rsync -a --delete` makes the archive a mirror. When the sweep deletes a transcript, the next mirror run deletes the archive copy too. I checked this on a test tree. After a simulated sweep, the plain copy still held the deleted session. The `--delete` copy had lost it.

Run the archive every hour. Add this line with `crontab -e`:

```text
0 * * * * mkdir -p "$HOME/claude-archive" && rsync -a "$HOME/.claude/projects/" "$HOME/claude-archive/projects/"
```

I ran that command with cron's bare `PATH` and it worked. The same `rsync -a` also works with the `openrsync` that ships with macOS 15.

## Verify it worked

Check that the setting loads:

```bash
jq .cleanupPeriodDays ~/.claude/settings.json
claude doctor | grep -A3 'Invalid settings'
```

Expected output is `3650` from the first command and nothing from the second.

Check that the archive holds every transcript:

```bash
comm -23 \
  <(cd ~/.claude/projects && find . -name '*.jsonl' | sort) \
  <(cd ~/claude-archive/projects && find . -name '*.jsonl' | sort)
```

Expected output is nothing. Each printed line is a transcript the archive is missing.

Use `find` here, not a shell glob. Project folder names start with `-`, and subagent transcripts sit one level deeper.

After a month, check that old transcripts survive the sweep:

```bash
find ~/.claude/projects -name '*.jsonl' -mtime +30 | wc -l
```

Any number above zero means files last written more than 30 days ago are still there. On my server it prints `1386`.

## Claude Code chat history retention

The sweep covers more than transcripts. The [`.claude` directory docs](https://code.claude.com/docs/en/claude-directory#cleaned-up-automatically) list what it deletes once it passes `cleanupPeriodDays`:

| Path under `~/.claude/` | What it is |
| --- | --- |
| `projects/<project>/<session>.jsonl` | The conversation transcript |
| `projects/<project>/<session>/subagents/` | Subagent transcripts |
| `projects/<project>/<session>/tool-results/` | Large tool outputs |
| `file-history/<session>/` | File snapshots for checkpoint restore |
| `plans/`, `paste-cache/`, `debug/` | Plan files, large pastes, debug logs |

Some things stay:

- `~/.claude/history.jsonl` keeps the prompts you typed. So up-arrow still shows an old prompt after its conversation is gone.
- Auto memory in `projects/<project>/memory/` is not swept.
- Sessions you started or last continued in Claude Desktop or Cowork are kept at any age by default, since v2.1.248. `desktopSessionCleanupPeriodDays` sets a limit for them.

`claude purge <path>` deletes a project's transcripts on purpose. The archive protects you from that too.

## Claude Code conversation history location

Transcripts live in one JSONL file per session:

```text
~/.claude/projects/<project>/<session-id>.jsonl
```

`<project>` is your working directory with every non-alphanumeric character replaced by `-`. So `/home/you/src/myapp` becomes `-home-you-src-myapp`. Each line is one JSON object, such as a message, a tool call or a tool result.

The docs warn that this format is internal and changes between versions. To read a session as text, run `/export` inside it.

These files get big. My server holds 3,058 transcript files across 1,041 project folders, 5.7 GB in total. The oldest was last written on 2026-03-17.

## Resume a previous Claude Code session

`claude --continue` reopens the most recent session in the current directory. `claude --resume` opens a picker, or takes a session name, a session ID, or the absolute path to a `.jsonl` file. All of them read transcripts on disk.

Once the sweep deletes a transcript, that session is gone from the picker. Resuming it by ID fails with:

```text
No conversation found with session ID: <session-id>
```

The docs describe no way to bring it back. Your archive is the copy.

Find the session by a word you remember. The file name is the session ID:

```bash
grep -rl --include='*.jsonl' --exclude-dir=subagents 'flaky test' ~/claude-archive/projects
```

Copy it back into place, then resume from the project directory:

```bash
p=-home-you-src-myapp
id=<session-id>
cp -a ~/claude-archive/projects/$p/$id.jsonl ~/.claude/projects/$p/
cd ~/src/myapp && claude --resume $id
```

If a `$id/` folder sits next to the file in the archive, copy it too. It holds the session's subagent transcripts and large tool outputs.

Set `cleanupPeriodDays` before you restore. Otherwise the next sweep can delete the old session again.

You can also run `claude --resume ~/claude-archive/projects/$p/$id.jsonl` with the full path. It works, but in my test Claude Code appended the new turns to the archive file itself. Copying back keeps the archive as it was.

## Trade-offs

Disk. Transcripts hold every file Claude read and every command output. Mine are 5.7 GB, and the archive doubles that. The archive also never shrinks, so prune it by hand when it gets too big.

Secrets. The docs are blunt: "Transcripts and history are not encrypted at rest. OS file permissions are the only protection." If a tool read a `.env` file, that value now sits in a transcript. Ten years of retention keeps it for ten years. Keep the archive on an encrypted disk and out of shared or cloud-synced folders.

Company policy. When managed settings set `cleanupPeriodDays`, Claude Code sweeps at that value and your setting loses. A short company value is usually there on purpose. Ask before you archive around it.

Same disk. The archive sits next to the original. It survives the sweep and `claude purge`. It does not survive a dead disk.

Skip all this on a shared machine, or for work under rules that require short retention. Skip it too if you never resume sessions older than a month.
