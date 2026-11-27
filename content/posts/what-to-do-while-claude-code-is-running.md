---
title: "What to Do While Claude Code Is Running"
date: 2026-11-27
draft: false
tags: [claude-code, ai-agents, productivity, context-switching, lean]
summary: "Most Claude Code turns end in under 3 minutes, so a second session just queues for you. Measure your waits, then sort them by length."
---

Measure how long your Claude Code turns actually take, and then sort every wait by its length. When a turn takes under 3 minutes, stay in the session and plan the next prompt. When a turn runs over 30 minutes and has a check that runs by itself, walk away and do work only a person can do. A second session only helps when turns run longer than the time you take to read and reply, and most of mine do not.

For a long time, I did the opposite. I kept opening more sessions to keep the AI busy, and I ended days spread thin and deep on nothing. Then my co-founder told me he reads a business book while the AI works. That made me stop and measure what was actually happening on my machine.

## Measure how long your Claude Code turns take

You do not need to guess, because the data is already on your disk. Claude Code writes every session to JSON lines files under `~/.claude/projects/`, and each line has a timestamp. A turn here means the span from a prompt you typed to the last agent reply before your next prompt. That includes the model thinking, reading files and running commands.

The script below reads the last 14 days. Save it as `claude_waits.py` and run it. It needs only Python 3, no packages. Pass a folder pattern to look at one project, such as `python3 claude_waits.py '-home-me-src-myapp*'`.

```python
# How long do your Claude Code turns take? Reads ~/.claude/projects/*/*.jsonl
import glob, json, os, statistics as st, sys
from collections import Counter
from datetime import datetime, timedelta, timezone

DAYS = 14
cut = datetime.now(timezone.utc) - timedelta(days=DAYS)

def typed_prompt(o):
    if o.get("type") != "user" or o.get("isMeta") or o.get("isSidechain"):
        return False
    c = o.get("message", {}).get("content")
    if isinstance(c, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
            return False
        c = " ".join(b.get("text", "") for b in c if isinstance(b, dict))
    if not isinstance(c, str):
        return False
    c = c.strip()
    # skip harness text: notifications, resumed-session summaries, tool notes
    return bool(c) and not c.startswith(("<", "This session is being continued", "Tool loaded"))

turns = []  # (start, end, session file)
pattern = sys.argv[1] if len(sys.argv) > 1 else "*"
for f in glob.glob(os.path.expanduser(f"~/.claude/projects/{pattern}/*.jsonl")):
    if os.path.getmtime(f) < cut.timestamp():
        continue
    start = last = None
    for line in open(f, errors="ignore"):
        try:
            o = json.loads(line)
            t = datetime.fromisoformat(o["timestamp"].replace("Z", "+00:00"))
        except (ValueError, KeyError, TypeError):
            continue
        # a prompt typed while the agent was still busy joins the current turn
        if typed_prompt(o) and not (last and (t - last).total_seconds() < 10):
            if start and last > start:
                turns.append((start, last, f))
            start = last = t
        elif start and o.get("type") in ("assistant", "user"):
            last = t
    if start and last > start:
        turns.append((start, last, f))

turns = [x for x in turns if x[0] > cut and (x[1] - x[0]) < timedelta(hours=10)]
mins = sorted((b - a).total_seconds() / 60 for a, b, _ in turns)
print(f"{len(mins)} turns in {DAYS} days, median {st.median(mins):.1f} min")
for lo, hi, label in [(0, 3, "under 3 min"), (3, 30, "3 to 30 min"), (30, 600, "over 30 min")]:
    n = sum(lo <= m < hi for m in mins)
    print(f"  {label:12} {100 * n / len(mins):4.0f}%")

busy = Counter()  # minute -> agents working
for a, b, _ in turns:
    m = a.replace(second=0, microsecond=0)
    while m <= b:
        busy[m] += 1
        m += timedelta(minutes=1)
one = sum(v == 1 for v in busy.values())
print(f"only one agent working: {100 * one / len(busy):.0f}% of busy minutes")

per_day = Counter()
for day, f in {(a.date(), f) for a, _, f in turns}:
    per_day[day] += 1
print(f"sessions touched per day, median: {st.median(per_day.values()):.0f}")

idle = []
by_session = sorted(turns, key=lambda x: (x[2], x[0]))
for p, q in zip(by_session, by_session[1:]):
    if p[2] == q[2]:
        gap = (q[0] - p[1]).total_seconds() / 60
        if 0 <= gap < 240:
            idle.append(gap)
print(f"agent waits for you: median {st.median(idle):.1f} min, "
      f"over 10 min {100 * sum(g > 10 for g in idle) / len(idle):.0f}% of the time")
```

My output on 2026-11-27, across all projects on my Linux dev box:

