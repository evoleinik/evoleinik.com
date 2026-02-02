---
title: "Serve Markdown to AI Agents (10x Smaller Payloads)"
date: 2026-02-02
tags: ["ai", "agents", "web", "markdown", "http"]
summary: "An entire infrastructure layer (CSS, JS, frameworks) is becoming optional for a growing class of consumers. Here's how to serve markdown via HTTP content negotiation."
---

Guillermo Rauch shared that Vercel's changelog now serves markdown when agents request it. Same URL, different `Accept` header.

The insight isn't the size reduction - it's that an entire infrastructure layer (CSS, JS, frameworks) is becoming optional for a growing class of consumers.

## How it works

HTTP content negotiation. Browsers send `Accept: text/html`. Agents can send `Accept: text/markdown`. Same URL, different representation.

I added this to my Hugo blog. The config:

```toml
[outputs]
page = ['HTML', 'MARKDOWN']

[outputFormats.MARKDOWN]
baseName = 'index'
mediaType = 'text/markdown'
isPlainText = true
```

The middleware (Vercel Edge):

```js
export const config = { matcher: ['/', '/posts/:path*'] }

export default async function middleware(request) {
  if (request.headers.get('accept')?.includes('text/markdown')) {
    const url = new URL(request.url)
    url.pathname = url.pathname.replace(/\/?$/, '/index.md')
    return fetch(url)
  }
}
```

Test it:

```bash
curl -H 'Accept: text/markdown' https://evoleinik.com/posts/markdown-for-agents/
```

My posts go from ~20kb HTML to ~2kb markdown. Not 250x like Vercel's changelog, but 10x adds up.

## The tradeoff

You maintain two output formats. For static sites like Hugo, this is trivial - markdown is the source anyway. For dynamic content or SPAs, it's harder. You'd need to generate markdown server-side or maintain parallel content.

## Why bother?

Agent traffic is growing. Lightweight, structured content gives agents cleaner context and burns fewer tokens.

The visual web was designed for human browsers. The agent web doesn't need the decoration.
