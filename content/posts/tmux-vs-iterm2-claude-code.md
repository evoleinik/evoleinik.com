---
title: "tmux vs iTerm2 for Claude Code: Use Both With tmux -CC"
date: 2026-11-15
draft: false
tags: [tmux, iterm2, claude-code, ssh, terminal, macos]
summary: "tmux vs iTerm2 is a false choice. iTerm2 is the Mac terminal and tmux keeps server sessions alive. Use both with tmux -CC and set it up for Claude Code."
---

tmux and iTerm2 are not alternatives. iTerm2 is the terminal app on your Mac. tmux runs on the server and keeps your sessions alive when SSH drops. Start tmux with `-CC` and iTerm2 shows each tmux window as a native tab, so you get both. For Claude Code, add four lines to `~/.tmux.conf` and keep the classic renderer.

My setup is a Mac laptop running iTerm2. It connects over SSH to a Linux dev server. Claude Code sessions run on that server inside tmux, usually through `tmux -CC`. Agent runs there can last for days.

## Connect with one command

```bash
ssh -t devbox 'tmux -CC new-session -A -s main'
```

`-A` attaches to the session called `main` if it exists. If it does not, tmux creates it. So one command covers the first connect and every reconnect. I keep it as an alias on the Mac:

```bash
# ~/.zshrc on the Mac
alias tdev="ssh devbox -t tmux -CC new-session -A -s main"
```

The [tmux control mode post](/posts/iterm2-tmux-control-mode/) explains this command and the iTerm2 profile in detail.

## tmux vs iTerm2 is a false choice

The two tools work at different layers. iTerm2 draws the screen on your Mac. tmux keeps programs running on the server.

tmux is a terminal multiplexer. It runs many terminal sessions inside one connection. When the connection drops, the sessions keep running, and you attach to them again later.

| | iTerm2 | tmux |
|---|---|---|
| Runs on | Your Mac | The machine where your programs run |
| Kind of tool | Terminal emulator | Terminal multiplexer |
| Keeps programs running after SSH drops | No | Yes |
| Scrollback | Native, with trackpad and Cmd+F | Copy mode, 2000 lines per window by default |
| Desktop notifications | Yes | Only by passing escape codes to the outer terminal |
| Split panes | Local to the Mac | On the server, kept after you disconnect |

The same logic covers Ghostty vs tmux. Ghostty is a terminal app, like iTerm2.

So the real question is where Claude Code runs:

- **Claude Code runs on your Mac.** Use iTerm2 alone. There is no SSH link to lose, so tmux adds little.
- **Claude Code runs on a server, and you work from a Mac.** Use `tmux -CC` in iTerm2. This is my default.
- **You attach from other machines too, or you want the fullscreen renderer.** Use plain tmux inside iTerm2, without `-CC`.

## tmux vs iTerm2 tabs and split panes

In plain tmux, every tmux window lives inside one iTerm2 tab. You switch windows with the tmux prefix key, `Ctrl+b` by default. An iTerm2 split that runs its own `ssh` loses its remote shell when the connection drops.

With `tmux -CC`, iTerm2 maps its own interface onto tmux. Splitting a pane in iTerm2 runs tmux's `split-window`. Closing a tab kills that tmux window. The Shell > tmux menu creates new tmux windows. So "iTerm2 split pane vs tmux" stops being a choice. The iTerm2 split is a tmux split, and it survives a dropped link.

iTerm2's documentation lists two limits that come from tmux itself:

- All tmux tabs have the same number of rows and columns. A tmux window is never larger than the smallest attached client.
- A tab that holds a tmux window cannot also hold a local split pane.

## Add four lines to ~/.tmux.conf

Claude Code's terminal docs give this tmux config. Put it on the server:

```bash
# ~/.tmux.conf on the server
set -g allow-passthrough on
set -g focus-events on
set -s extended-keys on
set -as terminal-features 'xterm*:extkeys'
```

Each line fixes one thing.

- `extended-keys` and the `terminal-features` line let tmux tell Shift+Enter apart from Enter. Without them, Shift+Enter submits your prompt instead of adding a new line.
- `allow-passthrough` lets Claude Code's notification escape codes reach iTerm2. With `on`, only a pane you can see sends them.
- `focus-events` tells Claude Code when you switch to and from its pane.