```text
1831 turns in 14 days, median 0.6 min
  under 3 min    79%
  3 to 30 min    18%
  over 30 min     4%
only one agent working: 61% of busy minutes
sessions touched per day, median: 31
agent waits for you: median 1.7 min, over 10 min 18% of the time
```

The median turn ends in 36 seconds. 79% end within 3 minutes, and only 4% run over 30 minutes.

The concurrency numbers surprised me more. For 61% of the minutes when any agent was working, only one was. So I was not running agents in parallel much, even though it felt that way. I was switching myself across about 31 sessions a day. Some of those were started by other sessions, so the count runs high, but the pattern is clear.

Then there is the human side of the clock. After a turn ends, the agent waits a median 1.7 minutes for me, and 18% of the time it waits over 10 minutes. Those are agents queued behind me. The bottleneck was not the model. It was me.

## Sort the wait by its length

A thirty-second pause and a forty-minute background job ask different things of your attention. Put every run into one of three buckets before you touch another window.

| Wait | What to do |
| --- | --- |
| Under 3 minutes | Stay. Re-read the output. Write the next prompt. Decide how you will check the result. |
| 3 to 30 minutes | The trap. Too short for deep work, long enough to drift into a feed. Make the task smaller so it returns fast, or bigger so it runs long. |
| Over 30 minutes, with a done check | Leave. Do work only a person can do. |

Other engineers have run into the exact same wall. Atomic Object published a similar menu sorted by wait length (blink 10-30 s, pause 1-3 min, breather 3-7 min, break 7-12 min). Their ranking: staying one step ahead of the agent is best, real rest is second, doomscrolling is worst because you come back tired to review the output.

An Elixir Forum thread names the core problem: you do not know if the wait is 1 minute or 10. That uncertainty is what tricks you into opening a browser tab just for a second. Shape your tasks so they fall into the short bucket or the long one, and the guessing goes away.

## Stay in the session when the turn is short

Because 79% of turns finish within 3 minutes, staying put is the default most of the day. That does not mean staring at the spinner. It means staying inside the problem you are solving.

Use the wait to re-read your prompt, draft the next one in a scratch file, and plan how you will verify the output. When the agent finishes, you already know how you will test its work and what the follow-up will say, so the next turn starts warm.

Above all, do not open Slack or a feed. Tao Bojlén (March 2026) wrote that agent work leaves him with "a jittery craving for more", the same as doomscrolling, because fast prompts and variable results work like a slot machine. One indie developer built a menu bar app, Unwait, after a two-minute run kept turning into twenty minutes of short videos.

## Make long runs safe to walk away from

The middle bucket between 3 and 30 minutes is a trap because it is too short to get into deep work on something else, yet long enough to bore you into drifting away. If a task is going to take more than a few minutes, push it until it belongs in the third bucket and can run unattended. You can only walk away cleanly if the run does not need you hovering over it.

First, give the run a written brief before it starts. Thinking moves to the front, like batch-era programmers who checked programs by hand before submitting, because one syntax error could waste a day's run. Write down the scope, the files involved, the constraints and the expected behavior before the agent takes its first step.

Second, give it a check that runs by itself and says done or failed: a test command, a script that exits 1. Without it you have to come back and read, and you never really left. If the agent can run that script on its own, see the exit code, and keep fixing its work until the check passes, you do not have to play human compiler in the middle of the run.

Third, do not let the agent pull you back. Mitchell Hashimoto (February 2026) runs one agent in the background on easy, well-defined tasks while he does deep manual work on something else. He turns off its notifications and checks when it suits him. He says an agent runs only about 10% to 20% of his day. The human stays in charge of the clock.

Finally, read finished runs at set times, not whenever one pings. Treat a long run like mail rather than a phone call. When you finish your own block of work, check whether the done check passed, then review the diff with a clear head.

## Use long waits for work only you can do

For me that is the outside step a model cannot take: a sales call, a follow-up, a decision. A coding agent can refactor a module and run the test suite while I am away, and it cannot talk to a customer, unblock a teammate on a product question, or decide which feature we are cutting to make our deadline.

My co-founder reads a business book, and I can see why it works. A book holds no state you must reload, so it leaves less residue than a second session. Still, how you read matters. Read in two-minute pieces it turns into scrolling with paper, so keep it for long waits.

A walk or a real meal also counts. A feed does not. Scrolling a timeline gives you all the fatigue of looking at a screen with none of the recovery of a real break.

## Running multiple Claude Code sessions at once: do the math first

Running three or four sessions to move four times as fast sounds logical until you do the arithmetic.

Factories studied this as the "machine interference problem", from the 1940s: one operator, many machines. Too few machines and the operator idles. Too many and machines queue for the operator. When several looms or lathes stop near the same time, the single worker can only fix one while the others sit idle.

The textbook count of machines one person can tend: `(service time + run time) / service time`. Here, run time is how long the machine works by itself, and service time is how long the operator takes to unload it, check the output, and start the next cycle.

