---
title: "Debugging Random Reboots with Claude Code: A PSU Power Limit Story"
date: 2025-12-22
tags: [linux, hardware, debugging, claude-code, ai-assisted-development]
summary: "How I used Claude Code to diagnose random system reboots caused by PSU power limits - and why AI assistants excel at systematic hardware debugging."
---

My Linux server started rebooting randomly during CPU benchmarks. I had no idea where to start, so I asked Claude Code to help diagnose. Twenty minutes later, we found the root cause and a working fix.

This is a story about AI-assisted debugging - specifically, how an AI assistant's systematic approach can cut through hardware issues that would take hours of Googling.

## The Problem

I was benchmarking local Whisper models for speech-to-text on a home server (Intel i9-10900K, 550W PSU). During heavy transcription loads, the system would randomly reboot. No warning, no error message - just instant power loss.

I described the symptoms to Claude Code: "Server reboots randomly under CPU load. No kernel panic. What should I check?"

## The AI-Guided Diagnosis

Claude Code walked me through a systematic diagnostic process. Each step built on the previous one.

### Step 1: Check the Logs

```bash
journalctl -b -1
```

Claude noted that the logs stopped abruptly mid-operation. No error, no shutdown sequence. "This is actually diagnostic," it explained. "Software crashes leave traces. Instant power loss doesn't."

### Step 2: Look for Hardware Errors

```bash
dmesg | grep -i error
```

Found Machine Check Errors (MCE). Claude explained these indicate hardware-level problems: thermal, memory, or power delivery.

### Step 3: Rule Out Thermal

```bash
apt install lm-sensors
sensors
```

Temps showed 39-51C under load. Well within spec. Claude crossed thermal off the list.

### Step 4: Check MCE Details

```bash
apt install rasdaemon
ras-mc-ctl --errors
```

No active errors. The MCE messages were stale.

### Step 5: The Diagnosis

Based on the evidence - logs stopping without kernel panic, load-dependent crashes, normal temps - Claude identified the likely cause: **PSU power limits**.

It asked about my PSU (550W) and looked up the i9-10900K specs. Under Turbo Boost with all cores loaded, this CPU can spike to 250W+. My PSU was undersized.

## The Fix Attempts

Claude suggested Intel RAPL to limit CPU power draw:

```bash
# Set PL1=125W, PL2=180W
echo 125000000 > /sys/class/powercap/intel-rapl/intel-rapl:0/constraint_0_power_limit_uw
echo 180000000 > /sys/class/powercap/intel-rapl/intel-rapl:0/constraint_1_power_limit_uw
```

Still crashed.

Tried lower limits (95W/125W). Still crashed.

Claude explained why: "RAPL operates on millisecond timescales. Your PSU's overcurrent protection trips in microseconds. The PSU cuts power before RAPL can throttle."

Software can't fix hardware that fails faster than software can react.

## The Working Fix

Claude's solution: disable Turbo Boost entirely to prevent power spikes.

```bash
echo 1 > /sys/devices/system/cpu/intel_pstate/no_turbo
```

System became stable. Claude then wrote a systemd service to make it persistent:

```ini
# /etc/systemd/system/disable-turbo.service
[Unit]
Description=Disable CPU Turbo Boost
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c "echo 1 > /sys/devices/system/cpu/intel_pstate/no_turbo"
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable disable-turbo.service
```

## Why AI-Assisted Debugging Worked

I could have Googled "random Linux reboots" and spent hours reading forum posts about kernel bugs, driver issues, and memory problems. Instead, Claude Code:

1. **Asked the right questions** - immediately focused on whether logs showed clean shutdown vs. power cut
2. **Followed a systematic process** - ruled out causes one by one instead of jumping to conclusions
3. **Knew the domain** - understood MCE errors, RAPL timing, PSU OCP behavior
4. **Explained the "why"** - didn't just give commands, but explained why RAPL couldn't work

The debugging took about 20 minutes of back-and-forth. Most of that was waiting for package installs and running tests.

## The Trade-offs

With Turbo disabled, the i9-10900K runs at 3.7GHz base instead of boosting to 5.3GHz. About 30% slower for my benchmarks.

The proper fix is a 750W+ PSU. But for now, disabling Turbo keeps the server stable.

For the Whisper benchmarks: local inference was 10-20x slower than cloud APIs (Groq) even with Turbo. The conclusion held - use cloud for production.

## Key Takeaways

- **Random reboots without kernel panic = power issue**, not software. Logs stopping abruptly is the tell.
- **Intel CPUs lie about power** - the i9-10900K's 125W "TDP" can spike to 250W+ under Turbo
- **RAPL can't save you from PSU trips** - hardware protection is faster than software throttling
- **AI assistants excel at systematic debugging** - they don't get distracted by red herrings or skip steps
- **The fix isn't always hardware** - disabling Turbo is a valid workaround when PSU upgrade isn't immediate

Next time you hit a weird hardware issue, try describing it to Claude Code. The systematic approach might save you hours of forum diving.

---

**Related:** [CLAUDE.md: Building Persistent Memory for AI Coding Agents](/posts/claude-md-as-agent-memory/) - Make Claude Code remember your project's quirks between sessions.
