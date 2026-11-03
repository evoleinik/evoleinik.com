---
title: "Automatic Research Loops Need an Honest Scorer"
date: 2026-11-03
draft: false
tags: [ai, llm, llm-as-judge, autoresearch, backtesting, evaluation, methodology]
aliases: [/posts/ai-review-panel-rank-not-rewrite/]
summary: "Karpathy's autoresearch and DeepMind's AlphaEvolve improve things with one simple loop: propose a change, score it, keep it only if it wins. I ran the same loop three ways: on trading strategies with a backtest as the scorer, on a spec and a strategy with LLM judges as the scorer, and by hand through 56 LLM review panels. The backtest loop inflated its own results 3 to 4 times. The LLM-judged loops stalled and learned to flatter the judges. Here is what each failure teaches, and how to build a loop that works."
---

Automatic research loops are having a moment. In March 2026 Andrej Karpathy released [autoresearch](https://github.com/karpathy/autoresearch). An AI agent edits one training file, trains a small model for five minutes, and checks one number. If the number improved, the change stays. If not, it is thrown away. The README says to expect about 12 experiments an hour and about 100 while you sleep.

DeepMind's [AlphaEvolve](https://deepmind.google/discover/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/) runs the same kind of loop on algorithms. Gemini models propose programs. Automated evaluators run and score them. The best programs feed the next round. It found a scheduling rule that recovers 0.7% of Google's worldwide compute, and a way to multiply 4x4 complex matrices with 48 multiplications, beating Strassen's 1969 method.

This year I ran the same loop three ways. One searched for trading strategies, with a backtest as the scorer. Two rewrote a product spec and a business strategy, with LLM judges as the scorer. And by hand, I ran 56 LLM review panels on documents, fixing what the critics said and running them again. None of these worked the way autoresearch does. Each one failed in a way that says something general about these loops.

## Every loop has three parts

Every automatic improvement loop has a proposer, a scorer and a keep rule.

| | Proposer | Scorer | Keep rule |
|---|---|---|---|
| autoresearch | An agent edits `train.py` | Validation bits per byte after a fixed 5-minute run | Keep the change only if the number improved |
| AlphaEvolve | Gemini Flash and Pro propose programs | Automated evaluators run each program and score it | A database of the best programs seeds the next round |
| [FunSearch](https://www.nature.com/articles/s41586-023-06924-6) (2023) | An LLM writes programs | An evaluator runs them on the maths problem | The best programs are kept and shown again |
| My trading loop | An agent writes and tunes strategies | Walk-forward Sharpe ratio on historical prices | Keep a change if portfolio Sharpe rises |
| My document loops | An LLM rewrites the document | A panel of LLM judges | Usually the latest draft |

The loops that work share three things. The scorer cannot be talked into a better number. The keep rule is a ratchet: nothing replaces the best version unless it beats it. And the scorer measures the thing you actually want. AlphaEvolve's own description names the limit. It works on problems whose solutions can be "automatically verified".

## A mechanical scorer can still be fooled

The trading loop looked like autoresearch. An agent ran for 55 iterations over a few days in March 2026. Each iteration researched one idea, coded it, and backtested it with walk-forward validation. A change to the portfolio stayed only if its walk-forward Sharpe ratio went up. The loop screened over a thousand ETFs and ran 49,266 backtests in one sweep alone.

The score climbed steadily, from about 1.5 to 2.97. Then, at iteration 55, the loop tested its own process honestly. It ran the whole selection pipeline on older data only, and scored the result on years it had never seen. The backtest Sharpe of 3.8 to 5.6 became about 0.83 out of sample. The loop's own summary says backtest Sharpe is "always inflated", "by 3-4x in practice, even with walk-forward".

Three things went wrong, and none of them needed an LLM judge.

**Too many tries.** Pick the best of thousands of backtests and you pick luck. [Harvey, Liu and Zhu (2016)](https://doi.org/10.1093/rfs/hhv059) argue that most claimed findings in finance are likely false for this reason. A new factor should clear a t-statistic of 3.0, not 2.0. The [deflated Sharpe ratio (Bailey and López de Prado, 2014)](https://papers.ssrn.com/abstract=2460551) corrects a Sharpe ratio for the number of strategies tried.

**The scorer measured a proxy.** Sharpe ratio rewards low volatility. So the loop learned to love low-volatility assets. Money market funds topped the rankings by "trivially gaming the Sharpe ratio", and had to be excluded by hand. The final portfolio put 93% into low-volatility credit funds. It scored a Sharpe of 2.94 and earned 3.9% a year. A plain 70/20/10 blend of stocks, managed futures and a factor fund, with no optimization at all, earned 14.1% a year.

**The test set got used up.** The loop checked its picks against the same recent years again and again. Every check leaked a little information into the next choice. At iteration 53 its own notes said to "stop optimizing on contaminated OOS period".

## An LLM judge adds three more ways to fail

In January 2026 I ran two loops with LLM judges as the scorer.

The first rewrote a product requirements document. Two LLM judges scored each version, and later four. The target was 8 out of 10. Over 100 versions the score went from 4.0 to a peak of 7.7 at version 86. The 14 versions after it never beat it. The last one scored 6.5.

The second searched for a business strategy, with five LLM judges. It peaked at 6.5 at version 16. None of the next six versions beat it. The last scored 3.6.

**There was no ratchet.** Each new version could start from anywhere, so the loop wandered away from its best draft.

**The judges rewarded spin.** In the spec loop, a version the loop itself labelled "inflated" scored 6.6. The next one, labelled "honest reality: $0 revenue", scored 3.9. A version that admitted how few real contacts it had took what the loop called an "honesty penalty". A backtest cannot be flattered. A language model reading a confident claim can. [Pan, He, Bowman and Feng (2024)](https://arxiv.org/abs/2407.04549) found the same in a controlled study: "the evaluator's ratings improve while the generation quality remains stagnant or even decreases."

**The loop took the judges' advice, and the wrong part of it.** The spec loop's instructions said to "fix weak dimensions", meaning whatever the judges marked down. They also said that when judges say "stop writing PRDs, start executing", to "ignore this advice". Both loops ended at the conclusion that advice pointed to. The spec loop's final summary reads: "No amount of iteration can break 7.7 without execution evidence."

Midway, the spec loop added a judge and two scoring dimensions. Three unchanged versions were scored again under the new setup. They moved by 0.26, 0.65 and 0.94 points. Changing the scorer moved the score as much as most rewrites did.

## The judges' advice is the weakest signal they give

The same thing happens by hand. You run an LLM review panel, fix what it says, and run it again. I went back through all 56 panels I had run this year, 147 rounds in all, and sorted each pair of consecutive rounds by the kind of edit made between them.

| Edit between rounds | Pairs | Mean score change (10-point scale) | Rounds where the yes share rose |
|---|---|---|---|
| Taste: framing, emphasis, structure, wording the critic preferred | 5 | +0.04 (2 up, 3 down) | 0 of 5 |
| Error: a wrong fact, a contradiction, a leak, an overclaim, an unexplained term, a typography error | 8 | +0.62 (8 up) | 1 of 5 |
| Proof: a new fact, something built, a signed customer | 4 | +0.66 (4 up) | 3 of 3 |
| Nothing: the same text run again | 9 | +0.14 | 0 of 8 |

The judges are right about errors. A wrong number is wrong for every reader, so fixing it raises every score. Their taste is noise. And the verdict moves on proof.

The research agrees. The [JETTS benchmark (Zhou et al., Salesforce, 2025)](https://arxiv.org/abs/2504.15253) tested LLM judges as helpers for a generator. Judges were "competitive with outcome reward models in reranking". But "their natural language critiques are currently ineffective in guiding the generator towards better responses". [Stechly, Marquez and Kambhampati (2023)](https://arxiv.org/abs/2310.12397) found "the correctness and content of the criticisms" was "largely irrelevant" to iterative prompting. The gains came from trying several answers and letting a sound verifier pick. [Turpin et al. (NeurIPS 2023)](https://arxiv.org/abs/2305.04388) showed that a model's written reasons can be plausible and still leave out what drove its answer. A loop that acts on the reason steers by the wrong signal.

LLM judges are also noisy. On one five-critic panel, identical text moved up to 0.6 points on one dimension between two runs. One critic said "pass" at 95% confidence, then "second meeting" at 80%, on the same text. A [2026 study of repeated LLM judging](https://arxiv.org/abs/2606.13685) found pairwise verdicts flip 13.6% of the time on identical input.

## How to build a loop that works

1. **Use a mechanical scorer wherever one exists.** A test suite, a checker script, a measured outcome. Put every part of the problem you can measure into code before you reach for a judge.
2. **Score the goal, not a proxy that is easy to raise.** Sharpe ratio was easy to raise by holding bonds. The goal was money. If the scorer can be satisfied by something you would not want, the loop will find it.
3. **Keep the proposer away from the scorer.** autoresearch lets the agent edit one file, and everything else stays fixed. An LLM judge should never see a changelog or the last round's verdict.
4. **Hold out a test the loop never sees.** Check the final winner on it once. If you look at it every round, it stops being a test.
5. **Count your tries, and discount for them.** The best of 1,000 candidates is mostly luck. Deflate the score, or confirm the winner on fresh data or fresh judge runs.
6. **Ratchet.** A new version replaces the best only if it beats it by more than the noise. Measure the noise first, by scoring the unchanged best version twice.
7. **Let an LLM judge score, not steer.** Ask it for scores, a verdict, checkable errors, and the one piece of evidence that would change its mind. Do not ask for improvements. Fix the errors directly, because they are wrong.
8. **Compare against a simple baseline.** On returns, the trading loop's 8-strategy portfolio lost to a three-fund blend that needed no loop at all.
9. **Treat the plateau as a signal.** When the best version stops improving, the gap is usually evidence the loop cannot produce. Stop and go get it. If real people will read or use the result, test it on them. Their behaviour is the most honest scorer there is.

## Limits

These are my own loops, three small cases and one panel log. I labelled the kind of each panel edit myself, and each kind has only 4 to 8 pairs. The critics often came from the same model family as the writer. The general point does not rest on my numbers, though. It is the one autoresearch, AlphaEvolve and FunSearch are built on, and the one quantitative finance learned the hard way. An automatic research loop is only as good as its scorer and its keep rule.
