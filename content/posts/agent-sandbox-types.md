---
title: "AI Agent Sandbox Types for Codex and Claude Code"
date: 2026-11-20
draft: false
tags: [ai-agents, sandbox, codex, claude-code, bubblewrap, security]
summary: "Your coding agent can read every key on your disk. Turn on its built-in sandbox and jail networked jobs with bubblewrap. Most teams need no hosted VM."
---

If you run Codex or Claude Code on your own machine, you probably do not need a hosted microVM. Turn on the agent's built-in sandbox and block reads outside the project. Wrap any job that needs network in a bubblewrap jail that hides your home folder.

That covers the threat a small team actually has. An agent reads your keys and sends them out.

## Know which threat you are guarding against

Hosted sandbox vendors sell to companies that run strangers' code. Lovable's CTO says they run a million sandboxes every day. Each one holds code that a stranger asked an AI to write. That company needs a wall between users and a wall around its own servers.

A small team has a different problem. The code is yours and the agent is yours. The risk is text the agent reads. A scraped page, a GitHub issue or an email can carry hidden instructions. This is called prompt injection. The agent follows them, reads a key from disk and posts it somewhere.

So ask two questions of any wall. Can the agent read my secrets? Can it send them out?

## 1. No sandbox

The agent runs as your user. Every command it types has your rights. It can read SSH keys, cloud credentials, `.env` files and your browser profile. It can push to any repo you can push to.

This stops nothing. It suits a throwaway VM with no secrets on it, and nothing else.

## 2. Turn on the agent's built-in sandbox

Both major coding agents ship a sandbox enforced by the operating system.

Codex uses Seatbelt on macOS. On Linux it started with Landlock and seccomp. Newer versions use bubblewrap plus seccomp. The default `workspace-write` mode limits writes to the project folder and turns network off.

```bash
codex exec --sandbox workspace-write "run the test suite"
```

Claude Code's sandbox is off by default. Run `/sandbox` in a session to turn it on. It uses Seatbelt on macOS and bubblewrap on Linux. Network traffic goes through a proxy that checks a domain allowlist.

Here is the catch. Both tools let sandboxed commands read most of the disk by default. Claude Code's docs say the default "still allows reading credential files."

We measured Codex on 2026-08-06 with codex-cli 0.145.0. Plain `workspace-write` blocked DNS as promised.

```text
curl: (6) Could not resolve host
```

The disk stayed readable. A worker printed our secrets file and our production env file verbatim. With network off, that leak went nowhere. Turn network on for one job and the same read becomes a real leak. A network block only contains the agent while the network stays off.

Both tools can now deny reads. Codex has permission profiles with `deny` rules for paths and globs. Claude Code has one setting that hides home folders and mounted volumes.

```json
{
  "sandbox": { "enabled": true },
  "permissions": { "blockReadsOutsideWorkingDirectories": true }
}
```

This layer stops writes outside the project. It stops network while network is off. It misses reads until you set them. Everyone should use it as the first layer.

## 3. Run the agent as a separate Unix user

Make a user with no sudo and no copy of your keys. Give it only the repos it needs.

```bash
sudo useradd --create-home --shell /bin/bash agent
sudo -iu agent codex
```

Now the kernel stops the agent from reading your home folder. This wall is old and well tested.

The trap is shared files. Git reads settings from `.git/config` in every repo. If the agent can write that file, it can set `core.fsmonitor` to any command. The next time your main user runs `git status` in that repo, the command runs as you. We tested this, and it works.

So never run git as yourself in a tree the agent can write. Let the agent push a branch. Then fetch that branch into your own clone.

This wall stops reads of your home folder. It misses anything you share with the agent user, and it does not limit network. It suits a server where agents run all day.

## 4. Jail each job with a bubblewrap sandbox

bubblewrap, or `bwrap`, builds a small Linux namespace jail around one process. You list what the process can see. Everything else does not exist inside.

Our offline test jail mounts only `/usr`, a few `/etc` files and the worktree. Here is a trimmed version.

```bash
bwrap \
  --ro-bind /usr /usr \
  --symlink usr/bin /bin --symlink usr/lib /lib --symlink usr/lib64 /lib64 \
  --ro-bind /etc/ld.so.cache /etc/ld.so.cache \
  --ro-bind /etc/passwd /etc/passwd \
  --dev /dev --proc /proc --tmpfs /tmp \
  --unshare-net --unshare-pid --cap-drop ALL \
  --new-session --die-with-parent \
  --bind "$WORKTREE" "$WORKTREE" --chdir "$WORKTREE" \
  -- python -m pytest
```

Some workers need network. For those we bind the host read-only and keep the network. Then we lay an empty tmpfs over `$HOME` and over the main repo. The worktree goes back on top, writable.

```bash
bwrap --ro-bind / / --dev /dev --proc /proc --tmpfs /tmp \
  --tmpfs "$HOME" --tmpfs "$REPO" \
  --bind "$WORKTREE" "$WORKTREE" --chdir "$WORKTREE" \
  --unshare-pid --die-with-parent \
  -- codex exec --sandbox workspace-write "$TASK"
```

