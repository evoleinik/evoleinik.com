#!/usr/bin/env python3
"""Ask ChatGPT and Gemini the searches this blog ranks for, and log whether they cite evoleinik.com.

  scripts/ai-citations.py                 top 20 posts' best Google query, both engines, append to the log
  scripts/ai-citations.py --query "tmux cc" --no-log     one ad-hoc query, log nothing
  scripts/ai-citations.py --last          print the latest logged run in one line (site-traffic-report)

Queries: from Search Console, the highest-impression query of each page, for the N pages with the
most impressions over --days. One query per post, so a run covers posts, not 20 spellings of tmux.
Queries under --min-impressions are dropped: at 1 or 2 impressions they are noise such as
"but they are related", and no engine would cite anyone for them.
Engines: ChatGPT = OpenAI gpt-4.1 with web_search through OpenRouter, provider pinned to OpenAI.
Gemini = gemini-3.8-flash with Google Search grounding on Vertex, in the gcloud default project.
Roughly $1-2 a run.
Keys: OPENROUTER_API_KEY from the environment, ~/.secrets, or the env file named by
AI_CITATIONS_ENV_FILE. Gemini uses `gcloud auth print-access-token`.
"Cited" = a source URL or title on evoleinik.com. "Own" = a source URL on one of his profiles or
copies (dev.to, GitHub). "Named" = the answer text says evoleinik or Eugene Oleinik. Only source domains are stored, never answer text.

Log: ~/Sync/site-reports/ai-citations.jsonl, one JSON object per run. --json prints that object.
Exit 0 ok, 1 every engine call failed, 2 no queries (Search Console failed or empty).
"""
import argparse, concurrent.futures, datetime, json, os, re, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

SITE, DOMAIN = "sc-domain:evoleinik.com", "evoleinik.com"
LOG = Path.home() / "Sync/site-reports/ai-citations.jsonl"
GWSP = Path.home() / "bin/gwsp"
GEMINI_MODEL, CHATGPT_MODEL = "gemini-3.8-flash", "openai/gpt-4.1"
NAME = re.compile(r"evoleinik|eugene oleinik", re.I)
# Eugene's own copies and profiles elsewhere. Only engines that return real URLs (ChatGPT) can match.
OWN = re.compile(r"dev\.to/evoleinik|github\.com/evoleinik|linkedin\.com/in/evoleinik|x\.com/eugeneoleinik|t\.me/eo_builds", re.I)


def env_key(name):
    """Environment first, then ~/.secrets, then $AI_CITATIONS_ENV_FILE. Never printed."""
    if os.environ.get(name):
        return os.environ[name]
    for path in (Path.home() / ".secrets", Path(os.environ.get("AI_CITATIONS_ENV_FILE", "/nonexistent"))):
        if path.is_file():
            out = subprocess.run(["bash", "-c", f'set -a; source "{path}" >/dev/null 2>&1; printf %s "${{{name}:-}}"'],
                                 capture_output=True, text=True).stdout
            if out:
                return out
    raise RuntimeError(f"{name} not in env, ~/.secrets or $AI_CITATIONS_ENV_FILE")


def post_json(url, body, headers, timeout):
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json", **headers})
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if attempt == 1 and e.code in (429, 500, 502, 503, 504):
                time.sleep(10)
                continue
            raise RuntimeError(f"HTTP {e.code}: {e.read()[:200].decode(errors='replace')}") from None


def domain(url_or_title):
    text = url_or_title.strip().lower()
    host = urllib.parse.urlparse(text).hostname if "://" in text else text.split("/")[0]
    return (host or "").removeprefix("www.")


def chatgpt(query, timeout):
    body = {"model": CHATGPT_MODEL, "input": query, "tools": [{"type": "web_search", "search_context_size": "medium"}],
            "tool_choice": "required", "provider": {"order": ["openai"], "allow_fallbacks": False}}
    r = post_json("https://openrouter.ai/api/v1/responses", body,
                  {"Authorization": "Bearer " + env_key("OPENROUTER_API_KEY")}, timeout)
    text, sources = "", []
    for item in r.get("output") or []:
        for part in item.get("content") or [] if item.get("type") == "message" else []:
            text += part.get("text") or ""
            sources += [a["url"] for a in part.get("annotations") or [] if a.get("type") == "url_citation"]
    return text, [(s, "") for s in sources]


_gcloud = {}


def gcloud(*args):
    if args not in _gcloud:
        _gcloud[args] = subprocess.run(["gcloud", *args], capture_output=True, text=True, check=True).stdout.strip()
    return _gcloud[args]


def gemini(query, timeout):
    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or gcloud("config", "get-value", "project")
    url = (f"https://aiplatform.googleapis.com/v1/projects/{project}/locations/global/publishers/google/"
           f"models/{GEMINI_MODEL}:generateContent")
    body = {"contents": [{"role": "user", "parts": [{"text": query}]}], "tools": [{"googleSearch": {}}]}
    r = post_json(url, body, {"Authorization": "Bearer " + gcloud("auth", "print-access-token")}, timeout)
    cand = (r.get("candidates") or [{}])[0]
    text = "".join(p.get("text") or "" for p in (cand.get("content") or {}).get("parts") or [])
    chunks = [c.get("web") or {} for c in (cand.get("groundingMetadata") or {}).get("groundingChunks") or []]
    # Vertex hands back redirect URIs, so the real site is in title or domain.
    return text, [(c.get("uri") or "", c.get("domain") or c.get("title") or "") for c in chunks]


