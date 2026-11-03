---
title: "How to Run an LLM Review Panel: Use It to Check, Not to Write"
date: 2026-11-03
draft: false
tags: [ai, llm, llm-as-judge, evaluation, writing, methodology]
summary: "An LLM review panel, or council, is several models with personas scoring a draft cold. The usual loop is to fix what the critics say and run them again. That loop barely moves the score. Across 270 logged rounds, edits of taste moved it 0.04 points out of 10, error fixes 0.62, and only new proof changed verdicts. Here is a method that uses the panel for what it does well: catching errors and naming the evidence a reader needs."
---

An LLM review panel is a simple idea. You give a draft to several language models. Each one plays a reader: a skeptical investor, a buyer, a competitor, a domain expert. Each reads the draft cold and returns scores, a verdict and comments. I call it a council. People use the same setup for pitches, specs, essays, cover letters and product pages.

The natural way to use a council is to read the comments, fix what they ask for, and run it again. That loop feels like progress. It mostly isn't. The score barely moves, the verdict almost never changes, and each round brings a new list of complaints.

This post describes a method that works better, and the evidence behind it. The short version: **use the council to catch errors and to name the evidence a reader would need. Do not use it to decide what to write.**

## What a council is good for

A council does three things well.

1. **Catching checkable errors.** A wrong number, a claim that contradicts another claim, an unexplained term, a typography mistake. These are wrong for every reader, so fixing them helps with every reader.
2. **Naming the missing proof.** Critics are good at saying what evidence would change their mind: a reference customer, a measured result, a working demo.
3. **Comparing two versions.** Given two drafts, it picks the stronger one fairly reliably. The [JETTS benchmark (Zhou et al., Salesforce, 2025)](https://arxiv.org/abs/2504.15253) tested LLM judges as helpers for a writer model. Judges were "competitive with outcome reward models in reranking".

It does one thing badly. Its advice on taste, meaning framing, emphasis, structure and wording, does not reliably make the draft better. JETTS found the same: the judges' "natural language critiques are currently ineffective in guiding the generator towards better responses".

## Set up the panel

- **Three to seven critics.** Mix model families, such as Claude, GPT and Gemini. Each family has its own blind spots and preferences.
- **Personas that match real readers.** Pick the people who will actually read the draft and decide something. Add one hostile reader, such as a competitor or a skeptic.
- **A fixed rubric.** Four to seven scores from 1 to 10, plus a verdict with named categories, plus a confidence level. Name the verdicts after the real decision: "take meeting / pass", "publish / revise / kill", "approve / reject".
- **Cold reads every round.** Never tell a critic the round number, its earlier verdict or what changed. Remove changelog notes and "reviewers said" lines from the text. A critic that knows the history grades the diff, and agrees out of politeness.
- **Freeze it.** Use the same personas, models and rubric for every round you plan to compare. A change in any of them starts a new baseline.

## Ask for numbers, errors and proof, never advice

The prompt matters more than the personas. Ask for this:

```
Score <dimensions> (1-10).
VERDICT: <named categories>, with confidence %.
ERRORS: each wrong fact, contradiction, leak, overclaim, unexplained term or
craft error, quoted with the line it is on. "None" is a valid answer.
PROOF: the one piece of evidence, not wording, that would change your verdict.
```

Do not ask for "top three improvements" or "suggestions". A critic asked for three problems returns three, whether or not they matter. Fix them and three new ones appear. The length of that list tells you nothing about how much better the draft can get.

## Read the output in two tables

Sort everything the critics say into two tables, and ignore whatever fits neither.

| Table | What goes in | What you do |
|---|---|---|
| Defects | Something you can check against a source: a wrong figure, a contradiction, a leak, a claim the evidence does not support, a promised item left out, an unexplained term, a craft error | Check it, then fix it directly. Fix it because it is wrong, not to raise the score |
| Proof | Evidence that does not exist yet: a reference, a result, a demo, money moving | Go and get it. No rewrite will supply it |

Everything else is taste: "lead with X", "add a section on Y", "cut Z", "sharpen the framing". Taste goes in neither table, and you do not act on it.

## Improve the draft with evidence and real readers

1. **Fix the defects.**
2. **Get the proof the critics named, and add it.** A measured result or a working demo moves readers in a way no rewording can.
3. **If you are torn between two approaches, write both yourself.** Compare them with the unchanged draft as a control, on the same frozen panel, cold. A difference smaller than the control's own spread is noise.
4. **If many people will read it, test the two versions on them.** A landing page, an email campaign or a public demo has real readers. Their replies, clicks and meetings are a better score than any panel. Use the panel only to check for errors before you send.
5. **Keep the version that wins, never simply the latest.**
6. **Stop editing when the score stops moving.** Whatever the critics still want is now in the Proof table. Go and get it.

## Measure the noise before you trust a difference

Run the unchanged control twice before you compare anything. On one five-critic panel, identical text moved up to 0.6 points on one dimension between two runs. One critic said "pass" at 95% confidence, then "second meeting" at 80%, on the same text. A typical edit is worth 0.1 to 0.4 points. One re-run cannot tell an improvement from a different roll of the dice.

The research agrees. [One 2026 study of repeated LLM judging](https://arxiv.org/abs/2606.13685) found pairwise verdicts flip 13.6% of the time on identical input. It took 11 repeats to recover a stable verdict 95% of the time. [Stureborg et al. (2024)](https://arxiv.org/abs/2405.01724) found LLM evaluators inconsistent across samples and prone to anchoring.

## The evidence: 270 logged rounds

I went back through every council I had run in 2026. That was 56 panels and 5 automated rewrite loops, 270 rounds in all, on business writing: pitch decks, partner notes, specs, applications, comments on public standards. For each round I logged the verdicts, the mean score and what had changed since the round before. Then I sorted every pair of consecutive rounds by the kind of edit made between them.

| Edit between rounds | Pairs | Mean score change (10-point scale) | Rounds where the yes share rose |
|---|---|---|---|
| Taste: framing, emphasis, structure, wording the critic preferred | 5 | +0.04 (2 up, 3 down) | 0 of 5 |
| Defect: a wrong fact, a contradiction, a leak, an overclaim, an unexplained term, a craft error | 8 | +0.62 (8 up) | 1 of 5 |
| Proof: a new fact, something built, a signed customer | 4 | +0.66 (4 up) | 3 of 3 |
| Nothing: the same text run again | 9 | +0.14 | 0 of 8 |

Some examples behind the rows:

- **Taste.** Two versions of a sales deck each applied all five of the panel's round-one fixes. They scored 6.0 and 6.1. The unchanged deck scored 6.2. All 15 runs gave the same verdict.
- **Defects.** A report's design went from 6.5 to 9.2 over four rounds of typography fixes. A demo video moved from 0.42 to 0.58 on its panel's 0-to-1 scale after wording changes that explained terms viewers could not follow. Its unchanged control moved from 0.41 to 0.42.
- **Proof.** A startup application gained 0.60 points and a second YES in the round after a paying pilot was signed. The demo video got its first "yes, next step" votes only when product changes were scripted as if they had shipped.

Automated rewrite loops are the extreme case of following the advice. One rewrote a spec for 94 rounds. It climbed from 4.0 to 7.7 and ended at 6.5. Another ran 23 rounds, peaked at 6.6 in round four, and ended at 3.6. Re-scoring the same version moved those judges by up to 0.94 points. A model rewriting to please a model drifts with the noise.

## Why advice on taste fails

- **The written reason is not the cause of the score.** A judge forms an overall verdict, then writes reasons for it. [Turpin et al. (NeurIPS 2023)](https://arxiv.org/abs/2305.04388) showed model explanations can be plausible and still leave out what drove the answer. [A 2026 study of LLM judges](https://arxiv.org/abs/2602.07996) found their stated reasons almost never mention the cue that swung the verdict. Fix the reason, and the cause is untouched.
- **The content of critique barely matters.** [Stechly, Marquez and Kambhampati (2023)](https://arxiv.org/abs/2310.12397) found "the correctness and content of the criticisms" was "largely irrelevant" to iterative prompting. The gains came from trying several answers and letting a sound verifier pick. [Valmeekam et al. (2023)](https://arxiv.org/abs/2310.08118) found binary and detailed feedback worked about the same.
- **Models need outside feedback to correct themselves.** [Huang et al. (ICLR 2024)](https://arxiv.org/abs/2310.01798) found models struggle to self-correct without external feedback, and sometimes get worse. [Kamoi et al. (TACL 2024)](https://arxiv.org/abs/2406.01297) surveyed the field and found no work showing success with feedback from prompted LLMs, outside tasks unusually suited to it. A review panel is prompted LLM feedback.
- **Writing to a judge's taste drifts from the real reader.** [Pan, He, Bowman and Feng (2024)](https://arxiv.org/abs/2407.04549) had one model edit essays to please another. "The evaluator's ratings improve while the generation quality remains stagnant or even decreases." [Pan et al. (ICML 2024)](https://arxiv.org/abs/2402.06627) showed that optimizing in a feedback loop creates side effects the objective does not see.
- **Advice changes its mind.** A cold critic does not remember what it asked for last time. In my log, critics twice asked for the opposite of what the previous round had asked for.
- **Fixes have costs that other critics score.** Answering every critic adds length, hedges and caveats. Critics also disagree with each other. A draft that satisfies all of them is a compromise each likes less.
- **Some scores are capped by facts.** When the remaining objections ask for proof, no wording can meet them.

Human feedback behaves the same way. In the NeurIPS 2014 experiment, [half the variation in reviewer scores was subjective](https://arxiv.org/abs/2109.09774). A [meta-analysis of 607 feedback interventions (Kluger and DeNisi, 1996)](https://psycnet.apa.org/doi/10.1037/0033-2909.119.2.254) found feedback helped on average, but more than a third of interventions made performance worse. Jakob Nielsen's [first rule of usability](https://www.nngroup.com/articles/first-rule-of-usability-dont-listen-to-users/) is "watch what people actually do", not what they say.

## Where written feedback does work

Written feedback is not useless. It works when a score decides what to keep. [GEPA (2025)](https://arxiv.org/abs/2507.19457) uses written reflection on failures to propose new prompts, and beats reinforcement learning with far fewer runs. But GEPA keeps a pool of candidates and selects by measured score. The reflection proposes. The score decides. If a critic's suggestion seems worth trying, treat it as one more version to test, not as an instruction.

## Limits

My log is one person's work, on business writing. I labelled the kind of each edit myself, and each kind has only 4 to 8 pairs. The critics often came from the same model family as the writer. A round exists only where someone chose to run the panel again. And a panel score is still a stand-in. The real test of a pitch deck is the meeting it gets. When a draft goes to many real readers, such as a landing page or an email campaign, their response is a better score than any panel.
