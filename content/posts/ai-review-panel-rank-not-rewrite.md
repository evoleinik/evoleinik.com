---
title: "Use an AI Review Panel to Rank Drafts, Not to Rewrite Them"
date: 2026-11-03
draft: false
tags: [ai, llm, llm-as-judge, evaluation, writing, research]
summary: "We counted every AI review panel we ran this year: 56 panels and 5 automated loops, 270 rounds. Rewriting a draft to match the critics' taste moved their score by 0.04 points out of 10 and changed no verdict. Fixing a checkable error raised the score every time. New proof was what changed decisions. The research agrees: LLM judges rank well and direct badly."
---

We use AI review panels for almost everything we send out. We call them councils. A council is three to seven LLM critics, each with a persona: a VC partner, a skeptical buyer, a competitor's head of product. They run on Claude, GPT and Gemini. Each reads the draft cold and returns scores, a verdict and a list of concerns. We use them on pitch decks, partner notes, specs, emails and comments on public specs.

The habit that grew around them was simple. Read the concerns, fix them, run the council again. It felt like progress. Then we noticed the second round rarely scored better than the first. The verdicts in particular almost never moved. A deck the panel called "second meeting" stayed "second meeting" after we did everything the panel asked.

So we went back and counted every council we had run. That was 56 panels and 5 automated loops, 270 rounds in all, from session transcripts since August and decision docs going back to January. For each round we recorded the verdicts, the mean score and what had changed since the round before.

## Taste advice moved nothing, error fixes and proof did

We sorted every pair of consecutive rounds by the kind of edit made between them. All scores are on a 10-point scale.

| Edit between rounds | Pairs | Mean score change | Rounds where the yes share rose |
|---|---|---|---|
| Taste: framing, emphasis, structure, wording the critic preferred | 5 | +0.04 (2 up, 3 down) | 0 of 5 |
| Error: a wrong fact, a contradiction, a leak, an overclaim, an unexplained term, a typography error | 8 | +0.62 (8 up) | 1 of 5 |
| Proof: a new fact, something built, a signed customer | 4 | +0.66 (4 up) | 3 of 3 |
| Nothing: the same text run again | 9 | +0.14 | 0 of 8 |

Three things stand out.

**Taste advice did nothing measurable.** On a sales deck, we wrote two versions that carried all five of the panel's round-one fixes. They scored 6.0 and 6.1. The unchanged deck, run again as a control, scored 6.2. Every one of the 15 runs said "second meeting" either way.

**Error fixes worked every time.** A report's design went from 6.5 to 9.2 over four rounds of fixes, all of them typography mistakes against known rules: ragged lines, straight quotes, stray emoji. A product demo video moved from 0.42 to 0.58 on its panel's 0-to-1 scale after a set of wording changes. Most of them explained a term viewers could not follow, such as what "Binding: false" means. The unchanged control moved from 0.41 to 0.42.

**Proof is what changed decisions.** Error fixes moved one critic out of 20 to a yes. Proof moved the yes share every time. On a startup application, the round after a paying pilot was signed gained 0.60 points. Traction rose 2 points, and a second critic switched to YES. The demo video got its first three "yes, next step" votes out of 21 only when product changes were added to the script as if they had shipped. Better words alone had moved none.

All advice taken together does lift the score a little: +0.52 on average, up in 16 of 19 pairs. But the yes share rose in only 5 of 28 pairs. The lift comes from fixing errors, and the decision moves on proof.

## Why the panel's taste is a bad guide

