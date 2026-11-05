---
title: "Why My Remote Claude Code Sessions Froze: A 45 KB/s SSH Link and TCP BBR"
date: 2026-11-05
draft: false
tags: [linux, tcp, bbr, ssh, claude-code, tailscale, networking]
summary: "Nine remote Claude Code sessions froze because 7% packet loss on a 105 ms link shrank cubic TCP to a 4-packet window and 45 KB/s. Switching the Linux server to BBR raised test speed 15 times to 508 KB/s and pushed live delivery rate to 7.0 Mbit/s."
---

My remote Claude Code sessions stopped answering even though the server had plenty of free resources. A single TCP connection carried all nine sessions over a long-distance link with 7% packet loss. The default Linux cubic congestion control shrank that pipe to about 45 KB/s. Switching the server to TCP BBR raised transfer speed 15 times and fixed the freezes.

## The setup and the symptoms

All nine Claude Code sessions shared one SSH connection.

I run the Claude desktop app on a Mac. The app runs Claude Code sessions on a Linux server I call box. The connection uses SSH on top of Tailscale and WireGuard. The link is long-distance with a 105 ms round trip. I had about nine sessions open at once.

All of those sessions share one SSH connection. On box, a small bridge process runs on that SSH connection. The bridge talks to a long-running app server through a Unix socket. The Claude Code processes are children of that app server. They do not belong to the SSH connection itself. This design allowed the sessions to survive when I restarted the desktop app later.

Then the sessions stopped responding. I opened a new session and watched it sit for minutes. It stayed on the message about setting up the environment and copying files. After a while the desktop app reported that there was still no answer from box.

Running sessions also broke. Inside a running session, the tool hooks built into the app timed out four times. Each timeout said that the host client may be unreachable. At the same time, the `df` command hung on box.

## The server was fine

Every health check on box came back clean. The CPU, memory, disk and local tools were all fast.

I checked the machine metrics first to see if box was overloaded. Everything looked normal. Every check pointed away from a local resource bottleneck:

| Check | Result |
|---|---|
| Load | 1.8 on 20 cores. The 15-minute average was 9.7 from an earlier burst |
| RAM | 51 GB available of 62 GB |
| Swap | 8.8 GB used with 0 swap-in and 0 swap-out |
| Pressure stall info in /proc/pressure | CPU, memory and IO all at 0 |
| Processes stuck in D state | None |
| git status and git worktree list | 0.06 s and 0.05 s |
| Interactive shell startup | 0.09 s |
| DNS and the Anthropic API | DNS took 0.01 to 0.04 s and the API answered in 0.29 s |
| Session hooks and status line script | Each ran in under 0.1 s |

The machine itself was healthy.

## Why df hung on a Google Drive mount

The `df` hang was a separate issue caused by Google Drive API rate limits on a FUSE mount.

When you run `df`, it calls `statfs` on every mounted file system. One mount on box connects to Google Drive through `rclone mount` using FUSE. Another FUSE mount was also present on the system.

To answer a `statfs` call, rclone asks the Google Drive API for account quota information through the About endpoint. The Drive API was rate-limiting the account. The rclone log showed the `RATE_LIMIT_EXCEEDED` error.

A single `stat -f` call on that rclone mount took 34 s to finish. Even running `timeout -s KILL 8` did not stop the command after 8 s. The process sat inside the kernel waiting for the FUSE daemon to answer. A `KILL` signal cannot interrupt that kernel wait until the daemon replies. Meanwhile, the other FUSE mount answered at once.

A cron job on box runs `rclone sync` to the same Google account every 15 minutes. That sync job likely uses the same API quota.

You can avoid the hang by telling `df` to skip the FUSE file systems:

```
df -h -x fuse.rclone -x fuse.mcp
```

## A recent app update added traffic

An app update rewrote hundreds of plugin files over the slow SSH link right before the freeze.

Just before the sessions stalled, the desktop app installed a new Claude Code version on box. Over about 3 minutes, it rewrote about 950 plugin files in its remote folder. The full plugin folder holds 5,675 files and takes 91 MB.

Later session starts copied only 36 files, and then only 2 files. So the large file copy was a one-off event from the update. It took minutes because all file transfers share the single SSH link.

## The SSH connection had collapsed

Packet loss on the long path crushed the TCP congestion window and reduced the SSH pipe to about 45 KB/s.

I inspected the single SSH connection carrying all the sessions with `ss -tni`. The socket stats showed why the app could not get data through:

```
rtt:105.271 cwnd:4 ssthresh:2 mss:1228 pmtu:1280
bytes_sent:56555831 bytes_retrans:3927444
delivery_rate 278808bps   Send-Q 47892
```

