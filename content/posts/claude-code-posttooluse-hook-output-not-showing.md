---
title: "Claude Code PostToolUse hook output not showing: use JSON"
date: 2026-11-15
tags: [claude-code, hooks, posttooluse, ai-agents]
summary: "A PostToolUse hook that prints plain text is ignored by Claude. Return additionalContext JSON, or exit 2 with stderr, and Claude reads the message."
draft: false
---

A Claude Code PostToolUse hook that prints plain text to stdout runs fine, and Claude never sees a word of it.
To get a message to Claude, exit 0 and print one JSON object with `hookSpecificOutput.additionalContext`.
The other way is to write the message to stderr and exit 2.

I tested eight output forms on Claude Code 2.1.318 on 2026-11-15, against the hooks reference as published that day.
The table near the end shows what each one did.
The hook contract changes between versions, so the last section shows how to recheck it after an upgrade.

## Return additionalContext JSON from the PostToolUse hook

This is the change that matters. Swap the `echo`:

```bash
# Invisible to Claude: plain stdout on PostToolUse is dropped
echo "The test suite has not run since this change."
```

for one JSON object built with `jq`:

```bash
# Claude reads this next to the tool result
jq -nc --arg msg "The test suite has not run since this change." \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'
exit 0
```

Three details break this silently:

1. `additionalContext` must sit inside `hookSpecificOutput`, next to `hookEventName`. At the top level it is ignored with no error in the transcript.
2. Stdout must hold nothing but that one object. One stray `echo` before it, or a shell profile that prints a banner, turns the whole output into plain text.
3. Build the JSON with `jq` or a JSON library. String concatenation breaks the first time your message contains a quote.

If you would rather not print JSON, this also reaches Claude:

```bash
echo "The test suite has not run since this change." >&2
exit 2
```

On PostToolUse, exit 2 cannot block anything, because the tool has already run.
It only hands your stderr to Claude.

## Write a hook that finds the right repo

Here is a complete, tested hook. After any `git commit`, it tells Claude when the commit skipped `CHANGELOG.md`.
Save it as `.claude/hooks/after-commit.sh` and run `chmod +x` on it.

```bash
#!/bin/bash
# PostToolUse hook on Bash: after a git commit, remind Claude about the changelog.
input=$(cat)
cmd=$(jq -r '.tool_input.command // empty' <<<"$input")

case "$cmd" in
  *"git commit"*) ;;
  *) exit 0 ;;
esac

# The hook runs in Claude's shell directory, and .cwd says the same.
# A "cd /other/repo && git commit" outside the project ran somewhere else,
# and .cwd still shows the project root. Take the absolute cd target.
dir=$(jq -r '.cwd' <<<"$input")
re='^cd[[:space:]]+(/[^[:space:];&]+)[[:space:]]*&&'
if [[ "$cmd" =~ $re ]]; then
  dir="${BASH_REMATCH[1]}"
fi

last=$(git -C "$dir" log -1 --format=%s 2>/dev/null) || exit 0
# Stay quiet when the commit already touched the changelog.
git -C "$dir" show --name-only --format= HEAD | grep -qx CHANGELOG.md && exit 0

jq -nc --arg msg "Commit \"$last\" in $dir did not touch CHANGELOG.md." \
  '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'
```

The message is a plain statement of fact.
The docs advise this, because text that reads like a system command can trip Claude's prompt-injection defences.

The `cd` parsing exists because of the working-directory trap below.

## Register the hook with "$CLAUDE_PROJECT_DIR"

Put this in `.claude/settings.json` at the project root:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/after-commit.sh"
          }
        ]
      }
    ]
  }
}
```

Never write the path as `.claude/hooks/after-commit.sh`.
The docs define `$CLAUDE_PROJECT_DIR` as "the project root where the session started", and that path never moves.
A relative path is resolved from wherever Claude's shell happens to be.

## Find the working directory a hook really runs in

A hook does not run in a fixed directory. It runs wherever Claude's Bash shell is at that moment.
I logged `pwd` and the input's `cwd` field from a hook across four commands:

| Command Claude ran | Hook `pwd` and `.cwd` |
|---|---|
| `cd sub && git commit ...` | `<project>/sub` |
| `echo hi` (next call) | `<project>/sub`, because the `cd` persists |
| `cd /path/to/other-repo && git commit ...` | `<project>`, not the other repo |
| `echo hi` (next call) | `<project>` |

Two traps come out of that table.

First, a relative hook path breaks once Claude has done a `cd` inside the project.
The hook never starts, the transcript records a non-blocking error, and Claude is told nothing.
On Linux the error read:

```text
Failed with non-blocking status code: /bin/sh: 1: .claude/hooks/post.sh: not found
```

The docs show the macOS form as `/bin/sh: /path/to/hook.sh: No such file or directory`.
The same hook ran fine on the next call, after the shell went back to the project root.
That makes the bug intermittent, which is worse than broken.

Second, a `cd` to a directory outside the project does not stick.
Claude Code resets the shell and appends this to the tool result:

```text
Shell cwd was reset to /path/to/project
```

The hook then runs in the project root, and `.cwd` also says the project root.
So a hook that runs `git log` to inspect "the repo that was just committed to" reads the wrong repo.
It gives no error, just a wrong answer.
That is why the hook above takes the `cd` target from `tool_input.command`.

One more case from the docs: if Claude enters a git worktree, `$CLAUDE_PROJECT_DIR` keeps pointing at the main checkout.
The `cwd` field follows Claude into the worktree.

## Verify it worked

First, feed the hook a fake payload. This needs no Claude session and runs in a second:

```bash
echo '{"tool_input":{"command":"git commit -m test"},"cwd":"'"$PWD"'"}' \
  | .claude/hooks/after-commit.sh | jq .