**The noise is bigger than the edit.** On the deck panel, the same text moved up to 0.6 points on one dimension between two runs. One critic said "pass" at 95% confidence, then "second meeting" at 80% on identical text. A typical edit is worth 0.1 to 0.4. One re-run cannot tell an improvement from a different roll of the dice. A [2026 study of repeated LLM judging](https://arxiv.org/abs/2606.13685) found pairwise verdicts flip 13.6% of the time on identical input, and needed 11 repeats to recover a stable verdict.

**The written reason is not the cause of the score.** A judge forms an overall verdict, then writes reasons. [Turpin et al. (NeurIPS 2023)](https://arxiv.org/abs/2305.04388) showed model explanations can be plausible and still leave out what drove the answer. [A 2026 study of LLM judges](https://arxiv.org/abs/2602.07996) found their stated reasons almost never mention the cue that actually swung the verdict. Fix the written reason and the real cause is untouched.

**A critic asked for three problems returns three.** Our persona prompts all asked for a "top three": concerns, improvements, gaps. Fix three, and three new ones appear. One write-up raised 14, then 13, then 9 concerns over three rounds, mostly new each time. The length of the list says nothing about how much better the draft can get.

**The advice changes its mind.** A fresh critic does not remember what it asked for last time. In one series, two critics asked again for words the previous round had told us to remove. In another, round four said "registration should not come first" and round five said registration must come before the quote.

**Some scores are capped by facts.** Every panel eventually asks for proof: a named reference customer, a measured result, money that moves. No wording supplies that. One deck search ran 500 variants and topped out around 7.6 "with these judges and these facts".

**Loops that keep the last draft lose the best one.** We had two automated rewrite loops. One ran 94 rounds, climbed from 4.0 to 7.7, and ended at 6.5. The other ran 23 rounds, peaked at 6.6 in round four, and ended at 3.6. Re-scoring the same version moved those judges by up to 0.94 points, so most of each loop's movement was noise. Without keeping the best-scoring draft, the loop wandered.

## The research says the same

The paper that names this is [JETTS (Zhou et al., Salesforce, 2025)](https://arxiv.org/abs/2504.15253). It tested LLM judges as helpers for a generator. Judges were "competitive with outcome reward models in reranking". But "their natural language critiques are currently ineffective in guiding the generator towards better responses".

The self-correction literature agrees.
- [Stechly, Marquez and Kambhampati (2023)](https://arxiv.org/abs/2310.12397) found "the correctness and content of the criticisms" was "largely irrelevant" to iterative prompting. The gains came from a correct answer turning up among several tries and a sound verifier recognising it.
- [Valmeekam et al. (2023)](https://arxiv.org/abs/2310.08118) found self-critique made plans worse than an external verifier did. Binary or detailed feedback made little difference.
- [Huang et al. (ICLR 2024)](https://arxiv.org/abs/2310.01798) found models struggle to self-correct without external feedback, and sometimes get worse.
- [Kamoi et al. (TACL 2024)](https://arxiv.org/abs/2406.01297) surveyed the field. Self-correction works with reliable external feedback. They found no work showing it succeeds with feedback from prompted LLMs, outside tasks unusually suited to it. A review panel is prompted LLM feedback.

Rewriting toward a judge can also go wrong on its own. [Pan, He, Bowman and Feng (2024)](https://arxiv.org/abs/2407.04549) had one model edit essays to please another. "The evaluator's ratings improve while the generation quality remains stagnant or even decreases." [Pan et al. (ICML 2024)](https://arxiv.org/abs/2402.06627) showed that optimizing in a feedback loop creates side effects the objective does not see.

People are no different. In the 2014 NeurIPS experiment, [half the variation in reviewer scores was subjective](https://arxiv.org/abs/2109.09774). A [meta-analysis of 607 feedback interventions](https://psycnet.apa.org/doi/10.1037/0033-2909.119.2.254) found feedback helped on average, but more than a third of interventions made performance worse. Jakob Nielsen's [first rule of usability](https://www.nngroup.com/articles/first-rule-of-usability-dont-listen-to-users/) is the same idea: watch what people do, not what they say.

There is counter-evidence, and it is useful. [GEPA (2025)](https://arxiv.org/abs/2507.19457) uses written reflection on failures to propose new prompts, and beats reinforcement learning with far fewer runs. But GEPA keeps a pool of candidates and selects by measured score. The reflection only proposes. The score decides.

## How we run a council now

The panel ranks. It does not direct.

1. Critics return scores, a verdict, errors of fact with the line they are on, and the one piece of proof that would change their verdict. We no longer ask for improvements.
2. We fix every checkable error directly, because it is wrong.
3. We write 3 to 10 variants ourselves: a different opening, spine, close or length. A variant that only applies the last round's advice does not count.
4. The current best text runs again in every round as an unchanged control. Its spread is the noise.
5. A variant wins only if it beats the control by more than that spread, and holds on fresh runs.
6. We always carry the best-scoring draft forward, never simply the latest.
7. When the top stops moving, we stop writing and go get the proof the critics asked for.

The first time we ran it this way, on 500 deck variants, the winner beat the unchanged deck by 0.40 points over 60 fresh judge calls. Its approval rate was 30%, against 13% for the control.

## Limits

I labelled the kind of each edit myself, from the recorded change. Each kind has only 4 to 8 pairs. The critics often came from the same model family as the editor. Rounds exist only where someone chose to run the panel again. And a panel score is still a stand-in for a real reader. The real test of a deck is the meeting it gets.
