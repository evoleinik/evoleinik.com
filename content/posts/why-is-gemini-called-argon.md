---
title: "Why is Gemini called Argon? Gemini 4 model names explained"
date: 2026-11-20
draft: false
tags: [gemini, gemini-4, google, llm, model-selection]
summary: "Gemini 4 models are named Hydrogen, Carbon and Argon. The element numbers don't match the tiers. Carbon is top, Argon is efficient, Hydrogen is fast."
---

Google DeepMind named the Gemini 4 models after chemical elements: Hydrogen, Carbon and Argon, with Neon seen in a leak. I found no public reason for the names. The element numbers do not match the tiers, so treat the names as labels. Carbon is the strongest model. Argon sits below it at the same price. Hydrogen is the fast, cheap one that replaces the Flash brand.

## Map each Gemini 4 name to its tier

| Model | Element number | Atomic weight | What it is |
|---|---|---|---|
| Hydrogen | 1 | 1.008 | Fast and cheap. Replaces "Flash". |
| Carbon | 6 | 12.011 | Strongest. Thinks more per turn than Argon. |
| Neon | 10 | 20.180 | Not confirmed by Google (see below). |
| Argon | 18 | 39.948 | Frontier model with lower token use. |

Read the table top to bottom and the chemistry climbs steadily. The model ladder does not. If the numbers meant anything, Argon would be the strongest model. It is the efficient pick instead. Carbon, the second lightest atom here, is the top model.

## Why is Gemini called Argon?

Nobody outside Google knows. The launch post and model card for Hydrogen give no reason for the theme. Neither did any coverage I read.

The element number is the count of protons in one atom. It says nothing about speed, size or price. Atomic weight follows the same order, so it gives no clue either.

One pattern does hold. All four names are light elements from the first three rows of the periodic table. That looks like a theme picked for sound, not a code for rank.

The theme is not even about gases. Hydrogen, neon and argon are gases at room temperature. Carbon is a solid. Hydrogen gas is made of two-atom molecules, while neon and argon exist as single atoms. So counting molecules gets you nowhere.

## Gemini Argon vs Carbon: which to pick

This is a real choice, not a sideways swap. Carbon is the step up. Secondary sources describe it as the strongest model, with more thinking per turn. Argon is the frontier model tuned for lower token use.

Both list at the same price on third-party comparison tables: $2 input and $10 output per million tokens until 30 November 2026. After that the listed price rises to $4 and $20 for both. Check Google's own pricing page before you rely on these numbers.

Pick Carbon for the hardest reasoning tasks, where the extra thinking pays off. Pick Argon for most coding and knowledge work, where you want frontier quality at fewer tokens per answer.

## Gemini 4 Hydrogen vs Argon

Hydrogen replaced the Flash line. It is the default for everyday coding and agent work, and it rolls out to free users too. One comparison lists it at $1.50 input and $7.50 output per million tokens.

A router vendor's blog claims Hydrogen scores about four index points above Argon and runs about three times faster. That source sells model routing, so treat the number as a hint and run your own test. If it holds for your workload, Argon's price no longer buys you more quality than Hydrogen.

## Check the Gemini 4 Neon rumor

Neon is not a released model as of 20 November 2026. TestingCatalog spotted a "Gemini 4 Neon" string in the Gemini web app code on 16 November. Google has not commented. Some reports guess it is a Flash Lite style model. Others note that Neon was also the internal name of an AI Ultra Lite plan, so the string may not be a model at all.

Do not plan around Neon until Google publishes a model card.

## Verify which Gemini 4 models your key can call

The names in blog posts and the IDs your API accepts are two different things. List what your key can see:

```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=$GEMINI_API_KEY" \
  | jq -r '.models[].name' | grep gemini-4
```

Expected output is one line per model, such as `models/gemini-4-argon`. A model missing from this list will fail with a 404 no matter what the docs say.

On Vertex AI, location matters too. In my tests in October 2026, `gemini-4-argon` answered only at location `global`. The same call at `us-central1` returned 404. Probe the exact endpoint you will use in production.

## Trade-offs

The tier facts above come mostly from secondary sources and one vendor blog. Google's Hydrogen post and model card confirm Hydrogen. Carbon vs Argon placement comes from comparison sites. Prices change, and the 30 November price rise is listed by third parties, not by me. Run a short side-by-side test on your own prompts before you switch models in production.

Sources:

- [Introducing Gemini 4 Hydrogen (Google blog)](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-hydrogen/)
- [Gemini 4 Hydrogen model card (DeepMind)](https://deepmind.google/models/model-cards/gemini-4-hydrogen/)
- [Hydrogen replaces Flash (Android Headlines)](https://www.androidheadlines.com/2026/11/google-gemini-4-hydrogen-replaces-flash.html)
- [Hydrogen vs Argon vs Carbon (SmartScope)](https://smartscope.blog/en/blog/gemini-4-hydrogen-vs-argon-vs-carbon-differences-2026/)
- [Gemini 4 Hydrogen vs Gemini 4 (OrcaRouter)](https://www.orcarouter.ai/blog/gemini-4-hydrogen-vs-gemini-4)
- [Gemini 4 Neon spotted (Nokia Power User)](https://nokiapoweruser.com/gemini-4-neon-spotted-google-ai-rumors/)
- [Gemini 4 Neon leak (Pasquale Pillitteri)](https://pasqualepillitteri.it/en/news/34252/gemini-4-neon-leak-flash-lite-ultra-lite-plan)
