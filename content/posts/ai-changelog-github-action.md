---
title: "Building an AI-Powered Changelog GitHub Action"
date: 2025-12-22
tags: [github-actions, ai, open-source, devops]
summary: "How a 87-line inline script became a reusable GitHub Action for AI-generated changelog summaries posted to Slack."
---

I wanted daily changelog summaries posted to Slack for my project. The existing solutions were either too complex (full-blown release management) or too dumb (just listing commits). I needed something that would read commits and produce a human-readable summary of what actually shipped.

So I built one. Then I open-sourced it: [evoleinik/changelog-summary](https://github.com/marketplace/actions/changelog-summary).

## The Problem

Raw commit logs are noisy. Even with good commit messages, a list of 15 commits doesn't tell a busy founder or stakeholder what actually changed. You want something like:

> - Shipped multi-provider dashboard with real-time sync
> - Fixed authentication bug causing logout loops
> - Improved search performance by 3x

Not:

> - fix: handle null case in auth middleware
> - refactor: extract dashboard component
> - feat: add provider selector to dropdown
> - fix: remove console.log
> - ...

LLMs are good at this. They can read commit messages (including the body, not just the subject line) and synthesize what matters.

## From Inline Script to Reusable Action

My first implementation was 87 lines of bash embedded directly in my GitHub Actions workflow file. It worked, but the workflow file became unreadable.

The extraction took about an hour. The result:

```yaml
- uses: evoleinik/changelog-summary@v1
  with:
    slack-webhook: ${{ secrets.SLACK_WEBHOOK_URL }}
    llm-provider: gemini
    llm-api-key: ${{ secrets.GEMINI_API_KEY }}
    voice: founder
```

24 lines instead of 87, and now any project can use it.

## Implementation Details

The action is a composite action (pure bash, no Node.js runtime). This matters because:

1. **No build step** - the script runs directly
2. **Easier to audit** - it's just bash you can read
3. **Faster startup** - no npm install

### Reading Full Commit Messages

Most changelog tools only read commit subjects. But the body often contains the real context:

```bash
COMMITS=$(git log --since="$SINCE" --pretty=format:"- %s%n%b" --no-merges)
```

The `%b` gives you the commit body. This means the LLM can see:

```
- feat: add multi-provider support

Added support for Gemini, OpenAI, and Anthropic.
Users can now switch providers without code changes.
Breaking: removed deprecated single-provider config.
```

Instead of just "feat: add multi-provider support".

### Voice Styles

Different audiences need different summaries. I implemented three:

**founder** - Direct, no-BS. What shipped? Skip the implementation details.

```
Be direct - what actually shipped? No fluff, no 'exciting updates' BS.
```

**developer** - Technical focus. APIs, breaking changes, specific files changed.

**marketing** - User-facing improvements. New capabilities, not bug fixes.

The prompt engineering is straightforward:

```bash
case "$VOICE" in
  founder)
    PROMPT="Summarize these commits for a busy founder. Be direct - what actually shipped? Rules: 3-5 bullets, no fluff..."
    ;;
  developer)
    PROMPT="Summarize these commits for developers. Focus on technical changes: APIs, breaking changes..."
    ;;
esac
```

### Slack Formatting Gotcha

Slack uses single asterisks for bold (`*text*`), not double (`**text**`). This took a few iterations to get right in the prompt:

```
Use Slack formatting: * for bullets, surround key terms with single asterisks for bold.
```

### Multi-Provider Support

I defaulted to Gemini because it's free tier is generous and the quality is good. But the action supports OpenAI and Anthropic too:

```bash
case "$LLM_PROVIDER" in
  gemini)
    curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key=$LLM_API_KEY" ...
    ;;
  openai)
    curl "https://api.openai.com/v1/chat/completions" -H "Authorization: Bearer $LLM_API_KEY" ...
    ;;
  anthropic)
    curl "https://api.anthropic.com/v1/messages" -H "x-api-key: $LLM_API_KEY" ...
    ;;
esac
```

Each provider has slightly different JSON structures, but `jq` handles the response parsing cleanly.

## Trade-offs

**No streaming** - The action waits for the full LLM response. For changelog summaries (typically under 200 tokens), this is fine. For longer documents, you'd want streaming.

**Single Slack message** - No threading, no reactions. Just a message. I could add richer Slack blocks, but the simple text format works and is easier to maintain.

**No commit filtering** - Every commit in the time range gets included. If you need to filter by path or author, you'd need to modify the `git log` command. I may add this as an option if there's demand.

**Bash-based** - This limits what you can do. A TypeScript action would be more extensible. But bash means zero dependencies and sub-second startup. For a simple utility, that's the right trade-off.

## Usage Examples

### Daily Summary

```yaml
on:
  schedule:
    - cron: '0 13 * * *'  # 1 PM UTC daily

jobs:
  summary:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Need full git history

      - uses: evoleinik/changelog-summary@v1
        with:
          slack-webhook: ${{ secrets.SLACK_WEBHOOK_URL }}
          llm-provider: gemini
          llm-api-key: ${{ secrets.GEMINI_API_KEY }}
```

### Weekly Summary with Custom Header

```yaml
on:
  schedule:
    - cron: '0 13 * * 0'  # Sundays

jobs:
  summary:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: evoleinik/changelog-summary@v1
        with:
          slack-webhook: ${{ secrets.SLACK_WEBHOOK_URL }}
          llm-provider: gemini
          llm-api-key: ${{ secrets.GEMINI_API_KEY }}
          since: '7 days ago'
          header: 'Weekly Update'
          voice: marketing
```

## What Makes Good Open Source

This started as a script to solve my own problem. A few observations from the extraction process:

1. **Solve your problem first** - I used this for weeks before open-sourcing. The edge cases were already handled.

2. **Keep it focused** - This does one thing: summarize commits and post to Slack. It doesn't manage releases, create tags, or update changelogs files.

3. **Provide sensible defaults** - Gemini as the default provider, "founder" voice, 24-hour window. You can override everything, but the defaults work out of the box.

4. **Document the trade-offs** - Be clear about what it doesn't do.

## Conclusion

- Small, focused utilities that solve your own problem first often make good open source
- Composite actions (bash) are underrated - no build step, easy to audit, fast
- Read full commit messages (`--pretty=format:"%s%n%b"`) for better AI context
- Voice/persona prompts let you tune the output for different audiences without changing the code
- Slack uses single asterisks for bold - check your target platform's formatting

The action is on [GitHub Marketplace](https://github.com/marketplace/actions/changelog-summary). MIT licensed. PRs welcome.

---

**Related:** [Adding LLM Polish to a Speech-to-Text App](/posts/adding-llm-polish-to-speech-to-text/) - More LLM integration patterns for user-facing tools.