The same secret reads now fail with "No such file or directory". Everything else on the host is still readable, so keep secrets out of `/etc`, `/opt` and shared mounts, or hide those paths too. A curl to our public API still works. If `bwrap` is missing, the job refuses to start. A job that quietly runs without its jail is worse than a job that fails.

Watch the way out too. A jailed job cannot read your secrets. The trusted code that collects its results can. Say the job writes `result.json` as a symlink to a secrets file. Your collector opens it and reads the secret for the job. Refuse symlinks, and check the resolved path stays inside the run folder.

```python
p = run_dir / "result.json"
if p.is_symlink() or not p.resolve().is_relative_to(run_dir.resolve()):
    raise ValueError("result.json points outside the run folder")
```

This wall stops reads of anything you did not list. It stops network when you unshare it. It shares your kernel, so a kernel bug is a way out. It suits Linux machines running unattended agent jobs.

## 5. Run the AI agent sandbox in Docker

A container is the same idea with more tooling around it. Mount only the repo and drop the network.

```bash
docker run --rm -it --network none \
  --cap-drop ALL --security-opt no-new-privileges \
  -v "$PWD":/work -w /work my-agent-image codex
```

It works on macOS, where bubblewrap does not exist. It gives every teammate the same setup. The common mistake is mounting `~/.ssh` or the Docker socket "just for now". Access to the Docker socket is root on the host. Containers also share the host kernel.

This wall stops reads of anything you did not mount. It misses kernel escapes and careless mounts. It suits teams who already use dev containers.

## 6. Hosted microVM sandboxes like E2B, Modal and Vercel Sandbox

These give each sandbox its own kernel, or a fake one. Firecracker is a tiny virtual machine that boots in a fraction of a second. AWS built it to run Lambda. gVisor catches system calls in user space, so the code never talks to the host kernel directly.

E2B and Vercel Sandbox run each sandbox in a Firecracker microVM. Modal uses gVisor and also offers a full VM runtime. Daytona says each sandbox gets a dedicated kernel.

This is the right wall when strangers send you code. It isolates the kernel, which nothing above does. For your own agents it guards the wrong door. The agent still needs your repo inside the VM. It usually needs your API keys too. Once the keys are inside, prompt injection steals them just as easily. You also pay per second and ship your code to a third party.

This wall stops kernel escapes and one tenant reaching another. It misses keys you put inside. It suits products that run customer code.

## Do not trust read-only access

People give agents "read-only" access and relax. A read-only database login handed to a shell agent still reads every table the role can see. That includes customer emails and tokens. The agent can print them. With network on, it can send them.

Give the role only the tables the task needs. Better still, hand the agent an export with the sensitive columns removed.

## Verify it worked

Plant a fake secret in your home folder. Then ask the jailed job to read it.

```bash
echo "FAKE_KEY=canary123" > "$HOME/.canary"
bwrap --ro-bind / / --dev /dev --proc /proc --tmpfs "$HOME" \
  --unshare-net -- cat "$HOME/.canary"
```

Expected output:

```text
cat: /home/dev/.canary: No such file or directory
```

Run the same test through the agent's own sandbox. Ask it to `cat` the canary file. If it prints `canary123`, your reads are still open.

For a networked jail, check that real work still gets out.

```bash
bwrap --ro-bind / / --dev /dev --proc /proc --tmpfs "$HOME" \
  -- curl -sS -o /dev/null -w '%{http_code}\n' https://example.com
```

You should see `200`. Delete the canary file when you are done.

## Pick a sandbox type

| Type | Hides your keys | Blocks sending out | Shares host kernel | Suits |
|------|-----------------|--------------------|--------------------|-------|
| No sandbox | No | No | Yes | Throwaway VMs |
| Built-in sandbox, defaults | No | Only with network off | Yes | Nobody on its own |
| Built-in sandbox, reads blocked | Yes | Allowlist or off | Yes | Every laptop |
| Separate Unix user | Yes | No | Yes | Always-on servers |
| bubblewrap jail | Yes | Yes, when unshared | Yes | Unattended Linux jobs |
| Docker, careful mounts | Yes | Yes, with `--network none` | Yes | Dev-container teams |
| Hosted microVM | Only keys you leave out | Configurable | No | Running strangers' code |

## Trade-offs

bubblewrap is Linux only. On recent Ubuntu, AppArmor blocks the user namespaces it needs, so you add a small profile first. Tight jails also break tools. A missing `/etc/ssl` or `/etc/resolv.conf` looks like a network bug.

Every local option shares your kernel. If an attacker has a kernel exploit, these walls will not hold. For a small team that is a rare attack. Stolen keys through prompt injection are the common one.

Do not stop at local walls if you run code your users send. That is exactly what hosted microVMs are for. Pay for them.

## The plain recommendation

On a laptop, turn on the built-in sandbox and block reads outside the project. On a server, add a separate user with no sudo. Wrap every unattended job in bubblewrap, and refuse to run when bubblewrap is missing. Keep the network off unless a job needs it.

Treat whatever comes back from a jail as hostile, including its file names. Never run git as yourself in a tree the agent can write. Buy a hosted sandbox when strangers' code enters the picture, and not before.