ENGINES = {"chatgpt": chatgpt, "gemini": gemini}


def top_queries(n, days, min_impressions):
    out = subprocess.run([str(GWSP), "searchconsole", "query", SITE, "--days", str(days), "--by", "query,page",
                          "--limit", "1000"], capture_output=True, text=True, timeout=120)
    rows = json.loads(out.stdout or "{}").get("rows") if out.returncode == 0 else None
    if rows is None:
        raise RuntimeError((out.stdout + out.stderr).strip()[:300])
    best = {}
    for row in rows:
        query, page = row["keys"]
        if page not in best or row["impressions"] > best[page]["impressions"]:
            best[page] = {"query": query, "page": page, "impressions": row["impressions"]}
    pages = sorted((b for b in best.values() if b["impressions"] >= min_impressions), key=lambda b: -b["impressions"])
    return [{**p, "page_impressions": sum(r["impressions"] for r in rows if r["keys"][1] == p["page"])}
            for p in pages][:n]


def ask(engine, item, timeout):
    started = time.time()
    try:
        text, sources = ENGINES[engine](item["query"], timeout)
        domains = [domain(title) if title else domain(url) for url, title in sources]
        cited = [i + 1 for i, d in enumerate(domains) if d == DOMAIN or d.endswith("." + DOMAIN)]
        own = sorted({url for url, _ in sources if OWN.search(url)})
        return {"engine": engine, "query": item["query"], "page": item.get("page"), "ok": True,
                "cited": bool(cited), "cited_rank": cited[0] if cited else None, "named": bool(NAME.search(text)), "own": own,
                "sources": domains[:10], "answer_chars": len(text), "ms": int((time.time() - started) * 1000)}
    except Exception as e:  # one failed call must not sink the run
        return {"engine": engine, "query": item["query"], "page": item.get("page"), "ok": False,
                "error": str(e)[:300], "ms": int((time.time() - started) * 1000)}


def summary(run):
    parts = []
    for engine in run["engines"]:
        rows = [r for r in run["results"] if r["engine"] == engine]
        ok = [r for r in rows if r["ok"]]
        failed = f", {len(rows) - len(ok)} failed" if len(ok) < len(rows) else ""
        own = sum(1 for r in ok if r["own"] and not r["cited"])
        extra = f" (+{own} citing your dev.to or GitHub copy)" if own else ""
        parts.append(f"{engine} cited it on {sum(r['cited'] for r in ok)} of {len(ok)} queries{extra}{failed}")
    return f"AI citations, {run['date']}: " + "; ".join(parts) + "."


def last():
    if not LOG.exists():
        print("AI citations: no run logged yet. Run ~/src/evoleinik.com/scripts/ai-citations.py", file=sys.stderr)
        return 2
    print(summary(json.loads(LOG.read_text().strip().splitlines()[-1])))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--queries", type=int, default=20, help="posts to test (default 20)")
    ap.add_argument("--days", type=int, default=90, help="Search Console window (default 90)")
    ap.add_argument("--min-impressions", type=int, default=5, help="drop rarer queries (default 5)")
    ap.add_argument("--query", action="append", help="ask this query instead of the Search Console list (repeatable)")
    ap.add_argument("--engines", default="chatgpt,gemini", help="comma list of: " + ",".join(ENGINES))
    ap.add_argument("--timeout", type=int, default=120, help="seconds per engine call (default 120)")
    ap.add_argument("--json", action="store_true", help="print the run record as JSON")
    ap.add_argument("--no-log", action="store_true", help="do not append to the log")
    ap.add_argument("--last", action="store_true", help="print the latest logged run and exit")
    args = ap.parse_args()
    if args.last:
        return last()
    engines = [e for e in args.engines.split(",") if e]
    if unknown := set(engines) - set(ENGINES):
        ap.error(f"unknown engine {sorted(unknown)}; choose from {sorted(ENGINES)}")
    try:
        items = [{"query": q} for q in args.query] if args.query else top_queries(args.queries, args.days, args.min_impressions)
    except Exception as e:
        print(f"Search Console failed: {e}. Try: ~/bin/gwsp relogin", file=sys.stderr)
        return 2
    if not items:
        print(f"No Search Console queries for {SITE} with {args.min_impressions}+ impressions in {args.days} days. "
              "Try: --days 180, --min-impressions 1, or --query", file=sys.stderr)
        return 2
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda job: ask(*job, args.timeout), [(e, i) for e in engines for i in items]))
    run = {"ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "date": datetime.date.today().isoformat(), "engines": engines,
           "models": {"chatgpt": CHATGPT_MODEL, "gemini": GEMINI_MODEL}, "source": "query" if args.query else
           f"search-console top {args.queries} pages, {args.days} days, min {args.min_impressions} impressions", "queries": items, "results": results}
    if not args.no_log:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as f:
            f.write(json.dumps(run) + "\n")
    print(json.dumps(run, indent=1) if args.json else summary(run))
    for r in results:
        if not r["ok"]:
            print(f"{r['engine']} failed on {r['query']!r}: {r['error']}", file=sys.stderr)
    return 1 if not any(r["ok"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
