---
title: "GitHub Actions startup_failure on every run: check billing"
date: 2026-11-15
draft: false
tags: [github-actions, ci, billing]
summary: "Every GitHub Actions run fails with startup_failure and no jobs, yet the YAML is fine. Pay the declined invoice, then raise the Actions budget."
---

When every GitHub Actions run on every branch fails at once with `startup_failure` and zero jobs, look at billing before you open a single workflow file. First check payment history for a declined charge, and re-save the payment method to force a new charge. Then check the Actions budget, because a $0 budget with "Stop usage when budget limit is reached" turned on blocks jobs as soon as the included usage runs out.

This happened to an organization I run. From one minute to the next, every run failed: pushes, pull requests, schedules on `main`, deployment events. No workflow file had changed. githubstatus.com showed Actions as operational. The CLI blamed the workflow file. The real cause was a declined card payment, which locked the account's paid features. Paying the invoice brought Actions back within a minute.

## Confirm the GitHub Actions startup_failure hits every run

A broken workflow file breaks that one workflow. A billing lock breaks all of them at the same moment. So count the failures across branches and events first:

```bash
gh run list --status startup_failure --limit 100 --json headBranch,event \
  --jq '{runs: length, branches: (map(.headBranch) | unique), events: (map(.event) | unique)}'
```

Five hours into the lock, mine looked like this. I changed the branch names:

```text
{"branches":["feature/search","fix/login-timeout","main"],"events":["deployment_status","pull_request","pull_request_target","push","schedule"],"runs":49}
```

Then find the last run that did start. Its timestamp tells you when the lock began, and you can match it against a billing email:

```bash
gh run list --limit 200 --json createdAt,conclusion,event \
  --jq '[.[] | select(.conclusion != "startup_failure")][0]'
```

```text
{"conclusion":"success","createdAt":"2026-10-01T21:42:43Z","event":"schedule"}
```

Rule out a GitHub outage while you are here:

```bash
curl -s https://www.githubstatus.com/api/v2/incidents/unresolved.json | jq '.incidents[].name'
```

No output means no open incident.

## Read the run's name and path

The REST API keeps a detail that `gh run list` hides. Pick one failed run and read its `name` and `path`:

```bash
gh api repos/OWNER/REPO/actions/runs/RUN_ID \
  --jq '{conclusion, display_title, name, path}'
```

My billing-locked runs all came back the same way. The name was empty, and the path pointed at no file:

```text
{"conclusion":"startup_failure","display_title":"(Unknown event)","name":"","path":"BuildFailed"}
```

A run that fails on a real workflow error still names its file:

```text
{"conclusion":"startup_failure","display_title":"Add retry to deploy step","name":"CI","path":".github/workflows/ci.yml"}
```

Both kinds have zero jobs, so the job count alone does not separate them:

```bash
gh run view RUN_ID --json conclusion,jobs --jq '{conclusion, jobs: (.jobs | length)}'
```

```text
{"conclusion":"startup_failure","jobs":0}
```

I have seen `BuildFailed` in one billing incident only. Treat it as a strong hint. The payment history in the next steps is the proof.

## Ignore "This run likely failed because of a workflow file issue"

`gh run view` prints this for every run that failed at startup:

```text
X This run likely failed because of a workflow file issue.

For more information, see: https://github.com/OWNER/REPO/actions/runs/RUN_ID
```

