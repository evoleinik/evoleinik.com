#!/usr/bin/env bash
# Tell Bing (and the other IndexNow engines) which pages changed.
# Bing's index feeds ChatGPT search and Copilot, so a ping gets a new post seen in minutes.
#
# Usage:
#   scripts/indexnow.sh --changed BASE HEAD   ping posts changed between two commits, plus / and /posts/
#   scripts/indexnow.sh --all                 ping every URL in the live sitemap
#   scripts/indexnow.sh URL...                ping these URLs
#
# Exit codes: 0 accepted or nothing to ping, 1 rejected by IndexNow, 2 bad usage.
# The key is the name of the one static/<32 hex>.txt file. It is public by design.
set -euo pipefail
cd "$(dirname "$0")/.."

SITE="https://evoleinik.com"
HOST="evoleinik.com"

keys=(static/????????????????????????????????.txt)
if [ "${#keys[@]}" -ne 1 ] || [ ! -f "${keys[0]}" ]; then
  echo "indexnow: expected exactly one static/<32 hex>.txt key file, found ${#keys[@]}" >&2
  exit 2
fi
KEY=$(basename "${keys[0]}" .txt)

post_url() { # content/posts/<file>.md -> live URL, honouring a front-matter slug
  local f=$1 slug
  slug=$(basename "$f" .md)
  if [ -f "$f" ]; then
    grep -qE '^draft:[[:space:]]*true' "$f" && return 0
    local s
    s=$(sed -n 's/^slug:[[:space:]]*["'\'']\{0,1\}\([^"'\'']*\)["'\'']\{0,1\}[[:space:]]*$/\1/p' "$f" | head -1)
    [ -n "$s" ] && slug=$s
  fi
  echo "$SITE/posts/$slug/"
}

urls=()
case "${1:-}" in
  --changed)
    [ $# -eq 3 ] || { echo "usage: $0 --changed BASE HEAD" >&2; exit 2; }
    while IFS= read -r f; do
      u=$(post_url "$f"); [ -n "$u" ] && urls+=("$u")
    done < <(git diff --name-only "$2" "$3" -- 'content/posts/*.md')
    [ ${#urls[@]} -gt 0 ] && urls+=("$SITE/" "$SITE/posts/")
    ;;
  --all)
    while IFS= read -r u; do urls+=("$u"); done \
      < <(curl -fsS "$SITE/sitemap.xml" | grep -o '<loc>[^<]*</loc>' | sed 's/<[^>]*>//g')
    ;;
  ''|-h|--help)
    sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
  *)
    urls=("$@") ;;
esac

if [ ${#urls[@]} -eq 0 ]; then
  echo "indexnow: no post changed, nothing to ping"
  exit 0
fi

body=$(printf '%s\n' "${urls[@]}" | python3 -c '
import json, sys
urls = list(dict.fromkeys(l.strip() for l in sys.stdin if l.strip()))
print(json.dumps({"host": sys.argv[1], "key": sys.argv[2],
                  "keyLocation": f"https://{sys.argv[1]}/{sys.argv[2]}.txt", "urlList": urls}))
' "$HOST" "$KEY")
n=$(printf '%s' "$body" | python3 -c 'import json,sys;print(len(json.load(sys.stdin)["urlList"]))')

code=$(curl -sS -o /tmp/indexnow.out -w '%{http_code}' -X POST \
  -H 'Content-Type: application/json; charset=utf-8' -d "$body" https://api.indexnow.org/indexnow)
case "$code" in
  200|202) echo "indexnow: $code accepted, $n URLs"; printf '%s\n' "${urls[@]}" | sort -u ;;
  *) echo "indexnow: $code rejected, $n URLs: $(head -c 300 /tmp/indexnow.out)" >&2
     echo "fix: check $SITE/$KEY.txt serves the key, then re-run: scripts/indexnow.sh --all" >&2
     exit 1 ;;
esac