Look at how that formula works with my numbers: `(1.7 + 0.6) / 1.7 = about 1.4 sessions`. My median run time is 36 seconds, which is 0.6 minutes, and my median service time between a turn ending and my next prompt is 1.7 minutes. Past that, agents wait for me. That matches the 18% of waits over 10 minutes. More terminals with sub-minute turns just build a longer line waiting for me.

To run four sessions without a queue, each turn would need to run about three times my service time, around 5 minutes or more. Only about one turn in five does.

Even when the math allows parallel runs, human review capacity sets a hard ceiling. Simon Willison says he can review and land only one significant change at a time. He sends parallel agents only low-review work: research, "how does this work" questions, small maintenance, and work he specified in detail himself.

## Why factories already solved this

The urge to open another window comes from a feeling that an idle terminal is wasted. Factories learned to distrust that feeling long ago.

Taiichi Ohno at Toyota used two different rates. Operable rate: is the machine ready when needed. Target 100%. Operating rate: how much of the time it runs. It need not be 100%, because a machine kept busy for its own sake makes parts nobody ordered. Ohno called overproduction the worst waste. In a factory, extra parts pile up in bins, hide defects, and tie up people who have to move and count them. Keeping the AI busy is the same urge. Its overproduction is unreviewed PRs and half-built features.

Toyota also named the step that makes walking away possible. It called it "separating human work from machine work". Before that, an operator stood at a saw while it cut steel tube. A worker walks away from a machine only when it feeds itself, stops itself, and presents the finished part. Then one worker runs several machines on a short loop. Nobody stands watching a dishwasher. The agent version is the brief, the done check and one place where results wait.

Leaving a human to stare at an automated process is not just slow. Watching is the worst job. In Norman Mackworth's WWII radar-watch test, detection fell about 10% within 30 minutes, and later work found half of the loss comes in the first 15 minutes. Lisanne Bainbridge's "Ironies of Automation" (1983) adds that people who only monitor lose the skill they are meant to supervise. The less you touch the work directly, the harder it gets to step in when the machine gets stuck. Simkute and colleagues at Microsoft Research (2024) found the same with generative AI: the user moves from making work to checking it, and easy tasks get easier while hard tasks get harder.

## Verify it worked

Run the script again after a week of the new habit. Expect fewer sessions touched per day, and a lower share of agent waits over 10 minutes.

You can also see whether your autonomous tasks are working as intended. If the share of turns over 30 minutes grows, your long runs are getting safe to leave.

## Trade-offs

This way of working has real costs.

First, more of the AI sits idle. Ohno would call that correct, but it feels wasteful. An idle agent creates no review debt. A busy one on a half-baked prompt creates cleanup work for you.

Second, not every problem can be packaged into a long batch job. Design talk and debugging are dialogue. They cannot be made long, so for those hours staying in one session is right.

Third, long runs need a done check. Without one, background work drifts out of sight and you end up touring tabs again. Writing a reliable test or verification script before kicking off a prompt takes upfront effort, and sometimes setting up the check feels harder than doing the task interactively.

Finally, keep in mind what the log files can and cannot tell you. The script counts timestamps, not attention. A turn where you watched and a turn where you left look the same. Still, the numbers are the fastest way to see that most waits are short, extra sessions queue up fast, and your own focus is the part worth protecting.

## Sources

- [Atomic Object, 26 Things To Do While You're Waiting for Your Agent to Run](https://spin.atomicobject.com/agent-wait-26-things-to-do/)
- [Elixir Forum, What do you do while waiting for it (Claude Code)?](https://elixirforum.com/t/what-do-you-do-while-waiting-for-it-claude-code/75143)
- [Tao Bojlén, Just one more prompt](https://btao.org/posts/2026-03-18-one-more-prompt)
- [Unwait](https://www.indiehackers.com/product/unwait)
- [Mitchell Hashimoto, My AI Adoption Journey](https://mitchellh.com/writing/my-ai-adoption-journey)
- [Simon Willison, Embracing the parallel coding agent lifestyle](https://simonwillison.net/2025/Oct/5/parallel-coding-agents/)
- [Lean Enterprise Institute, Operation availability versus operating rate](https://www.lean.org/lexicon-terms/operation-availabilty-versus-operating-rate/)
- [Michael Ballé, What does separating human work from machine work mean?](https://www.lean.org/the-lean-post/articles/what-does-separating-human-work-from-machine-work-mean/)
- [Cornell, The early years of academic computing](https://cs.cornell.edu/wya/AcademicComputing/text/360clones.html)
- [Mackworth Clock](https://en.wikipedia.org/wiki/Mackworth_Clock)
- [Simkute et al., Ironies of Generative AI](https://arxiv.org/abs/2402.11364)