```

If your last commit skipped the changelog, you should get one valid object:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Commit \"add login page\" in /path/to/repo did not touch CHANGELOG.md."
  }
}
```

If `jq` reports a parse error here, Claude Code will not read it either.

Then run Claude headless with a debug log, and ask it to repeat what it received:

```bash
claude -p "Run: git commit --allow-empty -m 'hook test'. Then quote, word for word, any hook message you received." \
  --allowedTools Bash --debug-file /tmp/hook-debug.log

grep -E "after-commit|does not start with|unrecognized keys" /tmp/hook-debug.log
```

A working hook leaves these two lines:

```text
Hooks: PostToolUse:Bash ["$CLAUDE_PROJECT_DIR"/.claude/hooks/after-commit.sh] finished with status 0 (12ms)
Hook PostToolUse ("$CLAUDE_PROJECT_DIR"/.claude/hooks/after-commit.sh) provided additionalContext (225 chars)
```

Your timing and character count will differ.

Claude's reply should quote your message.
Claude Code labels the message like this before Claude sees it:

```text
PostToolUse:Bash hook additional context: Commit "hook test" in /path/to/repo did not touch CHANGELOG.md.
```

If the message is missing, the grep usually tells you why.
`Hook output does not start with {, treating as plain text` means something printed before your JSON.
The other common line is this one:

```text
Hook JSON output had unrecognized keys (ignored): additionalContext. Did you mean hookSpecificOutput.additionalContext (with a hookEventName)?
```

That means the field is at the wrong level.

## What each PostToolUse hook output does

I ran one PostToolUse hook on Bash with eight output forms.
I read what reached the model from the session transcript, which stores each model request, and I asked Claude to quote what it saw.
The two sources agreed on every row. Claude Code 2.1.318, headless `-p` mode:

| Hook output | Claude sees it? | What happened |
|---|---|---|
| Plain text on stdout, exit 0 | No | Kept in the transcript file only |
| Text on stderr, exit 1 | No | Logged as `Failed with non-blocking status code: <stderr>` |
| Text on stderr, exit 2 | Yes | `PostToolUse:Bash hook blocking error from command: "<hook>": [<hook>]: <stderr>` |
| `{"decision":"block","reason":"..."}` | Yes | `PostToolUse:Bash hook blocking error from command: "<hook>": <reason>` |
| `hookSpecificOutput.additionalContext` | Yes | `PostToolUse:Bash hook additional context: <text>` |
| `additionalContext` at the top level | No | Ignored, with only a debug log line |
| `systemMessage` | No | Sent to the user. In `stream-json` output it arrived as `{"type":"system","subtype":"informational","content":"PostToolUse:Bash says: <text>"}` |
| `decision: block` plus `suppressOutput: true` | Yes | The reason still arrived. The docs list `suppressOutput` as "Has no effect" |

In every row the command had already run, and Claude went on to the next one.
On PostToolUse, "block" does not block anything.

## PostToolUse hook error: why exit 1 is silent

If you searched for "posttooluse hook error", you probably hit one of two cases.

In the first, the transcript shows a hook error notice that carries `Failed with non-blocking status code`.
That means your hook exited with a code other than 0 or 2, or never started.
Claude was not told, and the session went on.
Run the hook by hand with a sample payload, as in the verify step, and check `echo $?`.

In the second, you wanted the hook to fail loudly and it didn't.
Exit 1 is the usual Unix failure code, but Claude Code treats it as non-blocking.
Use exit 2 when Claude must hear about it.

## Claude Code hooks additional context vs decision block

Both reach Claude. They differ in how the message is framed.

`additionalContext` arrives labelled "hook additional context". Use it for facts and reminders, such as "this commit skipped the changelog".

`decision: "block"` and exit 2 both arrive labelled "hook blocking error", even though nothing was blocked.
Claude reads it as an error report.
Use it when you want Claude to treat the message as a problem to fix, such as a linter that failed on the file Claude just wrote.

Older notes, including my own, say PostToolUse needs `{"decision": "block", "reason": "..."}` to show anything.
On 2.1.318 that is one of three working forms, and the only one besides exit 2 that is framed as an error.

## Trade-offs

A PostToolUse message is a fact Claude learns after the fact. It cannot undo the command.
If the command must not run, use a PreToolUse hook.
If the rule never changes, put it in `CLAUDE.md`, which costs no script run per tool call.

Each message costs context tokens every time it fires.
Match narrowly with `matcher` and exit early, as the `case` above does.
The docs cap each message at 10,000 characters.
Past that, Claude gets a file path and a 2,000-character preview.

The docs also say that on `--resume`, Claude Code replays the saved text and does not re-run the hook.
So a message that holds a commit hash or a timestamp goes stale in a resumed session.

The `cd` parsing in the example is a heuristic.
It handles the common `cd /abs/path && ...` form only.
It misses `pushd`, subshells, and a relative `cd ../other` that leaves the project.
If you depend on the exact directory, read it from the command's own output instead.

Finally, this is how 2.1.318 behaved, and the hook contract has changed between versions before.
Rerun the verify step after each Claude Code upgrade.
A hook that goes quiet gives you no warning.