The connection had sent 56,555,831 bytes and resent 3,927,444 bytes. So 3.9 MB out of 56 MB had to be resent. That is about 7% of the data. The congestion window was down to 4 packets. The slow-start threshold was 2. Another 47,892 bytes sat waiting in the send queue.

Box was using cubic, which is the Linux default TCP congestion control algorithm. Cubic treats every lost packet as a sign of a full queue and cuts its congestion window.

The rough math explains the slowdown. A window of 4 packets at 1,228 bytes per packet over a 105 ms round trip gives about 47 KB/s. The classic loss formula for Reno-style TCP multiplies MSS divided by RTT by 1.22 divided by the square root of the loss rate. At 7% loss, that formula predicts about 54 KB/s. The measured speed on the link was 35 to 47 KB/s.

All nine Claude Code sessions stream their output back to the desktop app through that single 45 KB/s pipe. Requests from the app queue behind that output. The queue backs up, the app hooks time out, and the app says box is not answering.

The packet loss was happening somewhere along the long network path rather than on box. Box showed zero UDP buffer errors. The `tailscale0` interface showed zero drops. The physical network card had zero errors.

A regular ping test missed the problem completely. Running `ping` showed 0% loss across 20 packets. ICMP ping traffic is too light to reveal this kind of loss. The TCP resend counters in `ss -tni` caught it right away.

The direction that mattered was box to the Mac, because box sends the heavy session output. In TCP, the sender chooses the congestion control algorithm. Changing the setting on box alone was enough to fix the pipe.

## Switching to BBR raised speed 15 times

Enabling TCP BBR on box raised transfer speed from 34 KB/s to 508 KB/s on a test file and restored all sessions.

BBR works differently from cubic. It models the bottleneck bandwidth and the round-trip time of the path. It does not treat every random lost packet as a reason to cut the sending window.

At first, the kernel on box offered only `reno` and `cubic`. I loaded the BBR kernel module and switched the active algorithm with two commands:

```
sudo modprobe tcp_bbr
sudo sysctl -w net.ipv4.tcp_congestion_control=bbr
```

The default queuing discipline on box stayed `fq_codel`. Recent Linux kernels let BBR pace packets on its own without changing the queuing discipline.

I ran a test to compare both settings. The test sent 2 MB of random data from box to the Mac over a fresh SSH connection:

```
head -c 2M /dev/urandom | ssh air 'cat >/dev/null'
```

The difference was immediate:

| Setting | Time | Speed |
|---|---|---|
| cubic | 60.4 s | 34 KB/s |
| bbr | 4.0 s | 508 KB/s |

BBR was 15 times faster. Those 4.0 s also included the time needed for the SSH handshake.

A sysctl change only applies to new TCP connections. The existing SSH pipe from the desktop app was still stuck on cubic. I restarted the desktop app on the Mac so it would open a new SSH connection. Because the Claude Code processes on box belong to the long-running app server, all nine sessions kept running without interruption.

I checked the new SSH connection with `ss -tni`. It was using BBR. Its delivery rate reached 7.0 Mbit/s, up from 0.37 Mbit/s before, which is about 19 times faster. Its congestion window grew to 1,621 packets. It sent 12.3 MB in its first 20 seconds or so.

About 5% of the bytes were still being resent. The packet loss on the long path did not go away. BBR simply stopped collapsing the window in response to that loss. Inside the sessions, the app hooks answered again right away.

## Making the BBR change permanent

Two small config files keep BBR active across boots, with a couple of caveats to keep in mind.

To load the module and set the sysctl at boot, I wrote two files:

```
# /etc/modules-load.d/bbr.conf
tcp_bbr
# /etc/sysctl.d/90-bbr.conf
net.ipv4.tcp_congestion_control = bbr
```

Undoing the change is simple. You delete both files and set the sysctl back to `cubic`.

There are a few caveats. Mainline Linux kernels ship BBR version 1. BBRv1 can take more than its fair share of bandwidth when it competes with cubic flows on a shared bottleneck. For one person connecting to their own server, that fairness issue does not matter. Also, I have not tested a full reboot of box yet.

## Lessons from the outage

Transport metrics explain remote freezes that host metrics and ping tests miss.

First, when a remote tool says the host is unreachable, check the transport layer before blaming the host. Running `ss -tni` shows the round-trip time, the congestion window, and the byte resend counters for a single TCP connection.

Second, a clean ping test does not prove that a network link is clean. Twenty ICMP packets can pass with 0% loss while a busy TCP stream loses 7% of its data.

Third, a file system command that hangs may actually be waiting on a remote network API behind a FUSE mount. Skipping FUSE mounts keeps `df` fast when cloud APIs apply rate limits.

Fourth, on a long path with packet loss, the default cubic algorithm can turn a fast connection into a 45 KB/s trickle. One sysctl command fixed it.