That line is not a diagnosis from GitHub. The gh CLI prints the same fixed sentence for any run whose conclusion is `startup_failure` ([source](https://github.com/cli/cli/blob/3d5a9e355a837f2f5ee78d7484c118cc1342ad1a/pkg/cmd/run/view/view.go#L385-L388)). It cannot tell a billing lock from a typo.

The web UI shows "Startup failure" as the run's status and "failed at startup" in the run list. GitHub's docs define the `startup_failure` status in one line: "The check suite failed during startup." ([source](https://docs.github.com/en/pull-requests/reference/status-checks)). That is the whole definition. Nothing in it says the workflow file is at fault.

## Check payment history for a GitHub Actions billing issue

A declined payment locks the account's paid features, and Actions stops with them. GitHub's docs put it this way: "Your account's paid features are locked if your payment is past due because of billing problems." ([source](https://docs.github.com/en/billing/how-tos/troubleshooting/locked-account)).

Open the payment history:

- Organization: Your organizations, then Settings next to the organization, then Billing & Licensing, then Payment history.
- Enterprise: Your enterprises, the enterprise name, the Billing & Licensing tab, then Payment history.
- Personal account: Settings, then Billing & Licensing in the Access section, then Payment history.

Look for a row whose status reads `Declined`. GitHub also sends an email with the subject "We had a problem billing your account". Mine said:

```text
We will try billing your credit card again over the next two weeks.
```

Do not wait two weeks. The docs say to "update your billing information to trigger a newly authorized charge." Open Payment information, click Edit on the payment method, and save it. Re-entering the same card is enough. Saving starts a new charge at once.

Waiting does not help, because GitHub only retries on its own schedule. Re-saving the card charged the invoice, and the next run started normally about a minute later. The docs promise less: "The account will automatically unlock when a payment has been successfully processed. Payments may take up to 24 hours to process."

## Read the Actions budget

Budgets are the second billing cause. They replaced spending limits when GitHub moved accounts to its new billing platform. The changelog said: "Spending limits will be migrated and renamed as budgets in the new billing platform." ([source](https://github.blog/changelog/2025-02-24-migration-of-github-team-plan-organizations-to-the-enhanced-billing-platform/)).

The setting lives on the "Budgets and alerts" page ([source](https://docs.github.com/en/billing/how-tos/set-up-budgets)):

- Organization: Billing & Licensing in the organization's settings sidebar, then Budgets and alerts. Organization owners and billing managers can edit it.
- Personal account: open https://github.com/settings/billing, then Budgets and alerts.

For an organization you can also read the budgets from the CLI. You need to be an owner or billing manager. These calls only read:

```bash
gh api /organizations/YOUR_ORG/settings/billing/budgets \
  --jq '.budgets[] | {sku: (.budget_product_sku // .budget_product_skus), amount: .budget_amount, stop: .prevent_further_usage}'
```

```text
{"amount":0,"sku":"actions","stop":true}
{"amount":0,"sku":"packages","stop":true}
{"amount":0,"sku":"codespaces","stop":true}
```

`"amount":0` with `"stop":true` means zero paid Actions usage is allowed. The docs example names the field `budget_product_skus`, an array. The live API returned `budget_product_sku`, a string, for my organization. The `//` in the filter covers both ([budgets API](https://docs.github.com/en/rest/billing/budgets)).

Then check how much of the included usage a month has used. Set the year and month:

```bash
gh api "/organizations/YOUR_ORG/settings/billing/usage/summary?year=2026&month=10" \
  --jq '.usageItems[] | select(.sku == "actions_linux") | {minutes: .grossQuantity, included: .discountQuantity, paid: .netAmount}'
```

```text
{"included":1342,"minutes":1342,"paid":0}
```

`paid` above zero means you went past the included usage. With a $0 stop budget, jobs stop at the moment paid usage would begin ([usage API](https://docs.github.com/en/rest/billing/usage)).

Older guides point at a different endpoint. It is gone:

```bash
gh api /orgs/YOUR_ORG/settings/billing/actions
```

```text
gh: This endpoint has been moved. (HTTP 410)
```

In my case the budget was not what blocked runs that day. Every minute that month was still included, and `paid` was 0. But the month before, the organization had gone well past its included usage. A month like that under a $0 stop budget ends with every job blocked before the month is over.

## GitHub Actions budget is preventing further use

When a budget stops usage, the run may not end in `startup_failure` at all. In a public run I checked, GitHub created the job, gave it zero steps and no runner, and failed it in three seconds. The run's conclusion was `failure`. `gh run view RUN_ID` shows the cause under ANNOTATIONS:

```text
ANNOTATIONS
X The job was not started because an Actions budget is preventing further use.
```

Some accounts get a different annotation for a payment problem ([source](https://github.com/orgs/community/discussions/213007)):

```text
The job was not started because recent account payments have failed or your spending limit needs to be increased.
```

So check both shapes. A run-level `startup_failure` with no jobs, or a job that fails in seconds with one of these two annotations, both point at billing.

## Increase the GitHub Actions budget

On the Budgets and alerts page, click the menu next to the Actions budget, then Edit. Raise the amount. Keep "Stop usage when budget limit is reached" if you want a hard cap. Keep "Receive budget threshold alerts" on, so you get an email at 75%, 90% and 100%.

Two warnings from the docs. If you leave the stop option off, "usage **will not** be stopped", and you only get an email. And deleting a budget "may remove any limits on spending, depending on your other existing budgets." Edit it, do not delete it.

The same change is possible through the API with `PATCH /organizations/{org}/settings/billing/budgets/{budget_id}` ([docs](https://docs.github.com/en/rest/billing/budgets)). I set mine well above the previous month's overage.

## Restart the runs that failed at startup

GitHub refuses to rerun a run that failed at startup, even after billing is fixed:

```bash
gh run rerun RUN_ID
```

```text
run RUN_ID cannot be rerun; its workflow file may be broken
```

That text comes from the API, and once again it blames the file. Start fresh runs instead.

For an open pull request, close and reopen it. By default, `pull_request` workflows run on `opened`, `synchronize` and `reopened` ([source](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)):

```bash
gh pr close 123 --comment "Restarting CI after a billing lock" && gh pr reopen 123
```

First check that no workflow acts on `closed`, and note any workflow whose `types:` list leaves out `reopened`:

```bash
grep -n -A3 -E "pull_request(_target)?:" .github/workflows/*.yml | grep -E "types:"
```

For a workflow with a `workflow_dispatch` trigger, start it by hand:

```bash
gh workflow run ci.yml --ref main
```

Scheduled workflows restart on their next cron tick. Anything else needs a new push or a new trigger event.

## Verify it worked

Start a short workflow that has a `workflow_dispatch` trigger, then list its latest runs:

```bash
gh workflow run docs-check.yml --ref main
sleep 20
gh run list --workflow docs-check.yml --limit 2 --json createdAt,event,status,conclusion \
  --jq '.[] | [.createdAt, .event, .status, .conclusion] | @tsv'
```

Expected output once the lock is gone:

```text
2026-10-02T04:37:46Z	workflow_dispatch	completed	success
2026-10-01T07:42:21Z	schedule	completed	success
```

A longer workflow shows `in_progress` with an empty conclusion. That also counts. What matters is that the newest run is not `startup_failure`. Then check the newest runs across the repository:

```bash
gh run list --limit 5 --json createdAt,status,conclusion \
  --jq '.[] | [.createdAt, .status, .conclusion] | @tsv'
```

None of the runs created after the fix should read `startup_failure`.

## Other causes of startup_failure

Billing is not the only cause. These are the others I could confirm, with a quick way to tell each one apart.

| Cause | Ends in `startup_failure`? | How to tell |
|---|---|---|
| Declined payment, account locked | Yes, every workflow on every branch | `name` empty, `path` is `BuildFailed`, payment history shows `Declined` |
| Budget with stop reached | Not in the run I checked. It ended in `failure` with a zero-step job | Annotation "The job was not started because an Actions budget is preventing further use." |
| Invalid workflow file | Yes, that one file only | `path` names the file. The run page shows "Invalid workflow file" with a line number |
| Action not on the organization allow-list | Yes | Run page annotation "... are not allowed in OWNER/REPO because all actions must be from a repository owned by ..." |
| Blocked action inside a composite action | No, `failure` in "Set up job" | Annotation "The action actions/cache@v4 is not allowed in OWNER/REPO because all actions must be pinned to a full-length commit SHA." |
| Self-hosted runner label nobody serves | No | The job sits in `queued` and fails after 24 hours |

An invalid file fails fast and keeps failing. The docs warn: "If `.github/workflows` contains an invalid workflow file, GitHub Actions generates a failed workflow run for every new commit." ([source](https://docs.github.com/en/actions/how-tos/monitor-workflows/use-workflow-run-logs)). It looks like a lock, but only one workflow fails, and the run page shows an error like this:

```text
Invalid workflow file: .github/workflows/ci.yml#L17
The workflow is not valid. .github/workflows/ci.yml (Line: 17, Col: 3): ...
```

The gh CLI hides that annotation for runs with no jobs. Open the run in the browser to read it. Then run [actionlint](https://github.com/rhysd/actionlint) locally on the file it names.

A missing self-hosted runner does not cause `startup_failure`. GitHub's runner docs say: "If the job remains queued for more than 24 hours, the job will fail." ([source](https://docs.github.com/en/actions/reference/runners/self-hosted-runners)). So a run that sits in `queued` is a runner problem. A run that dies in zero seconds is not.

One more point about the billing lock. Many of my CI jobs ran on self-hosted runners, which GitHub does not bill. They were blocked too. The run failed before GitHub picked a runner for any job.

## Trade-offs

A $0 budget with the stop on is a reasonable setting for a small team. It guarantees no surprise bill. The cost is that running out of included usage takes CI down, and the first message you see may point at your YAML. If CI gates merges and deploys, set a real cap with alerts at 75%, 90% and 100%. A slightly larger bill is cheaper than an afternoon lost to an outage.

A budget does nothing against a declined card. Keep the card's limit above the monthly invoice, or pay with PayPal, which GitHub also accepts.

Raising a budget can itself trigger a card check. The docs warn that a failed authorization hold when you "increase a budget can also lock your personal account billing and block GitHub Actions." Raise it when you can watch the payment history.

Avoid overlapping budgets. If any budget with the stop on runs out, usage is blocked, even when a narrower budget has room left. The docs' example is a $50 Actions budget that blocks all GitHub-hosted runners, even though a $100 budget for one Actions SKU still has room.

A new budget only counts usage from the day you create it. In the first billing cycle you can go past it even with the stop on.

Do not edit the workflow files to make the error go away. Nothing in them is broken. Every commit you push to "fix" them also fails at startup, and it leaves noise in the history.
