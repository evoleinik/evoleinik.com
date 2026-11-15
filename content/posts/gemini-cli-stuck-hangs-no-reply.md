---
title: "Gemini CLI stuck or hangs with no reply: escape the @"
date: 2026-11-15
draft: false
tags: [gemini-cli, headless, git-diff, debugging]
summary: "Gemini CLI stuck or hangs with no reply when the prompt holds an @, like a git diff @@ line. Put a backslash before each @, or run from an empty folder."
---

If `gemini -p "..."` prints nothing and never exits, look for an `@` in the prompt. Gemini CLI reads `@` as a file include, and the `@@ -1,3 +1,3 @@` hunk header of a git diff counts. Put a backslash before every `@`, or run the CLI from an empty folder, and the reply comes back in about 4 to 5 seconds.

I hit this when a script sent a git diff to `gemini -p` for review. The call sat with empty stdout until my timeout killed it. The same text without the `@@` line answered in seconds. I tested everything below on Gemini CLI 0.52.0 and on 0.68.0, the latest on npm on 2026-11-15. Both used Vertex AI auth and the `gemini-3.8-flash` model on Linux.

## Find the @ that leaves Gemini CLI stuck

```bash
printf '%s\n' "$PROMPT" | grep -n '@'
```

Any line this prints is a suspect. The usual one is a diff hunk header, `@@ -874,6 +874,8 @@`. A decorator, an npm scope such as `@types/node`, or an email address matches the same rule. I only timed the `@@` case.

The hang looks like this. There is no error and no partial output. Stdout stays at 0 bytes. In my runs `timeout 60` sent SIGTERM at 60 seconds and the process kept going. Only the SIGKILL from `-k 5` ended it, at 65 seconds with exit code 137.

Here are the main runs, each with `timeout -k 5 60` and the same short test diff:

| Version | Started from | Prompt | Result | Wall time |
|---|---|---|---|---|
| 0.52.0 | home folder | `@@` hunk header | no output, killed | 65.0 s |
| 0.52.0 | empty temp folder | `@@` hunk header | answered | 4.3 s |
| 0.52.0 | home folder | `\@\@` escaped | answered | 3.8 s |
| 0.52.0 | home folder | `@@` line removed | answered | 3.7 s |
| 0.52.0 | home folder | escaped diff piped on stdin | answered | 3.9 s |
| 0.68.0 | home folder | `@@` hunk header | no output, killed | 65.0 s |
| 0.68.0 | empty temp folder | `@@` hunk header | answered | 4.6 s |
| 0.68.0 | home folder | `\@\@` escaped | answered | 5.0 s |
| 0.68.0 | home folder | `@@` line removed | answered | 5.0 s |

The model is not the problem. The same prompt answers in seconds from an empty folder.

## Escape every @ before calling gemini -p

```bash
PROMPT=$(git diff | sed 's/@/\\@/g')
gemini -p "Review this diff:
$PROMPT"
```

The CLI skips an `@` that has a backslash in front of it. This works from any folder, and it worked on both versions. The backslashes do reach the model. In my runs the answer was the same as with the `@@` line removed.

