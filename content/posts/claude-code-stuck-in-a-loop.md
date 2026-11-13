---
title: "Claude Code stuck in a loop: a CLAUDE.md rule and a hook"
date: 2026-11-13
tags: [claude-code, ai-agents, claude-md, hooks]
summary: "Claude Code going in circles on the same bug? Add a dead-end rule to CLAUDE.md and a UserPromptSubmit hook that triggers it."
---

When Claude Code goes in circles, it is not short of ideas. It is stuck on one wrong assumption, and every new attempt builds on the last. The fix is a rule in `CLAUDE.md` that tells it to stop editing and list what it actually knows. A small `UserPromptSubmit` hook then reminds it of the rule when your messages show a loop.

The rule comes from a post in the [emacsway_log](https://t.me/emacsway_log/1932) Telegram channel. I tuned the hook on 60 days of my own prompts.

## Spot the loop by what you can see

You know the pattern. The agent proposes a fix. You say "doesn't work". It apologises and changes something else. "Still doesn't work." By round five you are swearing at it.

Three loops feed each other here:

1. **Failed attempts stay in the context.** The agent's next guess grows out of its last one, so the guesses look alike.
2. **Frustration strips the facts out.** "Still broken" says less than the error text did. Fewer facts mean more guessing, and more guessing means more failures.
3. **Pressure to show progress.** The agent patches the symptom instead of diagnosing it.

Nothing in the session breaks these loops unless you add something that does. Swearing sometimes "works" because it carries one useful bit: your approach is wrong. The rest is noise. It pushes the model into apologising or into a big rewrite.

## Add the rule to CLAUDE.md

Put this in `~/.claude/CLAUDE.md` so it applies to every project, or in a repo's `CLAUDE.md` so the team gets it too:

```markdown
## Dead end in a session

Know the signs by what you can see, not by how the session feels. I ask the
same question again, or report the same symptom after your fix. I correct a fact
you got wrong. My replies get shorter or angrier. You edit the same spot a third
time, or revert your own change. Anger means "the approach is wrong and you are
losing information". It is not a cue to apologise. "stop, meta" means the same.

When you see one, stop editing. Look at how the search went wrong.
1. Write three lists. What a fact proved. What a fact disproved. What is only
   assumed.
2. Draw the loop that keeps you stuck, in 3 to 6 nodes.
3. Find the assumption every failed attempt shares. Test it first, with the
   cheapest check.
4. Tell two cases apart. If the knowledge exists and went unused, restate the
   task from scratch. If a fact is missing, go and observe it in a log, a test,
   a query, the source or the docs. A new guess fixes neither.
5. If failed attempts fill the context, give a fresh agent or a new session the
   step 1 lists only. Leave out the attempts and your theories.
6. Tell me in three lines: the loop, the shared assumption, the next step.

Every step ends in a check or an observation. When I say only "doesn't work",
fetch the error text yourself or ask me for it.
```

Step 4 matters most. Some dead ends are about attention: the model knows it should read the real error, but the context pulls it toward one more patch. Others are about a missing fact, such as the database state or an API newer than its training. No amount of thinking produces that fact. It has to be observed. Without step 4, "think harder" becomes a smarter way to keep guessing.

Step 5 uses a fresh context on purpose. A new agent that gets only the facts is not anchored on the failed attempts.

## Add a UserPromptSubmit hook that triggers it

A rule only works if the agent remembers it in the middle of a long session. A `UserPromptSubmit` hook runs on every message you send. Whatever it prints to stdout is added to the context. So it can spot the signs in your message and point the agent at the rule.

Save this as `~/.claude/hooks/dead_end.py`:

```python
#!/usr/bin/env python3
"""UserPromptSubmit hook: point Claude at the dead-end rule when a prompt shows a loop."""
import json
import re
import sys

SIGNS = [
    ("asked to step back", r"\bstop,? meta\b|\bmeta[- ]?position\b|^\W*stop it\b"),
    ("anger at the agent",
     r"\bwtf\b|\bwhat the fuck\b|\bdon'?t be (stupid|dumb)\b"
     r"|\b(you'?re|you are|are you)\b[^.?!\n]{0,15}\b(stupid|dumb|useless)\b"),
    ("the same thing again",
     r"\bstill (doesn'?t|don'?t|isn'?t) (work|get|understand|give|help|fix|make sense)"
     r"|\bstill (not (working|fixed|right|enough|clear)|broken|wrong|the same)\b"
     r"|\bsame (error|problem|issue|bug|symptom)\b"
     r"|\b(didn'?t|doesn'?t|did not|does not) (fix|help)\b"
     r"|\b(don'?t|do not) understand again\b|\bas i (already )?said\b"),
]
# Pasted text is not you speaking.
PASTED = re.compile(r"<pasted_content[^>]*>.*?</pasted_content>", re.S | re.I)


def main() -> int:
    try:
        prompt = json.loads(sys.stdin.read()).get("prompt")
    except (ValueError, AttributeError):
        return 0
    if not isinstance(prompt, str):
        return 0
    typed = PASTED.sub(" ", prompt)
    for kind, pattern in SIGNS:
        m = re.search(pattern, typed, re.I | re.M)
        if m:
            print(f'Dead-end check ({kind}: "{m.group(0)}"). If this repeats an earlier '
                  "question or symptom, or corrects a fact, stop editing and follow "
                  "CLAUDE.md § Dead end in a session. Otherwise ignore this note.")
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Then register it in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/dead_end.py", "timeout": 5 }
        ]
      }
    ]
  }
}
```

If you already have a `UserPromptSubmit` entry, add the command to its `hooks` list. Don't add a second block.

The hook always exits 0, so it never blocks a prompt. A hook that exits 2 blocks the prompt and shows `UserPromptSubmit operation blocked by hook`. That is the wrong behaviour for a reminder.

## Tune the patterns on your own prompts

Claude Code keeps every session as JSONL under `~/.claude/projects/`. Pull out your typed messages and run the hook's patterns over them:

```bash
python3 - <<'EOF'
import glob, json, os, re, sys
sys.path.insert(0, os.path.expanduser("~/.claude/hooks"))
import dead_end
seen = set()
for f in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")):
    for line in open(f):
        try:
            o = json.loads(line)
        except ValueError:
            continue
        c = o.get("message", {}).get("content") if o.get("type") == "user" else None
        if isinstance(c, str) and not c.startswith("<"):
            seen.add(c.strip()[:300])
hits = [p for p in seen if any(re.search(rx, p, re.I | re.M) for _, rx in dead_end.SIGNS)]
print(f"{len(hits)} of {len(seen)} prompts flagged")
for p in hits:
    print("-", p[:120])
EOF
```

My first draft flagged 24 of 4,318 prompts from 60 days, and about a third were false hits. "Competition doesn't work?" matched `doesn't work`. So did "we still don't know which model it uses". The shipped patterns above flag 16 (0.37%), and 14 of those were real loops.

Two lessons came out of that. A bare "doesn't work" is usually a first bug report, not a repeat, so the patterns only match "still doesn't work" and "didn't fix". And my own loops were mostly about understanding, not code: "I don't understand again", "it still doesn't give me". The rule covers both, because both are the agent repeating itself.

## Verify it worked

Pipe a fake payload into the hook:

```bash
echo '{"prompt": "wtf, still broken after your fix"}' | python3 ~/.claude/hooks/dead_end.py
```

Expected output:

```text
Dead-end check (anger at the agent: "wtf"). If this repeats an earlier question or symptom, or corrects a fact, stop editing and follow CLAUDE.md § Dead end in a session. Otherwise ignore this note.
```

A normal prompt prints nothing:

```bash
echo '{"prompt": "run the tests again"}' | python3 ~/.claude/hooks/dead_end.py
```

The real test happens in a session. The next time Claude Code goes in circles, you should get three lines (the loop, the shared assumption, the next check) instead of "You're absolutely right, let me try another approach."

## Claude Code going in circles: what you can do

The rule helps the agent notice. You can make it easier:

- Say "stop, meta" instead of swearing. It carries the same bit with no noise.
- Paste the error output, not "doesn't work". The verdict is one bit. The output is the fact.
- When the session has run long, start a new one with only the list of proven facts.

## Trade-offs

- **The hook only sees your side.** Repeated edits to one spot and reverted changes happen inside the agent's turn. No prompt hook can see them, so that half lives only in the rule.
- **Regex is blunt.** Expect a false hit now and then. The note says "otherwise ignore this note", so a false hit costs a sentence of context and nothing more.
- **Don't trigger on mood.** A rule that fires on "frustration" fires on every short message. Stick to signs you can observe: the same question, the same symptom, a correction.
- **It is behaviour, not a guarantee.** The agent can still ignore the note. The hook raises the odds that it reads the rule at the right moment. It cannot force the diagnosis.