Without `focus-events`, Claude Code 2.1.318 prints this hint at startup inside tmux:

```text
tmux focus-events off · add 'set -g focus-events on' to ~/.tmux.conf and reattach for focus tracking
```

Reload the config into the running server:

```bash
tmux source-file ~/.tmux.conf
```

Then detach and attach again. tmux applies `focus-events` to a client only when it attaches. Restart Claude Code after that.

If Shift+Enter still submits, press Ctrl+J. It adds a new line in every terminal with no setup.

## Send Claude Code notifications to the Mac

Claude Code sends a notification when it finishes a task or waits on a permission prompt, and you seem to be away. Over SSH it has to be told which terminal you use. Set this on the server:

```json
{
  "preferredNotifChannel": "iterm2"
}
```

That goes in `~/.claude/settings.json` on the server.

Then turn on alerts in iTerm2 on the Mac:

1. Open Settings > Profiles > Terminal.
2. Check "Notification Center Alerts".
3. Click "Filter Alerts" and enable "Send escape sequence-generated alerts".

The `allow-passthrough on` line only passes alerts from a pane you can see. tmux also accepts `set -g allow-passthrough all`, which passes escape codes from hidden panes as well.

## Keep the classic renderer under tmux -CC

Claude Code has two renderers. The classic one prints into your terminal's normal scrollback. The fullscreen one draws on the alternate screen, the way vim does. It stops flicker and keeps memory flat in long conversations.

Fullscreen rendering does not work with `tmux -CC`. The Claude Code docs say the mouse wheel does nothing there, and double-click can corrupt the terminal state.

Claude Code picks the classic renderer in `-CC` mode on its own. One setting overrides that. If `CLAUDE_CODE_NO_FLICKER=1` is set, you get fullscreen anyway. I pin the classic renderer on the server so a stray setting can't flip it:

```bash
# ~/.zshrc on the server
export CLAUDE_CODE_NO_FLICKER=0
```

I added this after the fullscreen renderer kept my mouse wheel from reaching iTerm2's scrollback.

Check which renderer is active by typing `/tui` inside Claude Code:

```text
Current renderer: default. Usage: /tui <default|fullscreen>
```

`default` is the classic renderer.

One case ignores all of this. The docs say sessions opened from agent view or `claude attach` always render fullscreen. So avoid agent view and `claude attach` inside a `tmux -CC` tab.

## Fix Claude Code scrolling in tmux

With `tmux -CC` and the classic renderer, the conversation sits in iTerm2's scrollback. Trackpad scrolling and Cmd+F work as usual.

Plain tmux needs more setup. tmux keeps 2000 lines of history per window by default, and a long Claude Code session can pass that quickly. Raise the limit and turn on the mouse:

```bash
# ~/.tmux.conf on the server
set -g history-limit 50000
set -g mouse on
```

The new `history-limit` applies only to windows created after the change. Existing windows keep their old limit.

If you use the fullscreen renderer in plain tmux, `mouse on` is required. Without it, wheel events go to tmux instead of Claude Code. To search the conversation, press `Ctrl+o` for transcript mode. Then press `/` to search, or `[` to write the whole conversation into tmux's scrollback.

## Name each tab after its Claude Code session

With ten sessions open, every tab looks the same. Give each one a name inside Claude Code:

```text
/rename auth-refactor
```

Claude Code writes the session name into the terminal title. In my test on Claude Code 2.1.318, the tmux pane title changed from `✳ Claude Code` to `✳ auth-refactor`.

In `-CC` mode, iTerm2 treats that title as the session name. Plain tmux shows window names in its status bar, so I copy the pane title into the window name with a hook:

```bash
# ~/.tmux.conf on the server
set-hook -g pane-title-changed 'rename-window "#{pane_title}"'
```

After `/rename`, the window is called `✳ auth-refactor`. I also run tmux-resurrect, which saves window names, so the names come back after a reboot.

If the title never changes, check your environment for `CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1`. It turns off title updates. My first test showed nothing because another tool had set it.

## Keep the tmux socket out of /tmp