The docs do not mention `\@`. They only say to escape spaces in a path, as in `@My\ Documents/file.txt`. The rule comes from the parser in the CLI source. [Issue #29434](https://github.com/google-gemini/gemini-cli/issues/29434) gives the same `sed` line as its workaround.

## Pipe a git diff into Gemini CLI safely

```bash
git diff | sed 's/@/\\@/g' | gemini -p "Review this diff."
```

Piping does not avoid the problem. In headless mode the CLI joins the stdin text and the `-p` text into one prompt, and then parses the whole thing for `@`. That is in the 0.52.0 source, and issue #29434 says the same. The escaped pipe above answered in 3.9 seconds from my home folder.

## Run Gemini CLI from an empty folder instead

```bash
run_dir=$(mktemp -d)
(cd "$run_dir" && GEMINI_CLI_TRUST_WORKSPACE=true gemini -p "$PROMPT")
rm -rf "$run_dir"
```

The fallback search for `@` paths runs over the folder you start in. An empty folder gives it nothing to search. This also covers an `@` you did not think to escape.

You need `GEMINI_CLI_TRUST_WORKSPACE=true` or `--skip-trust` here. A new folder is not trusted, and headless mode cannot ask. Without it, 0.52.0 exits with code 55 and this message:

```text
Gemini CLI is not running in a trusted directory. To proceed, either use `--skip-trust`, set the `GEMINI_CLI_TRUST_WORKSPACE=true` environment variable, or trust this directory in interactive mode. For more details, see https://geminicli.com/docs/cli/trusted-folders/#headless-and-automated-environments
```

The [trusted folders doc](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/trusted-folders.md) lists both options for headless runs. My own wrapper script does this whenever it is started from the home folder.

## Turn off the fallback file search

```bash
f=~/.gemini/settings.json
[ -f "$f" ] || echo '{}' > "$f"
jq '.context.fileFiltering.enableRecursiveFileSearch = false' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
```

With this setting in the user settings file, the `@@` prompt answered from the home folder in 4.0 seconds on 0.52.0 and in 5.3 seconds on 0.68.0.

The [configuration reference](https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/configuration.md) describes the setting as "Enable recursive file search functionality when completing @ references in the prompt." That reads like it only affects tab completion. In the source, the same setting gates the search that hangs. My runs agree with the source.

## Put a hard timeout on headless runs

```bash
timeout -k 5 120 gemini -p "$PROMPT"
```

A plain `timeout 120` was not enough in my runs. The CLI ignored SIGTERM while it was stuck. `-k 5` sends SIGKILL five seconds later. Check for exit code 124 or 137 and treat it as "no answer", so a script does not wait forever.

## Verify it worked

Run the escaped prompt from your home folder, where the hang is worst:

```bash
cd ~
time timeout -k 5 60 gemini -p 'Reply in one short sentence: what does this diff change?
\@\@ -1,3 +1,3 \@\@
-color = "red"
+color = "blue"'
echo "exit=$?"
```

Expected output in bash, with your own wording and timing:

```text
This diff changes the value of the `color` variable from "red" to "blue".

real	0m3.8s
...
exit=0
```

Now take the backslashes out and run it again. If it prints nothing and ends with `exit=137` after 65 seconds, you have this bug, and the fixes above are the cure.

## Why the @@ line makes Gemini CLI hang

The CLI looks for an `@` with no backslash before it, followed by path characters. In `@@ -1,3 +1,3 @@`, the first `@` starts an include and the second `@` is the path. So the CLI looks for a file named `@`.

The [commands reference](https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/commands.md) says a lone `@` is passed through as plain text. `@@` is not a lone `@`, so that rule does not save you.

No file named `@` exists. The CLI then falls back to a glob search for `**/*@*` in every workspace folder. Started from the home folder, that means the whole home tree. That search did not finish within 60 seconds on either version. In an empty folder it finishes at once, and the prompt goes to the model with `@@` as plain text.

The docs say a missing `@` path shows an error message. In headless mode I saw none. The hung runs never got that far. The runs that answered printed nothing about `@` either.

PR [#29557](https://github.com/google-gemini/gemini-cli/pull/29557), merged on 2026-09-30, fixed a related hang. In issue #29434, a quoted `"@scope/pkg"` swallowed thousands of characters of code into one huge path, and the glob search pegged the CPU. The fix skips the search for paths over 255 characters, absolute paths, paths with `..`, and paths with newlines or glob characters. A one-character path `@` passes all of those checks. That is why 0.68.0 still hangs on a diff.

## Other reasons Gemini CLI hangs

I did not reproduce these. Each one links to its report.

**Gemini CLI hangs on startup, stuck at "Initializing...".** [Issue #20433](https://github.com/google-gemini/gemini-cli/issues/20433), on 0.30.0, traced a 3 to 5 minute hang to a missing `ripgrep`. The CLI tried to download it in the background, and a proxy blocked the download. The reporter installed `ripgrep` and linked it to `~/.gemini/tmp/bin/rg`.

**Gemini CLI stuck on waiting for auth.** [Issue #13853](https://github.com/google-gemini/gemini-cli/issues/13853) reports that 0.18.0 froze on Google login on a server with no browser, without printing the login URL. [Issue #1835](https://github.com/google-gemini/gemini-cli/issues/1835) reports a "Waiting for auth" loop that ignored Ctrl-C.

**Gemini CLI hangs on thinking.** [Issue #29594](https://github.com/google-gemini/gemini-cli/issues/29594) reports the built-in GoogleSearch tool sitting in "Thinking..." for over 30 minutes with no timeout. [Issue #18030](https://github.com/google-gemini/gemini-cli/issues/18030) reports API calls that wait up to 5 minutes, the Node default, when the backend or a proxy stops answering.

## Trade-offs

Escaping every `@` also turns off real includes in that text. If you meant `@src/app.ts`, escape the pasted part only and leave your own include alone.

The empty folder hides your project from the CLI. It cannot read files you meant it to read. Only set `GEMINI_CLI_TRUST_WORKSPACE=true` on a folder you made empty yourself. The trusted folders doc says an untrusted folder's `.gemini/settings.json` and `.env` files are not loaded. Trusting a real project loads them, and its hooks, without asking.

Turning off `enableRecursiveFileSearch` is a global change. It also affects `@` completion in interactive mode. From the 0.52.0 source, an exact path such as `@src/app.ts` still resolves. A bare file name such as `@app.ts` that is not in the current folder will no longer be found.

None of this is fixed upstream as of 0.68.0. If a later version stops the search for short paths like `@`, you can drop the workaround. Run the verify step without the backslashes to find out.
