---
title: "Speed Up Syncthing File Sync Discovery (From 11 Seconds to 2)"
date: 2025-12-16
tags: [syncthing, performance, devtools]
summary: "Reduce Syncthing's file detection delay from 10+ seconds to under 3 by tuning fsWatcherDelayS on the sending machine."
---

New files were taking 11 seconds to sync from my Linux box to my Mac. That's an eternity when you're iterating on code or config. The fix took 30 seconds.

## The Problem

Syncthing uses filesystem watchers to detect changes. When a file changes, the watcher notices, Syncthing scans it, and sync begins. But there's a built-in delay before Syncthing acts on watcher events.

The default `fsWatcherDelayS` is 10 seconds. This batches multiple rapid changes into one scan, which makes sense for large codebases. But for small, frequent syncs, it's pure latency.

## The Fix

Set `fsWatcherDelayS="1"` on the **sending** machine. The receiver's setting doesn't matter for detection speed.

Find your config file:

- **Linux**: `~/.local/state/syncthing/config.xml` or `~/.config/syncthing/config.xml`
- **macOS**: `~/Library/Application Support/Syncthing/config.xml`

Find your folder element and change the delay:

```xml
<folder id="your-folder-id" label="Sync" path="/path/to/folder" ...>
    <!-- Change this from 10 to 1 -->
    <fsWatcherDelayS>1</fsWatcherDelayS>
    ...
</folder>
```

Restart Syncthing after editing.

## Benchmarks

I measured round-trip detection time: create a file, poll for its appearance on the other machine, record the elapsed time.

```bash
# On sender
echo "test" > ~/Sync/test-$(date +%s).txt

# On receiver (running in loop)
while [ ! -f ~/Sync/test-*.txt ]; do sleep 0.1; done
```

**Before** (default `fsWatcherDelayS=10` on Linux):

| Direction | Time |
|-----------|------|
| Linux to Mac | 11.4s |
| Mac to Linux | 1.7s |

Mac already had the delay set to 1 from earlier tinkering, which explains the asymmetry.

**After** (both set to `fsWatcherDelayS=1`):

| Direction | Time |
|-----------|------|
| Linux to Mac | 2.6s |
| Mac to Linux | 1.8s |

That's a 4x improvement on the slow path.

## Why the Asymmetry?

Linux uses inotify, which is fast and efficient. macOS uses FSEvents, which has higher latency. Even with identical settings, Mac detection will be slightly slower.

The remaining ~2 seconds includes:

- Filesystem watcher delay (1 second)
- Syncthing's internal scan
- Network round-trip for sync protocol
- File write on receiver

## Other Tuning Options

If you're still hungry for speed:

- **`pullerMaxPendingKiB`**: Increase for better throughput on large files (default 128 KiB is conservative)
- **`disableFsync`**: Skip fsync on writes for faster file creation. Risky if power fails mid-sync.
- **Syncthing 2.0**: Uses SQLite instead of flat files for the index database, plus multiple connections per device. Worth upgrading if you haven't.

## Trade-offs

Setting `fsWatcherDelayS=1` means more frequent scans. On a folder with thousands of rapid changes (like a build directory), this could increase CPU usage. For typical sync folders with occasional changes, the overhead is negligible.

## Takeaways

- The **sending** machine's `fsWatcherDelayS` controls detection speed
- Default of 10 seconds is conservative; 1 second works fine for most use cases
- Linux inotify is faster than macOS FSEvents
- Edit config.xml directly, restart Syncthing