tmux keeps its socket in `/tmp/tmux-<uid>/` by default. If a cleanup job deletes that file, the tmux server keeps running, but no client can reach it:

```text
error connecting to /tmp/tmux-1000/default (No such file or directory)
```

This happened to me. I had set the server to delete files in `/tmp` older than three days. A five-day agent run stayed alive and unreachable for two days.

tmux can make a new socket without a restart. Send the server a USR1 signal:

```bash
mkdir -p -m 700 /tmp/tmux-$(id -u)
kill -USR1 $(pgrep -x 'tmux: server')
```

To prevent it, move the socket to `/run/user/<uid>`, which no `/tmp` cleanup touches:

```bash
# ~/.zshenv on the server
[ -d "/run/user/$(id -u)" ] && export TMUX_TMPDIR="/run/user/$(id -u)"
```

Use `~/.zshenv` if your login shell is zsh. `ssh devbox -t tmux ...` runs through a non-interactive shell, which reads `~/.zshenv` and skips `~/.zshrc`.

systemd deletes `/run/user/<uid>` at your final logout. Turn on lingering so it stays:

```bash
sudo loginctl enable-linger "$USER"
```

Make the change before you start the tmux server. A client with the new `TMUX_TMPDIR` cannot find a server that is still on `/tmp`.

## Run Claude Code agent teams in tmux panes

Agent teams are an experimental Claude Code feature that runs several sessions as one team. In split-pane mode each teammate gets its own pane. The docs say this needs tmux, or iTerm2 with the `it2` CLI. They also say `tmux -CC` in iTerm2 is the suggested way into tmux.

Enable it in `~/.claude/settings.json` on the server:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "teammateMode": "auto"
}
```

With `auto`, teammates open in split panes when Claude Code runs inside tmux. Under `-CC`, iTerm2 draws each tmux pane as a native split.

If a team leaves a tmux session behind, find it and close it:

```bash
tmux ls
tmux kill-session -t <session-name>
```

## Verify it worked

Run these inside a tmux pane on the server:

```bash
echo "$TMUX"
tmux show -g allow-passthrough
tmux show -g focus-events
tmux show -s extended-keys
tmux show -g history-limit
```

Expected output:

```text
/run/user/1000/tmux-1000/default,12345,0
allow-passthrough on
focus-events on
extended-keys on
history-limit 50000
```

The first line starts with `/run/user` once the socket has moved. The middle number is the server's process ID.

Then check Claude Code itself:

1. Type `/tui`. It should print `Current renderer: default`.
2. Type a line, press Shift+Enter, and type another. Both lines stay in the prompt and nothing is sent. If it sends instead, use Ctrl+J.
3. Run `/rename test`. The tab or tmux window shows `✳ test`.
4. Quit iTerm2, open it, and run `tdev`. Your tabs come back with Claude Code still running.

## Trade-offs

tmux does not survive a server reboot. tmux-resurrect and tmux-continuum save the layout every 15 minutes in my config and restore it at start. By default, tmux-resurrect restarts only a short list of programs, such as vim, less and htop. Claude Code is not on it. After a reboot, run `claude --resume auth-refactor` in each pane, using the names from `/rename`. `claude --continue` opens the most recent conversation in the current directory.

`tmux -CC` costs you the fullscreen renderer. You give up flicker-free drawing and flat memory use in long sessions.

tmux itself has a cost too. tmux releases through 3.6 lack synchronized output, so the Claude Code docs warn of more flicker than in a bare terminal.

`-CC` is a less common path, and some bugs show up only there. One Claude Code issue reported that iTerm2's Cmd+Left key mapping typed a literal `0x1` into the prompt under `tmux -CC` ([#50995](https://github.com/anthropics/claude-code/issues/50995)).

All `-CC` tabs share one size. If two Macs attach at once, the smaller screen sets the size for both.

tmux keeps a session alive but cannot speed up a bad link. If sessions freeze while the server looks healthy, check the TCP connection. My [SSH link and TCP BBR post](/posts/ssh-link-tcp-bbr-claude-code/) covers that case. If your IP address changes often, the iTerm2 wiki suggests Eternal Terminal. It also says not to use mosh with tmux integration.

If Claude Code runs on your Mac, skip tmux and use iTerm2 alone.
